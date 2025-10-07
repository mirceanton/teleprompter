"""
Remote Teleprompter API Backend
FastAPI backend providing WebSocket communication for teleprompter functionality.
Simple architecture with no room management - everyone connects to the same channel.
"""

import json
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from redis_manager import redis_manager
from connection_manager import ConnectionManager
from obs_manager import obs_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the FastAPI application"""
    try:
        await redis_manager.connect()

        # Register the connection manager's message handler with Redis
        redis_manager.set_message_handler(connection_manager.handle_redis_message)

        # Start the Redis message listener in the background
        listener_task = asyncio.create_task(redis_manager.start_message_listener())
        app.state.redis_listener_task = listener_task
        logger.info("Redis Pub/Sub enabled")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without Redis pub/sub.")

    # Initialize OBS manager
    async def obs_status_callback(status_message):
        """Callback to broadcast OBS status updates"""
        await connection_manager.broadcast_to_all_instances(status_message)

    obs_manager.set_status_callback(obs_status_callback)
    
    # Try to connect to OBS if enabled
    if obs_manager.is_enabled():
        await obs_manager.connect()

    yield

    await redis_manager.disconnect()
    await obs_manager.disconnect()


# Initialize FastAPI application
app = FastAPI(
    title="Remote Teleprompter API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan,
)

# Configure CORS for frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class JoinRequest(BaseModel):
    role: str  # "controller" or "teleprompter"


class JoinResponse(BaseModel):
    success: bool
    message: str


class OBSConfig(BaseModel):
    host: str = "localhost"
    port: int = 4455
    password: str = ""
    enabled: bool = False
    start_delay: int = 0


class OBSStatusResponse(BaseModel):
    enabled: bool
    connected: bool
    recording: bool
    host: str
    port: int
    start_delay: int


# Initialize connection manager
connection_manager = ConnectionManager()


@app.post("/api/join", response_model=JoinResponse)
async def join_teleprompter(request: JoinRequest):
    """Join the teleprompter (no room management needed)"""
    try:
        return JoinResponse(success=True, message="Ready to connect via WebSocket")
    except Exception as e:
        logger.error(f"Error in join endpoint: {e}")
        raise HTTPException(status_code=500, detail="Failed to join")


@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""

    await connection_manager.connect(websocket)

    try:
        # Send connection update to all clients
        connection_update = {
            "type": "connection_update",
            "connection_count": connection_manager.get_connection_count(),
        }
        await connection_manager.broadcast_to_all_instances(
            connection_update, exclude=websocket
        )

        # Send current OBS status to the new client
        obs_status = await obs_manager.get_status()
        await websocket.send_text(json.dumps({
            "type": "obs_status",
            **obs_status
        }))

        # Message handling loop
        while True:
            message_text = await websocket.receive_text()

            try:
                message = json.loads(message_text)
                message["_sender"] = "client"

                # Handle OBS integration for teleprompter control
                if message.get("type") == "start":
                    # Start OBS recording when teleprompter starts
                    if obs_manager.is_enabled() and obs_manager.is_connected():
                        asyncio.create_task(obs_manager.start_recording_with_delay())
                elif message.get("type") == "pause" or message.get("type") == "reset":
                    # Stop OBS recording when teleprompter stops/resets
                    if obs_manager.is_enabled() and obs_manager.is_connected() and obs_manager.is_recording():
                        asyncio.create_task(obs_manager.stop_recording())

                # Broadcast to all other clients across instances
                await connection_manager.broadcast_to_all_instances(
                    message, exclude=websocket
                )
                logger.info(f"Broadcast message: {message.get('type', 'unknown')}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message_text}")

    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)

        # Notify remaining clients about updated connection count
        connection_update = {
            "type": "connection_update",
            "connection_count": connection_manager.get_connection_count(),
        }
        await connection_manager.broadcast_to_all_instances(connection_update)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": connection_manager.get_connection_count(),
        "redis": {
            "status": "connected" if redis_manager.is_connected else "disconnected",
            "available": redis_manager.is_available(),
        },
    }


@app.get("/api/obs/status", response_model=OBSStatusResponse)
async def get_obs_status():
    """Get current OBS status"""
    try:
        status = await obs_manager.get_status()
        return OBSStatusResponse(**status)
    except Exception as e:
        logger.error(f"Error getting OBS status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get OBS status")


@app.post("/api/obs/config")
async def configure_obs(config: OBSConfig):
    """Configure OBS connection settings"""
    try:
        # Update configuration
        obs_manager.configure(
            host=config.host,
            port=config.port,
            password=config.password,
            enabled=config.enabled,
            start_delay=config.start_delay,
        )

        # Try to connect if enabled
        if config.enabled:
            connected = await obs_manager.connect()
            if not connected:
                return {
                    "success": False,
                    "message": "OBS configuration saved but failed to connect"
                }
        else:
            await obs_manager.disconnect()

        return {"success": True, "message": "OBS configuration saved"}
    except Exception as e:
        logger.error(f"Error configuring OBS: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure OBS")


@app.post("/api/obs/test-connection")
async def test_obs_connection():
    """Test OBS connection with current settings"""
    try:
        connected = await obs_manager.connect()
        if connected:
            status = await obs_manager.get_status()
            return {
                "success": True,
                "message": "Successfully connected to OBS",
                "status": status
            }
        else:
            return {
                "success": False,
                "message": "Failed to connect to OBS"
            }
    except Exception as e:
        logger.error(f"Error testing OBS connection: {e}")
        return {
            "success": False,
            "message": f"Failed to connect to OBS: {str(e)}"
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
