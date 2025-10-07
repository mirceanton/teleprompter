"""
OBS Bridge Service for Remote Teleprompter
Connects teleprompter WebSocket to OBS Studio for automated recording control.
"""

import os
import json
import asyncio
import logging
from typing import Optional
from datetime import datetime

import websockets
from obswebsocket import obsws, requests as obs_requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OBSBridge:
    """Bridge between teleprompter WebSocket and OBS Studio"""
    
    def __init__(self):
        # Configuration from environment variables
        self.backend_ws_url = os.getenv("BACKEND_WS_URL", "ws://localhost:8001/api/ws")
        self.obs_host = os.getenv("OBS_HOST", "host.docker.internal")
        self.obs_port = int(os.getenv("OBS_PORT", "4455"))
        self.obs_password = os.getenv("OBS_PASSWORD", "")
        
        # Connection state
        self.teleprompter_ws: Optional[websockets.WebSocketClientProtocol] = None
        self.obs_client: Optional[obsws] = None
        self.obs_connected = False
        self.teleprompter_connected = False
        
        # OBS state
        self.is_recording = False
        self.is_streaming = False
        
        # Reconnection settings
        self.reconnect_delay = 1  # Start with 1 second
        self.max_reconnect_delay = 60  # Max 60 seconds
        
        # Configuration from controller
        self.auto_start_recording = False
        self.auto_stop_recording = False
        self.auto_pause_recording = False
        
    async def connect_to_obs(self) -> bool:
        """Connect to OBS WebSocket with retry logic"""
        try:
            logger.info(f"Connecting to OBS at {self.obs_host}:{self.obs_port}")
            self.obs_client = obsws(self.obs_host, self.obs_port, self.obs_password)
            self.obs_client.connect()
            
            # Get initial recording status
            status = self.obs_client.call(obs_requests.GetRecordStatus())
            self.is_recording = status.getOutputActive()
            
            # Get initial streaming status
            stream_status = self.obs_client.call(obs_requests.GetStreamStatus())
            self.is_streaming = stream_status.getOutputActive()
            
            self.obs_connected = True
            self.reconnect_delay = 1  # Reset reconnection delay on success
            logger.info("Connected to OBS successfully")
            
            # Broadcast connection status
            await self.broadcast_obs_status("connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.obs_connected = False
            await self.broadcast_obs_status("disconnected", error=str(e))
            return False
    
    async def connect_to_teleprompter(self):
        """Connect to teleprompter WebSocket with retry logic"""
        while True:
            try:
                logger.info(f"Connecting to teleprompter at {self.backend_ws_url}")
                async with websockets.connect(self.backend_ws_url) as websocket:
                    self.teleprompter_ws = websocket
                    self.teleprompter_connected = True
                    self.reconnect_delay = 1  # Reset reconnection delay
                    
                    logger.info("Connected to teleprompter successfully")
                    
                    # Send mode identification
                    await self.send_message({"type": "mode", "mode": "obs_bridge"})
                    
                    # Send initial OBS status
                    await self.broadcast_obs_status(
                        "connected" if self.obs_connected else "disconnected"
                    )
                    
                    # Message handling loop
                    async for message_text in websocket:
                        try:
                            message = json.loads(message_text)
                            await self.handle_teleprompter_message(message)
                        except json.JSONDecodeError:
                            logger.error(f"Invalid JSON from teleprompter: {message_text}")
                        except Exception as e:
                            logger.error(f"Error handling message: {e}")
                            
            except websockets.exceptions.ConnectionClosed:
                logger.warning("Teleprompter WebSocket connection closed")
            except Exception as e:
                logger.error(f"Teleprompter connection error: {e}")
            
            # Connection lost, prepare to reconnect
            self.teleprompter_connected = False
            self.teleprompter_ws = None
            
            logger.info(f"Reconnecting to teleprompter in {self.reconnect_delay}s...")
            await asyncio.sleep(self.reconnect_delay)
            
            # Exponential backoff
            self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
    
    async def handle_teleprompter_message(self, message: dict):
        """Handle incoming messages from teleprompter"""
        message_type = message.get("type")
        
        # Ignore messages from ourselves
        if message.get("_sender") == "obs_bridge":
            return
        
        logger.debug(f"Received message: {message_type}")
        
        if message_type == "start":
            await self.handle_start_message(message)
        elif message_type == "pause":
            await self.handle_pause_message()
        elif message_type == "reset":
            await self.handle_reset_message()
        elif message_type == "obs_config":
            await self.handle_obs_config(message)
    
    async def handle_start_message(self, message: dict):
        """Handle start playback message"""
        if not self.obs_connected:
            logger.warning("Start message received but OBS not connected")
            return
        
        wait_for_obs = message.get("waitForOBS", False)
        countdown = message.get("countdown", 0)
        
        if self.auto_start_recording and not self.is_recording:
            try:
                logger.info("Starting OBS recording")
                self.obs_client.call(obs_requests.StartRecord())
                self.is_recording = True
                
                await self.broadcast_obs_status("recording_started")
                
                # If controller is waiting for confirmation, send it
                if wait_for_obs:
                    await self.send_message({
                        "type": "obs_recording_confirmed",
                        "_sender": "obs_bridge"
                    })
                
            except Exception as e:
                logger.error(f"Failed to start OBS recording: {e}")
                await self.broadcast_obs_status("recording_failed", error=str(e))
    
    async def handle_pause_message(self):
        """Handle pause playback message"""
        if not self.obs_connected:
            return
        
        if self.auto_pause_recording and self.is_recording:
            try:
                logger.info("Pausing OBS recording")
                self.obs_client.call(obs_requests.PauseRecord())
                await self.broadcast_obs_status("recording_paused")
            except Exception as e:
                logger.error(f"Failed to pause OBS recording: {e}")
    
    async def handle_reset_message(self):
        """Handle reset/stop playback message"""
        if not self.obs_connected:
            return
        
        if self.auto_stop_recording and self.is_recording:
            try:
                logger.info("Stopping OBS recording")
                self.obs_client.call(obs_requests.StopRecord())
                self.is_recording = False
                await self.broadcast_obs_status("recording_stopped")
            except Exception as e:
                logger.error(f"Failed to stop OBS recording: {e}")
    
    async def handle_obs_config(self, message: dict):
        """Handle OBS configuration updates from controller"""
        self.auto_start_recording = message.get("autoStart", False)
        self.auto_stop_recording = message.get("autoStop", False)
        self.auto_pause_recording = message.get("autoPause", False)
        
        logger.info(f"OBS config updated: autoStart={self.auto_start_recording}, "
                   f"autoStop={self.auto_stop_recording}, autoPause={self.auto_pause_recording}")
    
    async def send_message(self, message: dict):
        """Send message to teleprompter WebSocket"""
        if self.teleprompter_ws and self.teleprompter_connected:
            try:
                await self.teleprompter_ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to teleprompter: {e}")
    
    async def broadcast_obs_status(self, status: str, error: Optional[str] = None):
        """Broadcast OBS status to all teleprompter clients"""
        message = {
            "type": "obs_status",
            "status": status,
            "connected": self.obs_connected,
            "recording": self.is_recording,
            "streaming": self.is_streaming,
            "timestamp": datetime.utcnow().isoformat(),
            "_sender": "obs_bridge"
        }
        
        if error:
            message["error"] = error
        
        await self.send_message(message)
    
    async def monitor_obs_status(self):
        """Periodically check OBS status and broadcast changes"""
        while True:
            await asyncio.sleep(2)  # Check every 2 seconds
            
            if not self.obs_connected:
                # Try to reconnect to OBS
                await self.connect_to_obs()
                continue
            
            try:
                # Check recording status
                status = self.obs_client.call(obs_requests.GetRecordStatus())
                new_recording_state = status.getOutputActive()
                
                if new_recording_state != self.is_recording:
                    self.is_recording = new_recording_state
                    status_msg = "recording_started" if new_recording_state else "recording_stopped"
                    await self.broadcast_obs_status(status_msg)
                
                # Check streaming status
                stream_status = self.obs_client.call(obs_requests.GetStreamStatus())
                new_streaming_state = stream_status.getOutputActive()
                
                if new_streaming_state != self.is_streaming:
                    self.is_streaming = new_streaming_state
                    await self.broadcast_obs_status("status_update")
                    
            except Exception as e:
                logger.error(f"Error checking OBS status: {e}")
                self.obs_connected = False
                await self.broadcast_obs_status("disconnected", error=str(e))
    
    async def run(self):
        """Main run loop"""
        logger.info("Starting OBS Bridge service")
        
        # Try initial OBS connection
        await self.connect_to_obs()
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self.connect_to_teleprompter()),
            asyncio.create_task(self.monitor_obs_status())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("Shutting down OBS Bridge service")
        finally:
            if self.obs_client:
                try:
                    self.obs_client.disconnect()
                except:
                    pass


async def main():
    """Entry point"""
    bridge = OBSBridge()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
