"""Diagnostics must never expose account names, secrets or locations."""

from __future__ import annotations

import asyncio
import sys
import types
from types import SimpleNamespace

import pytest


def _install_diagnostics_stub() -> None:
    """Provide the tiny HA helper diagnostics.py imports at call time."""

    if "homeassistant.components.diagnostics" in sys.modules:
        return

    ha = types.ModuleType("homeassistant")
    ha.__path__ = []  # type: ignore[attr-defined]
    components = types.ModuleType("homeassistant.components")
    components.__path__ = []  # type: ignore[attr-defined]
    diagnostics = types.ModuleType("homeassistant.components.diagnostics")

    def async_redact_data(data, to_redact):
        keys = set(to_redact)

        def walk(value):
            if isinstance(value, dict):
                return {
                    key: ("**REDACTED**" if key in keys else walk(item))
                    for key, item in value.items()
                }
            if isinstance(value, list):
                return [walk(item) for item in value]
            return value

        return walk(data)

    diagnostics.async_redact_data = async_redact_data
    sys.modules.setdefault("homeassistant", ha)
    sys.modules.setdefault("homeassistant.components", components)
    sys.modules["homeassistant.components.diagnostics"] = diagnostics


@pytest.fixture()
def diagnostics(diagnostics_module):
    _install_diagnostics_stub()
    return diagnostics_module


def test_config_entry_diagnostics_redacts_secrets(diagnostics) -> None:
    entry = SimpleNamespace(
        data={
            "username": "person@example.com",
            "password": "secret",
            "access_token": "token-value",
            "region": "eu",
        },
        options={"latitude": 41.0, "longitude": 29.0, "log_level": "info"},
    )
    hass = SimpleNamespace(config=SimpleNamespace(version="2026.10.0"))

    result = asyncio.run(
        diagnostics.async_get_config_entry_diagnostics(hass, entry)
    )

    assert result["config_entry"]["data"]["username"] == "**REDACTED**"
    assert result["config_entry"]["data"]["password"] == "**REDACTED**"
    assert result["config_entry"]["data"]["access_token"] == "**REDACTED**"
    assert result["config_entry"]["data"]["region"] == "eu"
    assert result["config_entry"]["options"]["latitude"] == "**REDACTED**"
    assert result["config_entry"]["options"]["log_level"] == "info"


def test_diagnostics_counts_are_numbers(diagnostics) -> None:
    counts = diagnostics._counts()

    assert isinstance(counts, dict)
    assert all(isinstance(value, int) for value in counts.values())
    assert counts["devices"] >= 0
    assert counts["apple_accounts"] >= 0


def test_conf_profile_has_no_account_fields(diagnostics) -> None:
    profile = diagnostics._conf_profile()

    assert isinstance(profile, dict)
    for key in ("username", "password", "email", "latitude", "longitude"):
        assert key not in profile
