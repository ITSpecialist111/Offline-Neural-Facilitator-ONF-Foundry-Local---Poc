
import os
import sys
import time

# Ensure we can import the main module
sys.path.append(os.getcwd())

from backend.services.voice_service import VoiceService, NEON_GREEN, RESET_COLOR

class SmokeTestVoiceService(VoiceService):
    def __init__(self):
        super().__init__()
        self.interaction_count = 0

    def record_audio(self, file_path):
        print(f"{NEON_GREEN}[SMOKE TEST] Mocking audio recording (Skipping Microphone)...{RESET_COLOR}")
        # Create a dummy file to satisfy any file existence checks
        with open(file_path, 'wb') as f:
            f.write(b'\0' * 1024) 

    def transcribe_with_whisper(self, audio_file_path):
        self.interaction_count += 1
        if self.interaction_count == 1:
            print(f"{NEON_GREEN}[SMOKE TEST] Simulating Input 1: 'Hello, who are you?'{RESET_COLOR}")
            return "Hello, who are you?"
        else:
            print(f"{NEON_GREEN}[SMOKE TEST] Simulating Input 2: 'exit'{RESET_COLOR}")
            return "exit"
            
    def play(self, temp_audio_file):
        print(f"{NEON_GREEN}[SMOKE TEST] Audio generation successful. File: {temp_audio_file}{RESET_COLOR}")
        print(f"{NEON_GREEN}[SMOKE TEST] Mocking playback (Skipping Audio Output)...{RESET_COLOR}")
        # We assume if we got here, TTS worked. Skipping playback to keep test silent/fast.
        # But allow file cleanup if original code does it (original code comments out os.remove)
        pass

if __name__ == "__main__":
    print("==================================================")
    print("STARTING SMOKE TEST PIPELINE")
    print("==================================================")
    
    try:
        # Instantiate our mocked service
        # This will still initialize models (loading from disk/GPU)
        vs = SmokeTestVoiceService()
        
        # Run the conversation loop
        # It should run once with the test query, then exit on the second loop
        vs.user_chatbot_conversation()
        
        print("==================================================")
        print("SMOKE TEST PASSED: Pipeline ran successfully.")
        print("==================================================")
        
    except Exception as e:
        print("==================================================")
        print(f"SMOKE TEST FAILED: {e}")
        print("==================================================")
        import traceback
        traceback.print_exc()
