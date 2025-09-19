#!/usr/bin/env python3
"""
Whisper Scroller Service for Remote Teleprompter
Separate service dedicated to AI-assisted scrolling using speech recognition.
"""

import asyncio
import json
import logging
import sys
import os
from typing import Dict, Optional
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException
from ai_scrolling import AIScrollingService, AIScrollingConfig

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WhisperScrollerService:
    """Separate AI scrolling service that connects to the main backend via WebSocket"""
    
    def __init__(self, backend_url: str = "ws://localhost:8001", service_id: str = "whisper_scroller"):
        self.backend_url = backend_url
        self.service_id = service_id
        self.websocket = None
        self.channels: Dict[str, Dict] = {}
        self.ai_service = AIScrollingService()
        self.running = False
        
    async def initialize(self):
        """Initialize the AI scrolling service"""
        success = await self.ai_service.initialize()
        if success:
            logger.info("AI scrolling service initialized successfully")
        else:
            logger.warning("AI scrolling service running in mock mode")
        return True
    
    async def connect_to_channel(self, channel_name: str):
        """Connect to a specific channel on the main backend"""
        try:
            ws_url = f"{self.backend_url}/api/ws/{channel_name}"
            logger.info(f"Connecting to channel {channel_name} at {ws_url}")
            
            self.websocket = await websockets.connect(ws_url)
            
            # Announce ourselves as the AI scroller
            await self.send_message({
                "type": "mode",
                "mode": "ai_scroller",
                "service_id": self.service_id
            })
            
            self.channels[channel_name] = {
                "websocket": self.websocket,
                "active": True
            }
            
            logger.info(f"Connected to channel {channel_name} as AI scroller")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to channel {channel_name}: {e}")
            return False
    
    async def send_message(self, message: dict):
        """Send a message to the backend"""
        if self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Error sending message: {e}")
    
    async def handle_message(self, message: dict, channel_name: str):
        """Handle messages received from the backend"""
        message_type = message.get("type")
        
        try:
            if message_type == "audio_chunk":
                await self.handle_audio_chunk(message, channel_name)
            elif message_type == "ai_scrolling_start":
                await self.handle_ai_scrolling_start(message, channel_name)
            elif message_type == "ai_scrolling_stop":
                await self.handle_ai_scrolling_stop(message, channel_name)
            elif message_type == "ai_scrolling_config":
                await self.handle_ai_scrolling_config(message, channel_name)
            else:
                logger.debug(f"Ignoring message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling message {message_type}: {e}")
    
    async def handle_audio_chunk(self, message: dict, channel_name: str):
        """Process audio chunk and determine scroll position"""
        try:
            # Extract audio data (base64 encoded)
            audio_data_b64 = message.get("audio_data", "")
            if not audio_data_b64:
                return
            
            import base64
            audio_data = base64.b64decode(audio_data_b64)
            
            # Process audio chunk using AI service
            scroll_command = await self.ai_service.process_audio_chunk(channel_name, audio_data)
            
            if scroll_command:
                # Send scroll command back to all participants
                await self.send_message(scroll_command)
            
            # Check for pause detection
            pause_command = await self.ai_service.check_pause_detection(channel_name)
            if pause_command:
                await self.send_message(pause_command)
                
        except Exception as e:
            logger.error(f"Error processing audio chunk: {e}")
    
    async def handle_ai_scrolling_start(self, message: dict, channel_name: str):
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
            
            self.ai_service.create_session(channel_name, script_content, config)
            logger.info(f"AI scrolling session started for channel {channel_name}")
            
        except Exception as e:
            logger.error(f"Error starting AI scrolling session: {e}")
    
    async def handle_ai_scrolling_stop(self, message: dict, channel_name: str):
        """Handle AI scrolling session stop"""
        try:
            self.ai_service.remove_session(channel_name)
            logger.info(f"AI scrolling session stopped for channel {channel_name}")
            
        except Exception as e:
            logger.error(f"Error stopping AI scrolling session: {e}")
    
    async def handle_ai_scrolling_config(self, message: dict, channel_name: str):
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
            
            self.ai_service.update_config(channel_name, config)
            logger.info(f"AI scrolling configuration updated for channel {channel_name}")
            
        except Exception as e:
            logger.error(f"Error updating AI scrolling config: {e}")
    
    async def listen_for_messages(self, channel_name: str):
        """Listen for messages from the backend"""
        websocket = self.channels[channel_name]["websocket"]
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(data, channel_name)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    
        except ConnectionClosed:
            logger.info(f"Connection to channel {channel_name} closed")
        except WebSocketException as e:
            logger.error(f"WebSocket error on channel {channel_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on channel {channel_name}: {e}")
        finally:
            # Clean up channel
            if channel_name in self.channels:
                self.channels[channel_name]["active"] = False
    
    async def run(self, channel_name: str):
        """Run the whisper scroller service for a specific channel"""
        logger.info(f"Starting Whisper Scroller Service for channel: {channel_name}")
        
        # Initialize AI service
        await self.initialize()
        
        # Connect to the channel
        if not await self.connect_to_channel(channel_name):
            logger.error("Failed to connect to backend. Exiting.")
            return
        
        self.running = True
        
        try:
            # Listen for messages
            await self.listen_for_messages(channel_name)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            self.running = False
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources...")
        
        for channel_name, channel_info in self.channels.items():
            websocket = channel_info["websocket"]
            if websocket and not websocket.closed:
                await websocket.close()
        
        self.channels.clear()
        logger.info("Cleanup completed")

async def main():
    """Main entry point for the whisper scroller service"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Whisper Scroller Service for Remote Teleprompter")
    parser.add_argument("--channel", required=True, help="Channel name to connect to")
    parser.add_argument("--backend", default="ws://localhost:8001", help="Backend WebSocket URL")
    parser.add_argument("--service-id", default="whisper_scroller", help="Service identifier")
    
    args = parser.parse_args()
    
    service = WhisperScrollerService(
        backend_url=args.backend,
        service_id=args.service_id
    )
    
    try:
        await service.run(args.channel)
    except Exception as e:
        logger.error(f"Service error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())