with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
new = ('    "registration": ["register a business name", "business name registration", "steps to register a business", '
       '"register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", '
       '"steps to start a business", "kusajili biashara", "naweza kusajili biashara", "jinsi ya kusajili biashara", '
       '"kuanzisha biashara", "nataka kusajili"],\n')

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Added Kiswahili keywords to registration")
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
