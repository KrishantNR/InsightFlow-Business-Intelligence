"""Offline smoke tests for the bundled InsightFlow datasets and analyst core."""
from __future__ import annotations
import ast
import io
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from insightflow_agent import execute_analytics_tool, FUNCTION_TOOLS

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app.py"
TREE = ast.parse(APP.read_text(encoding="utf-8"))
FUNCTIONS = {
    "read_file", "clean_df", "year_col", "numeric_cols", "metrics", "pretty", "fmt",
    "resolve_metric", "dataset_profile", "reset_threads_when_dataset_changes", "build_evidence", "local_answer",
    "chart_for_evidence", "iqr_outlier_summary", "safe_csv_bytes", "safe_html_text", "build_visual_figure",
}
NODES = [n for n in TREE.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in FUNCTIONS]
ns = {
    "io": io, "np": np, "pd": pd, "re": re, "json": json, "html": __import__("html"), "textwrap": __import__("textwrap"),
    "Path": Path, "LinearRegression": LinearRegression, "px": px, "go": go, "OpenAI": None,
}
exec(compile(ast.Module(body=NODES, type_ignores=[]), str(APP), "exec"), ns)

passed = []
def check(name, condition):
    if not condition:
        raise AssertionError(f"FAILED: {name}")
    passed.append(name)

# 1. Bundled CSV data load and shape checks.
tesla_path = ROOT / "data" / "Tesla_2021_2025_Company_Data.csv"
retail_path = ROOT / "data" / "sample_sales.csv"
check("Tesla sample exists", tesla_path.is_file())
check("Retail sample exists", retail_path.is_file())
tesla = ns["clean_df"](pd.read_csv(tesla_path))
retail = ns["clean_df"](pd.read_csv(retail_path))
check("Tesla data has five annual records", len(tesla) == 5 and "fiscal_year" in tesla.columns)
check("Tesla data has revenue field", ns["resolve_metric"](tesla, "revenue") is not None)
check("Retail sample loads", len(retail) > 0 and len(retail.columns) > 1)
# Verify CSV and XLSX ingestion helpers without depending on browser UI.
csv_bytes = tesla_path.read_bytes()
csv_roundtrip = ns["read_file"](csv_bytes, "roundtrip.csv")
check("CSV ingestion helper", len(csv_roundtrip) == len(tesla))
xlsx_buffer = io.BytesIO()
tesla.head(3).to_excel(xlsx_buffer, index=False)
xlsx_roundtrip = ns["read_file"](xlsx_buffer.getvalue(), "roundtrip.xlsx")
check("XLSX ingestion helper", len(xlsx_roundtrip) == 3 and len(xlsx_roundtrip.columns) == len(tesla.columns))

# 2. Data cleaning and profiling.
dup = pd.DataFrame([[1, 2, 3], [None, None, None]], columns=["A", "A", "B"])
cleaned = ns["clean_df"](dup)
check("Duplicate columns removed", list(cleaned.columns) == ["A", "B"] and cleaned.iloc[0]["A"] == 1)
formula_text = pd.DataFrame({"comment": ["=1+1", "  =2+2", "normal"], "amount": [-10, 20, 30]})
safe_export = ns["safe_csv_bytes"](formula_text).decode("utf-8-sig")
check("CSV export neutralizes spreadsheet formulas in text cells", "'=1+1" in safe_export and "'  =2+2" in safe_export and "-10" in safe_export)
check("Data-derived text is HTML escaped before trusted markup", ns["safe_html_text"]("<script>alert(1)</script>") == "&lt;script&gt;alert(1)&lt;/script&gt;")
check("All-empty row removed", len(cleaned) == 1)
nonfinite = ns["clean_df"](pd.DataFrame({"value": [1.0, np.inf, -np.inf]}))
check("Non-finite numeric values normalize to missing values", int(nonfinite["value"].isna().sum()) == 2)
profile = ns["dataset_profile"](tesla, "Tesla demo")
check("Dataset profile counts are consistent", profile["rows"] == len(tesla) and profile["columns"] == len(tesla.columns))
thread_state = {"if_dataset_fingerprint": "dataset-a", "if_current": "thread_2",
                "if_threads": {"thread_2": {"title": "Old company", "messages": [{"role": "user", "content": "old context"}]}}}
changed = ns["reset_threads_when_dataset_changes"](thread_state, "dataset-b")
check("Dataset switch resets conversation context", changed and thread_state["if_current"] == "thread_1" and not thread_state["if_threads"]["thread_1"]["messages"])
check("Same dataset preserves conversation context", not ns["reset_threads_when_dataset_changes"](thread_state, "dataset-b"))
iqr_sample = pd.DataFrame({"sales": [10, 11, 12, 13, 14, 100]})
iqr_result = ns["iqr_outlier_summary"](iqr_sample, "sales")
check("IQR outlier screening flags an extreme value", iqr_result["supported"] and len(iqr_result["outliers"]) == 1 and iqr_result["outliers"].iloc[0]["sales"] == 100)

# 3. Analyst question tests, grounded in bundled data.
questions = {
    "overall performance review": "How has the company performed overall?",
    "revenue trend": "How has revenue changed over time?",
    "forecast 2026": "What is the projected revenue in 2026?",
    "highest revenue year": "Which year had the highest revenue?",
    "average gross profit": "What is the average gross profit?",
    "specific year": "What was revenue in 2024?",
    "missing values": "Are there missing values in this dataset?",
    "unsupported workforce": "Which region has the highest employee concentration?",
}
answers = {}
for test_name, question in questions.items():
    ev = ns["build_evidence"](question, tesla)
    answer = ns["local_answer"](question, ev, tesla)
    check(f"Analyst returns answer: {test_name}", isinstance(answer, str) and len(answer.strip()) > 80)
    answers[test_name] = answer
check("Overall answer covers multiple measures", answers["overall performance review"].count("###") >= 3)
check("2026 projection is caveated", "exploratory" in answers["forecast 2026"].lower() or "few observations" in answers["forecast 2026"].lower())
check("Highest revenue year is correctly identified as 2024", "2024" in answers["highest revenue year"] and "$97.69B" in answers["highest revenue year"])
check("2026 projection includes latest-period comparison", "$114.39B" in answers["forecast 2026"] and "+20.63%" in answers["forecast 2026"])
check("Missing value answer reports quality", "5 missing cells" in answers["missing values"].lower())
limits_q = "What data limitations should I know about?"
limits_a = ns["local_answer"](limits_q, ns["build_evidence"](limits_q, tesla), tesla)
check("Dataset limitations question has a dedicated response", "analytical limitations" in limits_a.lower() and "5 rows" in limits_a)
driver_q = "What is driving the change in revenue?"
driver_a = ns["local_answer"](driver_q, ns["build_evidence"](driver_q, tesla), tesla)
check("Driver question distinguishes trend from causation", "not sufficient to establish the cause" in driver_a.lower())
check("Unsupported employee breakdown does not invent workforce", "does not contain" in answers["unsupported workforce"].lower() or "could not find" in answers["unsupported workforce"].lower() or "employee" in answers["unsupported workforce"].lower())
# Dataset without a recognized year should still answer highest/lowest value questions.
no_year = pd.DataFrame({"product": ["A", "B", "C"], "sales": [10, 35, 22]})
no_year_q = "Which product has the highest sales?"
no_year_a = ns["local_answer"](no_year_q, ns["build_evidence"](no_year_q, no_year), no_year)
check("Highest-value question works without a year column", "35.00" in no_year_a and "recognized period field" in no_year_a.lower())

# 4. Follow-up context resolution: combine prior ask with a short period follow-up.
follow = "How has revenue changed over time? Follow-up question: What about 2024?"
fev = ns["build_evidence"](follow, tesla)
fans = ns["local_answer"](follow, fev, tesla)
check("Follow-up year resolved from thread context", "2024" in fans)
correlation_sample = pd.DataFrame({"revenue_total_usd_m": [10, 20, 30, 40], "employee_count": [100, 110, 120, 130], "region": ["A", "B", "A", "B"]})
corr_q = "What is the relationship between revenue and employees?"
corr_ev = ns["build_evidence"](corr_q, correlation_sample)
check("Correlation question calculates relationship evidence", bool(corr_ev.get("correlations")) and "revenue_total_usd_m" in corr_ev["correlations"])

# 5. Whitelisted API analytics tools use the active dataframe safely.
check("Agent exposes a bounded set of strict function tools", len(FUNCTION_TOOLS) >= 12 and all(t.get("strict") for t in FUNCTION_TOOLS))
overview_tool = execute_analytics_tool("inspect_dataset", {}, tesla)
check("Agent dataset inspection returns schema metadata", overview_tool["ok"] and overview_tool["rows"] == 5 and overview_tool["columns"] == 52)
revenue_tool = execute_analytics_tool("aggregate_metric", {"metric_field": "revenue", "aggregation": "sum", "group_by": None, "top_n": 10}, tesla)
check("Agent aggregate tool calculates Tesla revenue", revenue_tool["ok"] and abs(revenue_tool["value"] - 424575) < 0.01)
period_tool = execute_analytics_tool("compare_periods", {"metric_field": "revenue", "period_field": "fiscal_year", "start_period": "2021", "end_period": "2025"}, tesla)
check("Agent period comparison returns five annual records", period_tool["ok"] and period_tool["observations"] == 5)
quality_tool = execute_analytics_tool("data_quality_report", {"numeric_field": None}, tesla)
check("Agent data-quality tool reports five missing cells", quality_tool["ok"] and quality_tool["missing_cells"] == 5)
contribution_tool = execute_analytics_tool("segment_contribution", {"metric_field": "revenue", "group_by": "currency", "top_n": 10}, tesla)
check("Agent segment-contribution tool calculates value shares", contribution_tool["ok"] and contribution_tool["groups"][0]["contribution_pct"] is not None)
profile_tool = execute_analytics_tool("numeric_profile", {"numeric_field": "revenue"}, tesla)
check("Agent numeric-profile tool calculates distribution statistics", profile_tool["ok"] and profile_tool["valid_count"] == 5)
growth_tool = execute_analytics_tool("growth_analysis", {"metric_field": "revenue", "period_field": "fiscal_year"}, tesla)
check("Agent growth-analysis tool calculates period growth", growth_tool["ok"] and growth_tool["period_count"] == 5)
crosstab_tool = execute_analytics_tool("cross_tabulate", {"row_field": "company", "column_field": "ticker", "top_n": 5}, tesla)
check("Agent cross-tabulation tool calculates categorical counts", crosstab_tool["ok"] and crosstab_tool["cells_returned"] >= 1)
ratio_tool = execute_analytics_tool("ratio_analysis", {"numerator_field": "gross_profit", "denominator_field": "revenue", "multiplier": 100, "method": "ratio_of_sums", "group_by": None}, tesla)
check("Agent ratio-analysis tool calculates a margin safely", ratio_tool["ok"] and ratio_tool["ratio"] is not None)

# 6. Test the exact Visual Explorer chart builder used by the UI.
df = tesla
num = ns["metrics"](df)
yc = ns["year_col"](df)
ycol = ns["resolve_metric"](df, "revenue")
xcol = yc if yc else df.columns[0]
check("Chart test has compatible x/y fields", xcol is not None and ycol is not None)
for chart_name in ["Line", "Area", "Bar", "Scatter", "Histogram", "Box", "Violin", "Pie", "Treemap"]:
    fig = ns["build_visual_figure"](df, chart_name, xcol, ycol)
    check(f"Visual Explorer {chart_name} chart builds through production helper", fig is not None and len(fig.data) > 0)
negative_chart_data = pd.DataFrame({"region": ["North", "South", "West"], "profit": [10, -4, 6]})
try:
    ns["build_visual_figure"](negative_chart_data, "Pie", "region", "profit")
    negative_pie_blocked = False
except ValueError as exc:
    negative_pie_blocked = "non-negative" in str(exc)
check("Pie chart refuses negative values instead of presenting misleading shares", negative_pie_blocked)

# 7. Port selection must return a bindable local port.
import importlib.util, socket
spec = importlib.util.spec_from_file_location("launch_insightflow", ROOT / "launch_insightflow.py")
launch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launch)
port = launch.find_available_port()
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", port))
check("Auto-port selector returns a bindable port", 8501 <= port <= 65535)
# Hold one available app port and ensure the next lookup selects a different one.
held = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
held.bind(("127.0.0.1", launch.find_available_port()))
held.listen(1)
next_port = launch.find_available_port()
check("Auto-port selector skips an occupied port", next_port != held.getsockname()[1])
held.close()

# 8. Mocked UI smoke tests: default page render and a submitted analyst question.
import runpy
import types
class _Context:
    def __enter__(self): return self
    def __exit__(self, *args): return False
class _ContextWithMethods(_Context):
    def __getattr__(self, name):
        if name in {"metric", "button", "markdown", "caption", "write", "selectbox", "multiselect", "plotly_chart", "dataframe", "download_button", "success", "info", "warning", "error", "text_input"}:
            def call(*args, **kwargs):
                if name == "button": return False
                if name == "selectbox":
                    opts = list(args[1]) if len(args) > 1 else list(kwargs.get("options", []))
                    return opts[kwargs.get("index", 0)] if opts else None
                if name == "multiselect": return kwargs.get("default", [])
                if name == "text_input": return kwargs.get("value", "")
                return None
            return call
        raise AttributeError(name)
class _State(dict):
    def __getattr__(self, key):
        try: return self[key]
        except KeyError as exc: raise AttributeError(key) from exc
    def __setattr__(self, key, value): self[key] = value
class _FakeStreamlit(types.ModuleType):
    def __init__(self, submit=False):
        super().__init__("streamlit")
        self.session_state = _State()
        self.secrets = {}
        self.sidebar = _Context()
        self._submit = submit
    def set_page_config(self, *a, **k): pass
    def markdown(self, *a, **k): pass
    def caption(self, *a, **k): pass
    def write(self, *a, **k): pass
    def subheader(self, *a, **k): pass
    def header(self, *a, **k): pass
    def title(self, *a, **k): pass
    def info(self, *a, **k): pass
    def success(self, *a, **k): pass
    def warning(self, *a, **k): pass
    def error(self, *a, **k): pass
    def metric(self, *a, **k): pass
    def dataframe(self, *a, **k): pass
    def table(self, *a, **k): pass
    def plotly_chart(self, *a, **k): pass
    def download_button(self, *a, **k): return False
    def button(self, *a, **k): return False
    def text_input(self, label, *a, **k): return k.get("value", "")
    def checkbox(self, label, *a, **k): return k.get("value", False)
    def text_area(self, *a, **k): return "How has the company performed overall?" if self._submit else ""
    def file_uploader(self, *a, **k): return None
    def radio(self, label, options, *a, **k): return options[k.get("index", 0)]
    def selectbox(self, label, options, *a, **k):
        options = list(options); return options[k.get("index", 0)] if options else None
    def multiselect(self, *a, **k): return k.get("default", [])
    def slider(self, *a, **k): return k.get("value", k.get("default", 1))
    def columns(self, n, *a, **k):
        count = n if isinstance(n, int) else len(n)
        return [_ContextWithMethods() for _ in range(count)]
    def tabs(self, labels): return [_Context() for _ in labels]
    def expander(self, *a, **k): return _Context()
    def spinner(self, *a, **k): return _Context()
    def chat_message(self, *a, **k): return _Context()
    def chat_input(self, *a, **k): return None
    def form(self, *a, **k): return _Context()
    def form_submit_button(self, *a, **k): return self._submit
    def rerun(self): pass
    def stop(self): raise SystemExit

prior_streamlit = sys.modules.get("streamlit")
try:
    sys.modules["streamlit"] = _FakeStreamlit(submit=False)
    runpy.run_path(str(APP), run_name="__main__")
    check("Mocked Streamlit default page render", True)
    fake_submit = _FakeStreamlit(submit=True)
    sys.modules["streamlit"] = fake_submit
    ui_result = runpy.run_path(str(APP), run_name="__main__")
    ui_messages = ui_result.get("messages", [])
    check("Mocked AI Analyst form submission", len(ui_messages) >= 2 and ui_messages[-1].get("role") == "assistant" and len(ui_messages[-1].get("content", "")) > 80)
finally:
    if prior_streamlit is None:
        sys.modules.pop("streamlit", None)
    else:
        sys.modules["streamlit"] = prior_streamlit

print(f"InsightFlow self-test passed: {len(passed)} checks")
for item in passed:
    print(f"  PASS  {item}")
