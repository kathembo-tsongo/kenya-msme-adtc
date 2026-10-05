"""Conversation-memory test (stage 2): does the app use what the operator told it? (core repo: kenya-msme-adtc)

Run from the kenya-msme-adtc folder:  python3 context_test.py [--db rafiki_pack_new.db]
Simulates whole conversations the way the app's Responder does (same rules as memory_patch.py -- keep in sync):
remembers business type / place; a message that only gives context re-answers the previous topic; otherwise the
message is routed normally with the previous topic as context (stage 1 follow-ups).
"""
import argparse
import re
import sqlite3

import query_pack as qp
from operator_test import detect_lang, field

PLACES = set(("nairobi mombasa kisumu nakuru eldoret thika kitale malindi naivasha nanyuki ruiru kitengela kwale "
              "kilifi lamu garissa wajir mandera marsabit isiolo meru embu kitui machakos makueni nyandarua nyeri "
              "kirinyaga muranga kiambu turkana samburu nandi baringo laikipia narok kajiado kericho bomet kakamega "
              "vihiga bungoma busia siaya migori kisii nyamira").split())
FOOD = ("food mango fruit vegetable chakula matunda mboga maembe embe restaurant hotel cafe bakery juice milk meat "
        "fish samaki nyama maziwa hoteli mkahawa mikate").split()
BUSINESS_RES = [re.compile(p) for p in (
    r"\bmy business is (?:for |in |about |selling |a |an )*([a-z' ]{3,40})",
    r"\bi (?:sell|deal in|trade in|run|own) (?:a |an )?([a-z' ]{3,40})",
    r"\bbiashara yangu ni (?:ya |la )?([a-z' ]{3,40})",
    r"\b(?:nauza|ninauza|tunauza) ([a-z' ]{3,40})",
    r"\bninafanya biashara ya ([a-z' ]{3,40})")]
QUESTION_START = re.compile(r"^(how|what|where|when|which|who|why|can|could|should|do|does|is|are|will|"
                            r"je|nawezaje|ninawezaje|vipi|gani|nini|lini|wapi|kwa nini)\b")

# (conversation, what the LAST message should get)
CASES = [
    (["is it a must to register for my business before I start operating?", "my business is for mangos"],
     "CONTEXT:start_business+food"),
    (["how do I start a small business here in kenya", "nauza maembe"], "CONTEXT:start_business+food"),
    (["do I need a permit for my shop", "niko Nakuru"], "CONTEXT:license"),
    (["hello", "I sell clothes"], "ACK"),
    (["I sell mangoes in Nakuru, do I need a permit?"], "ROUTE:license"),
    (["what is the VAT rate", "what if I pay late?"], "ROUTE:vat_penalty"),
    (["I run a salon", "how can I get more customers?"], "MODEL-WITH-CONTEXT"),
]


class Session:
    def __init__(self, db):
        self.db, self.business, self.place, self.prev_topic, self.prev_query = db, "", "", None, None

    def learn(self, q):
        l, learnt = q.lower(), False
        for rx in BUSINESS_RES:
            m = rx.search(l)
            if not m:
                continue
            b = re.split(r"\s+(?:in|at|from|kwa|huko|na|and)\s+", m.group(1))[0].strip()
            b = " ".join(b.split()[:4])
            if len(b) >= 3:
                self.business, learnt = b, True
            break
        for w in qp.words(l):
            if w in PLACES:
                self.place, learnt = w.capitalize(), True
                break
        return learnt

    @staticmethod
    def context_only(q):
        l = q.lower().strip()
        return not l.endswith("?") and not QUESTION_START.search(l) and len(qp.words(l)) <= 10

    def ask(self, q):
        if self.learn(q) and self.context_only(q):
            if self.prev_topic:
                food = "+food" if any(f in self.business for f in FOOD) else ""
                return f"CONTEXT:{self.prev_topic}{food}"
            return "ACK"
        r = qp.route(self.db, q, detect_lang(q), prev_topic=self.prev_topic, prev_query=self.prev_query)
        kind, topic = str(field(r, "kind")), str(field(r, "topic", "suggest"))
        if topic:
            self.prev_topic = topic
        self.prev_query = q
        if kind in ("ADVISORY", "DIGEST") or kind.startswith("FACTUAL STRONG"):
            return "MODEL-WITH-CONTEXT" if (self.business or self.place) else f"MODEL:{kind}"
        return f"ROUTE:{topic or kind}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="rafiki_pack_new.db")
    args = ap.parse_args()
    db = sqlite3.connect(args.db)
    ok = 0
    for i, (turns, expect) in enumerate(CASES, 1):
        s = Session(db)
        got = [s.ask(t) for t in turns][-1]
        hit = got == expect
        ok += hit
        mem = " · ".join(x for x in (s.business, s.place) if x) or "-"
        print(f"{i} {'OK  ' if hit else 'MISS'} got {got:<30} expect {expect:<30} memory: {mem:<22} | {' -> '.join(turns)}")
    print(f"\n{ok}/{len(CASES)} conversations used the context as expected.")


if __name__ == "__main__":
    main()
