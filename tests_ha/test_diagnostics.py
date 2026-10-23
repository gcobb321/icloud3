"""Diagnostics and health surface under the real HA runtime."""

from __future__ import annotations

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.icloud3.const import DOMAIN
from custom_components.icloud3.diagnostics import async_get_config_entry_diagnostics


async def test_diagnostics_redacts_entry_data(hass):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "person@example.com", "password": "secret", "region": "eu"},
    )
    entry.add_to_hass(hass)

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert result["config_entry"]["data"]["username"] == "**REDACTED**"
    assert result["config_entry"]["data"]["password"] == "**REDACTED**"
    assert result["config_entry"]["data"]["region"] == "eu"
    assert "health" in result


async def test_health_sensor_after_setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={})
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.icloud3_health")
    assert state is not None
    assert state.state in ("ok", "warning")

    assert "startup_stages_ms" in state.attributes
    stages = state.attributes["startup_stages_ms"]
    assert isinstance(stages, dict)
    assert "config_load" in stages
    assert all(isinstance(stage, str) for stage in stages)
    assert all(isinstance(value, (int, float)) for value in stages.values())

    assert "startup_total_ms" in state.attributes
    total = state.attributes["startup_total_ms"]
    assert isinstance(total, (int, float))
    assert total >= max(stages.values())

    result = await async_get_config_entry_diagnostics(hass, entry)

    assert "health" in result
    assert "last_error_message" in result["health"]
    assert "startup_stages_ms" in result["health"]
    assert "startup_total_ms" in result["health"]
