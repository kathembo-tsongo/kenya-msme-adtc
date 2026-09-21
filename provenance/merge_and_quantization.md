# Merge, conversion and quantization notes

- Base model: Qwen/Qwen2.5-1.5B-Instruct, commit 989aa7980e4cf806f80c7fef2b1adb7bc71aa306.
- Fine-tuning: LoRA (r=16, alpha=32, dropout 0.05) on training_data_v5.jsonl; adapter saved from checkpoint-430 in fp32.
- The adapter was merged into the base model, converted to GGUF and quantized to Q4_K_M with llama.cpp (llama-quantize built from source). The exact cells and outputs are in `My_Offline_AI_advicer_for_kenyan_msmes.ipynb` in this folder.
- A digest of verified Kenyan MSME facts (digest v9) was then written into the GGUF's chat-template metadata. This changes metadata only, not the weights.
- Final file: qwen-msme-v6-digest-v9-Q4_K_M.gguf, saved locally as model/msme-qwen2.5-1.5b-Q4_K_M.gguf, sha256 e88ec13968800a5e193974a6f132ab4e47658f61474063d7f2f8f3f56b34fca2, hosted at the pinned Hugging Face commit c73de544d83d85040cd3984fd180c718725200e3.
