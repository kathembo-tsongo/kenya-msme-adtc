with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_leave = '    "leave": ["annual leave", "leave entitlement", "leave days", "likizo ya mwaka", "siku za likizo", "haki ya likizo"],\n'
new_content = (
    '    "maternity_paternity_leave": ["maternity leave", "paternity leave", "maternity leave entitlement", '
    '"likizo ya uzazi", "likizo ya baba"],\n'
    '    "leave": ["annual leave", "leave days", "likizo ya mwaka", "siku za likizo", "annual leave entitlement"],\n'
)

count = content.count(old_leave)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old_leave, new_content, 1)
    print("Added maternity_paternity_leave keywords BEFORE leave, narrowed leave's keywords")
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
