# InsightFlow OpenAI API configuration guide

This guide explains how the optional LLM analyst is configured and how to choose settings for a capstone demo. Model names, availability, capabilities and prices can change; check the linked official documentation before a live presentation.

## What InsightFlow uses

InsightFlow uses the OpenAI **Responses API** for a bounded tool-calling workflow:

1. The application assembles the user's question, recent thread messages, dataset label and field metadata after explicit consent.
2. The selected model can request one or more of twelve strict-schema analytical functions.
3. InsightFlow executes the function locally in Python against the active DataFrame. It does not execute model-generated Python, SQL, shell commands or filesystem requests.
4. Bounded numerical results are returned to the model.
5. The model returns a structured business analysis with a direct answer, executive summary, findings, implications, recommendations, limitations and follow-up prompts.
6. Optional hosted web search can add public external context and source links. It is disabled by default.

This design combines model interpretation with reproducible local calculations. It intentionally does not send the complete DataFrame or raw sample rows through the registered analytics tools. Aggregated values and field metadata can still be sensitive.

## Twelve analytics functions

- `inspect_dataset` — dimensions, field names/types, missingness and unique counts.
- `aggregate_metric` — sums, means, medians, min/max, counts and standard deviation; optional grouping.
- `compare_periods` — period-by-period numeric comparisons.
- `correlation_matrix` — Pearson associations with pairwise observation counts.
- `forecast_metric` — exploratory linear extrapolation for one to five future periods.
- `categorical_distribution` — frequency counts and record shares.
- `data_quality_report` — missing cells, duplicate records and optional IQR screen.
- `segment_contribution` — grouped metric totals and share of the signed total.
- `numeric_profile` — distribution statistics, skew, zeros, negatives and IQR flags.
- `growth_analysis` — adjacent period growth and positive-endpoint CAGR.
- `cross_tabulate` — bounded frequency cross-tabulation of two dimensions.
- `ratio_analysis` — ratio-of-sums or mean-of-ratios, optionally grouped.

All tools validate requested fields against the active DataFrame and return JSON-safe, bounded outputs. Sensitive-dimension checks are heuristic, not a full PII classifier.

## Model profiles and recommended use

| Profile | Use | Suggested starting settings |
|---|---|---|
| GPT-6 Astra | Highest-quality complex analysis, multi-step research and difficult business questions | Standard mode, `high`; use `pro` + `xhigh`/`max` selectively after evaluation |
| GPT-6.1 Sol | Strong analysis at a lower cost than Astra | Standard, `medium` or `high`; compare `pro` on important questions |
| GPT-6.1 Terra | Faster responses and lighter analysis | Standard, `medium` |
| GPT-6 Luna | Cost-sensitive repeated or routine analysis | Standard, `low` or `medium` |
| Custom model ID | Use a model enabled in your own API project | Confirm its supported parameters in the model catalogue |

For the most demanding capstone demonstration, a reasonable quality-first test profile is **GPT-6 Astra + Pro mode + High reasoning + Deep dive answer depth + up to six tool rounds**. Use Max only when an evaluation on representative questions shows a real improvement. This setting can be slower and more expensive. For regular development and repeated testing, start with GPT-6.1 Sol at Medium/High in Standard mode.

Do not assume that your API project has access to every model. The in-app **Test API key + model access** button calls the model lookup endpoint. Availability, account tier, rate limits and billing are controlled by the API project.

Official references:

- [OpenAI model catalogue](https://developers.openai.com/api/docs/models)
- [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model)
- [Reasoning models and effort/mode](https://developers.openai.com/api/docs/guides/reasoning)
- [Function calling and strict schemas](https://developers.openai.com/api/docs/guides/function-calling)
- [Responses API web search](https://developers.openai.com/api/docs/guides/tools-web-search)
- [API pricing](https://developers.openai.com/api/docs/pricing)

## Feature controls

### Reasoning effort and mode

Reasoning effort controls how much additional reasoning the model applies. Reasoning mode selects Standard or Pro execution for supported models. They are separate controls. Use `medium` or `high` as normal baselines; reserve `xhigh` and `max` for quality-critical prompts where evaluation justifies the cost and latency. Unsupported options can be rejected by the API for a given model; the exact model's documentation is authoritative.

### Structured output

The final analyst response follows a strict JSON Schema. The UI formats that structured result into sections. This makes the response easier to validate and display, but structured output does not guarantee that the claims are factually correct; numerical claims still need to match tool evidence.

### Function calling

Only InsightFlow's twelve named local functions can be called. The application dispatches exact tool names and validates fields. No arbitrary generated code is run. Strict schemas reduce malformed arguments, while the Python functions remain responsible for validating the underlying request and its data.

### Web search

Enable web search only when public context is genuinely useful—for example, comparing company results with current public industry information. Do not put confidential values, private company names, customer details or personal data into search queries. Keep dataset-derived calculations distinct from external facts and inspect source links before citing them.

## API key setup

### Local Windows setup

Recommended options:

1. Enter the key in the password field in the sidebar for the current Streamlit session; or
2. Set `OPENAI_API_KEY` in your local environment; or
3. Create `.streamlit/secrets.toml` from `.streamlit/secrets.toml.example` and store the key there.

The actual key must never appear in Python source, README files, screenshots, GitHub issues, commits, or the public repository. `.gitignore` excludes `.streamlit/secrets.toml` and `.env` files. The example secrets file contains placeholders only.

### Public hosting

Do not put your personal key in the shared secrets of a public, unauthenticated demo. Every visitor may otherwise cause usage billed to your account. For a student portfolio demo, leave the shared key unset and let visitors use local analytical mode or enter their own API key for their session. A shared-key public service needs authentication, user-level authorization, server-side quotas, abuse monitoring and a secure backend before it is appropriate to expose.

## Cost and request limits

InsightFlow bounds the number of API attempts and tool rounds for each question, and maintains a per-session request counter. These are application safeguards—not a hard currency spending cap. They do not cap other browser sessions, other projects using the same key, separate web-search tool costs, or spending outside InsightFlow.

Use a dedicated API project/key for this capstone. Configure provider-side usage budgets/alerts, monitor token and tool usage, and revoke the key if it is exposed. Pro mode, high reasoning effort, deep outputs and web search can materially increase token usage, tool charges or latency.

## Privacy and retention

The app asks for explicit consent before sending LLM context to OpenAI. The request contains the user's question, recent thread context, dataset label/field metadata and calculated tool outputs. It does not send the complete active DataFrame or raw row samples through registered analytics functions. Derived values may still be commercially sensitive.

Responses requests set `store=False` to disable Responses API application-state storage for these response objects. This **does not** mean Zero Data Retention. OpenAI documents separate abuse-monitoring retention and feature-specific exceptions; review the current [data controls documentation](https://developers.openai.com/api/docs/guides/your-data) and your organization's actual settings. Optional web search also sends public search queries to the hosted search tool.

Do not use real personal, employee, customer, confidential or regulated data in LLM mode without the data owner's authorization and a proper security/privacy assessment.

## Recommended capstone evaluation

Before presenting the LLM feature, run the same fixed evaluation questions against at least two model/effort profiles and record:

- Whether the correct analytics tools were called.
- Whether all numerical values match hand-calculated references.
- Whether limitations and unsupported fields are handled correctly.
- Whether correlation is distinguished from causation.
- Whether follow-up questions preserve the right period and metric context.
- Input/output/total tokens, request count, latency and estimated cost.
- Any hallucination, incorrect tool choice, incomplete caveat or failed response.

Use `docs/EVALUATION_PROTOCOL.md` and record real results in `docs/DEVELOPMENT_LOG_TEMPLATE.md`. Do not write that a model is "best" without comparing it on the same test set.
