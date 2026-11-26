#!/usr/bin/env python3
"""
run_laptop_eval.py -- run the test set through the phone app's answering path on the LAPTOP, so
accuracy, routing, parity and consistency can be measured before the phone run.

It mirrors Responder.kt for a fresh, single-question conversation:
  router (query_pack.route, the same code the phone ports) -> verified answer / suggestion /
  passages / "no verified information" -> or a model prompt built exactly as on the phone ->
  llama-server -> figure check -> footer.
The model is called through llama-server's raw /completion endpoint with ChatML and the phone's
system prompt (read from Rafiki.kt), NOT /v1/chat/completions -- that would apply the chat
template baked into the GGUF (the old ADTC digest), which the phone does not use.

Laptop timings are NOT phone timings: report speed, speed drift and memory from the phone run.

Answer language (--answer-lang):
  en        today's phone behaviour: every model answer is written in English, and Kiswahili users get
            the "answers only in English" note in the footer (the baseline).
  operator  the model answers in the operator's language: Kiswahili questions get Kiswahili answers,
            and the English-only note is dropped. This is what Chapter 3 promises; the phone's
            Responder.kt gets the same change once the base model is chosen.

Prompt format (--template): the phone sends Qwen's ChatML. Gemma models need Gemma's own turn format
(no system role: the system prompt goes at the top of the user turn). "auto" reads the loaded
model's chat template from llama-server's /props and picks chatml or gemma.

Start the model first (same file as the phone, 4 threads, temperature 0.3):
    ./llama.cpp/build/bin/llama-server -m model/msme-qwen2.5-1.5b-Q4_K_M.gguf --port 8090 -c 4096 --threads 4

Then (from kenya-msme-adtc/):
    python3 eval/run_laptop_eval.py --limit 10            # a quick trial
    python3 eval/run_laptop_eval.py --passes 3            # full run (continues if interrupted)
    python3 eval/run_laptop_eval.py --answer-lang operator --model-only   # Kiswahili model comparison
    python3 eval/score_phone_eval.py eval/laptop_runs/rafiki_eval_laptop_<run>.jsonl
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import query_pack as qp  # noqa: E402

RAFIKI_KT = os.path.join(ROOT, "..", "rafiki-wa-biashara-mobile", "llama.cpp", "examples", "llama.android",
                         "app", "src", "main", "java", "com", "example", "llama", "rafiki", "Rafiki.kt")


# ---------------------------------------------------------------- phone constants, read from Rafiki.kt
def read_rafiki(path):
    src = open(path, encoding="utf-8").read()
    system = re.search(r'val SYSTEM_PROMPT = """\s*(.*?)\s*"""\.trimIndent\(\)', src, re.S).group(1).strip()
    block = re.search(r"val FACTS = listOf\((.*?)\n    \)", src, re.S).group(1)
    facts = re.findall(r'"""(.*?)"""', block, re.S)
    return system, facts


# ---------------------------------------------------------------- Responder.kt helpers (ported)
ACRONYMS = set("kra nssf sha vat paye msme msmes sme cbk knbs ifc unctad icta yedf agpo tveta afcfta faq sw pin "
               "brs kebs kephis".split())
SW_MARKERS = set("""na ya kwa ni je gani nini vipi naweza ninahitaji jinsi wapi lini kuna hii hiyo sana mimi yangu
nataka tafadhali habari asante ninawezaje nitasajili kupata kuanza kufungua biashara mkopo leseni kodi nawezaje
ninaweza unaweza tunaweza wateja mteja duka dukani maduka bidhaa faida hasara mauzo zaidi kwangu kwenye au pia sasa
kila bila hadi kama lakini kuhusu nina sina nani namna ndio hapana pesa fedha mtaji soko sokoni kampuni kusajili
kulipa ushuru mshahara wafanyakazi mfanyakazi kibali jina shilingi kiasi ngapi gharama bei chakula kilimo mwaka
mwezi siku wangu yetu yako ili hivyo bado ipo kiwango viwango cha vya ipi nauza ninauza tunauza niko tuko
ninafanya""".split())
EN_MARKERS = set("the is how what do i my for to and can of a in are does should which where when hello hi "
                 "thanks thank".split())
COMPLAINT = re.compile(
    r"why (are|did) you|i did ?n[o']t (ask|say|mean|specify)|not what i (asked|meant)|wrong (answer|topic)|"
    r"(that|this)('s| is) (wrong|not (it|correct|right))|sikuuliza|si hivyo|sio hivyo|jibu si sahihi|umekosea")
BUSINESS_RES = [re.compile(p) for p in (
    r"\bmy business is (?:for |in |about |selling |a |an )*([a-z' ]{3,40})",
    r"\bi (?:sell|deal in|trade in|run|own) (?:a |an )?([a-z' ]{3,40})",
    r"\bbiashara yangu ni (?:ya |la )?([a-z' ]{3,40})",
    r"\b(?:nauza|ninauza|tunauza) ([a-z' ]{3,40})",
    r"\bninafanya biashara ya ([a-z' ]{3,40})")]
PLACES = set("nairobi mombasa kisumu nakuru eldoret thika kitale malindi naivasha nanyuki ruiru kitengela kwale "
             "kilifi lamu garissa wajir mandera marsabit isiolo meru embu kitui machakos makueni nyandarua nyeri "
             "kirinyaga muranga kiambu turkana samburu nandi baringo laikipia narok kajiado kericho bomet kakamega "
             "vihiga bungoma busia siaya migori kisii nyamira".split())
QUESTION_START = re.compile(r"^(how|what|where|when|which|who|why|can|could|should|do|does|is|are|will|"
                            r"je|nawezaje|ninawezaje|vipi|gani|nini|lini|wapi|kwa nini)\b")


def pick(lang, en, sw):
    return sw if lang == "sw" else en


def footer(lang, en, sw):
    return "\n\n---\n" + pick(lang, en, sw)


def model_footer(lang, en, sw, answered_in=None):
    """answered_in = the language the model was told to write in; the English-only note is added only
    when a Kiswahili operator got an English answer."""
    english_note = lang == "sw" and (answered_in or "en") != "sw"
    return footer(lang, en, sw) + ("\n*Kumbuka: majibu yanayoandikwa na modeli kwa sasa yanapatikana kwa "
                                   "Kiingereza pekee.*" if english_note else "")


# How each prompt says which language to write in. The extracts and verified facts stay in English
# (that is what the pack holds), so the Kiswahili instruction says so explicitly.
WRITE_IN = {
    "en": "Answer in English",
    "sw": "Answer in Kiswahili (Swahili), not English, even though the extracts and facts are in English "
          "(keep names of offices, laws and websites as they are)",
}
ONLY_THIS = {
    "en": "Answer only this question, in English.",
    "sw": "Answer only this question, in Kiswahili (Swahili), not English.",
}


def title(source):
    base = os.path.splitext(source.rsplit("/", 1)[-1])[0]
    w = [x.upper() if x.lower() in ACRONYMS else x.lower() for x in re.split(r"[_\- ]", base) if x]
    t = " ".join(w)
    return (t[:1].upper() + t[1:]) if t else source


def excerpt(body, mx=300, focus=""):
    s = re.sub(r"\s+", " ", body).strip()
    if len(s) <= mx:
        return s
    start = 0
    if focus:
        i = s.lower().find(focus.lower())
        if i > mx // 3:
            j = s.rfind(" ", 0, i - mx // 3)
            start = 0 if j < 0 else j + 1
    end = min(start + mx, len(s))
    if end < len(s):
        j = s.rfind(" ", 0, end)
        cut = j if j > start + mx // 2 else end
    else:
        cut = end
    return ("…" if start > 0 else "") + s[start:cut] + ("…" if cut < len(s) else "")


def sw_family(t):
    return len(t) >= 5 and (t.startswith(("nawe", "ninawe", "tunawe", "unawe")) or
                            (t.startswith("ku") and t[-1] in "aeiou") or t.endswith("ni"))


def detect_lang(q):
    w = qp.words(q)
    sw = sum(t in SW_MARKERS or sw_family(t) for t in w)
    en = sum(t in EN_MARKERS for t in w)
    if sw != en:
        return "sw" if sw > en else "en"
    long = [t for t in w if len(t) >= 3 and t.isalpha()]
    if len(long) < 3:
        return "en"
    return "sw" if sum(t[-1] in "aeiou" for t in long) * 10 >= len(long) * 7 else "en"


def lang_mix(q):
    w = qp.words(q)
    sw = sum(t in SW_MARKERS or sw_family(t) for t in w)
    en = sum(t in EN_MARKERS for t in w)
    return "mixed" if sw >= 1 and en >= 1 else detect_lang(q)


def office(q, lang):
    w = set(qp.words(q))

    def any_(*k):
        return any(x in w for x in k)
    if any_("pharmacy", "chemist", "dawa"):
        return pick(lang, "the Pharmacy and Poisons Board", "Pharmacy and Poisons Board (PPB)")
    if any_("nssf"):
        return pick(lang, "your nearest NSSF office", "ofisi ya NSSF iliyo karibu nawe")
    if any_("pochi", "mpesa", "safaricom", "paybill", "till"):
        return pick(lang, "Safaricom (a Safaricom shop or M-PESA agent)", "Safaricom (duka la Safaricom au wakala wa M-PESA)")
    if any_("shif", "sha", "nhif"):
        return pick(lang, "the Social Health Authority (SHA)", "Mamlaka ya Afya ya Jamii (SHA)")
    if any_("trademark", "trademarks", "patent", "patents"):
        return pick(lang, "the Kenya Industrial Property Institute (KIPI)", "Kenya Industrial Property Institute (KIPI)")
    if any_("copyright", "copyrights"):
        return pick(lang, "the Kenya Copyright Board (KECOBO)", "Kenya Copyright Board (KECOBO)")
    if any_("kra", "tax", "taxes", "vat", "paye", "itax", "etims", "pin", "tcc", "turnover", "kodi", "ushuru"):
        return pick(lang, "KRA (a KRA service office, or iTax)", "KRA (ofisi ya huduma ya KRA, au iTax)")
    if any_("permit", "licence", "license", "licenses", "licences", "leseni", "kibali", "county", "kaunti"):
        return pick(lang, "your county government's business licensing office",
                    "ofisi ya leseni za biashara ya serikali ya kaunti yako")
    if any_("register", "registration", "company", "sole", "partnership", "usajili", "sajili", "kusajili"):
        return pick(lang, "the Business Registration Service (via eCitizen or a Huduma Centre)",
                    "Huduma ya Usajili wa Biashara (kupitia eCitizen au Kituo cha Huduma)")
    if any_("export", "exports", "exporting", "import", "imports"):
        return pick(lang, "KEPROBA (Kenya Export Promotion and Branding Agency)", "KEPROBA (Shirika la Kukuza Mauzo ya Nje)")
    if any_("employee", "employees", "employer", "wage", "wages", "salary", "leave", "termination", "mfanyakazi", "wafanyakazi"):
        return pick(lang, "your county labour office", "ofisi ya kazi ya kaunti yako")
    if any_("loan", "loans", "lender", "lenders", "credit", "sacco", "bank", "mkopo", "mikopo"):
        return pick(lang, "your bank or SACCO", "benki yako au SACCO")
    return pick(lang, "a Huduma Centre", "Kituo cha Huduma")


FIGURE = re.compile(r"(?i)(\*\*)?(?:(?:KES|KSh[s]?\.?|Kshs\.?|USD|US\$|\$)\s?\d[\d,]*(?:\.\d+)?"
                    r"(?:\s?(?:million|billion|m|bn)\b)?|\d[\d,]*(?:\.\d+)?\s?(?:%|percent\b|per cent\b)|"
                    r"\d[\d,]*(?:\.\d+)?\s?(?:shillings|bob)\b)(\*\*)?")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")


def figure_check(text, allowed):
    """Port of FigureCheck.kt."""
    if allowed is None:
        return text
    pool = allowed.replace(",", "")
    removed = 0

    def sub(m):
        nonlocal removed
        n = NUMBER.search(m.group(0))
        if not n:
            return m.group(0)
        n = n.group(0).replace(",", "")
        if re.search(r"(?<![\d.])" + re.escape(n) + r"(?!\d)", pool):
            return m.group(0)
        removed += 1
        return "*(amount not in the documents)*"
    out = FIGURE.sub(sub, text)
    if removed == 0:
        return out
    what = ("1 figure that is not in the documents was" if removed == 1
            else f"{removed} figures that are not in the documents were")
    return out.rstrip() + f"\n\n⚠️ *{what} removed -- check current amounts with the relevant office.*"


def fmt_date(iso):
    try:
        return dt.date.fromisoformat(iso).strftime("%-d %b %Y")
    except Exception:
        return iso


class Responder:
    """Single-question port of Responder.kt (fresh conversation for every question)."""

    def __init__(self, db, system, facts, answer_lang="en"):
        self.db, self.system, self.facts = db, system, facts
        self.answer_lang = answer_lang
        self.out = "en"   # language the model is told to write in, set per question in respond()
        self.as_of = db.execute("SELECT value FROM meta WHERE key = 'as_of'").fetchone()[0]
        commit = db.execute("SELECT value FROM meta WHERE key = 'source_commit'").fetchone()
        self.pack_id = " @ ".join(x for x in (self.as_of, commit[0] if commit else "") if x)

    def stamp(self, topic, lang):
        src = qp.canned_source(self.db, topic)
        if src:
            return pick(lang, f"Source: {src[0]} · checked {fmt_date(src[2])}",
                        f"Chanzo: {src[0]} · kimekaguliwa {fmt_date(src[2])}")
        return pick(lang, f"accurate as of {fmt_date(self.as_of)}", f"sahihi hadi {fmt_date(self.as_of)}")

    def topic_title(self, topic, lang):
        ans = qp.canned_answer(self.db, topic, lang)[0] or ""
        m = re.search(r"\*\*(.+?)\*\*", ans)
        if m:
            return m.group(1).rstrip(": ")
        t = topic.replace("_", " ")
        return t[:1].upper() + t[1:]

    def context_line(self):
        parts = []
        if self.ctx_business:
            parts.append(f"business -- {self.ctx_business}")
        if self.ctx_place:
            parts.append(f"location -- {self.ctx_place}")
        return ("About the operator: " + "; ".join(parts) + ".\n\n") if parts else ""

    def learn_context(self, q):
        l, learnt = q.lower(), False
        for rx in BUSINESS_RES:
            m = rx.search(l)
            if not m:
                continue
            b = re.split(r"\s+(?:in|at|from|kwa|huko|na|and)\s+", m.group(1))[0].strip()
            b = " ".join(b.split()[:4])
            if len(b) >= 3:
                self.ctx_business, learnt = b, True
            break
        for w in qp.words(l):
            if w in PLACES:
                self.ctx_place, learnt = w.capitalize(), True
                break
        return learnt

    def respond(self, q):
        """Returns (trace, reply) with reply = ("text", text) or ("model", prompt, footer, check_against)."""
        self.ctx_business = self.ctx_place = ""
        lang = detect_lang(q)
        self.out = lang if self.answer_lang == "operator" else "en"
        if COMPLAINT.search(q.lower()):
            return dict(lang=lang, route="COMPLAINT"), ("text", "complaint reply")
        if self.learn_context(q) and (not q.lower().strip().endswith("?") and not QUESTION_START.search(q.lower().strip())
                                      and len(qp.words(q)) <= 10):
            summ = " · ".join(x for x in (self.ctx_business, self.ctx_place) if x)
            return dict(lang=lang, route="CONTEXT"), ("text", pick(lang, f"Asante -- noted: **{summ}**.",
                                                                    f"Asante -- nimezingatia: **{summ}**."))
        if re.fullmatch(r"(\d{1,2}|yes|no|ndiyo|ndio|hapana)[.!]?", q.lower()):
            return dict(lang=lang, route="NO-QUESTION"), ("text", "no question")

        r = qp.route(self.db, q, lang)
        trace = dict(lang=lang, answer_lang=self.out, lang_mix=lang_mix(q),
                     expanded=" ".join(r.get("expanded", [])), route=r["kind"],
                     topic=r["topic"], domain=r.get("domain", ""), confidence=r["confidence"], suggest=r["suggest"],
                     sources="; ".join(h["source"] for h in r["hits"][:2]))
        k = r["kind"]
        if k == "CHAT":
            return trace, ("text", "chat reply")
        if k == "APP_INFO":
            return trace, ("text", "clock reply")
        if k == "NOT_UNDERSTOOD":
            return trace, ("text", "Sorry, I didn't understand. Please ask in English or Kiswahili.\n\n"
                                   "Samahani, sijaelewa. Tafadhali uliza kwa Kiingereza au Kiswahili.")
        if k == "FOLLOW_UP":
            return trace, ("text", pick(lang, "My last answer didn't come from a stored document. Which topic "
                                              "would you like to know more about?",
                                        "Jibu langu la mwisho halikutoka kwenye hati iliyohifadhiwa. Ungependa "
                                        "kujua zaidi kuhusu mada gani?"))
        if k == "VERIFIED":
            return trace, ("text", self.verified(r, q, lang))
        if k == "SUGGEST":
            t = self.topic_title(r["suggest"], lang)
            return trace, ("text", pick(lang, f"I have a verified answer that may match your question: **{t}**\n\n"
                                              "Reply **1** to see it, or **2** for what the documents say.",
                                        f"Nina jibu lililothibitishwa ambalo huenda linajibu swali lako: **{t}**\n\n"
                                        "Jibu **1** kuliona, au **2** kuona hati zinasema nini."))
        if k.startswith("FACTUAL"):
            return trace, self.documents(r, q, lang)
        if k == "DIGEST":
            return trace, ("model", self.digest_prompt(q), model_footer(
                lang, f"✅ *Based on verified figures (accurate as of {fmt_date(self.as_of)}). Confirm with "
                      f"{office(q, lang)} for your own case.*",
                f"✅ *Kulingana na takwimu zilizothibitishwa (sahihi hadi {fmt_date(self.as_of)}). Thibitisha na "
                f"{office(q, lang)} kwa hali yako.*", self.out), None)
        background = r["hits"][0] if r["hits"] and r["confidence"] == "STRONG" else None
        return trace, ("model", self.advisory_prompt(q, background), model_footer(
            lang, "💡 *General advice, not verified information.*",
            "💡 *Ushauri wa jumla, si taarifa iliyothibitishwa.*", self.out),
            background["body"] if background else "")

    def verified(self, r, q, lang):
        topic = r["topic"]
        ans, _, sw = qp.canned_answer(self.db, topic, lang)
        s = ans or ""
        if lang == "sw" and not sw:
            s = "*(Jibu hili bado halipo kwa Kiswahili.)*\n\n" + s
        f = r.get("followup")
        if f:
            words = ", ".join(f"**{w}**" for w in f["words"])
            top = f["hits"][0] if f["hits"] else None
            s += "\n\n"
            if f["confidence"] != "WEAK" and top:
                s += pick(lang, f"📄 *You also asked about {words}. A related document: {title(top['source'])}*",
                          f"📄 *Uliuliza pia kuhusu {words}. Hati inayohusiana: {title(top['source'])}*")
            else:
                s += pick(lang, f"⚠️ *I don't have verified information on {words} specifically. Check with {office(q, lang)}.*",
                          f"⚠️ *Sina taarifa iliyothibitishwa kuhusu {words} hasa. Wasiliana na {office(q, lang)}.*")
        t = self.topic_title(topic, lang)
        if not f:
            s += footer(lang, f"✅ *Verified answer · {self.stamp(topic, 'en')}*",
                        f"✅ *Jibu lililothibitishwa · {self.stamp(topic, 'sw')}*")
        else:
            s += footer(lang, f"✅ *Verified only for: {t} · {self.stamp(topic, 'en')}*",
                        f"✅ *Imethibitishwa kwa: {t} pekee · {self.stamp(topic, 'sw')}*")
        return s

    def documents(self, r, q, lang):
        if r["confidence"] == "STRONG":
            used = r["hits"][:2]
            srcs = list(dict.fromkeys(h["source"] for h in used))
            names = "; ".join(title(x) for x in srcs)
            prompt = ("Answer the question using ONLY the document extracts below. If they do not contain the answer, "
                      "say so in one sentence. Do not add any figure, fee, rate, date, phone number or website that is not "
                      f"in the extracts. {WRITE_IN[self.out]}, in at most 120 words, as short numbered steps where possible.\n\n"
                      "Extracts:\n" + "\n".join(f"[{i + 1}] ({title(h['source'])}) {excerpt(h['body'], 700)}"
                                                for i, h in enumerate(used))
                      + "\n\n" + self.context_line() + f"Question: {q}")
            return ("model", prompt, model_footer(
                lang, f"📄 *From: {names}. Confirm with {office(q, lang)} before acting.*",
                f"📄 *Chanzo: {names}. Thibitisha na {office(q, lang)} kabla ya kuchukua hatua.*", self.out),
                "\n".join(h["body"] for h in used))
        if r["confidence"] == "PARTIAL":
            s = pick(lang, "I found documents that may only partly answer this:",
                     "Nimepata hati ambazo huenda zinajibu swali hili kwa sehemu tu:")
            for h in r["hits"][:2]:
                s += f"\n\n> {excerpt(h['body'], focus=r['focus'])}\n\n— *{title(h['source'])}*"
            s += "\n\n" + pick(lang, f"For a definite answer, check with {office(q, lang)}.",
                               f"Kwa jibu la uhakika, wasiliana na {office(q, lang)}.")
            return ("text", s)
        return ("text", pick(lang, f"I don't have verified information on this yet. For a reliable answer, contact {office(q, lang)}.",
                             f"Bado sina taarifa iliyothibitishwa kuhusu hili. Kwa jibu la kuaminika, wasiliana na {office(q, lang)}."))

    def digest_prompt(self, q):
        skip = {"what", "your", "with", "from", "have", "does", "much", "many", "need", "kenya", "there"}
        words = [w for w in re.split(r"[^a-z0-9]+", q.lower()) if len(w) > 3 and w not in skip]
        relevant = [f for f in self.facts if any(w in f.lower() for w in words)]
        facts = relevant[:4] if relevant else self.facts
        return ("Answer the question using ONLY the verified facts below, exactly as stated. If they do not cover "
                "the question, say so in one sentence. When asked to calculate a KES amount, compute it step by step "
                f"and double-check the arithmetic. {WRITE_IN[self.out]}, in at most 120 words.\n\n"
                "Verified facts:\n" + "\n".join(facts) + "\n\n" + self.context_line() + f"Question: {q}")

    def advisory_prompt(self, q, background):
        return ("Give practical, general business advice to a small business owner in Kenya. Answer as 3 to 5 short "
                "points, in at most 120 words. Do not state specific prices, fees, interest rates, tax rates, laws, "
                "statistics or other figures, and do not state facts about specific named businesses, places or people. "
                "If the question is not about business, answer briefly and kindly.\n\n"
                + (f"Background (from a stored document): {excerpt(background['body'], 600)}\n\n" if background else "")
                + self.context_line() + f"Question: {q}\n\n{ONLY_THIS[self.out]}")


# ---------------------------------------------------------------- model call
TEMPLATES = {
    # Qwen ChatML -- exactly what the phone sends.
    "chatml": (lambda system, prompt: f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{prompt}"
                                      f"<|im_end|>\n<|im_start|>assistant\n",
               ["<|im_end|>", "<|endoftext|>"]),
    # Gemma 2/3: no system role, so the system prompt opens the user turn (as Gemma's own template does).
    # llama-server adds <bos> itself when it tokenizes the prompt.
    "gemma": (lambda system, prompt: f"<start_of_turn>user\n{system}\n\n{prompt}<end_of_turn>\n"
                                     f"<start_of_turn>model\n",
              ["<end_of_turn>", "<eos>"]),
}


def server_props(url):
    """Model file and chat template of the model llama-server has loaded ({} if /props is unavailable)."""
    try:
        with urllib.request.urlopen(url.rstrip("/") + "/props", timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return {}


def pick_template(choice, props):
    if choice != "auto":
        return choice
    tpl = props.get("chat_template", "") or ""
    name = os.path.basename(props.get("model_path", "") or "").lower()
    return "gemma" if "<start_of_turn>" in tpl or "gemma" in name else "chatml"


def model_tag(props):
    """Short model name for file names and reports, e.g. msme-qwen2.5-1.5b-Q4_K_M."""
    name = os.path.basename(props.get("model_path", "") or "")
    return os.path.splitext(name)[0] or "unknown-model"


def complete(url, system, prompt, n_predict, temperature, template="chatml"):
    build, stop = TEMPLATES[template]
    text = build(system, prompt)
    body = json.dumps(dict(prompt=text, n_predict=n_predict, temperature=temperature, cache_prompt=False,
                           stop=stop)).encode()
    req = urllib.request.Request(url.rstrip("/") + "/completion", data=body,
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        out = json.loads(resp.read())
    return out.get("content", ""), out.get("timings", {}), (time.time() - t0) * 1000


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=os.path.join(ROOT, "rafiki_pack.db"))
    ap.add_argument("--tests", default=os.path.join(HERE, "test_set.csv"))
    ap.add_argument("--rafiki-kt", default=RAFIKI_KT)
    ap.add_argument("--server", default="http://127.0.0.1:8090")
    ap.add_argument("--passes", type=int, default=1)
    ap.add_argument("--limit", type=int, help="only the first N questions (trial)")
    ap.add_argument("--split", choices=["all", "dev", "test"], default="all")
    ap.add_argument("--temperature", type=float, default=0.3, help="phone default: 0.3")
    ap.add_argument("--n-predict", type=int, default=300, help="phone default: 300")
    ap.add_argument("--answer-lang", choices=["en", "operator"], default="en",
                    help="en = model always writes English (today's phone); operator = Kiswahili questions get "
                         "Kiswahili answers")
    ap.add_argument("--template", choices=["auto", "chatml", "gemma"], default="auto",
                    help="prompt format; auto = chosen from the loaded model's chat template")
    ap.add_argument("--model-only", action="store_true",
                    help="only questions routed to the model (skip verified answers, suggestions, declines): "
                         "for comparing models")
    ap.add_argument("--out", help="output file (default: eval/laptop_runs/rafiki_eval_laptop_<time>[_<model>_<lang>]"
                                  ".jsonl); an existing file is continued")
    a = ap.parse_args()

    props = server_props(a.server)
    if not props:
        raise SystemExit(f"Could not reach llama-server at {a.server}. Start it first (see the top of this file).")
    template, tag = pick_template(a.template, props), model_tag(props)
    print(f"Model {tag} | prompt format {template} | answers in "
          f"{'the operator language' if a.answer_lang == 'operator' else 'English'}"
          f"{' | model-routed questions only' if a.model_only else ''}")

    system, facts = read_rafiki(a.rafiki_kt)
    db = sqlite3.connect(a.db)
    resp = Responder(db, system, facts, a.answer_lang)
    items = []
    for i, row in enumerate(csv.DictReader(open(a.tests, encoding="utf-8"))):
        split = "dev" if i % 2 == 0 else "test"
        if a.split != "all" and split != a.split:
            continue
        for lang in ("en", "sw"):
            if row[f"question_{lang}"].strip():
                items.append((row["id"], lang, " ".join(row[f"question_{lang}"].split())))
    if a.limit:
        items = items[:a.limit]

    os.makedirs(os.path.join(HERE, "laptop_runs"), exist_ok=True)
    run = dt.datetime.now().strftime("%Y-%m-%dT%H%M")
    default_plain = a.answer_lang == "en" and not a.model_only and tag == "msme-qwen2.5-1.5b-Q4_K_M"
    suffix = "" if default_plain else f"_{tag}_{'sw' if a.answer_lang == 'operator' else 'en'}"
    out = a.out or os.path.join(HERE, "laptop_runs", f"rafiki_eval_laptop_{run}{suffix}.jsonl")
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            if l.strip().startswith("{"):
                o = json.loads(l)
                if o.get("model_file", tag) != tag or o.get("answer_mode", a.answer_lang) != a.answer_lang:
                    raise SystemExit(f"{out} was made with {o.get('model_file')} ({o.get('answer_mode')} answers); "
                                     f"the server has {tag} loaded. Use another --out, or load that model.")
                run = o.get("run", run)
                done.add((o.get("pass"), o.get("id"), o.get("lang")))
        print(f"Continuing {out}: {len(done)} answers already there")

    if a.model_only:   # routing is deterministic, so a question routed elsewhere is never a model answer
        before = len(items)
        items = [it for it in items if resp.respond(it[2])[1][0] == "model"]
        print(f"{len(items)} of {before} questions reach the model")

    total, n = len(items) * a.passes, len(done)
    with open(out, "a", encoding="utf-8") as f:
        for p in range(1, a.passes + 1):
            for seq, (qid, lang, q) in enumerate(items):
                if (p, qid, lang) in done:
                    continue
                n += 1
                trace, reply = resp.respond(q)
                o = dict(run=run, **{"pass": p}, seq=seq, id=qid, lang=lang, question=q,
                         time=dt.datetime.now().isoformat(timespec="seconds"), device="laptop",
                         pack=resp.pack_id, model_file=tag, template=template, answer_mode=a.answer_lang,
                         **{("lang_detected" if k == "lang" else k): v for k, v in trace.items()})
                if reply[0] == "text":
                    o.update(model="no", answer=reply[1], total_ms=0)
                else:
                    _, prompt, foot, check = reply
                    try:
                        content, tim, ms = complete(a.server, system, prompt, a.n_predict, a.temperature, template)
                    except Exception as e:
                        raise SystemExit(f"\nCould not reach llama-server at {a.server} ({e}). Start it first "
                                         f"(see the top of this file); the run continues where it stopped.")
                    o.update(model="yes", answer=figure_check(content.strip(), check) + foot,
                             prompt_chars=len(prompt), gen_tokens=tim.get("predicted_n", 0),
                             ttft_ms=round(tim.get("prompt_ms", 0)), decode_tps=tim.get("predicted_per_second", 0.0),
                             total_ms=round(ms))
                f.write(json.dumps(o, ensure_ascii=False) + "\n")
                f.flush()
                print(f"\r{n}/{total} {qid} {lang} {o['route']:<16}", end="", flush=True)
    print(f"\nWrote {out}\nScore it:  python3 eval/score_phone_eval.py {os.path.relpath(out)}")


if __name__ == "__main__":
    main()
