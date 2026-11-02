'''
Session (hass + entry + iCloud3 state) and Flow (one Configure window) for the offline tests.
'''
from __future__ import annotations

import copy
import json
import tempfile
import traceback
from pathlib import Path

from homeassistant import data_entry_flow

from . import harness as h
from . import scenarios as st
from .frontend import VirtualFrontend, collect_keys


class FlowException(Exception):
    pass


SAVE_ACTIONS = ('save', 'submit', 'update', 'save_device', 'update_device', 'save_apple_acct')
ACTION_FIELDS = ('form_action', 'action_items')


def config_diff(a, b, path=''):
    '''[(added|removed|changed, path, old, new)] between two configuration file dicts'''
    diffs = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else k
            if k not in a:
                diffs.append(('added', p, None, b[k]))
            elif k not in b:
                diffs.append(('removed', p, a[k], None))
            else:
                diffs += config_diff(a[k], b[k], p)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and all(isinstance(x, dict) for x in a + b):
        for i, (x, y) in enumerate(zip(a, b)):
            diffs += config_diff(x, y, f"{path}[{i}]")
    elif a != b or type(a) is not type(b):
        diffs.append(('changed', path, a, b))
    return diffs


# Updated on every write of the configuration file
IGNORED_CONFIG_PATHS = ('profile.config_ic3_version', 'profile.last_update', 'profile.updated',
                        'profile.config_update_date')


def settings_diff(a, b):
    return [d for d in config_diff(a, b) if not d[1].startswith(IGNORED_CONFIG_PATHS)]


class Session:
    '''One HA instance with the iCloud3 state of a scenario. Use: async with Session(...) as s'''
    def __init__(self, scenario, language='en', units=None, config_override=None, purge=True):
        self.scenario = scenario if isinstance(scenario, st.Scenario) else st.SCENARIOS[scenario]
        self.language, self.units = language, units
        self.config_override = config_override
        self.purge = purge
        self.flows = []

    async def __aenter__(self):
        if self.purge:
            h.purge_integration_modules()
        st.STARTUP_ERRORS.clear()
        st.APPLE_CALLS.clear()
        self.config_dir = Path(tempfile.mkdtemp(prefix='cfg-', dir=h.WORK))
        kwargs = {'units': self.units} if self.units else {}
        self.hass = await h.make_hass(self.config_dir, language=self.language, **kwargs)
        self.entry = h.add_entry(self.hass)
        self.Gb = await st.build_ic3_state(self.hass, self.entry, self.scenario, self.config_override)
        self.config_at_start = st.read_config_file(self.Gb)
        self.frontend = await self._frontend(self.language)
        return self

    async def __aexit__(self, *exc):
        for flow in self.flows:
            if flow.open:
                try:
                    await flow.close()
                except Exception:
                    pass
        await h.stop_hass(self.hass)

    async def _frontend(self, language):
        from homeassistant.helpers import translation
        texts = {}
        for lang in dict.fromkeys(['en', language]):
            for category in ('title', 'options', 'config', 'selector', 'issues', 'exceptions'):
                texts.update(await translation.async_get_translations(self.hass, lang, category, [h.DOMAIN]))
        strings = json.loads((h.CC_DIR / 'custom_components' / h.DOMAIN / 'strings.json').read_text())
        return VirtualFrontend(texts, known_keys=collect_keys(strings))

    def config(self):
        return st.read_config_file(self.Gb)

    async def flow(self, **kw):
        flow = Flow(self, **kw)
        self.flows.append(flow)
        await flow.start()
        return flow

    def repairs_manager(self):
        '''HA's RepairsFlowManager with the iCloud3 repairs platform'''
        if getattr(self, '_repairs', None) is None:
            from homeassistant.components.repairs.issue_handler import RepairsFlowManager
            repairs = h.ic3('repairs')

            class _Platforms:
                async def async_get_platform(self, domain):
                    return repairs if domain == h.DOMAIN else None

            self.hass.data.setdefault('repairs', {})['platforms'] = _Platforms()
            self._repairs = RepairsFlowManager(self.hass)
        return self._repairs

    async def repair_flow(self, issue_id):
        flow = Flow(self, source='repair', data={'issue_id': issue_id})
        self.flows.append(flow)
        await flow.start()
        return flow

    async def settle(self):
        await self.hass.async_block_till_done(wait_background_tasks=True)


class Flow:
    '''
    A Configure window. Every result is serialized like the REST API does and rendered by the
    virtual frontend; render issues are collected in self.issues as (level, step, where, msg).
    '''
    def __init__(self, session, source='options', context=None, data=None):
        self.s, self.source, self.context, self.data = session, source, context, data
        self.result = None
        self.history = []
        self.issues = []
        self.open = False

    @property
    def manager(self):
        if self.source == 'repair':
            return self.s.repairs_manager()
        return (self.s.hass.config_entries.options if self.source == 'options'
                else self.s.hass.config_entries.flow)

    async def start(self):
        if self.source == 'options':
            res = await self.manager.async_init(self.s.entry.entry_id)
        elif self.source == 'repair':
            from homeassistant.helpers import issue_registry as ir
            issue = ir.async_get(self.s.hass).async_get_issue(h.DOMAIN, self.data['issue_id'])
            self.issue_tkey = issue.translation_key if issue else None
            res = await self.manager.async_init(h.DOMAIN, data={'issue_id': self.data['issue_id']})
        else:
            res = await self.manager.async_init(h.DOMAIN, context=self.context or {'source': self.source},
                                                data=self.data)
        self.flow_id = res.get('flow_id')
        self.open = res.get('type') in ('form', 'menu', 'progress', 'external')
        return self._record(('start', None), res)

    async def menu(self, option):
        if self.result.get('type') != 'menu':
            raise FlowException(f"not on a menu ({self.step}) for {option}")
        if option not in self.options():
            raise FlowException(f"{option} not in menu {self.step}: {self.options()}")
        return await self._configure({'next_step_id': option}, ('menu', option))

    async def submit(self, data=None, **changes):
        '''Submit the form with the displayed defaults (like the browser) and the changes'''
        if self.result.get('type') != 'form':
            raise FlowException(f"not on a form ({self.step})")
        user_input = self.form_defaults() if data is None else copy.deepcopy(data)
        for key, value in changes.items():
            self._set(user_input, key, value)
        return await self._configure(user_input, ('form', user_input))

    async def action(self, form_action, **changes):
        return await self.submit(form_action=form_action, **changes)

    async def raw(self, user_input):
        return await self._configure(user_input, ('raw', user_input))

    async def _configure(self, user_input, entry):
        try:
            res = await self.manager.async_configure(self.flow_id, user_input)
        except data_entry_flow.InvalidData as err:
            # The REST API returns 400 with the schema errors, the frontend shows them
            self.history.append((entry, 'InvalidData', str(err)))
            raise
        except Exception as err:
            self.history.append((entry, 'EXCEPTION', traceback.format_exc()))
            raise FlowException(f"{type(err).__name__} in step {self.step} on {entry}: {err}") from err
        return self._record(entry, res)

    def _record(self, entry, res):
        self.raw_result = res
        try:
            ser = h.serialize_result(res)
        except Exception as err:
            self.issues.append(('ERROR', res.get('step_id'), 'serialize', f"REST serialization failed: {err!r}"))
            ser = json.loads(json.dumps({k: v for k, v in res.items() if k != 'data_schema'}, default=str))
        self.result = ser
        self.history.append((entry, ser.get('type'), ser.get('step_id') or ser.get('reason')))
        if ser.get('flow_id') and getattr(self, 'flow_id', None) and ser['flow_id'] != self.flow_id:
            self.issues.append(('ERROR', ser.get('step_id'), 'flow_id',
                                f"the reply has the flow_id of another window ({ser['flow_id']}, "
                                f"this window is {self.flow_id})"))
        if ser.get('type') not in ('form', 'menu', 'progress', 'external'):
            self.open = False
        flow = {'options': 'options', 'repair': 'repair'}.get(self.source, 'config')
        self.rendered = self.s.frontend.render(ser, flow=flow, issue_id=getattr(self, 'issue_tkey', None))
        for level, where, msg in self.rendered.issues:
            self.issues.append((level, self.rendered.step, where, msg))
        return ser

    async def close(self):
        '''The X button: the frontend DELETEs the flow, HA calls async_remove'''
        if self.open:
            self.manager.async_abort(self.flow_id)
            self.open = False
        await self.s.settle()

    #------------------------------------------------------------------
    @property
    def step(self):
        return self.result.get('step_id') if self.result else None

    @property
    def type(self):
        return self.result.get('type') if self.result else None

    def options(self):
        opts = self.result.get('menu_options') or []
        return list(opts.keys()) if isinstance(opts, dict) else list(opts)

    def schema(self):
        return self.result.get('data_schema') or []

    def field(self, name):
        def find(schema):
            for f in schema:
                if f.get('name') == name:
                    return f
                if f.get('type') == 'expandable':
                    found = find(f.get('schema') or [])
                    if found:
                        return found
        return find(self.schema())

    def field_names(self):
        names = []
        def walk(schema, prefix=''):
            for f in schema:
                if f.get('type') == 'expandable':
                    walk(f.get('schema') or [], f"{f['name']}.")
                else:
                    names.append(prefix + f['name'])
        walk(self.schema())
        return names

    def select_values(self, name):
        f = self.field(name) or {}
        if 'selector' not in f and f.get('type') == 'select':
            # vol.In(...): options are [value, label] pairs
            return [o[0] if isinstance(o, (list, tuple)) else o for o in f.get('options') or []]
        opts = ((f.get('selector') or {}).get('select') or {}).get('options') or []
        return [o['value'] if isinstance(o, dict) else o for o in opts]

    def save_choice(self):
        '''(action field, value) of the form's Save choice, value None if there is none.
        The action field is form_action (option keys) or action_items (display labels).'''
        for name in ACTION_FIELDS:
            values = self.select_values(name)
            if not values:
                continue
            for key in SAVE_ACTIONS:
                if key in values:
                    return name, key
            for v in values:
                if 'SAVE' in str(v).upper():
                    return name, v
            return name, None
        return None, None

    async def open_step(self, step):
        '''Show a step of this window's handler like a menu row would, without the menu.
        update_device/update_apple_acct open the first device/account. None if there is none.'''
        from homeassistant.data_entry_flow import FlowResultType
        handler = self.manager._progress[self.flow_id]
        Gb = self.s.Gb
        if step == 'update_device':
            if not Gb.conf_devices:
                return None
            coro = handler.async_open_update_device_screen(Gb.conf_devices[0]['ic3_devicename'])
        elif step == 'update_apple_acct':
            if not Gb.conf_apple_accounts:
                return None
            coro = handler.async_open_update_apple_acct_screen(Gb.conf_apple_accounts[0]['apple_account'])
        else:
            coro = getattr(handler, f"async_step_{step}")()
        res = await coro
        if not isinstance(res['type'], FlowResultType):
            res['type'] = FlowResultType(res['type'])
        if res['type'] in (FlowResultType.FORM, FlowResultType.MENU):
            handler.cur_step = res
        return self._record(('direct', step), res)

    def has_step(self, step):
        handler = self.manager._progress[self.flow_id]
        if step == 'update_device':
            return hasattr(handler, 'async_open_update_device_screen')
        if step == 'update_apple_acct':
            return hasattr(handler, 'async_open_update_apple_acct_screen')
        return hasattr(handler, f"async_step_{step}")

    def select_labels(self, name):
        for fname, label, desc, options in self.rendered.fields:
            if fname == name:
                return {v: l for v, l in options}
        return {}

    def actions(self):
        return self.select_values('form_action')

    def form_defaults(self):
        def defaults(schema):
            data = {}
            for f in schema:
                if f.get('type') == 'expandable':
                    data[f['name']] = defaults(f.get('schema') or [])
                elif 'default' in f:
                    data[f['name']] = copy.deepcopy(f['default'])
            return data
        return defaults(self.schema())

    def _set(self, user_input, key, value):
        '''key may be a field inside a section'''
        if key in user_input or self.field(key) is None:
            user_input[key] = value
            return
        for f in self.schema():
            if f.get('type') == 'expandable' and any(sf.get('name') == key for sf in f.get('schema') or []):
                user_input.setdefault(f['name'], {})[key] = value
                return
        user_input[key] = value

    def text(self):
        return self.rendered.text()

    def errors(self):
        return self.result.get('errors') or {}
