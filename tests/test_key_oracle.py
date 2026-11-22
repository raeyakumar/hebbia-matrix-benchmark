"""Oracle test: answering every cell exactly as the answer key does, quoting the key's own
value-bearing row from a retrieved excerpt, must score 100% verified for both methods.
Failures here mean a bug in the checker or an inconsistent key row -- not a model error.

Run: .venv/bin/python tests/test_key_oracle.py
"""
import csv
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import score  # noqa: E402
from config import TICKER_TO_NAME  # noqa: E402

TICKERS = ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]


def oracle_row(k, ev):
    t = k["ticker"]
    if k["expect_abstain"] == "yes":
        return {"company": TICKER_TO_NAME[t], "status": "insufficient_evidence", "answer": "n/a", "value": None,
                "unit": "", "period": "", "excerpt_id": "", "quote": ""}
    seg = k["supporting_passage"].split(" || ")[-1]
    cid = next(c["id"] for c in ev["companies"][t] if score.norm(seg) in score.norm(c["text"]))
    return {"company": TICKER_TO_NAME[t], "status": "answered", "answer": k["expected_answer"],
            "value": float(k["expected_value"]), "unit": k["unit"], "period": k["period"],
            "excerpt_id": cid, "quote": seg}


def run(qset_prefix=("F", "T")):
    key = [r for r in csv.DictReader(open(ROOT / "benchmark/answer_key.csv"))]
    tmp = Path(tempfile.mkdtemp())
    (tmp / "manifest.json").write_text(json.dumps({"model": "oracle", "tickers": TICKERS}))
    recs = []
    for qid in sorted({k["question_id"] for k in key}):
        ev = json.load(open(ROOT / f"benchmark/evidence/{qid}.json"))
        rows = {k["ticker"]: oracle_row(k, ev) for k in key if k["question_id"] == qid}
        recs.append({"method": "A", "question_id": qid, "tickers": TICKERS,
                     "parsed": {"rows": [rows[t] for t in TICKERS]}, "usage": {}, "error": None})
        for t in TICKERS:
            recs.append({"method": "B", "question_id": qid, "tickers": [t],
                         "parsed": {"rows": [rows[t]]}, "usage": {}, "error": None})
    (tmp / "calls.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    sys.argv = ["score.py", str(tmp), "--key", "benchmark/answer_key.csv"]
    with redirect_stdout(io.StringIO()):
        score.main()
    return list(csv.DictReader(open(tmp / "scored_rows.csv")))


def test_oracle():
    rows = run()
    # cells where the right answer cannot be machine-verified from one quote and is routed to human review
    expected_unclear = {("T1", "GOOGL")}
    for r in rows:
        if (r["question_id"], r["ticker"]) in expected_unclear:
            assert r["support"] == "unclear" and r["needs_human"] == "yes", r
    bad = [r for r in rows if r["verified"] != "True" and (r["question_id"], r["ticker"]) not in expected_unclear]
    for r in bad:
        print("NOT VERIFIED:", r["method"], r["question_id"], r["ticker"], r["correct"], r["quote_ok"],
              r["period_check"], r["support"], r["support_reasons"])
    assert not bad, f"{len(bad)} oracle rows not verified"
    print(f"oracle: {len(rows)} rows, all verified")


if __name__ == "__main__":
    test_oracle()


def test_adversary_wrong_column_and_pair_swap():
    """Same quote, wrong number: another column of the quoted row, or the matched-pair partner's value."""
    key = [r for r in csv.DictReader(open(ROOT / "benchmark/answer_key.csv"))]
    kmap = {(k["question_id"], k["ticker"]): k for k in key}
    tmp = Path(tempfile.mkdtemp())
    (tmp / "manifest.json").write_text(json.dumps({"model": "adversary", "tickers": TICKERS}))
    recs, targets = [], set()
    for qid in sorted({k["question_id"] for k in key}):
        ev = json.load(open(ROOT / f"benchmark/evidence/{qid}.json"))
        rows = {}
        for t in TICKERS:
            k = kmap[(qid, t)]
            r = oracle_row(k, ev)
            if k["expect_abstain"] == "no":
                if qid in ("F9", "F10"):  # swap with partner question's answer, keep own quote
                    p = kmap[("F10" if qid == "F9" else "F9", t)]
                    if float(p["expected_value"]) != float(k["expected_value"]):
                        r["value"], r["unit"] = float(p["expected_value"]), p["unit"]
                        targets.add((qid, t))
                else:
                    cells = [score.numbers_in(c) for c in r["quote"].split(" | ")[1:]]
                    vals = [c[0][0] for c in cells if c and not c[0][1] == "%"]
                    exp_cell = float(k["expected_value"])  # key values are in the key's own stated unit
                    others = [v for v in vals if abs(v - exp_cell) > 1e-6]
                    if " | " in r["quote"] and others:
                        r["value"] = others[0]
                        targets.add((qid, t))
            rows[t] = r
        for t in TICKERS:
            recs.append({"method": "B", "question_id": qid, "tickers": [t],
                         "parsed": {"rows": [rows[t]]}, "usage": {}, "error": None})
    (tmp / "calls.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    sys.argv = ["score.py", str(tmp), "--key", "benchmark/answer_key.csv"]
    with redirect_stdout(io.StringIO()):
        score.main()
    rows = [r for r in csv.DictReader(open(tmp / "scored_rows.csv")) if (r["question_id"], r["ticker"]) in targets]
    for r in rows:
        if r["correct"] != "False": print("   CORRECT?!", r["question_id"], r["ticker"], r["value"], r["unit"], r["expected_answer"])
    assert all(r["correct"] == "False" and r["verified"] == "False" for r in rows)
    sup = {s: sum(r["support"] == s for r in rows) for s in ("pass", "fail", "unclear")}
    print(f"adversary: {len(rows)} wrong-number rows, 0 verified; support check verdicts {sup}")
    for r in rows:
        if r["support"] == "pass":
            print("   support passed a wrong number:", r["question_id"], r["ticker"], r["value"], r["quote"][:80])


if __name__ == "__main__":
    test_adversary_wrong_column_and_pair_swap()
