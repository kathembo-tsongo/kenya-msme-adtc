with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

old1 = '"- Mandatory once your annual taxable turnover exceeds **KES 5,000,000**\\n"'
new1 = '"- Mandatory once your annual taxable turnover exceeds **KES 5,000,000 (5 million)**\\n"'
count1 = content.count(old1)
print(f"VAT anchor occurrences found: {count1}")
if count1 == 1:
    content = content.replace(old1, new1, 1)
    changes.append("VAT: added (5 million)")
else:
    changes.append(f"ERROR: VAT anchor found {count1} times, expected 1")

old2 = '"needs, accessible via *254#.\\n\\nFor business specifically, Hustler "'
new2 = ('"needs, accessible via *254# on your **M-PESA**-registered line -- you\'ll need "'
        '"a valid **Kenyan national ID** and an active SIM card, no collateral required. "'
        '"\\n\\nFor business specifically, Hustler "')
count2 = content.count(old2)
print(f"Hustler Fund anchor occurrences found: {count2}")
if count2 == 1:
    content = content.replace(old2, new2, 1)
    changes.append("hustler_fund_business (EN): added M-PESA and national ID")
else:
    changes.append(f"ERROR: hustler_fund_business anchor found {count2} times, expected 1")

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
