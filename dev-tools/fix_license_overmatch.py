"""Narrow the 'license' canned-topic keywords so specific license questions
(food, pharmacy, tech, Unified Business Permit) fall through to real RAG
retrieval + generation instead of a generic canned answer."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_line = '    "license": ["license", "licence", "business permit", "trade license", "single business permit"],'
new_line = '    "license": ["single business permit", "what license do i need", "what licence do i need", "trade license requirements"],'

if old_line not in content:
    print("ERROR: could not find the license keyword line. No changes made.")
else:
    content = content.replace(old_line, new_line)
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: license keywords narrowed.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
