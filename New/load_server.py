import requests
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://127.0.0.1:8000/predict"
TOTAL_REQUESTS = 100
CONCURRENCY_LEVEL = 10  # Number of simultaneous threads

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
    except Exception as e:
        return "ERROR", 0.0

print(f"Starting concurrent stress test: sending {TOTAL_REQUESTS} total requests with {CONCURRENCY_LEVEL} parallel workers...")

test_start = time.time()
latencies = []
success_count = 0
failure_count = 0

with ThreadPoolExecutor(max_workers=CONCURRENCY_LEVEL) as executor:
    futures = [executor.submit(send_single_query, i) for i in range(TOTAL_REQUESTS)]
    
    for future in as_completed(futures):
        status_code, latency = future.result()
        if status_code == 200:
            success_count += 1
            latencies.append(latency)
        else:
            failure_count += 1

total_duration = time.time() - test_start
avg_latency = sum(latencies) / len(latencies) if latencies else 0
requests_per_second = TOTAL_REQUESTS / total_duration

print("\n" + "="*40)
print("CONCURRENT STRESS TEST RESULTS")
print("="*40)
print(f"Total Time Elapsed:  {total_duration:.2f} seconds")
print(f"Successful Queries:  {success_count}/{TOTAL_REQUESTS}")
print(f"Failed Queries:      {failure_count}/{TOTAL_REQUESTS}")
print(f"Average Latency:     {avg_latency:.2f} ms")
print(f"Throughput:          {requests_per_second:.2f} requests/sec")
print("="*40)