with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_line = '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction"],'
new_line = '    "shif_rate": ["shif rate", "shif contribution", "shif percentage", "how much shif", "shif deduction", "contribute to shif", "employer shif", "shif employer", "pay to shif", "shif pay"],'

if old_line not in content:
    print("ERROR: could not find the shif_rate keyword line. No changes made.")
else:
    content = content.replace(old_line, new_line)
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: shif_rate keywords broadened.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
