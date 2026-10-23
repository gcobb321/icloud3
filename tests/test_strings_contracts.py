"""Translation file contracts for the config and options flows.

Home Assistant resolves the keys in ``strings.json``/``translations/en.json`` at
runtime, so a missing key or a typo is shown to the user as a raw identifier
instead of a message. These checks read the JSON files directly and fail before
the integration is loaded.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components/icloud3"
STRINGS = COMPONENT / "strings.json"
ENGLISH = COMPONENT / "translations/en.json"

REPORTED_ERROR_KEYS = {
    "config": ("config_write_failed",),
    "options": ("config_write_failed", "reauth_apple_acct_unknown"),
}

REMOVED_TEXTS = ("xdescription", "bettery", "CURENT")


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def all_keys(node: Any) -> Iterator[str]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from all_keys(value)
    elif isinstance(node, list):
        for value in node:
            yield from all_keys(value)


def test_strings_json_is_valid() -> None:
    assert load(STRINGS)["title"]


def test_translations_en_json_is_valid() -> None:
    assert load(ENGLISH)["title"]


def test_reported_error_keys_are_translated() -> None:
    strings = load(STRINGS)
    english = load(ENGLISH)

    for section, keys in REPORTED_ERROR_KEYS.items():
        for key in keys:
            assert key in strings[section]["error"], f"{key} missing from {section}.error in strings.json"
            assert key in english[section]["error"], f"{key} missing from {section}.error in translations/en.json"


def test_translations_cover_strings_error_keys() -> None:
    strings = load(STRINGS)
    english = load(ENGLISH)

    for section in ("config", "options"):
        missing = sorted(set(strings[section]["error"]) - set(english[section]["error"]))
        assert not missing, f"{section}.error keys missing from translations/en.json: {missing}"


def test_stale_texts_are_removed() -> None:
    for path in (STRINGS, ENGLISH):
        text = path.read_text(encoding="utf-8")
        for stale in REMOVED_TEXTS:
            assert stale not in text, f"{stale} is still present in {path.name}"


def test_no_comment_keys_remain() -> None:
    for path in (STRINGS, ENGLISH):
        comments = [key for key in all_keys(load(path)) if key.startswith("_comment")]
        assert not comments, f"{path.name} still contains non-translation keys: {comments}"
