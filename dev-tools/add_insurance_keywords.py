with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business", "kusajili biashara", "naweza kusajili biashara", "jinsi ya kusajili biashara", "kuanzisha biashara", "nataka kusajili"],\n'
reg_new = (
    '    "business_insurance": ["insurance does a", "business insurance", "insurance for my business", '
    '"what insurance", "bima ya biashara", "bima gani", "nahitaji bima"],\n'
    + reg_anchor
)

count = content.count(reg_anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(reg_anchor, reg_new, 1)
    print("Inserted business_insurance keywords BEFORE registration")
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
