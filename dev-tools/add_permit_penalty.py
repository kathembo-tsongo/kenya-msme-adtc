with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''"services."
    ),'''
new = '''"services."
    ),
    "no_permit_penalty": (
        "Operating without a valid county business permit is illegal in "
        "Kenya, under the **County Governments Act 2012** combined with "
        "each county's own Finance Act and Trade Licensing Act (Nairobi's "
        "trade licensing, for example, falls under its own County Trade "
        "Licensing Act).\\n\\n**Consequences can include**:\\n"
        "- **Fines**: commonly cited in the range of KES 50,000-200,000, "
        "though this varies significantly by county -- confirm your "
        "specific county's penalty schedule\\n"
        "- **Closure orders**: county inspectors can issue an immediate "
        "closure order, shutting your business until you comply\\n"
        "- **Possible imprisonment**: in serious or repeated cases, "
        "directors/owners can face criminal prosecution personally, not "
        "just the business\\n"
        "- **Back-payment of penalties**: on top of the permit fee itself "
        "once you do comply\\n\\n"
        "Most counties allow a grace period (commonly 30-60 days after "
        "expiry) before penalties kick in for a *lapsed* permit -- but "
        "operating with no permit at all from the start carries the fuller "
        "risk above from day one."
    ),'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new, 1)
    print("Added no_permit_penalty canned answer")
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
