with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

anchor = "We report this second example's residual imprecision rather than omitting it: fine-tuning measurably shifted outputs toward domain-specific knowledge, but did not eliminate cross-topic confusion between related tax categories on its own -- which is precisely the gap our verified-answer layer is designed to close."

new_content = anchor + """

*Prompt (Kiswahili): "Kiwango cha VAT ni kiasi gani nchini Kenya?"*
- **Base model:** produces incoherent, repetitive text with no real content -- "Tafadhali na tafadhali... Taabulaji na tafadhali" (nonsense phrases, "Taabulaji" is not a real Kiswahili word) -- and never states an actual VAT rate.
- **Fine-tuned model:** "Nchi VAT ni 16% p.a." -- correctly states the actual VAT rate (16%), though the phrasing is not fully fluent Kiswahili.

**Honest disclosure on Kiswahili and fine-tuning.** Our training dataset (3,308 examples) and RAG corpus (323 documents) are both English-only -- within our project timeline, we were not able to source sufficient genuine Kiswahili-language regulatory material to include in either. The improvement visible above is best understood as a correct *fact* ("VAT = 16%") learned from English training data surfacing even when prompted in Kiswahili, not evidence that fine-tuning taught the model Kiswahili fluency or Kiswahili-specific domain knowledge -- it did not.

This is why our actual Kiswahili reliability comes from a different mechanism entirely: 38 hand-verified, natively-written Kiswahili canned answers (see Kiswahili Quality Pass, below), which bypass generation completely and return instantly. For any question outside that verified set, the live system still has to fall back on generation -- which takes longer and can produce hallucinated or incoherent Kiswahili text, as documented in our own live testing throughout this submission. We consider expanding genuine Kiswahili-language training data and RAG source material a priority for continued work on this project beyond this submission."""

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added revised, honest Kiswahili before/after example + disclosure")
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")
