with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

new_section = """

## Final Pre-Submission Testing Pass

A final round of live testing against the deployed web UI -- rather than
curl scripts alone -- surfaced two more issues worth documenting
honestly, plus a genuine crash bug.

### Context-window overflow (a recurring crash class, not a new one)

Two casual, uncovered questions ("How can I start a business of a salon
in Muranga", "I run a small tailoring shop with 2 employees...")
triggered `request exceeds the available context size (4096 tokens)`
errors from llama-server, surfacing as a generic failure message in the
UI. This is the same class of bug found and fixed at Gate 1 (originally
2048 -> 4096 tokens) -- it recurred because the Post-Gate-1 accuracy and
Kiswahili passes above substantially grew the system-prompt content
injected into every non-canned query, eventually exceeding even the
increased limit. Fixed by increasing the context window to 8192 tokens
in `start.sh`. This has no effect on the official Efficiency Score,
which is measured via an independent `llama-bench` invocation that does
not read this setting.

Fixing the crash surfaced the underlying generative content directly,
which included two real fabrications worth noting as evidence of the
raw-model fabrication risk already discussed above: a specific but false
minimum-capital figure (contradicting our own verified fact that no such
minimum exists), and a business-insurance question that was incorrectly
directed to KRA (the tax authority) rather than IRA (the actual
insurance regulator).

### Two more topics added, and one more routing bug fixed

- **`business_insurance`** (new, EN+SW): verified via web search --
  IRA as the correct regulator, WIBA and motor third-party liability as
  the compulsory categories, with common optional cover explained.
- **`maternity_paternity_leave`** (new, EN+SW): a maternity-leave
  question was being intercepted by the generic `leave` topic's
  overly-broad "leave entitlement" keyword, returning the wrong (annual
  leave) answer. Verified via web search (Employment Act Section 29: 90
  days maternity, 14 days paternity, both fully paid) and added as a
  dedicated topic, narrowing `leave`'s keywords to stop the
  over-matching.

### Final state

**38 canned topics**, all with complete, verified English and Kiswahili
content and correct keyword routing, confirmed via direct testing in
the deployed web UI as the final verification step before submission.
"""

content = content + new_section

with open("REPORT.md", "w", encoding="utf-8") as f:
    f.write(content)

print(f"Appended final testing section. New total length: {len(content)} chars")
