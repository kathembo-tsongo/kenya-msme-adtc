with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = "Kibali chenyewe ni **bure** (KES 0), "
count = content.count(old)
print(f"Occurrences of correct spacing found: {count}")
if count == 0:
    broken = "Kibali chenyeweni **bure**"
    if broken in content:
        content = content.replace(broken, "Kibali chenyewe ni **bure**", 1)
        print("Fixed the missing-space typo")
        with open("rag_server.py", "w", encoding="utf-8") as f:
            f.write(content)
    else:
        print("Could not find either version -- no changes made, please check manually")
else:
    print("Spacing already correct -- no fix needed (the display artifact may just be a terminal rendering issue)")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
