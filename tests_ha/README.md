# Home Assistant integration tests

These tests import the real integration and use the Home Assistant test
fixtures (`pytest-homeassistant-custom-component`). They live outside
`tests/` so the fast, Home-Assistant-free suite keeps running without the HA
dependency tree.

Run them with the matching Python/HA pair:

```bash
pip install pytest pytest-asyncio pytest-homeassistant-custom-component
pip install srp fido2 curl_cffi
pytest -q tests_ha
```

The CI job `ha-integration` uses Python 3.14 and the latest plugin.
