import requests
import sys
import time
import json
import uuid

BASE_URL = "http://localhost:8000"

def simulate_real_world_scenario():
    print("=== STARTING ENHANCED SIMULATION SCENARIO ===")
    print("This simulation stress-tests Transcript, RAG, and Proactive Intelligence.")
    print("Waiting 10s for frontend to connect (optional)...")
    time.sleep(10)
    
    events = [
        # Segment 1: Introductions
        {
            "type": "transcript",
            "text": "Hi everyone, I'm Graham. Let's start the sync on the new RAG module.",
            "role": "user",
            "timestamp": time.time()
        },
        # Segment 2: Contextual Insight
        {
            "type": "timeline_event",
            "subtype": "knowledge",
            "text": "Graham: Focuses on Offline-First & Privacy. (Source: privacy_spec.md)",
            "citation": "privacy_spec.md",
            "timestamp": time.time() + 2
        },
        # Segment 3: Technical Discussion
        {
            "type": "transcript",
            "text": "We need to make sure the vector store works with ChromaDB even when completely offline.",
            "role": "user",
            "timestamp": time.time() + 5
        },
        # Segment 4: Proactive Risk Detection
        {
            "type": "insight",
            "subtype": "risk",
            "text": "High Latency Risk: Local embeddings might slow down UI on lower-end CPUs.",
            "severity": "medium",
            "timestamp": time.time() + 7
        },
        # Segment 5: Action Item Detection
        {
            "type": "timeline_event",
            "subtype": "action_item",
            "text": "Action Item: Benchmarking suite for ChromaDB latency. (Assignee: QA)",
            "citation": "System Intelligence",
            "timestamp": time.time() + 10
        },
        # Segment 6: Reasoning Outcome
        {
            "type": "transcript",
            "text": "Deep Reason Engine: Considering the current load, I recommend using a sliding window for embeddings.",
            "role": "assistant",
            "timestamp": time.time() + 15
        }
    ]
    
    print(f"Sending {len(events)} events to /debug/simulate...")
    
    start_time = time.time()
    try:
        resp = requests.post(f"{BASE_URL}/debug/simulate", json=events)
        total_duration = time.time() - start_time
        
        if resp.status_code == 200:
            print(f"✅ Simulation sent successfully in {total_duration:.2f}s.")
            print("Check the UI for real-time visualization of these events.")
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text}")
    except Exception as e:
        print(f"❌ Error during simulation request: {e}")

if __name__ == "__main__":
    simulate_real_world_scenario()

