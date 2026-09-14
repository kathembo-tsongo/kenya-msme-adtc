#!/bin/bash
# Start Rafiki wa Biashara - Kenya MSME Advisor

# Check CPU turbo boost state before benchmarking. Turbo boost caused a
# measured peak core temperature of 96-100C during required profiler
# benchmarks (pp512/tg128), triggering the competition's thermal penalty.
# Disabling it drops peak temp to ~59C with no measurable throughput cost
# (16.03 vs 16.08 tok/s). See REPORT.md for full measurement details.
if [ -f /sys/devices/system/cpu/intel_pstate/no_turbo ]; then
    CURRENT_TURBO=$(cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null)
    if [ "$CURRENT_TURBO" != "1" ]; then
        echo ""
        echo "############################################################"
        echo "# WARNING: CPU turbo boost is currently ENABLED."
        echo "# This caused peak core temperatures of 96-100C in testing,"
        echo "# triggering the thermal penalty. Before generating any"
        echo "# official benchmark numbers, run:"
        echo "#"
        echo "#   echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo"
        echo "#"
        echo "############################################################"
        echo ""
    else
        echo "CPU turbo boost is disabled (confirmed safe for benchmarking)."
    fi
fi

echo "Starting llama-server..."
./llama.cpp/build/bin/llama-server \
  -m ./model/msme-qwen2.5-1.5b-Q4_K_M.gguf \
  --port 8090 \
  -c 8192 \
  --threads 4 \
  --temp 0.3 \
  --no-mmap &

sleep 3
echo "Starting RAG proxy..."
source venv/bin/activate
python3 rag_server.py
