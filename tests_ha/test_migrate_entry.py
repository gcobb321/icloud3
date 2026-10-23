"""Config-entry migration contracts under the real HA runtime."""

from __future__ import annotations

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.icloud3 import async_migrate_entry
from custom_components.icloud3.const import DOMAIN


def _entry(version=1, minor_version=1):
    return MockConfigEntry(
        domain=DOMAIN,
        version=version,
        minor_version=minor_version,
        data={},
    )


async def test_supported_version_is_accepted(hass):
    entry = _entry()
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is True


async def test_newer_entry_is_rejected(hass):
    entry = _entry(version=99)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False


async def test_newer_minor_version_is_rejected(hass):
    entry = _entry(minor_version=99)
    entry.add_to_hass(hass)

    assert await async_migrate_entry(hass, entry) is False


async def test_integration_config_flow_is_discoverable(hass):
    from custom_components.icloud3.config_flow import iCloud3_ConfigFlow

    assert iCloud3_ConfigFlow.VERSION >= 1
