"""
Remote Teleprompter API Backend
FastAPI backend providing WebSocket communication for teleprompter functionality.
Simple architecture with no room management - everyone connects to the same channel.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import logging
from typing import Set, Optional
from contextlib import asynccontextmanager

from redis_manager import redis_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    try:
        await redis_manager.connect()
        # Start the Redis message listener in the background
        listener_task = asyncio.create_task(redis_manager.start_message_listener())

        # Store the task to prevent it from being garbage collected
        app.state.redis_listener_task = listener_task
        logger.info("Redis Pub/Sub enabled for horizontal scaling")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without Redis pub/sub.")
    
    yield
    
    # Shutdown logic
    await redis_manager.disconnect()

app = FastAPI(
    title="Remote Teleprompter API", 
    openapi_url="/api/openapi.json", 
    docs_url="/api/docs",
    lifespan=lifespan
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure CORS for frontend apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for API requests/responses
class JoinRequest(BaseModel):
    role: str  # "controller" or "teleprompter"

class JoinResponse(BaseModel):
    success: bool
    message: str

# Store active connections with Redis Pub/Sub support
class ConnectionManager:
    def __init__(self):
        # Local connections for this instance only
        self.active_connections: Set[WebSocket] = set()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        connection_count = len(self.active_connections)
        print(f"Client connected (total: {connection_count})")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        connection_count = len(self.active_connections)
        print(f"Client disconnected (remaining: {connection_count})")
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
    
    async def broadcast_to_all(self, message_str: str, exclude: WebSocket = None):
        """Broadcast message to all local connections"""
        if not self.active_connections:
            return
        
        # Create a list of connections to remove (disconnected ones)
        disconnected = []
        
        for websocket in self.active_connections:
            if websocket == exclude:
                continue
                
            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)
    
    async def broadcast_to_all_instances(self, message_dict: dict, exclude: WebSocket = None):
        """Broadcast message to all instances via Redis and local connections"""
        message_str = json.dumps(message_dict)
        
        # Broadcast to local connections first
        await self.broadcast_to_all(message_str, exclude)
        
        # Publish to Redis for other instances (if available)
        if redis_manager.is_available():
            # Add metadata to distinguish from messages we should handle
            redis_message = {
                **message_dict,
                "_redis_source": True  # Mark this as coming from Redis to avoid loops
            }
            await redis_manager.publish_message("teleprompter", redis_message)
    
    async def _handle_redis_message(self, message: dict):
        """Handle messages received from Redis"""
        try:
            # Don't process messages that originated from this instance to avoid loops
            if message.get('_redis_source'):
                # Remove the metadata before broadcasting
                message_copy = {k: v for k, v in message.items() if not k.startswith('_')}
                message_str = json.dumps(message_copy)
                
                # Broadcast to local connections only (other instances handle their own)
                await self.broadcast_to_all(message_str)
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

manager = ConnectionManager()

# Simple API endpoints
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
    
    await manager.connect(websocket)
    
    try:
        # Send connection update to all clients
        connection_update = {
            "type": "connection_update",
            "connection_count": manager.get_connection_count()
        }
        await manager.broadcast_to_all_instances(connection_update, exclude=websocket)
        
        while True:
            # Wait for messages from this client
            message_text = await websocket.receive_text()
            
            try:
                message = json.loads(message_text)
                
                # Add sender info and broadcast to all other clients
                message["_sender"] = "client"
                await manager.broadcast_to_all_instances(message, exclude=websocket)
                
                logger.info(f"Broadcast message: {message.get('type', 'unknown')}")
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {message_text}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        # Notify remaining clients about updated connection count
        connection_update = {
            "type": "connection_update", 
            "connection_count": manager.get_connection_count()
        }
        await manager.broadcast_to_all_instances(connection_update)
        
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_connections": manager.get_connection_count(),
        "redis": {
            "status": "connected" if redis_manager.is_connected else "disconnected",
            "available": redis_manager.is_available()
        }
    }

# Setup Redis message handler
async def setup_redis_handler():
    """Setup Redis message handler for the connection manager"""
    if hasattr(redis_manager, 'set_message_handler'):
        redis_manager.set_message_handler(manager._handle_redis_message)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)