"""Behaviour tests for the Home Assistant free helpers in ``utils/pure.py``.

These pin the sign handling of UTC offsets and the boundary rules of the
zone/number predicates. Both used to be implemented inline in HA-coupled
modules, so a regression only surfaced in a live instance.
"""

from __future__ import annotations

import os
import time
from collections.abc import Iterator
from types import ModuleType

import pytest

FMT_EPOCH = 1789387200.0  # 2026-09-14 12:00:00 UTC


@pytest.fixture
def utc_timezone() -> Iterator[None]:
    """Run the test with ``TZ=UTC`` so ``fromtimestamp`` is deterministic."""
    previous = os.environ.get("TZ")
    os.environ["TZ"] = "UTC"
    if hasattr(time, "tzset"):
        time.tzset()
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("TZ", None)
        else:
            os.environ["TZ"] = previous
        if hasattr(time, "tzset"):
            time.tzset()


def test_utc_offset_secs_keeps_the_sign(pure: ModuleType) -> None:
    assert pure.utc_offset_secs("+0800") == 28800
    assert pure.utc_offset_secs("-0500") == -18000


def test_utc_offset_secs_accepts_a_colon(pure: ModuleType) -> None:
    assert pure.utc_offset_secs("+05:30") == 19800
    assert pure.utc_offset_secs("-03:30") == -12600


def test_utc_offset_secs_defaults_to_zero(pure: ModuleType) -> None:
    for offset in ("", "UTC", "+8", "+0x00", "+0599", "+08:0"):
        assert pure.utc_offset_secs(offset) == 0


def test_is_between_includes_the_boundaries(pure: ModuleType) -> None:
    assert pure.is_between(1, 1, 19) is True
    assert pure.is_between(0, 1, 19) is False
    assert pure.is_between(19, 1, 19) is True
    assert pure.is_between(20, 1, 19) is False


def test_is_zone_rejects_sentinels(pure: ModuleType) -> None:
    assert pure.is_zone("home", "not_home", "not_set") is True
    assert pure.is_zone("not_home", "not_home", "not_set") is False
    assert pure.is_zone("", "not_home", "not_set") is False
    assert pure.is_zone(None, "not_home", "not_set") is False
    assert pure.is_zone("not_set", "not_home", "not_set") is False


def test_encode_base64_ascii(pure: ModuleType) -> None:
    assert pure.encode_base64_ascii("abc") == "YWJj"


def test_encode_base64_ascii_refuses_non_ascii(pure: ModuleType) -> None:
    with pytest.raises(UnicodeEncodeError):
        pure.encode_base64_ascii("şifre")


@pytest.mark.usefixtures("utc_timezone")
def test_format_date_codes(pure: ModuleType) -> None:
    assert pure.format_date(FMT_EPOCH, "mmdd") == "9/14"
    assert pure.format_date(FMT_EPOCH, "ddmm") == "14/9"
    assert pure.format_date(FMT_EPOCH, "ddmmm") == "14Sep"


@pytest.mark.usefixtures("utc_timezone")
def test_format_date_default_and_fallback(pure: ModuleType) -> None:
    assert pure.format_date(FMT_EPOCH) == "Sep 14"
    assert pure.format_date(FMT_EPOCH, "yyyymmdd") == "14Sep2026"
