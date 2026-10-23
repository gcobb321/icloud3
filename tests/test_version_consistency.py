"""Keep the version in manifest.json, const.py and the release notes in sync."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"


def test_version_is_consistent() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    const_source = (COMPONENT / "const.py").read_text(encoding="utf-8")

    match = re.search(r"^VERSION\s*=\s*'([^']+)'", const_source, re.MULTILINE)
    assert match is not None, "VERSION not found in const.py"

    version = match.group(1)
    assert manifest["version"] == version
    assert (COMPONENT / "release_notes" / f"release_notes_v{version}.md").exists()


def test_changelog_lists_current_version() -> None:
    manifest = json.loads((COMPONENT / "manifest.json").read_text(encoding="utf-8"))
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    heading = re.compile(rf"^##\s+v?{re.escape(manifest['version'])}\b", re.MULTILINE)
    assert heading.search(changelog), (
        f"CHANGELOG.md has no '## v{manifest['version']}' section for the current VERSION"
    )
