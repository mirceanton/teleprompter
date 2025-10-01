"""
Redis Pub/Sub Manager for Remote Teleprompter
Handles Redis connections and pub/sub messaging for cross-instance communication.
"""

import asyncio
import json
import logging
import os
from typing import Callable, Optional, Awaitable
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)


class RedisManager:
    """Manages Redis connections and pub/sub for cross-instance communication"""

    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.is_connected = False
        self.message_handler: Optional[Callable[[dict], Awaitable[None]]] = None

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_password = os.getenv("REDIS_PASSWORD")

    async def connect(self) -> bool:
        """Initialize Redis connection"""
        try:
            # Connect using individual parameters
            self.redis_client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                retry_on_timeout=True,
            )

            # Test the connection
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.is_connected = True
            logger.info("Redis connection established successfully")
            return True

        except (ConnectionError, TimeoutError) as e:
            logger.error(f"Redis connection failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connections"""
        try:
            if self.pubsub:
                await self.pubsub.unsubscribe()
                await self.pubsub.close()

            if self.redis_client:
                await self.redis_client.close()

            self.is_connected = False
            logger.info("Redis connections closed")

        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}")

    def get_channel_name(self, channel: str) -> str:
        """Get Redis channel name for a teleprompter channel"""
        return f"room:{channel}"

    async def publish_message(self, channel: str, message: dict) -> bool:
        """
        Publish a message to a Redis channel.

        Args:
            channel: Teleprompter channel name
            message: Message dictionary to publish

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            logger.error("Redis client not initialized. Cannot publish message.")
            return False

        try:
            redis_channel = self.get_channel_name(channel)
            message_json = json.dumps(message)
            await self.redis_client.publish(redis_channel, message_json)
            return True

        except Exception as e:
            logger.error(f"Error publishing message to Redis: {e}")
            return False

    def set_message_handler(self, handler: Callable[[dict], Awaitable[None]]):
        """
        Set the message handler for incoming Redis messages.

        Args:
            handler: Async callable that processes incoming messages
        """
        self.message_handler = handler
        logger.info("Redis message handler registered")

    async def start_message_listener(self):
        """Start the Redis message listener loop"""
        if not self.is_connected:
            logger.warning("Cannot start message listener: Redis not connected")
            return

        if not self.message_handler:
            logger.warning("No message handler set. Messages will be ignored.")

        logger.info("Starting Redis message listener")

        try:
            # Subscribe to all room channels using pattern matching
            await self.pubsub.psubscribe("room:*")
            logger.info("Subscribed to Redis pattern: room:*")

            async for message in self.pubsub.listen():
                if message["type"] == "pmessage":
                    await self._handle_pattern_message(message)

        except asyncio.CancelledError:
            logger.info("Redis message listener cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in Redis message listener: {e}")
            logger.exception("Full traceback:")

    async def _handle_pattern_message(self, redis_message):
        """Handle incoming Redis pattern messages"""
        try:
            channel = redis_message["channel"]
            data = redis_message["data"]

            # Parse the message
            message = json.loads(data)

            # Extract the teleprompter channel from the Redis channel name
            # Redis channel format: "room:channel_name"
            if channel.startswith("room:"):
                teleprompter_channel = channel[5:]  # Remove "room:" prefix
                message["_teleprompter_channel"] = teleprompter_channel

                # Call the registered message handler
                if self.message_handler:
                    await self.message_handler(message)
                else:
                    logger.warning(
                        f"Received message but no handler registered: {message.get('type', 'unknown')}"
                    )
            else:
                logger.warning(f"Invalid Redis channel format: {channel}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Redis message: {e}")
        except Exception as e:
            logger.error(f"Error handling Redis pattern message: {e}")
            logger.exception("Full traceback:")

    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.is_connected

    async def health_check(self) -> dict:
        """Health check for Redis connection"""
        if not self.is_connected:
            return {"status": "disconnected", "available": False}

        try:
            await self.redis_client.ping()
            return {
                "status": "healthy",
                "available": True,
                "handler_registered": self.message_handler is not None,
            }
        except Exception as e:
            return {"status": "error", "available": False, "error": str(e)}


# Global Redis manager instance
redis_manager = RedisManager()
