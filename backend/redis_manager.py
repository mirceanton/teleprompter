"""
Redis Pub/Sub Manager for Remote Teleprompter
Handles Redis connections and pub/sub messaging for cross-instance communication.
"""

import asyncio
import json
import logging
import os
from typing import Callable, Optional, Dict, Any
import redis.asyncio as redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

class RedisManager:
    """Manages Redis connections and pub/sub for cross-instance communication"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None
        self.subscribed_channels: set = set()
        self.message_handlers: Dict[str, Callable] = {}
        self.is_connected = False
        
        # Redis configuration from environment variables
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_password = os.getenv('REDIS_PASSWORD')
        
    async def connect(self) -> bool:
        """Initialize Redis connection"""
        try:
            # Try to connect using URL first, then individual parameters
            if self.redis_url and self.redis_url != 'redis://localhost:6379':
                self.redis_client = redis.from_url(
                    self.redis_url,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    retry_on_timeout=True
                )
            else:
                self.redis_client = redis.Redis(
                    host=self.redis_host,
                    port=self.redis_port,
                    db=self.redis_db,
                    password=self.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    retry_on_timeout=True
                )
            
            # Test the connection
            await self.redis_client.ping()
            self.pubsub = self.redis_client.pubsub()
            self.is_connected = True
            logger.info("Redis connection established successfully")
            return True
            
        except (ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection failed: {e}. Running in local-only mode.")
            self.is_connected = False
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to Redis: {e}")
            self.is_connected = False
            return False
    
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
        """Publish a message to a Redis channel"""
        if not self.is_connected:
            return False
            
        try:
            redis_channel = self.get_channel_name(channel)
            message_json = json.dumps(message)
            await self.redis_client.publish(redis_channel, message_json)
            logger.debug(f"Published message to Redis channel {redis_channel}: {message.get('type', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing message to Redis: {e}")
            return False
    
    async def subscribe_to_channel(self, channel: str, message_handler: Callable[[dict], None]):
        """Subscribe to a Redis channel and register a message handler"""
        if not self.is_connected:
            logger.warning(f"Cannot subscribe to channel {channel}: Redis not connected")
            return False
            
        try:
            redis_channel = self.get_channel_name(channel)
            
            if redis_channel not in self.subscribed_channels:
                await self.pubsub.subscribe(redis_channel)
                self.subscribed_channels.add(redis_channel)
                logger.info(f"Subscribed to Redis channel: {redis_channel}")
            
            self.message_handlers[redis_channel] = message_handler
            return True
            
        except Exception as e:
            logger.error(f"Error subscribing to Redis channel: {e}")
            return False
    
    async def unsubscribe_from_channel(self, channel: str):
        """Unsubscribe from a Redis channel"""
        if not self.is_connected:
            return
            
        try:
            redis_channel = self.get_channel_name(channel)
            
            if redis_channel in self.subscribed_channels:
                await self.pubsub.unsubscribe(redis_channel)
                self.subscribed_channels.discard(redis_channel)
                self.message_handlers.pop(redis_channel, None)
                logger.info(f"Unsubscribed from Redis channel: {redis_channel}")
                
        except Exception as e:
            logger.error(f"Error unsubscribing from Redis channel: {e}")
    
    async def start_message_listener(self):
        """Start the Redis message listener loop"""
        if not self.is_connected:
            logger.warning("Cannot start message listener: Redis not connected")
            return
            
        logger.info("Starting Redis message listener")
        
        try:
            async for message in self.pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_redis_message(message)
                    
        except Exception as e:
            logger.error(f"Error in Redis message listener: {e}")
    
    async def _handle_redis_message(self, redis_message):
        """Handle incoming Redis messages"""
        try:
            channel = redis_message['channel']
            data = redis_message['data']
            
            # Parse the message
            message = json.loads(data)
            
            # Extract the teleprompter channel from the Redis channel name
            # Redis channel format: "room:channel_name"
            if channel.startswith('room:'):
                teleprompter_channel = channel[5:]  # Remove "room:" prefix
                
                # Find and call the appropriate handler
                handler = self.message_handlers.get(channel)
                if handler:
                    # Add channel info to message for the handler
                    message['_teleprompter_channel'] = teleprompter_channel
                    await handler(message)
                else:
                    logger.warning(f"No handler found for Redis channel: {channel}")
            else:
                logger.warning(f"Invalid Redis channel format: {channel}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in Redis message: {e}")
        except Exception as e:
            logger.error(f"Error handling Redis message: {e}")
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        return self.is_connected
    
    async def health_check(self) -> dict:
        """Health check for Redis connection"""
        if not self.is_connected:
            return {"redis": {"status": "disconnected", "available": False}}
            
        try:
            await self.redis_client.ping()
            return {
                "redis": {
                    "status": "healthy", 
                    "available": True,
                    "subscribed_channels": len(self.subscribed_channels)
                }
            }
        except Exception as e:
            return {
                "redis": {
                    "status": "error", 
                    "available": False, 
                    "error": str(e)
                }
            }

# Global Redis manager instance
redis_manager = RedisManager()