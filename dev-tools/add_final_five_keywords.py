with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
reg_new = (
    '    "unified_business_permit": ["unified business permit", "ubp nairobi", "nairobi business permit"],\n'
    '    "pharmacy_license": ["pharmacy license", "chemist shop license", "poisons board", "pharmacy and poisons board", "open a pharmacy", "chemist shop kenya"],\n'
    '    "ca_license": ["communications authority", "ca license kenya", "telecommunications license kenya"],\n'
    '    "nssf_registration": ["register my business and employees", "nssf registration", "register for nssf", "register my employees for nssf"],\n'
    '    "keproba": ["keproba", "kenya export promotion", "export promotion and branding agency", "brand kenya agency"],\n'
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
