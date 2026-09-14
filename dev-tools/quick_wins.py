with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

old1 = "Kenya doesn't have a single-step 'conversion' -- practically"
new1 = "Kenya doesn't have a single-step way to convert a business -- there's no direct 'conversion' process, practically"
if old1 in content:
    content = content.replace(old1, new1, 1)
    changes.append("sole_prop_to_llc: added 'convert'")
else:
    changes.append("ERROR: sole_prop_to_llc anchor not found")

old2 = 'VAT registration is mandatory once your annual taxable turnover exceeds **KES 5,000,000**;'
new2 = 'VAT registration is mandatory once your annual taxable turnover exceeds **KES 5,000,000 (5 million)**;'
if old2 in content:
    content = content.replace(old2, new2, 1)
    changes.append("VAT: added '5 million' phrasing")
else:
    changes.append("ERROR: VAT anchor not found")

old3 = ('"The basic **Personal Loan** tier (KES 500 to KES 50,000, 8% per '
        'annum, repayable in 14 days) can be used for business or personal '
        'needs, accessible via *254#.\\n\\nFor business specifically, Hustler '
        'Fund also offers group-based **Biashara/Enterprise loans** (for '
        'chamas, cooperatives, or registered groups) and higher-tier loans '
        'for **registered businesses with a KRA PIN**, both at the same 8% '
        'per annum rate but with larger amounts and longer repayment periods '
        'than the personal tier. Your loan limit and access to higher tiers '
        'grows with consistent on-time repayment history."')
new3 = ('"To apply: dial *254# on your **M-PESA**-registered line, or use the Hustler '
        'Fund app -- you need a **Kenyan national ID** and an active, registered SIM card, '
        'no collateral required. The basic **Personal Loan** tier (KES 500 to KES 50,000, '
        '8% per annum, repayable in 14 days) can be used for business or personal '
        'needs, disbursed directly to your M-PESA wallet.\\n\\nFor business specifically, Hustler '
        'Fund also offers group-based **Biashara/Enterprise loans** (for '
        'chamas, cooperatives, or registered groups) and higher-tier loans '
        'for **registered businesses with a KRA PIN**, both at the same 8% '
        'per annum rate but with larger amounts and longer repayment periods '
        'than the personal tier. Your loan limit and access to higher tiers '
        'grows with consistent on-time repayment history."')
if old3 in content:
    content = content.replace(old3, new3, 1)
    changes.append("hustler_fund_business (EN): added M-PESA and national ID")
else:
    changes.append("ERROR: hustler_fund_business EN anchor not found")

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
