import requests
import os
import time
import sys

BASE_URL = "http://localhost:8000"
SAMPLE_AUDIO = "sample voice.wav"
OUTPUT_DIR = "outputs_v2"

def main():
    print("=== STARTING ONF FULL SYSTEM TEST ===")
    
    # 1. Check for Audio File
    if not os.path.exists(SAMPLE_AUDIO):
        print(f"❌ Error: '{SAMPLE_AUDIO}' not found in current directory.")
        return

    print(f"✅ Found audio file: {SAMPLE_AUDIO}")

    # 2. Check Backend Health
    print("Checking backend health...")
    for i in range(15): # Retry for 30 seconds
        try:
            resp = requests.get(BASE_URL)
            if resp.status_code == 200:
                print("✅ Backend is reachable")
                break
            else:
                print(f"   Waiting for backend... ({i+1}/15)")
        except requests.exceptions.ConnectionError:
            print(f"   Waiting for backend... ({i+1}/15)")
        
        time.sleep(2)
    else:
        print("❌ Error: Could not connect to backend at http://localhost:8000 after 30 seconds.")
        print("   Please ensure the server is running (python backend/main.py)")
        return

    # 3. Send Transcribe Request
    print("\n[STEP 1] Sending Audio for Processing (ASR -> LLM -> TTS)...")
    start_time = time.time()
    
    try:
        with open(SAMPLE_AUDIO, 'rb') as f:
            files = {'file': (SAMPLE_AUDIO, f, 'audio/wav')}
            # Use 'reflex' mode for standard chat + TTS
            data = {'mode': 'reflex'} 
            response = requests.post(f"{BASE_URL}/transcribe", files=files, data=data)
            
        print(f"   Request completed in {time.time() - start_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            
            # 4. Verify Transcription
            transcription = result.get('transcription', '')
            if transcription:
                print(f"✅ Transcription Success: \"{transcription[:100]}...\"")
            else:
                print("❌ Transcription Empty")
                
            # 5. Verify LLM Response
            llm_response = result.get('response', '')
            if llm_response:
                print(f"✅ LLM Response Success: \"{llm_response[:100]}...\"")
            else:
                print("❌ LLM Response Empty")
                
            # 6. Verify Insight
            insight = result.get('insight', '')
            print(f"ℹ️  Generated Insight: {insight}")
            
            # 7. Verify TTS Output (File System Check)
            print("\n[STEP 2] Verifying TTS Generation...")
            # We look for the most recent file in outputs_v2
            files = [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR) if f.endswith('.wav') or f.endswith('.mp3')]
            if files:
                newest_file = max(files, key=os.path.getmtime)
                # Check if it was modified recently (within last 30 seconds)
                if time.time() - os.path.getmtime(newest_file) < 30:
                     print(f"✅ TTS Success: New audio file generated: {newest_file}")
                else:
                     print(f"⚠️  Warning: Newest audio file ({newest_file}) is old (>30s). TTS might have failed or not run.")
            else:
                print("❌ No audio files found in output directory.")
                
            print("\n🎉 TEST COMPLETE")
            
        else:
            print(f"❌ Server Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error during request: {e}")

if __name__ == "__main__":
    main()
