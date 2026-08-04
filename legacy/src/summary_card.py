"""
summary_card.py — Animated Summary Card Generator
Analyzes Claude's answer and generates a visual HTML summary card.
"""

import re


def should_show_card(answer: str) -> bool:
    """Only show card when answer has enough structured content."""
    if len(answer.split()) < 80:
        return False
    signals = 0
    if re.search(r'step\s+\d|^\d+[.)]\s', answer, re.MULTILINE | re.IGNORECASE):
        signals += 1
    if re.search(r'KES?\s*[\d,]+|Ksh', answer, re.IGNORECASE):
        signals += 1
    if re.search(r'\d+\s+days?|by\s+\w+\s+\d+|monthly|annually', answer, re.IGNORECASE):
        signals += 1
    if re.search(r'must|required|eligible|qualify|documents?', answer, re.IGNORECASE):
        signals += 1
    if re.search(r'https?://|\.go\.ke|\.or\.ke', answer):
        signals += 1
    return signals >= 2


def extract_summary(answer: str, question: str) -> dict:
    """Extract key points from Claude's answer for the card."""
    lines = [l.strip() for l in answer.split('\n') if l.strip()]
    q = question.lower()

    if any(w in q for w in ['register', 'registration', 'brs', 'incorporate']):
        topic, color, icon = "Business Registration", "#1a6b3c", "🏢"
    elif any(w in q for w in ['tax', 'vat', 'paye', 'kra', 'turnover', 'etims']):
        topic, color, icon = "Tax and KRA", "#c0392b", "🧾"
    elif any(w in q for w in ['loan', 'fund', 'finance', 'credit', 'hustler', 'yedf', 'wef', 'sacco']):
        topic, color, icon = "Financing", "#1565c0", "💳"
    elif any(w in q for w in ['permit', 'license', 'county', 'nairobi', 'mombasa']):
        topic, color, icon = "Permits and Licenses", "#6a1b9a", "📜"
    elif any(w in q for w in ['nssf', 'nhif', 'shif', 'nita', 'insurance', 'social']):
        topic, color, icon = "Social Security", "#e65100", "🏥"
    elif any(w in q for w in ['export', 'trade', 'afcfta', 'comesa', 'eac', 'market']):
        topic, color, icon = "Trade and Export", "#00695c", "🚢"
    elif any(w in q for w in ['mpesa', 'm-pesa', 'digital', 'mobile money', 'paybill']):
        topic, color, icon = "Digital Finance", "#37474f", "📱"
    else:
        topic, color, icon = "Business Advisory", "#2e7d32", "💡"

    costs = re.findall(r'KES?\s*[\d,]+(?:\s*(?:million|billion|thousand))?|Ksh\.?\s*[\d,]+', answer, re.IGNORECASE)
    costs = list(dict.fromkeys(costs))[:4]

    deadlines = re.findall(r'\d+(?:st|nd|rd|th)\s+\w+|\d+\s+days?|monthly|annually', answer, re.IGNORECASE)
    deadlines = list(dict.fromkeys(deadlines))[:3]

    steps = re.findall(r'(?:Step\s+\d+[:\.]?\s*|^\d+[.):]\s*)(.+)', answer, re.MULTILINE)
    steps = [s.strip()[:80] for s in steps if len(s.strip()) > 10][:5]

    requirements = []
    for line in lines:
        if any(w in line.lower() for w in ['must', 'required', 'need', 'eligib', 'qualif']):
            clean = re.sub(r'\*+', '', line).strip()
            if 20 < len(clean) < 120:
                requirements.append(clean)
    requirements = requirements[:4]

    websites = re.findall(r'https?://[^\s\)]+|www\.[^\s\)]+', answer)
    websites = list(dict.fromkeys(websites))[:3]

    summary = ""
    for line in lines:
        clean = re.sub(r'\*+|#+', '', line).strip()
        if len(clean) > 40 and not clean.startswith('http'):
            summary = clean[:150]
            break

    return {
        "topic": topic, "color": color, "icon": icon,
        "summary": summary, "steps": steps, "costs": costs,
        "deadlines": deadlines, "requirements": requirements,
        "websites": websites,
    }


def render_summary_card(data: dict) -> str:
    """Renders an animated HTML summary card."""
    color = data["color"]
    light = color + "18"

    steps_html = ""
    if data["steps"]:
        items = "".join(
            f'<div class="sc-step" style="animation-delay:{i*0.15}s">'
            f'<span class="sc-num">{i+1}</span>'
            f'<span class="sc-txt">{s}</span></div>'
            for i, s in enumerate(data["steps"])
        )
        steps_html = f'<div class="sc-sec"><div class="sc-lbl">Key Steps</div>{items}</div>'

    costs_html = ""
    if data["costs"]:
        items = "".join(
            f'<span class="sc-badge" style="animation-delay:{i*0.1}s">💰 {c}</span>'
            for i, c in enumerate(data["costs"])
        )
        costs_html = f'<div class="sc-sec"><div class="sc-lbl">Costs Involved</div><div class="sc-badges">{items}</div></div>'

    req_html = ""
    if data["requirements"]:
        items = "".join(
            f'<div class="sc-req" style="animation-delay:{i*0.12}s">✅ {r}</div>'
            for i, r in enumerate(data["requirements"])
        )
        req_html = f'<div class="sc-sec"><div class="sc-lbl">Requirements</div>{items}</div>'

    dl_html = ""
    if data["deadlines"]:
        items = "".join(
            f'<span class="sc-badge sc-dl" style="animation-delay:{i*0.1}s">⏰ {d}</span>'
            for i, d in enumerate(data["deadlines"])
        )
        dl_html = f'<div class="sc-sec"><div class="sc-lbl">Key Deadlines</div><div class="sc-badges">{items}</div></div>'

    web_html = ""
    if data["websites"]:
        items = "".join(f'<a class="sc-link" href="{w}" target="_blank">🔗 {w}</a>' for w in data["websites"])
        web_html = f'<div class="sc-sec"><div class="sc-lbl">Useful Links</div>{items}</div>'

    summary_html = f'<div class="sc-summary">{data["summary"]}</div>' if data["summary"] else ""

    return f"""
<style>
@keyframes scIn {{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
@keyframes scFade {{from{{opacity:0}}to{{opacity:1}}}}
.summary-card{{border-radius:14px;border:2px solid {color};background:linear-gradient(135deg,{light},#fff);margin:1rem 0;overflow:hidden;animation:scFade 0.5s ease forwards;font-family:'Segoe UI',sans-serif;}}
.sc-header{{background:{color};color:white;padding:0.8rem 1.2rem;display:flex;align-items:center;gap:0.6rem;}}
.sc-icon{{font-size:1.5rem;}}
.sc-title{{font-size:1rem;font-weight:700;letter-spacing:0.5px;}}
.sc-sub{{font-size:0.72rem;opacity:0.85;margin-top:2px;}}
.sc-body{{padding:1rem 1.2rem;}}
.sc-summary{{font-size:0.86rem;color:#333;background:{light};border-left:4px solid {color};padding:0.5rem 0.8rem;border-radius:6px;margin-bottom:0.8rem;animation:scIn 0.4s ease forwards;}}
.sc-sec{{margin-bottom:0.8rem;}}
.sc-lbl{{font-size:0.72rem;font-weight:700;color:{color};text-transform:uppercase;letter-spacing:0.8px;margin-bottom:0.4rem;}}
.sc-step{{display:flex;align-items:flex-start;gap:0.5rem;margin-bottom:0.35rem;animation:scIn 0.4s ease forwards;opacity:0;}}
.sc-num{{background:{color};color:white;border-radius:50%;width:20px;height:20px;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;margin-top:2px;}}
.sc-txt{{font-size:0.82rem;color:#444;line-height:1.4;}}
.sc-req{{font-size:0.82rem;color:#333;margin-bottom:0.25rem;animation:scIn 0.4s ease forwards;opacity:0;}}
.sc-badges{{display:flex;flex-wrap:wrap;gap:0.4rem;}}
.sc-badge{{font-size:0.78rem;padding:0.25rem 0.6rem;border-radius:20px;font-weight:600;background:{color}22;border:1px solid {color}44;color:{color};animation:scIn 0.4s ease forwards;opacity:0;}}
.sc-dl{{background:#fff3e0;border:1px solid #ff9800;color:#e65100;}}
.sc-link{{display:block;font-size:0.8rem;color:{color};text-decoration:none;margin-bottom:0.2rem;word-break:break-all;}}
.sc-link:hover{{text-decoration:underline;}}
.sc-footer{{background:#f8f8f8;border-top:1px solid #eee;padding:0.5rem 1.2rem;font-size:0.72rem;color:#888;display:flex;justify-content:space-between;}}
</style>
<div class="summary-card">
  <div class="sc-header">
    <span class="sc-icon">{data["icon"]}</span>
    <div><div class="sc-title">{data["icon"]} {data["topic"]}</div>
    <div class="sc-sub">Kenya MSME Advisor — Quick Reference Card</div></div>
  </div>
  <div class="sc-body">
    {summary_html}{steps_html}{req_html}{costs_html}{dl_html}{web_html}
  </div>
  <div class="sc-footer">
    <span>🇰🇪 Kenya MSME Advisory Platform</span>
    <span>⚠️ For guidance only — consult a professional for complex decisions</span>
  </div>
</div>"""
