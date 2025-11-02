#!/usr/bin/env python3
"""
Quick WebSocket test to verify your dev tunnel supports WebSocket connections
"""
import asyncio
import websockets
import os
from dotenv import load_dotenv
from urllib.parse import urlparse

load_dotenv()

async def test_websocket():
    callback_uri = os.getenv("CALLBACK_URI_HOST")
    
    if not callback_uri:
        print("❌ CALLBACK_URI_HOST not set in .env file")
        return
    
    print(f"Testing WebSocket connection to: {callback_uri}")
    
    # Convert HTTP to WSS
    parsed = urlparse(callback_uri)
    ws_url = f"wss://{parsed.netloc}/ws/test-connection"
    
    print(f"WebSocket URL: {ws_url}")
    print("Attempting to connect...")
    
    try:
        async with websockets.connect(ws_url, timeout=5) as websocket:
            print("✅ WebSocket connection successful!")
            await websocket.send("Hello Server")
            response = await websocket.recv()
            print(f"📩 Received: {response}")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        print("\nPossible issues:")
        print("1. Dev tunnel doesn't support WebSockets (need to enable it)")
        print("2. Backend server not running")
        print("3. CALLBACK_URI_HOST format incorrect")

if __name__ == "__main__":
    asyncio.run(test_websocket())

