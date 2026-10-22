"""Source-level contracts for regressions that were fixed by hand.

The integration imports Home Assistant, so these checks read the source instead
of importing it. Each assertion corresponds to a bug that was already reported
once; the point is that it cannot come back silently.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/icloud3"


def source_of(relative_path: str) -> str:
    return (COMPONENT / relative_path).read_text(encoding="utf-8")


def test_icloud3_main_has_no_dev_force_flag() -> None:
    source = source_of("icloud3_main.py")
    assert "is_dev_data_source_iCloud" not in source


def test_device_icloud_source_property_does_not_recurse() -> None:
    source = source_of("device.py")
    assert "return self.is_dev_data_source_ICLOUD" not in source
    assert "return self.dev_data_source in [ICLOUD]" in source


def test_fixed_interval_zero_stays_disabled() -> None:
    source = source_of("startup/config_file.py")
    # 0 means "no fixed interval"; a bare "< 3" would enable it for everyone.
    assert "0 < conf_device[CONF_FIXED_INTERVAL] < 3" in source


def test_icloud3_main_uses_the_zone_result_list() -> None:
    source = source_of("icloud3_main.py")
    assert "selected_zone_result =" not in source
    assert "selected_zone_results" in source


def test_icloud3_main_unsubscribes_and_shuts_down() -> None:
    source = source_of("icloud3_main.py")
    assert "self._unsub_5sec" in source
    assert "def shutdown" in source
    # HA's sync track_utc_time_change unsubscribe raises when called from the
    # event loop, so shutdown must hand it to an executor thread.
    assert "async_add_executor_job(unsub)" in source


def test_event_log_starts_with_a_list() -> None:
    source = source_of("support/event_log.py")
    assert "startup_event_recds = {}" not in source
    assert "startup_event_recds" in source


def test_mobapp_handler_rejects_stale_device_data() -> None:
    source = source_of("mobile_app/mobapp_data_handler.py")
    assert "secs_since(Device.loc_data_secs) <= 15" in source
    assert "x_unverified_devices_mobapp_handler" not in source


def test_timer_teardown_does_not_run_on_the_event_loop() -> None:
    for relative_path in (
        "startup/restore_state.py",
        "apple_acct/internet_error.py",
    ):
        source = source_of(relative_path)
        assert "is_running_in_event_loop" in source
        assert "async_add_executor_job" in source


def test_stale_mobapp_mapping_has_a_repair_path() -> None:
    handler = source_of("mobile_app/mobapp_data_handler.py")
    setup = source_of("startup/start_ic3.py")
    assert "clear_mobapp_mapping" in handler
    assert "clear_mobapp_mapping" in setup
    assert "register_repair_fix_handler('clear_mobapp_mapping'" in setup


def test_waze_history_creates_indexes_safely() -> None:
    source = source_of("tracking/waze_history.py")
    assert "CREATE INDEX IF NOT EXISTS" in source


def test_device_parameter_verification_returns_after_the_loop() -> None:
    tree = ast.parse(source_of("startup/config_file.py"))
    function = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "_verify_device_parameters_values")

    assert any(isinstance(node, ast.Return) for node in function.body)

    for node in function.body:
        if isinstance(node, ast.For):
            assert not any(
                isinstance(child, ast.Return) for child in ast.walk(node))
