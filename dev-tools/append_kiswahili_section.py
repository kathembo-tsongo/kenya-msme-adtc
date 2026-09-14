with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

new_section = """

## Kiswahili Quality Pass (Post-Gate-1)

While testing the system interactively in the web UI, a casual Kiswahili
query ("naweza kusajili biashara yangu?" -- "can I register my
business?") returned incoherent, non-grammatical text despite the
underlying topic already having a correct, hand-verified Kiswahili
canned answer. Investigating this surfaced a systemic issue affecting
Kiswahili users broadly, not an isolated bug.

### Root cause: two independent, disconnected mechanisms

The system has two separate layers that both need to recognize a query
as Kiswahili-relevant: `TOPIC_KEYWORDS` (routes a query to the correct
canned topic) and `is_swahili()` (decides whether to return the English
or Kiswahili version of that topic's canned answer, and whether to
route generative fallback through translation). These operated
independently -- `TOPIC_KEYWORDS` could correctly match a Kiswahili
phrase to its topic, while `is_swahili()` failed to recognize the same
text as Kiswahili at all, causing the system to silently fall back to
English (safe but incomplete) or, worse, to the generative-then-
translate path, which relies on the same small 1.5B model performing
free-form translation -- a task it does not do reliably, and which
produced the incoherent output observed.

`is_swahili()`'s word list was narrow (16 words) and missing several
extremely common, domain-relevant terms -- most notably **"ngapi"**
("how much/how many"), the single most natural way to ask about a rate
in Kiswahili, alongside "ushuru" (tax/levy), "mwezi" (month), and
others directly relevant to a tax/finance advisor. Expanded the list to
30 terms; confirmed the original false-positive fix (English text
containing "Kenya," which contains the substring "ya") remains intact.

### Full bilingual coverage achieved

Beyond the detection fix, we systematically audited and expanded
Kiswahili keyword routing across the original 17 Gate 1 topics, and
wrote full Kiswahili canned-answer content (not previously present) for
all 20 topics added during the accuracy pass above. **All 37 canned
topics now have complete English and Kiswahili content with correct
keyword routing in both languages**, each verified via live queries
against the running system.

This pass also surfaced and fixed two smaller, pre-existing issues
found along the way: a duplicated `probation_period` entry in the
Kiswahili answer dictionary (dead code from an earlier session; Python
silently used the later definition, so it never produced incorrect
answers, but was genuinely duplicated content), and a keyword-shadowing
case where the specific `food_business_license` topic was being
intercepted by the generic `license` topic's overly broad Kiswahili
keyword, fixed by reordering keyword-dictionary precedence.
"""

content = content + new_section

with open("REPORT.md", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Appended Kiswahili quality pass section. New total length: {len(content)} chars")
