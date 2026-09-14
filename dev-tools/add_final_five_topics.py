with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

anchor = '''Apply through WEF's regional offices, or online at wef.go.ke."
    ),'''

new_content = '''Apply through WEF's regional offices, or online at wef.go.ke."
    ),
    "unified_business_permit": (
        "In Nairobi County specifically, this is the **Unified Business Permit "
        "(UBP)** -- a single annual license that bundles what used to be "
        "several separate approvals (trade license, fire inspection, food/"
        "health certificate, advertisement/signage permit) into one "
        "application. Apply via the **NairobiPay self-service portal "
        "(nairobiservices.go.ke)**, dial ***647#**, or visit City Hall Annex "
        "in person.\\n\\nThe fee depends on your business category and size "
        "(a small shop might pay around KES 4,000 plus a KES 200 application "
        "fee; larger operations pay significantly more) -- confirm your "
        "exact category's fee on the portal. It runs on a **January-"
        "December annual cycle**; renewal applications typically open in "
        "November, with payment expected by around March 31 to avoid "
        "escalating late penalties. Other counties (Mombasa, Meru, Kisumu, "
        "and several others) use eCitizen instead of a county-specific "
        "portal for their equivalent single business permit."
    ),
    "pharmacy_license": (
        "Operating a pharmacy or chemist shop requires licensing from the "
        "**Pharmacy and Poisons Board (PPB)**, the national medicines "
        "regulator under the Pharmacy and Poisons Act (Cap 244) -- this is "
        "in addition to, not instead of, your county Single Business Permit "
        "(roughly KES 5,000-30,000).\\n\\n**Key requirement**: everyone "
        "holding a financial interest in the pharmacy must be a registered "
        "pharmacist or enrolled pharmaceutical technologist -- you generally "
        "can't own a pharmacy purely as a non-pharmacist investor. The "
        "designated superintendent pharmacist also needs their own annual "
        "practicing license from PPB.\\n\\n**Process**: register your "
        "premises with PPB, then pass a premises inspection covering proper "
        "shelving, ventilation, a dispensing area separate from the sales "
        "counter, a lockable poisons cabinet, a refrigerator for cold-chain "
        "products, and Green Cross signage. Licenses are issued after a "
        "successful inspection and must be renewed annually (all PPB "
        "licenses expire December 31)."
    ),
    "ca_license": (
        "Not every tech startup needs this -- the **Communications "
        "Authority of Kenya (CA)** specifically licenses telecommunications, "
        "broadcasting, internet service provision, and postal/courier "
        "operators, not general software or app businesses. If your startup "
        "purely builds an app or website without operating telecom "
        "infrastructure or providing regulated content/network services, you "
        "likely don't need a CA license at all.\\n\\nIf you DO fall into a "
        "regulated category, CA's Unified Licensing Framework covers three "
        "main types: **Network Facilities Provider**, **Application Service "
        "Provider**, and **Content Service Provider** (plus separate "
        "licenses for broadcasting, equipment type-approval, and courier/"
        "postal services). Applications need a cover letter to the Director "
        "of Licensing, your certificate of registration, company documents "
        "(CR12 for companies), and a list of directors -- foreign-owned "
        "companies need at least 30% Kenyan shareholding. Processing runs on "
        "a first-come-first-served basis with a stated turnaround of around "
        "135 days."
    ),
    "nssf_registration": (
        "**As an employer**, register via the NSSF Employer Self-Service "
        "portal (selfservice.nssf.or.ke) -- select 'Employer Registration' "
        "if you've never registered before. It's worth getting your **KRA "
        "PIN first**, since you'll need it during registration. Once "
        "approved, you're issued an employer number, often on the spot.\\n\\n"
        "**Registration is mandatory** for every employer with even one "
        "employee earning KES 1,000 or more per month -- this includes "
        "casual, temporary, and part-time workers, not just permanent "
        "staff. Skipping registration is a legal offense under the NSSF Act "
        "2013.\\n\\n**For each employee**: they can register in person at any "
        "NSSF office with their national ID/passport/Alien Card and an "
        "introduction letter from you as their employer, after which they "
        "receive an NSSF membership number you'll need to remit their "
        "contributions."
    ),
    "keproba": (
        "**KEPROBA** (Kenya Export Promotion and Branding Agency) is a "
        "state corporation (formed 2019, merging the former Export "
        "Promotion Council and Brand Kenya Board) that supports Kenyan "
        "exporters and promotes 'Brand Kenya' internationally.\\n\\n"
        "**What it actually offers**: guidance on export procedures and "
        "documentation, market intelligence and market-entry requirements "
        "for target countries, capacity-building through export training "
        "and coaching, organized trade missions and trade fair "
        "participation, and support with **product development and "
        "branding** -- including packaging, labelling, and brand "
        "positioning to help your goods resonate with international "
        "buyers. It particularly prioritizes bringing youth- and "
        "women-led producer groups into the export process. Reach out "
        "through KEPROBA's offices or makeitkenya.go.ke to access these "
        "services."
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
