# InsightFlow AI Analyst Architecture

## Design principle

InsightFlow is calculation-first: the model interprets the request and selects analytical tools, while deterministic Python functions calculate dataset evidence. The model is not given arbitrary Python, SQL, shell or filesystem execution capabilities.

## Request lifecycle

1. **User input:** a question is submitted in the active session thread.
2. **Context assembly:** the agent receives a bounded recent conversation history, dataset label, row/column counts, field names/types, numeric/categorical field metadata and the current question.
3. **Consent boundary:** the UI requires explicit consent before calling OpenAI. Without a key, consent or remaining request budget, the local analyst is used.
4. **Planning and tool selection:** the model calls one or more strict-schema function tools.
5. **Local execution:** `execute_analytics_tool()` dispatches only registered names and validates requested fields against the active DataFrame.
6. **Tool result return:** JSON-safe, bounded calculation outputs are returned to the Responses API using the original `call_id`.
7. **Synthesis:** the model returns a strict structured answer with direct answer, summary, findings, implications, recommended actions, limitations and follow-up questions.
8. **Presentation:** the UI displays the answer, model/request/token metadata, tool trace and optional web sources.

## Available tools

| Tool | Role |
|---|---|
| `inspect_dataset` | dimensions, types, missingness, unique counts |
| `aggregate_metric` | sum/mean/median/min/max/count/std; optionally grouped |
| `compare_periods` | period-by-period aggregate comparison |
| `correlation_matrix` | Pearson correlation among numeric fields |
| `forecast_metric` | exploratory 1–5 period linear extrapolation |
| `categorical_distribution` | category record counts and shares |
| `data_quality_report` | missingness, duplicate rows and IQR outlier screen |
| `segment_contribution` | grouped metric sums and share of total |
| `numeric_profile` | distribution statistics and IQR flags |
| `growth_analysis` | adjacent-period growth and valid positive-endpoint CAGR |
| `cross_tabulate` | bounded two-dimension frequency counts |
| `ratio_analysis` | ratio-of-sums or mean-of-ratios, optionally grouped |

All function tools use strict JSON schemas. Strict function calling requires every declared parameter to be required and `additionalProperties` to be false; nullable fields represent optional values. See [OpenAI function calling](https://developers.openai.com/api/docs/guides/function-calling).

## Model capabilities exposed by the UI

- Model profiles: GPT-6 Astra, GPT-6.1 Sol, GPT-6.1 Terra, GPT-6 Luna and a custom model ID.
- Reasoning effort: low, medium, high, xhigh and max, subject to model support.
- Reasoning mode: standard or pro for supported GPT-6 models.
- Answer depth: Balanced, Detailed or Deep dive.
- Optional OpenAI-hosted web search for public external context; disabled by default.
- Structured JSON-schema answer format.
- Bounded tool-call rounds and a per-session Responses API request counter.
- Token usage, model ID, response ID, tool log and source metadata available in the analysis trace.

Model features differ by ID and can change. Confirm current capabilities in the [OpenAI model catalogue](https://developers.openai.com/api/docs/models).

## Data sent outside the app

When LLM mode is used, the request includes the user's question, a bounded amount of recent conversation text, dataset label and field metadata, and local analytics tool outputs. It does not pass the full active DataFrame or raw row samples through the agent's initial context or registered tool outputs.

However, aggregated values may still be commercially sensitive. The user must explicitly consent. Do not use this workflow with confidential or regulated data without the data owner's approval and an appropriate privacy/security review. If optional web search is enabled, public search queries are sent to the hosted search tool; do not include private company details in those questions.

## Execution controls

- Responses API requests set `store=False` to disable application-state storage for these response objects. This is not a Zero Data Retention guarantee; provider abuse-monitoring retention and hosted-tool handling are separate. Review the current [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data).

- Only a fixed allowlist of local analytics functions can be invoked.
- No model-generated code is executed.
- Tool rounds and total API request attempts are bounded.
- `max_retries=0` avoids hidden SDK retries exceeding the app's request-attempt counter.
- Tool results are converted to JSON-safe values and truncated before being sent back.
- Known personal/account-identifying dimension names are blocked from grouping and cross-tab operations. This name-based check is heuristic, not a complete privacy classification system.
- Changing the selected dataset resets the active conversation to avoid reusing old-company context.
- When LLM mode is unavailable or fails, the app falls back to local analytical responses.

## Accuracy and limitations

The LLM is responsible for interpretation, not arithmetic authority. Numeric statements should be traceable to tool outputs. Correlation is not causation. Forecasts use simple linear regression and are exploratory. Tool outputs depend on field resolution and on the meanings/units of uploaded columns; ambiguous fields require user review.

Threads are held in Streamlit session state only. There is no durable chat database, authentication, tenant separation or per-user cloud identity in this release.
