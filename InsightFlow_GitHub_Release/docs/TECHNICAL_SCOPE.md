# Technical scope and feature status

## Implemented

- Streamlit-based multi-workspace interface with a dark enterprise theme.
- CSV, XLSX and XLS ingestion; Excel reads the first worksheet.
- Data cleaning, duplicate-column removal, empty-row/column cleanup, non-finite-value normalization, spreadsheet-safe CSV exports and data profiling.
- Executive overview and numeric summaries.
- Data Studio preview, simple category filters and safe CSV export.
- Plotly Visual Explorer: line, area, bar, scatter, histogram, box, violin, pie and treemap.
- Data Health: missing values, duplicate rows and IQR outlier screening.
- Forecast Lab using simple Scikit-learn linear regression.
- Local deterministic analyst for common metric, period, quality and comparison question types.
- Twelve allowlisted local analytics functions for the optional Responses API agent.
- Responses API function calling, structured JSON output, model/reasoning controls, standard/pro mode for supported models, bounded rounds/request attempts, `store=False` application-state control and optional web search.
- Explicit data-sharing consent and local fallback.
- Session-only conversational threads; dataset changes reset thread context.
- Rule-based period-over-period signals and dataset/conversation exports.
- Windows one-click launcher, auto-port selection, self-test, pytest tests and GitHub Actions configuration.

## Not implemented / not claimed

- Arbitrary model-generated Python, SQL or shell execution.
- General relational-database connector or automatic multi-table joins/entity resolution.
- Persistent chat history, login/authentication, role-based access, tenant isolation or row-level security.
- Production monitoring, abuse prevention or per-user API billing enforcement.
- Guaranteed causal inference or production-grade time-series forecasting.
- Complete PII detection or automatic compliance with every data-protection regime.
- Live API verification for every selected model in the build environment.

## Design choices

- Analytics calculations remain in deterministic Python functions to make numeric outputs testable.
- The LLM receives schema/field metadata and tool outputs rather than the full raw DataFrame.
- Function calling is allowlisted and strict-schema validated.
- API consent is explicit; web search is opt-in.
- Request attempts are counted before sending, including failed attempts.
- A dataset fingerprint resets conversation context to prevent mixing results across datasets.
- Forecasts and recommendations are visibly caveated as exploratory/rule-based.
