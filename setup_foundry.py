from foundry_local import FoundryLocalManager
import time
import sys

def setup():
    print("Initializing Foundry Manager...")
    try:
        manager = FoundryLocalManager()
        print("Starting Foundry Service...")
        manager.start_service()
        print(f"Service started at {manager.service_uri}")
        
        # Verify connectivity internally
        # print("Models:", manager.list_models()) # warning if list_models doesn't exist
        
        print("Setup Complete. Keeping process alive for backend.")
        # We start a loop to keep the process alive
        while True:
            time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup()
