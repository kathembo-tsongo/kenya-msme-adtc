with open("REPORT.md", "r", encoding="utf-8") as f:
    content = f.read()

anchor = """**38 canned topics**, all with complete, verified English and Kiswahili
content and correct keyword routing, confirmed via direct testing in
the deployed web UI as the final verification step before submission."""

new_content = anchor + """

## A Further Limitation: Retrieval Succeeding Does Not Guarantee a Correct Answer

Live testing surfaced a distinct failure mode worth documenting separately from the retrieval-quality and Kiswahili limitations already discussed: even when RAG retrieval fetches genuinely relevant source material, the model can still conflate or misapply facts while composing its answer -- a generation-level error, not a retrieval-level one.

**Example**: asked "What is the penalty for late payment of PAYE in Kenya?", the system answered with the late *filing* penalty figure (25% or KES 10,000, whichever is higher) rather than the late *payment* penalty (5% plus 1% monthly interest on the unpaid amount) -- two related but distinct categories under the same tax obligation. We did not verify whether the retrieved chunk(s) for this query actually contained the correct payment-specific figure that the model then failed to use, or whether retrieval itself surfaced the wrong section; either way, the output was wrong.

This matters because it means better retrieval alone -- e.g. semantic embeddings instead of TF-IDF, which we considered but have not implemented, given the added memory/compute cost on constrained hardware and the genuine risk of degrading exact-term matching that already works well for precise legal/tax terminology -- would not necessarily fix this class of error on its own. The model's own tendency to conflate closely related facts during generation is a separate risk that grounding mitigates but does not eliminate, distinct from what our digest-override and canned-answer layers close by removing generation from the loop entirely for our 38 highest-stakes topics."""

count = content.count(anchor)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(anchor, new_content, 1)
    print("Added generation-vs-retrieval limitation section")
    with open("REPORT.md", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")
