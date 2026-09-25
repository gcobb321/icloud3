"""Home Assistant Repairs entries for Apple Account problems only the user can fix.

Expired authentication already uses HA's reauth flow (the orange Reconfigure
button). These cover the other states that stop location updates until the
user acts on Apple's side, which were only visible in sensor.icloud3_alerts
and the Event Log:

- Apple's updated Terms of Use have not been accepted
- the Apple Account is locked

Callers run in worker threads and in the event loop, so the registry update is
always scheduled onto the loop, and a failure here never affects tracking.
"""
from __future__ import annotations

from functools import partial
import re

from homeassistant.helpers import issue_registry as ir

from ..global_variables import GlobalVariables as Gb
from ..const            import DOMAIN

ISSUE_TERMS_OF_USE = 'apple_acct_terms_of_use'
ISSUE_ACCT_LOCKED  = 'apple_acct_locked'


def _issue_id(issue, AppleAcct):
    account = re.sub(r'[^a-z0-9_]+', '_', str(AppleAcct.username_id).lower()).strip('_')
    return f"{issue}_{account}"


def _schedule(func, **kwargs):
    try:
        if Gb.hass is None:
            return
        Gb.hass.loop.call_soon_threadsafe(partial(func, Gb.hass, DOMAIN, **kwargs))
    except Exception:
        pass


def raise_apple_acct_issue(issue, AppleAcct):
    '''Show a Repairs entry for this Apple Account (replaces an existing one).'''
    _schedule(ir.async_create_issue,
                issue_id=_issue_id(issue, AppleAcct),
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.ERROR,
                translation_key=issue,
                translation_placeholders={'account': str(AppleAcct.username_id)})


def clear_apple_acct_issue(issue, AppleAcct):
    '''Remove the Repairs entry once the problem is gone (no-op if there is none).'''
    _schedule(ir.async_delete_issue, issue_id=_issue_id(issue, AppleAcct))
