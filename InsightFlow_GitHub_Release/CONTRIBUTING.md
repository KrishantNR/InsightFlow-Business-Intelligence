# Contributing

This repository is an academic capstone prototype. Contributions should be focused, testable and documented.

## Development setup

```bash
python -m pip install -r requirements-dev.txt
```

## Before opening a pull request

```bash
python -m compileall -q app.py insightflow_agent.py launch_insightflow.py self_test.py scripts tests
python self_test.py
python -m pytest -q
python -m pip check
python scripts/check_secrets.py
```

For changes to the Streamlit interface, also run `python scripts/streamlit_smoke.py` where Streamlit can be installed.

## Contribution principles

- Add a regression test for every bug fix.
- Calculate numerical evidence in tested Python tools, not in prose-only prompt instructions.
- Do not add arbitrary code execution, raw SQL execution or unrestricted filesystem access to the model toolset.
- Keep function schemas strict and bounded.
- Document any change in data-sharing behavior.
- Never commit credentials or confidential company data.
- State assumptions, units, sample sizes and unsupported fields in the UI and documentation.
