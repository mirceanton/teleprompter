"""
Remote Teleprompter Application
A web-based teleprompter that allows control from one device (computer) 
and display on another (phone).
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import json
import asyncio
from typing import Dict, Set
from pathlib import Path

app = FastAPI(title="Remote Teleprompter")

# Setup paths
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

# Mount static files for JS/CSS
app.mount("/js", StaticFiles(directory=str(STATIC_DIR / "js")), name="js")
app.mount("/css", StaticFiles(directory=str(STATIC_DIR / "css")), name="css")

# Store active connections by channel
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = set()
        self.active_connections[channel].add(websocket)
        print(f"Client connected to channel: {channel}")
    
    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
            self.active_connections[channel].discard(websocket)
            if not self.active_connections[channel]:
                del self.active_connections[channel]
        print(f"Client disconnected from channel: {channel}")
    
    async def broadcast_to_channel(self, message: str, channel: str, exclude: WebSocket = None):
        if channel in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[channel]:
                if connection != exclude:
                    try:
                        await connection.send_text(message)
                    except:
                        disconnected.add(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.active_connections[channel].discard(conn)

manager = ConnectionManager()

@app.get("/")
async def home():
    """Serve the main application page"""
    return FileResponse(str(STATIC_DIR / "index.html"))

@app.websocket("/ws/{channel}")
async def websocket_endpoint(websocket: WebSocket, channel: str):
    """WebSocket endpoint for real-time communication"""
    await manager.connect(websocket, channel)
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Log the message type for debugging
            print(f"Channel {channel}: Received {message.get('type', 'unknown')} message")
            
            # Broadcast to all other clients in the same channel
            await manager.broadcast_to_channel(data, channel, exclude=websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, channel)
    except Exception as e:
        print(f"Error in channel {channel}: {e}")
        manager.disconnect(websocket, channel)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "active_channels": len(manager.active_connections)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
