with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old = '''def get_canned_topic(query: str):
    """Return the topic key if the query matches a hard-verified topic with
    a canned answer, else None. Bypasses LLM generation entirely for these
    topics to guarantee zero fabrication."""
    query_lower = query.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return topic
    return None'''

new = '''def get_canned_topic(query: str):
    """Return the topic key if the query matches a hard-verified topic with
    a canned answer, else None. Bypasses LLM generation entirely for these
    topics to guarantee zero fabrication.

    Checks exact substrings first, then falls back to a space-normalized
    comparison (spaces stripped from both query and keyword) to tolerate
    common spacing variants -- e.g. someone typing "ku sajili" instead of
    "kusajili" for a Kiswahili compound verb form."""
    query_lower = query.lower()
    query_nospace = query_lower.replace(" ", "")
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            return topic
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw.replace(" ", "") in query_nospace for kw in keywords):
            return topic
    return None'''

count = content.count(old)
print(f"Anchor occurrences found: {count}")
if count == 1:
    content = content.replace(old, new, 1)
    print("Added space-normalized fallback matching")
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
else:
    print(f"ERROR: anchor found {count} times, expected 1 -- no changes made")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
