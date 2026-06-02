#!/usr/bin/env python3

import statistics
import sys
import time
import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


TEST_MESSAGES = [
    # booking
    "book a room tomorrow",
    "need deluxe room",
    "reserve room for 2 nights",

    # faq
    "wifi password",
    "parking available",
    "checkout time",

    # complaint
    "ac not working",
    "room is dirty",
    "water heater broken",

    # wakeup
    "wake me up at 6am",
    "need wakeup call",

    # cancellation
    "cancel my booking",
    "please cancel reservation",

    # ambiguous
    "maybe cancel my booking",
    "thinking of cancelling",

    # unknown
    "asdfghjkl",
    "random text",
]


def percentile(values, p):
    values = sorted(values)
    idx = int((p / 100) * len(values))

    if idx >= len(values):
        idx = len(values) - 1

    return values[idx]


def benchmark(num_runs=1000):
    classify_latencies = []
    e2e_latencies = []

    print(f"\nRunning {num_runs} benchmark requests...\n")

    for i in range(num_runs):
        if i % 50 == 0:
            pct = (i / num_runs) * 100

            print(
                f"[{pct:.0f}%] {i}/{num_runs}",
                flush=True,
            )
        message = TEST_MESSAGES[
            i % len(TEST_MESSAGES)
        ]

        start = time.perf_counter()

        response = client.post(
            "/message",
            json={
                "property_id": "hotel_a",
                "guest_id": f"guest_{i}",
                "message_id": str(uuid.uuid4()),
                "text": message,
            },
        )

        end = time.perf_counter()

        e2e_ms = (end - start) * 1000
        e2e_latencies.append(e2e_ms)

        if response.status_code == 200:
            body = response.json()

            if "latency_ms" in body:
                classify_latencies.append(
                    body["latency_ms"]
                )

    print("=" * 70)
    print("CLASSIFICATION LATENCY")
    print("=" * 70)

    print(
        f"Average : {statistics.mean(classify_latencies):.4f} ms"
    )

    print(
        f"P50     : {percentile(classify_latencies, 50):.4f} ms"
    )

    print(
        f"P95     : {percentile(classify_latencies, 95):.4f} ms"
    )

    print(
        f"P99     : {percentile(classify_latencies, 99):.4f} ms"
    )

    print(
        f"Min     : {min(classify_latencies):.4f} ms"
    )

    print(
        f"Max     : {max(classify_latencies):.4f} ms"
    )

    print()

    print("=" * 70)
    print("END-TO-END /message LATENCY")
    print("=" * 70)

    print(
        f"Average : {statistics.mean(e2e_latencies):.4f} ms"
    )

    print(
        f"P50     : {percentile(e2e_latencies, 50):.4f} ms"
    )

    print(
        f"P95     : {percentile(e2e_latencies, 95):.4f} ms"
    )

    print(
        f"P99     : {percentile(e2e_latencies, 99):.4f} ms"
    )

    print(
        f"Min     : {min(e2e_latencies):.4f} ms"
    )

    print(
        f"Max     : {max(e2e_latencies):.4f} ms"
    )

    print()

    print("=" * 70)
    print("COPY TO RESULTS.md")
    print("=" * 70)

    print(
        f"Classification P95: {percentile(classify_latencies,95):.4f} ms"
    )

    print(
        f"Classification P99: {percentile(classify_latencies,99):.4f} ms"
    )

    print(
        f"/message P95: {percentile(e2e_latencies,95):.4f} ms"
    )

    print(
        f"/message P99: {percentile(e2e_latencies,99):.4f} ms"
    )


if __name__ == "__main__":
    runs = (
        int(sys.argv[1])
        if len(sys.argv) > 1
        else 1000
    )

    benchmark(runs)