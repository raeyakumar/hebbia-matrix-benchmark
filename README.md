# Right Quote, Wrong Answer? Testing AI on Financial Filings

> **Status: complete (final run 2026-11-22).** Every number below comes from saved output in `results/`.
> Paper: [`paper/paper.pdf`](paper/paper.pdf) (source: [`paper/paper.md`](paper/paper.md)).

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

## Results

The final run made 90 calls on `gemini-3.8-flash` (15 for A, 75 for B), with 0 errors. 75 paired company × question cells:

| Scoring tier | A verified | B verified | Both | Only A | Only B | Neither |
|---|---|---|---|---|---|---|
| 1. Frozen automatic scorer | 70 | 69 | 69 | 1 | 0 | 5 |
| 2. + support verdicts re-read from excerpts* | 73 | 73 | 73 | 0 | 0 | 2 |
| 3. + one answer-key rounding fix* | 74 | 74 | 74 | 0 | 0 | 1 |

\*Tiers 2 and 3 are post-run re-readings by the AI assistant that ran the study. Each is recorded with its reason in
[`results/final/adjudication.csv`](results/final/adjudication.csv) and is **flagged for human confirmation**.

- **Same answers.** The two methods gave the same number in all 75 cells. The only differences were capex sign
  conventions and number formatting. Neither method made a numerically wrong claim.
- **Trick questions, reported separately.** Both methods were correct on 25/25 trap cells and verified on 23/25
  (tier 1). They read Meta's U.S.-only revenue from a footnote, Apple's share count in thousands and prior-year
  columns correctly, and abstained correctly where no credit facility exists.
- **Abstentions.** 4 per method: 3 correct (T5) and 1 wrong (Alphabet F2, caused by our own question wording; see
  the paper). Abstaining on an answerable cell counts as wrong.
- **Cost.** Estimated from API token counts × list price: A $0.185, B $0.198 (+6.9%). A used 12,720 prompt tokens
  per call; B used 2,823 per call, five calls per question.
- **Cost per additional verified answer: not computed.** B never produced an additional verified answer. Under
  tier 1, A has one more and is also cheaper; under tiers 2 and 3 the methods tie.
- **What failed was the checker.** The 9 cells that the automatic support check failed or marked unclear were all
  supported on reading, because of mixed-column table headers and one unit phrasing the checker missed.

**Bottom line:** at five companies and about 12.7k prompt tokens per call, answering one company at a time bought
nothing. Batching was about 7% cheaper.

## Matched-pair example (real output)

F9 asks how much stock was repurchased during the year; F10 asks how much authorization remains. Both questions
receive identical evidence. Meta's 10-K (excerpt `META-0229`) puts both numbers in adjacent sentences, so a real
quote could support either one. Both methods separated them correctly:

| | Method A | Method B |
|---|---|---|
| F9 repurchased in 2025 | **$26.26 billion**, quoting "In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate amount of $26.26 billion." | same value, same excerpt, same quote |
| F10 remaining at 12/31/2025 | **$25.03 billion**, quoting "As of December 31, 2025, $25.03 billion remained available and authorized for repurchases." | same value, same excerpt, same quote |

All four cells passed the correctness, quote and support checks (`results/results_final.csv`).

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
  results_final.csv    every cell, A and B side by side, all scoring tiers
  final/adjudication.csv  post-run re-readings with reasons (flagged for human confirmation)
paper/                 paper.md (editable source), paper.pdf, build_pdf.py
drafts/                outreach email draft (local only, not sent)
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

Paid runs use `gemini-3.8-flash`, thinking level `low`, temperature 0, called over the REST API. Runs refuse to start without a spend cap. The pilot cost an estimated $0.018 (6 calls). The final run cost an estimated $0.383 (90 calls):

```bash
cd src && ../.venv/bin/python run_benchmark.py --set practice --tickers AAPL,MSFT --out results/pilot --max-usd 0.10 && ../.venv/bin/python score.py results/pilot --key benchmark/answer_key_practice.csv
```

```bash
cd src && ../.venv/bin/python freeze.py --check && ../.venv/bin/python run_benchmark.py --set final --out results/final --max-usd 0.60 && ../.venv/bin/python score.py results/final && ../.venv/bin/python adjudicate.py results/final
```

```bash
.venv/bin/python paper/build_pdf.py
```

A run resumes from `calls.jsonl`. Failed calls stay in the log as error records, and the scorer counts them as wrong.

## Known limitations

- Five companies × 15 questions = 75 paired units, too few for strong statistical claims. The paired table and
  exact counts will be reported, not just percentages.
- Temperature is 0, but Gemini outputs are not guaranteed to be deterministic. Each condition runs once.
- The support check is automated. Cells it cannot decide are marked `unclear` and listed for human review, not
  passed silently.
- Answer-key judgment calls are listed in `benchmark/ANSWER_KEY_REVIEW.md` §2. Two key defects were found after the run
  (a rounded Microsoft value and an over-specified Alphabet F2 question); both are disclosed in the paper.
- Human verification time was not measured and is not reported.
