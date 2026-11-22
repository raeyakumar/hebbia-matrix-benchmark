# Right Quote, Wrong Answer? Testing AI on Financial Filings

*An independent experiment inspired by Hebbia's public description of its Matrix workflow. Not affiliated with or endorsed by Hebbia. Run on 22 November 2026.*

## Abstract

Tools that extract facts from many documents can ask a language model about all documents at once, or about one document at a time. We tested whether the second design, one company per call, raises the share of financial answers that are both correct and supported by their citation, when the model, settings, instructions and evidence are held fixed. We built a 15-question benchmark over the latest Form 10-K filings of Apple, Microsoft, Alphabet, Meta and Amazon. Five questions are deliberate traps (units, periods, a footnote, missing evidence) and two form a matched pair that asks for two different numbers from the same passage. Gemini 3.8 Flash answered each question in two ways: all five companies in one call (Method A), or each company in its own call (Method B), with identical excerpts. Under the frozen automatic scorer, A produced 70 of 75 verified answers and B 69 of 75. Of the 75 paired cells, 69 were verified by both methods, 1 by A only, 0 by B only and 5 by neither (exact McNemar p = 1.0). Both methods gave the same numeric answer in all 75 cells, passed every trap and made no numerically wrong claim. After the 9 cells that the automatic support check could not confirm were re-read by hand, the methods are identical: 73 of 75 verified each. B cost about 7% more (an estimated $0.198 against $0.185 for the whole run). Because B never produced an additional verified answer, the cost per additional verified answer is undefined. In this setting, five companies and about 12,700 prompt tokens per call, splitting the request bought nothing. The weakest component was the automated citation check, not the model.

## 1. Question

When the same model receives the same evidence, does answering one company at a time improve the percentage of financial claims that are correct *and* supported by their citations? And what does each additional verified answer cost?

The motivation is a common product design. A matrix of documents × questions can be filled row by row, one model call per document, or in batches. Per-document calls are easier to parallelise and keep each context small, but they repeat instructions and cost more calls. Batching is cheaper but risks cross-document contamination: citing one company's passage for another, or swapping periods. We wanted to measure that trade-off on a task where errors are easy to define.

The title names the failure we were looking for: a quote that really appears in the source but does not support the stated number, for example a table row whose *other* column holds the answer, or a sentence that contains two figures. A check that a quote appears in the source cannot catch this, so we scored support separately.

## 2. Setup

**Filings.** We downloaded the most recent 10-K for each company from SEC EDGAR and recorded the URL, accession number, filing date, fiscal year-end and SHA-256 of every file (`data/filings.csv`).

| Company | Fiscal year end | Filed | Accession |
|---|---|---|---|
| Apple | 2026-09-26 | 2026-11-03 | 0000320193-26-000026 |
| Microsoft | 2026-06-30 | 2026-07-29 | 0001193125-26-323660 |
| Alphabet | 2025-12-31 | 2026-02-05 | 0001652044-26-000018 |
| Meta | 2025-12-31 | 2026-01-29 | 0001628280-26-003942 |
| Amazon | 2025-12-31 | 2026-02-06 | 0001018724-26-000004 |

**Extraction.** The inline-XBRL HTML was converted to text in which every table row becomes one line of `cell | cell` values. SEC's split `$` and `)` cells are merged back onto their numbers, and table titles, unit lines (for example "(In millions)"), column headers and footnotes stay attached to their tables. The text was cut into excerpts of about 1,800 characters with stable IDs (for example `AAPL-0109`). If a table is split, its title, unit line and year header are repeated on every part.

**Evidence.** For each question, BM25 retrieval over each company's excerpts selected 5 excerpts per company, using a single query that does not name any company. The selection was made **once** and frozen to `benchmark/evidence/`. Method A received all five companies' excerpts concatenated; Method B received the identical excerpts for its company only. We checked programmatically that each company's excerpt block in B's prompts is byte-identical to the same block in A's prompts.

**Methods.** Both methods used one system instruction, one prompt template, one JSON output schema (company, status, answer, value, unit, period, excerpt id, quote) and the model `gemini-3.8-flash` through the REST API. Settings were temperature 0, top-p 1, seed 7, thinking level `low` (the model's lowest documented level; thinking cannot be disabled) and a maximum of 8,192 output tokens. Each excerpt block was headed with the company name and fiscal year-end in both methods. The instruction told the model to use only the excerpts, quote verbatim, report the value as stated with its unit and period, and answer "insufficient_evidence" rather than guess.

## 3. Benchmark

The benchmark has 15 final questions plus 2 practice questions that were used only in the pilot. Ten are routine (net income, diluted EPS, cash, total assets, gross capex, operating income, operating cash flow, equity, and the matched pair). Five are traps:

* **T1, units:** the diluted share count. Apple states share counts in *thousands* inside statements labelled "in millions", and Alphabet's count is split across share classes.
* **T2, period:** revenue for "fiscal year 2025". This is the *prior-year* column for Apple and Microsoft, and the latest year for the others. Alphabet and Amazon also order columns oldest to newest.
* **T3, period and units:** the cover-page market value held by non-affiliates. It is measured at mid-year, not year-end, and is stated as whole dollars by some companies and as "trillion" by others.
* **T4, footnote:** U.S.-only revenue. Meta's table row is "United States **and Canada**" ($78,866M); the U.S.-only $74.78B appears only in a footnote.
* **T5, insufficient evidence:** borrowings under unsecured revolving credit facilities. Apple, Microsoft and Meta describe none, so the correct answer is to abstain. Alphabet and Amazon state $0 drawn next to large capacity figures.

**Matched pair (F9/F10).** F9 asks how much stock was repurchased during the year and F10 how much authorization remained. Both use the same retrieval query, so each method saw identical evidence for both questions. In Meta's filing the two answers sit in adjacent sentences: "...for an aggregate amount of $26.26 billion. As of December 31, 2025, $25.03 billion remained available...". A verbatim quote from that passage supports one answer and not the other.

**Answer key.** The 75 company–question cells were filled by reading the filings. Every supporting passage was machine-checked to appear verbatim in the extracted text, and every answerable cell's passage was confirmed to be inside the frozen evidence (72/72). The key, with a plain-language note on every ambiguous cell, is in `benchmark/answer_key.csv` and `benchmark/ANSWER_KEY_REVIEW.md`. It was never placed in a prompt. The project owner reviewed the key and settled seven judgment calls before the run. For example, Apple's remaining authorization is accepted as $114,004M because the excerpts themselves state that total. Questions, evidence, prompts, settings and scoring rules were then frozen in one Git commit with SHA-256 hashes (`benchmark/FREEZE.json`), and an integrity check before the run confirmed that nothing had changed.

## 4. Scoring

Each method × question × company cell receives three independent checks:

1. **Correct:** the claimed value, converted to base units using the model's own unit label, lies within 0.1% of the key (0.01% for per-share amounts). Magnitudes are compared because no expected answer is negative.
2. **Quote check:** the quote appears verbatim, ignoring case and whitespace, in the cited excerpt. This shows only that the text exists.
3. **Support check:** the cited excerpt belongs to the row's company; the claimed value appears in the quote at the excerpt's stated scale; and the period matches. For tables, the matching cell is mapped to its column's year header; for prose, the year must appear in the sentence. Cases the rules cannot decide are labelled *unclear* and passed to human review rather than counted as passes.

An answer is **verified** only if all three checks pass. **Abstentions** (`insufficient_evidence` or a null value) count as correct, and as verified, only where the key expects one (T5 for three companies). Elsewhere they count as wrong and are reported separately from wrong numbers. API failures were to be kept as error rows and scored as wrong; the final run had none.

Before the run, the checker was tested offline. An "oracle" that answers every cell from the key scored 150/150 verified. An adversary that quotes the correct row but reports another column's number, or swaps the matched-pair answers, scored 0/64 verified, and 61 of those 64 cells also failed the support check.

## 5. Results

The final run made 90 calls (15 for A, 75 for B) with 0 errors and 0 retries; every call ended with `STOP`. All figures below come from `results/final/` and `results/results_final.csv`.

**Main result.** We report the frozen automatic score (tier 1), then two clearly labelled re-readings made after the run. Tier 2 re-judges only the support verdicts, by reading the excerpts. Tier 3 also corrects one answer-key defect.

| Tier | A verified | B verified | Both | Only A | Only B | Neither |
|---|---|---|---|---|---|---|
| 1. Frozen automatic scorer | 70/75 | 69/75 | 69 | 1 | 0 | 5 |
| 2. + support verdicts re-read | 73/75 | 73/75 | 73 | 0 | 0 | 2 |
| 3. + key rounding fix | 74/75 | 74/75 | 74 | 0 | 0 | 1 |

Both methods were correct on 73/75 cells under the frozen key. The quote check passed for 71 of 71 answered cells in both methods: no quote was invented or paraphrased. The automatic support check passed 67 (A) and 66 (B). With one discordant pair, the exact McNemar test gives p = 1.0; there is no evidence of a difference.

**Same answers.** The two methods gave the same number in all 75 cells. The only differences were that B reported Amazon's and Microsoft's capex as negative outflows (scored on magnitude, as the frozen rule specifies) and integer-versus-decimal formatting. They cited different excerpts in 8 cells, for example the income statement in one method and the MD&A table in the other. Seven of these were answered cells, and both citations were verified in every one, although one (B, Alphabet F6) needed the tier-2 re-reading. The eighth was a correct abstention.

**Tricky questions, reported separately.** Both methods were correct on all 25 trap cells and verified on 23/25 under tier 1 (25/25 in tier 2). Both reported Meta's U.S.-only $74.78B from the footnote rather than the "United States and Canada" row, read Apple's share count as thousands, chose the prior-year column for Apple's and Microsoft's fiscal 2025 revenue, gave the mid-year measurement dates for market value, and abstained on T5 for Apple, Microsoft and Meta without inventing a figure.

**Abstentions.** Each method abstained 4 times: 3 correct (T5) and 1 incorrect, on Alphabet F2. In that question we had reworded F2 at review time to ask for EPS "as reported on its consolidated income statement". The retrieved evidence held Note 12, whose *Consolidated* column shows the correct $10.81, but not the income statement itself, and both methods declined on that ground. We count this as wrong in every tier and attribute it to our question wording, not to either method.

**The matched pair.** All ten pair cells were correct in both methods. For Meta, both methods cited excerpt `META-0229`, quoted the "$26.26 billion" sentence for F9 and the "$25.03 billion" sentence for F10, and passed all three checks. For Microsoft, both methods reported the exact program total, $16,719M, from Note 15. That value differs from our key's rounded $16.7B by 0.11%, just outside the tolerance, which is the defect corrected in tier 3.

**Cost and speed.** Costs are estimates: API token counts multiplied by the published paid-tier prices ($0.75 per million input tokens, $3.75 per million output tokens including thinking).

| | Method A | Method B |
|---|---|---|
| Calls | 15 | 75 |
| Prompt tokens | 190,801 (12,720 / call) | 211,697 (2,823 / call) |
| Output tokens (incl. thinking) | 11,237 | 10,455 |
| Estimated cost | $0.185 | $0.198 (+6.9%) |
| Latency per question | 6.9 s (one call) | 15.7 s run one after another; about 4.6 s if run in parallel (estimated as the slowest of each question's five calls) |

B's extra cost comes almost entirely from repeating the system instruction and question in five calls instead of one. **Cost per additional verified answer:** under tier 1, A, not B, has the one extra verified answer and is also cheaper. Under tiers 2 and 3 the methods tie. B therefore never produced an additional verified answer, and the ratio is undefined; we do not report one.

## 6. What actually failed

No answer was a wrong number. The 9 cells that the automatic support check failed or marked unclear were all supported on reading. Three causes account for them: a table whose header mixes years with "$ Change | % Change" columns; a Shares/Amount table with two cells per year; and the unit phrase "(net income in millions and shares in thousands)", which our unit pattern did not recognise. One further unit appeared only in an earlier excerpt of the same note. These 9 cells were 6.3% of the 142 answered cells, and none of the 133 automatic passes was hand-audited. The remaining misses were our own: one rounded answer-key value and one over-specified question. **In this experiment the bottleneck was verification, not generation**, and the automatic verifier erred in the safe direction.

Human verification time was not measured and is not reported. The tier-2 and tier-3 re-readings were made by the AI assistant that ran the study, from the excerpts, and are recorded cell by cell with reasons in `results/final/adjudication.csv`. They still await human confirmation.

## 7. Limitations

* **Small and easy.** With 75 paired cells, the study can detect only large effects. Each A prompt was about 12,700 tokens over five companies; batching risks are likely to grow with more documents, longer excerpts and more similar entities. A null result here does not show that per-document calls never help.
* **One model, one run.** Temperature 0 does not guarantee deterministic output, and each condition ran once.
* **Retrieval held fixed.** Evidence recall was engineered to be complete (72/72), so the study isolates answer generation from retrieval. In production, misses in retrieval would interact with both methods.
* **Author-built key.** The key was built by the AI assistant that ran the study and reviewed by the project owner; it was not built by independent annotators. Two defects were found only after the run, and both are disclosed above.
* **Prices change.** Gemini 3.8 Flash list prices double on 1 January 2027; ratios between methods are more durable than dollar amounts.

## 8. Conclusion

On five large-cap 10-Ks, with identical evidence, settings and checker, answering one company at a time did not improve the rate of correct, supported financial claims. Both designs made the same numerical answers, passed the same traps and failed only where our own key, question or checker failed. Batching was about 7% cheaper. The design choice that mattered was scoring support separately from quote existence: it surfaced every ambiguity for review and accepted none of the 64 deliberately wrong answers in testing. A natural next step is to scale the matrix (more companies per call, longer excerpts, near-duplicate entities) until the methods diverge, and to measure human review time directly.

## Reproducibility

Code, frozen inputs and raw outputs are in the repository. The `README` gives exact commands. Raw model responses, token usage, latency and errors are in `results/final/calls.jsonl`; per-cell scores are in `results/final/scored_rows.csv`; and the side-by-side results with all tiers are in `results/results_final.csv`.
