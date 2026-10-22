# Unit tests

These tests cover the Home Assistant free helper modules:

- `custom_components/icloud3/startup/mobapp_resolver.py`
- `custom_components/icloud3/utils/backoff.py`

They do not import the integration package (which imports Home Assistant), so
they run without a Home Assistant test harness:

```bash
pip install pytest
pytest -q tests
```

Integration behaviour (config-entry unload, registry snapshots, Waze retry
loop) still needs the Home Assistant test harness or a staging instance.
