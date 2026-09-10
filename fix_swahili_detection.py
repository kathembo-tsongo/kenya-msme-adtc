"""Fix critical false-positive bug in is_swahili(): naive substring matching
caused 'Kenya' (contains 'ya') and similar English words to be misdetected
as Swahili on nearly every query. Switch to word-boundary regex matching
and drop the shortest, most collision-prone words."""
import re

with open("rag_server.py", "r", encoding="utf-8") as f:
    content = f.read()

old_func = '''def is_swahili(text: str) -> bool:
    """Heuristic Swahili detection based on common Swahili word presence."""
    text_lower = text.lower()
    common_swahili_words = [
        "ninahitaji", "kuhusu", "biashara", "nini", "vipi", "wapi", "gani",
        "kwa", "na", "ya", "wa", "je", "ninataka", "naomba", "nusu",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
    ]
    return any(w in text_lower for w in common_swahili_words)'''

new_func = '''def is_swahili(text: str) -> bool:
    """Heuristic Swahili detection based on common Swahili word presence.

    Uses word-boundary matching, not substring matching -- a naive substring
    check previously misfired on English text containing 'Kenya' (which
    contains the substring 'ya'), among other false positives from short
    words like 'na'/'wa'/'kwa'. Short, collision-prone words are dropped
    entirely; the remainder require whole-word matches only."""
    text_lower = text.lower()
    common_swahili_words = [
        "ninahitaji", "kuhusu", "biashara", "nini", "vipi", "wapi", "gani",
        "je", "ninataka", "naomba",
        "kodi", "usajili", "mfanyakazi", "mshahara", "kampuni", "sheria",
    ]
    return any(
        re.search(r"\\b" + re.escape(w) + r"\\b", text_lower)
        for w in common_swahili_words
    )'''

if old_func not in content:
    print("ERROR: could not find the is_swahili function. No changes made.")
    print("Paste the output of: sed -n '/^def is_swahili/,/^def /p' rag_server.py")
else:
    content = content.replace(old_func, new_func)
    with open("rag_server.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: is_swahili() fixed to use word-boundary matching.")

import ast
try:
    ast.parse(open("rag_server.py", encoding="utf-8").read())
    print("SYNTAX CHECK: PASSED")
except SyntaxError as e:
    print(f"SYNTAX CHECK: FAILED -- {e}")
