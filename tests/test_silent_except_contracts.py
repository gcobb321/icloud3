"""Contracts for error handling in the data and network paths.

An exception handler that does nothing hides a failure: the caller sees an
empty result and reports "no problems" instead of "could not read". These
checks are source-level because the integration imports Home Assistant, so the
modules cannot be imported here.

Allowed handlers:
    * a bare ``except:`` is never allowed — it also swallows KeyboardInterrupt
      and SystemExit, so it must name ``Exception`` at least;
    * ``except Exception`` must make the failure observable (log, report or
      re-raise);
    * a narrow handler (``except WRCError``, ``except RuntimeError``, ...) is
      out of scope: it expresses an expected condition, not a blind catch.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"

# The logging helpers in utils/messaging.py plus the event/alert paths that
# already make a failure visible. log_info_msg and the post_* helpers are the
# same observable path as log_warning_msg; a block that already reports through
# them must not be forced to log twice.
OBSERVABLE_CALLS = frozenset(
    {
        "log_exception",
        "log_debug_msg",
        "log_warning_msg",
        "log_error_msg",
        "log_info_msg",
        "post_internal_error",
        "post_error_msg",
        "post_alert",
        "post_event",
        "post_monitor_msg",
    }
)

SOURCES = (
    "tracking/waze.py",
    "tracking/waze_history.py",
    "tracking/determine_interval.py",
    "mobile_app/mobapp_data_handler.py",
    "mobile_app/mobapp_interface.py",
)


def tree_of(relative_path: str) -> ast.Module:
    source = (COMPONENT / relative_path).read_text(encoding="utf-8")
    return ast.parse(source)


def handlers(relative_path: str) -> list[ast.ExceptHandler]:
    return [
        node
        for node in ast.walk(tree_of(relative_path))
        if isinstance(node, ast.ExceptHandler)
    ]


def handler_type_name(handler: ast.ExceptHandler) -> str | None:
    if handler.type is None:
        return None
    return ast.unparse(handler.type)


def observable_in(handler: ast.ExceptHandler) -> bool:
    for node in ast.walk(handler):
        if isinstance(node, ast.Raise):
            return True
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in OBSERVABLE_CALLS:
            return True
        if isinstance(func, ast.Attribute) and func.attr in OBSERVABLE_CALLS:
            return True
    return False


def test_no_bare_except_in_data_and_network_paths() -> None:
    for relative_path in SOURCES:
        bare = [
            handler.lineno
            for handler in handlers(relative_path)
            if handler.type is None
        ]
        assert bare == [], f"{relative_path}: bare except at lines {bare}"


def test_broad_except_handlers_are_logged() -> None:
    silent: list[str] = []
    for relative_path in SOURCES:
        for handler in handlers(relative_path):
            if handler_type_name(handler) not in ("Exception", "BaseException"):
                continue
            if not observable_in(handler):
                silent.append(f"{relative_path}:{handler.lineno}")
    assert silent == [], f"broad except without a log or raise: {silent}"


def test_every_source_file_is_covered() -> None:
    for relative_path in SOURCES:
        assert (COMPONENT / relative_path).is_file(), relative_path
