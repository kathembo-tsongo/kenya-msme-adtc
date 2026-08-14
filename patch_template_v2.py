from gguf import GGUFReader

r = GGUFReader('./model/msme-qwen2.5-1.5b-Q4_K_M.gguf')
template = None
for f in r.fields.values():
    if f.name == 'tokenizer.chat_template':
        template = bytes(f.parts[-1]).decode('utf-8')
        break

if template is None:
    raise SystemExit("chat_template field not found")

OLD_DIGEST_TAIL = (
    "Vuka loan up to KES 5,000,000 at 8% p.a."
)
# Use a literal backslash-n (two chars) to match the template's own
# escaping convention -- NOT a real newline byte.
NEW_DIGEST_TAIL = (
    "Vuka loan up to KES 5,000,000 at 8% p.a.\\n"
    "- When a question asks you to calculate a KES amount from a salary or figure the user gives, "
    "compute it step by step (percentage times the given amount, per side) and double-check the "
    "arithmetic before stating a final figure. Never state a Shilling total that isn't the direct "
    "product of the stated percentage and the given amount.\\n"
    "- Do not invent additional numbers, worked examples, or calculations beyond what is explicitly "
    "requested or listed above."
)

count = template.count(OLD_DIGEST_TAIL)
print(f"Found {count} occurrence(s) of the digest tail")
new_template = template.replace(OLD_DIGEST_TAIL, NEW_DIGEST_TAIL)

with open('patched_chat_template.jinja', 'w') as f:
    f.write(new_template)

print("Wrote patched_chat_template.jinja")
