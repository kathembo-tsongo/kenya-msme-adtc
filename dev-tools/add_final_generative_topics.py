with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''"risk above from day one."
    ),'''

new_content = '''"risk above from day one."
    ),
    "sole_prop_vs_limited": (
        "The core difference is **liability and separateness**. A **sole "
        "proprietorship** isn't a separate legal entity from you -- you and "
        "the business are the same in law, meaning you carry **unlimited "
        "personal liability** for business debts, and you use your own "
        "**personal KRA PIN**. It's fast and cheap to set up, with no "
        "minimum capital.\\n\\nA **limited company** is a separate legal "
        "person from its owners -- shareholders' liability is generally "
        "limited to what they've invested in shares, and the company gets "
        "its **own separate KRA PIN**, its own bank account, and can enter "
        "contracts, sue, or be sued in its own name. There's **no legal "
        "minimum share capital** required to register one, though it "
        "involves more paperwork (Memorandum/Articles of Association, "
        "CR1/CR2/CR8 forms) and ongoing compliance (annual returns to BRS) "
        "than a sole proprietorship. Many businesses start as sole "
        "proprietorships and convert to a limited company as they grow, "
        "specifically to gain that liability protection."
    ),
    "late_filing_penalty": (
        "Penalties depend on which return and whether it's late filing or "
        "late payment -- both apply to KRA obligations under the **Tax "
        "Procedures Act 2015**:\\n\\n"
        "- **Individual income tax**: KES 2,000 per return for late filing\\n"
        "- **Company/partnership income tax**: KES 20,000 or 5% of the tax "
        "due, whichever is higher, for late filing; late payment adds "
        "another 5% plus 1% monthly interest on the unpaid amount\\n"
        "- **PAYE**: late filing is 25% of the tax due or KES 10,000, "
        "whichever is higher; late payment is 5% plus 1% monthly interest\\n"
        "- **VAT**: late filing is 5% of the tax due or KES 10,000, "
        "whichever is higher; late payment adds 5% plus 1% monthly "
        "interest\\n\\n"
        "**Even with zero income or sales, you must still file a nil "
        "return** -- skipping it triggers the same automatic penalty as "
        "any other missed return. Penalties apply automatically the day "
        "after the deadline, with no prior warning, so it's always better "
        "to file on time even if you can't pay yet (unpaid tax only draws "
        "interest, which is far less costly than filing-plus-payment "
        "penalties combined)."
    ),
    "etims_general": (
        "**eTIMS** (electronic Tax Invoice Management System) is KRA's "
        "system for generating tax-compliant, verifiable electronic "
        "invoices/receipts -- it's required for VAT-registered businesses, "
        "and for anyone wanting business expenses to be tax-deductible, "
        "since KRA only accepts eTIMS-generated invoices as valid proof of "
        "purchase.\\n\\n**Why your business needs it**: without eTIMS "
        "invoices, your business expenses may not be deductible for tax "
        "purposes, and customers who need to claim their own input VAT or "
        "expense deductions can't do so from a non-eTIMS invoice -- making "
        "it harder to sell to other VAT-registered businesses.\\n\\nFor "
        "smaller businesses, the free **eTIMS Lite** option (via web "
        "portal or USSD *222#) is the simplest way to comply without "
        "buying equipment. Non-compliance penalties can reach up to **KES "
        "1,000,000 or 10% of the tax involved**, whichever is higher."
    ),
    "sacco_vs_bank": (
        "**SACCOs** typically offer meaningfully cheaper loans than "
        "commercial banks -- commonly **10-14% per annum** (reducing "
        "balance), often fixed by the SACCO's own annual general meeting "
        "rather than fluctuating with the Central Bank Rate. Commercial "
        "**bank** loans typically run **13-20%+ per annum** and move with "
        "CBK rate changes.\\n\\n**Key trade-off**: SACCOs require you to "
        "**join and build a savings history first** (commonly 3-6 months) "
        "before you can borrow, and loan amounts are often capped as a "
        "multiple of your savings (roughly 3-5x). Banks generally don't "
        "require prior membership/savings and can lend larger, more "
        "flexible amounts, especially against collateral -- but at a "
        "higher rate. SACCO members also earn dividends on their shares "
        "and savings, which partially offsets the cost of borrowing, a "
        "benefit a bank account doesn't offer."
    ),
    "food_business_license": (
        "A food business (restaurant, cafe, bakery, shop) needs several "
        "layers, on top of your standard county business permit "
        "(Single/Unified Business Permit):\\n\\n"
        "- **Health/Food Hygiene Certificate**: issued by your county "
        "health department, confirming your premises meet hygiene "
        "standards -- typically KES 2,000-5,000, required before opening\\n"
        "- **Food Handler's Health Certificate**: required for **every "
        "individual employee** who handles food, obtained after a medical "
        "check-up (roughly KES 1,000 per person)\\n"
        "- **Fire Safety Certificate**: mandatory for all businesses, "
        "requiring fire extinguishers and a county fire department "
        "inspection, renewed annually\\n"
        "- **Restaurant-specific**: registration with the **Tourism "
        "Regulatory Authority (TRA)** under the Tourism Act 2011, if you "
        "operate as a restaurant\\n\\n"
        "If you manufacture or package food products for sale (not just "
        "serve food on-site), you'll also need **KEBS** certification "
        "(Standardization Mark) specific to packaged/processed goods."
    ),'''

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added all 5 new canned answers")
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
