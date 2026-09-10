"""Add M-Pesa Paybill/Till setup as a canned answer, bilingual.
Fixes a genuine procedural error: the model previously said to apply via
'a selected bank branch', when the real process goes through Safaricom."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes_made = []

en_anchor = '''        "to legal action, and company directors can be held personally "
        "liable for unpaid contributions."
    ),'''

en_new = '''        "to legal action, and company directors can be held personally "
        "liable for unpaid contributions."
    ),
    "mpesa_paybill_till": (
        "**Getting an M-Pesa Paybill or Till number** -- apply through "
        "**Safaricom**, not a bank:\\n\\n"
        "- **Till Number**: for retail/point-of-sale (shops, restaurants, "
        "kiosks) -- one till per outlet, customer pays no fee, merchant "
        "pays a small settlement fee (roughly 0.5-1%)\\n"
        "- **Paybill Number**: for recurring collections with an account/"
        "reference number (rent, school fees, utilities, subscriptions)\\n\\n"
        "**How to apply**: visit m-pesaforbusiness.co.ke and click "
        "'Apply Now', or visit any Safaricom shop. You'll need your "
        "national ID, KRA PIN, business registration documents (type "
        "depends on whether you're a sole proprietor, partnership, or "
        "company), and bank account details for settlement. Application "
        "is **free**. Once approved, you'll receive your number by SMS "
        "and activate it by dialing *234# on the registered line."
    ),'''

if en_anchor not in content:
    print("ERROR: could not find English anchor. No changes made to CANNED_ANSWERS.")
else:
    content = content.replace(en_anchor, en_new, 1)
    changes_made.append("English CANNED_ANSWERS updated (mpesa_paybill_till)")

sw_anchor = '''        "kudumu kunaweza kusababisha hatua za kisheria, na wakurugenzi wa "
        "kampuni wanaweza kuwajibika binafsi kwa michango isiyolipwa."
    ),'''

sw_new = '''        "kudumu kunaweza kusababisha hatua za kisheria, na wakurugenzi wa "
        "kampuni wanaweza kuwajibika binafsi kwa michango isiyolipwa."
    ),
    "mpesa_paybill_till": (
        "**Kupata namba ya Paybill au Till ya M-Pesa** -- omba kupitia "
        "**Safaricom**, si benki:\\n\\n"
        "- **Namba ya Till**: kwa biashara za rejareja (maduka, "
        "mikahawa, vibanda) -- till moja kwa kila tawi, mteja halipi "
        "ada, mfanyabiashara hulipa ada ndogo ya malipo (karibu 0.5-1%)\\n"
        "- **Namba ya Paybill**: kwa malipo yanayojirudia yenye namba ya "
        "akaunti/kumbukumbu (kodi, karo za shule, huduma, michango)\\n\\n"
        "**Jinsi ya kuomba**: tembelea m-pesaforbusiness.co.ke na bofya "
        "'Apply Now', au tembelea duka lolote la Safaricom. Utahitaji "
        "kitambulisho chako cha taifa, namba ya PIN ya KRA, hati za "
        "usajili wa biashara (aina inategemea kama wewe ni mmiliki "
        "binafsi, ubia, au kampuni), na maelezo ya akaunti ya benki kwa "
        "malipo. Kuomba ni **bure**. Baada ya kuidhinishwa, utapokea "
        "namba yako kwa SMS na kuiwezesha kwa kupiga *234# kwenye laini "
        "iliyosajiliwa."
    ),'''

if sw_anchor not in content:
    print("ERROR: could not find Kiswahili anchor. No changes made to CANNED_ANSWERS_SW.")
else:
    content = content.replace(sw_anchor, sw_new, 1)
    changes_made.append("Kiswahili CANNED_ANSWERS_SW updated (mpesa_paybill_till)")

kw_anchor = '    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine"],'
kw_new = '''    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine"],
    "mpesa_paybill_till": ["paybill", "till number", "buy goods till", "set up paybill", "mpesa business"],'''

if kw_anchor not in content:
    print("ERROR: could not find TOPIC_KEYWORDS anchor. No changes made there.")
else:
    content = content.replace(kw_anchor, kw_new, 1)
    changes_made.append("TOPIC_KEYWORDS updated (mpesa_paybill_till)")

with open("rag_server.py", "w", encoding="utf-8") as f:
    f.write(content)

print("\n".join(changes_made) if changes_made else "No changes were made -- check errors above.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("\nSYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"\nSYNTAX CHECK: FAILED -- {e}")
    print("Do NOT restart the server until this is fixed.")
