# Right Quote, Wrong Answer? Testing AI on Financial Filings

Raeya Kumar

First-year Business Analytics student, Penn State

Independent study inspired by Hebbia's Matrix; not affiliated with or endorsed by Hebbia

Experiment run November 22, 2026

## Abstract

When an AI model extracts figures from company filings, can a reader trust both the number and the citation behind it? This study compares two ways of asking the same model the same financial questions. The pooled method asks about five companies in one request, while the company-by-company method sends a separate request for each company. Both received identical excerpts. Across 75 comparisons, the methods agreed every time, with 71 identical numerical answers after ignoring sign and four shared decisions not to answer. Agreement does not establish that an answer is correct or supported. Under the original scoring rules, which also required supporting evidence for each numerical claim, 70 outcomes were verified for the pooled method and 69 for the company-by-company method. For this model and these filings, separating the companies did not improve performance. Most unverified outcomes came from limits in the automatic scoring or the benchmark itself, which suggests that checking a citation deserves as much attention as producing the answer.

## 1. Introduction

A financial figure is useful only when a reader knows exactly what it measures. Meta's 2025 annual report shows why this can be difficult. Its revenue table reports $78,866 million for the United States and Canada combined, while a footnote reports $74.78 billion for the United States alone ([Meta Platforms, 2026, Note 2](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm)). A model asked for U.S. revenue could copy the table row word for word and still be wrong by about $4.1 billion. The quote would be genuine, but it would not support a claim about the United States alone. I included this case as a benchmark challenge. In the saved outputs, neither method made the mistake: both answered $74.78 billion and quoted the footnote.

The example raises a question about how a model should be given its evidence. When passages from several companies appear together, the model must keep track of which figure belongs to which company, year, and unit. Asking about one company at a time removes the other companies from view, so I expected it to reduce confusion. It also repeats the instructions in every request, which adds cost.

I therefore asked whether, when the same model receives the same evidence, answering one company at a time increases the share of financial claims that are correct and supported by their citations. I also asked what each additional verified answer would cost. Giving both methods identical excerpts made the comparison fair because neither could benefit from finding better passages. The remaining difference was whether a company's excerpts were presented alone or alongside those of the other four.

Two earlier studies motivate this design. FinanceBench tested 16 model configurations on 150 questions about public companies and found frequent errors and refusals (Islam et al., 2023). Gao et al. (2023) evaluated whether models that write answers with citations are fluent, correct, and adequately supported by the passages they cite. This experiment asks a narrower question: if the excerpts are held fixed, does presenting companies together or separately change whether an answer is correct and supported?

## 2. Methods

### Filings and evidence

The sample contains the most recent Form 10-K available on the run date for five large technology companies (Table 1). Because their fiscal years end at different times, a question about fiscal year 2025 refers to the prior-year column for Apple and Microsoft and the latest column for the other three.

Table 1. Filings used. Each company name links to the exact SEC document.

| Company | Fiscal year end | Filing date | SEC accession number |
|---|---|---|---|
| [Apple](https://www.sec.gov/Archives/edgar/data/320193/000032019326000026/aapl-20260926.htm) | September 26, 2026 | November 3, 2026 | 0000320193-26-000026 |
| [Microsoft](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm) | June 30, 2026 | July 29, 2026 | 0001193125-26-323660 |
| [Alphabet](https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm) | December 31, 2025 | February 5, 2026 | 0001652044-26-000018 |
| [Meta](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm) | December 31, 2025 | January 29, 2026 | 0001628280-26-003942 |
| [Amazon](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm) | December 31, 2025 | February 6, 2026 | 0001018724-26-000004 |

Each filing was converted to text in a way that kept table rows, years, units, and footnotes together where possible, and then divided into excerpts of roughly 1,800 characters. For each question, BM25, a method that ranks passages by keyword overlap, selected five excerpts per company. Some search queries were adjusted during development, before the final run, after a check against the answer key showed missing passages. The selected excerpts were then frozen, so the results describe answering from prepared evidence and not the difficulty of finding it.

### Questions and answer key

The benchmark asks 15 questions about each of the five companies, which produces 75 comparisons. Ten questions cover standard measures such as net income and operating cash flow. Five were designed to be difficult: diluted share counts reported in different units, revenue for a specified fiscal year, market value measured at mid-year, U.S. revenue that may depend on a footnote, and a credit-facility balance that three of the filings do not provide.

Two of the ten standard questions form a matched pair. One asks how much stock a company repurchased, and the other asks how much it was still authorized to repurchase. They use the same excerpts, so a genuine quotation can support one answer but not the other.

Claude Code, an AI coding assistant, drafted the questions and answer key and built the experiment. I decided how to treat seven flagged answer-key cells and approved the key before the final run. A script confirmed that each supporting passage in the key appeared word for word in the filing text. The key was never included in a model prompt, and the questions, excerpts, prompts, and scoring rules were frozen before the run.

### Two ways of presenting the evidence

The pooled method sent one request per question containing the excerpts for all five companies, for 15 requests in total. The company-by-company method sent one request for each company and question, for 75 requests. A check of the saved prompts confirmed that all 75 sets of company excerpts matched their counterparts in the pooled prompts.

Both methods used Gemini 3.8 Flash with the same instructions, output format, and settings: temperature 0, top-p 1, seed 7, low thinking, and a limit of 8,192 output tokens. A token is a small unit of text used for model processing and billing. The model had to rely only on the excerpts, cite one excerpt with a word-for-word quote, state the unit and period, and report insufficient evidence instead of guessing.

### Scoring

Every numerical answer received three checks:

- **Answer accuracy:** The value and unit agree with the answer key within 0.1 percent, or 0.01 percent for per-share amounts. Signs are ignored because filings often show cash outflows as negative numbers.
- **Quote match:** The quotation appears in the cited excerpt, ignoring differences in capitalization and spacing.
- **Citation support:** The excerpt belongs to the right company, and the quote contains the claimed value at the right scale and for the year in the answer key.

A numerical answer is verified only when it passes all three. A decision not to answer is verified only when the answer key also expects one, and it needs no quotation. When the rules could not settle citation support, the result was marked unclear and did not count as verified. The support check compares the quote with the expected year; it does not separately grade the period the model wrote.

After the run, Claude Code reviewed the nine answers whose support had been marked unclear or failed, comparing each citation with the original SEC filing. This was a follow-up AI-assisted review by the same assistant that built the benchmark, and no independent human verification is reported. It did not change the original scores.

## 3. Results

### Agreement and verification

All 90 requests completed without an error or retry. The methods agreed in all 75 comparisons. They gave 71 numerical answers with the same magnitude and both declined to answer in the other four. In two of the 71, the company-by-company method wrote capital spending as a negative number, which the scoring rules treated as equivalent.

Verification was slightly lower than agreement because it also requires accuracy and support. The original rules verified 70 of 75 outcomes for the pooled method and 69 of 75 for the company-by-company method (Table 2). Each total includes three correct decisions not to answer. The single difference was Alphabet's operating income, where both methods gave the same correct number but cited different tables, and the scorer could not interpret the one cited by the company-by-company method.

Table 2. Verified outcomes out of 75. The original scoring is the main result.

| Scoring | Pooled | Company-by-company | Both | Pooled only | Company only | Neither |
|---|---|---|---|---|---|---|
| Original rules | 70 | 69 | 69 | 1 | 0 | 5 |
| After AI-assisted review | 72 | 72 | 72 | 0 | 0 | 3 |
| After review and key correction | 73 | 73 | 73 | 0 | 0 | 2 |

An exact McNemar test, which compares paired outcomes using only the cases where the methods differ, gives p = 1.0 for the original scores. With one differing case, the test cannot detect a difference; at least six, all in the same direction, would be needed for a two-sided p-value below 0.05. The comparisons also share questions and companies, so they are not fully independent. The result shows no evidence of an advantage here, but it does not show that the methods are equivalent in general.

### Difficult questions and unanswered cases

On the five difficult questions, both methods were correct in all 25 cases and verified in 23. In the Meta example, both selected the U.S.-only footnote. On the matched pair, each method was correct in nine of ten cases and verified in eight under the original rules. The one case scored incorrect was Microsoft's repurchase amount. Both methods reported $16,719 million from a detailed table, but the answer key contained the rounded figure of $16.7 billion, and the 0.11 percent gap exceeded the allowed tolerance.

Each method declined to answer four times. Three of these matched the answer key. The fourth concerned Alphabet's diluted earnings per share. The question asked for the figure reported on the income statement, but the excerpts contained only a note with the same figure. This was a flaw in the question, and the case still counts as incorrect in every row of Table 2.

### Why some citations were not verified

Every numerical answer included a quotation that appeared in its cited excerpt. However, the automatic support check did not pass nine of the 142 numerical answers. The follow-up AI-assisted review judged seven of these supported. The checker could not interpret some tables with extra columns and missed one unit description. The other two were judged inconclusive. Both methods cited the correct Alphabet share count, but the unit appeared only in a neighboring excerpt that they received and did not cite.

The second row of Table 2 uses those judgments, and the third also accepts Microsoft's exact figure. These rows help explain the original results but do not replace them, because both changes were made after the outputs were known.

### Cost and time

The company-by-company method cost an estimated $0.198, compared with $0.185 for the pooled method, an increase of 6.9 percent (Table 3). It used 11.0 percent more input tokens, which is consistent with repeating the instructions in more requests. The cost per additional verified answer is not reported because the more expensive method produced no additional verified answers under any scoring row.

Table 3. Resource use for the final run. Costs are estimates based on token counts and list prices.

| Measure | Pooled | Company-by-company |
|---|---|---|
| Requests | 15 | 75 |
| Input tokens | 190,801 | 211,697 |
| Output tokens, including thinking | 11,237 | 10,455 |
| Estimated cost | $0.185 | $0.198 |
| Mean time per question, run in sequence | 6.9 seconds | 15.7 seconds |

Prices were $0.75 per million input tokens and $3.75 per million output tokens on the run date. If each question's five company requests had run at the same time, the slowest would have averaged 4.6 seconds. That figure is an estimate, since the requests were sent one after another.

## 4. Limitations

The study is small and covers five large technology companies, one model, and one run per method. A temperature of 0 does not guarantee the same output every time. The pooled requests averaged only 12,720 input tokens, so the results may not extend to more companies, longer documents, or companies that are easier to confuse.

The evidence was prepared to make most questions answerable, and some retrieval choices were informed by the answer key during development. The same AI assistant drafted the key, built the scoring code, and conducted the follow-up review. This creates a risk of shared errors that an independent reviewer could reduce.

The scorer itself was imperfect. It was tested on answers taken directly from the key, where it verified 148 of 150 and left two unclear, both for the Alphabet share count discussed above. It verified none of 64 deliberately incorrect answers, although its support check alone passed one of them. The 133 citations that passed automatically in the final run were not reviewed again. Human verification time was not measured.

## 5. Conclusion

For these five filings and this model, asking about one company at a time did not increase the number of verified answers, and it cost slightly more. The methods agreed throughout, yet agreement alone did not show that their answers were supported. The unverified cases pointed instead to weaknesses in the scoring rules, answer key, question wording, and, for one company, the citation itself. A useful next step would be to increase the number and similarity of companies in each request while having an independent person review the citations.

## Data and code note

The [project repository](https://github.com/raeyakumar/hebbia-matrix-benchmark) contains the prompts, frozen excerpts, full output format, raw responses, scores, and instructions for reproducing the study. It also records file hashes and the [commit that froze the benchmark](https://github.com/raeyakumar/hebbia-matrix-benchmark/commit/bdebd2a) before the final run.

## References

Gao, T., Yen, H., Yu, J., & Chen, D. (2023). Enabling large language models to generate text with citations. Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, 6465–6488. [https://doi.org/10.18653/v1/2023.emnlp-main.398](https://doi.org/10.18653/v1/2023.emnlp-main.398)

Islam, P., Kannappan, A., Kiela, D., Qian, R., Scherrer, N., & Vidgen, B. (2023). FinanceBench: A new benchmark for financial question answering. arXiv. [https://arxiv.org/abs/2311.11944](https://arxiv.org/abs/2311.11944)

Meta Platforms, Inc. (2026). Form 10-K for the fiscal year ended December 31, 2025. Note 2, Revenue: revenue by geography table and footnote 1. U.S. Securities and Exchange Commission. [SEC filing](https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm)
