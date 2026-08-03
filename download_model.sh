#!/bin/bash
# download_model.sh -- Downloads the quantized model weights to model/
# Idempotent: safe to run multiple times, skips download if file already exists.

set -e

MODEL_DIR="model"
MODEL_FILE="msme-qwen2.5-1.5b-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/kathembo-tsongo/qwen-msme-gguf/resolve/main/qwen-msme-v2-Q4_K_M.gguf"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
    echo "Model already exists at $MODEL_DIR/$MODEL_FILE -- skipping download."
    exit 0
fi

echo "Downloading model from Hugging Face..."
curl -L -o "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL"

echo "Verifying download..."
FILE_SIZE=$(stat -c%s "$MODEL_DIR/$MODEL_FILE" 2>/dev/null || stat -f%z "$MODEL_DIR/$MODEL_FILE")
if [ "$FILE_SIZE" -lt 500000000 ]; then
    echo "ERROR: downloaded file is suspiciously small ($FILE_SIZE bytes) -- download may have failed."
    exit 1
fi

echo "Model downloaded successfully to $MODEL_DIR/$MODEL_FILE ($FILE_SIZE bytes)"
