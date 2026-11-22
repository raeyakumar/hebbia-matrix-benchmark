"""Render paper/paper.md (the editable source) to paper/paper.pdf with ReportLab.

Supports the subset of Markdown the paper uses: # title, ## headings, paragraphs, '* ' bullets,
pipe tables, **bold**, *italic* and `code`.
Usage: .venv/bin/python paper/build_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
SRC, OUT = HERE / "paper.md", HERE / "paper.pdf"

ss = getSampleStyleSheet()
BODY = ParagraphStyle("body", parent=ss["Normal"], fontName="Times-Roman", fontSize=10, leading=12.6,
                      alignment=TA_JUSTIFY, spaceAfter=5)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Times-Bold", fontSize=16, leading=19, alignment=1, spaceAfter=4)
SUB = ParagraphStyle("sub", parent=BODY, fontName="Times-Italic", fontSize=9.5, alignment=1, spaceAfter=8)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Times-Bold", fontSize=11.5, leading=14, spaceBefore=7, spaceAfter=3,
                    alignment=0)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=8.6, leading=10.2, alignment=0, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Times-Bold")


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font name="Courier" size="8.6">\1</font>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)
    return t


def table(lines, width):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    data = [[Paragraph(inline(c), CELLB if i == 0 else CELL) for c in r] for i, r in enumerate(rows)]
    n = len(rows[0])
    first = 0.30 if n > 3 else 0.34
    colw = [width * first] + [width * (1 - first) / (n - 1)] * (n - 1)
    t = Table(data, colWidths=colw, repeatRows=1, hAlign="CENTER")
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 1.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                            title="Right Quote, Wrong Answer? Testing AI on Financial Filings")
    width = letter[0] - 1.7 * inch
    lines = SRC.read_text().split("\n")
    story, i, para, title_done = [], 0, [], False

    def flush():
        nonlocal para
        if para:
            story.append(Paragraph(inline(" ".join(para)), BODY))
            para = []

    while i < len(lines):
        l = lines[i]
        if l.startswith("# "):
            flush(); story.append(Paragraph(inline(l[2:]), TITLE)); title_done = True
        elif l.startswith("## "):
            flush(); story.append(Paragraph(inline(l[3:]), H2))
        elif l.startswith("|"):
            flush()
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i]); i += 1
            story += [Spacer(1, 2), table(block, width), Spacer(1, 6)]
            continue
        elif l.startswith("* "):
            flush()
            items = []
            while i < len(lines) and lines[i].startswith("* "):
                items.append(ListItem(Paragraph(inline(lines[i][2:]), BODY), leftIndent=12)); i += 1
            story.append(ListFlowable(items, bulletType="bullet", start="•", leftIndent=12, bulletFontSize=8))
            continue
        elif not l.strip():
            flush()
        elif title_done and l.startswith("*") and l.endswith("*") and not story[1:]:
            story.append(Paragraph(inline(l.strip("*")), SUB))
        else:
            para.append(l.strip())
        i += 1
    flush()

    def footer(canvas, d):
        canvas.setFont("Times-Roman", 8.5)
        canvas.drawCentredString(letter[0] / 2, 0.45 * inch, str(d.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
