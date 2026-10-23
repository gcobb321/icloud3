"""Diagnostics support for the iCloud3 integration.

The diagnostics file is downloaded from Settings > Devices & Services > iCloud3
> Download diagnostics. It must never contain an Apple username/e-mail, a
password, a token or a location. Only counts and non-identifying profile
settings are reported; TO_REDACT is the last line of defense for values that
are passed through from HA (config entry data/options).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .const import VERSION
from .global_variables import GlobalVariables as Gb

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

# Redaction is done below with a case-insensitive walk. Do not rely on the HA
# helper alone: config keys written by older versions are not consistently cased.
TO_REDACT = [
    'username',
    'password',
    'token',
    'access_token',
    'refresh_token',
    'unique_id',
    'latitude',
    'longitude',
    'location',
    'email',
]

# conf_profile holds the configuration file layout/versioning fields. Everything
# that can identify the account, a device or its position is left out on purpose.
CONF_PROFILE_SAFE_FIELDS = (
    'version',
    'ic3_version',
    'version_install_date',
    'config_update_date',
    'first_seen',
    'event_log_version',
    'event_log_version_running',
    'event_log_card_directory',
    'event_log_card_program',
    'event_log_btnconfig_url',
    'sensors_hash',
)


async def async_get_config_entry_diagnostics(
        hass: HomeAssistant, entry: ConfigEntry) -> dict[str, Any]:
    '''Return the iCloud3 diagnostics for a config entry.'''

    return {
        'icloud3_version':     VERSION,
        'ha_version':          _ha_version(hass),
        'config_entry': {
            'data':    _redact(dict(entry.data or {})),
            'options': _redact(dict(getattr(entry, 'options', None) or {})),
        },
        'counts':              _counts(),
        'health':              _perf_snapshot(),
        'conf_profile':        _redact(_conf_profile()),
    }

#--------------------------------------------------------------------
def _redact(data: Any) -> Any:
    '''Recursively redact secrets. Keys are compared case-insensitively.'''

    if isinstance(data, dict):
        return {
            key: ('**REDACTED**' if str(key).lower() in _TO_REDACT_LOWER
                    else _redact(value))
            for key, value in data.items()
        }
    if isinstance(data, list):
        return [_redact(value) for value in data]
    return data

_TO_REDACT_LOWER = {key.lower() for key in TO_REDACT}

#--------------------------------------------------------------------
def _counts() -> dict[str, int]:
    '''Return entity, account and alert counts. No names are reported.'''

    Devices = getattr(Gb, 'Devices_by_devicename', None) or {}

    return {
        'devices':                  len(Devices),
        'devices_tracked':          len(getattr(Gb, 'Devices_by_devicename_tracked', None) or {}),
        'devices_mobapp_monitored': sum(1 for Device in Devices.values()
                                        if getattr(Device, 'is_mobapp_monitored', False)),
        'apple_accounts':           len(getattr(Gb, 'AppleAcct_by_username', None) or {}),
        'apple_account_errors':     len(getattr(Gb, 'AppleAcct_error_by_username', None) or {}),
        'sensors':                  _as_int(getattr(Gb, 'sensors_cnt', 0)),
        'device_trackers':          _as_int(getattr(Gb, 'device_trackers_cnt', 0)),
        'alerts':                   len(getattr(Gb, 'alerts_sensor_attrs', None) or {}),
        'startup_alerts':           len(getattr(Gb, 'startup_alerts_by_source', None) or {}),
    }

#--------------------------------------------------------------------
def _perf_snapshot() -> dict[str, Any]:
    '''Return the runtime performance counters. Empty when unavailable.'''

    perf = getattr(Gb, 'Perf', None)
    if perf is None:
        return {}

    return _redact(perf.snapshot())

#--------------------------------------------------------------------
def _conf_profile() -> dict[str, Any]:
    '''Return the non-identifying fields of Gb.conf_profile.'''

    conf_profile = getattr(Gb, 'conf_profile', None) or {}
    if not isinstance(conf_profile, dict):
        return {}

    return {field: conf_profile[field]
                for field in CONF_PROFILE_SAFE_FIELDS
                if field in conf_profile}

#--------------------------------------------------------------------
def _ha_version(hass: Any) -> str:
    '''Return the running HA version.'''

    version = getattr(getattr(hass, 'config', None), 'version', None)
    if version:
        return str(version)

    try:
        from homeassistant.const import __version__
    except ImportError:
        return 'unknown'

    return __version__

#--------------------------------------------------------------------
def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
