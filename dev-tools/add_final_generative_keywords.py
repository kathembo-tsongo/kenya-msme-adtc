with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
reg_new = (
    '    "sole_prop_vs_limited": ["difference between a sole proprietorship", "sole proprietorship and a limited company", "sole proprietorship vs limited company", "sole proprietorship or a limited company"],\n'
    '    "late_filing_penalty": ["penalties for late filing", "late filing of tax returns", "penalty for late filing", "what happens if i file late", "late tax return penalty"],\n'
    '    "etims_general": ["what is etims", "why does my business need etims", "why do i need etims"],\n'
    '    "sacco_vs_bank": ["saccos offer loans differently", "sacco vs bank", "sacco or bank loan", "difference between sacco and bank", "saccos differently from commercial banks"],\n'
    '    "food_business_license": ["food business need to operate", "licenses does a food business", "restaurant license kenya", "food business licenses", "licenses for a restaurant"],\n'
    + reg_anchor
)

if reg_anchor not in content:
    print("ERROR: could not find registration anchor.")
else:
    content = content.replace(reg_anchor, reg_new, 1)
    print("Inserted all 5 new topic keywords BEFORE registration")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
