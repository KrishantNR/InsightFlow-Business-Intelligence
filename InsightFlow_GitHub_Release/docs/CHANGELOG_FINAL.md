# InsightFlow — GitHub release candidate

Release preparation date: 2026-11-06

## Final security and quality pass

- Sets `store=False` on Responses API calls to disable response application-state storage. This is not a Zero Data Retention guarantee.
- HTML-escapes data-derived text before placing it in trusted presentation markup.
- Normalizes non-finite numeric values to missing values during cleaning.
- Hardens CSV formula-prefix neutralization for text cells with leading whitespace.
- Reports correlation sample counts pair by pair rather than presenting a full-table complete-case count as if it applied to every pair.
- Refactored Visual Explorer chart creation into a tested production helper; Pie and Treemap refuse negative or non-positive value sets.
- Re-ran the test suite: 30 pytest tests and 60 bundled self-test checks passed in the available build environment.

## AI Analyst

- Uses the OpenAI Responses API with strict-schema function calling and structured JSON answer output.
- Exposes twelve bounded Python analytics tools: dataset inspection, aggregation, period comparison, correlations, forecasting, categorical distribution, data-quality report, segment contribution, numeric profile, growth analysis, cross-tabulation and ratio analysis.
- Adds GPT-6 Astra, GPT-6.1 Sol, GPT-6.1 Terra and GPT-6 Luna model profiles plus custom model ID.
- Adds reasoning effort/mode, answer-depth, tool-round and request-budget controls.
- Keeps optional web search disabled by default and displays returned source links when enabled.
- Requires explicit consent before sending questions, recent thread context, metadata and tool outputs to OpenAI.
- Resets conversational context when the selected dataset changes.
- Retains a local Python fallback when LLM mode is unavailable or fails.

## Data and UI

- Retains the dark enterprise theme and eight workspaces.
- Adds/retains nine Plotly visualization types, data health and IQR outlier screening.
- Neutralizes spreadsheet formula prefixes in text cells during CSV exports.
- Keeps CSV/XLSX/XLS file ingestion; Excel currently reads the first worksheet.
- Includes Tesla 2021–2025 and illustrative retail demo data.

## Engineering and release hygiene

- Adds GitHub Actions quality workflow across Python 3.11–3.13 on Ubuntu and Windows.
- Adds an actual Streamlit HTTP health smoke test to the Ubuntu CI job.
- Adds Dependabot configuration and a local secret-pattern scanner.
- Adds security, contribution, GitHub beginner, API configuration, architecture, evaluation, data notes and data dictionary documentation.
- Improves `.gitignore` and adds Streamlit theme configuration/secrets example.

## Verification status

At final release preparation, 30 pytest tests, 60 project self-test checks, Python compilation, YAML parsing, CSV structure checks and repository secret-pattern scan passed in the available environment. The live Streamlit HTTP smoke test and a real OpenAI API request require a network-enabled runner and user API key; they are not claimed as locally verified.
