# InsightFlow Evaluation Protocol

This document defines a repeatable evaluation plan for the capstone. Fill the result column after personally running each scenario. Do not treat a code-level unit test as proof of business validity or a live model test.

## 1. Evaluation dimensions

| Dimension | What to measure | Evidence to retain |
|---|---|---|
| Data ingestion | CSV/XLSX success, encoding, empty files, malformed input | test file, result, error screenshot if any |
| Cleaning | duplicate columns, blank rows/columns, whitespace, missing values | before/after row and column counts |
| Metric resolution | correct field selected for revenue, profit, headcount, deliveries | question, resolved field, expected field |
| Numerical accuracy | aggregates, period growth, ratios, ranks | hand-calculated reference and tool output |
| Agent tool use | appropriate tools selected; no unsupported tool calls | tool trace and model response ID |
| Answer grounding | no unsupported amounts, periods or causal statements | evidence-to-answer review |
| Conversation | follow-up resolves pronouns/period context; dataset switch resets context | thread screenshots and dataset fingerprints |
| Privacy | consent is required; keys absent from Git; raw rows excluded from agent context | secret-scan result and code review |
| Failure recovery | API timeout, invalid key, exhausted request budget, empty model response | expected fallback and trace |
| Usability | readable layout, clear upload and question controls, useful error copy | screenshots and user feedback |

## 2. Tesla reference scenarios

The bundled Tesla dataset contains five annual observations, 2021–2025, in a compact extract. Values below are USD millions unless stated otherwise.

| Question | Expected reference | Interpretation caution |
|---|---|---|
| Which year had the highest revenue? | 2024; 97,690 | Only the five years in this extract |
| What was revenue in 2025? | 94,827 | USD millions = USD 94.827B |
| How much did revenue change 2021–2025? | +41,004; approximately +76.18% | First-to-last change, not CAGR |
| What is simple linear 2026 revenue projection? | approximately 114,390 USD million, or 114.39B | Exploratory 5-observation linear trend, not company guidance |
| How many missing cells are in the dataset? | 5 | Blanks are not zero |
| What was storage deployed in 2025? | 46.7 GWh | Annual reported deployment measure |
| What was energy generation/storage revenue in 2025? | 12,771 USD million | Verify the source/field definition |
| Which region has most employees? | Unsupported | No employee concentration dataset/field is included |

## 3. Recommended non-Tesla evaluation dataset

Create a small, synthetic dataset with at least 24 monthly rows and fields such as `month`, `region`, `product_category`, `units_sold`, `revenue`, `cost`, `gross_profit`, and `employee_count`. Ensure every synthetic row is clearly labeled as synthetic. This allows monthly trend, segment share, growth, ratio, cross-tabulation and forecasting scenarios without presenting fabricated values as real company information.

## 4. Live API evaluation worksheet

For each model/effort profile, run the same questions and record:

- Model ID and reasoning effort/mode.
- Whether a function tool was called and whether it was the correct tool.
- Whether the numerical values exactly match a hand-calculated reference.
- Whether the answer explains business significance without claiming causality.
- Request count, input/output/total tokens when returned by the API.
- Latency and user-rated usefulness.
- Any hallucination, missing caveat or unsupported recommendation.

Use at least five question categories: overview, period comparison, segment contribution, ratio analysis and unsupported/missing-field question. Repeat the set on both Tesla and the synthetic retail dataset.

## 5. Suggested pass criteria

- 100% exact match for deterministic reference calculations within declared numeric tolerance.
- 0 invented figures in unsupported-field scenarios.
- 100% of causal prompts clearly distinguish association/trend from causal proof.
- Dataset changes reset the conversation before a new analytical turn.
- Every live API call is made only after consent and is counted toward the request budget.
- API or parsing failures return a clear message and local fallback where the local analyst supports the question.

Record failures as findings; do not hide failed scenarios. Add a new regression test when a bug is fixed.
