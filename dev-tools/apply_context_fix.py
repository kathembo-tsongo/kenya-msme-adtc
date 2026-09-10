"""One-time patch: cap retrieved chunk length in build_context_block()
to prevent context-window overflow, without touching n_ctx (memory budget)."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_func = '''def build_context_block(retrieved):
    parts = [SCOPE_INSTRUCTION]
    if retrieved:
        parts.append("\\n\\nRELEVANT SOURCE MATERIAL (use if it genuinely pertains to the question):\\n")
        for i, r in enumerate(retrieved, 1):
            parts.append(f"[Source {i} — {r['kb']}]\\n{r['text']}\\n")
    return "\\n".join(parts)'''

new_func = '''MAX_CHUNK_CHARS = 700  # ~175-200 tokens per chunk; keeps 4 chunks well under the 2048 context window


def build_context_block(retrieved):
    parts = [SCOPE_INSTRUCTION]
    if retrieved:
        parts.append("\\n\\nRELEVANT SOURCE MATERIAL (use if it genuinely pertains to the question):\\n")
        for i, r in enumerate(retrieved, 1):
            text = r["text"]
            if len(text) > MAX_CHUNK_CHARS:
                text = text[:MAX_CHUNK_CHARS].rsplit(" ", 1)[0] + "..."
            parts.append(f"[Source {i} — {r['kb']}]\\n{text}\\n")
    return "\\n".join(parts)'''

if old_func not in content:
    print("ERROR: Could not find the exact original function text. No changes made.")
    print("The file may have been edited since this patch was written — check manually.")
else:
    content = content.replace(old_func, new_func)
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: build_context_block() patched with MAX_CHUNK_CHARS = 700.")
    print("Restart your server for the change to take effect.")
