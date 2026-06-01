#!/usr/bin/env python3
"""
Benchmark script: measure classify latency P50/P95/P99.
Runs N requests to POST /message and captures latency_ms from response.

Usage:
  python benchmark_classify.py
  python benchmark_classify.py 200  # custom num_runs
"""
import time
import statistics
import sys
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def benchmark_classify(num_runs=100):
    """
    Run classify benchmark.
    Collects latency_ms from each POST /message response.
    """
    latencies = []
    
    test_messages = [
        "I'd like to book a room",
        "wifi password?",
        "The room is dirty",
        "wake me up at 6am",
        "I want to cancel",
        "What's the checkout time?",
        "Can I cancel my booking?",
        "How is the food quality?",
        "Is there parking?",
        "I need airport pickup",
    ]
    
    print(f"Running {num_runs} classify requests...")
    
    for i in range(num_runs):
        msg = test_messages[i % len(test_messages)]
        
        response = client.post(
            "/message",
            json={
                "property_id": "hotel_a",
                "guest_id": f"guest_{i}",
                "message_id": str(uuid.uuid4()),
                "text": msg
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if "latency_ms" in data:
                latencies.append(data["latency_ms"])
        else:
            print(f"  Request {i} failed: {response.status_code}")
    
    if not latencies:
        print("ERROR: No latencies collected")
        return
    
    p50 = statistics.median(latencies)
    p95 = sorted(latencies)[int(0.95 * len(latencies))]
    p99 = sorted(latencies)[int(0.99 * len(latencies))] if len(latencies) >= 100 else max(latencies)
    avg = statistics.mean(latencies)
    
    print("\n" + "="*60)
    print("CLASSIFY LATENCY BENCHMARK RESULTS")
    print("="*60)
    print(f"Requests:  {len(latencies)}/{num_runs}")
    print(f"Average:   {avg:.2f}ms")
    print(f"P50:       {p50:.2f}ms")
    print(f"P95:       {p95:.2f}ms")
    print(f"P99:       {p99:.2f}ms")
    print(f"Min:       {min(latencies):.2f}ms")
    print(f"Max:       {max(latencies):.2f}ms")
    print("="*60)
    print("\nAdd these numbers to RESULTS.md:")
    print(f"  Classify P50: ~{p50:.0f}ms")
    print(f"  Classify P95: ~{p95:.0f}ms")
    print(f"  Classify P99: ~{p99:.0f}ms")

if __name__ == "__main__":
    num_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    benchmark_classify(num_runs)
