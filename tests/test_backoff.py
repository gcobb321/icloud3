from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from types import ModuleType


def test_parse_retry_after_seconds(backoff: ModuleType) -> None:
    assert backoff.parse_retry_after("120") == 120
    assert backoff.parse_retry_after("120.0") == 120
    assert backoff.parse_retry_after(120) == 120
    assert backoff.parse_retry_after("-5") == 0


def test_parse_retry_after_http_date(backoff: ModuleType) -> None:
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    retry_at = now + timedelta(seconds=90)
    assert backoff.parse_retry_after(format_datetime(retry_at), now=now) == 90


def test_parse_retry_after_never_raises(backoff: ModuleType) -> None:
    for value in (None, "", "not-a-date", object(), "1e400", "inf",
                  float("inf"), float("nan")):
        assert backoff.parse_retry_after(value) == 0


def test_parse_retry_after_is_capped(backoff: ModuleType) -> None:
    assert backoff.parse_retry_after("999999999") == backoff.MAX_RETRY_AFTER_SECS
    now = datetime(2026, 10, 22, 12, 0, 0, tzinfo=timezone.utc)
    retry_at = now + timedelta(days=365)
    assert backoff.parse_retry_after(format_datetime(retry_at), now=now) == \
        backoff.MAX_RETRY_AFTER_SECS


def test_waze_pause_is_monotonic(backoff: ModuleType) -> None:
    assert backoff.waze_pause_secs(9) == 0
    assert backoff.waze_pause_secs(10) == 600
    # Regression: the old equality lookup returned 0 for 11-19 and 21-29.
    for count in (11, 15, 19):
        assert backoff.waze_pause_secs(count) == 600
    for count in (20, 21, 25, 29):
        assert backoff.waze_pause_secs(count) == 1800
    for count in (30, 31, 40):
        assert backoff.waze_pause_secs(count) == 3600

