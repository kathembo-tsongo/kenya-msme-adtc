"""
benchmark.py -- Measure raw model throughput (tokens/second) against
llama-server directly, matching how ADTC judges will test the standalone
.gguf. Run this with ONLY llama-server active (rag_server.py not required).
"""
import json
import time
import statistics
import requests

LLAMA_SERVER_URL = "http://localhost:8090"

TEST_PROMPTS = [
    "What percentage of my employee's salary goes to NSSF?",
    "How do I register a business name in Kenya?",
    "What is the VAT registration threshold for a small business?",
    "What are the requirements for a Tax Compliance Certificate?",
    "How many days of annual leave must I give my employees?",
    "What is the Youth Enterprise Development Fund and who qualifies?",
    "What documents do I need to open a business bank account?",
    "What are my obligations under the Social Health Insurance Act?",
]

results = []

print(f"Running {len(TEST_PROMPTS)} benchmark prompts against {LLAMA_SERVER_URL}...\n")

for i, prompt in enumerate(TEST_PROMPTS, 1):
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
        "temperature": 0.3,
    }
    start = time.time()
    resp = requests.post(f"{LLAMA_SERVER_URL}/v1/chat/completions", json=payload)
    wall_time = time.time() - start
    data = resp.json()

    timings = data.get("timings", {})
    predicted_tps = timings.get("predicted_per_second")
    predicted_n = timings.get("predicted_n")
    prompt_tps = timings.get("prompt_per_second")

    print(f"[{i}/{len(TEST_PROMPTS)}] {prompt[:50]!r}")
    print(f"    Generated {predicted_n} tokens at {predicted_tps:.2f} tok/s "
          f"(prompt processing: {prompt_tps:.2f} tok/s, wall time: {wall_time:.2f}s)")

    results.append({
        "prompt": prompt,
        "predicted_tps": predicted_tps,
        "predicted_n": predicted_n,
        "prompt_tps": prompt_tps,
        "wall_time": wall_time,
    })

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

gen_speeds = [r["predicted_tps"] for r in results]
print(f"Generation speed (tokens/sec):")
print(f"  Mean:   {statistics.mean(gen_speeds):.2f}")
print(f"  Median: {statistics.median(gen_speeds):.2f}")
print(f"  Min:    {min(gen_speeds):.2f}")
print(f"  Max:    {max(gen_speeds):.2f}")
print(f"  Stdev:  {statistics.stdev(gen_speeds):.2f}")

print(f"\nADTC reference (TPS_REFERENCE): 15.0")
print(f"Your mean Sperf estimate: {100 * statistics.mean(gen_speeds) / 15.0:.1f} "
      f"(capped at 100 if you exceed the reference)")

with open("benchmark_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nFull results saved to benchmark_results.json")
