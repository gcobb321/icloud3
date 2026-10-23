"""Tests for the Event Log display cache and the Waze History database pragmas.

Both modules import Home Assistant, so the cache class is loaded straight from
event_log.py by AST and everything that needs the module namespace is checked
against the source instead of being imported.
"""

from __future__ import annotations

import ast
import sqlite3
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"

CACHE_CLASS_NAME = "FilteredEvLogCache"


def component_source(relative_path: str) -> str:
    return (COMPONENT / relative_path).read_text(encoding="utf-8")


def function_node(module: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} was not found")


def function_source(module: ast.Module, source: str, name: str) -> str:
    return ast.get_source_segment(source, function_node(module, name)) or ""


def module_assignment(module: ast.Module, name: str) -> ast.expr:
    for node in module.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == name for target in node.targets
        ):
            return node.value
    raise AssertionError(f"{name} was not found")


def load_cache_class() -> Any:
    module = ast.parse(component_source("support/event_log.py"))
    class_node = next(
        node
        for node in module.body
        if isinstance(node, ast.ClassDef) and node.name == CACHE_CLASS_NAME
    )
    namespace: dict[str, Any] = {}
    class_module = ast.Module(body=[class_node], type_ignores=[])
    exec(compile(class_module, "<event_log>", "exec"), namespace)
    return namespace[CACHE_CLASS_NAME]


# --------------------------------------------------------------------------
# FilteredEvLogCache behaviour
# --------------------------------------------------------------------------
def test_cache_returns_none_for_an_unseen_key() -> None:
    cache = load_cache_class()(2)

    assert cache.get(("dev", 10, 3)) is None


def test_cache_returns_the_text_for_the_same_key() -> None:
    cache = load_cache_class()(2)

    cache.set(("dev", 10, 3), "text")

    assert cache.get(("dev", 10, 3)) == "text"


def test_cache_misses_when_a_key_element_changes() -> None:
    cache = load_cache_class()(2)
    cache.set(("dev", 10, 3), "text")

    assert cache.get(("dev", 10, 4)) is None
    assert cache.get(("dev", 11, 3)) is None
    assert cache.get(("other", 10, 3)) is None


def test_cache_keeps_only_the_last_entries() -> None:
    cache = load_cache_class()(2)

    for recd_cnt in (1, 2, 3):
        cache.set(("dev", recd_cnt), f"text{recd_cnt}")

    assert len(cache) == 2
    assert cache.get(("dev", 1)) is None
    assert cache.get(("dev", 2)) == "text2"
    assert cache.get(("dev", 3)) == "text3"


def test_cache_clear_drops_every_entry() -> None:
    cache = load_cache_class()(2)
    cache.set(("dev", 1), "text")
    cache.set(("dev", 2), "text")

    cache.clear()

    assert len(cache) == 0
    assert cache.get(("dev", 1)) is None


# --------------------------------------------------------------------------
# Event Log wiring
# --------------------------------------------------------------------------
def test_initialize_creates_the_filtered_cache() -> None:
    source = component_source("support/event_log.py")

    initialize = " ".join(function_source(ast.parse(source), source, "initialize").split())

    assert "self._filtered_cache = FilteredEvLogCache(" in initialize


def test_filtered_evlog_recds_reads_and_fills_the_cache() -> None:
    source = component_source("support/event_log.py")

    body = function_source(ast.parse(source), source, "_filtered_evlog_recds")

    assert "self._filtered_cache.get(cache_key)" in body
    assert "self._filtered_cache.set(cache_key, time_text_recds_str)" in body


def test_cache_key_covers_every_filter_input() -> None:
    module = ast.parse(component_source("support/event_log.py"))
    returns = [
        node
        for node in ast.walk(function_node(module, "_filtered_evlog_recds_cache_key"))
        if isinstance(node, ast.Return)
    ]

    assert len(returns) == 1
    key_expression = returns[0].value
    assert isinstance(key_expression, ast.Tuple)
    key_elements = {ast.unparse(element) for element in key_expression.elts}

    assert {
        "devicename",
        "max_recds",
        "len(self.event_recds)",
        "self.greenbar_alert_msg",
        "Gb.is_gps_lat_long_displayed",
        "Gb.is_evlog_trk_monitors_displayed",
        "Gb.is_evlog_startup_log_displayed",
        "self.devicename",
    } <= key_elements


def test_every_event_log_change_invalidates_the_cache() -> None:
    source = component_source("support/event_log.py")
    module = ast.parse(source)

    for function_name in (
        "_add_recd_to_event_recds",
        "_shrink_event_recds",
        "_save_startup_log_recd",
        "clear_greenbar_msg",
        "display_user_message",
    ):
        assert "self._filtered_cache.clear()" in function_source(module, source, function_name), function_name


def test_event_log_growth_paths_clear_a_shrunk_cache() -> None:
    source = component_source("support/event_log.py")

    body = function_source(ast.parse(source), source, "post_event")

    assert "_filtered_cache.clear()" in body


# --------------------------------------------------------------------------
# Waze History database pragmas
# --------------------------------------------------------------------------
def pragma_statements() -> list[str]:
    module = ast.parse(component_source("tracking/waze_history.py"))

    return [ast.literal_eval(element) for element in module_assignment(module, "SQL_PRAGMAS").elts]


def test_waze_history_pragma_set() -> None:
    pragmas = " ".join(pragma_statements())

    assert "journal_mode=WAL" in pragmas
    assert "synchronous=NORMAL" in pragmas
    assert "busy_timeout=5000" in pragmas
    assert "temp_store=MEMORY" in pragmas


def test_waze_history_pragmas_are_valid_sqlite_statements(tmp_path: Path) -> None:
    connection = sqlite3.connect(tmp_path / "wazehist.db")
    try:
        cursor = connection.cursor()
        for pragma in pragma_statements():
            cursor.execute(pragma)

        cursor.execute("PRAGMA journal_mode")
        journal_mode = cursor.fetchone()[0]
        cursor.execute("PRAGMA busy_timeout")
        busy_timeout = cursor.fetchone()[0]
    finally:
        connection.close()

    assert journal_mode.lower() == "wal"
    assert busy_timeout == 5000


def test_open_waze_history_database_applies_the_pragmas() -> None:
    source = component_source("tracking/waze_history.py")

    body = function_source(ast.parse(source), source, "open_waze_history_database")

    assert "self._apply_sql_pragmas()" in body


def test_pragma_failure_is_logged_and_keeps_the_connection() -> None:
    source = component_source("tracking/waze_history.py")
    node = function_node(ast.parse(source), "_apply_sql_pragmas")
    body = ast.get_source_segment(source, node) or ""

    assert any(isinstance(child, ast.Try) and child.handlers for child in ast.walk(node))
    assert "log_warning_msg" in body
    assert "self.connection = None" not in body
    assert ".close(" not in body
    assert "self._sql(" not in body
