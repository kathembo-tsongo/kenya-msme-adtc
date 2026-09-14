with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

reg_anchor = '    "registration": ["register a business name", "business name registration", "steps to register a business", "register a small business", "register a business in kenya", "how to register a business", "start a business in kenya", "steps to start a business"],\n'
reg_new = (
    '    "employee_compliance_checklist": ["employee compliance", "statutory deductions", '
    '"legal documentation and statutory", "compliance under the kenyan employment act", '
    '"documentation and statutory deductions", "three permanent staff", "permanent staff members", '
    '"statutory deductions a small trading enterprise"],\n'
    + reg_anchor
)

if reg_anchor not in content:
    print("ERROR: could not find registration anchor -- may have already been modified.")
else:
    content = content.replace(reg_anchor, reg_new, 1)
    print("Inserted employee_compliance_checklist keywords BEFORE registration")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
