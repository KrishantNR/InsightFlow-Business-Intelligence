# InsightFlow GitHub release — QA verification

Verification date: 2026-11-06  
Release candidate: GitHub release candidate

Pytest is explicitly configured to collect only `tests/test_*.py`; the separately invoked `self_test.py` is not double-collected.

## Checks completed in the available build environment

| Check | Result | Scope |
|---|---:|---|
| Python compilation | PASS | Application, agent, launcher, self-test, scripts and pytest module |
| Pytest | PASS — 30 tests | Analytics functions, strict tool schemas, Responses API tool cycle mocks, request budget, callback failures, privacy controls and model parameters |
| Project self-test | PASS — 60 checks | Bundled datasets, CSV/XLSX loading, cleaning, spreadsheet formula export protection, HTML escaping, non-finite-value normalization, profiles, local analyst questions, context reset, 12 tools, nine production Visual Explorer chart types, negative-value Pie guard, launcher and mocked UI paths |
| Secret-pattern scan | PASS | No matching credential patterns or local `.env` / `secrets.toml` found in the release tree |
| Dataset audit | PASS | Tesla extract: 5 rows × 52 columns; 5 documented missing cells; 52 fields in the dictionary |
| Correlation count accuracy | PASS | Pairwise sample counts are reported separately; complete-case count is not mislabeled as pairwise |
| Responses API storage | PASS | `store=False` asserted in mocked request tests |
| ZIP integrity | PASS after packaging | CRC verification, expected release files and no embedded local secrets verified on the final archive |

## Environment limitations and checks not completed here

- This build environment does not have Streamlit or the OpenAI Python SDK installed, and outbound package-index access failed. A real Streamlit browser session and a live OpenAI API call could not be run in this environment.
- GitHub Actions is configured to test Python 3.11, 3.12 and 3.13 on Ubuntu and Windows, plus an Ubuntu Streamlit HTTP health smoke test. These hosted checks have not run until the repository is pushed to GitHub.
- `python -m pip check` in the shared build container reports a pre-existing global environment conflict: `moviepy 2.2.1` requires `pillow <12`, while the shared environment has `pillow 12.3.0`. MoviePy is not an InsightFlow requirement. The clean GitHub Actions runners run `pip check` after installing this project's requirements.
- No live OpenAI API key was supplied; no real API request or API charge was made.

## What these checks do not prove

- They do not prove every arbitrary CSV/XLSX layout, encoding, formula, workbook size or uploaded data type will be supported.
- Mocked Streamlit UI tests do not replace a real target-browser test.
- Mocked Responses API tests do not validate a real API key, project billing, model access, quota, latency, hosted web search, or every model's current behavior.
- The per-session request cap is not a monetary spend cap and is not a substitute for provider-side budget controls.
- `store=False` disables Responses API application-state storage for these requests; it is not a Zero Data Retention guarantee and does not remove all abuse-monitoring or tool-specific retention described by the provider.
- Sensitive-field checks are heuristic and cannot guarantee detection of every personal, confidential or regulated field.
- This release is an academic prototype; it has no production authentication, tenant isolation, durable database, row-level access controls or multi-user abuse protection.

## Required verification on the target Windows computer

1. Extract the release and run `START_INSIGHTFLOW.bat`.
2. Confirm the self-test completes and the Streamlit page opens.
3. Load the Tesla demo; test an overview, highest revenue year, margin ratio, a forecast and a missing-data question.
4. Switch to the retail sample; confirm the previous dataset's chat context is reset.
5. Upload one non-confidential CSV and one XLSX workbook.
6. If enabling LLM mode, enter your own API key, enable the explicit data-sharing consent, test model access and run the evaluation scenarios in `docs/EVALUATION_PROTOCOL.md`.
7. Save screenshots and record actual results. Do not mark live API or browser checks as passed until personally verified.
