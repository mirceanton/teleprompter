"""
Connection Manager for Remote Teleprompter
Handles WebSocket connections and message broadcasting across instances.
"""

import json
import logging
import uuid
from typing import Set, Dict, Optional
from fastapi import WebSocket

from redis_manager import redis_manager

logger = logging.getLogger(__name__)


class Participant:
    """Represents a connected participant"""
    def __init__(self, websocket: WebSocket, role: str = "unknown"):
        self.id = str(uuid.uuid4())
        self.websocket = websocket
        self.role = role  # "controller" or "teleprompter"
        self.joined_at = None


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.participants: Dict[str, Participant] = {}  # participant_id -> Participant
        self.websocket_to_participant: Dict[WebSocket, str] = {}  # websocket -> participant_id
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Create a participant for this connection
        participant = Participant(websocket)
        self.participants[participant.id] = participant
        self.websocket_to_participant[websocket] = participant.id
        
        logger.info(f"Client connected (total: {len(self.active_connections)})")
        return participant.id
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        
        # Remove participant tracking
        if websocket in self.websocket_to_participant:
            participant_id = self.websocket_to_participant[websocket]
            del self.websocket_to_participant[websocket]
            if participant_id in self.participants:
                del self.participants[participant_id]
        
        logger.info(f"Client disconnected (remaining: {len(self.active_connections)})")
    
    def set_participant_role(self, websocket: WebSocket, role: str):
        """Set the role for a participant"""
        if websocket in self.websocket_to_participant:
            participant_id = self.websocket_to_participant[websocket]
            if participant_id in self.participants:
                self.participants[participant_id].role = role
                return participant_id
        return None
    
    def get_participant_list(self) -> list:
        """Get list of all participants with their info"""
        from datetime import datetime
        participants = []
        for participant in self.participants.values():
            participants.append({
                "id": participant.id,
                "role": participant.role,
                "joined_at": datetime.now().isoformat() if participant.joined_at is None else participant.joined_at
            })
        return participants
    
    def get_teleprompter_participants(self) -> list:
        """Get list of teleprompter participants only"""
        return [p for p in self.get_participant_list() if p["role"] == "teleprompter"]
    
    def get_connection_count(self) -> int:
        """Get the number of active connections on this instance"""
        return len(self.active_connections)
    
    async def broadcast_to_local(self, message_str: str, exclude: WebSocket = None, target_participant_id: Optional[str] = None):
        """
        Broadcast message to all local connections or a specific participant.
        
        Args:
            message_str: JSON string to broadcast
            exclude: Optional WebSocket to exclude from broadcast
            target_participant_id: If specified, only send to this participant
        """
        if not self.active_connections:
            return
        
        disconnected = []
        
        # If targeting a specific participant
        if target_participant_id:
            if target_participant_id in self.participants:
                participant = self.participants[target_participant_id]
                if participant.websocket != exclude:
                    try:
                        await participant.websocket.send_text(message_str)
                    except Exception as e:
                        logger.error(f"Error sending to target participant {target_participant_id}: {e}")
                        disconnected.append(participant.websocket)
        else:
            # Broadcast to all connections
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
            self.disconnect(conn)
    
    async def broadcast_to_all_instances(self, message_dict: dict, exclude: WebSocket = None, target_participant_id: Optional[str] = None):
        """
        Broadcast message to all instances via Redis and local connections.
        
        Args:
            message_dict: Message dictionary to broadcast
            exclude: Optional WebSocket to exclude from local broadcast
            target_participant_id: If specified, only send to this participant
        """
        message_str = json.dumps(message_dict)
        
        # Broadcast to local connections first
        await self.broadcast_to_local(message_str, exclude, target_participant_id)
        
        # Publish to Redis for other instances (if available)
        if redis_manager.is_available():
            redis_message = {
                **message_dict,
                "_redis_source": True,  # Mark to avoid message loops
                "_target_participant_id": target_participant_id  # Include target for other instances
            }
            await redis_manager.publish_message("teleprompter", redis_message)
    
    async def handle_redis_message(self, message: dict):
        """
        Handle messages received from Redis Pub/Sub.
        
        Args:
            message: Message dictionary from Redis
        """
        try:
            # Only process messages from other instances
            if message.get('_redis_source'):
                # Extract target participant ID if present
                target_participant_id = message.get('_target_participant_id')
                
                # Remove metadata before broadcasting
                clean_message = {k: v for k, v in message.items() if not k.startswith('_')}
                message_str = json.dumps(clean_message)
                
                # Broadcast to local connections only (with targeting support)
                await self.broadcast_to_local(message_str, target_participant_id=target_participant_id)
                
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")