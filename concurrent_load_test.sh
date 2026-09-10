#!/bin/bash
ROUNDS=15
PROMPT="Explain the requirements for registering a small business in Kenya, including taxation and NSSF obligations, in detail."

echo "Starting CONCURRENT load test: $ROUNDS rounds of 4 simultaneous requests"
echo "Timestamp: $(date)"
echo "---"

for round in $(seq 1 $ROUNDS); do
  START=$(date +%s.%N)
  for slot in 1 2 3 4; do
    curl -s -X POST http://localhost:8090/completion \
      -H "Content-Type: application/json" \
      -d "{\"prompt\": \"$PROMPT\", \"n_predict\": 200, \"temperature\": 0.3}" \
      -o /tmp/resp_$slot.json &
  done
  wait
  END=$(date +%s.%N)
  ELAPSED=$(echo "$END - $START" | bc)
  echo "[round $round/$ROUNDS] 4 concurrent requests completed in ${ELAPSED}s at $(date +%H:%M:%S)"
done

echo "---"
echo "Concurrent load test complete: $(date)"
