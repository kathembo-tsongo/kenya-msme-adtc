with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

anchor = "## Constraints"

provenance_section = '''## Model Provenance

**Base model.** [Qwen/Qwen2.5-1.5B-Instruct](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct), loaded via `transformers.AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-1.5B-Instruct")` at training time (main branch, no pinned revision).

**Fine-tuning method.** LoRA, rank 16 (`r=16, lora_alpha=32, lora_dropout=0.05, bias="none", target_modules=["q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj"]`), trained via TRL's `SFTTrainer` for 2 epochs, batch size 4 with gradient accumulation 4, learning rate 2e-4 (cosine schedule, 3% warmup), on a Colab T4 GPU. Final training loss: **1.3941499436567277** at global step 394. Full configuration, training call, and logged output are preserved in the training notebook (`provenance/My_Offline_AI_advicer_for_kenyan_msmes.ipynb`) and `provenance/trainer_state.json`.

**Training dataset.** 3,308 synthetic conversational examples covering Kenyan MSME tax, registration, financing, and social security topics, generated from the project's own verified regulatory source documents (see Data Extraction, below) rather than any third-party licensed dataset. No external dataset license applies; the dataset is original work produced for this project and is included in full at `provenance/training_data_v4_merged.jsonl` (3,308 records, SHA256 checksum below).

**Merge and quantization.** The LoRA adapter (`checkpoint-394`) was merged into the base model via `peft.PeftModel.from_pretrained()` + `merge_and_unload()`, converted to GGUF via `llama.cpp`'s `convert_hf_to_gguf.py`, and quantized to Q4_K_M via `llama-quantize`. All three steps, including their real logged output, are preserved in the same training notebook.

**Proof-of-training files** (in `provenance/`):
- `adapter_model.safetensors` + `adapter_config.json` -- the trained LoRA adapter
- `My_Offline_AI_advicer_for_kenyan_msmes.ipynb` -- full training notebook (data prep, LoRA training, merge, GGUF conversion, quantization), with cell outputs intact
- `trainer_state.json` -- per-step training metrics
- `training_data_v4_merged.jsonl` -- the complete training dataset (3,308 records)
- Colab execution link: [PLACEHOLDER -- pending]

**SHA256 checksums:**

**Before/after comparison.** Two identical prompts run through the unmodified base model (`Qwen/Qwen2.5-1.5B-Instruct-GGUF`, official Q4_K_M release) and our fine-tuned model, both without RAG or the digest-override layer, isolating the fine-tuning's effect specifically:

*Prompt: "What are the NSSF contribution rates for an employee earning KSh 30,000 per month?"*
- **Base model:** invents a fictional "1.5% to 2.5%" rate and a non-existent "Additional Contribution Rate" concept; no calculation given.
- **Fine-tuned model:** "The NSSF contribution... is **KSh 1,800**. This is calculated as 6% of the employee's salary plus 6% of the employer's contribution... the employee pays **KSh 1,800** and the employer matches with **KSh 1,800**." -- correct rate, correctly calculated.

*Prompt: "What is Turnover Tax in Kenya and who qualifies to pay it?"*
- **Base model:** conflates Turnover Tax entirely with VAT, states a fabricated "KES 100,000" threshold and a fictional "18%... progressive" rate, and invents a non-existent "Goods and Services Tax (GST)."
- **Fine-tuned model:** correctly uses Kenya-specific terminology and a real regulatory figure (KES 5,000,000), though it still conflates Turnover Tax's identity with VAT's threshold -- a partial improvement, not a full fix, and the exact reason our digest-override layer (see Hybrid Grounding Strategy, above) provides a hand-verified answer for this specific topic rather than relying on generation alone.

We report this second example's residual imprecision rather than omitting it: fine-tuning measurably shifted outputs toward domain-specific knowledge, but did not eliminate cross-topic confusion between related tax categories on its own -- which is precisely the gap our verified-answer layer is designed to close.

## Constraints'''

if anchor not in content:
    print("ERROR: could not find '## Constraints' anchor. No changes made.")
else:
    content = content.replace(anchor, provenance_section, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Model Provenance section added.")
    print(f"New file length: {len(content.splitlines())} lines")
