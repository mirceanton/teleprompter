"""
Remote Teleprompter API Backend
FastAPI backend providing WebSocket communication and API endpoints for teleprompter microservices.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import logging
from typing import Dict, Set, Optional
from pathlib import Path
from contextlib import asynccontextmanager
from ai_scrolling import ai_scrolling_service, AIScrollingConfig
from redis_manager import redis_manager
from room_manager import room_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    try:
        await redis_manager.connect()
        await ai_scrolling_service.initialize()
        # Start the Redis message listener in the background
        listener_task = asyncio.create_task(redis_manager.start_message_listener())

        # Store the task to prevent it from being garbage collected
        app.state.redis_listener_task = listener_task
        logger.info("Redis Pub/Sub enabled for horizontal scaling")
    except Exception as e:
        logger.warning(f"Redis not available: {e}. Running without Redis pub/sub.")
        await ai_scrolling_service.initialize()
    
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
class CreateRoomRequest(BaseModel):
    room_name: Optional[str] = None

class CreateRoomResponse(BaseModel):
    room_id: str
    room_secret: str
    room_name: str

class JoinRoomRequest(BaseModel):
    room_id: str
    room_secret: str
    role: str  # "controller" or "teleprompter"

class JoinRoomResponse(BaseModel):
    success: bool
    participant_id: Optional[str] = None
    room_name: Optional[str] = None
    message: str

class RoomInfoResponse(BaseModel):
    room_id: str
    room_name: str
    participants: list
    controller_id: Optional[str]

class UpdateRoomNameRequest(BaseModel):
    room_id: str
    room_name: str
    participant_id: str



# Store active connections by channel with Redis Pub/Sub support
class ConnectionManager:
    def __init__(self):
        # Local connections for this instance only
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        connection_count = len(self.active_connections[channel])
        print(f"Client connected to channel: {channel} (total: {connection_count})")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            connection_count = len(self.active_connections[channel])
            if not self.active_connections[channel]:
                del self.active_connections[channel]
                print(f"Client disconnected from channel: {channel} (channel closed)")
            else:
                print(f"Client disconnected from channel: {channel} (remaining: {connection_count})")
    
    def get_channel_info(self, channel: str) -> dict:
        """Get information about local connections in a channel"""
        if channel not in self.active_connections:
            return {"exists": False, "connection_count": 0}
        return {
            "exists": True, 
            "connection_count": len(self.active_connections[channel])
        }
    
    async def broadcast_to_channel(self, message: str, channel: str, exclude: WebSocket = None):
        """Broadcast message to local WebSocket connections only"""
        if channel in self.active_connections:
            disconnected = set()
            # Create a copy of the set to avoid "Set changed size during iteration"
            connections_copy = self.active_connections[channel].copy()
            for connection in connections_copy:
                if connection != exclude:
                    try:
                        await connection.send_text(message)
                    except:
                        disconnected.add(connection)
            
            # Clean up disconnected clients - check if channel still exists
            if channel in self.active_connections:
                for conn in disconnected:
                    self.active_connections[channel].discard(conn)
    
    async def broadcast_to_all_instances(self, message_dict: dict, channel: str, exclude: WebSocket = None):
        """Broadcast message to all instances via Redis and local connections"""
        message_str = json.dumps(message_dict)
        
        # Broadcast to local connections first
        await self.broadcast_to_channel(message_str, channel, exclude)
        
        # Publish to Redis for other instances (if available)
        if redis_manager.is_available():
            # Add metadata to distinguish from messages we should handle
            redis_message = {
                **message_dict,
                "_redis_source": True  # Mark this as coming from Redis to avoid loops
            }
            await redis_manager.publish_message(channel, redis_message)
    
    async def _handle_redis_message(self, message: dict):
        """Handle messages received from Redis"""
        try:
            # Extract the teleprompter channel from the message
            channel = message.get('_teleprompter_channel')
            if not channel:
                logger.warning("Redis message missing teleprompter channel information")
                return
            
            # Don't process messages that originated from this instance to avoid loops
            if message.get('_redis_source'):
                # Remove the metadata before broadcasting
                message_copy = {k: v for k, v in message.items() if not k.startswith('_')}
                message_str = json.dumps(message_copy)
                
                # Broadcast to local connections only (other instances handle their own)
                await self.broadcast_to_channel(message_str, channel)
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")

manager = ConnectionManager()

# Room Management Endpoints
@app.post("/api/rooms", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """Create a new room (controller only)"""
    try:
        room_id, room_secret, room_name = await room_manager.create_room(request.room_name)
        return CreateRoomResponse(
            room_id=room_id,
            room_secret=room_secret,
            room_name=room_name
        )
    except Exception as e:
        logger.error(f"Error creating room: {e}")
        raise HTTPException(status_code=500, detail="Failed to create room")

@app.post("/api/rooms/join", response_model=JoinRoomResponse)
async def join_room(request: JoinRoomRequest):
    """Join an existing room with authentication"""
    try:
        # Verify room exists and secret is correct
        if not await room_manager.verify_room_access(request.room_id, request.room_secret):
            return JoinRoomResponse(
                success=False,
                message="Invalid room ID or secret"
            )
        
        # Add participant to room
        participant_id = await room_manager.add_participant(request.room_id, request.role)
        if not participant_id:
            return JoinRoomResponse(
                success=False,
                message="Failed to join room. Room may be full or role unavailable."
            )
        
        # Get room info for room name
        room = await room_manager.get_room(request.room_id)
        room_name = room.room_name if room else None
        
        return JoinRoomResponse(
            success=True,
            participant_id=participant_id,
            room_name=room_name,
            message="Successfully joined room"
        )
        
    except Exception as e:
        logger.error(f"Error joining room: {e}")
        raise HTTPException(status_code=500, detail="Failed to join room")

@app.get("/api/rooms/{room_id}", response_model=RoomInfoResponse)
async def get_room_info(room_id: str):
    """Get room information"""
    try:
        room = await room_manager.get_room(room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        participants = []
        for participant in room.participants.values():
            participants.append({
                "id": participant.id,
                "role": participant.role,
                "joined_at": participant.joined_at,
                "last_seen": participant.last_seen
            })
        
        return RoomInfoResponse(
            room_id=room.room_id,
            room_name=room.room_name,
            participants=participants,
            controller_id=room.controller_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting room info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get room info")

@app.put("/api/rooms/{room_id}/name")
async def update_room_name(room_id: str, request: UpdateRoomNameRequest):
    """Update room name (controller only)"""
    try:
        # Verify the participant is the controller of this room
        if not await room_manager.is_controller(room_id, request.participant_id):
            raise HTTPException(status_code=403, detail="Only the controller can update room name")
        
        # Update room name
        success = await room_manager.update_room_name(room_id, request.room_name)
        if not success:
            raise HTTPException(status_code=404, detail="Room not found")
        
        # Broadcast room name update to all participants
        update_message = {
            "type": "room_name_updated",
            "room_id": room_id,
            "room_name": request.room_name
        }
        await manager.broadcast_to_all_instances(update_message, room_id)
        
        return {"success": True, "message": "Room name updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating room name: {e}")
        raise HTTPException(status_code=500, detail="Failed to update room name")

@app.delete("/api/rooms/{room_id}/participants/{participant_id}")
async def kick_participant(room_id: str, participant_id: str, kicker_id: str):
    """Kick a participant from a room (controller only)"""
    try:
        # Verify kicker is the controller
        if not await room_manager.is_controller(room_id, kicker_id):
            raise HTTPException(status_code=403, detail="Only the controller can kick participants")
        
        # Don't allow controller to kick themselves
        if kicker_id == participant_id:
            raise HTTPException(status_code=400, detail="Controller cannot kick themselves")
        
        success = await room_manager.remove_participant(room_id, participant_id)
        if not success:
            raise HTTPException(status_code=404, detail="Participant not found")
        
        return {"success": True, "message": "Participant kicked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error kicking participant: {e}")
        raise HTTPException(status_code=500, detail="Failed to kick participant")

@app.websocket("/api/ws/{room_id}/{participant_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, participant_id: str):
    """WebSocket endpoint for real-time communication with room authentication"""
    
    # Verify participant is in the room
    room = await room_manager.get_room(room_id)
    if not room or participant_id not in room.participants:
        await websocket.close(code=4003, reason="Invalid room or participant")
        return
    
    # Use room_id as the channel for backward compatibility
    channel = room_id
    await manager.connect(websocket, channel)
    
    # Update participant last seen
    await room_manager.update_participant_last_seen(room_id, participant_id)
    
    # Send connection count update to all clients in channel (including the new one)
    connection_info = manager.get_channel_info(channel)
    participants = await room_manager.get_room_participants(room_id)
    
    connection_update = {
        "type": "connection_update",
        "channel": channel,
        "room_id": room_id,
        "connection_count": connection_info["connection_count"],
        "participants": [
            {
                "id": p.id,
                "role": p.role,
                "joined_at": p.joined_at,
                "last_seen": p.last_seen
            }
            for p in participants
        ]
    }
    await manager.broadcast_to_all_instances(connection_update, channel)
    
    # Send participant joined notification to other participants
    current_participant = await room_manager.get_participant(room_id, participant_id)
    if current_participant:
        participant_joined = {
            "type": "participant_joined",
            "room_id": room_id,
            "participant": {
                "id": current_participant.id,
                "role": current_participant.role,
                "joined_at": current_participant.joined_at
            }
        }
        await manager.broadcast_to_all_instances(participant_joined, channel, exclude=websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add participant info to message
            message["sender_id"] = participant_id
            message["room_id"] = room_id
            
            # Log the message type for debugging
            print(f"Channel {channel}: Received {message.get('type', 'unknown')} message from {participant_id}")
            
            # Update participant last seen on any activity
            await room_manager.update_participant_last_seen(room_id, participant_id)
            
            # Handle special messages
            message_type = message.get('type')
            
            if message_type == 'request_connection_info':
                # Send current connection count and participants to requesting client
                participants = await room_manager.get_room_participants(room_id)
                connection_update_str = json.dumps({
                    "type": "connection_update",
                    "channel": channel,
                    "room_id": room_id,
                    "connection_count": manager.get_channel_info(channel)["connection_count"],
                    "participants": [
                        {
                            "id": p.id,
                            "role": p.role,
                            "joined_at": p.joined_at,
                            "last_seen": p.last_seen
                        }
                        for p in participants
                    ]
                })
                await websocket.send_text(connection_update_str)
            elif message_type == 'kick_participant':
                # Handle participant kick (controller only)
                target_participant_id = message.get('target_participant_id')
                if await room_manager.is_controller(room_id, participant_id) and target_participant_id:
                    if target_participant_id != participant_id:  # Can't kick self
                        await room_manager.remove_participant(room_id, target_participant_id)
                        # Broadcast kick notification
                        kick_message = {
                            "type": "participant_kicked",
                            "participant_id": target_participant_id,
                            "room_id": room_id
                        }
                        await manager.broadcast_to_all_instances(kick_message, channel)
            elif message_type == 'ai_scrolling_config':
                # Handle AI scrolling configuration
                await handle_ai_scrolling_config(channel, message, websocket)
            elif message_type == 'audio_chunk':
                # Handle audio chunk for AI scrolling
                await handle_audio_chunk(channel, message, websocket)
            elif message_type == 'ai_scrolling_start':
                # Start AI scrolling session
                await handle_ai_scrolling_start(channel, message, websocket)
            elif message_type == 'ai_scrolling_stop':
                # Stop AI scrolling session
                await handle_ai_scrolling_stop(channel, message, websocket)
            else:
                # Broadcast to all other clients in the same channel across all instances
                await manager.broadcast_to_all_instances(message, channel, exclude=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        # Remove participant from room
        await room_manager.remove_participant(room_id, participant_id)
        # Clean up AI scrolling session if needed
        ai_scrolling_service.remove_session(channel)
        
        # Check if room still exists and broadcast updated connection count
        room = await room_manager.get_room(room_id)
        if room:
            connection_info = manager.get_channel_info(channel)
            participants = await room_manager.get_room_participants(room_id)
            connection_update = {
                "type": "connection_update",
                "channel": channel,
                "room_id": room_id,
                "connection_count": connection_info["connection_count"],
                "participants": [
                    {
                        "id": p.id,
                        "role": p.role,
                        "joined_at": p.joined_at,
                        "last_seen": p.last_seen
                    }
                    for p in participants
                ]
            }
            await manager.broadcast_to_all_instances(connection_update, channel)
        else:
            # Room was deleted, notify any remaining connections
            room_deleted_message = {
                "type": "room_deleted",
                "room_id": room_id,
                "message": "Room has been closed"
            }
            await manager.broadcast_to_all_instances(room_deleted_message, channel)
            
    except Exception as e:
        print(f"Error in channel {channel}: {e}")
        manager.disconnect(websocket, channel)
        # Remove participant from room
        await room_manager.remove_participant(room_id, participant_id)
        # Clean up AI scrolling session if needed
        ai_scrolling_service.remove_session(channel)
        
        # Check if room still exists and broadcast updated connection count
        room = await room_manager.get_room(room_id)
        if room:
            connection_info = manager.get_channel_info(channel)
            participants = await room_manager.get_room_participants(room_id)
            connection_update = {
                "type": "connection_update",
                "channel": channel,
                "room_id": room_id,
                "connection_count": connection_info["connection_count"],
                "participants": [
                    {
                        "id": p.id,
                        "role": p.role,
                        "joined_at": p.joined_at,
                        "last_seen": p.last_seen
                    }
                    for p in participants
                ]
            }
            await manager.broadcast_to_all_instances(connection_update, channel)
        else:
            # Room was deleted, notify any remaining connections
            room_deleted_message = {
                "type": "room_deleted",
                "room_id": room_id,
                "message": "Room has been closed"
            }
            await manager.broadcast_to_all_instances(room_deleted_message, channel)

# AI Scrolling message handlers
async def handle_ai_scrolling_config(channel: str, message: dict, websocket: WebSocket):
    """Handle AI scrolling configuration updates"""
    try:
        config = AIScrollingConfig(
            enabled=message.get("enabled", False),
            look_ahead_chars=message.get("look_ahead_chars", 100),
            look_behind_chars=message.get("look_behind_chars", 50),
            confidence_threshold=message.get("confidence_threshold", 0.7),
            pause_threshold_seconds=message.get("pause_threshold_seconds", 3.0),
            scroll_speed_multiplier=message.get("scroll_speed_multiplier", 1.0),
            audio_source=message.get("audio_source", "controller")
        )
        
        ai_scrolling_service.update_config(channel, config)
        
        # Broadcast configuration update to all clients
        response = {
            "type": "ai_scrolling_config_updated",
            "config": {
                "enabled": config.enabled,
                "look_ahead_chars": config.look_ahead_chars,
                "look_behind_chars": config.look_behind_chars,
                "confidence_threshold": config.confidence_threshold,
                "pause_threshold_seconds": config.pause_threshold_seconds,
                "scroll_speed_multiplier": config.scroll_speed_multiplier,
                "audio_source": config.audio_source
            }
        }
        await manager.broadcast_to_all_instances(response, channel)
        
    except Exception as e:
        logger.error(f"Error handling AI scrolling config: {e}")

async def handle_ai_scrolling_start(channel: str, message: dict, websocket: WebSocket):
    """Handle AI scrolling session start"""
    try:
        script_content = message.get("script_content", "")
        config_data = message.get("config", {})
        
        config = AIScrollingConfig(
            enabled=True,
            look_ahead_chars=config_data.get("look_ahead_chars", 100),
            look_behind_chars=config_data.get("look_behind_chars", 50),
            confidence_threshold=config_data.get("confidence_threshold", 0.7),
            pause_threshold_seconds=config_data.get("pause_threshold_seconds", 3.0),
            scroll_speed_multiplier=config_data.get("scroll_speed_multiplier", 1.0),
            audio_source=config_data.get("audio_source", "controller")
        )
        
        ai_scrolling_service.create_session(channel, script_content, config)
        
        # Notify all clients that AI scrolling has started
        response = {
            "type": "ai_scrolling_started",
            "channel": channel
        }
        await manager.broadcast_to_all_instances(response, channel)
        
    except Exception as e:
        logger.error(f"Error starting AI scrolling: {e}")
        error_response = {
            "type": "ai_scrolling_error",
            "error": str(e)
        }
        await websocket.send_text(json.dumps(error_response))

async def handle_ai_scrolling_stop(channel: str, message: dict, websocket: WebSocket):
    """Handle AI scrolling session stop"""
    try:
        ai_scrolling_service.remove_session(channel)
        
        # Notify all clients that AI scrolling has stopped
        response = {
            "type": "ai_scrolling_stopped",
            "channel": channel
        }
        await manager.broadcast_to_all_instances(response, channel)
        
    except Exception as e:
        logger.error(f"Error stopping AI scrolling: {e}")

async def handle_audio_chunk(channel: str, message: dict, websocket: WebSocket):
    """Handle audio chunk for speech recognition"""
    try:
        # Extract audio data (base64 encoded)
        audio_data_b64 = message.get("audio_data", "")
        if not audio_data_b64:
            return
        
        import base64
        audio_data = base64.b64decode(audio_data_b64)
        
        # Process audio chunk
        scroll_command = await ai_scrolling_service.process_audio_chunk(channel, audio_data)
        
        if scroll_command:
            # Send scroll command to all clients
            await manager.broadcast_to_all_instances(scroll_command, channel)
        
        # Check for pause detection
        pause_command = await ai_scrolling_service.check_pause_detection(channel)
        if pause_command:
            await manager.broadcast_to_all_instances(pause_command, channel)
            
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")

@app.get("/api/channel/{channel}/info")
async def get_channel_info(channel: str):
    """Get information about a specific channel"""
    return manager.get_channel_info(channel)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy", 
        "active_channels": len(manager.active_connections)
    }
    
    # Add Redis health information
    redis_health = await redis_manager.health_check()
    health_status.update(redis_health)
    
    return health_status

@app.get("/api/channel/{channel}/ai-scrolling")
async def get_ai_scrolling_info(channel: str):
    """Get AI scrolling information for a channel"""
    session_info = ai_scrolling_service.get_session_info(channel)
    if session_info:
        return session_info
    else:
        return {"enabled": False, "available": ai_scrolling_service.is_available()}

@app.post("/api/channel/{channel}/ai-scrolling/config")
async def update_ai_scrolling_config(channel: str, config: dict):
    """Update AI scrolling configuration for a channel"""
    try:
        ai_config = AIScrollingConfig(
            enabled=config.get("enabled", False),
            look_ahead_chars=config.get("look_ahead_chars", 100),
            look_behind_chars=config.get("look_behind_chars", 50),
            confidence_threshold=config.get("confidence_threshold", 0.7),
            pause_threshold_seconds=config.get("pause_threshold_seconds", 3.0),
            scroll_speed_multiplier=config.get("scroll_speed_multiplier", 1.0),
            audio_source=config.get("audio_source", "controller")
        )
        
        ai_scrolling_service.update_config(channel, ai_config)
        return {"success": True, "message": "AI scrolling configuration updated"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)