from __future__ import annotations

import json
from types import SimpleNamespace

import pandas as pd
import pytest

from insightflow_agent import (
    ANSWER_SCHEMA,
    FUNCTION_TOOLS,
    execute_analytics_tool,
    run_responses_agent,
    _extract_sources,
)


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "fiscal_year": [2021, 2022, 2023, 2024, 2025],
        "region": ["North", "South", "North", "South", "North"],
        "revenue_usd_m": [100, 120, 150, 180, 170],
        "gross_profit_usd_m": [30, 36, 45, 54, 48],
        "employee_count": [1000, 1100, 1200, 1250, 1300],
    })




def test_tool_registry_is_strict_and_whitelisted():
    names = {tool["name"] for tool in FUNCTION_TOOLS}
    assert names == {
        "inspect_dataset", "aggregate_metric", "compare_periods",
        "correlation_matrix", "forecast_metric", "categorical_distribution", "data_quality_report",
        "segment_contribution", "numeric_profile", "growth_analysis", "cross_tabulate", "ratio_analysis",
    }
    assert all(tool.get("strict") is True for tool in FUNCTION_TOOLS)
    assert ANSWER_SCHEMA["additionalProperties"] is False


def test_inspect_dataset_returns_metadata_not_raw_rows(sample_df):
    result = execute_analytics_tool("inspect_dataset", {}, sample_df)
    assert result["ok"] is True
    assert result["rows"] == 5
    assert result["columns"] == 5
    assert "revenue_usd_m" in result["numeric_fields"]
    assert "sample_rows" not in result


def test_aggregate_total(sample_df):
    result = execute_analytics_tool("aggregate_metric", {
        "metric_field": "revenue", "aggregation": "sum", "group_by": None, "top_n": 10,
    }, sample_df)
    assert result["ok"] is True
    assert result["metric"] == "revenue_usd_m"
    assert result["value"] == 720


def test_aggregate_by_dimension(sample_df):
    result = execute_analytics_tool("aggregate_metric", {
        "metric_field": "revenue_usd_m", "aggregation": "sum", "group_by": "region", "top_n": 10,
    }, sample_df)
    assert result["ok"] is True
    assert result["groups"][0] == {"category": "North", "value": 420}


def test_compare_periods(sample_df):
    result = execute_analytics_tool("compare_periods", {
        "metric_field": "revenue_usd_m", "period_field": "fiscal_year",
        "start_period": "2022", "end_period": "2024",
    }, sample_df)
    assert result["ok"] is True
    assert result["observations"] == 3
    assert result["absolute_change_first_to_last"] == 60


def test_correlation_matrix(sample_df):
    result = execute_analytics_tool("correlation_matrix", {"fields": ["revenue_usd_m", "gross_profit_usd_m"]}, sample_df)
    assert result["ok"] is True
    assert result["matrix"]["revenue_usd_m"]["gross_profit_usd_m"] == 0.993 or result["matrix"]["revenue_usd_m"]["gross_profit_usd_m"] > 0.98
    assert "does not establish causation" in result["warning"]


def test_forecast_is_caveated(sample_df):
    result = execute_analytics_tool("forecast_metric", {
        "metric_field": "revenue_usd_m", "period_field": "fiscal_year", "periods_ahead": 2,
    }, sample_df)
    assert result["ok"] is True
    assert len(result["forecasts"]) == 2
    assert result["forecasts"][0]["period"] == 2026.0
    assert "Exploratory extrapolation" in result["warning"]


def test_categorical_distribution():
    df = pd.DataFrame({"region": ["North", "South", "North", "West", None]})
    result = execute_analytics_tool("categorical_distribution", {"category_field": "region", "top_n": 5}, df)
    assert result["ok"] is True
    assert result["categories"][0]["category"] == "North"
    assert result["categories"][0]["share_pct"] == 50.0


def test_sensitive_personal_dimension_is_blocked():
    df = pd.DataFrame({"customer_id": ["C1", "C2", "C1"], "sales": [10, 20, 30]})
    result = execute_analytics_tool("aggregate_metric", {
        "metric_field": "sales", "aggregation": "sum", "group_by": "customer_id", "top_n": 10,
    }, df)
    assert result["ok"] is False
    assert "blocked" in result["error"].lower()


def test_data_quality_and_outlier_screen():
    df = pd.DataFrame({"sales": [10, 11, 12, 13, 14, 100], "segment": ["A", "A", None, "B", "B", "B"]})
    result = execute_analytics_tool("data_quality_report", {"numeric_field": "sales"}, df)
    assert result["ok"] is True
    assert result["missing_cells"] == 1
    assert result["outlier_screen"]["flagged_count"] == 1


def test_invalid_column_is_refused(sample_df):
    result = execute_analytics_tool("aggregate_metric", {
        "metric_field": "confidential_salary", "aggregation": "sum", "group_by": None, "top_n": 10,
    }, sample_df)
    assert result["ok"] is False
    assert "available_numeric_fields" in result


class FakeFunctionCall:
    type = "function_call"
    name = "aggregate_metric"
    call_id = "call_001"
    arguments = json.dumps({
        "metric_field": "revenue", "aggregation": "sum", "group_by": None, "top_n": 10,
    })


class FakeResponse:
    def __init__(self, output, output_text="", usage=None, response_id="resp_test"):
        self.output = output
        self.output_text = output_text
        self.usage = usage or SimpleNamespace(input_tokens=100, output_tokens=50, total_tokens=150)
        self.id = response_id


class FakeResponses:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if not self._responses:
            raise AssertionError("Unexpected additional Responses API request")
        return self._responses.pop(0)


class FakeClient:
    def __init__(self, responses):
        self.responses = FakeResponses(responses)


def test_responses_agent_executes_local_tool_then_returns_structured_answer(sample_df):
    final = {
        "direct_answer": "Revenue totals 720 (USD millions).",
        "executive_summary": "The sum is calculated from five annual records.",
        "findings": [{"title": "Revenue", "evidence": "720", "interpretation": "Total over the sample period."}],
        "business_implications": ["The total is descriptive, not a forward-looking result."],
        "recommendations": [{"priority": "Medium", "action": "Review annual trend", "rationale": "Check inflection periods", "metric_to_monitor": "Revenue"}],
        "limitations": ["Five observations only."],
        "follow_up_questions": ["Would you like a year-by-year comparison?"],
    }
    fake = FakeClient([
        FakeResponse([FakeFunctionCall()], output_text=""),
        FakeResponse([SimpleNamespace(type="message", content=[])], output_text=json.dumps(final)),
    ])
    result = run_responses_agent(
        question="What is total revenue?", history=[], df=sample_df,
        dataset_label="QA sample", api_key="sk-test-not-real", model="gpt-6-astra",
        client=fake,
    )
    assert "Revenue totals 720" in result["answer"]
    assert result["mode"] == "OpenAI Responses agent"
    assert result["api_requests"] == 2
    assert result["tool_calls"][0]["tool"] == "aggregate_metric"
    assert "function_call_output" in str(fake.responses.calls[1]["input"])


def test_responses_agent_respects_tool_round_limit(sample_df):
    class AlwaysCall(FakeResponses):
        def create(self, **kwargs):
            self.calls.append(kwargs)
            if len(self.calls) == 1:
                return FakeResponse([FakeFunctionCall()])
            return FakeResponse([], output_text="Final bounded answer")

    fake = FakeClient([])
    fake.responses = AlwaysCall([])
    result = run_responses_agent(
        question="Summarize revenue", history=[], df=sample_df,
        dataset_label="QA sample", api_key="sk-test-not-real", model="gpt-6-astra",
        max_tool_rounds=1, client=fake,
    )
    assert result["answer"] == "Final bounded answer"
    assert result["api_requests"] == 2
    assert "tools" not in fake.responses.calls[-1]


def test_web_search_is_opt_in(sample_df):
    final = {"direct_answer": "Answer", "executive_summary": "Summary", "findings": [],
             "business_implications": [], "recommendations": [], "limitations": [], "follow_up_questions": []}
    fake = FakeClient([FakeResponse([], output_text=json.dumps(final))])
    run_responses_agent("How is this data?", [], sample_df, "QA", "sk-test-not-real", client=fake)
    assert not any(t.get("type") == "web_search" for t in fake.responses.calls[0]["tools"])
    fake2 = FakeClient([FakeResponse([], output_text=json.dumps(final))])
    run_responses_agent("How is this data?", [], sample_df, "QA", "sk-test-not-real", use_web_search=True, client=fake2)
    assert any(t.get("type") == "web_search" for t in fake2.responses.calls[0]["tools"])


def test_openai_prompt_does_not_include_dataframe_rows(sample_df):
    final = {"direct_answer": "Answer", "executive_summary": "Summary", "findings": [],
             "business_implications": [], "recommendations": [], "limitations": [], "follow_up_questions": []}
    fake = FakeClient([FakeResponse([], output_text=json.dumps(final))])
    run_responses_agent("Summarize", [], sample_df, "QA", "sk-test-not-real", client=fake)
    prompt_text = str(fake.responses.calls[0]["instructions"]) + str(fake.responses.calls[0]["input"])
    assert "1000" not in prompt_text  # employee_count values are not shipped as raw rows.
    assert "employee_count" in prompt_text  # field metadata is shared after consent.


def test_segment_contribution_calculates_share(sample_df):
    result = execute_analytics_tool("segment_contribution", {
        "metric_field": "revenue", "group_by": "region", "top_n": 10,
    }, sample_df)
    assert result["ok"] is True
    assert result["groups"][0]["category"] == "North"
    assert result["groups"][0]["value"] == 420
    assert result["groups"][0]["contribution_pct"] == pytest.approx(58.333, abs=0.001)


def test_numeric_profile_returns_distribution_statistics(sample_df):
    result = execute_analytics_tool("numeric_profile", {"numeric_field": "revenue_usd_m"}, sample_df)
    assert result["ok"] is True
    assert result["valid_count"] == 5
    assert result["min"] == 100
    assert result["max"] == 180
    assert "iqr_outlier_count" in result


def test_growth_analysis_calculates_adjacent_growth_and_cagr(sample_df):
    result = execute_analytics_tool("growth_analysis", {
        "metric_field": "revenue", "period_field": "fiscal_year",
    }, sample_df)
    assert result["ok"] is True
    assert result["period_count"] == 5
    assert result["periods"][1]["growth_pct"] == pytest.approx(20.0)
    assert result["cagr_pct"] is not None


def test_cross_tabulate_returns_bounded_counts(sample_df):
    result = execute_analytics_tool("cross_tabulate", {
        "row_field": "region", "column_field": "fiscal_year", "top_n": 5,
    }, sample_df)
    assert result["ok"] is True
    assert result["cells_returned"] <= 5
    assert all("count" in cell for cell in result["cells"])


def test_cross_tabulate_blocks_sensitive_fields(sample_df):
    df = sample_df.assign(customer_email=["a@example.com"] * 5)
    result = execute_analytics_tool("cross_tabulate", {
        "row_field": "region", "column_field": "customer_email", "top_n": 5,
    }, df)
    assert result["ok"] is False
    assert "blocked" in result["error"].lower()


def test_gpt6_pro_reasoning_parameters_are_passed(sample_df):
    final = {"direct_answer": "Answer", "executive_summary": "Summary", "findings": [],
             "business_implications": [], "recommendations": [], "limitations": [], "follow_up_questions": []}
    fake = FakeClient([FakeResponse([], output_text=json.dumps(final))])
    run_responses_agent(
        "Summarize", [], sample_df, "QA", "sk-test-not-real", client=fake,
        model="gpt-6-astra", reasoning_effort="max", reasoning_mode="pro",
    )
    assert fake.responses.calls[0]["reasoning"] == {"effort": "max", "mode": "pro"}
    assert fake.responses.calls[0]["store"] is False
    assert all(call["store"] is False for call in fake.responses.calls)


def test_ratio_analysis_calculates_weighted_margin(sample_df):
    result = execute_analytics_tool("ratio_analysis", {
        "numerator_field": "gross_profit_usd_m", "denominator_field": "revenue_usd_m",
        "multiplier": 100, "method": "ratio_of_sums", "group_by": None,
    }, sample_df)
    assert result["ok"] is True
    assert result["ratio"] == pytest.approx((213 / 720) * 100)


def test_ratio_analysis_grouped_by_region(sample_df):
    result = execute_analytics_tool("ratio_analysis", {
        "numerator_field": "gross_profit_usd_m", "denominator_field": "revenue_usd_m",
        "multiplier": 100, "method": "ratio_of_sums", "group_by": "region",
    }, sample_df)
    assert result["ok"] is True
    assert len(result["groups"]) == 2
    assert all("ratio" in group for group in result["groups"])


def test_growth_analysis_handles_unsorted_periods(sample_df):
    shuffled = sample_df.sample(frac=1, random_state=7)
    result = execute_analytics_tool("growth_analysis", {
        "metric_field": "revenue", "period_field": "fiscal_year",
    }, shuffled)
    assert result["ok"] is True
    assert [row["period"] for row in result["periods"]] == [2021, 2022, 2023, 2024, 2025]


def test_api_request_budget_and_callback_are_enforced(sample_df):
    final = {"direct_answer": "Bounded answer", "executive_summary": "Summary", "findings": [],
             "business_implications": [], "recommendations": [], "limitations": [], "follow_up_questions": []}
    fake = FakeClient([FakeResponse([FakeFunctionCall()]), FakeResponse([], output_text=json.dumps(final))])
    counted = []
    result = run_responses_agent(
        question="Summarize revenue", history=[], df=sample_df,
        dataset_label="QA", api_key="sk-test-not-real", client=fake,
        max_api_requests=2, max_tool_rounds=6, on_api_request=lambda: counted.append(1),
    )
    assert result["api_requests"] == 2
    assert result["api_request_budget"] == 2
    assert len(counted) == 2
    assert "tools" not in fake.responses.calls[-1]


def test_api_callback_counts_failed_request_attempt(sample_df):
    class FailingResponses:
        def create(self, **kwargs):
            raise TimeoutError("mock timeout")
    client = SimpleNamespace(responses=FailingResponses())
    counted = []
    with pytest.raises(TimeoutError):
        run_responses_agent("Summarize", [], sample_df, "QA", "sk-test-not-real",
                            client=client, on_api_request=lambda: counted.append(True))
    assert counted == [True]


def test_max_reasoning_effort_and_pro_mode_are_passed(sample_df):
    final = {"direct_answer": "Answer", "executive_summary": "Summary", "findings": [],
             "business_implications": [], "recommendations": [], "limitations": [], "follow_up_questions": []}
    fake = FakeClient([FakeResponse([], output_text=json.dumps(final))])
    run_responses_agent("Summarize", [], sample_df, "QA", "sk-test-not-real", client=fake,
                        model="gpt-6-astra", reasoning_effort="max", reasoning_mode="pro")
    assert fake.responses.calls[0]["reasoning"] == {"effort": "max", "mode": "pro"}


def test_strict_function_schemas_require_all_declared_properties():
    for tool in FUNCTION_TOOLS:
        parameters = tool["parameters"]
        assert tool["strict"] is True
        assert parameters["additionalProperties"] is False
        assert set(parameters["required"]) == set(parameters["properties"])


def test_correlation_reports_pairwise_observation_counts():
    df = pd.DataFrame({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, None, 8, 10],
        "c": [None, None, 3, 6, 9],
    })
    result = execute_analytics_tool("correlation_matrix", {"fields": ["a", "b", "c"]}, df)
    assert result["ok"] is True
    assert result["pairwise_observations"]["a"]["b"] == 4
    assert result["pairwise_observations"]["a"]["c"] == 3
    assert result["pairwise_observations"]["b"]["c"] == 2
    assert result["complete_case_observations"] == 2
    assert "observations_per_pair" not in result


def test_web_search_sources_are_extracted_and_unsafe_schemes_rejected():
    response = SimpleNamespace(output=[
        SimpleNamespace(type="web_search_call", action=SimpleNamespace(sources=[
            SimpleNamespace(title="Official [source](javascript:alert(1))", url="https://example.com/report"),
            SimpleNamespace(title="Unsafe", url="javascript:alert(1)"),
        ])),
        SimpleNamespace(type="message", content=[SimpleNamespace(annotations=[
            SimpleNamespace(title="Cited page", url="https://example.org/page"),
        ])]),
    ])
    sources = _extract_sources(response)
    assert sources == [
        {"title": "Official source javascript:alert 1", "url": "https://example.com/report"},
        {"title": "Cited page", "url": "https://example.org/page"},
    ]
