#!/bin/bash
# Downloads the quantized GGUF model weights for Rafiki wa Biashara
# from Hugging Face into the model/ directory.

set -e

MODEL_DIR="model"
MODEL_FILE="qwen-msme-v2-Q4_K_M.gguf"
MODEL_URL="https://huggingface.co/kathembo-tsongo/qwen-msme-gguf/resolve/main/qwen-msme-v2-Q4_K_M.gguf"

mkdir -p "$MODEL_DIR"

if [ -f "$MODEL_DIR/$MODEL_FILE" ]; then
    echo "Model already exists at $MODEL_DIR/$MODEL_FILE — skipping download."
else
    echo "Downloading model weights..."
    wget -O "$MODEL_DIR/$MODEL_FILE" "$MODEL_URL"
    echo "Download complete: $MODEL_DIR/$MODEL_FILE"
fi
