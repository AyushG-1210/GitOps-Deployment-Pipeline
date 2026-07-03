import requests
import time
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://127.0.0.1:8000/predict"
TOTAL_REQUESTS = 100
CONCURRENCY_LEVEL = 10

# GitOps Quality Gate Thresholds
MIN_THROUGHPUT = 100.0       # Minimum acceptable requests per second
MAX_P95_LATENCY = 100.0      # Maximum acceptable p95 tail latency in ms
MAX_P99_LATENCY = 150.0      # Maximum acceptable p99 tail latency in ms
REQUIRED_SUCCESS_RATE = 1.0  # 100% success rate required

def send_single_query(query_id):
    payload = {
        "x": round(random.uniform(0.0, 1.0), 4),
        "y": round(random.uniform(0.0, 1.0), 4),
        "t": round(random.uniform(0.0, 1.0), 4)
    }
    
    start_time = time.time()
    try:
        response = requests.post(URL, json=payload, timeout=5)
        latency = (time.time() - start_time) * 1000
        return response.status_code, latency
    except Exception:
        return "ERROR", 0.0

print(f"Executing automated performance gate against {URL}...")
test_start = time.time()
latencies = []
success_count = 0

with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
    futures = [executor.submit(send_single_query, i) for i in range(TOTAL_REQUESTS)]
    
    for future in as_completed(futures):
        status_code, latency = future.result()
        if status_code == 200:
            success_count += 1
            latencies.append(latency)

total_duration = time.time() - test_start
throughput = TOTAL_REQUESTS / total_duration
success_rate = success_count / TOTAL_REQUESTS

# Compute Percentiles
if latencies:
    latencies.sort()
    p95_latency = latencies[int(len(latencies) * 0.95) - 1]
    p99_latency = latencies[int(len(latencies) * 0.99) - 1]
else:
    p95_latency = float('inf')
    p99_latency = float('inf')

print("\n" + "="*40)
print("PERFORMANCE GATE EVALUATION")
print("="*40)
print(f"Throughput:    {throughput:.2f} req/sec  (Target: > {MIN_THROUGHPUT})")
print(f"p95 Latency:   {p95_latency:.2f} ms      (Target: < {MAX_P95_LATENCY})")
print(f"p99 Latency:   {p99_latency:.2f} ms      (Target: < {MAX_P99_LATENCY})")
print(f"Success Rate:  {success_rate * 100:.1f}%       (Target: {REQUIRED_SUCCESS_RATE * 100:.1f}%)")
print("="*40)

if success_rate < REQUIRED_SUCCESS_RATE:
    print("CRITICAL FAILURE: API dropped requests. Breaking the build.")
    sys.exit(1)

if throughput < MIN_THROUGHPUT:
    print(f"PERFORMANCE REGRESSION: Throughput fell below target. Breaking the build.")
    sys.exit(1)

if p95_latency > MAX_P95_LATENCY:
    print(f"PERFORMANCE REGRESSION: p95 tail latency exceeded limit. Breaking the build.")
    sys.exit(1)

if p99_latency > MAX_P99_LATENCY:
    print(f"PERFORMANCE REGRESSION: p99 tail latency exceeded limit. Breaking the build.")
    sys.exit(1)

print("SUCCESS: All performance regression guardrails passed safely.")
sys.exit(0)