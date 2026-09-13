with open("README.md", "r", encoding="utf-8") as f:
    content = f.read()

changes = []

old_sources = "Knowledge base built from 313 verified Kenyan regulatory, tax, and policy source documents"
new_sources = "Knowledge base built from 323 verified Kenyan regulatory, tax, and policy source documents"
if old_sources in content:
    content = content.replace(old_sources, new_sources, 1)
    changes.append("Fixed document count typo (313 -> 323)")
else:
    print("WARNING: could not find the '313' sources line to fix.")

old_limitations = '''## Known limitations

The fine-tuned model's standalone factual accuracy (no RAG) is uneven -- strongest on frequently-repeated training topics, weaker elsewhere. A system-prompt fact digest corrects several verified high-risk figures (NSSF rate, annual leave entitlement, company registration capital requirements, YEDF details). The RAG layer substantially improves reliability by grounding answers in actual source documents, and includes scope-boundary handling to avoid answering questions outside Kenya/MSME topics with unfounded confidence.'''

new_limitations = '''## Known limitations

The fine-tuned model's standalone factual accuracy (no RAG) is uneven -- strongest on frequently-repeated training topics, weaker elsewhere, and this holds regardless of decoding temperature (tested at both 0.6 and 0.3 with comparable fabrication rates). A verified-answer digest in `rag_server.py` bypasses generation entirely for 17 hand-checked, high-risk topics (NSSF rate and late-payment penalty, PAYE bands/deadline/penalty, SHIF rate, VAT threshold, Turnover Tax, Affordable Housing Levy, Minimum Wage, YEDF, business registration, KRA PIN, and others), each available in both English and Kiswahili. The RAG layer substantially improves reliability elsewhere by grounding answers in actual source documents, and includes scope-boundary handling to avoid answering questions outside Kenya/MSME topics with unfounded confidence.

Note: this digest-override layer protects the chat/qualitative evaluation path only. The raw model's automated multiple-choice/log-likelihood scoring loads the `.gguf` directly and never renders a chat template, so it reflects the base model's own fine-tuned weights independent of this mitigation -- see REPORT.md ("Two distinct accuracy-evaluation paths") for the full explanation.'''

if old_limitations in content:
    content = content.replace(old_limitations, new_limitations, 1)
    changes.append("Updated Known limitations section (17 bilingual topics, two-path explanation)")
else:
    print("WARNING: could not find the Known limitations section to update.")

old_run = '''Then open webui/index.html directly in a browser.

## Testing the raw model standalone (no RAG)'''

new_run = '''Then open webui/index.html directly in a browser.

**Before benchmarking:** disable CPU turbo boost first. We found turbo boost
causes a sharp power/heat spike during sustained inference on thin-chassis
hardware, driving peak temperature to 96-100C (triggering the thermal
penalty) with no measurable throughput benefit. Disabling it drops peak
temperature to ~59C with no measurable cost (see REPORT.md, "Thermal --
root cause found and fixed", for full measurements):

    echo 1 | sudo tee /sys/devices/system/cpu/intel_pstate/no_turbo

`start.sh` checks this automatically and prints a warning if it's off.

## Testing the raw model standalone (no RAG)'''

if old_run in content:
    content = content.replace(old_run, new_run, 1)
    changes.append("Added turbo-boost benchmarking note")
else:
    print("WARNING: could not find the Run the stack section anchor.")

with open("README.md", "w", encoding="utf-8") as f:
    f.write(content)

print("\n".join(changes) if changes else "No changes applied -- check warnings above.")
print(f"\nNew file length: {len(content.splitlines())} lines")
