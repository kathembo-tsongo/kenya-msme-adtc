"""Fix: move the broad 'registration' topic to the END of TOPIC_KEYWORDS,
so it acts as a fallback rather than shadowing more specific, narrower
topics (minimum_wage, housing_levy, etc.) that happen to share generic
words like 'business' or 'start' with its broadened keyword list."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

reg_line = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'

if reg_line not in content:
    print("ERROR: could not find the exact registration line to move. No changes made.")
    print("Paste: grep -n 'registration.*register a business name' rag_server.py")
else:
    content_without = content.replace(reg_line, "", 1)
    anchor = '    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay"],\n}'
    if anchor not in content_without:
        print("ERROR: could not find the TOPIC_KEYWORDS closing anchor. No changes made.")
    else:
        new_ending = '    "minimum_wage": ["minimum wage", "minimum salary", "lowest wage", "minimum pay"],\n' + reg_line + '}'
        content_fixed = content_without.replace(anchor, new_ending, 1)
        with open("rag_server.py", "w", encoding="utf-8") as f:
            f.write(content_fixed)
        print("SUCCESS: 'registration' moved to end of TOPIC_KEYWORDS (now a fallback, not a shadower).")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
    print("Do NOT restart the server until this is fixed.")
