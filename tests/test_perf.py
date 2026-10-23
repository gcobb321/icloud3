"""Tests for the Home Assistant free runtime counters in ``utils/perf.py``.

The integration package cannot be imported without Home Assistant, so the
module is loaded by path. These tests pin the snapshot shape because the
``sensor.icloud3_health`` attributes and the diagnostics payload are built
from it.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import threading
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]
PERF_PATH = ROOT / "custom_components/icloud3/utils/perf.py"

SNAPSHOT_KEYS = {
    "loop_count",
    "error_count",
    "last_error_secs_ago",
    "last_error_message",
    "uptime_secs",
    "loop_duration_ms",
    "config_write_failures",
    "apple_requests",
    "apple_failures",
    "waze_status_counts",
    "startup_stages_ms",
    "startup_total_ms",
}

DURATION_KEYS = {"samples", "p50", "p95", "p99", "max", "last"}


@pytest.fixture(scope="module")
def perf() -> ModuleType:
    spec = importlib.util.spec_from_file_location("icloud3_perf", PERF_PATH)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {PERF_PATH}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["icloud3_perf"] = module
    spec.loader.exec_module(module)
    return module


def test_empty_snapshot_shape(perf: ModuleType) -> None:
    counters = perf.PerfCounters()

    snapshot = counters.snapshot()

    assert set(snapshot) == SNAPSHOT_KEYS
    assert snapshot["loop_count"] == 0
    assert snapshot["error_count"] == 0
    assert snapshot["last_error_secs_ago"] is None
    assert snapshot["last_error_message"] is None
    assert snapshot["config_write_failures"] == 0
    assert snapshot["apple_requests"] == 0
    assert snapshot["apple_failures"] == 0
    assert snapshot["waze_status_counts"] == {}
    assert snapshot["uptime_secs"] >= 0
    assert snapshot["startup_stages_ms"] == {}
    assert snapshot["startup_total_ms"] is None

    durations = snapshot["loop_duration_ms"]
    assert set(durations) == DURATION_KEYS
    assert durations == {
        "samples": 0,
        "p50": None,
        "p95": None,
        "p99": None,
        "max": None,
        "last": None,
    }


def test_percentiles_for_100_loops(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    for index in range(1, 101):
        counters.record_loop(index / 1000.0)

    snapshot = counters.snapshot()
    durations = snapshot["loop_duration_ms"]

    assert snapshot["loop_count"] == 100
    assert snapshot["error_count"] == 0
    assert durations["samples"] == 100
    assert 45.0 <= durations["p50"] <= 55.0
    assert 90.0 <= durations["p95"] <= 100.0
    assert 95.0 <= durations["p99"] <= 100.0
    assert durations["max"] == 100.0
    assert durations["last"] == 100.0


def test_ring_buffer_keeps_the_last_window(perf: ModuleType) -> None:
    counters = perf.PerfCounters(window=10)
    for index in range(25):
        counters.record_loop(0.001)

    snapshot = counters.snapshot()

    assert snapshot["loop_count"] == 25
    assert snapshot["loop_duration_ms"]["samples"] == 10


def test_error_counter_and_last_error(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_loop(0.01)
    counters.record_loop(0.02, error=True)
    counters.record_loop(0.03)

    snapshot = counters.snapshot()

    assert snapshot["loop_count"] == 3
    assert snapshot["error_count"] == 1
    assert isinstance(snapshot["last_error_secs_ago"], float)
    assert snapshot["last_error_secs_ago"] >= 0
    assert snapshot["last_error_message"] is None


def test_error_message_is_stored_and_truncated(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_loop(0.01, error=True, error_message="ValueError: boom")

    snapshot = counters.snapshot()

    assert snapshot["last_error_message"] == "ValueError: boom"

    counters.record_loop(0.01, error=True, error_message="x" * 500)

    snapshot = counters.snapshot()

    assert snapshot["last_error_message"] == "x" * 200
    assert len(snapshot["last_error_message"]) == perf.MAX_ERROR_MESSAGE_LEN


def test_error_message_is_kept_after_a_clean_loop(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_loop(0.01, error=True, error_message="TimeoutError: slow")
    counters.record_loop(0.02)

    snapshot = counters.snapshot()

    assert snapshot["error_count"] == 1
    assert snapshot["last_error_message"] == "TimeoutError: slow"


def test_request_and_config_failure_counters(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_apple_request(True)
    counters.record_apple_request(False)
    counters.record_waze_request("OK")
    counters.record_waze_request(" error ")
    counters.record_waze_request("")
    counters.record_config_write_failure()

    snapshot = counters.snapshot()

    assert snapshot["apple_requests"] == 2
    assert snapshot["apple_failures"] == 1
    assert snapshot["waze_status_counts"] == {"ok": 1, "error": 1, "unknown": 1}
    assert snapshot["config_write_failures"] == 1


def test_reset_clears_every_counter(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_loop(1.0, error=True, error_message="RuntimeError: boom")
    counters.record_apple_request(False)
    counters.record_waze_request("error")
    counters.record_config_write_failure()
    counters.record_startup_stage("config_load", 0.25)
    counters.record_startup_stage("total", 1.5)

    counters.reset()
    snapshot = counters.snapshot()

    assert snapshot["loop_count"] == 0
    assert snapshot["error_count"] == 0
    assert snapshot["last_error_secs_ago"] is None
    assert snapshot["last_error_message"] is None
    assert snapshot["loop_duration_ms"]["samples"] == 0
    assert snapshot["apple_requests"] == 0
    assert snapshot["apple_failures"] == 0
    assert snapshot["waze_status_counts"] == {}
    assert snapshot["config_write_failures"] == 0
    assert snapshot["startup_stages_ms"] == {}
    assert snapshot["startup_total_ms"] is None


def test_startup_stages_are_recorded_in_milliseconds(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_startup_stage("config_load", 0.25)
    counters.record_startup_stage("platforms", 1.0)

    snapshot = counters.snapshot()

    assert snapshot["startup_stages_ms"] == {
        "config_load": 250.0,
        "platforms": 1000.0,
    }
    assert snapshot["startup_total_ms"] is None
    assert all(isinstance(value, float)
               for value in snapshot["startup_stages_ms"].values())


def test_startup_stage_recording_is_ordered_by_name(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_startup_stage("stage_1_2_3", 0.4)
    counters.record_startup_stage("config_load", 0.1)

    snapshot = counters.snapshot()

    assert set(snapshot["startup_stages_ms"]) == {"config_load", "stage_1_2_3"}
    assert snapshot["startup_stages_ms"]["config_load"] == 100.0
    assert snapshot["startup_stages_ms"]["stage_1_2_3"] == 400.0


def test_repeated_startup_stage_overwrites_the_previous_value(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_startup_stage("ha_wait", 5.0)
    counters.record_startup_stage("ha_wait", 0.25)

    snapshot = counters.snapshot()

    assert snapshot["startup_stages_ms"] == {"ha_wait": 250.0}


def test_total_stage_sets_startup_total(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_startup_stage("config_load", 0.2)
    counters.record_startup_stage("total", 3.5)

    snapshot = counters.snapshot()

    assert snapshot["startup_total_ms"] == 3500.0
    assert snapshot["startup_stages_ms"]["total"] == 3500.0

    counters.record_startup_stage("total", 4.0)

    assert counters.snapshot()["startup_total_ms"] == 4000.0


def test_negative_startup_durations_are_clamped(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_startup_stage("config_load", -2.0)

    assert counters.snapshot()["startup_stages_ms"] == {"config_load": 0.0}


def test_concurrent_recording_is_thread_safe(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    threads_count = 8
    loops_per_thread = 250
    barrier = threading.Barrier(threads_count)

    def worker() -> None:
        barrier.wait()
        for _ in range(loops_per_thread):
            counters.record_loop(0.005)

    threads = [threading.Thread(target=worker) for _ in range(threads_count)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    snapshot = counters.snapshot()

    assert snapshot["loop_count"] == threads_count * loops_per_thread
    assert snapshot["loop_duration_ms"]["samples"] == perf.LOOP_WINDOW


def test_snapshot_is_json_serializable(perf: ModuleType) -> None:
    counters = perf.PerfCounters()
    counters.record_loop(0.012)
    counters.record_loop(0.009, error=True, error_message="KeyError: 'x'")
    counters.record_apple_request(True)
    counters.record_waze_request("ok")
    counters.record_startup_stage("config_load", 0.125)

    encoded = json.dumps(counters.snapshot())
    decoded = json.loads(encoded)

    assert decoded["loop_count"] == 2
    assert decoded["error_count"] == 1
    assert decoded["last_error_message"] == "KeyError: 'x'"
    assert decoded["startup_stages_ms"] == {"config_load": 125.0}
    assert decoded["startup_total_ms"] is None
