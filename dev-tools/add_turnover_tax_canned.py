"""Add Turnover Tax as a new canned/verified-answer topic, matching the
existing structure exactly."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_keywords_line = '    "license": ["license", "licence", "business permit", "trade license", "single business permit"],\n}'
new_keywords_line = '    "license": ["license", "licence", "business permit", "trade license", "single business permit"],\n    "turnover_tax": ["turnover tax", "tot rate", "tot threshold"],\n}'

if old_keywords_line not in content:
    print("ERROR: Could not find TOPIC_KEYWORDS closing line. No changes made.")
else:
    content = content.replace(old_keywords_line, new_keywords_line)
    print("TOPIC_KEYWORDS updated.")

marker = "\n\nTOPIC_KEYWORDS = {"
if marker not in content:
    print("ERROR: Could not find TOPIC_KEYWORDS start marker. No changes made.")
else:
    new_answer_entry = '''    "turnover_tax": (
        "**Turnover Tax (TOT)** applies to resident persons and corporates in "
        "Kenya whose gross turnover is **more than KES 1,000,000** but **does "
        "not exceed KES 25,000,000** in a year of income. It is chargeable "
        "under Section 12(C) of the Income Tax Act (CAP 470).\\n\\n"
        "- **Rate:** 1.5% on gross sales, effective 1st July 2023 per the "
        "Finance Act 2023\\n"
        "- **Final tax:** TOT is charged on gross sales with **no expense "
        "deductions allowed**\\n"
        "- **Below KES 1,000,000:** exempt from TOT (but other tax "
        "obligations may still apply)\\n"
        "- **Above KES 25,000,000:** must register for the regular Income "
        "Tax regime instead\\n"
        "- **Not applicable to:** rental income, management/professional/"
        "training fees, income already subject to final withholding tax "
        "(e.g. qualifying dividends or interest), and non-resident "
        "taxpayers\\n"
        "- If your turnover reaches **KES 5,000,000** and you deal in "
        "vatable supplies, you must also register for VAT\\n"
        "- You may elect, by written notice to the Commissioner, to opt "
        "out of TOT and remain under the regular Income Tax regime "
        "instead\\n\\n"
        "Confirm your specific position via iTax (itax.kra.go.ke), since "
        "individual circumstances can affect eligibility."
    ),
'''
    content = content.replace(marker, "\n" + new_answer_entry + marker[1:])
    print("CANNED_ANSWERS updated.")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\nDone. Verify with: grep -A5 'turnover_tax' rag_server.py")
