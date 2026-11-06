# Developer checks for Configure (optional)

Two optional checks for the iCloud3 Configure screens. They are not needed to use or
release iCloud3, and nothing here runs in Home Assistant.

## 1. Quick static checks (no Home Assistant needed)

```
python tests/check_configure.py
```

Takes about 20 seconds (tested with Python 3.14). `pip install pyflakes` adds the
undefined-name check; it is skipped without it. It checks:

- `strings.json` and `translations/en.json` have the same keys and texts, every
  translation file is valid JSON, and a translation has no placeholder the English text
  doesn't have.
- Every module imports (Home Assistant is replaced by stubs).
- Names the code uses exist: `module.name` and `self.name` in the flow classes. Each one
  raises `AttributeError` when its line runs.
- Text keys the code uses exist: selector options, menu rows, step texts, error keys.
- The `{placeholders}` of the screen texts get a value from the code, as the HA frontend
  passes them (for example, a menu title gets no placeholders).
- Text keys no code refers to (WARN, does not fail).

Exit code 1 if there is an ERROR. `-v` also lists the INFO lines. To check another copy
of the code: `python tests/check_configure.py DIR` (DIR contains `custom_components/icloud3`).

## 2. Offline Configure tests (pytest)

```
pip install pytest-homeassistant-custom-component==0.13.375 srp "fido2>=1.1.3" curl_cffi
pytest tests/
```

Version 0.13.375 installs Home Assistant 2026.10.4 with the matching pytest and
pytest-asyncio (Python 3.14). The other three are iCloud3's requirements from `manifest.json`. The tests start their own Home Assistant, so the package's
pytest plugin is turned off in `tests/pytest.ini`. Takes a few minutes.

Each test starts a real Home Assistant core in a temp directory, adds an iCloud3 config
entry without starting iCloud3, and builds the iCloud3 state from a test configuration file:
Apple Accounts (signed in, waiting for a code, Terms of Use, login failed), devices
(tracked, monitored, inactive, without an Apple Account) and the settings. Apple is a fake
that records the calls; the network is blocked. The real Home Assistant, the real
`.storage/icloud3` files and Apple are never touched.

The Configure windows are driven like the browser does through HA's REST API, and every
screen is checked like the HA frontend would show it: missing texts, raw keys, unfilled
`{placeholders}`, a broken screen after an error.

- `test_configure.py`: open and close Configure (the configuration file must not change);
  every settings screen saved with what it shows (same file in, same file out, the same
  values when opened again); bad input on every field; two Configure windows at the same
  time; a double click on Save; HA's reauth flow; the Repairs fix flows; a German
  translation. These work with the v3.8.0 menu.
- `test_configure_menus.py`: the tests for HA menus (`async_show_menu`): every row of every
  menu, the "Needs attention" rows. They skip themselves when the main screen is not an HA
  menu.

To test another copy of the code: `IC3_CODE_DIR=DIR pytest tests/`. `pytest tests/ -k two_windows`
runs one group.

## GitHub workflow

`.github/workflows/dev-checks.yml` runs both. It only runs when started by hand
(Actions > Developer checks > Run workflow), so it adds no checks to pushes or PRs.
