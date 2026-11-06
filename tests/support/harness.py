'''
Offline harness for the iCloud3 Configure (options flow) on a real Home Assistant core,
no network, no Apple.

    hass   - HomeAssistant on a temp config dir, real ConfigEntries/FlowManager/loader/
             translations, registries on temp storage
    entry  - an icloud3 ConfigEntry that is NOT set up (the integration's startup would
             contact Apple); the Gb state the Configure screens need is built by
             build_ic3_state() from a synthetic configuration file
    Flow   - drives hass.config_entries.options like the REST API does (results are
             serialized with the same cv.custom_serializer call) and renders every
             result with a "virtual frontend" (frontend.py)

The code under test is custom_components/icloud3 of this repository, or of the directory
in the IC3_CODE_DIR environment variable. It is copied to a temp directory once per
pytest run, and the integration modules are purged and re-imported for every test so the
Gb globals start clean.
'''
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import types
from pathlib import Path

from homeassistant import config_entries, loader
from homeassistant.core import HomeAssistant, CoreState
from homeassistant.helpers import (area_registry as ar, device_registry as dr,
                                   entity_registry as er, floor_registry as fr,
                                   issue_registry as ir, label_registry as lr,
                                   category_registry as cr, translation, entity)
from homeassistant.helpers.data_entry_flow import _BaseFlowManagerView
from homeassistant.util.unit_system import METRIC_SYSTEM

DOMAIN = 'icloud3'
CODE_DIR = Path(os.environ.get('IC3_CODE_DIR') or Path(__file__).resolve().parents[2])
WORK = Path(tempfile.mkdtemp(prefix='ic3-offline-'))
CC_DIR = WORK / 'cc'        # contains custom_components/icloud3 (a copy of CODE_DIR's)


#----------------------------------------------------------------------------------------
#   Network guard: the code under test must never reach Apple (or anything else)
#----------------------------------------------------------------------------------------
class NetworkBlocked(RuntimeError):
    pass

NETWORK_ATTEMPTS = []

def _blocked(*args, **kwargs):
    NETWORK_ATTEMPTS.append((args[:2], list(kwargs)[:4]))
    raise NetworkBlocked(f"network access blocked in the offline tests: {args[:2]}")

def install_network_guard():
    import socket
    real_socket = socket.socket

    class GuardedSocket(real_socket):
        def connect(self, address):
            if self.family == socket.AF_UNIX:
                return super().connect(address)
            _blocked('socket.connect', address)

        def connect_ex(self, address):
            if self.family == socket.AF_UNIX:
                return super().connect_ex(address)
            _blocked('socket.connect_ex', address)

    socket.socket = GuardedSocket
    socket.create_connection = lambda *a, **k: _blocked('socket.create_connection', a)
    socket.getaddrinfo = lambda *a, **k: _blocked('socket.getaddrinfo', a)

    import requests
    requests.Session.request = lambda self, *a, **k: _blocked('requests', a)
    import aiohttp
    async def _aiohttp_request(self, *a, **k):
        _blocked('aiohttp', a)
    aiohttp.ClientSession._request = _aiohttp_request
    import httpx
    httpx.Client.send = lambda self, *a, **k: _blocked('httpx', a)
    async def _httpx_send(self, *a, **k):
        _blocked('httpx', a)
    httpx.AsyncClient.send = _httpx_send

    # Integration requirements that talk to devices/the network are replaced by stubs
    def _stub_getattr(name):
        def __getattr__(attr):
            if attr.startswith('__'):
                raise AttributeError(attr)
            raise ImportError(f"{name}.{attr} is stubbed in the offline tests")
        return __getattr__

    for name in ('curl_cffi', 'curl_cffi.requests', 'fido2', 'fido2.client', 'fido2.hid',
                 'fido2.webauthn', 'fido2.ctap2', 'fido2.utils'):
        mod = types.ModuleType(name)
        mod.__getattr__ = _stub_getattr(name)
        sys.modules[name] = mod

    # The HA mobile_app/ios components pull in conversation/cloud/camera (not installed);
    # iCloud3 only uses them to send notifications
    from unittest.mock import MagicMock
    for name in ('homeassistant.components.mobile_app', 'homeassistant.components.mobile_app.notify',
                 'homeassistant.components.ios', 'homeassistant.components.ios.notify'):
        mod = types.ModuleType(name)
        mod.__path__ = []
        mod.__getattr__ = lambda attr: MagicMock(name=attr)
        sys.modules[name] = mod
    sys.modules['homeassistant.components.mobile_app'].notify = sys.modules['homeassistant.components.mobile_app.notify']
    sys.modules['homeassistant.components.ios'].notify = sys.modules['homeassistant.components.ios.notify']


#----------------------------------------------------------------------------------------
#   Code under test
#----------------------------------------------------------------------------------------
def prepare_code_copy(extra_translations=None):
    '''
    Copy CODE_DIR's custom_components/icloud3 into WORK/cc (once per process).
    extra_translations {lang: dict} adds translations/<lang>.json files (e.g. a fake de.json).
    '''
    dest = CC_DIR / 'custom_components' / DOMAIN
    if not dest.exists():
        shutil.copytree(CODE_DIR / 'custom_components' / DOMAIN, dest,
                        ignore=shutil.ignore_patterns('__pycache__', '*.png', '*.jpg'))
        (CC_DIR / 'custom_components' / '__init__.py').touch()
    for lang, data in (extra_translations or {}).items():
        (dest / 'translations' / f'{lang}.json').write_text(json.dumps(data, ensure_ascii=False))
    if str(CC_DIR) not in sys.path:
        sys.path.insert(0, str(CC_DIR))
    return dest


def purge_integration_modules():
    for name in [n for n in sys.modules if n == 'custom_components'
                    or n.startswith(f'custom_components.{DOMAIN}')]:
        del sys.modules[name]
    config_entries.HANDLERS.pop(DOMAIN, None)


def ic3(module):
    '''The custom_components.icloud3.<module> module of the code under test'''
    import importlib
    return importlib.import_module(f'custom_components.{DOMAIN}.{module}')


#----------------------------------------------------------------------------------------
#   Home Assistant
#----------------------------------------------------------------------------------------
async def make_hass(config_dir, language='en', units=METRIC_SYSTEM, ha_version=None):
    hass = HomeAssistant(str(config_dir))
    os.symlink(CC_DIR / 'custom_components', Path(config_dir) / 'custom_components')
    # The startup copies the Event Log card to www/icloud3 (Display settings lists the www dirs)
    os.makedirs(Path(config_dir) / 'www' / 'icloud3', exist_ok=True)
    hass.data[loader.DATA_CUSTOM_COMPONENTS] = None
    hass.config.location_name = 'offline test home'
    hass.config.latitude, hass.config.longitude, hass.config.elevation = 52.52, 13.40, 34
    await hass.config.async_set_time_zone('Europe/Berlin')
    hass.config.units = units
    hass.config.language = language
    hass.config.country = 'DE'
    hass.config.skip_pip = True
    hass.config.skip_pip_packages = []
    hass.config_entries = config_entries.ConfigEntries(hass, {'_': 'not empty'})
    entity.async_setup(hass)
    loader.async_setup(hass)
    hass.data[translation.TRANSLATION_FLATTEN_CACHE] = translation._TranslationCache(hass)
    dr.async_setup(hass)
    for reg in (ar, cr, dr, er, fr, ir, lr):
        await reg.async_load(hass)
    await hass.config_entries.async_initialize()
    hass.set_state(CoreState.running)
    return hass


async def stop_hass(hass):
    try:
        await hass.async_block_till_done(wait_background_tasks=False)
    except Exception:
        pass
    await hass.async_stop(force=True)


def add_entry(hass):
    entry = config_entries.ConfigEntry(
        version=1, minor_version=1, domain=DOMAIN, title='iCloud3',
        data={'added': '2026-10-01 10:00:00'}, options={}, source=config_entries.SOURCE_USER,
        unique_id=DOMAIN, discovery_keys={}, subentries_data=None)
    hass.config_entries._entries[entry.entry_id] = entry
    return entry


def serialize_result(result):
    '''What the REST API sends to the frontend (_prepare_result_json doesn't use self)'''
    data = _BaseFlowManagerView._prepare_result_json(None, result)
    return json.loads(json.dumps(data, default=str))
