with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

loan_anchor = '    "loan": ["apply for a loan", "apply for financing", "get a loan", "startup loan", "hustler fund", "loan to start"],\n'
loan_new = (
    '    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", '
    '"hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan"],\n'
    + loan_anchor
)

if loan_anchor not in content:
    print("ERROR: could not find loan anchor.")
else:
    content = content.replace(loan_anchor, loan_new, 1)
    print("Inserted hustler_fund_business BEFORE loan (avoids shadowing)")

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
reg_new = (
    '    "class_r_permit": ["class r permit", "eac permit", "east african community permit", '
    '"foreigner certificate", "alien card", "permit for ugandan", "permit for tanzanian", "permit for rwandan"],\n'
    '    "tcc_application": ["tax compliance certificate", "apply for tcc", "tcc application", '
    '"how to get tcc", "tax compliance certificate application"],\n'
    '    "probation_period": ["probation period", "probation length", "how long can probation", '
    '"maximum probation", "probation extension"],\n'
    '    "agpo": ["agpo", "government procurement opportunities", "government tenders for youth", '
    '"30% government procurement", "access to government procurement"],\n'
    + reg_anchor
)

if reg_anchor not in content:
    print("ERROR: could not find registration anchor.")
else:
    content = content.replace(reg_anchor, reg_new, 1)
    print("Inserted class_r_permit, tcc_application, probation_period, agpo BEFORE registration")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
