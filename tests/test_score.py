"""Offline tests for the citation checker using hand-built model responses (no API calls).

Run: .venv/bin/python -m pytest tests  (or: .venv/bin/python tests/test_score.py)
"""
import csv
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import score  # noqa: E402

KEY = "benchmark/answer_key_practice.csv"


def row(company, value, unit, period, eid, quote, status="answered"):
    return {"company": company, "status": status, "answer": "x", "value": value, "unit": unit,
            "period": period, "excerpt_id": eid, "quote": quote}


CASES = {
    # (method, qid, tickers): rows  -> expectations checked below
    "good_table": row("Apple", 478834, "USD millions", "fiscal 2026", "AAPL-0109",
                      "Total net sales | 478,834 | 416,161 | 391,035"),
    "good_billions": row("Microsoft", 331.839, "USD billions", "fiscal year ended June 30, 2026", "MSFT-0142",
                         "Total revenue | 331,839 | 281,724 | 245,122"),
    "wrong_period": row("Apple", 416161, "USD millions", "fiscal 2025", "AAPL-0109",
                        "Total net sales | 478,834 | 416,161 | 391,035"),
    "fabricated_quote": row("Microsoft", 331839, "USD millions", "fiscal 2026", "MSFT-0142",
                            "Total revenue was $331,839 million in fiscal 2026"),
    "wrong_company_cite": row("Apple", 478834, "USD millions", "fiscal 2026", "MSFT-0142",
                              "Total revenue | 331,839 | 281,724 | 245,122"),
}


def run():
    tmp = Path(tempfile.mkdtemp())
    (tmp / "manifest.json").write_text(json.dumps({"model": "test", "tickers": ["AAPL", "MSFT"]}))
    recs = [
        {"method": "A", "question_id": "P1", "tickers": ["AAPL", "MSFT"],
         "parsed": {"rows": [CASES["good_table"], CASES["good_billions"]]}, "usage": {}, "error": None},
        {"method": "B", "question_id": "P1", "tickers": ["AAPL"],
         "parsed": {"rows": [CASES["wrong_period"]]}, "usage": {}, "error": None},
        {"method": "B", "question_id": "P1", "tickers": ["MSFT"],
         "parsed": {"rows": [CASES["fabricated_quote"]]}, "usage": {}, "error": None},
        {"method": "A", "question_id": "P2", "tickers": ["AAPL", "MSFT"],
         "parsed": {"rows": [
             row("Apple", 167000, "employees", "as of September 26, 2026", "AAPL-0018",
                 "As of September 26, 2026, the Company had approximately 167,000 full-time equivalent employees."),
             row("Microsoft", None, "", "", "", "", status="insufficient_evidence")]}, "usage": {}, "error": None},
        {"method": "B", "question_id": "P2", "tickers": ["AAPL"], "parsed": None, "usage": None,
         "error": "ServerError: 503 UNAVAILABLE"},
        {"method": "B", "question_id": "P2", "tickers": ["MSFT"],
         "parsed": {"rows": [row("Microsoft", 223000, "employees", "June 30, 2026", "MSFT-0022",
                                 "As of June 30, 2026, we employed approximately 223,000 people on a full-time basis")]},
         "usage": {}, "error": None},
    ]
    (tmp / "calls.jsonl").write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    sys.argv = ["score.py", str(tmp), "--key", KEY]
    score.main()
    return {(r["method"], r["question_id"], r["ticker"]): r for r in csv.DictReader(open(tmp / "scored_rows.csv"))}


def test_checker():
    r = run()
    a1 = r[("A", "P1", "AAPL")]
    assert a1["correct"] == "True" and a1["quote_ok"] == "True" and a1["support"] == "pass" and a1["verified"] == "True"
    a2 = r[("A", "P1", "MSFT")]  # value reported in billions, quote in millions -> still supported
    assert a2["correct"] == "True" and a2["support"] == "pass", a2
    b1 = r[("B", "P1", "AAPL")]  # real quote, wrong year's column -> quote passes, support & correctness fail
    assert b1["quote_ok"] == "True" and b1["correct"] == "False" and b1["support"] == "fail", b1
    b2 = r[("B", "P1", "MSFT")]  # right number, paraphrased "quote" -> correct but not verified
    assert b2["correct"] == "True" and b2["quote_ok"] == "False" and b2["verified"] == "False", b2
    a3 = r[("A", "P2", "MSFT")]  # abstained on answerable question -> wrong, not verified
    assert a3["abstained"] == "True" and a3["correct"] == "False"
    b3 = r[("B", "P2", "AAPL")]  # API error preserved as an error row
    assert b3["status"] == "error" and b3["verified"] == "False"
    b4 = r[("B", "P2", "MSFT")]
    assert b4["verified"] == "True" and b4["period_check"] == "ok", b4
    print("all checker tests passed")


if __name__ == "__main__":
    test_checker()
