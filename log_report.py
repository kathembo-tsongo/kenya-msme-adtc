"""Turn Rafiki test/pilot logs into a readable report: summary tables + each conversation as a chat transcript.

Run from the kenya-msme-adtc folder:
    python3 log_report.py phone_logs/rafiki_log_20261005-1306.jsonl
    python3 log_report.py ~/Downloads/rafiki_log_P01_20261105-1400.txt      # a log exported from the app
    python3 log_report.py phone_logs/*.jsonl                                 # several logs together
Writes phone_logs/report_<name>.html (open it in a browser; print to PDF for an appendix) and a plain-text
version phone_logs/report_<name>.txt. Conversations are grouped by participant and split into sessions when
more than 30 minutes pass between questions.
"""
import datetime as dt
import html
import json
import os
import re
import sys
from collections import Counter, defaultdict

GAP = dt.timedelta(minutes=30)

ROUTE_STYLE = {   # label, colour
    "VERIFIED": ("Verified", "#1b7f3b"),
    "SUGGEST": ("Suggestion", "#8a6d00"),
    "DOCUMENTS": ("Documents", "#1f5fa8"),
    "FACTUAL": ("Documents", "#1f5fa8"),
    "DIGEST": ("Verified facts (model)", "#5b4bb7"),
    "ADVISORY": ("Advice (model)", "#7a4fa0"),
    "COMPLAINT": ("Complaint", "#b3261e"),
    "CHAT": ("Chat", "#666"),
}


def route_style(route):
    for key, val in ROUTE_STYLE.items():
        if route.startswith(key):
            return val
    return (route or "?", "#666")


def load(paths):
    rows = []
    for p in paths:
        for line in open(os.path.expanduser(p), encoding="utf-8", errors="replace"):
            line = line.strip()
            if line.startswith("{"):
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    for r in rows:
        r["_t"] = dt.datetime.fromisoformat(r.get("time", "1970-01-01T00:00:00"))
    return sorted(rows, key=lambda r: (r.get("participant", ""), r["_t"]))


def sessions(rows):
    by_p = defaultdict(list)
    for r in rows:
        by_p[r.get("participant") or "—"].append(r)
    out = []
    for p, rs in by_p.items():
        cur = [rs[0]]
        for prev, r in zip(rs, rs[1:]):
            if r["_t"] - prev["_t"] > GAP:
                out.append((p, cur))
                cur = []
            cur.append(r)
        out.append((p, cur))
    return out


def md_to_html(text):
    """Enough markdown for Rafiki answers: **bold**, *italic*, line breaks, the --- footer rule."""
    t = html.escape(text)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", t)
    t = t.replace("\n---\n", '\n<hr class="f">')
    return t.replace("\n", "<br>")


def secs(ms):
    ms = int(ms or 0)
    return f"{ms} ms" if ms < 1000 else f"{ms/1000:.1f} s"


def median(xs):
    xs = sorted(xs)
    return xs[len(xs) // 2] if xs else 0


def summary(rows):
    model = [int(r.get("ms", 0)) for r in rows if r.get("model") == "yes"]
    instant = [int(r.get("ms", 0)) for r in rows if r.get("model") != "yes"]
    routes = Counter(route_style(r.get("route", ""))[0] for r in rows)
    langs = Counter({"sw": "Kiswahili", "en": "English"}.get(r.get("lang", ""), r.get("lang", "?")) for r in rows)
    parts = Counter(r.get("participant") or "—" for r in rows)
    return model, instant, routes, langs, parts


def build_html(rows, title):
    model, instant, routes, langs, parts = summary(rows)
    first, last = rows[0]["_t"], rows[-1]["_t"]

    def table(head, items):
        body = "".join(f"<tr><td>{html.escape(str(k))}</td><td class=n>{v}</td></tr>" for k, v in items)
        return f"<table><tr><th>{head}</th><th>Questions</th></tr>{body}</table>"

    out = [f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title>
<style>
body{{font-family:system-ui,Segoe UI,Roboto,sans-serif;max-width:900px;margin:24px auto;padding:0 16px;color:#222;background:#fafafa}}
h1{{font-size:22px}} h2{{font-size:18px;margin-top:32px;border-bottom:2px solid #ddd;padding-bottom:4px}}
.grid{{display:flex;gap:16px;flex-wrap:wrap}} table{{border-collapse:collapse;background:#fff;font-size:14px}}
td,th{{border:1px solid #ddd;padding:4px 10px;text-align:left}} th{{background:#f0f0f0}} .n{{text-align:right}}
.turn{{margin:14px 0}} .q{{background:#1f5fa8;color:#fff;padding:8px 12px;border-radius:12px 12px 2px 12px;
display:inline-block;max-width:80%;float:right;clear:both}}
.a{{background:#fff;border:1px solid #ddd;padding:10px 12px;border-radius:12px 12px 12px 2px;max-width:85%;
clear:both;margin-top:6px;display:inline-block;font-size:14px}}
.meta{{clear:both;font-size:12px;color:#555;margin-top:4px}} .badge{{color:#fff;padding:1px 7px;border-radius:8px;font-size:11px}}
.cf{{clear:both}} hr.f{{border:0;border-top:1px solid #eee}} .sess{{color:#777;font-size:13px}}
.flag{{border-left:4px solid #b3261e;padding-left:8px}}
</style></head><body>
<h1>{html.escape(title)}</h1>
<p>{len(rows)} questions · {len(parts)} participant(s) · {first:%d %b %Y %H:%M} – {last:%d %b %Y %H:%M}</p>
<div class=grid>
{table("Answer type", routes.most_common())}
{table("Language", langs.most_common())}
{table("Participant", parts.most_common())}
<table><tr><th>Response time</th><th>Median</th><th>Slowest</th><th>n</th></tr>
<tr><td>Instant (verified, quoted, fixed)</td><td class=n>{secs(median(instant))}</td><td class=n>{secs(max(instant, default=0))}</td><td class=n>{len(instant)}</td></tr>
<tr><td>Written by the model</td><td class=n>{secs(median(model))}</td><td class=n>{secs(max(model, default=0))}</td><td class=n>{len(model)}</td></tr></table>
</div>"""]

    for i, (p, rs) in enumerate(sessions(rows), 1):
        out.append(f"<h2>Participant {html.escape(p)} — session {i}</h2>"
                   f"<p class=sess>{rs[0]['_t']:%a %d %b %Y, %H:%M} – {rs[-1]['_t']:%H:%M} · {len(rs)} questions"
                   f" · pack {html.escape(rs[0].get('pack', '?'))}</p>")
        pack = rs[0].get("pack", "")
        for r in rs:
            label, colour = route_style(r.get("route", ""))
            bits = [f"{r['_t']:%H:%M:%S}", f'<span class=badge style="background:{colour}">{html.escape(label)}</span>']
            if r.get("topic"):
                bits.append(f"topic: {html.escape(r['topic'])}")
            if r.get("suggest"):
                bits.append(f"offered: {html.escape(r['suggest'])}")
            if r.get("confidence"):
                bits.append(f"match: {html.escape(r['confidence'].lower())}")
            bits.append({"sw": "Kiswahili", "en": "English"}.get(r.get("lang", ""), r.get("lang", "")))
            bits.append(secs(r.get("ms")))
            if r.get("sources"):
                bits.append("sources: " + html.escape(r["sources"].replace("\\/", "/")))
            if r.get("pack", "") != pack:      # the app was updated during the session
                pack = r.get("pack", "")
                bits.append(f"<b>new pack {html.escape(pack)}</b>")
            flag = " flag" if r.get("route", "").startswith("COMPLAINT") else ""
            out.append(f'<div class="turn{flag}"><div class=q>{html.escape(r.get("question", ""))}</div>'
                       f'<div class=a>{md_to_html(r.get("answer", ""))}</div>'
                       f'<div class=meta>{" · ".join(b for b in bits if b)}</div></div>')
    out.append("<div class=cf></div></body></html>")
    return "\n".join(out)


def build_text(rows, title):
    model, instant, routes, langs, parts = summary(rows)
    L = [title, "=" * len(title), f"{len(rows)} questions · {len(parts)} participant(s)", "",
         "Answer types:  " + ", ".join(f"{k} {v}" for k, v in routes.most_common()),
         "Languages:     " + ", ".join(f"{k} {v}" for k, v in langs.most_common()),
         f"Response time: instant median {secs(median(instant))} (n={len(instant)}); "
         f"model median {secs(median(model))}, slowest {secs(max(model, default=0))} (n={len(model)})", ""]
    for i, (p, rs) in enumerate(sessions(rows), 1):
        head = f"Participant {p} — session {i} — {rs[0]['_t']:%a %d %b %Y %H:%M}"
        L += ["", head, "-" * len(head)]
        for r in rs:
            label = route_style(r.get("route", ""))[0]
            extra = " · ".join(x for x in [r.get("topic") and f"topic {r['topic']}",
                                            r.get("suggest") and f"offered {r['suggest']}", secs(r.get("ms"))] if x)
            ans = re.sub(r"\*\*?(.+?)\*\*?", r"\1", r.get("answer", "")).split("\n---\n")[0].strip()
            L += [f"[{r['_t']:%H:%M}] Q: {r.get('question', '').strip()}",
                  f"        → {label} ({extra})",
                  "          " + ans.replace("\n", "\n          "), ""]
    return "\n".join(L)


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not paths:
        print(__doc__)
        return
    rows = load(paths)
    if not rows:
        print("No log lines found.")
        return
    name = os.path.splitext(os.path.basename(paths[0]))[0] + (f"_and_{len(paths)-1}_more" if len(paths) > 1 else "")
    title = f"Rafiki wa Biashara — conversation log ({name})"
    os.makedirs("phone_logs", exist_ok=True)
    h, t = f"phone_logs/report_{name}.html", f"phone_logs/report_{name}.txt"
    open(h, "w", encoding="utf-8").write(build_html(rows, title))
    open(t, "w", encoding="utf-8").write(build_text(rows, title))
    print(f"{len(rows)} questions -> {h}")
    print(f"               -> {t}")


if __name__ == "__main__":
    main()
