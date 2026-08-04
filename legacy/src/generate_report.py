"""
generate_report.py — Professional PDF Analytics Report
Kenya MSME Advisor — Strathmore University MSIT Thesis 2026
"""

import io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image, PageBreak
)
from datetime import datetime

DARK_GREEN  = colors.HexColor("#006600")
DARK_RED    = colors.HexColor("#cc0000")
DARK_NAVY   = colors.HexColor("#1a1a2e")
LIGHT_GREEN = colors.HexColor("#e8f5e9")
LIGHT_GRAY  = colors.HexColor("#f5f5f5")
MID_GRAY    = colors.HexColor("#cccccc")
WHITE       = colors.white
MPL_GREEN   = "#006600"
MPL_RED     = "#cc0000"
MPL_NAVY    = "#1a1a2e"
MPL_GOLD    = "#f9a825"


def make_topic_bar(topics, total):
    labels = list(topics.keys())
    values = list(topics.values())
    pcts   = [v / total * 100 for v in values]
    fig, ax = plt.subplots(figsize=(7, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    clrs = [MPL_GREEN if i == 0 else MPL_NAVY for i in range(len(labels))]
    bars = ax.barh(labels[::-1], values[::-1],
                   color=clrs[::-1], height=0.6,
                   edgecolor="white", linewidth=0.5)
    for bar, pct in zip(bars, pcts[::-1]):
        ax.text(bar.get_width() + 0.1,
                bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", va="center", ha="left",
                fontsize=8, color=MPL_NAVY, fontweight="bold")
    ax.set_xlabel("Number of Questions", fontsize=9, color=MPL_NAVY)
    ax.set_title("Questions by Topic Category",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    ax.tick_params(axis="both", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlim(0, max(values) * 1.25)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def make_language_pie(languages):
    lang_map = {
        "english": "English", "kiswahili": "Kiswahili",
        "dholuo": "Dholuo", "kikuyu": "Kikuyu",
        "kalenjin": "Kalenjin", "kamba": "Kamba",
    }
    labels = [lang_map.get(k, k) for k in languages.keys()]
    values = list(languages.values())
    clrs   = [MPL_GREEN, MPL_RED, MPL_NAVY, MPL_GOLD, "#9c27b0", "#00796b"]
    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_facecolor("white")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=clrs[:len(values)],
        autopct="%1.1f%%", startangle=90, pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 2}
    )
    for t in texts:      t.set_fontsize(8)
    for at in autotexts:
        at.set_fontsize(7); at.set_fontweight("bold"); at.set_color("white")
    ax.set_title("Language Distribution",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def make_response_donut(fast, medium, slow):
    values = [fast, medium, slow]
    labels = ["Fast\n(<10s)", "Medium\n(10-30s)", "Slow\n(>30s)"]
    clrs   = [MPL_GREEN, MPL_GOLD, MPL_RED]
    fig, ax = plt.subplots(figsize=(4, 3.5))
    fig.patch.set_facecolor("white")
    wedges, texts, autotexts = ax.pie(
        values, labels=labels, colors=clrs,
        autopct="%1.1f%%", startangle=90, pctdistance=0.75,
        wedgeprops={"width": 0.5, "edgecolor": "white", "linewidth": 2}
    )
    for t in texts:      t.set_fontsize(8)
    for at in autotexts:
        at.set_fontsize(7); at.set_fontweight("bold"); at.set_color("white")
    ax.set_title("Response Time Distribution",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def make_daily_activity(dates):
    sorted_dates = sorted(dates.items())
    labels = [d[0] for d in sorted_dates]
    values = [d[1] for d in sorted_dates]
    fig, ax = plt.subplots(figsize=(7, 2.8))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar(labels, values, color=MPL_GREEN,
                  edgecolor="white", linewidth=0.5, width=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.3, str(val),
                ha="center", va="bottom",
                fontsize=9, fontweight="bold", color=MPL_NAVY)
    ax.set_ylabel("Questions", fontsize=9, color=MPL_NAVY)
    ax.set_title("Daily Activity",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    ax.tick_params(axis="both", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0, max(values) * 1.2)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def make_score_chart(excellent, good, partial, weak):
    labels = ["Excellent\n(5/5)", "Good\n(4/5)",
              "Partial\n(3/5)", "Weak/Poor\n(≤2)"]
    values = [excellent, good, partial, weak]
    clrs   = [MPL_GREEN, "#2196f3", MPL_GOLD, MPL_RED]
    fig, ax = plt.subplots(figsize=(5, 3))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.bar(labels, values, color=clrs,
                  edgecolor="white", linewidth=0.5, width=0.5)
    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.1, str(val),
                ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=MPL_NAVY)
    ax.set_ylabel("Questions", fontsize=9, color=MPL_NAVY)
    ax.set_title("Score Distribution",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    ax.tick_params(axis="both", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_ylim(0, max(values) * 1.3 if max(values) > 0 else 5)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def make_category_chart(cat_scores):
    cats = list(cat_scores.keys())
    avgs = [sum(v) / len(v) for v in cat_scores.values()]
    paired = sorted(zip(cats, avgs), key=lambda x: x[1], reverse=True)
    cats = [p[0] for p in paired]
    avgs = [p[1] for p in paired]
    clrs = [MPL_GREEN if a >= 4.5 else "#2196f3"
            if a >= 4.0 else MPL_GOLD for a in avgs]
    fig, ax = plt.subplots(figsize=(6, 3.5))
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    bars = ax.barh(cats[::-1], avgs[::-1],
                   color=clrs[::-1], height=0.6,
                   edgecolor="white", linewidth=0.5)
    for bar, avg in zip(bars, avgs[::-1]):
        ax.text(bar.get_width() + 0.02,
                bar.get_y() + bar.get_height() / 2,
                f"{avg:.2f}", va="center", ha="left",
                fontsize=8, fontweight="bold", color=MPL_NAVY)
    ax.set_xlim(0, 5.5)
    ax.axvline(x=5, color="#cccccc", linestyle="--",
               linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Mean Score (out of 5.0)", fontsize=9, color=MPL_NAVY)
    ax.set_title("Scores by Category",
                 fontsize=11, fontweight="bold", color=MPL_NAVY, pad=10)
    ax.tick_params(axis="both", labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    legend_elements = [
        mpatches.Patch(color=MPL_GREEN, label="Excellent (>=4.5)"),
        mpatches.Patch(color="#2196f3", label="Good (>=4.0)"),
        mpatches.Patch(color=MPL_GOLD,  label="Partial (<4.0)"),
    ]
    ax.legend(handles=legend_elements, loc="lower right", fontsize=7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    plt.close()
    buf.seek(0)
    return buf


def _section_header(title, width):
    style = ParagraphStyle(
        "SH", fontSize=12, fontName="Helvetica-Bold",
        textColor=colors.white,
    )
    t = Table([[Paragraph(title, style)]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), DARK_GREEN),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("LINEBELOW",     (0,0), (-1,-1), 2, DARK_RED),
    ]))
    return t


def generate_pdf_report(data):
    buf = io.BytesIO()
    W   = A4[0] - 4*cm
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
        title="Kenya MSME Advisor Research Report",
        author=data.get("author", "Kathembo Tsongo Dieudonne"),
    )

    body = ParagraphStyle(
        "Body", fontSize=9, fontName="Helvetica",
        textColor=DARK_NAVY, spaceAfter=4, alignment=TA_JUSTIFY,
    )
    caption_s = ParagraphStyle(
        "Cap", fontSize=8, fontName="Helvetica-Oblique",
        textColor=colors.gray, alignment=TA_CENTER, spaceAfter=6,
    )
    kpi_val = ParagraphStyle(
        "KV", fontSize=16, fontName="Helvetica-Bold",
        textColor=DARK_GREEN, alignment=TA_CENTER,
    )
    kpi_lbl = ParagraphStyle(
        "KL", fontSize=8, fontName="Helvetica",
        textColor=colors.gray, alignment=TA_CENTER,
    )
    finding = ParagraphStyle(
        "Find", fontSize=9, fontName="Helvetica-Oblique",
        textColor=DARK_NAVY, leftIndent=10,
        spaceAfter=4, alignment=TA_JUSTIFY,
    )
    h2 = ParagraphStyle(
        "H2", fontSize=11, fontName="Helvetica-Bold",
        textColor=DARK_NAVY, spaceBefore=10, spaceAfter=4,
    )

    story = []
    total    = data["total"]
    sessions = data["sessions"]
    avg_time = data["avg_time"]
    avg_words= data["avg_words"]
    times    = data["times"]
    fast     = data["fast"]
    medium   = data["medium"]
    slow     = data["slow"]

    # ── Cover ───────────────────────────────────────────────────────────────────
    hdr = Table(
        [[Paragraph("KENYA MSME ADVISOR", ParagraphStyle(
            "T", fontSize=20, fontName="Helvetica-Bold",
            textColor=WHITE, alignment=TA_CENTER))],
         [Paragraph("Research Analytics Report", ParagraphStyle(
            "S", fontSize=12, fontName="Helvetica",
            textColor=WHITE, alignment=TA_CENTER))],
         [Paragraph(
            "Strathmore University · School of Computing and Engineering Sciences",
            ParagraphStyle("SS", fontSize=9, fontName="Helvetica",
                           textColor=WHITE, alignment=TA_CENTER))]],
        colWidths=[W],
    )
    hdr.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), DARK_NAVY),
        ("TOPPADDING",    (0,0),(-1,-1), 18),
        ("BOTTOMPADDING", (0,0),(-1,-1), 18),
        ("LINEBELOW",     (0,2),(-1,2),  3, DARK_RED),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    meta = [
        ["Author",       data.get("author","Kathembo Tsongo Dieudonne")],
        ["Registration", "112721"],
        ["Institution",  "Strathmore University"],
        ["Programme",    "Master of Science in Information Technology"],
        ["Generated",    data.get("generated",
                         datetime.now().strftime("%Y-%m-%d %H:%M"))],
        ["System",       "Kenya MSME Advisor v1.0"],
    ]
    mt = Table(
        [[Paragraph(f"<b>{k}</b>", body), Paragraph(v, body)]
         for k, v in meta],
        colWidths=[3.5*cm, W-3.5*cm],
    )
    mt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), LIGHT_GREEN),
        ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
    ]))
    story.append(mt)
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width=W, thickness=2,
                             color=DARK_GREEN, spaceAfter=8))

    # ── Section 1: Executive Summary ────────────────────────────────────────────
    story.append(_section_header("1.  Executive Summary", W))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"This report presents operational analytics and evaluation results "
        f"for the Kenya MSME Advisor, an Artificial Intelligence-powered "
        f"advisory chatbot developed as part of an MSIT thesis at Strathmore "
        f"University. The system recorded <b>{total}</b> interactions across "
        f"<b>{sessions}</b> sessions, achieving a mean accuracy of "
        f"<b>{data.get('avg_score','4.70')}/5.00 "
        f"({data.get('accuracy','94')}%)</b> on structured evaluation. "
        f"Multilingual support was confirmed with "
        f"{len(data['languages'])} language(s) detected.",
        body
    ))
    story.append(Spacer(1, 0.3*cm))

    kpis = [
        (str(total),              "Total Q&As"),
        (str(sessions),           "Sessions"),
        (f"{avg_time}s",          "Avg Response"),
        (f"{avg_words}w",         "Avg Answer"),
        (f"{min(times):.1f}s",   "Fastest"),
        (f"{max(times):.1f}s",   "Slowest"),
    ]
    kpi_row = [[Paragraph(v, kpi_val), Paragraph(l, kpi_lbl)]
               for v, l in kpis]
    kt = Table([kpi_row], colWidths=[W/6]*6)
    kt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LIGHT_GREEN),
        ("BOX",           (0,0),(-1,-1), 1, DARK_GREEN),
        ("INNERGRID",     (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))
    story.append(kt)
    story.append(Spacer(1, 0.4*cm))

    # ── Section 2: Topic Distribution ───────────────────────────────────────────
    story.append(_section_header("2.  Topic Distribution Analysis", W))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Distribution of user queries across MSME knowledge categories, "
        "revealing the primary advisory needs of Kenyan enterprise operators.",
        body
    ))
    story.append(Spacer(1, 0.15*cm))

    topic_img = Image(make_topic_bar(data["topics"], total),
                      width=W*0.95, height=9*cm)
    story.append(topic_img)
    story.append(Paragraph("Figure 1: Topic category distribution", caption_s))

    td = [[Paragraph("<b>Topic</b>", body),
           Paragraph("<b>Questions</b>", body),
           Paragraph("<b>Share</b>", body)]]
    for topic, count in data["topics"].most_common():
        td.append([Paragraph(topic, body),
                   Paragraph(str(count), body),
                   Paragraph(f"{count/total*100:.1f}%", body)])
    tt = Table(td, colWidths=[W*0.6, W*0.2, W*0.2])
    tt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), DARK_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN",         (1,0),(-1,-1), "CENTER"),
    ]))
    story.append(tt)
    story.append(Spacer(1, 0.2*cm))
    top1 = data["topics"].most_common(1)[0]
    story.append(Paragraph(
        f"Key Finding: The most queried category is <b>{top1[0]}</b> "
        f"with {top1[1]} questions ({top1[1]/total*100:.1f}%), consistent "
        f"with World Bank identification of regulatory and financing "
        f"barriers as top MSME challenges.",
        finding
    ))

    story.append(PageBreak())

    # ── Section 3: Language & Response Time ─────────────────────────────────────
    story.append(_section_header(
        "3.  Language Distribution and Response Performance", W))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Language detection results and system response time performance "
        "across all recorded interactions.",
        body
    ))
    story.append(Spacer(1, 0.15*cm))

    lang_img = Image(make_language_pie(data["languages"]),
                     width=W*0.47, height=8*cm)
    rt_img   = Image(make_response_donut(fast, medium, slow),
                     width=W*0.47, height=8*cm)
    ct = Table([[lang_img, rt_img]], colWidths=[W*0.5, W*0.5])
    ct.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(ct)
    story.append(Paragraph(
        "Figure 2: Language distribution (left)  ·  "
        "Response time distribution (right)", caption_s))

    # Language table
    lang_map = {
        "english":"English","kiswahili":"Kiswahili",
        "dholuo":"Dholuo","kikuyu":"Kikuyu",
        "kalenjin":"Kalenjin","kamba":"Kamba",
    }
    support = {"english":"Full","kiswahili":"Full",
               "dholuo":"Partial","kikuyu":"Partial",
               "kalenjin":"Partial","kamba":"Partial"}
    ld = [[Paragraph("<b>Language</b>", body),
           Paragraph("<b>Questions</b>", body),
           Paragraph("<b>Share</b>", body),
           Paragraph("<b>Support</b>", body)]]
    for lang, count in data["languages"].most_common():
        total_l = sum(data["languages"].values())
        ld.append([
            Paragraph(lang_map.get(lang, lang.title()), body),
            Paragraph(str(count), body),
            Paragraph(f"{count/total_l*100:.1f}%", body),
            Paragraph(support.get(lang,"Partial"), body),
        ])
    lt = Table(ld, colWidths=[W*0.3, W*0.2, W*0.2, W*0.3])
    lt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), DARK_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN",         (1,0),(-1,-1), "CENTER"),
    ]))
    story.append(lt)
    story.append(Spacer(1, 0.2*cm))

    # Performance table
    story.append(Paragraph("<b>Response Time Statistics</b>", h2))
    pd_data = [
        [Paragraph("<b>Metric</b>", body),
         Paragraph("<b>Value</b>", body),
         Paragraph("<b>Note</b>", body)],
        [Paragraph("Average response time", body),
         Paragraph(f"{avg_time}s", body),
         Paragraph("Acceptable for advisory queries", body)],
        [Paragraph("Fastest response", body),
         Paragraph(f"{min(times):.1f}s", body),
         Paragraph("Excellent — near real-time", body)],
        [Paragraph("Slowest response", body),
         Paragraph(f"{max(times):.1f}s", body),
         Paragraph("Complex query or API latency", body)],
        [Paragraph(f"Fast (<10s)", body),
         Paragraph(f"{fast} ({fast/total*100:.1f}%)", body),
         Paragraph("Ideal for mobile users", body)],
        [Paragraph(f"Medium (10-30s)", body),
         Paragraph(f"{medium} ({medium/total*100:.1f}%)", body),
         Paragraph("Acceptable for advisory use", body)],
        [Paragraph(f"Slow (>30s)", body),
         Paragraph(f"{slow} ({slow/total*100:.1f}%)", body),
         Paragraph("May indicate complex queries", body)],
    ]
    pdt = Table(pd_data, colWidths=[W*0.4, W*0.2, W*0.4])
    pdt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), DARK_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN",         (1,0),(1,-1), "CENTER"),
    ]))
    story.append(pdt)

    story.append(PageBreak())

    # ── Section 4: Daily Activity & Knowledge Sources ────────────────────────────
    story.append(_section_header(
        "4.  Daily Activity and Knowledge Base Utilisation", W))
    story.append(Spacer(1, 0.2*cm))

    daily_img = Image(make_daily_activity(data["dates"]),
                      width=W*0.95, height=7*cm)
    story.append(daily_img)
    story.append(Paragraph("Figure 3: Daily question volume", caption_s))

    story.append(Paragraph("<b>Top Knowledge Sources Retrieved</b>", h2))
    story.append(Paragraph(
        "Documents most frequently retrieved from the 245-document "
        "knowledge base during user interactions.", body
    ))
    story.append(Spacer(1, 0.15*cm))

    sd = [[Paragraph("<b>#</b>", body),
           Paragraph("<b>Document</b>", body),
           Paragraph("<b>Uses</b>", body)]]
    for rank, (src, count) in enumerate(data["src_count"].most_common(12), 1):
        clean = (src.replace("_"," ").replace(".pdf","")
                    .replace(".txt","").title()[:58])
        sd.append([
            Paragraph(str(rank), body),
            Paragraph(clean, body),
            Paragraph(str(count), body),
        ])
    st_table = Table(sd, colWidths=[1*cm, W-3*cm, 2*cm])
    st_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,0), DARK_NAVY),
        ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_GRAY]),
        ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 5),
        ("BOTTOMPADDING", (0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("ALIGN",         (0,0),(0,-1), "CENTER"),
        ("ALIGN",         (2,0),(2,-1), "CENTER"),
    ]))
    story.append(st_table)

    story.append(PageBreak())

    # ── Section 5: Evaluation Results ───────────────────────────────────────────
    story.append(_section_header("5.  System Evaluation Results", W))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        "Structured evaluation using 30 test questions across 9 knowledge "
        "categories, scored on a five-point rubric assessing keyword coverage, "
        "relevance, depth, and Kenya institutional specificity.",
        body
    ))
    story.append(Spacer(1, 0.2*cm))

    avg_score = data.get("avg_score","4.70")
    accuracy  = data.get("accuracy","94.0")
    rate      = data.get("rate","97")
    excellent = data.get("excellent",22)
    good      = data.get("good",7)
    partial   = data.get("partial",1)
    weak      = data.get("weak",0)
    total_q   = data.get("total_q",30)

    eval_kpis = [
        (str(total_q),       "Questions"),
        (f"{avg_score}/5.0", "Mean Score"),
        (f"{accuracy}%",     "Accuracy"),
        (f"{rate}%",         "Good/Excellent"),
        (str(excellent),     "Perfect (5/5)"),
    ]
    ekr = [[Paragraph(v, kpi_val), Paragraph(l, kpi_lbl)]
           for v, l in eval_kpis]
    ekt = Table([ekr], colWidths=[W/5]*5)
    ekt.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), LIGHT_GREEN),
        ("BOX",           (0,0),(-1,-1), 1, DARK_GREEN),
        ("INNERGRID",     (0,0),(-1,-1), 0.5, MID_GRAY),
        ("TOPPADDING",    (0,0),(-1,-1), 10),
        ("BOTTOMPADDING", (0,0),(-1,-1), 10),
        ("ALIGN",         (0,0),(-1,-1), "CENTER"),
    ]))
    story.append(ekt)
    story.append(Spacer(1, 0.3*cm))

    s_img = Image(make_score_chart(excellent, good, partial, weak),
                  width=W*0.47, height=7*cm)

    if data.get("cat_scores"):
        c_img = Image(make_category_chart(data["cat_scores"]),
                      width=W*0.47, height=7*cm)
        ec = Table([[s_img, c_img]], colWidths=[W*0.5, W*0.5])
    else:
        ec = Table([[s_img]], colWidths=[W])

    ec.setStyle(TableStyle([
        ("ALIGN",  (0,0),(-1,-1), "CENTER"),
        ("VALIGN", (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(ec)
    story.append(Paragraph(
        "Figure 4: Score distribution (left)  ·  "
        "Category scores (right)", caption_s))

    if data.get("cat_scores"):
        story.append(Paragraph("<b>Category Results</b>", h2))
        cd = [[Paragraph("<b>Category</b>", body),
               Paragraph("<b>Questions</b>", body),
               Paragraph("<b>Mean Score</b>", body),
               Paragraph("<b>Rating</b>", body)]]
        for cat, sc in sorted(
            data["cat_scores"].items(),
            key=lambda x: -sum(x[1])/len(x[1])
        ):
            avg = sum(sc) / len(sc)
            rating = ("Excellent" if avg >= 4.5
                      else "Good" if avg >= 4.0 else "Partial")
            cd.append([
                Paragraph(cat, body),
                Paragraph(str(len(sc)), body),
                Paragraph(f"{avg:.2f}/5.0", body),
                Paragraph(rating, body),
            ])
        cdt = Table(cd, colWidths=[W*0.4, W*0.15, W*0.2, W*0.25])
        cdt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,0), DARK_NAVY),
            ("TEXTCOLOR",     (0,0),(-1,0), WHITE),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT_GRAY]),
            ("GRID",          (0,0),(-1,-1), 0.5, MID_GRAY),
            ("TOPPADDING",    (0,0),(-1,-1), 5),
            ("BOTTOMPADDING", (0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 8),
            ("ALIGN",         (1,0),(-1,-1), "CENTER"),
        ]))
        story.append(cdt)

    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Key Finding: The system achieved a mean score of "
        f"<b>{avg_score}/5.00 ({accuracy}%)</b> with <b>{rate}%</b> of "
        f"responses rated Good or Excellent, demonstrating the feasibility "
        f"of a localised RAG advisory system for Kenyan MSMEs.",
        finding
    ))

    story.append(PageBreak())

    # ── Section 6: Conclusions ───────────────────────────────────────────────────
    story.append(_section_header("6.  Conclusions and Recommendations", W))
    story.append(Spacer(1, 0.2*cm))

    for title, text in [
        ("System Performance",
         f"The Kenya MSME Advisor achieved {accuracy}% accuracy across "
         f"{total_q} structured evaluation questions, demonstrating "
         f"suitability for prototype deployment."),
        ("Knowledge Base",
         f"The 245-document knowledge base generated {total} responses "
         f"across {sessions} sessions. Key sources include government "
         f"institutional documents confirming knowledge base relevance."),
        ("Multilingual Support",
         f"{len(data['languages'])} language(s) detected. English and "
         f"Kiswahili received full support. Indigenous language expansion "
         f"is recommended as a priority for future development."),
        ("Deployment Recommendation",
         "Online deployment via Streamlit Cloud is recommended as the "
         "immediate next step, followed by WhatsApp Business API integration "
         "to reach rural MSME operators across Kenya's 47 counties."),
    ]:
        story.append(Paragraph(f"<b>{title}</b>", h2))
        story.append(Paragraph(text, body))

    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width=W, thickness=1,
                             color=MID_GRAY, spaceAfter=8))
    story.append(Paragraph(
        f"Kenya MSME Advisor · Research Analytics Report · "
        f"Generated {data.get('generated','')} · "
        f"Strathmore University MSIT Thesis 2026",
        caption_s
    ))

    doc.build(story)
    buf.seek(0)
    return buf.read()
