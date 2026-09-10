with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

if "\nimport re\n" in content or content.startswith("import re\n"):
    print("Already imported.")
else:
    old_line = "import requests"
    new_line = "import re\nimport requests"
    if old_line not in content:
        print("ERROR: could not find 'import requests' to anchor the new import. No changes made.")
    else:
        content = content.replace(old_line, new_line, 1)
        with open("rag_server.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("SUCCESS: import re added.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
