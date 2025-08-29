"""
Remote Teleprompter Application
A web-based teleprompter that allows control from one device (computer) 
and display on another (phone).
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
from typing import Dict, Set
from pathlib import Path

app = FastAPI(title="Remote Teleprompter")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

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

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Serve the main application page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.websocket("/ws/{channel}")
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
            if message.get('type') == 'request_connection_info':
                # Send current connection count to requesting client
                await websocket.send_text(connection_update)
            else:
                # Broadcast to all other clients in the same channel
                await manager.broadcast_to_channel(data, channel, exclude=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
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
        # Broadcast updated connection count  
        connection_info = manager.get_channel_info(channel)
        if connection_info["exists"]:
            connection_update = json.dumps({
                "type": "connection_update",
                "channel": channel,
                "connection_count": connection_info["connection_count"]
            })
            await manager.broadcast_to_channel(connection_update, channel)

@app.get("/channel/{channel}/info")
async def get_channel_info(channel: str):
    """Get information about a specific channel"""
    return manager.get_channel_info(channel)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_channels": len(manager.active_connections)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
