with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "grows with consistent on-time repayment history."
    ),
}'''

new_content = '''        "grows with consistent on-time repayment history."
    ),
    "sole_prop_to_llc": (
        "Kenya doesn't have a single-step 'conversion' -- practically, it's two "
        "separate actions: **(1) cease your existing business name** by filing "
        "**Form BN6** on eCitizen, and **(2) register a new private limited "
        "company** using **Forms CR1, CR2, CR8** plus Articles/Memorandum of "
        "Association (BRS provides standard templates, or you can customize "
        "them). You can typically reserve and reuse the same business name, "
        "now with 'Limited' or 'Ltd' added.\\n\\n"
        "**On KRA PIN specifically**: your sole proprietorship used your "
        "**personal KRA PIN**. The new company needs its **own separate "
        "company PIN**, applied for via iTax by selecting 'Non-Individual' as "
        "the taxpayer type -- and every director/shareholder must already "
        "have their own individual KRA PIN before the company PIN application "
        "can go through.\\n\\n"
        "**On fees**: expect two separate government charges -- business name "
        "cessation, and private limited company registration (roughly KES "
        "10,650-10,750 based on current BRS fee schedules, though I'd confirm "
        "the exact current figure on eCitizen directly). Note there is **no "
        "legal minimum share capital** requirement, though many people choose "
        "a nominal figure like KES 100,000 as practice. A clean conversion "
        "with all documents in order typically takes **5-10 working days**."
    ),
}'''

if anchor not in content:
    print("ERROR: could not find anchor for new canned answer.")
else:
    content = content.replace(anchor, new_content, 1)
    print("Added sole_prop_to_llc canned answer")

old_kw = '    "kra_pin": ["kra pin"],\n'
new_kw = ('    "sole_prop_to_llc": ["transition into a limited", "convert my sole proprietorship", '
          '"converting sole proprietorship", "convert a sole proprietorship", '
          '"sole proprietorship into a limited", "sole proprietorship to a limited", '
          '"convert business name to company", "business name to limited company", '
          '"sole prop to llc", "sole proprietorship to llc"],\n'
          '    "kra_pin": ["how do i get a kra pin", "kra pin registration", "apply for kra pin", '
          '"get a kra pin", "kra pin for my business"],\n')

if old_kw not in content:
    print("ERROR: could not find kra_pin keyword line to fix.")
else:
    content = content.replace(old_kw, new_kw, 1)
    print("Narrowed kra_pin keywords and added sole_prop_to_llc routing")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
