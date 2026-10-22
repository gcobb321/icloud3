"""Source-level contracts for the config-entry lifecycle.

The integration cannot be imported without a Home Assistant test harness. These
checks guard the two regressions that caused zombie entities and an unload
KeyError: teardown must be driven by an explicit reload flag, and unload must
not index listener storage that may not exist.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INIT = ROOT / "custom_components/icloud3/__init__.py"


def test_unload_always_runs_the_full_teardown() -> None:
    source = INIT.read_text(encoding="utf-8")
    # A reload must unload the platforms: keeping them loaded while setup
    # skipped recreation left every device sensor 'unavailable'.
    assert "Gb.reload_in_progress or Gb.icloud3_reload_requested" not in source
    assert "Gb.was_icloud3_reloaded = False" in source
    assert "async_forward_entry_unload" in source
    assert "async def async_remove_entry" in source


def test_unload_does_not_index_missing_listener_keys() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert 'hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()' not in source
    assert 'hass.data[DOMAIN][entry.entry_id]["update_device_registry"]()' not in source
    assert 'hass.data[DOMAIN][entry.entry_id]["update_entity_registry"]()' not in source


def test_config_writes_are_serialized() -> None:
    source = (ROOT / "custom_components/icloud3/startup/config_file.py").read_text(
        encoding="utf-8")
    assert "_CONFIG_WRITE_LOCK" in source
    assert "with _CONFIG_WRITE_LOCK:" in source


def test_unload_resets_internal_sensor_objects() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert "Gb.EvLogSensor = None" in source
    assert "Gb.AlertsSensor = None" in source
    assert "Gb.WazeHistTrackSensor = None" in source


def test_unload_drops_sensor_links_so_reload_recreates_them() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert "Gb.Sensors_by_devicename.clear()" in source
    assert "Gb.Sensors_by_devicename_sensor.clear()" in source
    assert "Gb.sensors_cnt = 0" in source


def test_apple_device_data_tolerates_unassigned_device() -> None:
    source = (ROOT / "custom_components/icloud3/apple_acct/apple_acct_device_data.py").read_text(
        encoding="utf-8")
    assert "if self.Device is not None:" in source
    assert "new_device_data['Device']            = None" in source
