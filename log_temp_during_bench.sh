#!/bin/bash
LOGFILE="temp_log.csv"
echo "timestamp,package_temp_c" > "$LOGFILE"

(
  while true; do
    TEMP=$(sensors -u 2>/dev/null | grep -A1 "Package id 0" | grep "temp1_input" | awk '{print $2}')
    if [ -n "$TEMP" ]; then
      echo "$(date +%H:%M:%S.%N),$TEMP" >> "$LOGFILE"
    fi
    sleep 0.5
  done
) &
LOGGER_PID=$!

echo "Logging started (PID $LOGGER_PID). Running llama-bench..."
llama-bench -m ./model/msme-qwen2.5-1.5b-Q4_K_M.gguf -p 512 -n 128 -ngl 0 --output json > bench_output.json

kill $LOGGER_PID 2>/dev/null
echo "Done. Peak temperature:"
sort -t, -k2 -n -r "$LOGFILE" | head -5
