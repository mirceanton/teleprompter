"""
Connection Manager for Remote Teleprompter
Handles WebSocket connections and message broadcasting across instances.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Optional
from fastapi import WebSocket

from redis_manager import redis_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        # Map of WebSocket to participant info
        self.connections: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket) -> str:
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        participant_id = str(uuid.uuid4())
        self.connections[websocket] = {
            "id": participant_id,
            "role": None,  # Will be set when client sends mode message
            "joined_at": datetime.utcnow().isoformat(),
        }
        logger.info(f"Client connected with id {participant_id} (total: {len(self.connections)})")
        return participant_id

    def disconnect(self, websocket: WebSocket) -> Optional[str]:
        """Remove a WebSocket connection and return participant id"""
        participant_info = self.connections.pop(websocket, None)
        participant_id = participant_info["id"] if participant_info else None
        logger.info(f"Client {participant_id} disconnected (remaining: {len(self.connections)})")
        return participant_id

    def set_participant_role(self, websocket: WebSocket, role: str):
        """Set the role for a participant"""
        if websocket in self.connections:
            self.connections[websocket]["role"] = role
            logger.info(f"Set role '{role}' for participant {self.connections[websocket]['id']}")

    def get_participant_info(self, websocket: WebSocket) -> Optional[dict]:
        """Get participant info for a websocket"""
        return self.connections.get(websocket)

    def get_participant_id(self, websocket: WebSocket) -> Optional[str]:
        """Get participant ID for a websocket"""
        info = self.connections.get(websocket)
        return info["id"] if info else None

    def get_websocket_by_id(self, participant_id: str) -> Optional[WebSocket]:
        """Get websocket for a participant ID"""
        for ws, info in self.connections.items():
            if info["id"] == participant_id:
                return ws
        return None

    def get_all_participants(self) -> list:
        """Get list of all participants"""
        return [info.copy() for info in self.connections.values()]

    def get_teleprompter_participants(self) -> list:
        """Get list of teleprompter participants only"""
        return [info.copy() for info in self.connections.values() if info.get("role") == "teleprompter"]

    def get_connection_count(self) -> int:
        """Get the number of active connections on this instance"""
        return len(self.connections)

    async def broadcast_to_websockets(self, message_str: str, exclude: WebSocket = None):
        """
        Broadcast message to all WebSocket clients connected to this backend instance.

        Args:
            message_str: JSON string to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        if not self.connections:
            return

        disconnected = []

        for websocket in self.connections:
            if websocket == exclude:
                continue

            try:
                await websocket.send_text(message_str)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.append(websocket)

        # Clean up disconnected clients
        for conn in disconnected:
            self.connections.pop(conn, None)

    async def broadcast_to_redis(self, message_dict: dict):
        """
        Broadcast message to Redis pub/sub for other backend instances.

        Args:
            message_dict: Message dictionary to broadcast
        """
        # Mark message with Redis source flag to avoid message loops
        redis_message = {
            **message_dict,
            "_redis_source": True,
        }
        await redis_manager.publish_message("teleprompter", redis_message)

    async def send_to_participant(self, participant_id: str, message_dict: dict):
        """
        Send a message to a specific participant.
        
        Args:
            participant_id: The target participant's ID
            message_dict: Message dictionary to send
        """
        websocket = self.get_websocket_by_id(participant_id)
        if websocket:
            try:
                message_str = json.dumps(message_dict)
                await websocket.send_text(message_str)
                logger.info(f"Sent targeted message to participant {participant_id}")
            except Exception as e:
                logger.error(f"Error sending to participant {participant_id}: {e}")
                self.connections.pop(websocket, None)
        else:
            # Participant might be on another instance, publish via Redis
            targeted_message = {
                **message_dict,
                "_target_participant": participant_id,
            }
            await self.broadcast_to_redis(targeted_message)

    async def broadcast_to_all(
        self, message_dict: dict, exclude: WebSocket = None
    ):
        """
        Broadcast message to all clients across all backend instances.
        
        This method orchestrates both:
        1. WebSocket broadcasting to clients on this instance
        2. Redis pub/sub to reach clients on other backend instances

        Args:
            message_dict: Message dictionary to broadcast
            exclude: Optional WebSocket to exclude from local broadcast
        """
        message_str = json.dumps(message_dict)

        # Broadcast to WebSocket clients on this instance
        await self.broadcast_to_websockets(message_str, exclude)

        # Publish to Redis for other backend instances
        await self.broadcast_to_redis(message_dict)

    async def handle_redis_message(self, message: dict):
        """
        Handle messages received from Redis Pub/Sub.
        
        Relays messages from other backend instances to WebSocket clients on this instance.

        Args:
            message: Message dictionary from Redis
        """
        try:
            # Only process messages from other instances
            if message.get("_redis_source"):
                target_participant = message.get("_target_participant")
                
                # Remove metadata before broadcasting
                clean_message = {
                    k: v for k, v in message.items() if not k.startswith("_")
                }
                message_str = json.dumps(clean_message)

                if target_participant:
                    # Targeted message - send only to specific participant
                    websocket = self.get_websocket_by_id(target_participant)
                    if websocket:
                        try:
                            await websocket.send_text(message_str)
                            logger.info(f"Delivered targeted Redis message to participant {target_participant}")
                        except Exception as e:
                            logger.error(f"Error sending to participant {target_participant}: {e}")
                            self.connections.pop(websocket, None)
                else:
                    # Broadcast to all WebSocket clients on this instance
                    await self.broadcast_to_websockets(message_str)

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
