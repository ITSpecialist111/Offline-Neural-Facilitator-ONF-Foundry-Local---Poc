import os
import sys
import time
import json

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.rag_service import RagService

def run_benchmarks():
    print("=== STARTING RAG ACCURACY BENCHMARK ===")
    
    rag = RagService()
    doc_count = rag.count()
    print(f"Knowledge Vault Status: {doc_count} documents loaded.\n")

    if doc_count == 0:
        print("❌ Cannot run benchmark on empty vault. Run RAG ingestion first.")
        return

    # Define test queries and expected substrings/sources
    # These are based on common content found in vault.txt and project requirements
    test_cases = [
        {
            "query": "Who is User?",
            "expected": ["User", "My name is User"],
            "description": "Basic Identity Retrieval"
        },
        {
            "query": "What are the core requirements for the Facilitator AI app?",
            "expected": ["offline-first", "Whisper", "RAG", "Foundry Local"],
            "description": "Project Vision Retrieval"
        },
        {
            "query": "What templates are defined for the agent?",
            "expected": ["Agenda detection", "Action extraction", "Section summarization"],
            "description": "Technical Detail Retrieval"
        },
        {
            "query": "How is speaker identification implemented?",
            "expected": ["diarization", "voice fingerprint", "real time"],
            "description": "Feature Detail Retrieval"
        },
        {
            "query": "What format should the agenda detection output be?",
            "expected": ["JSON", "topics", "start times"],
            "description": "Structured Data Requirements"
        }
    ]

    results = []
    total_passed = 0

    for i, case in enumerate(test_cases):
        print(f"Test {i+1}: {case['description']} ('{case['query']}')")
        start_time = time.time()
        
        # Search the vault
        search_results = rag.search(case["query"], n_results=3)
        latency = time.time() - start_time
        
        # Check for expected content in results
        found_expected = []
        for exp in case["expected"]:
            match = any(exp.lower() in res["text"].lower() for res in search_results)
            found_expected.append(match)
        
        passing = all(found_expected)
        if passing:
            total_passed += 1
            print(f"  ✅ Pass ({latency:.3f}s)")
        else:
            print(f"  ❌ Fail ({latency:.3f}s)")
            # Print feedback for debugging
            missing = [case["expected"][j] for j, found in enumerate(found_expected) if not found]
            print(f"     Missing: {missing}")
            if search_results:
                print(f"     Top Result: {search_results[0]['text'][:100]}...")
            else:
                print("     No results found.")
        
        results.append({
            "test": case["description"],
            "query": case["query"],
            "latency": latency,
            "pass": passing,
            "results_found": len(search_results)
        })

    # Summary Stats
    accuracy = (total_passed / len(test_cases)) * 100
    avg_latency = sum(r["latency"] for r in results) / len(results)

    print(f"\n=== BENCHMARK SUMMARY ===")
    print(f"Accuracy: {accuracy:.1f}% ({total_passed}/{len(test_cases)})")
    print(f"Avg Latency: {avg_latency:.3f}s")
    
    # Save results for artifact documentation
    with open("rag_benchmark_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "accuracy": accuracy,
            "avg_latency": avg_latency,
            "cases": results
        }, f, indent=2)

if __name__ == "__main__":
    run_benchmarks()
