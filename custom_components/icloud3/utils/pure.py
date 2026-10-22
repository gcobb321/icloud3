"""Pure helpers shared by the iCloud3 utility modules.

Nothing here imports Home Assistant, so every function can be unit tested
without the integration package or a Home Assistant runtime. Callers that need
the historical utility names keep using ``utils``/``time_util``, which delegate
to these implementations.
"""

from __future__ import annotations

import base64
from datetime import datetime


def is_between(number: float, min_value: float, max_value: float) -> bool:
    """Return True when ``min_value <= number <= max_value`` (inclusive)."""
    return max_value >= number >= min_value


def is_zone(zone: str | None, not_home: str, not_set: str) -> bool:
    """Return True when ``zone`` is a real zone name.

    ``None``, an empty string and the two sentinel values (``not_home`` and
    ``not_set``) are not zones. The sentinels are passed in so this module does
    not have to import the integration constants.
    """
    return zone is not None and zone not in ('', not_set, not_home)


def utc_offset_secs(offset: str) -> int:
    """Convert a UTC offset such as ``"+0800"`` or ``"-03:30"`` to seconds.

    Empty or malformed input returns 0 instead of raising: the offset often
    comes from a platform string whose shape varies between platforms.
    """
    if not offset or not isinstance(offset, str):
        return 0

    text = offset.strip()
    sign = -1 if text.startswith('-') else 1
    digits = text[1:] if text[:1] in ('+', '-') else text
    digits = digits.replace(':', '')

    if len(digits) != 4 or not digits.isdigit():
        return 0

    hours = int(digits[:2])
    mins = int(digits[2:])
    if mins > 59:
        return 0

    return sign * (hours * 3600 + mins * 60)


def encode_base64_ascii(text: str) -> str:
    """Encode ``text`` as ASCII base64.

    Raises:
        UnicodeEncodeError: the text is not ASCII. Callers own the fallback.
    """
    return base64.b64encode(text.encode('ascii')).decode('ascii')


def format_date(secs: float, fmt_code: str | None = None) -> str:
    """Format an epoch timestamp for the Event Log.

    ``mmdd`` -> 9/14, ``ddmm`` -> 14/9, ``ddmmm`` -> 14Sep, default -> Sep 14,
    any other code -> 14Sep2026.
    """
    if fmt_code is None:
        return datetime.fromtimestamp(secs).strftime('%b %-d')
    if fmt_code == 'mmdd':
        return datetime.fromtimestamp(secs).strftime('%-m/%-d')
    if fmt_code == 'ddmm':
        return datetime.fromtimestamp(secs).strftime('%-d/%-m')
    if fmt_code == 'ddmmm':
        return datetime.fromtimestamp(secs).strftime('%-d%b')

    return datetime.fromtimestamp(secs).strftime('%-d%b%Y')
