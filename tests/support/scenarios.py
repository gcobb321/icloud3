'''
The iCloud3 Gb state the Configure screens need, built without the integration's startup
(which logs into Apple). Scenarios describe Apple Accounts (with a fake login state), devices
and the general settings; build_ic3_state() writes them to the configuration file, loads it
with the integration's own config_file code and adds fake AppleAcct/Device objects.
'''
from __future__ import annotations

import copy
import json
import os
import time
from dataclasses import dataclass, field

from .harness import ic3, DOMAIN

STARTUP_ERRORS = []         # (name, error) of the startup steps that failed
FAKE_MISSING_ATTRS = set()  # attributes the code read that the fake objects don't have
APPLE_CALLS = []            # (apple_id, method, args, kwargs) the code called on a fake


#----------------------------------------------------------------------------------------
#   Fake Apple layer, never contacts Apple
#----------------------------------------------------------------------------------------
class _Recorder:
    def __init__(self, owner, name):
        self.owner, self.name = owner, name

    def __call__(self, *args, **kwargs):
        APPLE_CALLS.append((self.owner.apple_id, self.name, args, kwargs))
        result = self.owner._results.get(self.name)
        return result(*args, **kwargs) if callable(result) else result


def _async_value(value):
    async def _value(*args, **kwargs):
        return value
    return _value


class FakeAppleAcct:
    '''state: signed_in | needs_code | terms | login_failed | failed_503'''
    METHODS = {'setup_error', 'update_auth_method', 'request_auth_code_via_push_notification',
               'request_auth_code_via_text_msg', 'untrust_session_and_authenticate',
               'refresh_icloud_data', 'refresh_hwkey_names_preserve_trust',
               'make_cookie_filename_base_from_apple_id', 'get_hwkey_names',
               'delete_cookie_and_session_files', 'create_AADevices_object', 'code_description',
               'authenticate_with_hwkey', 'authenticate', 'auth_method_value',
               'async_validate_apple_id_password_srp', 'async_validate_apple_id_password',
               'validate_auth_code', 'send_auth_code', 'validate_2fa_push_popup_window_code',
               'validate_2fa_text_code'}

    def __init__(self, apple_id, owner, state='signed_in', devices=(), auth_method='push',
                 server_location='usa', results=None):
        self.apple_id = apple_id
        self.username = apple_id
        self.apple_user = apple_id.split('@')[0]
        self.account_owner = owner
        self.account_owner_short = owner.split(' ')[0]
        self.owner_first_name = owner.split(' ')[0]
        self.apple_id_account_owner = f"{owner} ({apple_id})"
        self.password = 'pw-not-real'
        self.apple_server_location = server_location
        self.state = state
        self.is_reauth_needed = state == 'needs_code'
        self.is_reauth_needed_secs = time.time() if self.is_reauth_needed else 0
        self.was_auth_code_requested = state == 'needs_code'
        self.is_2fa_challenge_session_live = state == 'needs_code'
        self.alerts_by_alert_key = {}
        self.account_locked = False
        self.terms_of_use_repair_issue_posted = False
        self.terms_of_use_update_needed = state == 'terms'
        self.terms_of_use_accepted = state != 'terms'
        self.login_successful = state in ('signed_in', 'needs_code', 'terms')
        self.login_successful_srp = self.login_successful
        self.is_authenticated = state == 'signed_in'
        self.auth_failed_503 = state == 'failed_503'
        self.response_code = {'login_failed': 401, 'failed_503': 503}.get(state, 200)
        self.response_code_pw = self.response_code
        self.response_code_desc = ''
        self.error_next_retry_secs = 0
        self.error_retry_cnt = 0
        self.current_auth_method = auth_method
        self.hwkey_names = ''
        self.HwKey = None
        self.is_auth_method_PUSH = auth_method == 'push'
        self.is_auth_method_TEXT = auth_method.startswith('text')
        self.is_auth_method_HWKEY = auth_method == 'hwkey'
        self.was_ha_auth_code_alert_sent = False
        self.is_auth_alert_displayed = False
        self.trusted_phone_data = [{'id': 1, 'numberWithDialCode': '+49 0000 0012'}]
        self.iCloudSession = None
        self.session_filename = f"/tmp/does-not-exist/{self.apple_user}.session"
        self.cookies_filename = f"/tmp/does-not-exist/{self.apple_user}.cookies"
        self.conf_apple_acct = {}
        self.AppleAcct = self
        self.device_id_by_aadev_dname = {}
        self.device_model_name_by_aadev_dname = {}
        self.device_model_info_by_aadev_dname = {}
        self.AADev_by_device_id = {}
        for i, (aadev_name, model_info, *ids) in enumerate(devices):
            device_id = ids[0] if ids else f"{self.apple_user}-dev{i}"
            self.device_id_by_aadev_dname[aadev_name] = device_id
            self.device_model_name_by_aadev_dname[aadev_name] = model_info[2]
            self.device_model_info_by_aadev_dname[aadev_name] = list(model_info)
            self.AADev_by_device_id[device_id] = FakeAADev(aadev_name, device_id, model_info, owner)
        self.aadevice_dnames = list(self.device_id_by_aadev_dname)
        self._results = {'async_validate_apple_id_password': _async_value(False),
                         'async_validate_apple_id_password_srp': _async_value(False),
                         'authenticate': False, 'code_description': '',
                         'auth_method_value': auth_method,
                         'get_hwkey_names': '', 'setup_error': None,
                         **(results or {})}

    @property
    def auth_methods(self):
        return self.conf_apple_acct.get('auth_methods', {})

    @property
    def current_auth_method_value(self):
        return self.auth_methods.get(self.current_auth_method, '')

    def __getattr__(self, attr):
        if attr in FakeAppleAcct.METHODS:
            return _Recorder(self, attr)
        if attr.startswith('__'):
            raise AttributeError(attr)
        FAKE_MISSING_ATTRS.add(f"AppleAcct.{attr}")
        raise AttributeError(f"FakeAppleAcct has no attribute {attr!r} (add it to the fake)")

    def __repr__(self):
        return f"<FakeAppleAcct {self.apple_id} {self.state}>"


class FakeAADev:
    def __init__(self, name, device_id, model_info, owner):
        self.name = self.fname = self.device_name = name
        self.device_id = device_id
        self.raw_model, self.model, self.model_display_name = model_info
        self.data_source = 'iCloud'
        self.family_share_device = False
        self.owner_first_name = owner.split(' ')[0]
        self.startup_msg = ''

    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError(attr)
        FAKE_MISSING_ATTRS.add(f"AADev.{attr}")
        raise AttributeError(attr)


class FakeDevice:
    def __init__(self, conf_device, located_secs_ago=None, zone='home'):
        self.devicename = conf_device['ic3_devicename']
        self.fname = conf_device['fname']
        self.fname_devicename = f"{self.fname} ({self.devicename})"
        self.conf_apple_acct_apple_id = conf_device.get('apple_account', '')
        self.family_share_device = False
        self.loc_data_secs = (time.time() - located_secs_ago) if located_secs_ago is not None else 0
        self.loc_data_zone = zone
        self.is_tracked = conf_device['tracking_mode'] == 'track'
        self.is_monitored = conf_device['tracking_mode'] == 'monitor'
        self.primary_data_source = 'iCloud'
        self.paused = False
        self.alerts_by_alert_key = {}

    def pause_tracking(self):
        self.paused = True

    def __getattr__(self, attr):
        if attr.startswith('__'):
            raise AttributeError(attr)
        FAKE_MISSING_ATTRS.add(f"Device.{attr}")
        raise AttributeError(attr)


class FakeLovelaceResources:
    def __init__(self):
        self.items = []
        self.loaded = True

    async def async_load(self):
        pass

    def async_items(self):
        return list(self.items)

    async def async_create_item(self, data):
        self.items.append({'id': str(len(self.items)), **data})
        return self.items[-1]

    async def async_update_item(self, item_id, data):
        return data

    async def async_delete_item(self, item_id):
        self.items = [i for i in self.items if i['id'] != item_id]


class FakeLovelace:
    '''hass.data['lovelace'] (LovelaceData) without dashboards'''
    def __init__(self):
        self.dashboards = {}
        self.yaml_dashboards = {}
        self.resources = FakeLovelaceResources()
        self.resource_mode = 'storage'
        self.mode = 'storage'


#----------------------------------------------------------------------------------------
#   Scenarios
#----------------------------------------------------------------------------------------
MODELS = [('iPhone15,2', 'iPhone', 'iPhone 14 Pro'), ('iPad7,11', 'iPad', 'iPad (7th generation)'),
          ('Watch6,1', 'Watch', 'Apple Watch Series 7'), ('iPhone16,1', 'iPhone', 'iPhone 15'),
          ('MacBookPro18,1', 'MacBook', 'MacBook Pro'), ('AirPods1,1', 'AirPods', 'AirPods'),
          ('iPod9,1', 'iPod', 'iPod touch')]
DEVICE_TYPE_BY_MODEL = {'iPhone': 'iphone', 'iPad': 'ipad', 'Watch': 'watch', 'MacBook': 'mac',
                        'AirPods': 'airpods', 'iPod': 'ipod'}


@dataclass
class Account:
    apple_id: str
    owner: str
    state: str = 'signed_in'
    auth_method: str = 'push'
    password: str = 'secret-not-real'


@dataclass
class Dev:
    devicename: str
    fname: str
    acct: int | None = 0                # index of the Account, None = no Apple Account
    model: int = 0                      # MODELS index
    tracking_mode: str = 'track'
    mobapp: str = 'None'
    located_secs_ago: int | None = 300


@dataclass
class Scenario:
    name: str
    accounts: list = field(default_factory=list)
    devices: list = field(default_factory=list)
    data_source: str = 'iCloud,MobApp'
    conf_version: int = 1               # conf_profile version, 0 = just installed
    analytics_enabled: bool | None = False
    unit: str = 'mi'
    general: dict = field(default_factory=dict)

    def __str__(self):
        return self.name


def _acct(i, state='signed_in', **kw):
    return Account(f"user{i}@example.com", f"Owner{i} Test", state=state, **kw)


def _devs(n, acct=0, start=0, **kw):
    return [Dev(f"dev{start + i}_test", f"Device {start + i}", acct=acct, model=(start + i) % 5, **kw)
            for i in range(n)]


SCENARIOS = {
    'fresh':            Scenario('fresh', conf_version=0, analytics_enabled=None),
    'one_acct':         Scenario('one_acct', [_acct(1)],
                                 [Dev('max_iphone', 'Max iPhone', model=0),
                                  Dev('ipad_seven', 'iPad (7)', model=1, tracking_mode='monitor')]),
    'no_devices':       Scenario('no_devices', [_acct(1)], []),
    'needs_code':       Scenario('needs_code', [_acct(1, 'needs_code')], _devs(2)),
    'needs_code_text':  Scenario('needs_code_text', [_acct(1, 'needs_code', auth_method='text_1')], _devs(2)),
    'terms':            Scenario('terms', [_acct(1, 'terms')], _devs(2)),
    'login_failed':     Scenario('login_failed', [_acct(1, 'login_failed')], _devs(2)),
    'failed_503':       Scenario('failed_503', [_acct(1, 'failed_503')], _devs(1)),
    'many':             Scenario('many', [_acct(i) for i in range(1, 7)],
                                 [d for i in range(6) for d in _devs(2, acct=i, start=2 * i)]),
    'many_mixed':       Scenario('many_mixed',
                                 [_acct(1), _acct(2, 'needs_code'), _acct(3, 'login_failed'),
                                  _acct(4, 'terms'), _acct(5), _acct(6)],
                                 _devs(4, acct=0) + _devs(3, acct=1, start=4) + _devs(2, acct=4, start=7)),
    'all_inactive':     Scenario('all_inactive', [_acct(1)], _devs(3, tracking_mode='inactive')),
    'some_inactive':    Scenario('some_inactive', [_acct(1)],
                                 _devs(2) + _devs(2, start=2, tracking_mode='inactive')),
    'no_data_source':   Scenario('no_data_source', [_acct(1)],
                                 _devs(1) + [Dev('orphan', 'Orphan Device', acct=None)]),
    'mobapp_only':      Scenario('mobapp_only', [], [Dev('mob_phone', 'Mob Phone', acct=None,
                                                         mobapp='mobile_app_mob_phone')],
                                 data_source='MobApp'),
    'analytics_ask':    Scenario('analytics_ask', [_acct(1)], _devs(2), analytics_enabled=None),
    'metric':           Scenario('metric', [_acct(1)], _devs(2), unit='km'),
}


#----------------------------------------------------------------------------------------
def conf_account(acct, default):
    conf = copy.deepcopy(default)
    conf.update({'apple_account': acct.apple_id, 'username': acct.apple_id,
                 'password': acct.password})
    conf['auth_methods'] = {**conf.get('auth_methods', {}), 'current': acct.auth_method}
    if acct.auth_method.startswith('text_'):
        conf['auth_methods'][acct.auth_method] = '**12'
    return conf


def conf_device(dev, scenario, default):
    conf = copy.deepcopy(default)
    raw_model, model, model_dname = MODELS[dev.model]
    acct = scenario.accounts[dev.acct] if dev.acct is not None else None
    conf.update({'ic3_devicename': dev.devicename, 'fname': dev.fname,
                 'device_type': DEVICE_TYPE_BY_MODEL[model], 'tracking_mode': dev.tracking_mode,
                 'mobile_app_device': dev.mobapp})
    if acct:
        conf.update({'apple_account': acct.apple_id, 'apple_device_name': f"{dev.fname} AA",
                     'apple_device_id': f"{acct.apple_id.split('@')[0]}-{dev.devicename}",
                     'raw_model': raw_model, 'model': model, 'model_display_name': model_dname})
        # The legacy famshr_ fields are kept in sync with the apple_ ones by config_file
        conf['famshr_devicename'] = conf['apple_device_name']
        conf['famshr_device_id'] = conf['apple_device_id']
    return conf


async def build_ic3_state(hass, entry, scenario: Scenario, config_override=None):
    '''
    Set the Gb globals like the integration's startup does (without logging into Apple).
    config_override - a configuration file dict written as is, instead of the scenario
    Returns Gb.
    '''
    Gb = ic3('global_variables').GlobalVariables
    start_ic3 = ic3('startup.start_ic3')
    config_file = ic3('startup.config_file')
    const_config = ic3('const_config')

    hass.states.async_set('zone.home', 'zoning', {'latitude': 52.52, 'longitude': 13.40,
                          'radius': 100, 'friendly_name': 'Home', 'passive': False})
    hass.states.async_set('zone.work', '0', {'latitude': 52.50, 'longitude': 13.30,
                          'radius': 150, 'friendly_name': 'Work', 'passive': False})

    Gb.hass, Gb.config_entry, Gb.config_entry_id = hass, entry, entry.entry_id
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {}
    hass.data[DOMAIN][entry.unique_id] = DOMAIN
    hass.data['lovelace'] = FakeLovelace()
    Gb.operating_mode = 'Integration'
    start_ic3.initialize_directory_filenames()

    if config_override is None:
        # The integration creates the default configuration file, the scenario changes it
        await config_file.async_load_icloud3_configuration_file()
        Gb.conf_profile['version'] = scenario.conf_version
        Gb.conf_tracking['data_source'] = scenario.data_source
        Gb.conf_apple_accounts[:] = [conf_account(a, const_config.DEFAULT_APPLE_ACCOUNT_CONF)
                                     for a in scenario.accounts]
        Gb.conf_devices[:] = [conf_device(d, scenario, const_config.DEFAULT_DEVICE_CONF)
                              for d in scenario.devices]
        Gb.conf_general['unit_of_measurement'] = scenario.unit
        Gb.conf_general['analytics_enabled'] = scenario.analytics_enabled
        Gb.conf_general.update(scenario.general)
        Gb.conf_profile['picture_www_dirs'] = ['www/icloud3']
        await hass.async_add_executor_job(config_file.write_icloud3_configuration_file)
    else:
        os.makedirs(Gb.ha_storage_icloud3, exist_ok=True)
        with open(Gb.icloud3_config_filename, 'w') as f:
            json.dump(config_override, f, indent=4)
    await config_file.async_load_icloud3_configuration_file()

    _try('EventLog', lambda: setattr(Gb, 'EvLog', ic3('support.event_log').EventLog()))
    _try('InternetError', lambda: setattr(Gb, 'InternetError',
                    ic3('apple_acct.internet_error').InternetConnection_ErrorHandler()))
    for name in ('initialize_global_variables', 'set_global_variables_from_conf_parameters',
                 'initialize_data_source_variables', 'set_um_formats', 'set_zone_display_as'):
        func = getattr(start_ic3, name, None)
        if func:
            _try(name, func)
    Gb.polling_5_sec_loop_running = True
    Gb.restore_state_apple_accts = {}          # set by startup/restore_state.py
    _try('ValidateAppleAcctUPW', lambda: setattr(Gb, 'ValidateAppleAcctUPW',
                    ic3('apple_acct.apple_acct_upw').ValidateAppleAcctUPW()))
    Gb.analytics_enabled = Gb.conf_general.get('analytics_enabled')
    Gb.internet_error = False

    # Apple Accounts and devices as the startup would leave them
    Gb.AppleAcct_by_apple_id = {}
    Gb.AppleAcct_error_by_apple_id = {}
    Gb.upw_valid_by_apple_id = {}
    Gb.AppleAcct_reauth_needed = None
    for i, acct in enumerate(scenario.accounts):
        devices = [(f"{d.fname} AA", MODELS[d.model], f"{acct.apple_id.split('@')[0]}-{d.devicename}")
                   for d in scenario.devices if d.acct == i]
        AppleAcct = FakeAppleAcct(acct.apple_id, acct.owner, acct.state, devices, acct.auth_method)
        AppleAcct.conf_apple_acct = next((c for c in Gb.conf_apple_accounts
                                          if c['apple_account'] == acct.apple_id), {})
        Gb.AppleAcct_by_apple_id[acct.apple_id] = AppleAcct
        Gb.upw_valid_by_apple_id[acct.apple_id] = acct.state != 'login_failed'
        if acct.state == 'login_failed':
            Gb.AppleAcct_error_by_apple_id[acct.apple_id] = AppleAcct
        if acct.state == 'needs_code' and Gb.AppleAcct_reauth_needed is None:
            Gb.AppleAcct_reauth_needed = AppleAcct
    Gb.AppleAcct_password_by_apple_id = {a.apple_id: a.password for a in scenario.accounts}

    Gb.Devices, Gb.Devices_by_devicename = [], {}
    Gb.inactive_fname_by_devicename = {}
    Gb.Sensors_by_devicename = {}               # no HA sensor entities offline
    for conf_dev, dev in zip(Gb.conf_devices, scenario.devices):
        if dev.tracking_mode == 'inactive':
            Gb.inactive_fname_by_devicename[dev.devicename] = dev.fname
            continue
        Device = FakeDevice(conf_dev, dev.located_secs_ago)
        Gb.Devices.append(Device)
        Gb.Devices_by_devicename[dev.devicename] = Device
        Gb.Sensors_by_devicename[dev.devicename] = {}
    return Gb


def _try(name, func):
    try:
        func()
    except Exception as err:
        STARTUP_ERRORS.append((name, f"{type(err).__name__}: {err}"))


def read_config_file(Gb):
    with open(Gb.icloud3_config_filename) as f:
        return json.load(f)
