#!/usr/bin/env python3
"""
Multi-Teleprompter Demo Script

This script demonstrates the multi-teleprompter functionality by connecting
multiple simulated teleprompter clients to the same channel.

Usage:
1. Start the teleprompter application: python3 main.py
2. Open a browser to http://localhost:8000
3. Set up a controller in the browser
4. Run this script: python3 demo_multi_teleprompter.py
5. Watch the connection count update in the browser
6. Test control commands from the browser

The script will simulate 2 teleprompter clients for 60 seconds.
"""

import asyncio
import websockets
import json
import time

async def teleprompter_client(channel, client_id):
    """Simulate a teleprompter client"""
    uri = f"ws://localhost:8000/ws/{channel}"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"📱 Teleprompter-{client_id}: Connected to channel '{channel}'")
            
            # Send mode information
            await websocket.send(json.dumps({"type": "mode", "mode": "teleprompter"}))
            
            # Listen for messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type', 'unknown')
                    
                    if msg_type == 'connection_update':
                        count = data.get('connection_count', 0)
                        print(f"📱 Teleprompter-{client_id}: {count} clients now connected")
                    elif msg_type == 'text':
                        content = data.get('content', '')[:50] + "..." if len(data.get('content', '')) > 50 else data.get('content', '')
                        print(f"📱 Teleprompter-{client_id}: Text updated: '{content}'")
                    elif msg_type == 'start':
                        print(f"📱 Teleprompter-{client_id}: ▶️ START command received")
                    elif msg_type == 'pause':
                        print(f"📱 Teleprompter-{client_id}: ⏸️ PAUSE command received")
                    elif msg_type == 'reset':
                        print(f"📱 Teleprompter-{client_id}: ⏮️ RESET command received")
                    elif msg_type == 'speed':
                        speed = data.get('value', 5)
                        print(f"📱 Teleprompter-{client_id}: Speed changed to {speed}")
                    elif msg_type == 'mirror':
                        mode = data.get('value', 'none')
                        print(f"📱 Teleprompter-{client_id}: Mirror mode set to '{mode}'")
                    
                except json.JSONDecodeError:
                    print(f"📱 Teleprompter-{client_id}: Received invalid JSON")
                    
    except ConnectionRefusedError:
        print(f"❌ Teleprompter-{client_id}: Could not connect to {uri}")
        print("   Make sure the teleprompter application is running on http://localhost:8000")
    except Exception as e:
        print(f"📱 Teleprompter-{client_id}: Disconnected ({e})")

async def main():
    """Demo multiple teleprompters connecting to a channel"""
    print("🎬 Multi-Teleprompter Demo")
    print("=" * 50)
    print("This demo simulates multiple teleprompter clients connecting to the same channel.")
    print("Open http://localhost:8000 in your browser and set up a controller to test!")
    print()
    
    # Use a demo channel name
    channel = "demo-multicam"
    print(f"📺 Using channel: '{channel}'")
    print(f"💻 In your browser, use this channel name to connect as a controller")
    print()
    
    # Start multiple teleprompter clients
    print("🚀 Starting 2 teleprompter clients...")
    
    tasks = [
        teleprompter_client(channel, 1),
        teleprompter_client(channel, 2)
    ]
    
    # Run for 60 seconds
    try:
        await asyncio.wait_for(asyncio.gather(*tasks), timeout=60.0)
    except asyncio.TimeoutError:
        print()
        print("⏰ Demo completed after 60 seconds")
    except KeyboardInterrupt:
        print()
        print("⏹️ Demo stopped by user")

if __name__ == "__main__":
    asyncio.run(main())