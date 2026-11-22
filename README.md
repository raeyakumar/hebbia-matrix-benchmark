# Right Quote, Wrong Answer? Testing AI on Financial Filings

> **Status: pre-registration.** The pipeline, filings, evidence, prompts and draft answer key are built and
> tested offline. No model output exists yet, so this README reports **no findings**. Results sections will be
> filled only from saved outputs in `results/`.

**Research question.** When the same model receives the same evidence, does answering *one company at a time*
raise the share of financial claims that are correct **and** supported by their citations? And what does each
additional verified answer cost?

This is an independent experiment inspired by the public description of Hebbia's Matrix workflow (one row per
document, one cell per question). It is not affiliated with or endorsed by Hebbia.

## Design in one paragraph

Five FY2025/26 Form 10-Ks (Apple, Microsoft, Alphabet, Meta, Amazon) are pulled from SEC EDGAR and converted to
text that keeps table titles, unit lines, column years and footnotes. For each question, BM25 selects 5 excerpts per
company **once**, and those excerpts are frozen to `benchmark/evidence/<qid>.json`. **Method A** sends every company's
excerpts in one call and asks for one row per company. **Method B** sends each company's identical excerpts in its own
call, then the rows are combined. Both methods use the same model, settings, system instruction, JSON schema,
company names and checker. Each answer is scored on three separate checks: *correct* (matches the answer key),
*quote check* (quote is verbatim in the cited excerpt) and *support check* (the quote actually backs the claimed
value for the right company, period and unit). An answer counts as **verified** only if all three pass.

## The matched pair (F9 / F10)

Two questions ask for two different numbers that sit in the **same passage**, and both are given identical evidence.
From Meta's 10-K (Item 7):

> In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate
> amount of $26.26 billion. As of December 31, 2025, $25.03 billion remained available and authorized for repurchases.

F9 (repurchased) = **$26.26B**; F10 (remaining) = **$25.03B**. A correct verbatim quote supports one of them and not
the other, so the quote check alone cannot tell a right answer from a swapped one. *Model results for this pair:
pending the frozen run.*

## Repository layout

```
src/
  config.py            paths, companies, model settings, prices (everything frozen with the run)
  fetch_filings.py     EDGAR download + data/filings.csv (URL, filing date, fiscal year end, SHA-256)
  extract.py           HTML -> text with tables as "cell | cell" rows, units/footnotes kept with tables -> chunks
  select_evidence.py   BM25 evidence selection, once per question -> benchmark/evidence/
  prompts.py           the single shared instruction + JSON schema
  run_benchmark.py     Method A / Method B runner; logs raw output, tokens, latency, errors
  score.py             normalization, quote check, support check, paired tables, cost per verified answer
  build_answer_key.py  hand-written answer-key spec -> benchmark/answer_key.csv
  validate_key.py      verifies every key passage is verbatim in the filing and inside the evidence
  make_review.py       renders benchmark/ANSWER_KEY_REVIEW.md
  check_setup.py       confirms the API key is set (never prints it) and lists models
  estimate_cost.py     cost estimate from dry-run prompts
benchmark/
  questions.json       2 practice + 15 final questions (5 tricky, 1 matched pair)
  answer_key.csv       expected answers, passages, units, periods, sources, ambiguity notes
  answer_key_practice.csv
  ANSWER_KEY_REVIEW.md human-readable review of the key
  evidence/            frozen excerpts per question
data/
  filings.csv          provenance for each 10-K
  text/, chunks/       extracted text and excerpt units (raw HTML is git-ignored and re-downloadable)
tests/                 offline checker tests (no API calls)
results/               one folder per run: manifest, calls.jsonl (raw), scored_rows.csv, summary.json
```

## Reproduce

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt
```

```bash
cp .env.example .env    # then paste your key after GEMINI_API_KEY= ; .env is git-ignored
```

```bash
cd src && ../.venv/bin/python check_setup.py
```

Rebuild data and evidence (deterministic; SHA-256 of each filing is checked against `data/filings.csv`):

```bash
cd src && ../.venv/bin/python fetch_filings.py && ../.venv/bin/python extract.py && ../.venv/bin/python select_evidence.py practice AAPL,MSFT && ../.venv/bin/python select_evidence.py final
```

```bash
cd src && ../.venv/bin/python build_answer_key.py && ../.venv/bin/python validate_key.py benchmark/answer_key.csv
```

Offline tests (checker cases, oracle = 100% verified, wrong-column adversary = 0% verified):

```bash
.venv/bin/python tests/test_score.py && .venv/bin/python tests/test_key_oracle.py
```

Paid runs use `gemini-3.8-flash`, thinking level `low`, temperature 0, called over the REST API. Runs refuse to start without a spend cap. The pilot cost an estimated $0.018 (6 calls). The final run is estimated at $0.43 (90 calls):

```bash
cd src && ../.venv/bin/python run_benchmark.py --set practice --tickers AAPL,MSFT --out results/pilot --max-usd 0.10 && ../.venv/bin/python score.py results/pilot --key benchmark/answer_key_practice.csv
```

```bash
cd src && ../.venv/bin/python run_benchmark.py --set final --out results/final --max-usd 0.60 && ../.venv/bin/python score.py results/final
```

A run resumes from `calls.jsonl`. Failed calls stay in the log as error records, and the scorer counts them as wrong.

## Known limitations (stated in advance)

- Five companies × 15 questions = 75 paired units, too few for strong statistical claims. The paired table and
  exact counts will be reported, not just percentages.
- Temperature is 0, but Gemini outputs are not guaranteed to be deterministic. Each condition runs once.
- The support check is automated. Cells it cannot decide are marked `unclear` and listed for human review, not
  passed silently.
- Answer-key judgment calls are listed in `benchmark/ANSWER_KEY_REVIEW.md` §2.
