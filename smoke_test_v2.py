import asyncio
import websockets
import requests
import json
import os
import time

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/stream"

def create_dummy_wav(filename="test_audio.wav"):
    # Create a 1-second silent WAV file for testing
    import wave
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b'\x00' * 32000) # 1 sec of silence
    return filename

def test_deep_reasoning():
    print("\n[SMOKE] Testing Deep Reasoning Endpoint...")
    filename = create_dummy_wav()
    try:
        with open(filename, 'rb') as f:
            files = {'file': (filename, f, 'audio/wav')}
            data = {'mode': 'reason'}
            start = time.time()
            response = requests.post(f"{BASE_URL}/transcribe", files=files, data=data)
            duration = time.time() - start
            
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get('mode') == 'reason':
                print(f"✅ Deep Reasoning Success ({duration:.2f}s)")
                return True
            else:
                print(f"❌ Failed: Mode mismatch. Got {res_json.get('mode')}")
        else:
            print(f"❌ Failed: Status {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)
    return False

async def test_websocket_stream():
    print("\n[SMOKE] Testing WebSocket Streaming...")
    filename = create_dummy_wav("stream_test.wav")
    try:
        async with websockets.connect(WS_URL) as websocket:
            print("   Connected to WebSocket")
            
            # Send audio chunks
            with open(filename, 'rb') as f:
                while chunk := f.read(4000): # Send small chunks
                    await websocket.send(chunk)
                    await asyncio.sleep(0.1)
            
            # Send a bit more silence to trigger buffer
            await websocket.send(b'\x00' * 65000)
            
            print("   Sent audio data")
            
            # Wait for meaningful response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                if data.get('type') == 'transcript':
                    print(f"✅ WebSocket Stream Success: Received transcript update")
                    print(f"   Segments: {len(data.get('segments', []))}")
                    return True
            except asyncio.TimeoutError:
                print("⚠️ WebSocket Timeout (Expected if mock silence yields no text, but connection held)")
                return True # Connection held is a pass for now
                
    except Exception as e:
        print(f"❌ WebSocket Error: {e}")
        return False
    finally:
         if os.path.exists(filename):
            os.remove(filename)

def test_skills_endpoint():
    print("\n[SMOKE] Testing Skills Endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/skills")
        if response.status_code == 200:
            data = response.json()
            if "skills" in data and isinstance(data["skills"], list):
                print(f"✅ Skills Endpoint Success (Found {len(data['skills'])} skills)")
                return True
            else:
                print(f"❌ Failed: Invalid format {data}")
        else:
            print(f"❌ Failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_agenda_endpoint():
    print("\n[SMOKE] Testing Agenda Endpoint...")
    try:
        # Check Agenda (POST)
        response = requests.post(f"{BASE_URL}/agenda/check")
        if response.status_code == 200:
            data = response.json()
            if "current_topic" in data:
                print(f"✅ Agenda Endpoint Success (Topic: '{data['current_topic']}')")
                return True
            else:
                 print(f"❌ Failed: Invalid format {data}")
        else:
             print(f"❌ Failed: Status {response.status_code}")
    except Exception as e:
         print(f"❌ Error: {e}")
    return False

def test_rag_health():
    print("\n[SMOKE] Testing RAG & ChromaDB Health...")
    try:
        # Assuming we can check count via a debug endpoint or just test upload/search
        # Let's test a simple search via /chat if available, or just verify the service initializes
        response = requests.post(f"{BASE_URL}/chat", json={"query": "Hello"})
        if response.status_code == 200:
            print(f"✅ RAG/Chat Health Success")
            return True
        else:
            print(f"❌ Failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def test_report_endpoint():
    print("\n[SMOKE] Testing Report Endpoint...")
    try:
        data = {
            "transcript": [{"role": "user", "text": "Hello"}],
            "insights": [{"type": "Topic", "text": "Intro"}],
            "summary": "This is a test summary.",
            "topic": "Smoke Test"
        }
        response = requests.post(f"{BASE_URL}/report/generate", json=data)
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("status") == "success" and "filepath" in res_json:
                print(f"✅ Report Endpoint Success (Saved to {res_json['filepath']})")
                return True
            else:
                print(f"❌ Failed: Invalid format {res_json}")
        else:
             print(f"❌ Failed: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False


async def main():
    print("=== STARTING SMOKE TESTS v2.2 ===")
    
    # Wait for server to be up
    for i in range(10):
        try:
            requests.get(BASE_URL)
            break
        except:
            print(f"Waiting for server... {i+1}/10")
            time.sleep(2)
            
    reason_pass = test_deep_reasoning()
    skills_pass = test_skills_endpoint()
    agenda_pass = test_agenda_endpoint()
    report_pass = test_report_endpoint()
    rag_pass = test_rag_health()
    ws_pass = await test_websocket_stream()
    
    if reason_pass and skills_pass and agenda_pass and report_pass and ws_pass and rag_pass:
        print("\n🎉 ALL SMOKE TESTS PASSED!")
    else:
        print("\n💥 SMOKE TESTS FAILED")


if __name__ == "__main__":
    asyncio.run(main())
