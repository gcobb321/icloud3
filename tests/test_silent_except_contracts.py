"""Contracts for error handling in the data, network and configuration paths.

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

The bare-except rule is checked against ``ALL_SOURCES``, which is every module
of the integration (``rglob``), so a new file cannot slip past it. The
"must log or re-raise" rule is checked against ``SOURCES``: the modules that
have been converted to named handlers. The remaining modules still carry silent
broad handlers; converting them is a separate change, and hiding them behind a
module-level exemption would weaken the contract for every handler in them.
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
        "internal_error_msg",
        "internal_error_msg2",
        "post_error_msg",
        "post_alert",
        "post_event",
        "post_monitor_msg",
    }
)

# The stdlib logger methods on _LOGGER / Gb.HALogger. startup/config_file.py and
# utils/file_io.py report through these instead of the messaging helpers.
OBSERVABLE_LOGGER_METHODS = frozenset(
    {"debug", "info", "warning", "error", "exception", "critical"}
)

SOURCES = (
    "tracking/waze.py",
    "tracking/waze_history.py",
    "tracking/determine_interval.py",
    "mobile_app/mobapp_data_handler.py",
    "mobile_app/mobapp_interface.py",
    "apple_acct/icloud_data_handler.py",
    "apple_acct/apple_acct_devices.py",
    "apple_acct/apple_acct_device_data.py",
    "apple_acct/apple_acct_support.py",
    "apple_acct/apple_acct_support_cf.py",
    "apple_acct/icloud_hwkey.py",
    "apple_acct/internet_error.py",
    "startup/config_file.py",
    "startup/restore_state.py",
    "startup/start_ic3_control.py",
    "support/event_log.py",
    "support/service_handler.py",
    "support/hacs_ic3.py",
    "utils/entity_io.py",
    "utils/entity_reg_util.py",
    "utils/file_io.py",
    "utils/time_util.py",
    "utils/utils.py",
    # The Configure/Options UI. These are the modules under configure/ that
    # declare exception handlers; the form and apply paths run inside the
    # config flow, where a swallowed failure shows up as an empty selection
    # list or a form that saves nothing.
    "configure/dashboard_builder.py",
    "configure/selection_lists.py",
    "configure/utils_cf.py",
    "configure/screens/form_config_flow.py",
    "configure/screens/form_parameters.py",
    "configure/screens/step_icloud3_device.py",
    "configure/screens/step_parameters.py",
    "configure/screens/step_reauth.py",
    "configure/screens/step_sensors.py",
    "configure/screens/step_tools.py",
    # The modules converted from bare handlers: every handler here names its
    # exception and reports it, so the "must log or re-raise" rule applies.
    "sensor.py",
    "device.py",
    "zone.py",
    "icloud3_main.py",
    "device_fm_zone.py",
    "device_tracker.py",
    "utils/messaging.py",
    "startup/start_ic3.py",
    "apple_acct/apple_acct.py",
    "apple_acct/apple_acct_auth.py",
    "apple_acct/apple_acct_session.py",
    "apple_acct/apple_acct_upw.py",
    "apple_acct/icloud_session.py",
    "apple_acct/icloud_requests_io.py",
)

# Every module in the integration. The bare-except rule is repo-wide: a new
# file must not be able to reintroduce a catch-all that also swallows
# KeyboardInterrupt and SystemExit.
ALL_SOURCES = tuple(
    sorted(
        path.relative_to(COMPONENT).as_posix()
        for path in COMPONENT.rglob("*.py")
    )
)

# Handlers that stay silent on purpose. Each entry is "module::function" and
# carries its own justification; an entry weakens the contract for that one
# function only, so it must not be a way to skip a whole file.
EXEMPT_HANDLERS = {
    # asyncio.get_running_loop() raises RuntimeError for every call made off the
    # event loop, which is the normal case for the worker threads: this helper
    # returns False on the common path. A log line here would flood the log from
    # the most frequently called helper in the integration, and the answer
    # ("not in the loop") is already the caller's expected branch.
    "utils/utils.py::is_running_in_event_loop",
}


def tree_of(relative_path: str) -> ast.Module:
    source = (COMPONENT / relative_path).read_text(encoding="utf-8")
    return ast.parse(source)


def handlers(relative_path: str) -> list[ast.ExceptHandler]:
    return [handler for handler, _ in scan(relative_path)]


def scan(relative_path: str) -> list[tuple[ast.ExceptHandler, str]]:
    """Return each handler with the name of the function that contains it."""
    found: list[tuple[ast.ExceptHandler, str]] = []

    def visit(node: ast.AST, function_name: str) -> None:
        for child in ast.iter_child_nodes(node):
            child_function = (
                child.name
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                else function_name
            )
            if isinstance(child, ast.ExceptHandler):
                found.append((child, child_function))
            visit(child, child_function)

    visit(tree_of(relative_path), "")
    return found


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
        if isinstance(func, ast.Attribute) and (
            func.attr in OBSERVABLE_CALLS
            or func.attr in OBSERVABLE_LOGGER_METHODS
        ):
            return True
    return False


def exempt_key(relative_path: str, function_name: str) -> str:
    return f"{relative_path}::{function_name}"


def test_no_bare_except_in_the_integration() -> None:
    for relative_path in ALL_SOURCES:
        bare = [
            handler.lineno
            for handler in handlers(relative_path)
            if handler.type is None
        ]
        assert bare == [], f"{relative_path}: bare except at lines {bare}"


def test_broad_except_handlers_are_logged() -> None:
    silent: list[str] = []
    for relative_path in SOURCES:
        for handler, function_name in scan(relative_path):
            if handler_type_name(handler) not in ("Exception", "BaseException"):
                continue
            if observable_in(handler):
                continue
            if exempt_key(relative_path, function_name) in EXEMPT_HANDLERS:
                continue
            silent.append(f"{relative_path}:{handler.lineno}")
    assert silent == [], f"broad except without a log or raise: {silent}"


def test_exempt_handlers_still_name_their_exception() -> None:
    for relative_path in SOURCES:
        for handler, function_name in scan(relative_path):
            key = exempt_key(relative_path, function_name)
            if key not in EXEMPT_HANDLERS:
                continue
            assert handler.type is not None, (
                f"{relative_path}:{handler.lineno}: an exempt handler still may not "
                f"be a bare except"
            )


def test_exempt_handlers_exist() -> None:
    for key in EXEMPT_HANDLERS:
        relative_path, function_name = key.split("::")
        assert relative_path in ALL_SOURCES, f"{key}: exempt module is not scanned"
        names = {
            node.name
            for node in ast.walk(tree_of(relative_path))
            if isinstance(node, ast.FunctionDef)
        }
        assert function_name in names, f"{key}: exempt function does not exist"


def test_all_sources_are_discovered() -> None:
    assert len(ALL_SOURCES) > 50, ALL_SOURCES
    assert "sensor.py" in ALL_SOURCES
    assert "apple_acct/apple_acct.py" in ALL_SOURCES
    handlers_found = sum(len(handlers(relative_path)) for relative_path in ALL_SOURCES)
    assert handlers_found > 100, handlers_found


def test_every_source_file_is_covered() -> None:
    for relative_path in SOURCES:
        assert relative_path in ALL_SOURCES, relative_path
        assert (COMPONENT / relative_path).is_file(), relative_path
