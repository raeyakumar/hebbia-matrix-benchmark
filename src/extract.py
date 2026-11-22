"""Convert 10-K inline-XBRL HTML into plain text and stable excerpt chunks.

Design goals (from the study protocol):
  * keep financial-table structure: each <tr> becomes one line of ' | '-separated cells,
    with SEC's split "$" / ")" / "%" cells merged back onto their numbers;
  * keep table headings, unit lines ("(In millions)") and footnotes attached to the table
    they describe, so no excerpt contains a table without its units;
  * give every chunk a stable id (e.g. AAPL-0123) and its nearest section heading.

Outputs: data/text/<TICKER>.txt and data/chunks/<TICKER>.jsonl
"""
import json
import re
import sys
import unicodedata

from bs4 import BeautifulSoup, NavigableString, Tag

from config import CHUNKS, CHUNK_TARGET_CHARS, COMPANIES, RAW, TEXT

BLOCK = {"div", "p", "li", "h1", "h2", "h3", "h4", "h5", "h6", "table", "tr", "ul", "ol", "center"}
FOOTNOTE_RE = re.compile(r"^\s*(\(\w{1,2}\)|\*{1,3}|\[\d+\]|\d\))\s")
HEADING_RE = re.compile(r"^(Item\s+\d+[A-C]?\.|Note\s+\d+|NOTE\s+\d+|PART\s+[IV]+)", re.I)
PAGE_FOOTER_RE = re.compile(r"Form 10-K \| \d+$")
UNIT_RE = re.compile(r"\((in|dollars in|amounts in)\s+(millions|billions|thousands)", re.I)


def clean(s):
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("​", "").replace("\xa0", " ")
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-")
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


def text_of(el):
    # SEC HTML puts explicit spaces inside spans; joining with "" avoids "INC OME"-style splits.
    # <br> and block children inside a cell still need a separator.
    for br in el.find_all("br"):
        br.replace_with(" ")
    for blk in el.find_all(["div", "p", "li"]):  # stacked lines inside one table cell
        blk.insert_after(" ")
    return clean(el.get_text(""))


def render_table(tbl):
    lines = []
    for tr in tbl.find_all("tr"):
        cells = [text_of(td) for td in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c]
        merged = []
        for c in cells:
            if merged and (c in {")", "%", ")%", "%)"} or c.startswith(")")):
                merged[-1] += c
            elif merged and merged[-1] in {"$", "(", "$(", "€", "£"}:
                merged[-1] = (merged[-1] + c).replace("$ ", "$")
            else:
                merged.append(c)
        if merged:
            line = " | ".join(merged)
            if PAGE_FOOTER_RE.search(line):
                continue
            lines.append(line)
    return lines


def walk(el, out):
    """Emit ('p', text) and ('table', [rows]) blocks in document order."""
    for child in el.children:
        if isinstance(child, NavigableString):
            continue
        if not isinstance(child, Tag):
            continue
        name = child.name.lower() if child.name else ""
        if name in {"script", "style", "head"}:
            continue
        if name == "ix:header" or (child.get("style") and "display:none" in child.get("style").replace(" ", "")):
            continue
        if name == "table":
            rows = render_table(child)
            if rows:
                # single-cell "tables" are usually layout boxes around a paragraph
                if all(" | " not in r for r in rows) and len(rows) <= 2:
                    for r in rows:
                        out.append(("p", r))
                else:
                    out.append(("table", rows))
            continue
        if any(isinstance(c, Tag) and c.name and c.name.lower() in BLOCK for c in child.find_all(recursive=False)) \
                or child.find("table") is not None:
            walk(child, out)
        else:
            t = text_of(child)
            if t and not PAGE_FOOTER_RE.search(t):
                out.append(("p", t))


def group_blocks(blocks):
    """Attach short lead-in lines (titles, unit lines) and trailing footnotes to tables."""
    groups, i = [], 0
    pending = []  # short paragraphs that might be a table's lead-in
    while i < len(blocks):
        kind, val = blocks[i]
        if kind == "p":
            if len(val) < 160:
                pending.append(val)
                if len(pending) > 3:
                    groups.append(("p", [pending.pop(0)]))
            else:
                groups.extend(("p", [p]) for p in pending)
                pending = []
                groups.append(("p", [val]))
            i += 1
            continue
        # table: absorb lead-ins and following footnotes
        lines = pending + val
        pending = []
        i += 1
        while i < len(blocks) and blocks[i][0] == "p" and (FOOTNOTE_RE.match(blocks[i][1]) or UNIT_RE.search(blocks[i][1])):
            lines.append(blocks[i][1])
            i += 1
        groups.append(("table", lines))
    groups.extend(("p", [p]) for p in pending)
    return groups


def chunk(groups, ticker):
    chunks, cur, cur_len, heading, cur_heading = [], [], 0, "", ""

    def flush():
        nonlocal cur, cur_len
        if cur:
            chunks.append({"id": f"{ticker}-{len(chunks):04d}", "ticker": ticker,
                           "heading": cur_heading, "text": "\n".join(cur)})
        cur, cur_len = [], 0

    for kind, lines in groups:
        # a section heading can be a paragraph of its own or a lead-in line absorbed by a table
        for l in lines[:4] if kind == "table" else lines[:1]:
            if " | " in l:
                break
            m = HEADING_RE.match(l)
            if m:
                h = l if len(l) < 160 else re.split(r"(?<=[A-Z]{3}) (?=[A-Z][a-z])", l)[0][:160]
                if h != heading:
                    flush()
                    heading = h
        size = sum(len(l) + 1 for l in lines)
        if kind == "table" and size > CHUNK_TARGET_CHARS * 2.5:
            # split very large tables, repeating the first 3 lines (title/units/column header)
            flush()
            # repeat title / unit line / column-header lines on every part: everything up to and
            # including the first line that carries >= 2 years (the column header), max 6 lines
            hn = next((i + 1 for i, l in enumerate(lines[:6]) if len(re.findall(r"20\d\d", l)) >= 2), 3)
            head = lines[:hn]
            body = lines[hn:]
            part = list(head)
            for l in body:
                if sum(len(x) + 1 for x in part) + len(l) > CHUNK_TARGET_CHARS * 2:
                    cur_heading = heading
                    cur = part
                    flush()
                    part = list(head) + ["(table continued)"]
                part.append(l)
            cur_heading, cur = heading, part
            flush()
            continue
        if cur_len + size > CHUNK_TARGET_CHARS and cur:
            flush()
        if not cur:
            cur_heading = heading
        cur.extend(lines)
        cur_len += size
    flush()
    return chunks


def extract(ticker):
    html = (RAW / f"{ticker}.htm").read_bytes()
    soup = BeautifulSoup(html, "lxml")
    blocks = []
    walk(soup.body or soup, blocks)
    groups = group_blocks(blocks)
    TEXT.mkdir(parents=True, exist_ok=True)
    CHUNKS.mkdir(parents=True, exist_ok=True)
    with (TEXT / f"{ticker}.txt").open("w") as fh:
        for kind, lines in groups:
            fh.write("\n".join(lines) + "\n\n")
    chunks = chunk(groups, ticker)
    with (CHUNKS / f"{ticker}.jsonl").open("w") as fh:
        for c in chunks:
            fh.write(json.dumps(c) + "\n")
    print(f"{ticker}: {len(blocks)} blocks -> {len(chunks)} chunks, "
          f"{sum(len(c['text']) for c in chunks):,} chars")


if __name__ == "__main__":
    for t in (sys.argv[1:] or [t for t, _ in COMPANIES.values()]):
        extract(t)
