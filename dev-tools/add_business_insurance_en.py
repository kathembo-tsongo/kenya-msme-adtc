with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "isn't fully standardized nationally."
    ),
}


CANNED_ANSWERS_SW = {'''

new_content = '''        "isn't fully standardized nationally."
    ),
    "business_insurance": (
        "Kenya's insurance industry is regulated by the **Insurance "
        "Regulatory Authority (IRA)**, not KRA -- KRA is the tax "
        "authority and has no role in insurance.\\n\\n**Compulsory "
        "insurance, if you have employees**: cover under the **Work "
        "Injury Benefits Act (WIBA)**, protecting employees injured or "
        "disabled at work -- this is legally required, not optional. If "
        "your business uses any motor vehicle, **motor third-party "
        "liability insurance** is also compulsory.\\n\\n**Common optional "
        "cover worth considering**: public liability insurance (covers "
        "injury to customers/visitors on your premises), property/fire "
        "insurance (covers your stock, equipment, and premises), and "
        "business interruption cover (covers lost income if you have to "
        "close temporarily, e.g. after a fire).\\n\\nCoverage details, "
        "exclusions, and pricing vary significantly by insurer -- confirm "
        "specifics with a **licensed insurer or broker** (check the IRA's "
        "list of licensed providers at ira.go.ke), not KRA."
    ),
}


CANNED_ANSWERS_SW = {'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added business_insurance (English) canned answer")
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
