# Answer key review

Generated from `benchmark/answer_key.csv` by `src/make_review.py`. Edit the CSV (or the spec in `src/build_answer_key.py`), not this file. The key is read only by the scorer; it never enters a prompt.

Every `supporting_passage` has been machine-checked to appear verbatim in the extracted 10-K text, and for every answerable cell the passage is inside the evidence the models receive (evidence recall 72/72).

## 1. Matched pair (F9 / F10): two facts, one passage

**F9.** What dollar amount of its common stock did the company repurchase under its share repurchase program(s) during its most recent fiscal year?

**F10.** What was the total dollar amount remaining available for future repurchases across all of the company's active share repurchase programs at the end of its most recent fiscal year?

Both questions use the same retrieval query, so each method sees *identical* excerpts for F9 and F10; only the requested fact differs.

Meta's filing (https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm), Item 7 (MD&A, excerpt META-0229). Both this passage and the Note 12 version, which adds the prior-year $51.28 billion remaining, are in the evidence:

> In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate amount of $26.26 billion. As of December 31, 2025, $25.03 billion remained available and authorized for repurchases.

| | Expected | Wrong-but-plausible answer in the same passage |
|---|---|---|
| F9 repurchased in 2025 | **$26.26 billion repurchased** | $25.03 billion (the remaining amount) |
| F10 remaining at 12/31/2025 | **$25.03 billion remaining** | $26.26 billion (the repurchased amount); $51.28 billion (prior-year remaining, in the Note version) |

The pair for the other four companies:

| Company | F9 repurchased | F10 remaining |
|---|---|---|
| Apple | $85.8 billion repurchased | $114,004 million (about $114.0 billion) may yet be purchased under the plans or programs |
| Microsoft | $16.7 billion repurchased | $40.6 billion remaining |
| Alphabet | $45.4 billion repurchased | $69.5 billion remaining |
| Meta | $26.26 billion repurchased | $25.03 billion remaining |
| Amazon | $0 (no repurchases in 2025) | $6.1 billion remaining |

## 2. Cells that need your judgment

`DECIDED` = settled by the reviewer (2026-11-22). `AMBIGUOUS` = my call, not separately reviewed. `NEEDS YOUR DECISION` = open.

| Q | Company | Draft expected answer | Also accepted | Note |
|---|---|---|---|---|
| F10 | Apple | $114,004 million (about $114.0 billion) may yet be purchased under the plans or programs | - | DECIDED (reviewer rule, 2026-11-22): $114B is accepted only if the excerpts both methods receive establish the full total. They do: the Item 5 table (excerpt AAPL-0091, in the F10 evidence) states the 'Approximate Dollar Value of Shares That May Yet Be Purchased Under the Plans or Programs' as $114,004 million, and footnote (1) gives $14.0B under the May 2025 program plus the new $100B program. $14.0B alone is NOT accepted, because the question asks for the total across all active programs. Note the extracted Total row drops empty cells, so the $114,004 figure sits next to the share count; the column header names it. Caution: the table is labeled 'in millions, except number of shares, which are reflected in thousands'. |
| F2 | Alphabet | $10.81 per diluted share | - | DECIDED (reviewer, 2026-11-22): question now asks for the company-wide figure as reported on the consolidated income statement, so $10.81 is expected. Note 12's per-class figures (Class A $10.82, Class C $10.80) are NOT accepted; EPS rows use a tight tolerance so they are not silently accepted. |
| F9 | Apple | $85.8 billion repurchased | - | DECIDED (reviewer, 2026-11-22): only $85.8B accepted. The equity-statement ($86,485M) and cash-flow ($86,390M) figures are NOT accepted. |
| F9 | Microsoft | $16.7 billion repurchased | - | DECIDED (reviewer, 2026-11-22): only $16.7B accepted. The cash-flow line 'Common stock repurchased' ($22,271M) also includes shares withheld for employee taxes and is NOT accepted. Same sentence also gives FY2025 ($13.0B) - period trap. |
| T5 | Amazon | $0 - no borrowings under the two unsecured revolving credit facilities | - | DECIDED (reviewer, 2026-11-22): $0 kept because the provided excerpt (AMZN-0073) states it for exactly the facilities the question names - the two unsecured revolving credit facilities ($15.0B Credit Agreement and $5.0B 364-day Short-Term Credit Agreement) - as of December 31, 2025, Amazon's fiscal year-end. The $455M belongs to 'other short-term credit facilities', which the question now excludes. Also excluded: a secured revolving facility terminated in 2024. Capacity figures ($15.0B, $5.0B) are traps. |
| F5 | Amazon | $131,819 million | - | AMBIGUOUS-MINOR: gross purchases. Amazon also reports proceeds from property and equipment sales and incentives; a net figure is not accepted. |
| T1 | Alphabet | 12,230 million shares (Class A 6,671M as-converted + Class C 5,559M) | - | AMBIGUOUS: Alphabet computes EPS per share class. The 'Total' column of the 2025 diluted computation (Note 12) is 12,230M. The Class A diluted count (6,671M) already includes the as-converted Class B shares, so summing A+B+C would double count. Only 12,230M accepted. |

## 3. Scoring rules (to be frozen with the key)

- **Correct**: claimed value converted to base units (using the model's own `unit`) is within the row's relative tolerance (0.1%; 0.01% for per-share amounts) of the expected value or an accepted alternate. Signs are ignored (magnitudes compared): no expected answer is negative, and the filings show outflows such as capex in parentheses.
- **Abstention**: `status = insufficient_evidence` (or a null value). Correct only where the key says `expect_abstain = yes` (T5 for Apple, Microsoft and Meta). Abstaining on an answerable cell counts as wrong, reported separately from wrong numbers. A correct abstention counts as verified, since there is no claim to cite.
- **Quote check**: quote appears verbatim (case/whitespace-normalized) in the cited excerpt. Passing it means only that the text exists.
- **Support check** (separate): the cited excerpt belongs to the row's company; the claimed value at the claimed unit appears in the quote at the excerpt's stated scale; the period matches (table column mapped to its year header, or the year stated in a prose quote). Undecidable cases are `unclear` and are listed for human review instead of being silently passed.
- **Verified** = correct AND quote check AND support check.

## 4. Full key

### F1

What was the company's net income for its most recent fiscal year covered by this 10-K?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $132,175 million | USD millions | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (In millions, except number of shares, which are reflected in thousands, and per-share amounts) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Net income \| $132,175 \| $112,010 \| $93,736 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $133,749 million | USD millions | fiscal year ended June 30 2026 | INCOME STATEMENTS \|\| (In millions, except per share amounts) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Net income \| $133,749 \| $101,832 \| $88,136 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $132,170 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (in millions, except per share amounts) \|\| 2023 \| 2024 \| 2025 \|\| Net income \| $73,795 \| $100,118 \| $132,170 | Columns run oldest to newest (2023 \| 2024 \| 2025); the most recent year is the LAST column. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $60,458 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (In millions, except per share amounts) \|\| 2025 \| 2024 \| 2023 \|\| Net income \| $60,458 \| $62,360 \| $39,098 | 2025 net income is LOWER than 2024 ($62,360M); a model assuming growth could pick the wrong column. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $77,670 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (in millions, except per share data) \|\| 2023 \| 2024 \| 2025 \|\| Net income \| $30,425 \| $59,248 \| $77,670 | Columns run oldest to newest. |

### F2

What were the company's company-wide diluted earnings per share for its most recent fiscal year, as reported on its consolidated income statement (one figure for the whole company, not a per-share-class figure)?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $8.98 per diluted share | USD per share | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (In millions, except number of shares, which are reflected in thousands, and per-share amounts) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Diluted \| $8.98 \| $7.46 \| $6.08 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $17.95 per diluted share | USD per share | fiscal year ended June 30 2026 | INCOME STATEMENTS \|\| (In millions, except per share amounts) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Diluted \| $17.95 \| $13.64 \| $11.80 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $10.81 per diluted share | USD per share | year ended December 31 2025 | Diluted net income per share (Note 12) \| $5.80 \| $8.04 \| $10.81 \|\| Diluted net income per share \| $10.82 \| $10.81 \| $10.80 \| $10.81 | DECIDED (reviewer, 2026-11-22): question now asks for the company-wide figure as reported on the consolidated income statement, so $10.81 is expected. Note 12's per-class figures (Class A $10.82, Class C $10.80) are NOT accepted; EPS rows use a tight tolerance so they are not silently accepted. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $23.49 per diluted share | USD per share | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (In millions, except per share amounts) \|\| 2025 \| 2024 \| 2023 \|\| Diluted \| $23.49 \| $23.86 \| $14.87 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $7.17 per diluted share | USD per share | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (in millions, except per share data) \|\| 2023 \| 2024 \| 2025 \|\| Diluted earnings per share \| $2.90 \| $5.53 \| $7.17 |  |

### F3

What was the company's cash and cash equivalents balance at the end of its most recent fiscal year (balance sheet amount)?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $36,305 million | USD millions | as of September 26 2026 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares, which are reflected in thousands, and par value) \|\| September 26, 2026 \| September 27, 2025 \|\| Cash and cash equivalents \| $36,305 \| $35,934 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $20,935 million | USD millions | as of June 30 2026 | BALANCE SHEETS \|\| (In millions) \|\| June 30, \| 2026 \| 2025 \|\| Cash and cash equivalents \| $20,935 \| $30,242 | Balance-sheet cash and cash equivalents only; excludes short-term investments. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $30,708 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except par value per share amounts) \|\| 2024 \| 2025 \|\| Cash and cash equivalents \| $23,466 \| $30,708 | Columns 2024 \| 2025. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $35,873 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares and par value) \|\| 2025 \| 2024 \|\| Cash and cash equivalents \| $35,873 \| $43,889 | Columns 2025 \| 2024; cash fell year over year. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $86,810 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except per share data) \|\| 2024 \| 2025 \|\| Cash and cash equivalents \| $78,779 \| $86,810 | Columns 2024 \| 2025. |

### F4

What were the company's total assets at the end of its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $404,548 million | USD millions | as of September 26 2026 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares, which are reflected in thousands, and par value) \|\| September 26, 2026 \| September 27, 2025 \|\| Total assets \| $404,548 \| $359,241 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $758,376 million | USD millions | as of June 30 2026 | BALANCE SHEETS \|\| (In millions) \|\| June 30, \| 2026 \| 2025 \|\| Total assets \| $758,376 \| $619,003 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $595,281 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except par value per share amounts) \|\| 2024 \| 2025 \|\| Total assets \| $450,256 \| $595,281 | Columns 2024 \| 2025. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $366,021 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares and par value) \|\| 2025 \| 2024 \|\| Total assets \| $366,021 \| $276,054 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $818,042 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except per share data) \|\| 2024 \| 2025 \|\| Total assets \| $624,894 \| $818,042 | Columns 2024 \| 2025. |

### F5

What were the company's gross cash purchases of (additions to) property and equipment in its most recent fiscal year, as reported in the investing section of the cash flow statement? Report the gross amount, before any proceeds from sales of property and equipment or incentives.

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $9,041 million | USD millions | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (In millions) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Payments for acquisition of property, plant and equipment \| (9,041) \| (12,715) \| (9,447) | Shown as a negative (cash outflow) in the filing; scored on magnitude. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $115,948 million | USD millions | fiscal year ended June 30 2026 | CASH FLOWS STATEMENTS \|\| (In millions) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Additions to property and equipment \| (115,948) \| (64,551) \| (44,477) | Excludes assets acquired under finance leases, which Microsoft discusses separately. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $91,447 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (in millions) \|\| 2023 \| 2024 \| 2025 \|\| Purchases of property and equipment \| (32,251) \| (52,535) \| (91,447) |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $69,691 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (In millions) \|\| 2025 \| 2024 \| 2023 \|\| Purchases of property and equipment \| (69,691) \| (37,256) \| (27,045) |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $131,819 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (in millions) \|\| 2023 \| 2024 \| 2025 \|\| Purchases of property and equipment \| (52,729) \| (82,999) \| (131,819) | AMBIGUOUS-MINOR: gross purchases. Amazon also reports proceeds from property and equipment sales and incentives; a net figure is not accepted. |

### F6

What was the company's operating income (income from operations) for its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $158,063 million | USD millions | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (In millions, except number of shares, which are reflected in thousands, and per-share amounts) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Operating income \| 158,063 \| 133,050 \| 123,216 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $155,237 million | USD millions | fiscal year ended June 30 2026 | INCOME STATEMENTS \|\| (In millions, except per share amounts) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Operating income \| 155,237 \| 128,528 \| 109,433 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $129,039 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (in millions, except per share amounts) \|\| 2023 \| 2024 \| 2025 \|\| Income from operations \| 84,293 \| 112,390 \| 129,039 |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $83,276 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (In millions, except per share amounts) \|\| 2025 \| 2024 \| 2023 \|\| Income from operations \| 83,276 \| 69,380 \| 46,751 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $79,975 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (in millions, except per share data) \|\| 2023 \| 2024 \| 2025 \|\| Operating income \| 36,852 \| 68,593 \| 79,975 |  |

### F7

What was the company's net cash provided by operating activities for its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $145,097 million | USD millions | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (In millions) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Cash generated by operating activities \| 145,097 \| 111,482 \| 118,254 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $182,935 million | USD millions | fiscal year ended June 30 2026 | CASH FLOWS STATEMENTS \|\| (In millions) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Net cash from operations \| 182,935 \| 136,162 \| 118,548 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $164,713 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (in millions) \|\| 2023 \| 2024 \| 2025 \|\| Net cash provided by operating activities \| 101,746 \| 125,299 \| 164,713 |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $115,800 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (In millions) \|\| 2025 \| 2024 \| 2023 \|\| Net cash provided by operating activities \| 115,800 \| 91,328 \| 71,113 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $139,514 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF CASH FLOWS \|\| (in millions) \|\| 2023 \| 2024 \| 2025 \|\| Net cash provided by (used in) operating activities \| 84,946 \| 115,877 \| 139,514 |  |

### F8

What was the company's total stockholders' (shareholders') equity at the end of its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $112,093 million | USD millions | as of September 26 2026 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares, which are reflected in thousands, and par value) \|\| September 26, 2026 \| September 27, 2025 \|\| Total shareholders' equity \| 112,093 \| 73,733 |  |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $442,387 million | USD millions | as of June 30 2026 | BALANCE SHEETS \|\| (In millions) \|\| June 30, \| 2026 \| 2025 \|\| Total stockholders' equity \| 442,387 \| 343,479 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $415,265 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except par value per share amounts) \|\| 2024 \| 2025 \|\| Total stockholders' equity \| 325,084 \| 415,265 |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $217,243 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (In millions, except number of shares and par value) \|\| 2025 \| 2024 \|\| Total stockholders' equity \| 217,243 \| 182,637 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $411,065 million | USD millions | as of December 31 2025 | CONSOLIDATED BALANCE SHEETS \|\| (in millions, except per share data) \|\| 2024 \| 2025 \|\| Total stockholders' equity \| 285,970 \| 411,065 |  |

### F9

What dollar amount of its common stock did the company repurchase under its share repurchase program(s) during its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $85.8 billion repurchased | USD billions | fiscal year ended September 26 2026 | During 2026, the Company repurchased 297 million shares of its common stock for $85.8 billion. | DECIDED (reviewer, 2026-11-22): only $85.8B accepted. The equity-statement ($86,485M) and cash-flow ($86,390M) figures are NOT accepted. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $16.7 billion repurchased | USD billions | fiscal year ended June 30 2026 | During fiscal years 2026 and 2025, we repurchased 36 million shares and 31 million shares of our common stock for $16.7 billion and $13.0 billion, respectively, through our share repurchase program. | DECIDED (reviewer, 2026-11-22): only $16.7B accepted. The cash-flow line 'Common stock repurchased' ($22,271M) also includes shares withheld for employee taxes and is NOT accepted. Same sentence also gives FY2025 ($13.0B) - period trap. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $45.4 billion repurchased | USD billions | year ended December 31 2025 | During 2025, we repurchased and subsequently retired 240 million shares for $45.4 billion. |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $26.26 billion repurchased | USD billions | year ended December 31 2025 | In 2025, we repurchased and subsequently retired 40 million shares of our Class A common stock for an aggregate amount of $26.26 billion. | MATCHED-PAIR SHOWCASE: the same two sentences give $26.26B repurchased and $25.03B remaining. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $0 (no repurchases in 2025) | USD billions | year ended December 31 2025 | There were no repurchases of our common stock in 2023, 2024, or 2025. | Correct answer is zero, stated explicitly; an 'insufficient evidence' abstention is scored wrong. Same passage gives $6.1B remaining (F10). |

### F10

What was the total dollar amount remaining available for future repurchases across all of the company's active share repurchase programs at the end of its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $114,004 million (about $114.0 billion) may yet be purchased under the plans or programs | USD millions | as of September 26 2026 | Periods \| Total Number of Shares Purchased \| Average Price Paid Per Share \| Total Number of Shares Purchased as Part of Publicly Announced Plans or Programs \| Approximate Dollar Value of Shares That May Yet Be Purchased Under the Plans or Programs (1) \|\| As of September 26, 2026, remaining availability under the May 2025 program was $14.0 billion. \|\| Total \| 81,767 \| $114,004 | DECIDED (reviewer rule, 2026-11-22): $114B is accepted only if the excerpts both methods receive establish the full total. They do: the Item 5 table (excerpt AAPL-0091, in the F10 evidence) states the 'Approximate Dollar Value of Shares That May Yet Be Purchased Under the Plans or Programs' as $114,004 million, and footnote (1) gives $14.0B under the May 2025 program plus the new $100B program. $14.0B alone is NOT accepted, because the question asks for the total across all active programs. Note the extracted Total row drops empty cells, so the $114,004 figure sits next to the share count; the column header names it. Caution: the table is labeled 'in millions, except number of shares, which are reflected in thousands'. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $40.6 billion remaining | USD billions | as of June 30 2026 | As of June 30, 2026, $40.6 billion remained of our $60 billion share repurchase program. | Trap: the $60B program size appears in the same sentence. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $69.5 billion remaining | USD billions | as of December 31 2025 | As of December 31, 2025, $69.5 billion remained available for Class A and Class C share repurchases. | Trap: two $70.0B authorizations appear in the same paragraph. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $25.03 billion remaining | USD billions | as of December 31 2025 | As of December 31, 2025, $25.03 billion remained available and authorized for repurchases. | MATCHED-PAIR SHOWCASE (see F9). The Note version of this passage also gives the prior-year $51.28B remaining. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $6.1 billion remaining | USD billions | as of December 31 2025 | As of December 31, 2025, we have $6.1 billion remaining under the repurchase program. | Trap: the $10.0B program size appears in the same passage. |

### T1 *(tricky: units)*

What was the consolidated (company-wide, all share classes combined) weighted-average number of diluted shares used to calculate the company's annual diluted earnings per share for its most recent fiscal year? Report the count of shares.

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | 14,720,306 thousand shares (about 14.72 billion) | thousand shares | fiscal year ended September 26 2026 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (In millions, except number of shares, which are reflected in thousands, and per-share amounts) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Diluted \| 14,720,306 \| 15,004,697 \| 15,408,095 | UNIT TRAP: Apple reports share counts in THOUSANDS while dollar amounts are in millions (stated in the statement's unit line). A model reading 14,720,306 as millions is off by 1,000x. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | 7,453 million shares | million shares | fiscal year ended June 30 2026 | INCOME STATEMENTS \|\| (In millions, except per share amounts) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Diluted \| 7,453 \| 7,465 \| 7,469 |  |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | 12,230 million shares (Class A 6,671M as-converted + Class C 5,559M) | million shares | year ended December 31 2025 | Number of shares used in per share computation \| 6,671 \| 849 \| 5,559 \| 12,230 | AMBIGUOUS: Alphabet computes EPS per share class. The 'Total' column of the 2025 diluted computation (Note 12) is 12,230M. The Class A diluted count (6,671M) already includes the as-converted Class B shares, so summing A+B+C would double count. Only 12,230M accepted. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | 2,574 million shares | million shares | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (In millions, except per share amounts) \|\| 2025 \| 2024 \| 2023 \|\| Diluted \| 2,574 \| 2,614 \| 2,629 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | 10,827 million shares | million shares | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (in millions, except per share data) \|\| 2023 \| 2024 \| 2025 \|\| Diluted \| 10,492 \| 10,721 \| 10,827 |  |

### T2 *(tricky: period)*

What was the company's total revenue (total net sales) for its fiscal year 2025?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $416,161 million (fiscal 2025 = year ended September 27 2025, the PRIOR-year column) | USD millions | fiscal year ended September 27 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (In millions, except number of shares, which are reflected in thousands, and per-share amounts) \|\| September 26, 2026 \| September 27, 2025 \| September 28, 2024 \|\| Total net sales \| 478,834 \| 416,161 \| 391,035 | PERIOD TRAP: this 10-K covers fiscal 2026; fiscal 2025 is the middle column. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $281,724 million (fiscal 2025 = year ended June 30 2025, the PRIOR-year column) | USD millions | fiscal year ended June 30 2025 | INCOME STATEMENTS \|\| (In millions, except per share amounts) \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| Total revenue \| 331,839 \| 281,724 \| 245,122 | PERIOD TRAP: this 10-K covers fiscal 2026; fiscal 2025 is the middle column. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $402,836 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (in millions, except per share amounts) \|\| 2023 \| 2024 \| 2025 \|\| Revenues \| $307,394 \| $350,018 \| $402,836 | Fiscal 2025 is the most recent year here (last column). |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $200,966 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF INCOME \|\| (In millions, except per share amounts) \|\| 2025 \| 2024 \| 2023 \|\| Revenue \| $200,966 \| $164,501 \| $134,902 |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $716,924 million | USD millions | year ended December 31 2025 | CONSOLIDATED STATEMENTS OF OPERATIONS \|\| (in millions, except per share data) \|\| 2023 \| 2024 \| 2025 \|\| Total net sales \| 574,785 \| 637,959 \| 716,924 | Fiscal 2025 is the most recent year here (last column). |

### T3 *(tricky: period_and_units)*

What aggregate market value of the company's stock held by non-affiliates did the company report on the cover of this 10-K?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | approximately $3,647,099,000,000 as of March 27 2026 | USD | as of March 27 2026 (last business day of second fiscal quarter) | The aggregate market value of the voting and non-voting stock held by non-affiliates of the Registrant, as of March 27, 2026, the last business day of the Registrant's most recently completed second fiscal quarter, was approximately $3,647,099,000,000. | PERIOD TRAP: measured at mid-year, not fiscal year-end. UNITS: stated in whole dollars. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $3.6 trillion as of December 31 2025 | USD trillions | as of December 31 2025 | As of December 31, 2025, the aggregate market value of the registrant's common stock held by non-affiliates of the registrant was $3.6 trillion | PERIOD TRAP: Microsoft's measurement date (Dec 31, 2025) falls in a different calendar year than its fiscal year-end (June 30, 2026). |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | approximately $1.9 trillion as of June 30 2025 | USD trillions | as of June 30 2025 | As of June 30, 2025, the aggregate market value of shares held by non-affiliates of the registrant (based upon the closing sale prices of such shares on the Nasdaq Global Select Market on June 30, 2025) was approximately $1.9 trillion. |  |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | approximately $1.6 trillion as of June 30 2025 | USD trillions | as of June 30 2025 | The aggregate market value of the voting and non-voting stock held by non-affiliates of the registrant as of June 30, 2025, the last business day of the registrant's most recently completed second fiscal quarter, was approximately $1.6 trillion |  |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $2,118,061,430,046 as of June 30 2025 | USD | as of June 30 2025 | Aggregate market value of voting stock held by non-affiliates of the registrant as of June 30, 2025 \| $2,118,061,430,046 | UNITS: whole dollars. |

### T4 *(tricky: footnote)*

How much revenue (net sales) did the company attribute to the United States alone for its most recent fiscal year?

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | $167,746 million | USD millions | fiscal year ended September 26 2026 | U.S. \| $167,746 \| $151,790 \| $142,196 | From the country table in Note 13 (Segment Information). Do not confuse with the 'Americas' segment, which includes Canada and Latin America. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | $170,794 million | USD millions | fiscal year ended June 30 2026 | Includes billings to OEMs and certain multinational organizations because of the nature of these businesses and the impracticability of determining the geographic source of the revenue. \|\| Revenue, classified by the major geographic areas in which our customers were located, was as follows: \|\| Year Ended June 30, \| 2026 \| 2025 \| 2024 \|\| United States (a) \| $170,794 \| $144,546 \| $124,704 | FOOTNOTE: footnote (a) qualifies the U.S. figure (includes some OEM/multinational billings). Still the reported U.S. figure. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $194,229 million | USD millions | year ended December 31 2025 | United States \| $146,286 \| 47% \| $170,447 \| 49% \| $194,229 \| 48% | Columns 2023 \| % \| 2024 \| % \| 2025 \| %. The percentage cells are a trap. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | $74.78 billion (U.S. only; from footnote) | USD billions | year ended December 31 2025 | United States and Canada (1) \| $78,866 \| $63,207 \| $52,888 \|\| (1)United States revenue was $74.78 billion, $59.73 billion, and $49.78 billion for the years ended December 31, 2025, 2024, and 2023, respectively. | FOOTNOTE TRAP: the table row is 'United States and Canada' ($78,866M). The U.S.-only figure exists only in footnote (1). $78,866M is WRONG. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $489,657 million | USD millions | year ended December 31 2025 | United States \| $395,637 \| $438,015 \| $489,657 | From 'Net sales attributed to countries' (Note 10). Do not confuse with the North America segment. |

### T5 *(tricky: insufficient_evidence)*

As of the last day of the fiscal year covered by this 10-K, what amount was borrowed or outstanding under the company's unsecured revolving credit facility or facilities (committed bank credit agreements)? Exclude commercial paper, secured credit facilities, and other short-term credit facilities.

| Company | Expected | Unit | Period | Supporting passage / table cells | Note |
|---|---|---|---|---|---|
| [Apple 10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | INSUFFICIENT EVIDENCE - Apple's 10-K describes no revolving credit facility | - | - | - | Checked: no 'revolving' / 'credit facility' / 'credit agreement' text in the extracted filing. Apple discusses commercial paper and term debt only; citing those as a revolver balance is wrong. |
| [Microsoft 10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | INSUFFICIENT EVIDENCE - Microsoft's 10-K describes no revolving credit facility | - | - | - | Checked: no revolving-credit-facility text in the extracted filing. |
| [Alphabet 10-K](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | $0 - no amounts borrowed under $10.0B of revolving credit facilities | USD billions | as of December 31 2025 | As of December 31, 2025, we had $10.0 billion of revolving credit facilities, $4.0 billion expiring in April 2026 and $6.0 billion expiring in April 2030. No amounts have been borrowed under the credit facilities. | Answerable (zero). The $10.0B capacity is a trap. |
| [Meta 10-K](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | INSUFFICIENT EVIDENCE - Meta's 10-K describes no revolving credit facility | - | - | - | Checked: no revolving-credit-facility text in the extracted filing. |
| [Amazon 10-K](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | $0 - no borrowings under the two unsecured revolving credit facilities | USD billions | as of December 31 2025 | We had no borrowings outstanding under the two unsecured revolving credit facilities or the commercial paper programs as of December 31, 2025. | DECIDED (reviewer, 2026-11-22): $0 kept because the provided excerpt (AMZN-0073) states it for exactly the facilities the question names - the two unsecured revolving credit facilities ($15.0B Credit Agreement and $5.0B 364-day Short-Term Credit Agreement) - as of December 31, 2025, Amazon's fiscal year-end. The $455M belongs to 'other short-term credit facilities', which the question now excludes. Also excluded: a secured revolving facility terminated in 2024. Capacity figures ($15.0B, $5.0B) are traps. |
