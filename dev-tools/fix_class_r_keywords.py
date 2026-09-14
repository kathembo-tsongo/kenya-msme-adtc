with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''    "class_r_permit": ["class r permit", "eac permit", "east african community permit", "foreigner certificate", "alien card", "permit for ugandan", "permit for tanzanian", "permit for rwandan"],'''
new = '''    "class_r_permit": ["class r permit", "eac permit", "east african community permit", "foreigner certificate", "alien card", "ugandan need to trade", "ugandan trader", "tanzanian trader", "rwandan trader", "burundian trader", "eac national", "east african citizen business", "foreign trader permit kenya"],'''

if old not in content:
    print("ERROR: could not find anchor.")
else:
    content = content.replace(old, new, 1)
    print("Broadened class_r_permit keywords")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
