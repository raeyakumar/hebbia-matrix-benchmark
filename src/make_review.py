"""Render benchmark/ANSWER_KEY_REVIEW.md from benchmark/answer_key.csv (so the two never drift).

Order: matched-pair example first, then every row whose notes ask for a decision or flag an
ambiguity, then the full key question by question.
"""
import csv
import json

from config import BENCH

PAIR_SHOWCASE = "META"


def md_escape(s):
    return (s or "").replace("|", "\\|").replace("\n", " ")


def main():
    key = list(csv.DictReader((BENCH / "answer_key.csv").open()))
    qs = {q["id"]: q for q in json.load((BENCH / "questions.json").open())}
    by = {(r["question_id"], r["ticker"]): r for r in key}
    out = ["# Answer key review", "",
           "Generated from `benchmark/answer_key.csv` by `src/make_review.py`. Edit the CSV (or the spec in "
           "`src/build_answer_key.py`), not this file. The key is read only by the scorer; it never enters a prompt.",
           "", "Every `supporting_passage` has been machine-checked to appear verbatim in the extracted 10-K text, and "
           "for every answerable cell the passage is inside the evidence the models receive (evidence recall 72/72).",
           "", "## 1. Matched pair (F9 / F10): two facts, one passage", ""]
    f9, f10 = by[("F9", PAIR_SHOWCASE)], by[("F10", PAIR_SHOWCASE)]
    out += [f"**F9.** {qs['F9']['question']}", "", f"**F10.** {qs['F10']['question']}", "",
            "Both questions use the same retrieval query, so each method sees *identical* excerpts for F9 and F10; "
            "only the requested fact differs.", "",
            f"Meta's filing ({f9['source_url']}), Item 7 (MD&A, excerpt META-0229). Both this passage and the "
            "Note 12 version, which adds the prior-year $51.28 billion remaining, are in the evidence:", "",
            "> " + f9["supporting_passage"] + " " + f10["supporting_passage"], "",
            "| | Expected | Wrong-but-plausible answer in the same passage |", "|---|---|---|",
            f"| F9 repurchased in 2025 | **{f9['expected_answer']}** | $25.03 billion (the remaining amount) |",
            f"| F10 remaining at 12/31/2025 | **{f10['expected_answer']}** | $26.26 billion (the repurchased amount); "
            "$51.28 billion (prior-year remaining, in the Note version) |", "",
            "The pair for the other four companies:", "", "| Company | F9 repurchased | F10 remaining |",
            "|---|---|---|"]
    for t in ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]:
        out.append(f"| {by[('F9', t)]['company']} | {md_escape(by[('F9', t)]['expected_answer'])} | "
                   f"{md_escape(by[('F10', t)]['expected_answer'])} |")
    flagged = [r for r in key if any(w in r["ambiguity_notes"] for w in ("NEEDS YOUR DECISION", "AMBIGUOUS", "DECIDED"))]
    out += ["", "## 2. Cells that need your judgment", "",
            "`DECIDED` = settled by the reviewer (2026-11-22). `AMBIGUOUS` = my call, not separately reviewed. "
            "`NEEDS YOUR DECISION` = open.",
            "", "| Q | Company | Draft expected answer | Also accepted | Note |", "|---|---|---|---|---|"]
    for r in sorted(flagged, key=lambda r: ("NEEDS" not in r["ambiguity_notes"], "DECIDED" not in r["ambiguity_notes"], r["question_id"])):
        out.append(f"| {r['question_id']} | {r['company']} | {md_escape(r['expected_answer'])} | "
                   f"{md_escape(r['accepted_alternates']) or '-'} | {md_escape(r['ambiguity_notes'])} |")
    out += ["", "## 3. Scoring rules (to be frozen with the key)", "",
            "- **Correct**: claimed value converted to base units (using the model's own `unit`) is within the "
            "row's relative tolerance (0.1%; 0.01% for per-share amounts) of the expected value or an accepted "
            "alternate. Signs are ignored (magnitudes compared): no expected answer is negative, and the filings show "
            "outflows such as capex in parentheses.",
            "- **Abstention**: `status = insufficient_evidence` (or a null value). Correct only where the key says "
            "`expect_abstain = yes` (T5 for Apple, Microsoft and Meta). Abstaining on an answerable cell counts as "
            "wrong, reported separately from wrong numbers. A correct abstention counts as verified, since there "
            "is no claim to cite.",
            "- **Quote check**: quote appears verbatim (case/whitespace-normalized) in the cited excerpt. Passing it "
            "means only that the text exists.",
            "- **Support check** (separate): the cited excerpt belongs to the row's company; the claimed value at the "
            "claimed unit appears in the quote at the excerpt's stated scale; the period matches (table column mapped "
            "to its year header, or the year stated in a prose quote). Undecidable cases are `unclear` and are listed "
            "for human review instead of being silently passed.",
            "- **Verified** = correct AND quote check AND support check.", "",
            "## 4. Full key", ""]
    for qid in [q for q in qs if qs[q]["set"] == "final"]:
        q = qs[qid]
        tag = f" *(tricky: {q.get('tricky_type')})*" if q.get("tricky") else ""
        out += [f"### {qid}{tag}", "", q["question"], "",
                "| Company | Expected | Unit | Period | Supporting passage / table cells | Note |",
                "|---|---|---|---|---|---|"]
        for t in ["AAPL", "MSFT", "GOOGL", "META", "AMZN"]:
            r = by[(qid, t)]
            src = f"[{r['company']} 10-K]({r['source_url']})"
            out.append(f"| {src} | {md_escape(r['expected_answer'])} | {r['unit'] or '-'} | {r['period'] or '-'} | "
                       f"{md_escape(r['supporting_passage']) or '-'} | {md_escape(r['ambiguity_notes']) or ''} |")
        out.append("")
    (BENCH / "ANSWER_KEY_REVIEW.md").write_text("\n".join(out))
    print(f"wrote ANSWER_KEY_REVIEW.md ({len(flagged)} flagged rows)")


if __name__ == "__main__":
    main()
