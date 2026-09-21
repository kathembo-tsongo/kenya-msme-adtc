# Before/after outputs for the test prompts

Each prompt was run once at temperature 0 (context 2048, max 500 tokens) through llama-server with no retrieval, verified answers or system prompt. BASE = unmodified Qwen2.5-1.5B-Instruct Q4_K_M (sha256 6a1a2eb6d15622bf...). SUBMITTED = the submitted GGUF (sha256 e88ec13968800a5e...). The two servers ran at the same time.

## Current test prompts in metadata.json (run September 21, 2026)

### Prompt: How many days of annual leave is an employee entitled to in Kenya?

#### BASE (unmodified Qwen2.5-1.5B-Instruct, Q4_K_M)

In Kenya, the standard annual leave entitlement for employees is 20 days. This is a common practice across many countries, including Kenya, where employees are entitled to a minimum of 20 days of paid annual leave per year. However, it's important to note that this can vary depending on the specific company's policies and the country's labor laws.

#### SUBMITTED (fine-tuned + digest)

An employee in Kenya is entitled to a minimum of **21 working days** of annual leave per year, with no lower limit set by law. This applies regardless of the employee's length of service or salary level. The exact calculation method and any additional entitlements (such as public holidays) are determined under employment regulations rather than fixed statutory rules.

### Prompt: What is the turnover tax rate for small businesses in Kenya?

#### BASE (unmodified Qwen2.5-1.5B-Instruct, Q4_K_M)

As an AI developed by Alibaba Cloud, I don't have real-time data or specific information about the current tax rates for small businesses in Kenya. The tax rates can vary depending on the country, region, and specific circumstances. It's best to check the latest tax regulations from the relevant government or tax authority in Kenya for accurate and up-to-date information.

#### SUBMITTED (fine-tuned + digest)

The **Turnover Tax (TOT)** is charged at **1.5% of gross sales** with no expense deductions allowed under any circumstances. This applies to all income earned through a business operation, not just profits after expenses.

For example, if your annual turnover is KES 2 million, the TOT liability would be approximately KES 30,000 (1.5% of KES 2,000,000).

This is a separate tax from income tax or PAYE -- it's applied directly to gross sales without any expense deductions allowed by law.

If you're unsure about your exact turnover figure for the year, confirm with **KRA** what your annual taxable sales are.

## Earlier prompt pair (NSSF and VAT, run September 21, 2026, same setup)

### Prompt: What are the NSSF contribution rates for an employee earning KSh 30,000 per month?

#### BASE

The National Social Security Fund (NSSF) contribution rates vary depending on the country and the specific type of contribution. In Kenya, for an employee earning KSh 30,000 per month, the contribution rates for the National Social Security Fund (NSSF) are as follows:

1. **Basic Contribution Rate**: This is the rate that the employer and employee contribute to the NSSF. For an employee earning KSh 30,000 per month, the basic contribution rate is typically around 10% of the employee's salary.

2. **Contributory Pension Rate**: This is the rate that the employee contributes to the NSSF. For an employee earning KSh 30,000 per month, the contributory pension rate is also typically around 10% of the employee's salary.

3. **Contributory Provident Fund Rate**: This is the rate that the employee contributes to the NSSF. For an employee earning KSh 30,000 per month, the contributory provident fund rate is also typically around 10% of the employee's salary.

It's important to note that these rates can vary based on the specific rules and regulations of the NSSF in Kenya. For the most accurate and up-to-date information, it's best to consult the official NSSF website or contact their customer service directly.

#### SUBMITTED

For a monthly salary of **KES 30,000**, the NSSF deduction is:

- Employee side: 6% of gross pay = **KES 1,800.0** (matched by employer at 6%, so total **KES 3,420.0**)
- Employer side: 6% of gross pay = **KES 1,800.0**

Combined, the NSSF contribution for this employee is **KES 3,420.0 monthly**, with each side split evenly between employer and employee -- no separate Tier I or Tier II contributions apply at KES 30,000/month.

### Prompt: What is the VAT rate?

#### BASE

The VAT rate is a tax rate used in the value-added tax system. It is the percentage of the value of goods or services that is taxed. The VAT rate varies depending on the country or region. In the United States, the VAT rate is 0%. In the European Union, the VAT rate is 21%. In China, the VAT rate is 13%.

#### SUBMITTED

VAT in Kenya is charged at **16%** on all supplies and services. This is a separate obligation from NSSF contributions or PAYE deductions -- it's applied to top-up an existing KRA PIN account, not added as part of registration or tax calculation. The 16% VAT rate applies across the board for both resident and non-resident businesses operating in Kenya.
