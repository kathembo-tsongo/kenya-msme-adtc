with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '"kinapatikana kupitia *254#.\\n\\nKwa biashara hasa, Hustler Fund "'
new = ('"kinapatikana kupitia *254# kwenye laini yako iliyosajiliwa ya **M-PESA** -- utahitaji "'
       '"**kitambulisho cha taifa cha Kenya** na SIM kadi inayotumika, hakuna dhamana inayohitajika. "'
       '"\\n\\nKwa biashara hasa, Hustler Fund "')

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("hustler_fund_business (SW): added M-PESA and national ID")
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
