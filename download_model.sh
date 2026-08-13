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
    rm -f "$MODEL_DIR/$MODEL_FILE"
    exit 1
fi

EXPECTED_SHA256="6ad480be1fd3f56ba096aac5e5f2f7fd5196d34357a5e4f0d2bfaa618f02edc8"
ACTUAL_SHA256=$(sha256sum "$MODEL_DIR/$MODEL_FILE" | cut -d " " -f 1)
if [ "$ACTUAL_SHA256" != "$EXPECTED_SHA256" ]; then
    echo "ERROR: checksum mismatch -- downloaded file is corrupted."
    echo "  expected: $EXPECTED_SHA256"
    echo "  actual:   $ACTUAL_SHA256"
    echo "This can happen from a dropped connection mid-download. Deleting the corrupted file -- rerun this script to retry."
    rm -f "$MODEL_DIR/$MODEL_FILE"
    exit 1
fi

echo "Model downloaded and verified successfully at $MODEL_DIR/$MODEL_FILE ($FILE_SIZE bytes, sha256 confirmed)"
