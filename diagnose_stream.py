import asyncio
import websockets
import json
import time

async def stream_audio():
    uri = "ws://localhost:8000/ws/stream"
    filename = "sample voice.wav"
    chunk_size = 32000 # ~1 second of 16k mono 16bit
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to {uri}")
            
            with open(filename, "rb") as f:
                while True:
                    data = f.read(chunk_size)
                    if not data:
                        break
                    
                    print(f"Sending chunk size: {len(data)}")
                    await websocket.send(data)
                    
                    # Wait for potential response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                        print(f"Received: {response}")
                    except asyncio.TimeoutError:
                        pass
                    
                    await asyncio.sleep(1) # Simulate real-time
            
            print("Stream finished. Waiting for final response...")
            try:
                while True:
                    response = await websocket.recv()
                    print(f"Received: {response}")
            except Exception as e:
                print(f"Connection closed: {e}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(stream_audio())
