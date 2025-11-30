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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown events for the FastAPI application"""
    # Connect to Redis (required)
    await redis_manager.connect()

    # Register the connection manager's message handler with Redis
    redis_manager.set_message_handler(connection_manager.handle_redis_message)

    # Start the Redis message listener in the background
    listener_task = asyncio.create_task(redis_manager.start_message_listener())
    app.state.redis_listener_task = listener_task
    logger.info("Redis Pub/Sub enabled")

    yield

    await redis_manager.disconnect()


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


# Initialize connection manager
connection_manager = ConnectionManager()

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""

    participant_id = await connection_manager.connect(websocket)

    try:
        # Send welcome message with participant ID
        welcome_message = {
            "type": "welcome",
            "participant_id": participant_id,
        }
        await websocket.send_text(json.dumps(welcome_message))

        # Send connection update to all clients
        connection_update = {
            "type": "connection_update",
            "connection_count": connection_manager.get_connection_count(),
            "participants": connection_manager.get_all_participants(),
        }
        await connection_manager.broadcast_to_all(
            connection_update, exclude=websocket
        )

        # Message handling loop
        while True:
            message_text = await websocket.receive_text()

            try:
                message = json.loads(message_text)
                message_type = message.get("type")
                
                # Handle mode message to set participant role
                if message_type == "mode":
                    role = message.get("mode")
                    connection_manager.set_participant_role(websocket, role)
                    
                    # Broadcast updated participants list
                    participants_update = {
                        "type": "participants_update",
                        "participants": connection_manager.get_all_participants(),
                    }
                    await connection_manager.broadcast_to_all(participants_update)
                    continue

                # Handle targeted settings messages (per-prompter)
                target_id = message.get("target_id")
                if target_id:
                    # Send to specific participant only
                    await connection_manager.send_to_participant(target_id, message)
                    logger.info(f"Sent targeted message type '{message_type}' to participant {target_id}")
                else:
                    # Broadcast to all other clients across instances
                    message["_sender"] = "client"
                    await connection_manager.broadcast_to_all(
                        message, exclude=websocket
                    )
                    logger.info(f"Broadcast message: {message_type}")

            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message_text}")

    except WebSocketDisconnect:
        disconnected_id = connection_manager.disconnect(websocket)

        # Notify remaining clients about participant leaving
        disconnect_update = {
            "type": "participant_left",
            "participant_id": disconnected_id,
            "connection_count": connection_manager.get_connection_count(),
            "participants": connection_manager.get_all_participants(),
        }
        await connection_manager.broadcast_to_all(disconnect_update)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    redis_health = await redis_manager.health_check()
    return {
        "status": "healthy",
        "active_connections": connection_manager.get_connection_count(),
        "redis": redis_health,
    }

@app.get("/api/live")
async def live_check():
    """Liveness check endpoint"""
    return {"status": "alive"}

# Playback control endpoints
@app.post("/api/playback/start")
async def start_playback():
    """Start playback """
    try:
        message = {"type": "start"}
        await connection_manager.broadcast_to_all(message)
        logger.info("Playback started via API")
        return {"success": True, "message": "Playback started"}
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        raise HTTPException(status_code=500, detail="Failed to start playback")


@app.post("/api/playback/stop")
async def stop_playback():
    """Stop playback """
    try:
        message = {"type": "pause"}
        await connection_manager.broadcast_to_all(message)
        logger.info("Playback stopped via API")
        return {"success": True, "message": "Playback stopped"}
    except Exception as e:
        logger.error(f"Error stopping playback: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop playback")

@app.post("/api/playback/scroll/back/{lines}")
@app.post("/api/playback/scroll/back")
@app.post("/api/playback/scroll/bwd/{lines}")
@app.post("/api/playback/scroll/bwd")
@app.post("/api/playback/scroll/b/{lines}")
@app.post("/api/playback/scroll/b/")
async def scroll_back(lines: int = 5):
    """Scroll back by specified number of lines (default: 5)"""
    try:
        message = { "type": "scroll_lines", "direction": "backward", "lines": lines, "smooth": True }
        await connection_manager.broadcast_to_all(message)
        logger.info(f"Scrolling back {lines} line(s) via API")
        return {"success": True, "message": f"Scrolled back {lines} line(s)"}
    except Exception as e:
        logger.error(f"Error scrolling back: {e}")
        raise HTTPException(status_code=500, detail="Failed to scroll back")

@app.post("/api/playback/scroll/forward/{lines}")
@app.post("/api/playback/scroll/forward")
@app.post("/api/playback/scroll/fwd/{lines}")
@app.post("/api/playback/scroll/fwd")
@app.post("/api/playback/scroll/f/{lines}")
@app.post("/api/playback/scroll/f/")
async def scroll_forward(lines: int = 5):
    """Scroll forward by specified number of lines (default: 5)"""
    try:
        message = { "type": "scroll_lines", "direction": "forward", "lines": lines, "smooth": True }
        await connection_manager.broadcast_to_all(message)
        logger.info(f"Scrolling forward {lines} line(s) via API")
        return {"success": True, "message": f"Scrolled forward {lines} line(s)"}
    except Exception as e:
        logger.error(f"Error scrolling forward: {e}")
        raise HTTPException(status_code=500, detail="Failed to scroll forward")


@app.post("/api/playback/scroll/top")
@app.post("/api/playback/scroll/start")
@app.post("/api/playback/scroll/beginning")
async def scroll_to_top():
    """Scroll to the top of the script"""
    try:
        message = {"type": "go_to_beginning"}
        await connection_manager.broadcast_to_all(message)
        logger.info("Scrolling to top via API")
        return {"success": True, "message": "Scrolled to top"}
    except Exception as e:
        logger.error(f"Error scrolling to top: {e}")
        raise HTTPException(status_code=500, detail="Failed to scroll to top")


@app.post("/api/playback/scroll/bottom")
@app.post("/api/playback/scroll/end")
@app.post("/api/playback/scroll/finish")
async def scroll_to_end():
    """Scroll to the end of the script"""
    try:
        message = {"type": "go_to_end"}
        await connection_manager.broadcast_to_all(message)
        logger.info("Scrolling to end via API")
        return {"success": True, "message": "Scrolled to end"}
    except Exception as e:
        logger.error(f"Error scrolling to end: {e}")
        raise HTTPException(status_code=500, detail="Failed to scroll to end")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
