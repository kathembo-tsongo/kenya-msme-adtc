# Rafiki wa Biashara - Kenya MSME Advisor (ADTC 2026 Submission)

An offline, on-device advisory assistant for Kenyan MSME (micro, small, and medium enterprise) owners, covering tax, business registration, financing, and regulatory compliance. Built for the Africa Deep Tech Challenge 2026 (Corporate/Enterprise track).

## Repository Scope

This repository was adapted from my broader academic thesis project (Kenya MSME
Advisor, a RAG advisory chatbot originally using a cloud LLM). This is the project I am currently working on as my final Master's project. Files from that
earlier project that are not part of this specific ADTC submission -- data
scraping scripts, a Streamlit web application, an admin/research dashboard --
have been moved into `legacy/` for reference and are not required to run or
evaluate this submission. Everything needed for the ADTC submission (the
offline model, RAG retrieval, and web UI) lives in the repository root.

## Architecture

Browser (webui/index.html)
  -- fetch --> RAG proxy (rag_server.py) on port 8091
       -- TF-IDF retrieval over documents/kb1..kb9
       -- forwards augmented prompt -->
  llama-server (llama.cpp) on port 8090
       -- loads model/msme-qwen2.5-1.5b-Q4_K_M.gguf

The fine-tuned model (msme-qwen2.5-1.5b-Q4_K_M.gguf) also runs standalone via llama-cli/llama-server with no RAG layer -- this is what the raw model evaluation tests directly.

## Requirements

- Python 3.10+
- A C++ build toolchain (for compiling llama.cpp): cmake, gcc/g++
- About 4GB free RAM to run the full stack comfortably

## Setup

### 1. Clone this repo and install Python dependencies

git clone https://github.com/kathembo-tsongo/kenya-msme-adtc.git
cd kenya-msme-adtc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

### 2. Get the model file

Run `bash download_model.sh` -- this downloads the model automatically from Hugging Face (kathembo-tsongo/qwen-msme-gguf, idempotent, safe to re-run).

Place it at model/msme-qwen2.5-1.5b-Q4_K_M.gguf

### 3. Build llama.cpp

git clone --depth 1 https://github.com/ggerganov/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=OFF -DCMAKE_BUILD_TYPE=Release
cmake --build build --target llama-server llama-cli -j 4
cd ..

### 4. Build the RAG retrieval index

Requires documents/ (the source knowledge base). Run `bash download_corpus.sh` -- this downloads and extracts the corpus automatically from Hugging Face (idempotent, safe to re-run).

python3 build_index.py

This produces rag_index.pkl (18,307 chunks indexed, zero extraction failures across all 323 source documents).

### 5. Run the stack

Terminal 1 -- start the model server:
./llama.cpp/build/bin/llama-server -m ./model/msme-qwen2.5-1.5b-Q4_K_M.gguf --port 8090 -c 4096

Terminal 2 -- start the RAG proxy:
source venv/bin/activate
python3 rag_server.py

Then open webui/index.html directly in a browser.

**Before benchmarking:** disable CPU turbo boost first. We found turbo boost
causes a sharp power/heat spike during sustained inference on thin-chassis
hardware, driving peak temperature to 96-100C (triggering the thermal
penalty) with no measurable throughput benefit. Disabling it drops peak
temperature to ~59C with no measurable cost (see REPORT.md, "Thermal --
root cause found and fixed", for full measurements):

    echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

`start.sh` checks this automatically and prints a warning if it's off.

## Testing the raw model standalone (no RAG)

./llama.cpp/build/bin/llama-cli -m ./model/msme-qwen2.5-1.5b-Q4_K_M.gguf -p "Your question here" -n 200 --temp 0.3 -no-cnv

## Resource usage (measured)

- Combined RAM (llama-server + rag_server.py): about 3.3GB
- Model file size: 935MB (Q4_K_M quantization)

## Known limitations

The fine-tuned model's standalone factual accuracy (no RAG) is uneven -- strongest on frequently-repeated training topics, weaker elsewhere, and this holds regardless of decoding temperature (tested at both 0.6 and 0.3 with comparable fabrication rates). A verified-answer digest in `rag_server.py` bypasses generation entirely for 17 hand-checked, high-risk topics (NSSF rate and late-payment penalty, PAYE bands/deadline/penalty, SHIF rate, VAT threshold, Turnover Tax, Affordable Housing Levy, Minimum Wage, YEDF, business registration, KRA PIN, and others), each available in both English and Kiswahili. The RAG layer substantially improves reliability elsewhere by grounding answers in actual source documents, and includes scope-boundary handling to avoid answering questions outside Kenya/MSME topics with unfounded confidence.

Note: this digest-override layer protects the chat/qualitative evaluation path only. The raw model's automated multiple-choice/log-likelihood scoring loads the `.gguf` directly and never renders a chat template, so it reflects the base model's own fine-tuned weights independent of this mitigation -- see REPORT.md ("Two distinct accuracy-evaluation paths") for the full explanation.

## Sources

Knowledge base built from 323 verified Kenyan regulatory, tax, and policy source documents across 9 categories: legal/regulatory, tax/KRA, financing, social security, digital trade, county/geospatial, culture/context, national policy, and bank lending.
