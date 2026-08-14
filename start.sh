#!/bin/bash
# Start Rafiki wa Biashara - Kenya MSME Advisor

echo "Starting llama-server..."
./llama.cpp/build/bin/llama-server \
  -m ./model/msme-qwen2.5-1.5b-Q4_K_M.gguf \
  --port 8090 \
  -c 2048 \
  --threads 4 \
  --temp 0.3 \
  --no-mmap &

sleep 3
echo "Starting RAG proxy..."
source venv/bin/activate
python3 rag_server.py
