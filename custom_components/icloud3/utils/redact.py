"""Secret and location redaction for log output.

Pure module: no Home Assistant import and no I/O, so it can be loaded by path
from the tests and imported from any layer without pulling in the integration.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

REDACTED = "**REDACTED**"
CYCLE = "<cycle>"

SENSITIVE_KEY_PARTS: tuple[str, ...] = (
    "password",
    "passwd",
    "token",
    "session",
    "trust",
    "cookie",
    "authorization",
    "secret",
    "dsid",
    "email",
    "username",
    "apple_id",
    "latitude",
    "longitude",
    "lat",
    "long",
    "location",
)

_BEARER_RE = re.compile(r"(?i)\b(bearer)\s+[A-Za-z0-9._~+/=-]+")
_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(\b[a-z0-9_]{0,40}?"
    r"(?:password|passwd|token|secret|session|trust|cookie|dsid|apple_id|email|username)"
    r"[a-z0-9_]{0,20}[\"']?\s*[:=]\s*)"
    r"(['\"][^'\"]*['\"]|[^\s,;&)}\]>]+)"
)
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+")
_COORDINATE_RE = re.compile(r"(?<![\d.])\d{1,3}\.\d{4,}(?!\d)")


def redact_text(text: str) -> str:
    """Mask bearer tokens, secret assignments, e-mails and coordinates."""
    if not isinstance(text, str):
        text = str(text)
    if not text:
        return text

    text = _BEARER_RE.sub(f"Bearer {REDACTED}", text)
    text = _SECRET_ASSIGNMENT_RE.sub(_mask_assignment, text)
    text = _EMAIL_RE.sub(REDACTED, text)
    text = _COORDINATE_RE.sub(REDACTED, text)
    return text


def redact_value(value: Any, key: str | None = None) -> Any:
    """Recursively redact a single value; ``key`` selects key based masking."""
    return _redact_value(value, key, set())


def redact_mapping(data: Mapping[Any, Any]) -> dict[Any, Any]:
    """Recursively redact a mapping, keeping its keys intact."""
    seen = {id(data)}
    return {
        key: _redact_value(value, key if isinstance(key, str) else None, seen)
        for key, value in data.items()
    }


def _mask_assignment(match: re.Match[str]) -> str:
    return f"{match.group(1)}{REDACTED}"


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def _redact_value(value: Any, key: str | None, seen: set[int]) -> Any:
    if isinstance(key, str) and _is_sensitive_key(key):
        return REDACTED

    if isinstance(value, str):
        return redact_text(value)

    if isinstance(value, Mapping):
        if id(value) in seen:
            return CYCLE
        child_seen = seen | {id(value)}
        return {
            child_key: _redact_value(
                child_value,
                child_key if isinstance(child_key, str) else None,
                child_seen,
            )
            for child_key, child_value in value.items()
        }

    if isinstance(value, (list, tuple, set, frozenset)):
        if id(value) in seen:
            return CYCLE
        child_seen = seen | {id(value)}
        return [_redact_value(item, None, child_seen) for item in value]

    return value
