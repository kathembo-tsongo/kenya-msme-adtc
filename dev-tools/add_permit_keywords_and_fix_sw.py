with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
reg_new = (
    '    "no_permit_penalty": ["without a county permit", "operate a business without", "without a permit", "penalty for operating without", "no business permit"],\n'
    + reg_anchor
)
if reg_anchor in content:
    content = content.replace(reg_anchor, reg_new, 1)
    changes.append("Added no_permit_penalty keywords")
else:
    changes.append("ERROR: registration anchor not found")

hf_anchor = '    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", "hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan", "personal loan and business loan", "hustler fund personal loan and business", "difference between the hustler fund", "apply for the hustler fund", "hustler fund and what are the eligibility", "eligibility requirements for the hustler fund"],\n'
hf_new = '    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", "hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan", "personal loan and business loan", "hustler fund personal loan and business", "difference between the hustler fund", "apply for the hustler fund", "hustler fund and what are the eligibility", "eligibility requirements for the hustler fund", "mkopo kutoka hustler fund", "kupata mkopo kutoka hustler fund", "hustler fund na ninahitaji", "ninahitaji nini kustahili"],\n'
if hf_anchor in content:
    content = content.replace(hf_anchor, hf_new, 1)
    changes.append("Added Kiswahili keywords to hustler_fund_business")
else:
    changes.append("ERROR: hustler_fund_business anchor not found")

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
