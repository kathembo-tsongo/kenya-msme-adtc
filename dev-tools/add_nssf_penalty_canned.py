"""Add NSSF late-payment penalty as a canned answer, bilingual.
Inserted BEFORE the existing 'nssf' entry in TOPIC_KEYWORDS, since
get_canned_topic() returns the first matching topic in dict order --
without this ordering, the generic 'nssf' keyword would always win
and return the wrong (contribution-rate) answer for penalty questions."""

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

changes_made = []

en_anchor = '''        "Social Protection or the current Kenya Gazette Wage Order, "
        "rather than relying on a single number."
    ),'''

en_new = '''        "Social Protection or the current Kenya Gazette Wage Order, "
        "rather than relying on a single number."
    ),
    "nssf_penalty": (
        "**NSSF late payment penalty in Kenya**: a penalty of **5% of the "
        "outstanding contribution** is charged for each month, or part of "
        "a month, that remittance remains late. Some sources also note "
        "additional monthly interest on top of this base penalty -- "
        "confirm the full current figure directly with NSSF, since this "
        "detail varies across sources. Persistent non-compliance can lead "
        "to legal action, and company directors can be held personally "
        "liable for unpaid contributions."
    ),'''

if en_anchor not in content:
    print("ERROR: could not find English anchor. No changes made to CANNED_ANSWERS.")
else:
    content = content.replace(en_anchor, en_new, 1)
    changes_made.append("English CANNED_ANSWERS updated (nssf_penalty)")

sw_anchor = '''        "Ulinzi wa Jamii au Amri ya Mishahara ya sasa ya Kenya Gazette, "
        "badala ya kutegemea nambari moja."
    ),'''

sw_new = '''        "Ulinzi wa Jamii au Amri ya Mishahara ya sasa ya Kenya Gazette, "
        "badala ya kutegemea nambari moja."
    ),
    "nssf_penalty": (
        "**Adhabu ya kuchelewesha malipo ya NSSF nchini Kenya**: faini ya "
        "**5% ya mchango usiolipwa** hutozwa kwa kila mwezi, au sehemu ya "
        "mwezi, ambao malipo yanabaki kuchelewa. Baadhi ya vyanzo pia "
        "hutaja riba ya ziada ya kila mwezi juu ya faini hii ya msingi -- "
        "thibitisha kiwango kamili cha sasa moja kwa moja na NSSF, kwa "
        "kuwa maelezo haya hutofautiana kati ya vyanzo. Kutozingatia kwa "
        "kudumu kunaweza kusababisha hatua za kisheria, na wakurugenzi wa "
        "kampuni wanaweza kuwajibika binafsi kwa michango isiyolipwa."
    ),'''

if sw_anchor not in content:
    print("ERROR: could not find Kiswahili anchor. No changes made to CANNED_ANSWERS_SW.")
else:
    content = content.replace(sw_anchor, sw_new, 1)
    changes_made.append("Kiswahili CANNED_ANSWERS_SW updated (nssf_penalty)")

kw_anchor = '    "nssf": ["nssf", "national social security fund"],'
kw_new = '''    "nssf_penalty": ["nssf penalty", "late nssf", "nssf late payment", "penalty for late nssf", "nssf fine"],
    "nssf": ["nssf", "national social security fund"],'''

if kw_anchor not in content:
    print("ERROR: could not find the 'nssf' TOPIC_KEYWORDS line. No changes made there.")
else:
    content = content.replace(kw_anchor, kw_new, 1)
    changes_made.append("TOPIC_KEYWORDS updated (nssf_penalty inserted BEFORE nssf for priority)")

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
