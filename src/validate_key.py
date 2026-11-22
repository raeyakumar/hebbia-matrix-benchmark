"""Validate an answer-key CSV against the filings and the frozen evidence.

For every row:
  * each segment of `supporting_passage` (segments separated by ' || ') must appear verbatim
    in that company's extracted 10-K text -> otherwise the row is reported as an error;
  * fills `source_chunk_ids` (chunks containing the last segment, i.e. the value-bearing one),
    `in_selected_evidence` (whether any of those chunks was retrieved for the question),
    and the filing provenance columns (source_url, filing_date, fiscal_year_end).
The key is only ever read by this script and score.py -- never by prompt construction.

Usage: python validate_key.py benchmark/answer_key.csv
"""
import csv
import json
import sys

from config import BENCH, CHUNKS, DATA, ROOT
from score import norm

COLS = ["question_id", "ticker", "company", "question", "expected_answer", "expected_value", "unit",
        "period", "period_year", "expect_abstain", "tolerance_rel", "accepted_alternates",
        "supporting_passage", "source_chunk_ids", "in_selected_evidence", "source_url", "filing_date",
        "fiscal_year_end", "tricky_type", "ambiguity_notes"]


def main(path):
    path = ROOT / path
    filings = {r["ticker"]: r for r in csv.DictReader((DATA / "filings.csv").open())}
    qs = {q["id"]: q for q in json.load((BENCH / "questions.json").open())}
    chunks = {t: [json.loads(l) for l in (CHUNKS / f"{t}.jsonl").open()] for t in filings}
    rows = list(csv.DictReader(path.open()))
    problems = 0
    for r in rows:
        t = r["ticker"]
        f = filings[t]
        r["company"] = f["company"]
        r["question"] = qs[r["question_id"]]["question"]
        r["source_url"], r["filing_date"], r["fiscal_year_end"] = f["url"], f["filing_date"], f["fiscal_year_end"]
        segs = [s for s in r["supporting_passage"].split(" || ") if s.strip()]
        text = norm(open(DATA / "text" / f"{t}.txt").read())
        missing = [s for s in segs if norm(s) not in text]
        if missing:
            problems += 1
            print(f"!! {r['question_id']} {t}: passage segment not found verbatim: {missing[0][:90]!r}")
        if segs:
            ids = [c["id"] for c in chunks[t] if norm(segs[-1]) in norm(c["text"])]
            r["source_chunk_ids"] = ";".join(ids)
            ev_path = BENCH / "evidence" / f"{r['question_id']}.json"
            if ev_path.exists():
                sel = {c["id"] for c in json.load(ev_path.open())["companies"].get(t, [])}
                r["in_selected_evidence"] = "yes" if sel & set(ids) else "NO"
        else:
            r["source_chunk_ids"] = ""
            r["in_selected_evidence"] = "n/a"
    with path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    recall = [r["in_selected_evidence"] for r in rows if r["in_selected_evidence"] in ("yes", "NO")]
    print(f"{len(rows)} rows, {problems} passage problems, evidence recall "
          f"{recall.count('yes')}/{len(recall)}")
    for r in rows:
        if r["in_selected_evidence"] == "NO":
            print(f"   not retrieved: {r['question_id']} {r['ticker']} (key chunk {r['source_chunk_ids']})")
    return problems


if __name__ == "__main__":
    sys.exit(1 if main(sys.argv[1]) else 0)
