from pathlib import Path
import io, os, json, re, textwrap, hashlib, html
from datetime import datetime
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from sklearn.linear_model import LinearRegression

from insightflow_agent import OpenAI, run_responses_agent

st.set_page_config(page_title="InsightFlow | Intelligence Workspace", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root {--if-bg:#0b1020;--if-panel:#121a2d;--if-panel2:#172239;--if-border:rgba(148,163,184,.17);--if-text:#edf3ff;--if-muted:#9aabc5;--if-cyan:#57d6c7;--if-violet:#9b8cff;--if-blue:#70a9ff;}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
.stApp{background:radial-gradient(ellipse at 15% 0%,rgba(75,92,180,.16),transparent 36%),radial-gradient(ellipse at 95% 8%,rgba(44,185,174,.10),transparent 32%),var(--if-bg);color:var(--if-text)}
.block-container{max-width:1580px;padding-top:1.25rem;padding-bottom:3rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#10182b,#0d1424);border-right:1px solid var(--if-border)}
[data-testid="stSidebar"] *{color:var(--if-text)}
h1,h2,h3,h4{font-family:'Manrope',sans-serif;letter-spacing:-.035em}
h1{font-weight:800!important}
.hero{padding:1.6rem 1.8rem;border:1px solid rgba(112,169,255,.23);border-radius:22px;background:linear-gradient(115deg,rgba(76,96,190,.23),rgba(41,174,164,.12) 65%,rgba(155,140,255,.12));box-shadow:0 18px 60px rgba(0,0,0,.18)}
.eyebrow{font-size:.72rem;letter-spacing:.16em;text-transform:uppercase;color:#80dcd2;font-weight:700}
.hero-title{font:800 2.15rem 'Manrope';margin:.25rem 0}
.hero-copy{color:#b9c8df;max-width:800px;font-size:.98rem}
.panel{background:linear-gradient(145deg,rgba(23,34,57,.92),rgba(17,26,44,.92));border:1px solid var(--if-border);border-radius:17px;padding:1.1rem 1.25rem}
.kpi{background:linear-gradient(145deg,rgba(28,43,70,.95),rgba(18,28,48,.95));border:1px solid var(--if-border);border-radius:16px;padding:1rem 1.1rem;min-height:116px}
.kpi-label{font-size:.78rem;color:#aab9d1}
.kpi-value{font:800 1.7rem 'Manrope';color:#f4f7ff;margin-top:.25rem}
.kpi-note{font-size:.75rem;color:#80dcd2;margin-top:.25rem}
.pill{display:inline-block;border:1px solid rgba(87,214,199,.3);background:rgba(87,214,199,.09);border-radius:99px;padding:.2rem .65rem;color:#9ce9e0;font-size:.72rem;margin-right:.3rem}
div[data-testid="stMetric"]{background:rgba(23,34,57,.8);border:1px solid var(--if-border);padding:.85rem 1rem;border-radius:14px}
.stButton>button{border-radius:10px;border:1px solid rgba(112,169,255,.28);background:linear-gradient(110deg,rgba(89,111,214,.95),rgba(42,167,161,.9));color:white;font-weight:700}
.stButton>button:hover{border-color:#8de9df;color:white;box-shadow:0 0 0 3px rgba(87,214,199,.12)}
.stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]>div{background:#121c30!important;border-color:rgba(148,163,184,.24)!important;color:#edf3ff!important;border-radius:10px!important}
.stTabs [data-baseweb="tab-list"]{gap:.4rem;border-bottom:1px solid var(--if-border)}
.stTabs [data-baseweb="tab"]{background:rgba(18,28,48,.6);border-radius:9px 9px 0 0;padding:.65rem 1rem}
.stTabs [aria-selected="true"]{background:rgba(87,214,199,.12)!important;color:#a8f1e8!important}
div[data-testid="stChatMessage"]{background:rgba(21,32,53,.82);border:1px solid var(--if-border);border-radius:15px;padding:.75rem 1rem;margin-bottom:.65rem}
[data-testid="stChatInput"] textarea{background:#121c30!important}
[data-testid="stForm"]{background:linear-gradient(145deg,rgba(23,34,57,.65),rgba(17,26,44,.65));border:1px solid rgba(87,214,199,.25);border-radius:16px;padding:1rem 1.1rem}
[data-testid="stTextArea"] textarea{min-height:100px;background:#121c30!important;color:#edf3ff!important;border:1px solid rgba(87,214,199,.32)!important;border-radius:12px!important}
hr{border-color:var(--if-border)}
.caption{color:var(--if-muted);font-size:.82rem}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

def read_file(upload, filename=None):
    name = filename or upload.name
    raw = upload if isinstance(upload, bytes) else upload.getvalue()
    bio = io.BytesIO(raw)
    if name.lower().endswith(".csv"):
        try: return pd.read_csv(bio)
        except UnicodeDecodeError:
            bio.seek(0); return pd.read_csv(bio, encoding="latin-1")
    return pd.read_excel(bio)

def safe_csv_bytes(frame):
    """Neutralize spreadsheet formula prefixes in text cells before CSV download."""
    safe = frame.copy()
    text_columns = safe.select_dtypes(include=["object", "string"]).columns
    dangerous_prefixes = ("=", "+", "-", "@", "\t", "\r")
    for column in text_columns:
        values = safe[column].astype("string")
        # Excel may treat cells with leading whitespace before a formula marker as formulas.
        stripped = values.str.lstrip(" \t\r\n")
        mask = stripped.str.startswith(dangerous_prefixes, na=False)
        safe.loc[mask, column] = "'" + values[mask].fillna("").astype(str)
    return safe.to_csv(index=False).encode("utf-8-sig")


def clean_df(df):
    x=df.copy()
    x.columns=[str(c).strip() for c in x.columns]
    x=x.loc[:,~pd.Index(x.columns).duplicated()].copy()
    x=x.dropna(axis=0,how="all").dropna(axis=1,how="all")
    x=x.replace(r"^\s*$",np.nan,regex=True)
    # Non-finite numeric values break several statistical and charting operations.
    x=x.replace([np.inf, -np.inf], np.nan)
    return x

def year_col(df):
    for c in df.columns:
        if str(c).lower().strip() in {"year","fiscal_year","fiscal year","calendar_year"}:
            v=pd.to_numeric(df[c],errors="coerce")
            if v.notna().sum()>=max(2,int(len(df)*.5)): return c
    return None

def numeric_cols(df):
    out=[]
    for c in df.columns:
        s=pd.to_numeric(df[c],errors="coerce")
        if s.notna().sum()>=max(2,int(len(df)*.5)): out.append(c)
    return out

def metrics(df):
    yc=year_col(df)
    return [c for c in numeric_cols(df) if c!=yc and str(c).lower() not in {"id","index"} and not str(c).lower().endswith("_id")]

def iqr_outlier_summary(df, column, multiplier=1.5):
    """Return univariate IQR outliers for a numeric field (screening, not diagnosis)."""
    values = pd.to_numeric(df[column], errors="coerce")
    valid = values.dropna()
    if len(valid) < 4:
        return {"supported": False, "count": int(len(valid)), "lower": None, "upper": None, "outliers": df.iloc[0:0].copy()}
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    lower = q1 - float(multiplier) * iqr
    upper = q3 + float(multiplier) * iqr
    mask = values.notna() & ((values < lower) | (values > upper))
    outliers = df.loc[mask].copy()
    return {"supported": True, "count": int(len(valid)), "q1": q1, "q3": q3, "iqr": float(iqr),
            "lower": float(lower), "upper": float(upper), "outliers": outliers}


def pretty(c):
    return str(c).replace("_"," ").replace("-"," ").title()

def safe_html_text(value):
    """Escape data-derived text before inserting it into trusted presentation HTML."""
    return html.escape(str(value), quote=True)


def build_visual_figure(df, chart_type, xcol, ycol, colorcol=None):
    """Build a validated Plotly figure for the Visual Explorer."""
    allowed = {"Line", "Area", "Bar", "Scatter", "Histogram", "Box", "Violin", "Pie", "Treemap"}
    if chart_type not in allowed:
        raise ValueError(f"Unsupported chart type: {chart_type}")
    if xcol not in df.columns or ycol not in df.columns:
        raise ValueError("Choose fields that exist in the active dataset.")
    if chart_type != "Histogram" and xcol == ycol:
        raise ValueError("Choose different fields for the dimension and numeric measure.")

    data = df.copy()
    data[ycol] = pd.to_numeric(data[ycol], errors="coerce")
    data = data.dropna(subset=[ycol])
    if data.empty:
        raise ValueError(f"'{ycol}' has no valid numeric observations to chart.")
    color = colorcol if colorcol in data.columns and colorcol not in {xcol, ycol, "None", None} else None

    if chart_type in {"Pie", "Treemap"}:
        grouped = data.groupby(xcol, dropna=False, as_index=False)[ycol].sum()
        if (grouped[ycol] < 0).any():
            raise ValueError("Pie and treemap charts require non-negative grouped values. Use a bar chart to display profit/loss values that can be negative.")
        if float(grouped[ycol].sum()) <= 0:
            raise ValueError("Pie and treemap charts require a positive total. Choose a different measure.")
        fig = px.pie(grouped, names=xcol, values=ycol) if chart_type == "Pie" else px.treemap(grouped, path=[xcol], values=ycol)
    elif chart_type == "Line":
        fig = px.line(data, x=xcol, y=ycol, color=color, markers=True)
    elif chart_type == "Area":
        fig = px.area(data, x=xcol, y=ycol, color=color)
    elif chart_type == "Bar":
        group_fields = [xcol, color] if color else [xcol]
        grouped = data.groupby(group_fields, dropna=False, as_index=False)[ycol].sum()
        fig = px.bar(grouped, x=xcol, y=ycol, color=color)
    elif chart_type == "Scatter":
        fig = px.scatter(data, x=xcol, y=ycol, color=color)
    elif chart_type == "Histogram":
        fig = px.histogram(data, x=ycol, color=color)
    elif chart_type == "Box":
        fig = px.box(data, x=xcol, y=ycol, color=color)
    else:  # Violin
        fig = px.violin(data, x=xcol, y=ycol, color=color, box=True)

    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=10, r=10, t=50, b=10))
    return fig

def fmt(v, c=""):
    if pd.isna(v):
        return "not available"
    try:
        v = float(v)
    except Exception:
        return str(v)
    n = str(c).lower()
    if n.endswith(("_usd_m", "_usd_mn")):
        return f"${v / 1000:,.2f}B" if abs(v) >= 1000 else f"${v:,.2f}M"
    if n.endswith("_pct") or "margin" in n or "share" in n or "ratio" in n:
        return f"{v:,.2f}%"
    if n.endswith("_gwh") or "storage_deployed" in n:
        return f"{v:,.2f} GWh"
    if n.endswith("_units") or n in {"tesla_locations", "supercharger_stations", "supercharger_connectors"}:
        return f"{v:,.0f}"
    if n.endswith("_usd") or "diluted_eps" in n:
        return f"${v:,.2f}"
    return f"{v:,.2f}"



def resolve_metric(df, phrase):
    """Resolve common business language to a dataset measure, preferring exact semantic matches."""
    cols = metrics(df)
    raw = str(phrase).lower().strip()
    p = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    aliases = {
        "revenue": ["revenue_total", "total_revenue", "revenue", "sales", "turnover"],
        "sales": ["sales", "revenue_total", "revenue"],
        "gross profit": ["gross_profit"], "gross_profit": ["gross_profit"],
        "net income": ["net_income_attributable_common", "net_income", "net_profit"],
        "net_income": ["net_income_attributable_common", "net_income", "net_profit"],
        "operating income": ["operating_income"], "operating_income": ["operating_income"],
        "operating profit": ["operating_income"],
        "profit": ["net_income", "operating_income", "gross_profit"],
        "employees": ["employee_count", "employees", "headcount", "workforce"],
        "employee": ["employee_count", "employees", "headcount", "workforce"],
        "headcount": ["employee_count", "employees", "headcount", "workforce"],
        "deliveries": ["vehicle_deliveries", "deliveries"],
        "production": ["vehicle_production", "production"],
        "cash flow": ["operating_cash_flow", "cash_flow"],
        "operating cash flow": ["operating_cash_flow"],
        "inventory": ["inventory"], "assets": ["total_assets", "assets"],
        "liabilities": ["total_liabilities", "liabilities"],
        "equity": ["stockholders_equity", "equity"],
        "gross margin": ["gross_margin"], "operating margin": ["operating_margin"],
        "net margin": ["net_margin"], "eps": ["diluted_eps", "eps"],
        "storage": ["storage_deployed", "energy_storage", "storage"],
    }
    terms = aliases.get(raw, aliases.get(p, [p]))
    scored = []
    for c in cols:
        n = re.sub(r"[^a-z0-9]+", "_", str(c).lower()).strip("_")
        score = 0
        for term in terms:
            t = term.lower().replace(" ", "_")
            if n == t: score = max(score, 120 + len(t))
            elif n.startswith(t + "_"): score = max(score, 95 + len(t))
            elif t in n: score = max(score, 65 + len(t))
        if raw in {"revenue", "sales", "turnover"}:
            if "revenue_total" in n or n in {"revenue", "total_revenue"}: score += 80
            if any(k in n for k in ("automotive", "energy", "services", "regional", "revenue_us", "revenue_china")): score -= 35
        if raw in {"net income", "net_income"} and "attributable_common" in n: score += 8
        if score > 0: scored.append((score, str(c), c))
    return sorted(scored, key=lambda x: (-x[0], str(x[1])))[0][2] if scored else None



def dataset_profile(df, label):
    ncols=metrics(df)
    return {
      "dataset":label,"rows":int(len(df)),"columns":int(len(df.columns)),
      "fields":[{"name":str(c),"dtype":str(df[c].dtype),"missing":int(df[c].isna().sum()),"unique":int(df[c].nunique(dropna=True))} for c in df.columns],
      "numeric_fields":[str(c) for c in ncols],
      "categorical_fields":[str(c) for c in df.columns if c not in ncols and df[c].nunique(dropna=True)<=100],
      "missing_cells":int(df.isna().sum().sum()),"duplicate_rows":int(df.duplicated().sum())
    }

def reset_threads_when_dataset_changes(session_state, fingerprint):
    """Reset chat history when the selected file changes to prevent context mixing."""
    previous = session_state.get("if_dataset_fingerprint")
    changed = previous is not None and previous != fingerprint
    if changed:
        session_state["if_threads"] = {"thread_1": {"title": "New dataset analysis", "messages": []}}
        session_state["if_current"] = "thread_1"
    session_state["if_dataset_fingerprint"] = fingerprint
    return changed

def build_evidence(question, df):
    """Create deterministic, dataset-grounded evidence for the local analyst and optional LLM."""
    q = str(question).lower()
    evidence = {
        "question": str(question), "dataset_rows": int(len(df)), "dataset_columns": int(len(df.columns)),
        "missing_cells": int(df.isna().sum().sum()), "duplicate_rows": int(df.duplicated().sum()),
        "facts": [], "available_fields": [str(c) for c in df.columns]
    }
    yc = year_col(df)
    ncols = metrics(df)
    metric_phrases = [
        "gross profit", "operating income", "net income", "operating cash flow", "cash flow",
        "revenue", "sales", "employees", "headcount", "deliveries", "production", "inventory",
        "assets", "liabilities", "equity", "gross margin", "operating margin", "net margin", "storage", "eps"
    ]
    requested = []
    for phrase in metric_phrases:
        if phrase in q:
            col = resolve_metric(df, phrase)
            if col is not None and col not in requested:
                requested.append(col)

    broad = any(w in q for w in ["overall", "company performed", "business performed", "performance", "business health", "company health", "how is the company doing", "how has the company done", "summari", "overview"])
    if broad:
        for phrase in ["revenue", "gross profit", "operating income", "net income", "operating cash flow", "deliveries", "production", "storage"]:
            col = resolve_metric(df, phrase)
            if col is not None and col not in requested:
                requested.append(col)

    # Exact field-name mentions may map user language to a specific measure.
    explicit = next((c for c in ncols if str(c).lower().replace("_", " ") in q), None)
    if explicit is not None and explicit not in requested:
        requested.insert(0, explicit)

    quality_intent = any(w in q for w in ["missing", "quality", "duplicate", "null", "blank", "incomplete"])
    if quality_intent:
        miss = df.isna().sum().sort_values(ascending=False)
        evidence["quality"] = {
            "missing_by_field": {str(k): int(v) for k, v in miss.items() if int(v) > 0},
            "duplicate_rows": int(df.duplicated().sum()),
            "completely_empty_columns": [str(c) for c in df.columns if df[c].isna().all()],
        }

    # For broad performance prompts, use metrics present in the data; never imply unavailable measures exist.
    for c in requested[:10]:
        vals = pd.to_numeric(df[c], errors="coerce")
        valid = vals.dropna()
        fact = {
            "metric": str(c), "label": pretty(c), "valid_records": int(valid.size),
            "missing": int(vals.isna().sum()), "sum": float(valid.sum()) if len(valid) else None,
            "mean": float(valid.mean()) if len(valid) else None, "median": float(valid.median()) if len(valid) else None,
            "min": float(valid.min()) if len(valid) else None, "max": float(valid.max()) if len(valid) else None,
        }
        if yc:
            temp = pd.DataFrame({"period": pd.to_numeric(df[yc], errors="coerce"), "value": vals}).dropna()
            temp = temp.groupby("period", as_index=False).value.sum().sort_values("period")
            fact["period_column"] = str(yc)
            fact["period_values"] = [{"period": float(r.period), "value": float(r.value)} for r in temp.tail(30).itertuples()]
            if len(temp):
                hi = temp.loc[temp.value.idxmax()]
                lo = temp.loc[temp.value.idxmin()]
                fact["highest_period"] = int(hi.period) if float(hi.period).is_integer() else float(hi.period)
                fact["highest_value"] = float(hi.value)
                fact["lowest_period"] = int(lo.period) if float(lo.period).is_integer() else float(lo.period)
                fact["lowest_value"] = float(lo.value)
            if len(temp) >= 2:
                first, last = temp.iloc[0], temp.iloc[-1]
                fact["first_period"] = int(first.period) if float(first.period).is_integer() else float(first.period)
                fact["first_value"] = float(first.value)
                fact["last_period"] = int(last.period) if float(last.period).is_integer() else float(last.period)
                fact["last_value"] = float(last.value)
                fact["absolute_change"] = float(last.value - first.value)
                fact["percent_change"] = float((last.value - first.value) / abs(first.value) * 100) if first.value else None
                if len(temp) >= 3:
                    model = LinearRegression().fit(temp.period.to_numpy().reshape(-1, 1), temp.value.to_numpy())
                    nextp = int(temp.period.max()) + 1
                    estimate = float(model.predict(np.array([[nextp]]))[0])
                    last_observed = float(temp.iloc[-1].value)
                    forecast_delta = estimate - last_observed
                    forecast_pct = (forecast_delta / abs(last_observed) * 100) if last_observed else None
                    fact["linear_trend_next_period"] = {
                        "period": nextp, "estimate": estimate,
                        "change_vs_last_observed": forecast_delta,
                        "percent_change_vs_last_observed": forecast_pct,
                        "last_observed_period": int(temp.iloc[-1].period) if float(temp.iloc[-1].period).is_integer() else float(temp.iloc[-1].period),
                        "last_observed_value": last_observed,
                        "observations": int(len(temp)),
                        "warning": "Exploratory linear trend only; few observations and external drivers are not modeled."
                    }
        evidence["facts"].append(fact)

    # Categorical breakdowns: only run when an appropriate dimension is actually present.
    dimension_terms = {
        "region": ["region", "geography", "geographical"], "country": ["country", "market"],
        "segment": ["segment", "business line"], "factory": ["factory", "plant", "facility"],
        "department": ["department", "division"],
    }
    for label, terms in dimension_terms.items():
        if label in q or any(t in q for t in terms):
            cat = next((c for c in df.columns if any(t in str(c).lower() for t in terms)), None)
            if cat is not None:
                candidates = requested[:3] if requested else ncols[:1]
                for metric in candidates[:2]:
                    tmp = df[[cat, metric]].copy()
                    tmp[metric] = pd.to_numeric(tmp[metric], errors="coerce")
                    grouped = tmp.dropna().groupby(cat)[metric].sum().sort_values(ascending=False).head(12)
                    evidence.setdefault("grouped_breakdowns", []).append({
                        "dimension": str(cat), "metric": str(metric),
                        "top_values": [{"category": str(k), "value": float(v)} for k, v in grouped.items()]
                    })

    if any(w in q for w in ["correlat", "relationship", "associated", "related"]):
        chosen = requested or ncols[:8]
        if len(chosen) >= 2:
            corr = df[chosen].apply(pd.to_numeric, errors="coerce").corr().round(3)
            evidence["correlations"] = corr.where(pd.notna(corr), None).to_dict()

    evidence["intent"] = {
        "average": any(w in q for w in ["average", "mean"]),
        "highest": any(w in q for w in ["highest", "largest", "maximum", "max", "best", "top year"]),
        "lowest": any(w in q for w in ["lowest", "smallest", "minimum", "min", "worst"]),
        "forecast": any(w in q for w in ["forecast", "project", "projected", "predict", "estimate", "next year", "2026"]),
        "overview": broad,
        "specific_period": [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", q)],
    }
    evidence["sample_rows"] = df.head(4).replace({np.nan: None}).to_dict(orient="records")
    return evidence



def local_answer(question, evidence, df):
    """Readable local-mode analyst response; all figures come from calculated evidence."""
    q = str(question).lower()
    facts = evidence.get("facts", [])
    quality = evidence.get("quality")
    if quality is not None:
        missing_total = evidence.get("missing_cells", 0)
        duplicate_rows = quality.get("duplicate_rows", 0)
        affected = [(k, v) for k, v in quality.get("missing_by_field", {}).items() if v > 0]
        lines = ["## Data quality review", f"I checked **{len(df):,} rows** across **{len(df.columns):,} fields**.",
                 f"There are **{missing_total:,} missing cells** and **{duplicate_rows:,} duplicate rows**."]
        if affected:
            lines.append("### Fields with missing values")
            lines.extend([f"- **{k}**: {v:,} missing" for k, v in affected[:12]])
        else:
            lines.append("No missing values were detected in the current dataset.")
        if duplicate_rows:
            lines.append("Review duplicate records before aggregating or exporting; duplicates can inflate totals.")
        else:
            lines.append("No exact duplicate rows were detected.")
        return "\n\n".join(lines)

    if any(w in q for w in ["limitation", "limitations", "data coverage", "what data", "what information", "what fields", "dataset coverage"]):
        prof = dataset_profile(df, "selected dataset")
        numeric_available = [pretty(c) for c in prof["numeric_fields"][:12]]
        categorical_available = [pretty(c) for c in prof["categorical_fields"][:12]]
        lines = [
            "## Dataset coverage and analytical limitations",
            f"The selected dataset contains **{prof['rows']:,} rows**, **{prof['columns']:,} columns**, **{prof['missing_cells']:,} missing cells**, and **{prof['duplicate_rows']:,} exact duplicate rows**.",
            "### What can be analysed",
            "Numeric measures available: " + (", ".join(numeric_available) if numeric_available else "none detected") + ".",
            "Categorical dimensions available: " + (", ".join(categorical_available) if categorical_available else "none detected") + ".",
            "### What the data cannot establish by itself",
            "A dataset can show associations and changes, but aggregate historical figures alone do not prove why a change happened. Regional or workforce questions need matching geographic and employee fields. Multi-table analysis needs reliable shared keys and compatible time periods.",
        ]
        if len(df) <= 5:
            lines.append("**Forecasting caution:** there are only a few records. Trend projections are demonstrations, not reliable forecasts.")
        return "\n\n".join(lines)

    if not facts:
        available = ", ".join(pretty(c) for c in metrics(df)[:10]) or "no numeric measures"
        if any(w in q for w in ["employee", "employees", "headcount", "workforce", "staff"]):
            employee_fields = [c for c in df.columns if any(w in str(c).lower() for w in ["employee", "headcount", "workforce", "staff_count"])]
            if not employee_fields:
                return ("## Workforce analysis is not available in this dataset\n\n"
                        "I could not find an employee-count, headcount or workforce field. To calculate employee concentration, upload workforce data with at least a period and employee count; add country, region, department or site fields for the relevant breakdown. "
                        "I won't estimate workforce numbers from revenue or other unrelated measures.")
        return ("I couldn't map that question to a measure that exists in this dataset. I don't want to guess or fabricate a result.\n\n"
                f"**Available numeric measures include:** {available}.\n\n"
                "Try a question such as *revenue by year*, *average gross profit*, *which year had the highest revenue*, or *compare operating income and net income*. "
                "A regional analysis requires a country/region dimension and a compatible numeric measure in the uploaded data.")

    lines = []
    if evidence.get("intent", {}).get("overview"):
        lines.append("## Company performance review")
        lines.append(f"This review uses **{len(df):,} records** and **{len(df.columns):,} fields** from the currently selected dataset. It summarizes the measures that are actually available; it is not a full explanation of every business driver.")
    for f in facts:
        label, metric = f["label"], f["metric"]
        lines.append(f"### {label}")
        target_periods = evidence.get("intent", {}).get("specific_period", [])
        matching_points = [pt for pt in f.get("period_values", []) if int(pt["period"]) in target_periods] if f.get("period_values") and target_periods else []
        if matching_points and not evidence.get("intent", {}).get("average"):
            selected_points = ", ".join(f"**{int(pt['period'])}: {fmt(pt['value'], metric)}**" for pt in matching_points)
            lines.append(f"The recorded value for the requested period is {selected_points}.")
            if evidence.get("intent", {}).get("forecast") and f.get("linear_trend_next_period") and any(y > max(pt["period"] for pt in f["period_values"]) for y in target_periods):
                tr = f["linear_trend_next_period"]
                lines.append(f"The model's next-period linear estimate is **{fmt(tr['estimate'], metric)}** for **{tr['period']}**. This is exploratory, not an official forecast.")
        elif evidence.get("intent", {}).get("average") and not evidence.get("intent", {}).get("overview"):
            lines.append(f"The average across the {f['valid_records']:,} valid observations is **{fmt(f.get('mean'), metric)}** (median: **{fmt(f.get('median'), metric)}**). The observed range is **{fmt(f.get('min'), metric)}** to **{fmt(f.get('max'), metric)}**.")
        elif evidence.get("intent", {}).get("highest"):
            if f.get("period_values"):
                lines.append(f"The highest recorded value is **{fmt(f.get('highest_value'), metric)}** in **{f.get('highest_period')}**. The lowest is **{fmt(f.get('lowest_value'), metric)}** in **{f.get('lowest_period')}**.")
            else:
                lines.append(f"The highest observed value is **{fmt(f.get('max'), metric)}**. The dataset does not contain a recognized period field to identify when it occurred.")
        elif evidence.get("intent", {}).get("lowest"):
            if f.get("period_values"):
                lines.append(f"The lowest recorded value is **{fmt(f.get('lowest_value'), metric)}** in **{f.get('lowest_period')}**. The highest is **{fmt(f.get('highest_value'), metric)}** in **{f.get('highest_period')}**.")
            else:
                lines.append(f"The lowest observed value is **{fmt(f.get('min'), metric)}**. The dataset does not contain a recognized period field to identify when it occurred.")
        elif f.get("period_values"):
            points = f["period_values"]
            if len(points) >= 2:
                lines.append(f"Across the available {f['period_column']} observations, {label.lower()} moved from **{fmt(f.get('first_value'), metric)}** in **{f.get('first_period')}** to **{fmt(f.get('last_value'), metric)}** in **{f.get('last_period')}**.")
                if f.get("percent_change") is not None:
                    direction = "increase" if f["absolute_change"] >= 0 else "decrease"
                    lines.append(f"That is a net {direction} of **{fmt(abs(f['absolute_change']), metric)} ({abs(f['percent_change']):.2f}%)** between the first and last available periods.")
                high = f.get("highest_period")
                if high is not None:
                    lines.append(f"The highest recorded period was **{high}**, at **{fmt(f.get('highest_value'), metric)}**.")
                if evidence.get("intent", {}).get("forecast") and f.get("linear_trend_next_period"):
                    tr = f["linear_trend_next_period"]
                    change_pct = tr.get("percent_change_vs_last_observed")
                    change_pct_text = f"{change_pct:+.2f}%" if change_pct is not None else "not calculable"
                    lines.append(f"A simple linear trend estimates **{fmt(tr['estimate'], metric)}** for **{tr['period']}**. Compared with the latest actual period ({tr['last_observed_period']}), that is a modelled change of **{fmt(abs(tr['change_vs_last_observed']), metric)}** ({change_pct_text}). Treat this as an exploratory baseline, not a dependable company forecast: it uses only {tr['observations']} observations and does not model market conditions or business decisions.")
            else:
                lines.append(f"The available value is **{fmt(points[-1]['value'], metric)}** in **{points[-1]['period']}**.")
        else:
            lines.append(f"Total: **{fmt(f.get('sum'), metric)}**. Average: **{fmt(f.get('mean'), metric)}**. Median: **{fmt(f.get('median'), metric)}**. Range: **{fmt(f.get('min'), metric)}** to **{fmt(f.get('max'), metric)}**.")

    if evidence.get("grouped_breakdowns"):
        lines.append("## Segment / geography breakdown")
        for g in evidence["grouped_breakdowns"]:
            top = g["top_values"][0] if g["top_values"] else None
            if top:
                lines.append(f"By **{pretty(g['dimension'])}**, the largest available total is **{top['category']}** at **{fmt(top['value'], g['metric'])}**.")
    elif any(t in q for t in ["region", "country", "geograph", "employee", "headcount", "workforce"]):
        lines.append("## Data needed to answer the dimension question")
        lines.append("The current dataset does not contain a compatible dimension/measure combination for that breakdown. For example, employee concentration by country requires both a country/region field and an employee-count measure with matching time periods or entity keys.")

    if evidence.get("correlations"):
        lines.append("## Relationships to investigate")
        lines.append("The correlation matrix is available in the evidence panel, but correlation does not establish causation. Check timing, confounding variables and business context before drawing conclusions.")

    if any(w in q for w in ["driving", "driver", "why did", "why has", "cause", "caused"]):
        lines.append("## What may be driving the change?\nThe selected dataset can quantify the movement, but the available aggregate time series is not sufficient to establish the cause. To investigate drivers, add compatible price, volume, segment, product, regional, cost or workforce measures. I will not label a factor as the cause without supporting evidence.")

    lines.append("## How to interpret this")
    lines.append(f"The figures above are calculated from the selected dataset. Coverage: **{len(df):,} rows**, **{len(df.columns):,} columns**, and **{evidence.get('missing_cells', 0):,} missing cells**. Results depend on the completeness, definitions and units of the uploaded fields.")
    if len(df) <= 5 and evidence.get("intent", {}).get("forecast"):
        lines.append("**Important limitation:** this dataset has very few observations. A trend extrapolation is useful for demonstrating the method, but it is not statistically strong enough for a high-confidence forecast.")
    lines.append("If you want to go deeper, ask a follow-up about a specific segment, period or driver that exists in this dataset.")
    return "\n\n".join(lines)



def chart_for_evidence(evidence):
    facts=evidence.get("facts",[])
    if not facts: return None
    f=next((x for x in facts if x.get("period_values")),None)
    if f:
        d=pd.DataFrame(f["period_values"])
        fig=px.line(d,x="period",y="value",markers=True,title=f"{f['label']} over time")
        fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",margin=dict(l=10,r=10,t=50,b=10))
        return fig
    return None

def kpi(label,value,note=""):
    st.markdown(f'<div class="kpi"><div class="kpi-label">{safe_html_text(label)}</div><div class="kpi-value">{safe_html_text(value)}</div><div class="kpi-note">{safe_html_text(note)}</div></div>',unsafe_allow_html=True)

# ---------- Sidebar and data ----------
with st.sidebar:
    st.markdown("## ✦ InsightFlow")
    st.caption("Enterprise intelligence workspace")
    st.markdown("---")
    st.markdown("**DATA SOURCE**")
    demo_options={}
    for fn in ["Tesla_2021_2025_Company_Data.csv","sample_sales.csv"]:
        p=Path(__file__).parent/"data"/fn
        if p.exists(): demo_options[fn]=p
    source=st.radio("Choose a dataset",["Tesla 2021–2025","Retail sample","Upload your own"],index=0)
    if source=="Tesla 2021–2025" and "Tesla_2021_2025_Company_Data.csv" in demo_options:
        source_path = demo_options["Tesla_2021_2025_Company_Data.csv"]
        source_bytes = source_path.read_bytes()
        df=clean_df(read_file(source_bytes, source_path.name)); data_label="Tesla 2021–2025 demo"
        dataset_fingerprint = hashlib.sha256(source_bytes).hexdigest()
    elif source=="Retail sample" and "sample_sales.csv" in demo_options:
        source_path = demo_options["sample_sales.csv"]
        source_bytes = source_path.read_bytes()
        df=clean_df(read_file(source_bytes, source_path.name)); data_label="Retail sample"
        dataset_fingerprint = hashlib.sha256(source_bytes).hexdigest()
    else:
        upload=st.file_uploader("Upload CSV or Excel",type=["csv","xlsx","xls"])
        if upload:
            try:
                source_bytes = upload.getvalue()
                df=clean_df(read_file(source_bytes, upload.name)); data_label=upload.name
                dataset_fingerprint = hashlib.sha256(source_bytes).hexdigest()
            except Exception as e:
                st.error(f"Could not read this file: {e}"); st.stop()
        else:
            df=pd.DataFrame(); data_label="No dataset loaded"
            dataset_fingerprint = "no-dataset"
    st.markdown("---")
    st.markdown("**AI CONNECTION & REASONING**")
    default_key = os.getenv("OPENAI_API_KEY", "")
    configured_model = os.getenv("OPENAI_MODEL", "gpt-6-astra")
    try:
        default_key = st.secrets.get("OPENAI_API_KEY", default_key)
        configured_model = st.secrets.get("OPENAI_MODEL", configured_model)
    except Exception:
        pass
    entered_key = st.text_input(
        "Your OpenAI API key (session only)", value="", type="password",
        help="Prefer OPENAI_API_KEY in your environment or Streamlit secrets. Never commit a key to GitHub."
    )
    api_key = (entered_key or default_key or "").strip()
    model_profiles = {
        "Maximum reasoning · GPT-6 Astra": "gpt-6-astra",
        "Balanced · GPT-6.1 Sol": "gpt-6.1-sol",
        "Fast and versatile · GPT-6.1 Terra": "gpt-6.1-terra",
        "Efficient · GPT-6 Luna": "gpt-6-luna",
        "Custom model ID": "",
    }
    configured_profile = next((label for label, model_id in model_profiles.items() if model_id and model_id == configured_model), "Custom model ID")
    model_profile = st.selectbox("Model profile", list(model_profiles), index=list(model_profiles).index(configured_profile),
                                 help="Astra is the flagship reasoning option; Sol balances capability and cost; Terra is fast and versatile; Luna is designed for lower-cost usage. Availability depends on your API project.")
    if model_profile == "Custom model ID":
        model = st.text_input("OpenAI model ID", value=configured_model,
                              help="Enter an exact model ID enabled for your API project.")
    else:
        model = model_profiles[model_profile]
        st.caption(f"Selected model: `{model}`")
    reasoning_effort = st.selectbox("Reasoning effort", ["low", "medium", "high", "xhigh", "max"], index=1,
                                     help="Used only by models that support reasoning controls. Higher effort can increase latency and API usage.")
    reasoning_mode = st.selectbox("Reasoning mode (GPT-6 / GPT-5.6 models)", ["standard", "pro"], index=0,
                                  help="Pro mode is intended for harder analysis and can take longer or use more tokens. It is ignored for models that do not support it.")
    answer_depth = st.selectbox("Analyst response depth", ["Balanced", "Detailed", "Deep dive"], index=1)
    max_tool_rounds = st.slider("Maximum analysis tool rounds", min_value=1, max_value=6, value=4,
                                help="Bounds the number of tool-calling iterations per question.")
    use_web_search = st.checkbox("Allow external web research", value=False,
                                 help="Adds OpenAI's hosted web_search tool for public external context. This can add cost and sends search queries outside the app.")
    st.caption("GPT-6 Astra and Pro reasoning are premium/longer-running options. Check current API pricing and project limits before using Deep dive, Max effort or web research frequently.")
    share_analytics = st.checkbox(
        "I consent to send my question, recent thread context, dataset field metadata and calculated analysis results to OpenAI.",
        value=False,
        help="InsightFlow does not upload the full raw DataFrame through its analytics tools, but calculated values and metadata are sent for LLM reasoning. Keep this off for confidential datasets."
    )
    session_call_limit = st.selectbox("LLM API request limit for this session", [5, 10, 20, 40], index=2)
    if "if_api_requests" not in st.session_state:
        st.session_state.if_api_requests = 0
    st.caption(f"Responses API requests used in this session: {st.session_state.if_api_requests} / {session_call_limit}")
    st.caption("This session cap does not guarantee a monetary spending limit or include every hosted-tool fee. Set a separate usage budget in your OpenAI API project settings.")
    if api_key:
        st.success("API key available")
        if OpenAI is not None and st.button("Test API key + model access", use_container_width=True):
            try:
                check_client = OpenAI(api_key=api_key, timeout=20.0, max_retries=0)
                check_client.models.retrieve(model.strip())
                st.success(f"API key accepted and model '{model.strip()}' is accessible.")
            except Exception as exc:
                st.error(f"Connection check failed: {type(exc).__name__}: {str(exc)[:260]}")
    else:
        st.info("Local analytical mode. Add an API key to enable the Responses API analyst.")
    if api_key and not share_analytics:
        st.warning("LLM is paused until you enable the data-sharing consent checkbox.")
    st.markdown("---")
    st.caption("InsightFlow · Python analytics + OpenAI Responses API agent")

if df.empty:
    st.markdown('<div class="hero"><div class="eyebrow">Business intelligence, reimagined</div><div class="hero-title">Understand your business beyond the obvious.</div><div class="hero-copy">Upload a CSV or Excel workbook to explore performance, uncover patterns and ask questions in a continuing analyst conversation.</div></div>',unsafe_allow_html=True)
    st.info("Choose a demo dataset or upload a file from the sidebar to begin.")
    st.stop()

profile=dataset_profile(df,data_label)
num=metrics(df); yc=year_col(df)
# Do not carry conversational context from one dataset into a different dataset.
dataset_changed = reset_threads_when_dataset_changes(st.session_state, dataset_fingerprint)
if dataset_changed:
    st.info("The selected dataset changed. InsightFlow started a fresh conversation so answers from the previous dataset are not mixed into this analysis.")
# Session-based threaded conversations
if "if_threads" not in st.session_state: st.session_state.if_threads={"thread_1":{"title":"Company performance review","messages":[]}}
if "if_current" not in st.session_state: st.session_state.if_current="thread_1"
if st.session_state.if_current not in st.session_state.if_threads: st.session_state.if_current=list(st.session_state.if_threads)[0]
with st.sidebar:
    st.markdown("**CONVERSATIONS**")
    if st.button("＋ New analysis thread",use_container_width=True):
        tid=f"thread_{len(st.session_state.if_threads)+1}_{datetime.now().strftime('%H%M%S')}"
        st.session_state.if_threads[tid]={"title":"New analysis","messages":[]}
        st.session_state.if_current=tid
        st.rerun()
    thread_ids=list(st.session_state.if_threads)
    labels=[st.session_state.if_threads[t]["title"] for t in thread_ids]
    selected=st.selectbox("Your threads",thread_ids,index=thread_ids.index(st.session_state.if_current),format_func=lambda x:st.session_state.if_threads[x]["title"])
    st.session_state.if_current=selected
    if st.button("Clear current thread",use_container_width=True):
        st.session_state.if_threads[selected]["messages"]=[]
        st.rerun()

# Header
st.markdown(f"<div class='hero'><div class='eyebrow'>Your company&#39;s intelligence layer</div><div class='hero-title'>See the story behind the numbers.</div><div class='hero-copy'>Explore <b>{safe_html_text(data_label)}</b> through executive metrics, interactive visuals and a continuing analyst conversation. InsightFlow grounds its explanations in calculations from your uploaded data.</div></div>",unsafe_allow_html=True)
st.write("")
t_over,t_studio,t_visual,t_quality,t_forecast,t_ai,t_reco,t_reports=st.tabs(["✦ Overview","▦ Data Studio","◈ Visual Explorer","⌁ Data Health","↗ Forecast Lab","✧ AI Analyst","◎ Recommendations","⇩ Reports"])

with t_over:
    st.subheader("Executive snapshot")
    st.caption("A quick read of the dataset. Select business measures in the controls below to tailor the view.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Records",f"{len(df):,}")
    c2.metric("Fields",f"{len(df.columns):,}")
    c3.metric("Numeric measures",f"{len(num):,}")
    c4.metric("Missing cells",f"{profile['missing_cells']:,}")
    chosen=st.selectbox("Primary business measure",num,index=(num.index(resolve_metric(df,"revenue")) if resolve_metric(df,"revenue") in num else 0),key="overview_metric") if num else None
    if chosen:
        s=pd.to_numeric(df[chosen],errors="coerce").dropna()
        a,b,c=st.columns(3)
        a.metric("Total",fmt(s.sum(),chosen))
        b.metric("Average",fmt(s.mean(),chosen))
        c.metric("Median",fmt(s.median(),chosen))
        if yc:
            temp=pd.DataFrame({"Period":pd.to_numeric(df[yc],errors="coerce"),"Value":pd.to_numeric(df[chosen],errors="coerce")}).dropna().groupby("Period",as_index=False).Value.sum().sort_values("Period")
            fig=px.area(temp,x="Period",y="Value",markers=True,title=f"{pretty(chosen)} · historical movement")
            fig.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig,use_container_width=True)
    with st.expander("Dataset profile"):
        st.write(pd.DataFrame(profile["fields"]))
        st.dataframe(df.head(15),use_container_width=True)

with t_studio:
    st.subheader("Data studio")
    st.caption("Inspect, filter and export the data used by the analyst.")
    filters=[c for c in df.columns if df[c].nunique(dropna=True)<=30 and df[c].nunique(dropna=True)>1]
    filtered=df.copy()
    fcols=st.columns(min(3,max(1,len(filters))))
    for i,col in enumerate(filters[:3]):
        vals=sorted(df[col].dropna().astype(str).unique().tolist())
        choice=fcols[i].multiselect(pretty(col),vals,default=[],key=f"filter_{col}")
        if choice: filtered=filtered[filtered[col].astype(str).isin(choice)]
    st.caption(f"Showing {len(filtered):,} of {len(df):,} rows")
    st.dataframe(filtered,use_container_width=True,height=420)
    st.download_button("Download filtered CSV",safe_csv_bytes(filtered), "insightflow_filtered_data.csv","text/csv")

with t_visual:
    st.subheader("Visual explorer")
    st.caption("Build a chart from compatible fields in the uploaded dataset.")
    if not num:
        st.info("This dataset has no numeric measure that can be charted. Upload a dataset with at least one numeric field.")
    else:
        left,right=st.columns([1,3])
        with left:
            chart_type=st.selectbox("Chart type",["Line","Area","Bar","Scatter","Histogram","Box","Violin","Pie","Treemap"])
            xcol=st.selectbox("Dimension / X axis",df.columns.tolist(),index=0)
            yopts=[c for c in num if c != xcol] or num
            ycol=st.selectbox("Measure / Y axis",yopts,index=0)
            coloropts=["None"]+[c for c in df.columns if c not in [xcol,ycol] and df[c].nunique(dropna=True)<=30]
            colorcol=st.selectbox("Color by",coloropts)
        with right:
            color=None if colorcol=="None" else colorcol
            try:
                fig=build_visual_figure(df,chart_type,xcol,ycol,color)
                st.plotly_chart(fig,use_container_width=True)
                st.download_button("Download chart data",safe_csv_bytes(df[[xcol,ycol]]),"chart_data.csv","text/csv")
            except Exception as exc:
                st.warning(f"This chart could not be built from the selected fields: {type(exc).__name__}: {exc}")
                st.caption("Try a different dimension, numeric measure or chart type.")

with t_quality:
    st.subheader("Data health")
    a,b,c=st.columns(3); a.metric("Missing cells",f"{profile['missing_cells']:,}"); b.metric("Duplicate rows",f"{profile['duplicate_rows']:,}"); c.metric("Fields",f"{len(df.columns):,}")
    miss=df.isna().sum().sort_values(ascending=False).head(20)
    miss=miss[miss>0]
    if len(miss): st.plotly_chart(px.bar(x=miss.values,y=miss.index,orientation="h",title="Missing values by field").update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)"),use_container_width=True)
    else: st.success("No missing values detected.")
    st.dataframe(pd.DataFrame({"Field":df.columns,"Type":[str(df[c].dtype) for c in df.columns],"Missing":[int(df[c].isna().sum()) for c in df.columns],"Unique":[int(df[c].nunique(dropna=True)) for c in df.columns]}),use_container_width=True)
    st.markdown("### Univariate outlier screening (IQR)")
    if num:
        outlier_metric=st.selectbox("Measure to screen",num,key="outlier_metric")
        outlier_result=iqr_outlier_summary(df,outlier_metric)
        if not outlier_result["supported"]:
            st.info("At least four valid numeric observations are required for IQR screening.")
        else:
            left,right=st.columns(2)
            left.metric("Potential outliers",f"{len(outlier_result['outliers']):,}")
            right.metric("Valid observations",f"{outlier_result['count']:,}")
            st.caption(f"IQR screening bounds: {outlier_result['lower']:,.3f} to {outlier_result['upper']:,.3f}. These are statistical flags for review, not proof of data errors or business anomalies.")
            if len(outlier_result["outliers"]): st.dataframe(outlier_result["outliers"],use_container_width=True)
            else: st.success("No values fell outside the IQR screening bounds.")
    else:
        st.info("No numeric measures are available for outlier screening.")

with t_forecast:
    st.subheader("Forecast lab")
    st.caption("Exploratory trend model. Use at least three observations; small samples are not reliable forecasts.")
    forecast_options=[c for c in num if c!=yc] if yc else []
    if yc and forecast_options:
        metric=st.selectbox("Measure to forecast",forecast_options,key="forecast_metric")
        periods=st.slider("Periods ahead",1,5,1)
        if st.button("Run forecast"):
            try:
                temp=pd.DataFrame({"year":pd.to_numeric(df[yc],errors="coerce"),"value":pd.to_numeric(df[metric],errors="coerce")}).dropna().groupby("year",as_index=False).value.sum().sort_values("year")
                if len(temp)<3: st.warning("At least three annual observations are needed.")
                else:
                    model=LinearRegression().fit(temp.year.to_numpy().reshape(-1,1),temp.value.to_numpy())
                    future=np.arange(int(temp.year.max())+1,int(temp.year.max())+periods+1)
                    pred=model.predict(future.reshape(-1,1))
                    plot=pd.concat([pd.DataFrame({"Year":temp.year.astype(int),"Value":temp.value,"Type":"Actual"}),pd.DataFrame({"Year":future,"Value":pred,"Type":"Forecast"})])
                    st.plotly_chart(px.line(plot,x="Year",y="Value",color="Type",markers=True,title=f"{pretty(metric)}: actual vs trend estimate").update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)"),use_container_width=True)
                    st.dataframe(plot,use_container_width=True)
                    st.warning("This is a simple linear extrapolation, not a causal or production-grade forecast. Validate against more observations and external drivers.")
            except Exception as exc:
                st.error(f"Forecasting could not be completed for this field: {type(exc).__name__}: {exc}")
    else: st.info("A recognizable year field and at least one other numeric measure are required for forecasting.")

with t_ai:
    st.subheader("AI Analyst · Your business, understood in context")
    st.markdown('<div class="panel"><span class="pill">Context-aware threads</span><span class="pill">Local calculation tools</span><span class="pill">Responses API function calling</span><span class="pill">Structured analyst reports</span><p style="margin:.7rem 0 0;color:#b6c6dc">Ask a question, challenge the answer, compare periods, or follow the thread. The model can request safe Python analytics tools and explain their returned evidence.</p></div>',unsafe_allow_html=True)
    st.caption("Privacy: when LLM mode is enabled, the question, recent messages, field metadata and calculated tool outputs are sent to OpenAI. Raw dataframe rows are not passed to the agent tools. External web research is optional.")
    tid=st.session_state.if_current
    thread=st.session_state.if_threads[tid]
    messages=thread["messages"]
    if not messages:
        st.markdown("#### Start with a business question")
        prompts=["How has the company performed overall?","What is driving the change in revenue?","Which year had the highest revenue?","What data limitations should I know about?"]
        pcols=st.columns(2)
        for i,p in enumerate(prompts):
            if pcols[i%2].button(p,key=f"suggest_{tid}_{i}",use_container_width=True):
                st.session_state.pending_question=p
                st.rerun()
    for m in messages:
        with st.chat_message(m["role"]):  # Let Streamlit choose its built-in role avatar; avoids treating symbols as image paths.
            st.markdown(m["content"])
            if m.get("source")=="LLM": st.caption("LLM-assisted · grounded in calculated dataset evidence")
            elif m.get("source")=="Local": st.caption("Local analytical mode · calculated from uploaded data")
            if m.get("chart_data") is not None:
                cd=pd.DataFrame(m["chart_data"])
                if {"period","value"}.issubset(cd.columns):
                    st.plotly_chart(px.line(cd,x="period",y="value",markers=True).update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)"),use_container_width=True)
            if m.get("correlations"):
                st.caption("Calculated correlation coefficients — associations do not establish causation.")
                st.dataframe(pd.DataFrame(m["correlations"]),use_container_width=True)
            if m.get("agent_meta"):
                meta = m["agent_meta"]
                with st.expander("Analysis trace · tools, model and usage"):
                    st.write(f"**Model:** {meta.get('model', 'Not recorded')}  ·  **API requests:** {meta.get('api_requests', 0)}")
                    usage = meta.get("usage", {})
                    st.write(f"**Tokens:** {usage.get('input_tokens', '—')} input / {usage.get('output_tokens', '—')} output / {usage.get('total_tokens', '—')} total")
                    calls = meta.get("tool_calls", [])
                    if calls:
                        st.dataframe(pd.DataFrame(calls), use_container_width=True, hide_index=True)
                    else:
                        st.caption("No local analytics function call was needed for this response.")
                    for source_item in meta.get("sources", []):
                        st.markdown(f"- [{source_item.get('title', 'External source')}]({source_item.get('url', '')})")
    pending=st.session_state.pop("pending_question",None)
    # Use an explicit form inside the AI Analyst tab instead of st.chat_input.
    # This keeps the question composer visible and editable within the selected tab
    # across Streamlit/browser layouts where the docked chat_input can be confusing.
    with st.form(key=f"analyst_question_form_{tid}", clear_on_submit=True):
        question_text = st.text_area(
            "Your question",
            placeholder="Type a question about your data, then click Send to analyst. Example: How did revenue and operating income change between 2021 and 2025?",
            height=100,
            key=f"analyst_question_text_{tid}",
            help="Ask a new question or a follow-up. InsightFlow keeps the active thread's previous questions and answers in context."
        )
        submitted = st.form_submit_button("Send to analyst  →", type="primary")
    question = (question_text or "").strip() if submitted else None
    if pending:
        question = pending
    if question:
        messages.append({"role":"user","content":question})
        previous_user = next((m["content"] for m in reversed(messages[:-1]) if m.get("role") == "user"), "")
        followup_markers = ["what about", "and ", "same for", "compare that", "why did it", "why was it", "what changed", "that year", "the previous year"]
        is_short_followup = len(question.split()) <= 6 or any(marker in question.lower() for marker in followup_markers)
        evidence_question = f"{previous_user}. Follow-up question: {question}" if previous_user and is_short_followup else question
        evidence=build_evidence(evidence_question,df)
        agent_meta = None
        with st.spinner("InsightFlow is examining the question, selecting analytics tools and preparing an evidence-based response…"):
            remaining_requests = max(0, int(session_call_limit) - int(st.session_state.if_api_requests))
            if api_key and share_analytics and remaining_requests >= 2:
                def record_api_attempt():
                    # Count each API attempt immediately, including failed calls, to keep the session cap meaningful.
                    st.session_state.if_api_requests += 1
                try:
                    agent_result = run_responses_agent(
                        question=question,
                        history=messages[:-1],
                        df=df,
                        dataset_label=data_label,
                        api_key=api_key,
                        model=model.strip(),
                        reasoning_effort=reasoning_effort,
                        reasoning_mode=reasoning_mode,
                        answer_depth=answer_depth,
                        use_web_search=use_web_search,
                        max_tool_rounds=max_tool_rounds,
                        max_api_requests=min(remaining_requests, max_tool_rounds + 1),
                        on_api_request=record_api_attempt,
                    )
                    reply = agent_result["answer"]
                    mode = "OpenAI Responses agent"
                    agent_meta = {k: agent_result.get(k) for k in ["model", "prompt_version", "api_requests", "api_request_budget", "tool_calls", "usage", "sources", "structured"]}
                except Exception as e:
                    reply=local_answer(question,evidence,df)
                    mode="Local fallback"
                    st.warning(f"The OpenAI agent could not complete this request ({type(e).__name__}: {str(e)[:220]}). InsightFlow has shown the locally calculated answer instead.")
            else:
                reply=local_answer(question,evidence,df)
                mode="Local"
                if api_key and not share_analytics:
                    reply += "\n\n*LLM mode is paused because data-sharing consent is off. Enable it in the sidebar to use the OpenAI Responses API agent.*"
                elif api_key and remaining_requests < 2:
                    reply += "\n\n*Fewer than two API requests remain in this session. InsightFlow used local analysis rather than start an agent turn that could not complete its final answer. Increase the session limit or start a new session.*"
                elif not api_key:
                    reply += "\n\n*To enable OpenAI Responses API reasoning, add your API key in the sidebar and explicitly enable data-sharing consent. Local analysis remains available without it.*"
        messages.append({"role":"assistant","content":reply,"source":mode,"chart_data":evidence.get("facts",[{}])[0].get("period_values") if evidence.get("facts") else None,"correlations":evidence.get("correlations"),"agent_meta":agent_meta})
        if len(messages)==2 and thread["title"]=="New analysis":
            thread["title"]=question[:42]+("…" if len(question)>42 else "")
        st.rerun()
    if messages and st.button("Export this conversation",key=f"export_{tid}"):
        content="\n\n".join(f"{m['role'].upper()}:\n{m['content']}" for m in messages)
        st.download_button("Download conversation (.md)",content.encode(),"insightflow_conversation.md","text/markdown")

with t_reco:
    st.subheader("Decision support")
    st.caption("Rule-based signals derived from the uploaded dataset. Validate business context before acting.")
    recommendations=[]
    for phrase,label in [("revenue","Revenue"),("gross profit","Gross profit"),("net income","Net income"),("employees","Employees"),("deliveries","Deliveries")]:
        c=resolve_metric(df,phrase)
        if c and yc:
            tmp=pd.DataFrame({"year":pd.to_numeric(df[yc],errors="coerce"),"v":pd.to_numeric(df[c],errors="coerce")}).dropna().groupby("year",as_index=False).v.sum().sort_values("year")
            if len(tmp)>=2:
                delta=tmp.v.iloc[-1]-tmp.v.iloc[-2]
                pct=delta/abs(tmp.v.iloc[-2])*100 if tmp.v.iloc[-2] else np.nan
                recommendations.append((label,c,delta,pct))
    if recommendations:
        for label,c,delta,pct in recommendations:
            direction="increased" if delta>=0 else "declined"
            change_text = f"{abs(pct):.1f}%" if np.isfinite(pct) else "percentage change unavailable (prior value was zero)"
            st.markdown(f'<div class="panel"><b>{safe_html_text(label)}</b><h3 style="margin:.25rem 0">{safe_html_text(direction.title())} {safe_html_text(change_text)} period over period</h3><span class="caption">Based on {safe_html_text(pretty(c))} and the two latest available periods. Review the underlying drivers before attributing cause.</span></div>',unsafe_allow_html=True)
            st.write("")
    else: st.info("No period-over-period recommendations can be generated from the fields currently available.")

with t_reports:
    st.subheader("Reports & exports")
    st.download_button("Download cleaned dataset (CSV)",safe_csv_bytes(df),"insightflow_cleaned_dataset.csv","text/csv")
    report=[f"INSIGHTFLOW DATASET REPORT",f"Generated: {datetime.now().isoformat(timespec='minutes')}",f"Dataset: {data_label}",f"Rows: {len(df)}",f"Columns: {len(df.columns)}",f"Missing cells: {profile['missing_cells']}",f"Duplicate rows: {profile['duplicate_rows']}","","FIELD PROFILE"]
    for c in df.columns: report.append(f"{c}: type={df[c].dtype}; missing={df[c].isna().sum()}; unique={df[c].nunique(dropna=True)}")
    report += ["","NUMERIC SUMMARY"]
    for c in num:
        s=pd.to_numeric(df[c],errors="coerce").dropna()
        if len(s): report.append(f"{c}: count={len(s)}; total={s.sum():.4f}; mean={s.mean():.4f}; min={s.min():.4f}; max={s.max():.4f}")
    st.download_button("Download dataset profile report (TXT)","\n".join(report).encode(),"insightflow_dataset_report.txt","text/plain")
