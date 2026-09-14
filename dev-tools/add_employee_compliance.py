with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "with all documents in order typically takes **5-10 working days**."
    ),
}'''

new_content = '''        "with all documents in order typically takes **5-10 working days**."
    ),
    "employee_compliance_checklist": (
        "For a trading enterprise with permanent staff, here's what to maintain:\\n\\n"
        "**Employment contracts**: a written contract (or at minimum a written "
        "statement of particulars, required within 2 months of start date for "
        "any employment lasting more than 3 months) covering start date, job "
        "description, salary, working hours, and leave entitlement.\\n\\n"
        "**Statutory deductions, per employee, per month**:\\n"
        "- **NSSF**: 6% employee + 6% employer (matched), Tier I up to KES "
        "9,000, Tier II up to KES 108,000\\n"
        "- **PAYE**: progressive bands from 10% to 35%, less KES 2,400 "
        "personal relief\\n"
        "- **SHIF** (Social Health Insurance Fund -- this replaced NHIF in "
        "October 2024): 2.75% of gross pay, employee-side only, no cap\\n"
        "- **Housing Levy**: 1.5% employee + 1.5% employer, no minimum "
        "income threshold\\n\\n"
        "**Leave records**: minimum 21 working days of annual leave per 12 "
        "months of service (Employment Act Section 28).\\n\\n"
        "**Payroll records**: document each employee's monthly salary and "
        "all deductions above, and remit them on time -- NSSF, PAYE, SHIF, "
        "and Housing Levy all follow the same 9th-of-the-following-month "
        "deadline. Keep these records available for inspection, and confirm "
        "your county's specific retention-period requirement, since this "
        "isn't fully standardized nationally."
    ),
}'''

if anchor not in content:
    print("ERROR: could not find anchor.")
else:
    content = content.replace(anchor, new_content, 1)
    print("Added employee_compliance_checklist canned answer")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
