# Review of the nine flagged citations (AI-assisted)

**What this is.** An AI-assisted review, carried out by the Claude assistant that ran the study on 2026-11-22. It
is **not** independent human verification, and no human review time was measured. The **frozen automatic scores
(tier 1) remain the main result**. This review feeds only the secondary tier-2/3 re-readings
(`adjudication.csv`, `src/adjudicate.py`).

**Scope.** These are the 9 answered cells where the frozen support check returned `unclear` or `fail` although the
answer's number was in the quote. All 9 answers are the model's saved output (`calls.jsonl`); no API call was made
for this review.

**Method.** For each cell:
1. Read the model's quote and the full cited excerpt as both methods received it.
2. Confirm that every label, figure and unit phrase below also appears in the **original SEC HTML**. The files were
   re-hashed against `data/filings.csv`, and each passage was found co-located in the stripped HTML text.
3. Judge company, metric, period and unit separately, using only what the **cited excerpt** shows.

A cell is *supported* only if all four judgments hold from the cited excerpt. It is *inconclusive* if any of them
depends on text outside the cited excerpt or is ambiguous.

**Result: 7 supported, 2 inconclusive, 0 not supported.**

| # | Cell | Answer | Verdict |
|---|---|---|---|
| 1 | B · F6 · Alphabet | $129,039M operating income, FY2025 | Supported |
| 2 | A · F9 · Alphabet | $45,398M repurchased, FY2025 | Supported |
| 3 | B · F9 · Alphabet | $45,398M repurchased, FY2025 | Supported |
| 4 | A · T1 · Apple | 14,720,306 thousand diluted shares, FY2026 | Supported |
| 5 | B · T1 · Apple | 14,720,306 thousand diluted shares, FY2026 | Supported |
| 6 | A · T1 · Alphabet | 12,230 million diluted shares, FY2025 | **Inconclusive** |
| 7 | B · T1 · Alphabet | 12,230 million diluted shares, FY2025 | **Inconclusive** |
| 8 | A · F9 · Microsoft | $16,719M repurchased under the program, FY2026 | Supported |
| 9 | B · F9 · Microsoft | $16,719M repurchased under the program, FY2026 | Supported |

---

### 1. B · F6 · Alphabet: Supported

Cited excerpt `GOOGL-0107` (Item 7, MD&A), Alphabet 10-K for the year ended December 31, 2025:

> The following table summarizes consolidated financial results (in millions, except for per share information and percentages):
> Year Ended December 31,
> 2024 | 2025 | $ Change | % Change
> Operating income | $112,390 | $129,039 | $16,649 | 15%

- **Company:** an Alphabet excerpt, cited in Alphabet's row. ✓
- **Metric:** "Operating income". It matches the income statement's "Income from operations" ($129,039M). ✓
- **Period:** the second value sits under the 2025 header; the last two cells are the change columns. ✓
- **Unit:** "(in millions…)" in the same excerpt; the claim is USD millions. ✓
- **Why the checker missed it:** the header has 2 years but the row has 4 numeric cells, so its column mapping gave
  up.

### 2–3. A and B · F9 · Alphabet: Supported

Both methods cited `GOOGL-0209` (Note 11, Stockholders' Equity) and the same row:

> The following table presents Class A and Class C shares repurchased and subsequently retired (in millions):
> Year Ended December 31,
> 2023 | 2024 | 2025
> Shares | Amount | Shares | Amount | Shares | Amount
> Total share repurchases(1) | 528 | $62,184 | 379 | $62,047 | 240 | $45,398
> (1) Shares repurchased include any unsettled repurchases.
> … The repurchase programs do not have an expiration date.

- **Company:** Alphabet. ✓
- **Metric:** total dollar amount repurchased. The same excerpt goes on to describe these repurchases under "the
  repurchase programs". The Class A $6,501M and Class C $38,897M rows sum to $45,398M, which matches the MD&A's
  "$45.4 billion". ✓
- **Period:** the 2025 pair is the last Shares/Amount pair; $45,398 is its Amount. ✓
- **Unit:** "(in millions)" in the same excerpt; the claim is USD millions. ✓
- **Note:** footnote (1) says the total includes unsettled repurchases. That changes nothing here, because the
  answer key's $45.4B is the same figure.
- **Why the checker missed it:** three year labels over six cells.

### 4–5. A and B · T1 · Apple: Supported

Both methods cited `AAPL-0121` (Note 3, Earnings Per Share):

> The following table shows the computation of basic and diluted earnings per share for 2026, 2025 and 2024 (net income in millions and shares in thousands):
> 2026 | 2025 | 2024
> Weighted-average diluted shares | 14,720,306 | 15,004,697 | 15,408,095

- **Company:** Apple. ✓
- **Metric:** the weighted-average diluted shares used for diluted EPS. Basic 14,661,935 plus dilutive awards 58,371
  gives 14,720,306. ✓
- **Period:** the first column is 2026, Apple's fiscal year ended September 26, 2026. ✓
- **Unit:** "shares in thousands" in the same excerpt. Both methods reported thousands (A "shares in thousands",
  B "thousands of shares"). ✓
- **Why the checker failed it:** its unit-line pattern expects "(in thousands…" and did not match "(net income in
  millions and shares in thousands)". This is a checker false negative.

### 6–7. A and B · T1 · Alphabet: Inconclusive

Both methods cited `GOOGL-0214` (Note 12, Net Income Per Share):

> Year Ended December 31, 2025
> Class A | Class B | Class C | Consolidated
> …
> Number of shares used in per share computation | 5,822 | 849 | 5,445 | 12,116   *(basic)*
> Diluted net income per share: …
> Restricted stock units and other contingently issuable shares | 0 | 0 | 114 | 114
> Number of shares used in per share computation | 6,671 | 849 | 5,559 | 12,230   *(diluted)*

- **Company:** Alphabet. ✓
- **Metric:** the diluted count in the **Consolidated** column (basic 12,116 plus 114 dilutive shares = 12,230,
  which also equals Class A 6,671 plus Class C 5,559 as converted). Excerpt `GOOGL-0210` states that diluted EPS
  "is computed using the weighted-average number of shares". ✓
- **Period:** the table is headed "Year Ended December 31, 2025". ✓
- **Unit:** **not in the cited excerpt.** The unit is stated only in excerpt `GOOGL-0211` ("…net income per share of
  Class A, Class B, and Class C stock (in millions, except per share amounts):"), which introduces the 2023, 2024
  and 2025 tables. Both methods received that excerpt, so "12,230 **million** shares" is correct and grounded in
  the evidence. But the citation the models gave does not on its own establish the unit.
- **Verdict:** inconclusive as a *citation* (the claim itself is right). Under the study's definition, a claim
  supported by its citation, this cell cannot be counted as verified without relying on a second, uncited
  excerpt.

### 8–9. A and B · F9 · Microsoft: Supported

Both methods cited `MSFT-0199` (Note 15, Stockholders' Equity):

> We repurchased the following shares of common stock under the share repurchase programs:
> (In millions) | Shares | Amount | Shares | Amount | Shares | Amount
> Year Ended June 30, | 2026 | 2025 | 2024
> First Quarter | 8 | $3,955 | … / Second Quarter | 12 | 5,964 | … / Third Quarter | 7 | 3,400 | … / Fourth Quarter | 9 | 3,400 | …
> Total | 36 | $16,719 | 31 | $13,000 | 32 | $11,960

- **Company:** Microsoft. ✓
- **Metric:** the amount repurchased "under the share repurchase programs". This is the program figure the
  reviewer chose, not the cash-flow line ($22,271M). The quarters sum to $16,719M. ✓
- **Period:** the first pair is fiscal 2026 (year ended June 30, 2026). The 2021 program was completed in April
  2025, before fiscal 2026 began. ✓
- **Unit:** "(In millions)" in the same excerpt. ✓
- **Separate issue (correctness, not support):** the frozen key states the rounded "$16.7 billion" from MD&A, and
  $16,719M is 0.11% from it, outside the 0.1% tolerance. Tier 1 therefore scores this cell incorrect. Only tier 3
  corrects it, as a disclosed post-hoc key fix.

---

### Effect on the secondary tiers (tier 1 unchanged)

| Tier | A verified | B verified | Both | Only A | Only B | Neither |
|---|---|---|---|---|---|---|
| 1. Frozen automatic scorer (**main result**) | 70 | 69 | 69 | 1 | 0 | 5 |
| 2. + this AI-assisted support review | 72 | 72 | 72 | 0 | 0 | 3 |
| 3. + post-hoc key rounding fix (Microsoft F9) | 73 | 73 | 73 | 0 | 0 | 2 |

The earlier version of tier 2 counted Alphabet T1 as supported, giving 73 and 74 at tiers 2 and 3. This review
reclassifies it as inconclusive, and inconclusive cells are **not** counted as verified.
