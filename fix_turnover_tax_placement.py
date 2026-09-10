"""Fix: move the turnover_tax entry from after CANNED_ANSWERS' closing brace
to before it, where it belongs."""
import re

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(
    r'\}\n(    "turnover_tax": \(.*?\),\n)\n*TOPIC_KEYWORDS = \{',
    re.DOTALL
)
m = pattern.search(content)
if not m:
    print("ERROR: could not find the misplaced block. No changes made.")
    print("Paste the output of: sed -n '260,275p' rag_server.py")
else:
    entry = m.group(1)
    fixed = entry + "}\n\n\nTOPIC_KEYWORDS = {"
    content = content[:m.start()] + fixed + content[m.end():]
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Fixed: turnover_tax entry moved inside CANNED_ANSWERS, before its closing brace.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED — rag_server.py is valid Python.")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED — {e}")
    print("Do NOT restart the server until this is fixed.")
