from backend.llm.foundry_manager import FoundryEngine
import sys

def test_engine():
    print("Testing FoundryEngine integration...")
    try:
        engine = FoundryEngine()
        print(f"Engine initialized. Base URL: {engine.base_url}")
        
        print("Testing fast_reflex...")
        response = engine.fast_reflex("Hello, are you there?", system_prompt="Answer briefly.")
        print(f"Response: {response}")
        
        if response:
            print("Integration Test Passed!")
        else:
            print("Integration Test Failed: No response.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Integration Test Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_engine()
