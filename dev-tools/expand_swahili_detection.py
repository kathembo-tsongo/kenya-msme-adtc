with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''    common_swahili_words = [
        "ninahitaji", "kuhusu", "biashara", "nini", "vipi", "wapi", "gani",
        "je", "ninataka", "naomba",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
    ]'''

new = '''    common_swahili_words = [
        "ninahitaji", "kuhusu", "biashara", "nini", "vipi", "wapi", "gani",
        "je", "ninataka", "naomba", "ngapi", "nataka",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
        "ushuru", "mwezi", "kiasi", "leseni", "ada", "pesa", "mkopo",
        "kibali", "ruhusa", "malipo", "faida", "huduma", "mwaka",
    ]'''

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Expanded Swahili detection word list")
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
