"""Small, Home Assistant free retry/back-off helpers.

The tracking loop runs in an executor thread, but an unbounded retry loop still
consumes the shared request budget (Apple and Waze) and fills the log with the
same message. These helpers keep the policy deterministic and testable.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
# A broken proxy or a server with a wrong clock can send a far-future
# Retry-After. Never let that disable Waze for the rest of the HA session.
MAX_RETRY_AFTER_SECS = 6 * 60 * 60


def _clamp_retry_after(seconds: int) -> int:
    return min(MAX_RETRY_AFTER_SECS, max(0, int(seconds)))


def parse_retry_after(value: object, now: datetime | None = None) -> int:
    """Parse an HTTP ``Retry-After`` value into seconds.

    Accepts delta-seconds (``"120"``, ``"120.0"``) and HTTP-date values. Any
    malformed value returns 0 instead of raising; a bad header must not take
    down the tracking loop.
    """

    if value is None:
        return 0

    if isinstance(value, (int, float)):
        try:
            return _clamp_retry_after(int(value))
        except (ValueError, OverflowError):
            return 0

    text = str(value).strip()
    if not text:
        return 0

    try:
        return _clamp_retry_after(int(float(text)))
    except (ValueError, OverflowError):
        pass

    try:
        retry_at = parsedate_to_datetime(text)
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        now = now or datetime.now(timezone.utc)
        return _clamp_retry_after(int((retry_at - now).total_seconds()))
    except (TypeError, ValueError, OverflowError):
        return 0


def waze_pause_secs(consecutive_errors: int) -> int:
    """Return the Waze pause for a number of consecutive server errors.

    The old implementation used an equality lookup (``{10: 600, 20: 1800,
    30: 3600}.get(count, 0)``), so counts 11-19 and 21-29 never paused Waze.
    Thresholds make the pause monotonic.
    """

    if consecutive_errors >= 30:
        return 3600
    if consecutive_errors >= 20:
        return 1800
    if consecutive_errors >= 10:
        return 600
    return 0
