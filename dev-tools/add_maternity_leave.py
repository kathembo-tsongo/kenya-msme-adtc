with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

en_anchor = '''        "Check your specific employment contract for any additional leave beyond the statutory minimum."
    ),
    "capital": ('''
en_new = '''        "Check your specific employment contract for any additional leave beyond the statutory minimum."
    ),
    "maternity_paternity_leave": (
        "**Maternity leave** (Section 29, Employment Act 2007): female employees "
        "are entitled to **3 months (90 calendar days)** of maternity leave with "
        "**full pay** -- this can be taken before or after childbirth. Annual "
        "leave and sick leave continue accruing normally during maternity leave; "
        "she's entitled to return to the same or an equivalent position "
        "afterward.\\n\\n**Paternity leave** (Section 29(8)): male employees are "
        "entitled to **2 weeks (14 days)** of paternity leave, also with full "
        "pay, around the birth of their child.\\n\\nBoth are separate from, and "
        "don't reduce, the standard 21-working-day annual leave entitlement. "
        "Dismissing or disadvantaging an employee for taking either is illegal "
        "under the Employment Act."
    ),
    "capital": ('''

count1 = content.count(en_anchor)
print(f"English anchor occurrences: {count1}")
if count1 == 1:
    content = content.replace(en_anchor, en_new, 1)
    changes.append("Added English maternity_paternity_leave")
else:
    changes.append(f"ERROR: English anchor found {count1} times")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

for c in changes:
    print(c)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
