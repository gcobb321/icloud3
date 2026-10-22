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


def test_unload_uses_explicit_reload_flag() -> None:
    source = INIT.read_text(encoding="utf-8")
    assert "Gb.reload_in_progress or Gb.icloud3_reload_requested" in source
    assert "Gb.reload_in_progress = False" in source
    assert "Gb.was_icloud3_reloaded = True" in source
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
