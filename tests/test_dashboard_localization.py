"""Run with: python -m unittest discover -s tests -p 'test_dashboard_localization.py'."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components" / "icloud3"
spec = importlib.util.spec_from_file_location(
    "dashboard_localization", COMPONENT / "configure" / "dashboard_localization.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class DashboardLocalizationTest(unittest.TestCase):
    def test_builtin_labels(self):
        self.assertEqual(module.dashboard_text("Main", "zh-Hans"), "主页")
        self.assertEqual(module.dashboard_text("NextUpdt", "zh-Hans"), "下次更新")

    def test_other_languages_are_unchanged(self):
        for language in ("en", "fr", "zh-Hant"):
            self.assertEqual(module.dashboard_text("Main", language), "Main")

    def test_user_text_and_identifiers_are_preserved(self):
        original = {
            "title": "Other Devices",
            "path": "other-devices",
            "cards": [{"entity": "sensor.my_phone_home_distance", "name": "^fname"},
                      {"name": "李李的iPhone"}],
        }
        translated = module.localize_template(original, "zh-Hans")
        self.assertEqual(translated["title"], "其他设备")
        self.assertEqual(translated["path"], original["path"])
        self.assertEqual(translated["cards"], original["cards"])
        self.assertEqual(original["title"], "Other Devices")

    def test_template_placeholders_are_preserved(self):
        text = "<h4><br>🀫 Combined Group (results+status+info) → ^fname</h4>"
        self.assertIn("^fname", module.dashboard_text(text, "zh-Hans"))

    def test_all_template_structures_are_preserved(self):
        def structure(value):
            if isinstance(value, dict):
                return {key: structure(item) for key, item in value.items()}
            if isinstance(value, list):
                return [structure(item) for item in value]
            return type(value).__name__
        for filename in (COMPONENT / "configure" / "dashboard_templates").glob("*.json"):
            original = json.loads(filename.read_text(encoding="utf-8"))
            translated = module.localize_template(original, "zh-Hans")
            self.assertEqual(structure(original), structure(translated), filename.name)
            json.dumps(translated, ensure_ascii=False)


if __name__ == "__main__":
    unittest.main()
