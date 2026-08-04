#!/bin/bash
# download_corpus.sh -- Downloads and extracts the source knowledge base to documents/
# Idempotent: safe to run multiple times, skips if documents/ already exists.

set -e

CORPUS_URL="https://huggingface.co/datasets/kathembo-tsongo/rafiki-wa-biashara-corpus/resolve/main/documents.zip"
ZIP_FILE="documents.zip"

if [ -d "documents" ]; then
    echo "documents/ already exists -- skipping download."
    exit 0
fi

echo "Downloading corpus from Hugging Face..."
curl -L -o "$ZIP_FILE" "$CORPUS_URL"

echo "Verifying download..."
FILE_SIZE=$(stat -c%s "$ZIP_FILE" 2>/dev/null || stat -f%z "$ZIP_FILE")
if [ "$FILE_SIZE" -lt 100000000 ]; then
    echo "ERROR: downloaded file is suspiciously small ($FILE_SIZE bytes) -- download may have failed."
    exit 1
fi

echo "Extracting..."
unzip -q "$ZIP_FILE"
rm "$ZIP_FILE"

echo "Corpus downloaded and extracted to documents/"
