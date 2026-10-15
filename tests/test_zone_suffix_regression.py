"""Regression tests for iCloud3 registry cleanup with genuine zone suffixes.

Extract only the small registration helpers so these tests do not require a
running Home Assistant instance or iCloud credentials.
"""
import ast
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock


SOURCE = Path(__file__).resolve().parents[1] / "custom_components/icloud3/sensor.py"


def load_registry_functions(registry_entries=()):
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    names = {"_is_generated_numeric_sensor_suffix", "correct_sensor_entity_ids_with_2_extension"}
    nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
    sensor_cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "DeviceSensor_Base")
    method = next(n for n in sensor_cls.body if isinstance(n, ast.FunctionDef) and n.name == "repair_entity_2_suffix")
    code = compile(ast.fix_missing_locations(ast.Module(body=nodes + [method], type_ignores=[])), str(SOURCE), "exec")

    entity_reg = SimpleNamespace(entities={e.entity_id: e for e in registry_entries})
    change_id = Mock()
    remove_id = Mock()
    ns = {
        "er": SimpleNamespace(async_get=lambda hass: entity_reg),
        "Gb": SimpleNamespace(hass=object()),
        "PLATFORM_SENSOR": "sensor",
        "DOMAIN": "icloud3",
        "entity_io": SimpleNamespace(change_entity_id=change_id),
        "er_util": SimpleNamespace(remove_sensor=remove_id),
        "log_debug_msg": Mock(),
    }
    exec(code, ns)
    return SimpleNamespace(
        generated=ns["_is_generated_numeric_sensor_suffix"],
        cleanup=ns["correct_sensor_entity_ids_with_2_extension"],
        repair=ns["repair_entity_2_suffix"],
        change_id=change_id,
        remove_id=remove_id,
    )


def entry(entity_id, unique_id, platform="icloud3", domain="sensor"):
    return SimpleNamespace(entity_id=entity_id, unique_id=unique_id, platform=platform, domain=domain)


class SensorZoneSuffixTests(unittest.TestCase):
    def test_genuine_zone_x_is_never_a_numbered_duplicate(self):
        a = load_registry_functions()
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal_x", "sensor.avi_travel_time_terminal"))
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal_x", "sensor.avi_travel_time_terminal_x"))
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal", "sensor.avi_travel_time_terminal_x"))

    def test_numeric_suffix_only_when_appended_to_full_expected_id(self):
        a = load_registry_functions()
        self.assertTrue(a.generated("sensor.avi_travel_time_terminal_x_2", "sensor.avi_travel_time_terminal_x"))
        self.assertTrue(a.generated("sensor.avi_travel_time_terminal_10", "sensor.avi_travel_time_terminal"))
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal_1", "sensor.avi_travel_time_terminal"))
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal_2_extra", "sensor.avi_travel_time_terminal"))
        self.assertFalse(a.generated("sensor.avi_travel_time_terminal_2", "sensor.avi_travel_time_terminal_2"))

    def test_cleanup_preserves_zone_x_and_other_integrations(self):
        a = load_registry_functions([
            entry("sensor.avi_travel_time_terminal_x", "icloud3_avi_travel_time_terminal_x"),
            entry("sensor.avi_travel_time_terminal", "icloud3_avi_travel_time_terminal_x"),
            entry("sensor.other_2", "icloud3_other", platform="template"),
        ])
        self.assertFalse(a.cleanup(verify=True))
        self.assertFalse(a.cleanup())
        a.change_id.assert_not_called()
        a.remove_id.assert_not_called()

    def test_cleanup_renames_only_safe_numbered_icloud3_entity(self):
        a = load_registry_functions([
            entry("sensor.avi_travel_time_terminal_x_2", "icloud3_avi_travel_time_terminal_x"),
        ])
        self.assertTrue(a.cleanup(verify=True))
        a.change_id.assert_not_called()
        self.assertTrue(a.cleanup())
        a.change_id.assert_called_once_with(
            "sensor.avi_travel_time_terminal_x_2", "sensor.avi_travel_time_terminal_x"
        )
        a.remove_id.assert_not_called()

    def test_cleanup_never_overwrites_existing_registry_entity(self):
        a = load_registry_functions([
            entry("sensor.avi_travel_time_terminal_x_2", "icloud3_avi_travel_time_terminal_x"),
            entry("sensor.avi_travel_time_terminal_x", "icloud3_another_sensor"),
        ])
        self.assertFalse(a.cleanup(verify=True))
        a.change_id.assert_not_called()
        a.remove_id.assert_not_called()

    def test_auto_repair_preserves_user_renames_and_zone_x(self):
        a = load_registry_functions()
        obj = SimpleNamespace(
            entity_id="sensor.avi_travel_time_terminal",
            entity_id_base="sensor.avi_travel_time_terminal_x",
        )
        a.repair(obj)
        a.change_id.assert_not_called()
        a.remove_id.assert_not_called()

    def test_auto_repair_only_changes_numeric_duplicate_when_base_is_free(self):
        a = load_registry_functions()
        obj = SimpleNamespace(
            entity_id="sensor.avi_travel_time_terminal_x_2",
            entity_id_base="sensor.avi_travel_time_terminal_x",
        )
        a.repair(obj)
        a.change_id.assert_called_once_with(
            "sensor.avi_travel_time_terminal_x_2", "sensor.avi_travel_time_terminal_x"
        )
        a.remove_id.assert_not_called()

    def test_auto_repair_never_deletes_occupied_target(self):
        a = load_registry_functions([
            entry("sensor.avi_travel_time_terminal_x", "icloud3_avi_travel_time_terminal_x"),
        ])
        obj = SimpleNamespace(
            entity_id="sensor.avi_travel_time_terminal_x_2",
            entity_id_base="sensor.avi_travel_time_terminal_x",
        )
        a.repair(obj)
        a.change_id.assert_not_called()
        a.remove_id.assert_not_called()


if __name__ == "__main__":
    unittest.main()
