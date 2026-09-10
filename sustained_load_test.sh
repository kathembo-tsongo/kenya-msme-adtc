#!/bin/bash
N=50
PROMPT="Explain the requirements for registering a small business in Kenya, including taxation and NSSF obligations, in detail."

echo "Starting sustained load test: $N consecutive generations"
echo "Timestamp: $(date)"
echo "---"

for i in $(seq 1 $N); do
  START=$(date +%s.%N)
  RESPONSE=$(curl -s -X POST http://localhost:8090/completion \
    -H "Content-Type: application/json" \
    -d "{\"prompt\": \"$PROMPT\", \"n_predict\": 200, \"temperature\": 0.3}")
  END=$(date +%s.%N)
  ELAPSED=$(echo "$END - $START" | bc)
  TPS=$(echo "$RESPONSE" | grep -o '"predicted_per_second":[0-9.]*' | cut -d: -f2)
  echo "[$i/$N] elapsed=${ELAPSED}s tok/s=${TPS} at $(date +%H:%M:%S)"
done

echo "---"
echo "Sustained load test complete: $(date)"
