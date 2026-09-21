import hashlib, json
def sha(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()
def n(p): return sum(1 for _ in open(p,encoding="utf-8"))
v5="future-training-data/training_data_v5.jsonl"; v4="provenance/original-run/training_data_v4_merged.jsonl"
ad="provenance/adapter_model.safetensors"; ad0="provenance/original-run/adapter_model.safetensors"
ts=json.load(open("provenance/trainer_state.json"))
L=["Training log for the submitted weights (LoRA, checkpoint-430), generated from provenance/trainer_state.json",
   f"global_step={ts.get('global_step')} epoch={ts.get('epoch')}",""]
for e in ts.get("log_history",[]):
    L.append(f"step={e.get('step')} epoch={e.get('epoch')} loss={e.get('loss')} lr={e.get('learning_rate')} grad_norm={e.get('grad_norm')}" if "loss" in e else "summary: "+json.dumps(e))
open("provenance/training_log.txt","w",encoding="utf-8").write("\n".join(L)+"\n")
open("provenance/dataset_info.md","w",encoding="utf-8").write(f"""# Dataset information

## Used for the submitted weights (v6 run, 430 steps)
- **Name:** training_data_v5.jsonl (stored at `future-training-data/training_data_v5.jsonl`; the folder name is historical -- this is the dataset the submitted weights were trained on)
- **Source:** synthetic conversational question-answer examples about Kenyan MSME tax, registration, financing and social security, produced from verified Kenyan regulatory and financing documents; generation scripts are in `future-training-data/generation-scripts/`
- **Records:** {n(v5)}
- **sha256:** {sha(v5)}

## Used for the earlier first run (not the submitted weights)
- **Name:** training_data_v4_merged.jsonl (`provenance/original-run/`)
- **Records:** {n(v4)}
- **sha256:** {sha(v4)}

## Adapters
- Submitted (fp32, checkpoint-430): `provenance/adapter_model.safetensors`, sha256 {sha(ad)}
- First run (fp16): `provenance/original-run/adapter_model.safetensors`, sha256 {sha(ad0)}
""")
open("provenance/merge_and_quantization.md","w",encoding="utf-8").write("""# Merge, conversion and quantization notes

- Base model: Qwen/Qwen2.5-1.5B-Instruct, commit 989aa7980e4cf806f80c7fef2b1adb7bc71aa306.
- Fine-tuning: LoRA (r=16, alpha=32, dropout 0.05) on training_data_v5.jsonl; adapter saved from checkpoint-430 in fp32.
- The adapter was merged into the base model, converted to GGUF and quantized to Q4_K_M with llama.cpp (llama-quantize built from source). The exact cells and outputs are in `My_Offline_AI_advicer_for_kenyan_msmes.ipynb` in this folder.
- A digest of verified Kenyan MSME facts (digest v9) was then written into the GGUF's chat-template metadata. This changes metadata only, not the weights.
- Final file: qwen-msme-v6-digest-v9-Q4_K_M.gguf, saved locally as model/msme-qwen2.5-1.5b-Q4_K_M.gguf, sha256 e88ec13968800a5e193974a6f132ab4e47658f61474063d7f2f8f3f56b34fca2, hosted at the pinned Hugging Face commit c73de544d83d85040cd3984fd180c718725200e3.
""")
print("v5 records:", n(v5), "| v4 records:", n(v4))
