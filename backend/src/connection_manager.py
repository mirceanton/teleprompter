"""
Connection Manager for Remote Teleprompter
Handles WebSocket connections and message broadcasting across instances.
"""

import json
import logging
from typing import Set
from fastapi import WebSocket

from redis_manager import redis_manager

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and message broadcasting"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"Client connected (total: {len(self.active_connections)})")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        self.active_connections.discard(websocket)
        logger.info(f"Client disconnected (remaining: {len(self.active_connections)})")

    def get_connection_count(self) -> int:
        """Get the number of active connections on this instance"""
        return len(self.active_connections)

    async def broadcast_to_websockets(self, message_str: str, exclude: WebSocket = None):
        """
        Broadcast message to all WebSocket clients connected to this backend instance.

        Args:
            message_str: JSON string to broadcast
            exclude: Optional WebSocket to exclude from broadcast
        """
        if not self.active_connections:
            return

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
                # Remove metadata before broadcasting
                clean_message = {
                    k: v for k, v in message.items() if not k.startswith("_")
                }
                message_str = json.dumps(clean_message)

                # Broadcast to WebSocket clients on this instance
                await self.broadcast_to_websockets(message_str)

        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
