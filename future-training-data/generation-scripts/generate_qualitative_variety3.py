import json
import random

random.seed(19)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []
biz_types = ["a small retail shop", "a salon", "a mechanic workshop", "a restaurant", "a tech startup",
             "a farming business", "a boutique", "a hardware store", "a barber shop", "a trading business"]

def add(user, assistant):
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": user}, {"role": "assistant", "content": assistant}]})

yedf_answer = ("**YEDF (Youth Enterprise Development Fund)** -- apply via youthfund.go.ke, with products including "
               "Vuka, Talanta, Agribizz, and Vijana Bahari loans, plus LPO financing. You'll need Form 1A with your "
               "county/constituency details. This sits alongside other government-backed options: **Hustler Fund** "
               "(via USSD *254# or the app, no collateral), **SACCOs** (require membership and savings history "
               "first), and **commercial banks** (require registration, financial records, and collateral for "
               "larger amounts).")
yedf_qs = [
    "What government loan options exist for a young entrepreneur starting {biz}?",
    "How do I apply for YEDF funding for my business?",
    "What's the difference between YEDF and the Hustler Fund?",
]
for _ in range(6):
    q = random.choice(yedf_qs).format(biz=random.choice(biz_types))
    add(q, yedf_answer)

shif_gen_answer = ("**SHIF (Social Health Insurance Fund)** contributions are charged at **2.75% of gross income**, "
                    "with no upper cap. SHIF replaced NHIF from October 2024, and unlike NSSF, it's not split into "
                    "employer-matched tiers -- it's an employee-side deduction that you as the employer withhold and "
                    "remit. Confirm the exact current employer/employee split and remittance process directly with "
                    "the **SHA (Social Health Authority)** or your payroll provider, since implementation details can "
                    "be updated.")
shif_gen_qs = [
    "What are my SHIF obligations as an employer running {biz}?",
    "Do I need to register {biz} for SHIF, and how does it work?",
    "What is the truth about how SHIF contributions are actually structured?",
]
for _ in range(5):
    q = random.choice(shif_gen_qs).format(biz=random.choice(biz_types))
    add(q, shif_gen_answer)

ahl_gen_answer = ("The **Affordable Housing Levy (AHL)** is 1.5% of gross salary from the employee, matched by 1.5% "
                   "from the employer -- 3% total per employee, per month, with **no minimum income threshold**, so "
                   "it applies even to low-wage staff. Remittance is due by the 9th working day after month-end via "
                   "KRA iTax; late remittance carries a 3% per month penalty on the unpaid amount.")
ahl_gen_qs = [
    "Does the Housing Levy apply to my {biz} even with just 1-2 low-wage employees?",
    "What are my obligations under the Affordable Housing Levy as a small employer?",
]
for _ in range(5):
    q = random.choice(ahl_gen_qs).format(biz=random.choice(biz_types))
    add(q, ahl_gen_answer)

yearend_answer = ("Your deadlines shift to follow your own financial year-end rather than calendar-year dates. "
                   "Corporation tax returns are due within **six months after your financial year-end**. Instalment "
                   "tax payments are due on the 20th day of the 4th, 6th, 9th, and 12th months of *your* financial "
                   "year, not fixed calendar months. Changing your financial year-end requires KRA's approval.")
yearend_qs = [
    "My {biz}'s financial year doesn't run January to December. How does that affect my tax deadlines?",
    "How do instalment tax payment dates work if my company's year-end isn't 31 December?",
]
for _ in range(5):
    q = random.choice(yearend_qs).format(biz=random.choice(biz_types))
    add(q, yearend_answer)

add("I have never filed a tax return for my business. What should I do?",
    "File as soon as possible rather than waiting -- the longer unfiled returns sit, the more penalties and interest "
    "can accumulate. Log into iTax, check exactly which obligations are outstanding, and file each missing return, "
    "including nil returns for periods with no income. If you're unsure how far back you need to go or face a large "
    "penalty, it's worth consulting a tax advisor or visiting a KRA office to discuss your specific situation, since "
    "penalty waivers or payment plans may be available depending on your case.")

add("KRA sent me a message about my account. I don't understand what it means. What should I do?",
    "Don't ignore it -- log into your iTax account directly (rather than clicking any link in the message, to avoid "
    "phishing) and check your obligations, filing status, and any notices under your profile. Common reasons include "
    "an unfiled return, an outstanding balance, or a request to update your details. If the message itself is unclear, "
    "you can contact the KRA Call Centre directly to ask what it specifically relates to, rather than guessing.")

add("A customer owes me money and refuses to pay. What can I do?",
    "Start with a clear, written **demand letter** stating the amount owed, the reason, and a deadline to pay -- this "
    "creates a paper trail and often resolves things without further action. Keep any evidence of the debt (invoices, "
    "delivery notes, WhatsApp messages agreeing to the amount). If they still don't pay, you can pursue the matter "
    "through the **Small Claims Court**, which is designed to be faster and cheaper than regular civil court for "
    "smaller amounts -- though I'd confirm the current claim-value limit and process with the court directly, since "
    "these details can be updated.")

add("I want to close my business. What do I need to do?",
    "Closing a business properly means more than just stopping operations. You'll generally need to: settle any "
    "outstanding tax obligations and file final returns with KRA, deregister relevant tax obligations (VAT, PAYE, "
    "etc.) on iTax, settle any outstanding NSSF/SHIF/Housing Levy contributions for your employees, notify your "
    "county government to close out your business permit, and if you're a registered company, formally apply to "
    "strike off or dissolve the company with the Registrar of Companies. Keep your records for the standard retention "
    "period afterward, since you may still be asked to account for past periods.")

print(f"Generated {len(examples)} more examples in this batch")

with open("generated_qualitative_batch3.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_qualitative_batch3.jsonl")
