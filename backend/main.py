"""
Remote Teleprompter API Backend
FastAPI backend providing WebSocket communication and API endpoints for teleprompter microservices.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import logging
from typing import Dict, Set
from pathlib import Path
from ai_scrolling import ai_scrolling_service, AIScrollingConfig

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

# Initialize AI scrolling service on startup
@app.on_event("startup")
async def startup_event():
    await ai_scrolling_service.initialize()

# Store active connections by channel
class ConnectionManager:
    def __init__(self):
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
        """Get information about connections in a channel"""
        if channel not in self.active_connections:
            return {"exists": False, "connection_count": 0}
        return {
            "exists": True, 
            "connection_count": len(self.active_connections[channel])
        }
    
    async def broadcast_to_channel(self, message: str, channel: str, exclude: WebSocket = None):
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

manager = ConnectionManager()

@app.websocket("/api/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, channel)
    
    # Send connection count update to all clients in channel (including the new one)
    connection_info = manager.get_channel_info(channel)
    connection_update = json.dumps({
        "type": "connection_update",
        "channel": channel,
        "connection_count": connection_info["connection_count"]
    })
    await manager.broadcast_to_channel(connection_update, channel)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Log the message type for debugging
            print(f"Channel {channel}: Received {message.get('type', 'unknown')} message")
            
            # Handle special messages
            message_type = message.get('type')
            
            if message_type == 'request_connection_info':
                # Send current connection count to requesting client
                await websocket.send_text(connection_update)
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
                # Broadcast to all other clients in the same channel
                await manager.broadcast_to_channel(data, channel, exclude=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
        # Clean up AI scrolling session if needed
        ai_scrolling_service.remove_session(channel)
        # Broadcast updated connection count
        connection_info = manager.get_channel_info(channel)
        if connection_info["exists"]:
            connection_update = json.dumps({
                "type": "connection_update",
                "channel": channel,
                "connection_count": connection_info["connection_count"]
            })
            await manager.broadcast_to_channel(connection_update, channel)
    except Exception as e:
        print(f"Error in channel {channel}: {e}")
        manager.disconnect(websocket, channel)
        # Clean up AI scrolling session if needed
        ai_scrolling_service.remove_session(channel)
        # Broadcast updated connection count  
        connection_info = manager.get_channel_info(channel)
        if connection_info["exists"]:
            connection_update = json.dumps({
                "type": "connection_update",
                "channel": channel,
                "connection_count": connection_info["connection_count"]
            })
            await manager.broadcast_to_channel(connection_update, channel)

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
        response = json.dumps({
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
        })
        await manager.broadcast_to_channel(response, channel)
        
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
        response = json.dumps({
            "type": "ai_scrolling_started",
            "channel": channel
        })
        await manager.broadcast_to_channel(response, channel)
        
    except Exception as e:
        logger.error(f"Error starting AI scrolling: {e}")
        error_response = json.dumps({
            "type": "ai_scrolling_error",
            "error": str(e)
        })
        await websocket.send_text(error_response)

async def handle_ai_scrolling_stop(channel: str, message: dict, websocket: WebSocket):
    """Handle AI scrolling session stop"""
    try:
        ai_scrolling_service.remove_session(channel)
        
        # Notify all clients that AI scrolling has stopped
        response = json.dumps({
            "type": "ai_scrolling_stopped",
            "channel": channel
        })
        await manager.broadcast_to_channel(response, channel)
        
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
            response = json.dumps(scroll_command)
            await manager.broadcast_to_channel(response, channel)
        
        # Check for pause detection
        pause_command = await ai_scrolling_service.check_pause_detection(channel)
        if pause_command:
            response = json.dumps(pause_command)
            await manager.broadcast_to_channel(response, channel)
            
    except Exception as e:
        logger.error(f"Error processing audio chunk: {e}")

@app.get("/api/channel/{channel}/info")
async def get_channel_info(channel: str):
    """Get information about a specific channel"""
    return manager.get_channel_info(channel)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_channels": len(manager.active_connections)}

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