"""Diagnostics must never expose account names, secrets or locations."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest


@pytest.fixture()
def diagnostics(diagnostics_module):
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


def test_redaction_is_case_insensitive(diagnostics) -> None:
    payload = {
        "Username": "person@example.com",
        "PASSWORD": "secret",
        "Access_Token": "token-value",
        "nested": {"Latitude": 41.0, "safe": 1},
    }

    result = diagnostics._redact(payload)

    assert result["Username"] == "**REDACTED**"
    assert result["PASSWORD"] == "**REDACTED**"
    assert result["Access_Token"] == "**REDACTED**"
    assert result["nested"]["Latitude"] == "**REDACTED**"
    assert result["nested"]["safe"] == 1


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
