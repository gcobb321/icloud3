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

Once the workflow exists on a repository's default branch, you can
also use **Actions > Waze Route Regression Tests > Run workflow**, choose a
branch, and enable **run_live_waze**. GitHub does not allow manual
`workflow_dispatch` events when the workflow file exists only on a
non-default branch. Until then, run the command above locally.
The `waze-live` job is separate from the mocked CI tests.

## Verified test runs (2026-10-13)

- Mocked regression tests: 14 passed, 1 skipped (live intentionally excluded).
- Live Israel routing smoke test: **1 passed**, using public Tel Aviv
  coordinates and the unmodified Waze server endpoint:
  https://github.com/matanmesika/icloud3/actions/runs/38361640376

This proves the revised calculator can successfully return a live route at
the time of the run; the server may have returned 200 on the initial HTTP
client request. The 403-to-Chrome fallback itself is exercised by mocked
regression tests, not proven by the live smoke test.

Integration behavior inside a running Home Assistant system is not covered.
