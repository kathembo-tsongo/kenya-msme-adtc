with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '    "vat": ["vat registration", "vat threshold"],'
new = ('    "vat": ["vat registration", "vat threshold", "register for vat", '
       '"required to register for vat", "do i need to register for vat", '
       '"vat registration threshold"],')

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Broadened vat keywords")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
