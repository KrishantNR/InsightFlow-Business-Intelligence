# InsightFlow — Business Intelligence & Decision Support

[![CI](https://github.com/krishant0811/InsightFlow-Business-Intelligence/actions/workflows/ci.yml/badge.svg)](https://github.com/krishant0811/InsightFlow-Business-Intelligence/actions/workflows/ci.yml)

> **Live application:** [Open InsightFlow](<https://insightflow-business-intelligence-gshfmqhusvcelq9nffulmy.streamlit.app/>). Hosted on Streamlit Community Cloud; the URL was supplied by the project owner.

InsightFlow is an individual Business Analytics capstone prototype that turns CSV and Excel data into an analytical workspace with data profiling, KPI exploration, interactive charts, exploratory forecasting, data-quality checks, recommendations, and a conversational analyst using a controlled set of Python analytics tools.

## Project

- **Source code:** [Open the application folder](InsightFlow_GitHub_Release/)
- **Project documentation:** [Read the detailed README](InsightFlow_GitHub_Release/README.md)
- **AI agent implementation:** [insightflow_agent.py](InsightFlow_GitHub_Release/insightflow_agent.py)
- **Application entry point:** [app.py](InsightFlow_GitHub_Release/app.py)
- **Technical architecture:** [AI agent architecture](InsightFlow_GitHub_Release/docs/AI_AGENT_ARCHITECTURE.md)
- **Data dictionary:** [Dataset fields and definitions](InsightFlow_GitHub_Release/docs/DATA_DICTIONARY.md)
- **Evaluation protocol:** [How to evaluate the prototype](InsightFlow_GitHub_Release/docs/EVALUATION_PROTOCOL.md)

## Main capabilities

- CSV and Excel ingestion, normalization and dataset profiling.
- Executive overview, data studio and interactive Plotly visual exploration.
- Nine chart types, descriptive statistics, correlation and IQR outlier screening.
- Exploratory linear-regression forecasts with limitations.
- Conversational analyst with twelve allowlisted analytical tools.
- Optional OpenAI Responses API integration with tool calling and session-based threads.
- Rule-based recommendations and CSV/Markdown/TXT exports.
- Local Windows launcher, self-tests and automated GitHub Actions checks.

## Run locally

1. Install Python 3.11 or newer.
2. Download or clone this repository.
3. Open the `InsightFlow_GitHub_Release` folder.
4. On Windows, double-click `START_INSIGHTFLOW.bat`.

Or run from the repository root:

```bash
python -m pip install -r InsightFlow_GitHub_Release/requirements.txt
python InsightFlow_GitHub_Release/launch_insightflow.py
```

See the [full setup guide](InsightFlow_GitHub_Release/README.md#quick-start--windows).

## Live website and deployment

**Live application:** [https://insightflow-business-intelligence-gshfmqhusvcelq9nffulmy.streamlit.app/](https://insightflow-business-intelligence-gshfmqhusvcelq9nffulmy.streamlit.app/)

The source code is maintained in this GitHub repository and the interactive Python application is hosted on [Streamlit Community Cloud](https://share.streamlit.io/). The deployed entry point is `InsightFlow_GitHub_Release/app.py` on branch `main`. The project owner selected Python 3.14 in the Streamlit deployment settings.

To open the app, use the live link above. To review the source, tests and documentation, browse the project folder in this repository. Streamlit's [deployment guide](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy) documents the repository/branch/entry-point setup.

## AI and data security

The local analytical mode works without an API key. LLM-assisted analysis requires the user's own OpenAI API key. Do not commit API keys or private secrets. Do not add a personal API key as a shared secret to an unauthenticated public app: visitors could consume your API credits. Review the [security notes](InsightFlow_GitHub_Release/SECURITY.md) before deploying.

## Current limitations

This is an academic prototype, not a production enterprise service. It does not provide user authentication, tenant isolation, persistent chat storage, unrestricted SQL/Python execution or guaranteed causal reasoning. Forecasts are exploratory. The bundled Tesla sample has five annual observations and is not suitable for robust forecasting.

## Academic integrity

The repository is a foundation for an individual capstone. Add your own real design decisions, evaluation results, screenshots, user feedback and reflection. Describe only features and testing you have personally verified, and follow your university's policy on AI-assisted development.
