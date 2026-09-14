with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''        "with all documents in order typically takes **5-10 working days**."
    ),'''
wef_new = '''        "with all documents in order typically takes **5-10 working days**."
    ),
    "wef": (
        "The **Women Enterprise Fund (WEF)** is a real, distinct government agency "
        "(established 2007, under the Ministry of Public Service, Youth & Gender "
        "Affairs) -- not to be confused with YEDF (youth-focused) or the Hustler "
        "Fund. **Eligibility: any Kenyan woman aged 18 or older**, applying "
        "individually or as part of a registered group.\\n\\n"
        "**Key products**:\\n"
        "- **Tuinuke Chama Loan** (via the Constituency Women Enterprise Scheme): "
        "for registered women's groups of 10-30 members (at least 70% women, "
        "100% women in leadership), registered with Social Services for at "
        "least 3 months, with a bank/SACCO account -- low-cost with a small "
        "administration charge\\n"
        "- **LPO Financing**: for individual women-owned businesses needing to "
        "fulfill purchase orders or tenders\\n\\n"
        "Apply through WEF's regional offices, or online at wef.go.ke."
    ),'''

if anchor not in content:
    print("ERROR: could not find anchor for WEF.")
else:
    content = content.replace(anchor, wef_new, 1)
    print("Added Women Enterprise Fund (wef) canned answer")

old_kw = ('    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", '
          '"hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan"],\n')
new_kw = ('    "hustler_fund_business": ["hustler fund business", "hustler fund for my business", '
          '"hustler fund biashara loan", "business tier hustler fund", "hustler fund enterprise loan", '
          '"personal loan and business loan", "hustler fund personal loan and business", '
          '"difference between the hustler fund", "apply for the hustler fund", '
          '"hustler fund and what are the eligibility", "eligibility requirements for the hustler fund"],\n')

if old_kw not in content:
    print("ERROR: could not find hustler_fund_business keyword line.")
else:
    content = content.replace(old_kw, new_kw, 1)
    print("Broadened hustler_fund_business keywords")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
