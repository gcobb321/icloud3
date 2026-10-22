# Unit tests

These tests cover the Home Assistant free modules and source-level contracts:

- `custom_components/icloud3/utils/pure.py` (timezone, validators, base64, dates)
- `custom_components/icloud3/utils/backoff.py`
- `custom_components/icloud3/startup/mobapp_resolver.py`
- `custom_components/icloud3/diagnostics.py` (redaction and counts)
- `tests/test_static_contracts.py` (regressions that already happened once)

They do not import the integration package (which imports Home Assistant), so
they run without a Home Assistant test harness:

```bash
pip install pytest pytest-cov
pytest -q tests
```

## Quality gate

CI runs:

1. `ruff check custom_components/icloud3` with the narrow breakage rules in
   `pyproject.toml` (`E9`, `F63`, `F7`, `F82`, `F821`).
2. `mypy` (strict) on `pure.py`, `backoff.py` and `mobapp_resolver.py`.
3. `pytest` with a 90% floor for `pure.py`.

The coverage floor deliberately covers only `pure.py`. Integration code
(config entry lifecycle, registry snapshots, Waze retry loop, repairs) still
needs a Home Assistant harness or a staging instance; the static contracts
guard the specific regressions listed in `test_static_contracts.py`.
