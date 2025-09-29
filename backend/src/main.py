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

    yield
    
    await redis_manager.disconnect()


# Initialize FastAPI application
app = FastAPI(
    title="Remote Teleprompter API",
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    lifespan=lifespan
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


@app.post("/api/join", response_model=JoinResponse)
async def join_teleprompter(request: JoinRequest):
    """Join the teleprompter (no room management needed)"""
    try:
        return JoinResponse(
            success=True,
            message="Ready to connect via WebSocket"
        )
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
            "connection_count": connection_manager.get_connection_count()
        }
        await connection_manager.broadcast_to_all_instances(connection_update, exclude=websocket)
        
        # Message handling loop
        while True:
            message_text = await websocket.receive_text()
            
            try:
                message = json.loads(message_text)
                message["_sender"] = "client"
                
                # Broadcast to all other clients across instances
                await connection_manager.broadcast_to_all_instances(message, exclude=websocket)
                logger.info(f"Broadcast message: {message.get('type', 'unknown')}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message_text}")
                
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket)
        
        # Notify remaining clients about updated connection count
        connection_update = {
            "type": "connection_update", 
            "connection_count": connection_manager.get_connection_count()
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
            "available": redis_manager.is_available()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)