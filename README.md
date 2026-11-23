# The Answer Is in the Footnote: Testing AI Answers Against Financial Filings

**Raeya Kumar** · Smeal College of Business, Pennsylvania State University · [Paper (PDF, 5 pages)](paper/paper.pdf) · [source](paper/paper.md)

**The question I wanted to answer.** I wanted to know whether an AI model answers questions about financial
filings more reliably when it looks at one company at a time instead of several companies at once. Hebbia's Matrix
organizes this kind of work as a grid, with one row per document and one column per question, which made me curious
whether filling that grid one row at a time actually makes the answers more trustworthy.

**Why I expected one company at a time to help.** When the model reads passages from five 10-Ks in a single
request, it could mix up which passage belongs to which company, or take a number from the wrong year's column.
Giving it only one company's passages at a time seemed like it should remove that confusion.

**How the test worked.** The model never reads a whole 10-K. For each question, a search step pulls the five most
relevant passages from each company's filing, and the model has to answer using only those passages and copy the
exact sentence or table row its number came from. Both setups received the same passages, the same instructions and
the same model (Gemini 3.8 Flash), so the only difference was whether the companies were asked about together or
separately. An answer only counted as **verified** if the number was right, the quote really appeared in the
passage, and the quote actually supported that number for the right company, year and unit.

**What actually happened.** The company-by-company setup did not help. The two setups agreed on all 75
company-question pairs: 71 numerical answers matched, ignoring sign, and both declined to answer the other four. Under the scoring rules I locked in before the run,
asking about all five companies at once verified 70 of 75 outcomes, and asking one at a time verified 69 (each
total includes three correct decisions not to answer) while
costing about 7% more. What was harder than getting the right number was checking the citation: most of the misses
came from the automatic citation checker, not from the model.

> **An independent project inspired by Hebbia.**
> 
> It builds on Hebbia's public description of its Matrix workflow (one row per document, one cell per question). It is not affiliated with, sponsored by or endorsed by Hebbia, and it uses no Hebbia software or data. All filings are public SEC documents.

**Status: complete (final run 2026-11-22).** Every number below comes from saved output in `results/`. The
benchmark was frozen in commit `bdebd2a` before the experiment ran.

## Methods

Five FY2025/26 Form 10-Ks (Apple, Microsoft, Alphabet, Meta, Amazon) are downloaded from SEC EDGAR and converted to
text that keeps table titles, unit lines, column years and footnotes. For each question, a keyword search (BM25)
selects 5 passages per company **once**, and those passages are frozen to `benchmark/evidence/<qid>.json`.
**Method A** sends every company's passages in one request and asks for one row per company. **Method B** sends each
company's identical passages in its own request, and the rows are then combined. Both methods use the same model,
settings, instructions, output format, company names and checker. Each answer gets three separate checks: *correct*
(matches the answer key), *quote check* (the quote appears word for word in the cited passage) and *support check*
(the quote actually backs the claimed number for the right company, period and unit). An answer counts as
**verified** only if all three pass. The follow-up review of the 9 citations the automatic checker could not confirm
was manual: I compared each cited passage with the original SEC filing. Claude Code had done an AI-assisted review
earlier and I had seen its overall results, so mine was not a blind review. The two sets of verdicts match.

## Results

The final test ran once, with 90 requests to `gemini-3.8-flash` (15 for the all-at-once setup, Method A, and 75
for the one-at-a-time setup, Method B), and none of them failed. Each row below counts how many of the 75
company-question pairs were verified.

| Scoring tier | A verified | B verified | Both | Only A | Only B | Neither |
|---|---|---|---|---|---|---|
| 1. Original scoring | 70 | 69 | 69 | 1 | 0 | 5 |
| 2. After manual citation review | 72 | 72 | 72 | 0 | 0 | 3 |
| 3. After manual citation review and answer-key correction | 73 | 73 | 73 | 0 | 0 | 2 |

**The first row is the main result.** It comes from the scoring rules I locked in before the run, so nothing in it
was adjusted after the answers came in. \*The second and third rows are later, secondary checks. For the second row, the
manual review described in Methods found 7 of the 9 flagged citations supported and 2 inconclusive
(Alphabet T1, in both setups), and inconclusive cells are not counted as verified. The third row also corrects one rounding mistake in the
answer key. My verdicts and reasons are in
[`results/final/manual_review.csv`](results/final/manual_review.csv). 

- **Same answers.** The setups agreed in all 75 cells: 71 numerical answers had the same magnitude, and both declined
  the other four. In two of the 71, the one-at-a-time setup wrote capital spending as a negative number, which the
  scoring rules treat as equivalent. Units and number formats sometimes differed in wording. The only numerical
  answer scored incorrect was Microsoft's F9, where both gave the exact $16,719 million and the key was rounded.
- **Trick questions, reported separately.** The five trick questions were designed to catch specific mistakes, so I
  report them on their own. Both setups answered all 25 trick cells correctly and verified 23 of 25 under the main
  scoring. For example, both read Meta's U.S.-only revenue ($74.78B) from a footnote instead of the "United States
  and Canada" row, read Apple's share count in thousands, picked the prior-year column when the question asked for
  fiscal 2025, and correctly said there was not enough evidence when a company has no credit facility.
- **Abstentions.** An "insufficient evidence" answer counted as correct only if the answer key expected
  it, and as wrong otherwise. Each setup abstained 4 times: 3 were correct (T5) and 1 was wrong
  (Alphabet F2). That one was caused by the question's wording, not by the model (see the paper).
- **Cost.** Based on API token counts and Google's list prices, the all-at-once setup cost an estimated $0.185 and
  the one-at-a-time setup cost $0.198, about 6.9% more. The difference comes from repeating the instructions: A used
  about 12,720 prompt tokens per request, while B used about 2,823 per request but needed five requests per question.
- **Cost per additional verified answer: not calculated.** This number only makes sense when the more expensive
  setup produces extra verified answers, and it never did. Under the main scoring, the cheaper all-at-once setup has
  the one extra verified answer, and under the secondary checks the two setups tie.
- **Mostly the checker failed, not the model.** Of the 9 cells the automatic checker failed or marked unclear, 7
  turned out to be supported. The checker missed them because of tables that mix year columns with "$ Change |
  % Change" columns, and because of one unit phrase it did not recognize. The other 2 (Alphabet T1) have the right
  number, but the table they cite states its unit only in a neighboring passage.

Overall, with five companies and about 12,700 prompt tokens per request, asking about one company at a time did
not make the answers more accurate, and asking about all five at once was about 7% cheaper.

## A matched-pair example (real output)

The benchmark includes a matched pair of questions. F9 asks how much stock a company bought back during the year,
and F10 asks how much it is still allowed to buy back. Both questions receive the same passages, and in Meta's 10-K
(excerpt `META-0229`) the two numbers sit in back-to-back sentences. This means a real quote could support either
number, so a quote check alone could not tell a right answer from a swapped one. Both setups kept them apart
correctly:

| | Method A | Method B |
|---|---|---|
| F9 repurchased in 2025 | **$26.26 billion**, quoting "In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate amount of $26.26 billion." | same value, same excerpt, same quote |
| F10 remaining at 12/31/2025 | **$25.03 billion**, quoting "As of December 31, 2025, $25.03 billion remained available and authorized for repurchases." | same value, same excerpt, same quote |

All four cells passed the correctness, quote and support checks (`results/results_final.csv`).

## Repository layout

```
src/
  config.py            paths, companies, model settings, prices (everything frozen with the run)
  fetch_filings.py     downloads the exact filings in data/filings.csv and verifies their content
  extract.py           HTML -> text with tables as "cell | cell" rows, units/footnotes kept with tables -> chunks
  select_evidence.py   BM25 evidence selection, once per question -> benchmark/evidence/
  prompts.py           the single shared instruction + JSON schema
  run_benchmark.py     Method A / Method B runner; logs raw output, tokens, latency, errors
  score.py             normalization, quote check, support check, paired tables, cost per verified answer
  build_answer_key.py  answer-key spec (AI-drafted from the filings, reviewed by me) -> benchmark/answer_key.csv
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
  filings.csv          provenance for each 10-K (URL, filing date, fiscal year end, SHA-256 of original download)
  filings_content_sha256.csv  SHA-256 of each filing without SEC's changing script tag
  text/, chunks/       extracted text and excerpt units (raw HTML is git-ignored and re-downloadable)
tests/                 offline checker tests (no API calls)
results/               one folder per run: manifest, calls.jsonl (raw), scored_rows.csv, summary.json
  results_final.csv    every cell, A and B side by side, all scoring tiers
  final/manual_review.csv  my verdicts on the 9 flagged citations
  final/citation_review.md  earlier AI-assisted review of the 9 flagged citations, with quoted evidence
  final/adjudication.csv  verdicts used by the secondary tiers (src/adjudicate.py)
paper/                 paper.md (editable source), paper.pdf, build_pdf.py
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

Rebuild data and evidence. The script downloads the exact filings listed in `data/filings.csv` and checks their content.
SEC adds one script tag with a changing address to the end of each page, so the check ignores that tag and compares
everything else with `data/filings_content_sha256.csv`. Any other difference, including a single changed digit, stops
the download from being accepted. The rest of the rebuild is deterministic:

```bash
cd src && ../.venv/bin/python fetch_filings.py && ../.venv/bin/python extract.py && ../.venv/bin/python select_evidence.py practice AAPL,MSFT && ../.venv/bin/python select_evidence.py final
```

```bash
cd src && ../.venv/bin/python build_answer_key.py && ../.venv/bin/python validate_key.py benchmark/answer_key.csv
```

Offline tests (checker cases; answers taken from the key = 148 of 150 verified and 2 unclear, which the test
expects; deliberately wrong answers = 0 of 64 verified; download check accepts only a changed SEC script tag):

```bash
.venv/bin/python tests/test_score.py && .venv/bin/python tests/test_key_oracle.py && .venv/bin/python tests/test_fetch_filings.py
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

- With five companies and 15 questions, there are only 75 paired answers, which is too few for strong statistical
  claims, so I report exact counts instead of only percentages.
- The temperature was set to 0, but Gemini's outputs are not guaranteed to be identical every time, and each setup
  ran only once.
- The support check is automated. When it cannot decide, it marks the cell `unclear` instead of passing it, and
  I reviewed those cells by hand, along with the two it marked `fail`.
- The judgment calls in the answer key are listed in `benchmark/ANSWER_KEY_REVIEW.md` §2. Two problems with the key
  were found after the run (a rounded Microsoft value and an over-specified Alphabet F2 question), and both are
  disclosed in the paper.
- I did not measure how long the manual review took, so that is not reported.
