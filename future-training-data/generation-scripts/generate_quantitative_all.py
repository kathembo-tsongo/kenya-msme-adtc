import json
import random

random.seed(42)
SYS = "You are a helpful assistant advising Kenyan MSME operators on tax, registration, financing, and regulatory compliance."
examples = []

def nssf_calc(salary):
    tier1 = min(salary, 9000) * 0.06
    tier2 = max(0, min(salary, 108000) - 9000) * 0.06
    return round(tier1 + tier2, 2)

nssf_salaries = [8000, 9000, 12000, 15000, 18000, 20000, 22000, 25000, 28000, 32000,
                 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000, 80000,
                 85000, 90000, 95000, 100000, 108000, 120000, 150000, 200000]
nssf_phrasings = [
    "What are the NSSF contribution rates for an employee earning KSh {s} per month?",
    "How much NSSF do I deduct from an employee's salary of KES {s}?",
    "I pay one of my staff KSh {s} a month. What's my NSSF obligation, employer and employee side?",
    "NSSF ya mfanyakazi anayelipwa KSh {s} kwa mwezi ni how much?",
    "Can you break down NSSF contributions for a KES {s} monthly salary?",
]
for salary in nssf_salaries:
    amt = nssf_calc(salary)
    phr = random.choice(nssf_phrasings).format(s=f"{salary:,}")
    if salary <= 9000:
        breakdown = f"Since KSh {salary:,} falls entirely within Tier I (pensionable pay up to KES 9,000), the contribution is 6% of the full salary."
    elif salary < 108000:
        breakdown = f"This splits across both tiers: Tier I is 6% of the first KES 9,000 (KES 540), and Tier II is 6% of the remaining KES {salary-9000:,} (KES {round((salary-9000)*0.06,2):,})."
    else:
        breakdown = f"Since KSh {salary:,} exceeds the KES 108,000 pensionable pay ceiling, Tier II is capped: Tier I is 6% of KES 9,000 (KES 540), and Tier II is capped at 6% of KES 99,000 (KES 5,940), for a maximum of KES 6,480 per side."
    content = (f"**NSSF contributions** are split evenly, each side paying **6% of pensionable pay** across Tier I "
               f"(first KES 9,000) and Tier II (up to KES 108,000).\n\n{breakdown}\n\nFor a monthly salary of KES {salary:,}, "
               f"each side contributes **KES {amt:,}**, combined total **KES {round(amt*2,2):,}**, remitted by the 9th of the following month.")
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": phr}, {"role": "assistant", "content": content}]})

def paye_calc(salary):
    bands = [(24000, 0.10), (8333, 0.25), (467667, 0.30), (300000, 0.325), (float('inf'), 0.35)]
    remaining = salary
    tax = 0
    breakdown = []
    for width, rate in bands:
        if remaining <= 0:
            break
        taxed = min(remaining, width)
        band_tax = taxed * rate
        tax += band_tax
        if taxed > 0:
            breakdown.append((taxed, rate, band_tax))
        remaining -= taxed
    tax_after_relief = max(0, tax - 2400)
    return round(tax, 2), round(tax_after_relief, 2), breakdown

paye_salaries = [20000, 24000, 28000, 32333, 38000, 45000, 55000, 65000, 80000, 95000,
                 110000, 130000, 150000, 180000, 220000, 260000, 310000, 380000, 450000,
                 520000, 600000, 700000, 800000, 900000, 1000000]
paye_phrasings = [
    "How much PAYE should I deduct from an employee earning KSh {s} per month?",
    "What is the PAYE for a monthly salary of KES {s}?",
    "I just hired someone at KSh {s} a month. What PAYE do I remit to KRA?",
    "PAYE ya mshahara wa KES {s} kwa mwezi ni ngapi?",
]
for salary in paye_salaries:
    gross_tax, net_tax, breakdown = paye_calc(salary)
    phr = random.choice(paye_phrasings).format(s=f"{salary:,}")
    band_lines = "; ".join([f"KES {round(t,0):,.0f} at {int(r*100)}%" for t, r, _ in breakdown])
    content = (f"For a monthly salary of **KES {salary:,}**, PAYE is calculated across the progressive bands: {band_lines}, "
               f"giving a gross tax of **KES {gross_tax:,}**.\n\nSubtracting the standard **personal relief of KES 2,400/month** "
               f"(for a resident employee), the final PAYE payable is **KES {net_tax:,}**.\n\nThis must be remitted to KRA by the "
               f"**9th of the following month** via the iTax P10 return; late remittance carries a 25% penalty plus 2% monthly interest.")
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": phr}, {"role": "assistant", "content": content}]})

def ahl_calc(salary):
    each = round(salary * 0.015, 2)
    return each, round(each * 2, 2)

ahl_salaries = [10000, 15000, 18047, 22000, 28000, 35000, 42000, 50000, 60000, 75000,
                90000, 110000, 135000, 160000, 200000, 250000, 300000]
ahl_phrasings = [
    "How much Housing Levy applies to a salary of KES {s} per month?",
    "What is the Affordable Housing Levy for an employee earning KSh {s}?",
    "Housing levy ya mshahara wa KES {s} ni how much kwa kila upande?",
    "Calculate the Housing Levy deduction for a KSh {s} monthly salary, both employer and employee share.",
]
for salary in ahl_salaries:
    each, total = ahl_calc(salary)
    phr = random.choice(ahl_phrasings).format(s=f"{salary:,}")
    content = (f"The **Affordable Housing Levy (AHL)** is 1.5% of gross salary from the employee, matched by 1.5% from the "
               f"employer -- 3% total, with **no minimum income threshold**.\n\nFor a monthly salary of KES {salary:,}: "
               f"employee pays **KES {each:,}** (1.5%), employer matches **KES {each:,}** (1.5%), for a combined total of "
               f"**KES {total:,}** remitted by the 9th working day after month-end via KRA iTax.")
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": phr}, {"role": "assistant", "content": content}]})

def shif_calc(salary):
    return round(salary * 0.0275, 2)

shif_salaries = [12000, 18000, 24000, 30000, 38000, 45000, 55000, 65000, 80000, 95000,
                 115000, 140000, 170000, 210000, 260000]
shif_phrasings = [
    "How much SHIF is deducted from a salary of KES {s}?",
    "What is the SHIF contribution for an employee earning KSh {s} monthly?",
    "SHIF ya mshahara wa KES {s} ni how much?",
]
for salary in shif_salaries:
    amt = shif_calc(salary)
    phr = random.choice(shif_phrasings).format(s=f"{salary:,}")
    content = (f"**SHIF (Social Health Insurance Fund)** is charged at **2.75% of gross income**, with no upper cap.\n\n"
               f"For a monthly salary of KES {salary:,}, the SHIF deduction is **KES {amt:,}**. This is an employee-side "
               f"deduction (unlike NSSF, the employer does not match it), withheld by the employer and remitted to the "
               f"SHA (Social Health Authority) by the 9th of the following month.")
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": phr}, {"role": "assistant", "content": content}]})

def tot_calc(turnover):
    return round(turnover * 0.015, 2)

tot_turnovers = [1200000, 1800000, 2500000, 3000000, 4000000, 5500000, 7000000, 9000000,
                 11000000, 13500000, 16000000, 19000000, 22000000, 24500000]
tot_phrasings = [
    "My shop's annual turnover is about KES {s}. How much Turnover Tax do I owe?",
    "What Turnover Tax applies to a business with KSh {s} in annual sales?",
    "Turnover tax ya biashara yenye mauzo ya KES {s} kwa mwaka ni how much?",
]
for turnover in tot_turnovers:
    amt = tot_calc(turnover)
    phr = random.choice(tot_phrasings).format(s=f"{turnover:,}")
    content = (f"With an annual turnover of KES {turnover:,}, you fall within the **Turnover Tax (TOT)** bracket "
               f"(KES 1,000,000 to KES 25,000,000 for resident businesses).\n\nTOT is a flat **1.5% of gross sales**, "
               f"so your annual liability would be approximately **KES {amt:,}**. This is a final tax -- no expense "
               f"deductions apply, and you don't file a separate income tax return for this turnover. Note: if your "
               f"turnover later exceeds KES 5,000,000, you'll also need to register for VAT separately.")
    examples.append({"messages": [{"role": "system", "content": SYS}, {"role": "user", "content": phr}, {"role": "assistant", "content": content}]})

print(f"NSSF: {len(nssf_salaries)}, PAYE: {len(paye_salaries)}, AHL: {len(ahl_salaries)}, SHIF: {len(shif_salaries)}, TOT: {len(tot_turnovers)}")
print(f"Total generated: {len(examples)}")

with open("generated_quantitative_all.jsonl", "w", encoding="utf-8") as f:
    for ex in examples:
        f.write(json.dumps(ex, ensure_ascii=False) + "\n")

print(f"Wrote {len(examples)} examples to generated_quantitative_all.jsonl")
