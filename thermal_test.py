"""
thermal_test.py -- Sustained-load thermal check. Fires consecutive
generations against llama-server while sampling CPU temperature via
`sensors`, to check for the ADTC 85C throttling threshold.
"""
import subprocess
import re
import time
import requests

LLAMA_SERVER_URL = "http://localhost:8090"
NUM_ROUNDS = 20
PROMPT = "Explain in detail the tax obligations, registration requirements, and social security responsibilities for a Kenyan small business owner with five employees."

def get_package_temp():
    out = subprocess.run(["sensors"], capture_output=True, text=True).stdout
    match = re.search(r"Package id 0:\s+\+([\d.]+)", out)
    return float(match.group(1)) if match else None

print(f"Starting sustained-load thermal test: {NUM_ROUNDS} consecutive generations\n")

temps = []
start_temp = get_package_temp()
print(f"Starting temp: {start_temp}C\n")

for i in range(1, NUM_ROUNDS + 1):
    t0 = time.time()
    resp = requests.post(f"{LLAMA_SERVER_URL}/v1/chat/completions", json={
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 300,
        "temperature": 0.5,
    })
    elapsed = time.time() - t0
    temp = get_package_temp()
    temps.append(temp)
    print(f"[{i}/{NUM_ROUNDS}] {elapsed:.1f}s generation -- CPU package: {temp}C")

print(f"\n{'='*50}")
print(f"Start temp: {start_temp}C")
print(f"Max temp reached: {max(temps)}C")
print(f"Min temp: {min(temps)}C")
print(f"ADTC throttle threshold: 85C")
print(f"Margin remaining: {85 - max(temps):.1f}C")
if max(temps) > 85:
    print("WARNING: exceeded ADTC thermal threshold -- Pthermal penalty applies")
else:
    print("OK: stayed under ADTC thermal threshold")
