with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

old = "**SHA256 checksums:**\n\n**Before/after comparison.**"

new = (
    "**SHA256 checksums:**\n\n"
    "    adapter_model.safetensors:      962a625b15ef4a7b8c67a38982dcb395b065b87cba1604170597a751704ec623\n"
    "    msme-qwen2.5-1.5b-Q4_K_M.gguf:  62d36ba73e54586cc4606c82312def17c6b7daeb5e19cb483dcaf6f4a0eced61\n"
    "    training_data_v4_merged.jsonl:  f238a4290e0d5a173147c20a52a503cd718149489693c995c245ec99bde016b8\n\n"
    "**Before/after comparison.**"
)

if old not in content:
    print("ERROR: could not find the exact gap. No changes made.")
    print("Paste: sed -n '95,102p' REPORT.md")
else:
    content = content.replace(old, new, 1)
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: checksums block inserted using indented-code style (no backticks).")
