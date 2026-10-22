"""Resolve stale Mobile App device_tracker names.

The Mobile App integration creates ``device_tracker.<name>`` entities. When an
entity is renamed, Home Assistant keeps the entity id in the registry but the
name stored in the iCloud3 configuration still points at the old id. iCloud3
then reports the tracker as missing on every start-up.

This module contains the decision logic only. It deliberately has no Home
Assistant imports and no global state so it can be unit-tested on its own.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import AbstractSet

# Home Assistant appends ``_2`` (or `` (2)``) when an entity id is already
# taken. These are the only suffixes removed when comparing names. A name such
# as ``gary_iphone`` is never treated as a prefix of ``gary_iphone_app``.
_DUPLICATE_SUFFIX = re.compile(r"(?:_\d+| \(\d+\))$")

EXACT = "exact"
RENAMED = "renamed"
AMBIGUOUS = "ambiguous"
NOT_FOUND = "not_found"
RESERVED = "reserved"
DISABLED = "disabled"
INVALID = "invalid"


def mobapp_dname_base(dname: str) -> str:
    """Return the name without a Home Assistant duplicate suffix.

    ``foo_2`` -> ``foo``, ``foo (3)`` -> ``foo``, ``foo`` -> ``foo``.
    """

    if not dname:
        return ""

    return _DUPLICATE_SUFFIX.sub("", dname.strip())


def resolve_mobapp_dname(
    configured_dname: str,
    candidate_dnames: Iterable[str],
    reserved_dnames: AbstractSet[str] = frozenset(),
    disabled_dnames: AbstractSet[str] = frozenset(),
) -> tuple[str | None, str]:
    """Find the tracker that belongs to *configured_dname*.

    Returns ``(dname, status)``. ``status`` is one of :data:`EXACT`,
    :data:`RENAMED`, :data:`AMBIGUOUS`, :data:`NOT_FOUND`, :data:`RESERVED`,
    :data:`DISABLED` or :data:`INVALID`.

    A renamed tracker is only accepted when exactly one unused candidate has
    the same base name. Ambiguous results are never resolved by picking an
    arbitrary entry; the caller must keep reporting the configuration error.
    """

    configured_dname = (configured_dname or "").strip()
    if configured_dname in ("", "None"):
        return None, INVALID

    candidates = [dname for dname in candidate_dnames if dname]
    if configured_dname in disabled_dnames:
        return None, DISABLED
    if configured_dname in reserved_dnames:
        return None, RESERVED
    if configured_dname in candidates:
        return configured_dname, EXACT

    base = mobapp_dname_base(configured_dname)
    if base == "":
        return None, INVALID

    matches = [dname for dname in candidates
               if mobapp_dname_base(dname) == base]

    if not matches:
        return None, NOT_FOUND

    usable = [dname for dname in matches
              if dname not in reserved_dnames
              and dname not in disabled_dnames]

    if len(usable) == 1:
        return usable[0], RENAMED
    if len(usable) > 1:
        return None, AMBIGUOUS
    if all(dname in disabled_dnames for dname in matches):
        return None, DISABLED

    return None, RESERVED
