"""Render paper/paper.md (the editable source) to paper/paper.pdf with ReportLab.

Supports the Markdown the paper uses: # title, ## and ### headings, paragraphs, '- ' items,
pipe tables with a preceding 'Table N.' caption, [links](url), **bold**, *italic* and `code`.
Lines between the title and the first heading form the byline.
Usage: .venv/bin/python paper/build_pdf.py
"""
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

HERE = Path(__file__).resolve().parent
SRC, OUT = HERE / "paper.md", HERE / "paper.pdf"
MARGIN = 1.0 * inch

BODY = ParagraphStyle("body", fontName="Times-Roman", fontSize=10.5, leading=13.8, spaceAfter=6.5,
                      allowWidows=0, allowOrphans=0)
TITLE = ParagraphStyle("title", parent=BODY, fontName="Times-Bold", fontSize=18, leading=23, alignment=1, spaceAfter=14)
BYLINE = ParagraphStyle("byline", parent=BODY, alignment=1, spaceAfter=3)
H2 = ParagraphStyle("h2", parent=BODY, fontName="Times-Bold", fontSize=12.5, leading=15.5, spaceBefore=12, spaceAfter=5,
                    keepWithNext=1)
H3 = ParagraphStyle("h3", parent=BODY, fontName="Times-Bold", fontSize=10.5, leading=13.8, spaceBefore=7, spaceAfter=3,
                    keepWithNext=1)
ITEM = ParagraphStyle("item", parent=BODY, leftIndent=16, spaceAfter=5)
REF = ParagraphStyle("ref", parent=BODY, leftIndent=20, firstLineIndent=-20)
CAPTION = ParagraphStyle("caption", parent=BODY, fontSize=9.5, leading=12, spaceBefore=4, spaceAfter=4)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=9.5, leading=11.8, spaceAfter=0)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="Times-Bold")


def inline(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" color="black">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)


def table(lines, width):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines]
    rows = [r for r in rows if not all(re.fullmatch(r":?-{2,}:?", c) for c in r)]
    data = [[Paragraph(inline(c), CELLB if i == 0 else CELL) for c in r] for i, r in enumerate(rows)]
    n = len(rows[0])
    shares = {7: [.295, .085, .235, .075, .095, .115, .10], 4: [.17, .26, .25, .32], 3: [.46, .22, .32]}[n]
    t = Table(data, colWidths=[width * s for s in shares], repeatRows=1)
    t.setStyle(TableStyle([
        ("LINEABOVE", (0, 0), (-1, 0), 0.8, colors.black),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.black),
        ("LINEBELOW", (0, -1), (-1, -1), 0.8, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
    ]))
    return t


def build():
    doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=0.8 * inch, bottomMargin=0.85 * inch, author="Raeya Kumar",
                            title="Right Quote, Wrong Answer? Testing AI on Financial Filings", invariant=1)
    width = letter[0] - 2 * MARGIN - 12  # SimpleDocTemplate frames pad 6pt on each side
    blocks = [b for b in re.split(r"\n\s*\n", SRC.read_text().strip())]
    story, section, caption = [], None, None
    for b in blocks:
        lines = b.split("\n")
        if b.startswith("# "):
            story += [Spacer(1, 14), Paragraph(inline(b[2:]).replace("? ", "?<br/>", 1), TITLE)]
        elif b.startswith("## "):
            if section is None:
                story.append(Spacer(1, 10))
            section = b[3:]
            story.append(Paragraph(inline(section), H2))
        elif b.startswith("### "):
            story.append(Paragraph(inline(b[4:]), H3))
        elif re.match(r"Table \d+\.", b):
            caption = Paragraph(inline(b), CAPTION)
        elif b.startswith("|"):
            story.append(KeepTogether([caption, table(lines, width), Spacer(1, 11)]))
        elif b.startswith("- "):
            story.append(KeepTogether([Paragraph(inline(l[2:]), ITEM) for l in lines]))
        else:
            style = BYLINE if section is None else REF if section == "References" else BODY
            story.append(Paragraph(inline(" ".join(lines)), style))

    def footer(canvas, d):
        canvas.setFont("Times-Roman", 10)
        canvas.drawCentredString(letter[0] / 2, 0.55 * inch, str(d.page))

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    build()
