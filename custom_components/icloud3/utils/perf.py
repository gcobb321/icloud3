"""Runtime performance counters for the iCloud3 5-second loop.

This module deliberately has no Home Assistant imports so it can be tested
without an HA harness. Counters are guarded by a lock because the timer
callback, the config writer and the request helpers may run on different
threads.
"""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import Any

LOOP_WINDOW = 288  # 24 minutes at one sample per 5 seconds


class PerfCounters:
    """Thread-safe counters for the 5-second loop and external requests."""

    def __init__(self, window: int = LOOP_WINDOW) -> None:
        if window < 1:
            raise ValueError("window must be at least 1")

        self._lock = threading.Lock()
        self._loop_durations: deque[float] = deque(maxlen=window)
        self._started_at = time.perf_counter()
        self._loop_count = 0
        self._error_count = 0
        self._last_error_at: float | None = None
        self._config_write_failures = 0
        self._apple_requests = 0
        self._apple_failures = 0
        self._waze_status_counts: dict[str, int] = {}

    def record_loop(self, duration_secs: float, error: bool = False) -> None:
        """Record one completed 5-second loop."""
        with self._lock:
            self._loop_durations.append(max(float(duration_secs), 0.0))
            self._loop_count += 1
            if error:
                self._error_count += 1
                self._last_error_at = time.perf_counter()

    def record_config_write_failure(self) -> None:
        """Record a failed configuration write."""
        with self._lock:
            self._config_write_failures += 1

    def record_apple_request(self, ok: bool) -> None:
        """Record one Apple/icloud.com request and its outcome."""
        with self._lock:
            self._apple_requests += 1
            if not ok:
                self._apple_failures += 1

    def record_waze_request(self, status: str) -> None:
        """Record one Waze request keyed by its outcome."""
        key = str(status).strip().lower() or 'unknown'
        with self._lock:
            self._waze_status_counts[key] = self._waze_status_counts.get(key, 0) + 1

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serializable view of the counters."""
        with self._lock:
            durations = list(self._loop_durations)
            now = time.perf_counter()

            return {
                'loop_count': self._loop_count,
                'error_count': self._error_count,
                'last_error_secs_ago': (
                    None if self._last_error_at is None
                    else round(now - self._last_error_at, 3)
                ),
                'uptime_secs': round(now - self._started_at, 3),
                'loop_duration_ms': _duration_stats(durations),
                'config_write_failures': self._config_write_failures,
                'apple_requests': self._apple_requests,
                'apple_failures': self._apple_failures,
                'waze_status_counts': dict(self._waze_status_counts),
            }

    def reset(self) -> None:
        """Clear every counter and restart the uptime clock."""
        with self._lock:
            self._loop_durations.clear()
            self._started_at = time.perf_counter()
            self._loop_count = 0
            self._error_count = 0
            self._last_error_at = None
            self._config_write_failures = 0
            self._apple_requests = 0
            self._apple_failures = 0
            self._waze_status_counts.clear()


def _duration_stats(durations: list[float]) -> dict[str, Any]:
    """Return percentile/max/last loop durations in milliseconds."""
    samples = len(durations)
    if samples == 0:
        return {
            'samples': 0,
            'p50': None,
            'p95': None,
            'p99': None,
            'max': None,
            'last': None,
        }

    ordered = sorted(value * 1000.0 for value in durations)

    def percentile(fraction: float) -> float:
        index = int(fraction * (samples - 1))
        return round(ordered[index], 3)

    return {
        'samples': samples,
        'p50': percentile(0.50),
        'p95': percentile(0.95),
        'p99': percentile(0.99),
        'max': round(ordered[-1], 3),
        'last': round(durations[-1] * 1000.0, 3),
    }


def install_perf_counters() -> PerfCounters:
    """Attach the shared counter to GlobalVariables and return it."""
    from ..global_variables import GlobalVariables as Gb

    existing = getattr(Gb, 'Perf', None)
    if isinstance(existing, PerfCounters):
        return existing

    counters = PerfCounters()
    setattr(Gb, 'Perf', counters)
    return counters
