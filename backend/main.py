"""
Remote Teleprompter API Backend
FastAPI backend providing WebSocket communication and API endpoints for teleprompter microservices.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import logging
import secrets
import string
from typing import Dict, Set, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
from ai_scrolling import ai_scrolling_service, AIScrollingConfig
from redis_manager import redis_manager

app = FastAPI(title="Remote Teleprompter API", openapi_url="/api/openapi.json", docs_url="/api/docs")

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

# Initialize services on startup
@app.on_event("startup")
async def startup_event():
    await ai_scrolling_service.initialize()
    # Initialize Redis connection
    redis_connected = await redis_manager.connect()
    if redis_connected:
        # Start the Redis message listener in the background
        listener_task = asyncio.create_task(redis_manager.start_message_listener())
        # Store the task to prevent it from being garbage collected
        app.state.redis_listener_task = listener_task
        logger.info("Redis Pub/Sub enabled for horizontal scaling")
    else:
        logger.warning("Running in local-only mode (Redis unavailable)")

@app.on_event("shutdown")
async def shutdown_event():
    await redis_manager.disconnect()

# Store active connections by channel with Redis Pub/Sub support

@dataclass
class RoomParticipant:
    """Represents a participant in a room"""
    websocket: WebSocket
    mode: str  # 'controller' or 'teleprompter'
    participant_id: str

@dataclass 
class Room:
    """Represents a teleprompter room"""
    room_id: str
    secret: str
    controller_id: Optional[str] = None
    participants: Dict[str, RoomParticipant] = None
    
    def __post_init__(self):
        if self.participants is None:
            self.participants = {}

class RoomManager:
    """Manages teleprompter rooms and authentication"""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
    
    def generate_room_id(self) -> str:
        """Generate a unique room ID"""
        while True:
            room_id = 'room-' + ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(6))
            if room_id not in self.rooms:
                return room_id
    
    def generate_secret(self) -> str:
        """Generate a room secret/join code"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    
    def create_room(self) -> Room:
        """Create a new room with generated ID and secret"""
        room_id = self.generate_room_id()
        secret = self.generate_secret()
        room = Room(room_id=room_id, secret=secret)
        self.rooms[room_id] = room
        logger.info(f"Created room {room_id} with secret {secret}")
        return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return self.rooms.get(room_id)
    
    def authenticate_room(self, room_id: str, secret: str) -> bool:
        """Verify room credentials"""
        room = self.get_room(room_id)
        return room is not None and room.secret == secret
    
    def add_participant(self, room_id: str, websocket: WebSocket, mode: str, participant_id: str) -> bool:
        """Add participant to room"""
        room = self.get_room(room_id)
        if not room:
            return False
        
        participant = RoomParticipant(websocket=websocket, mode=mode, participant_id=participant_id)
        room.participants[participant_id] = participant
        
        # Set controller if this is the first controller
        if mode == 'controller' and not room.controller_id:
            room.controller_id = participant_id
        
        logger.info(f"Added {mode} participant {participant_id} to room {room_id}")
        return True
    
    def remove_participant(self, room_id: str, participant_id: str) -> bool:
        """Remove participant from room"""
        room = self.get_room(room_id)
        if not room or participant_id not in room.participants:
            return False
        
        participant = room.participants.pop(participant_id)
        
        # Clear controller if this was the controller
        if room.controller_id == participant_id:
            room.controller_id = None
            # Promote another controller if available
            for pid, p in room.participants.items():
                if p.mode == 'controller':
                    room.controller_id = pid
                    break
        
        # Remove room if empty
        if not room.participants:
            del self.rooms[room_id]
            logger.info(f"Removed empty room {room_id}")
        else:
            logger.info(f"Removed participant {participant_id} from room {room_id}")
        
        return True
    
    def get_participant_by_websocket(self, websocket: WebSocket) -> Optional[tuple[str, str]]:
        """Find room_id and participant_id by websocket"""
        for room_id, room in self.rooms.items():
            for participant_id, participant in room.participants.items():
                if participant.websocket == websocket:
                    return room_id, participant_id
        return None
    
    def kick_participant(self, room_id: str, participant_id: str, kicker_id: str) -> bool:
        """Kick a participant from the room (only controller can kick)"""
        room = self.get_room(room_id)
        if not room or room.controller_id != kicker_id:
            return False
        
        if participant_id in room.participants and participant_id != kicker_id:
            participant = room.participants[participant_id]
            # Close the websocket connection
            asyncio.create_task(participant.websocket.close())
            self.remove_participant(room_id, participant_id)
            return True
        
        return False

room_manager = RoomManager()

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

@app.websocket("/api/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """WebSocket endpoint for real-time communication with room authentication"""
    
    # Wait for authentication message
    await websocket.accept()
    
    try:
        # First message must be authentication
        auth_data = await websocket.receive_text()
        auth_message = json.loads(auth_data)
        
        if auth_message.get('type') != 'authenticate':
            await websocket.send_text(json.dumps({
                "type": "auth_error", 
                "message": "First message must be authentication"
            }))
            await websocket.close()
            return
        
        room_id = auth_message.get('room_id', channel)  # Support both for backward compatibility
        secret = auth_message.get('secret')
        mode = auth_message.get('mode', 'teleprompter')
        participant_id = secrets.token_urlsafe(8)
        
        # Verify room credentials
        if not room_manager.authenticate_room(room_id, secret):
            await websocket.send_text(json.dumps({
                "type": "auth_error", 
                "message": "Invalid room credentials"
            }))
            await websocket.close()
            return
        
        # Add participant to room
        if not room_manager.add_participant(room_id, websocket, mode, participant_id):
            await websocket.send_text(json.dumps({
                "type": "auth_error", 
                "message": "Failed to join room"
            }))
            await websocket.close()
            return
        
        # Send authentication success
        room = room_manager.get_room(room_id)
        await websocket.send_text(json.dumps({
            "type": "auth_success",
            "room_id": room_id,
            "participant_id": participant_id,
            "mode": mode,
            "is_controller": room.controller_id == participant_id
        }))
        
        # Connect to legacy connection manager for backward compatibility
        await manager.connect(websocket, room_id)
        
        # Send connection count update to all clients in channel
        connection_info = manager.get_channel_info(room_id)
        room_info = {
            "type": "room_update",
            "room_id": room_id,
            "participant_count": len(room.participants),
            "participants": [
                {
                    "participant_id": pid,
                    "mode": p.mode,
                    "is_controller": pid == room.controller_id
                } for pid, p in room.participants.items()
            ]
        }
        await manager.broadcast_to_all_instances(room_info, room_id)
        
        # Main message handling loop
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Add participant info to message
            message['participant_id'] = participant_id
            message['mode'] = mode
            
            # Log the message type for debugging
            print(f"Channel {room_id}: Received {message.get('type', 'unknown')} message from {mode} {participant_id}")
            
            # Handle special messages
            message_type = message.get('type')
            
            if message_type == 'request_connection_info':
                # Send current room info to requesting client
                room_update_str = json.dumps(room_info)
                await websocket.send_text(room_update_str)
            elif message_type == 'kick_participant':
                # Handle participant kick (only controller can kick)
                target_participant_id = message.get('target_participant_id')
                if room_manager.kick_participant(room_id, target_participant_id, participant_id):
                    # Broadcast kick notification
                    kick_message = {
                        "type": "participant_kicked",
                        "participant_id": target_participant_id,
                        "kicked_by": participant_id
                    }
                    await manager.broadcast_to_all_instances(kick_message, room_id)
            elif message_type == 'ai_scrolling_config':
                # Handle AI scrolling configuration
                await handle_ai_scrolling_config(room_id, message, websocket)
            elif message_type == 'audio_chunk':
                # Handle audio chunk for AI scrolling
                await handle_audio_chunk(room_id, message, websocket)
            elif message_type == 'ai_scrolling_start':
                # Start AI scrolling session
                await handle_ai_scrolling_start(room_id, message, websocket)
            elif message_type == 'ai_scrolling_stop':
                # Stop AI scrolling session
                await handle_ai_scrolling_stop(room_id, message, websocket)
            else:
                # Broadcast to all other clients in the same channel across all instances
                await manager.broadcast_to_all_instances(message, room_id, exclude=websocket)
            
    except WebSocketDisconnect:
        # Clean up participant
        room_participant_info = room_manager.get_participant_by_websocket(websocket)
        if room_participant_info:
            room_id, participant_id = room_participant_info
            room_manager.remove_participant(room_id, participant_id)
            manager.disconnect(websocket, room_id)
            
            # Clean up AI scrolling session if needed
            ai_scrolling_service.remove_session(room_id)
            
            # Broadcast updated room info
            room = room_manager.get_room(room_id)
            if room:
                room_info = {
                    "type": "room_update",
                    "room_id": room_id,
                    "participant_count": len(room.participants),
                    "participants": [
                        {
                            "participant_id": pid,
                            "mode": p.mode,
                            "is_controller": pid == room.controller_id
                        } for pid, p in room.participants.items()
                    ]
                }
                await manager.broadcast_to_all_instances(room_info, room_id)
    except Exception as e:
        print(f"Error in room {channel}: {e}")
        # Clean up participant
        room_participant_info = room_manager.get_participant_by_websocket(websocket)
        if room_participant_info:
            room_id, participant_id = room_participant_info
            room_manager.remove_participant(room_id, participant_id)
            manager.disconnect(websocket, room_id)
            
            # Clean up AI scrolling session if needed
            ai_scrolling_service.remove_session(room_id)
            
            # Broadcast updated room info  
            room = room_manager.get_room(room_id)
            if room:
                room_info = {
                    "type": "room_update",
                    "room_id": room_id,
                    "participant_count": len(room.participants),
                    "participants": [
                        {
                            "participant_id": pid,
                            "mode": p.mode,
                            "is_controller": pid == room.controller_id
                        } for pid, p in room.participants.items()
                    ]
                }
                await manager.broadcast_to_all_instances(room_info, room_id)

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

@app.post("/api/rooms")
async def create_room():
    """Create a new room"""
    room = room_manager.create_room()
    return {
        "room_id": room.room_id,
        "secret": room.secret,
        "join_url": f"/teleprompter?room={room.room_id}&secret={room.secret}"
    }

@app.get("/api/rooms/{room_id}")
async def get_room_info(room_id: str):
    """Get room information"""
    room = room_manager.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    return {
        "room_id": room.room_id,
        "participant_count": len(room.participants),
        "controller_id": room.controller_id,
        "participants": [
            {
                "participant_id": pid,
                "mode": p.mode,
                "is_controller": pid == room.controller_id
            } for pid, p in room.participants.items()
        ]
    }

@app.post("/api/rooms/{room_id}/verify")
async def verify_room_credentials(room_id: str, credentials: dict):
    """Verify room credentials"""
    secret = credentials.get('secret')
    if not secret:
        raise HTTPException(status_code=400, detail="Secret required")
    
    if room_manager.authenticate_room(room_id, secret):
        room = room_manager.get_room(room_id)
        return {
            "valid": True,
            "room_id": room_id,
            "participant_count": len(room.participants) if room else 0
        }
    else:
        return {"valid": False}

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