# Waze route calculator tests

test_waze_hotfix.py tests the iCloud3 synchronous Waze client in isolation,
without loading Home Assistant and without using actual device/GPS data.
The tests mock the requests library and the curl_cffi Session used for an
HTTP 403 fallback. They cover successful routing, IL endpoint selection,
403 retry with a fresh Chrome-impersonating session, repeated requests,
non-403 errors, invalid JSON, network failure, and route parsing.

## Mocked CI tests (default; no Waze traffic)

    python -m pip install pytest requests
    python -m pytest -q tests/test_waze_hotfix.py

## Optional live smoke test (requires internet and Waze service availability)

    python -m pip install pytest requests 'curl-cffi>=0.13.0'
    ICLOUD3_WAZE_LIVE_TEST=1 python -m pytest -q tests/test_waze_hotfix.py -k live

The live test contacts routing-livemap-il.waze.com using public Tel Aviv
coordinates. It checks for a positive distance and duration. It must be run
manually and is skipped in GitHub Actions, so CI cannot guarantee that the
external Waze service is currently reachable.
