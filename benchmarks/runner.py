"""
Benchmark runner for SmallHands evaluation harness.
"""

import time
import subprocess
import json
from typing import List, Dict

BENCHMARKS: List[Dict[str, str]] = [
    {
        "name": "Hello World",
        "query": "Create a Python function that prints 'Hello, World!'."
    },
    # Add more benchmarks here.
]

def run_benchmark(benchmark: Dict[str, str]) -> Dict[str, object]:
    start = time.time()
    proc = subprocess.run(
        ["python3", "-u", "main.py", benchmark["query"]],
        capture_output=True, text=True
    )
    duration = time.time() - start
    return {
        "name": benchmark["name"],
        "query": benchmark["query"],
        "success": proc.returncode == 0,
        "duration": duration,
        "stdout": proc.stdout,
        "stderr": proc.stderr
    }

def run_all() -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []
    for bench in BENCHMARKS:
        res = run_benchmark(bench)
        print(f"Benchmark {res['name']}: success={res['success']}, time={res['duration']:.2f}s")
        results.append(res)
    with open("benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2)
    return results

if __name__ == "__main__":
    run_all()