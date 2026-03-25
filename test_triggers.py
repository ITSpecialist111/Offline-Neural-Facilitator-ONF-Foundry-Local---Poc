import asyncio
import json
from backend.services.voice_service import VoiceService

async def simulate_triggers():
    print("=== STARTING TRIGGER SIMULATION ===")
    vs = VoiceService()
    
    # Mock broadcast callback
    async def mock_broadcast(event):
        print(f"\n[BROADCAST] {event['type']} | {event.get('subtype', 'N/A')} | {event['text']}")
        if 'intervention' in event:
            print(f"Intervention Strategy: {event['intervention'][:200]}...")

    vs.set_broadcast_callback(mock_broadcast)

    # 1. Simulate High Cognitive Load
    print("\n--- Simulating High Cognitive Load ---")
    vs.conversation_history = [
        {"role": "user", "content": "We need to discuss the architecture of the new neural network. It's a transformer-based model with 50 layers, each with multi-head attention and position-wise feed-forward networks. We also need to consider the gradient clipping and the learning rate scheduler which uses a cosine annealing pattern. The dataset is 10TB and requires a distributed training setup across 100 GPUs using ZeRO-3 optimization and deepspeed."},
        {"role": "assistant", "content": "That sounds complex. How should we start?"}
    ]
    await vs.proactive_dynamics_check()

    # 2. Simulate Conflict
    print("\n--- Simulating Conflict ---")
    vs.conversation_history = [
        {"role": "user", "content": "I completely disagree with this approach. It's totally wrong and a waste of time."},
        {"role": "assistant", "content": "I understand you have concerns, but we need to move forward."},
        {"role": "user", "content": "No, wait! Stop! You are not listening. This is incorrect and I will not support it. No way."},
    ]
    # This should trigger keyword count and then Reflex check.
    # We might need to mock Reflex if it's not connected, but let's see if it works with the real engine.
    await vs.proactive_dynamics_check()

    print("\n=== SIMULATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(simulate_triggers())
