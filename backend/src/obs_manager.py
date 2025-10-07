"""
OBS Manager for Remote Teleprompter
Handles OBS WebSocket connection and recording control.
"""

import asyncio
import logging
import os
from typing import Optional, Callable

try:
    import obsws_python as obs
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False
    obs = None

logger = logging.getLogger(__name__)


class OBSManager:
    """Manages OBS WebSocket connection and recording control"""

    def __init__(self):
        self.client: Optional[obs.ReqClient] = None
        self.enabled = False
        self.connected = False
        self.recording = False
        self.host = os.getenv("OBS_HOST", "localhost")
        self.port = int(os.getenv("OBS_PORT", "4455"))
        self.password = os.getenv("OBS_PASSWORD", "")
        self.start_delay = int(os.getenv("OBS_START_DELAY", "0"))
        self.status_callback: Optional[Callable] = None

    def set_status_callback(self, callback: Callable):
        """Set callback for OBS status updates"""
        self.status_callback = callback

    def configure(
        self,
        host: str = None,
        port: int = None,
        password: str = None,
        enabled: bool = None,
        start_delay: int = None,
    ):
        """Update OBS configuration"""
        if host is not None:
            self.host = host
        if port is not None:
            self.port = port
        if password is not None:
            self.password = password
        if enabled is not None:
            self.enabled = enabled
        if start_delay is not None:
            self.start_delay = start_delay

        logger.info(f"OBS configured: host={self.host}, port={self.port}, enabled={self.enabled}, delay={self.start_delay}s")

    async def connect(self):
        """Establish connection to OBS WebSocket"""
        if not OBS_AVAILABLE:
            logger.warning("obs-websocket-py not available. OBS integration disabled.")
            return False

        if not self.enabled:
            logger.info("OBS integration is disabled")
            return False

        try:
            self.client = obs.ReqClient(
                host=self.host,
                port=self.port,
                password=self.password if self.password else None,
                timeout=5,
            )
            self.connected = True
            logger.info(f"Connected to OBS at {self.host}:{self.port}")
            await self._broadcast_status()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to OBS: {e}")
            self.connected = False
            self.client = None
            await self._broadcast_status()
            return False

    async def disconnect(self):
        """Disconnect from OBS WebSocket"""
        if self.client:
            try:
                self.client = None
                self.connected = False
                logger.info("Disconnected from OBS")
                await self._broadcast_status()
            except Exception as e:
                logger.error(f"Error disconnecting from OBS: {e}")

    async def start_recording_with_delay(self):
        """Start OBS recording after configured delay"""
        if not self.enabled or not self.connected:
            logger.warning("Cannot start recording - OBS not enabled or not connected")
            return False

        try:
            # Wait for the configured delay
            if self.start_delay > 0:
                logger.info(f"Waiting {self.start_delay} seconds before starting recording...")
                await asyncio.sleep(self.start_delay)

            # Start recording
            await self.start_recording()
            return True
        except Exception as e:
            logger.error(f"Error in delayed recording start: {e}")
            return False

    async def start_recording(self):
        """Start OBS recording"""
        if not self.enabled or not self.connected or not self.client:
            return False

        try:
            # Check if already recording
            status = self.client.get_record_status()
            if status.output_active:
                logger.warning("OBS is already recording")
                self.recording = True
                await self._broadcast_status()
                return True

            # Start recording
            self.client.start_record()
            self.recording = True
            logger.info("Started OBS recording")
            await self._broadcast_status()
            return True
        except Exception as e:
            logger.error(f"Failed to start OBS recording: {e}")
            return False

    async def stop_recording(self):
        """Stop OBS recording"""
        if not self.enabled or not self.connected or not self.client:
            return False

        try:
            # Check if recording
            status = self.client.get_record_status()
            if not status.output_active:
                logger.warning("OBS is not recording")
                self.recording = False
                await self._broadcast_status()
                return True

            # Stop recording
            self.client.stop_record()
            self.recording = False
            logger.info("Stopped OBS recording")
            await self._broadcast_status()
            return True
        except Exception as e:
            logger.error(f"Failed to stop OBS recording: {e}")
            return False

    async def get_status(self) -> dict:
        """Get current OBS status"""
        status = {
            "enabled": self.enabled,
            "connected": self.connected,
            "recording": self.recording,
            "host": self.host,
            "port": self.port,
            "start_delay": self.start_delay,
        }

        # If connected, get live recording status
        if self.connected and self.client:
            try:
                record_status = self.client.get_record_status()
                status["recording"] = record_status.output_active
                self.recording = record_status.output_active
            except Exception as e:
                logger.error(f"Failed to get OBS recording status: {e}")

        return status

    async def _broadcast_status(self):
        """Broadcast OBS status to all clients via callback"""
        if self.status_callback:
            try:
                status = await self.get_status()
                await self.status_callback({
                    "type": "obs_status",
                    **status
                })
            except Exception as e:
                logger.error(f"Error broadcasting OBS status: {e}")

    def is_available(self) -> bool:
        """Check if OBS WebSocket library is available"""
        return OBS_AVAILABLE

    def is_enabled(self) -> bool:
        """Check if OBS integration is enabled"""
        return self.enabled

    def is_connected(self) -> bool:
        """Check if connected to OBS"""
        return self.connected

    def is_recording(self) -> bool:
        """Check if OBS is currently recording"""
        return self.recording


# Singleton instance
obs_manager = OBSManager()
