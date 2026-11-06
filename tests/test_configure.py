'''
Offline tests of the iCloud3 Configure flow: a real Home Assistant core, a fake Apple layer
and a temp configuration file. Nothing here contacts Apple or the network.

The screens are opened by their step id, like a menu item does, so these tests work with
the v3.8.0 menu (Menu #1/#2) and with HA menus. test_configure_menus.py has the tests that
need the HA menus.
'''
import copy
import json

import pytest
from homeassistant import data_entry_flow

from support import harness as h
from support import scenarios as st
from support.flow import Session, Flow, FlowException, settings_diff


def render_errors(flow):
    return [i for i in flow.issues if i[0] == 'ERROR']


def field_defaults(flow):
    '''{field name: default} with the sections flattened'''
    out = {}
    def walk(schema):
        for f in schema:
            if f.get('type') == 'expandable':
                walk(f.get('schema') or [])
            else:
                out[f['name']] = f.get('default', '<none>')
    walk(flow.schema())
    return out


# The settings screens that open by themselves (the others need a device or an account
# that the screen before them selects)
SETTINGS_STEPS = ['tracking_parameters', 'format_settings', 'display_text_as', 'away_time_zone',
                  'inzone_intervals', 'waze_main', 'special_zones', 'sensors',
                  'update_device', 'update_apple_acct']
SETTINGS_SCENARIOS = ['one_acct', 'many_mixed', 'metric', 'mobapp_only']


async def open_settings_step(s, step):
    flow = await s.flow()
    if not flow.has_step(step):
        pytest.skip(f"the code has no {step} step")
    if await flow.open_step(step) is None:
        pytest.skip(f"{s.scenario} has no device/Apple Account for {step}")
    if flow.type == 'menu':
        pytest.skip(f"{step} is a menu in this code")
    return flow


#----------------------------------------------------------------------------------------
#   Open / close
#----------------------------------------------------------------------------------------
@pytest.mark.parametrize('scenario', list(st.SCENARIOS))
async def test_open_close_is_noop(scenario):
    '''Opening Configure and closing it with X does not change the configuration file'''
    async with Session(scenario) as s:
        flow = await s.flow()
        assert flow.type in ('menu', 'form'), flow.result
        assert not render_errors(flow), render_errors(flow)
        before = s.config()
        await flow.close()
        assert st.STARTUP_ERRORS == []
        if scenario != 'fresh':
            assert settings_diff(before, s.config()) == []
        assert h.NETWORK_ATTEMPTS == []


async def test_fresh_install_opens_add_apple_acct():
    '''A new install opens the Apple Account screen. Its fields are prefilled with ' ';
    saving them unchanged must not add a blank Apple Account.'''
    async with Session('fresh') as s:
        flow = await s.flow()
        assert flow.step == 'update_apple_acct'
        assert not render_errors(flow), render_errors(flow)
        name, save = flow.save_choice()
        assert save, f"no Save choice in {flow.select_values(name)}"
        try:
            await flow.submit(**{name: save})
        except data_entry_flow.InvalidData:
            pass
        assert not render_errors(flow), render_errors(flow)
        accounts = s.config()['data']['tracking']['apple_accounts']
        assert all(a['apple_account'].strip() for a in accounts), accounts
        assert h.NETWORK_ATTEMPTS == []


#----------------------------------------------------------------------------------------
#   Settings screens: same configuration file in, same file out
#----------------------------------------------------------------------------------------
@pytest.mark.parametrize('step', SETTINGS_STEPS)
@pytest.mark.parametrize('scenario', SETTINGS_SCENARIOS)
async def test_settings_screen_saved_unchanged(scenario, step):
    '''Save a settings screen with the values it shows: the configuration file does not
    change, and the screen shows the same values when it is opened again'''
    async with Session(scenario) as s:
        flow = await open_settings_step(s, step)
        assert flow.type == 'form', flow.result
        assert not render_errors(flow), render_errors(flow)
        shown = field_defaults(flow)
        name, save = flow.save_choice()
        before = s.config()
        if save:
            await flow.submit(**{name: save})
        else:
            await flow.submit()
        assert not render_errors(flow), render_errors(flow)
        await s.settle()
        assert settings_diff(before, s.config()) == []
        if flow.open:
            await flow.close()
        again = await s.flow()
        await again.open_step(step)
        assert again.type == 'form', again.result
        changed = {k: (v, field_defaults(again).get(k, '<gone>'))
                   for k, v in shown.items() if field_defaults(again).get(k, '<gone>') != v}
        assert changed == {}
        assert h.NETWORK_ATTEMPTS == []


def _bad_values(fld):
    sel = fld.get('selector') or {}
    if 'number' in sel:
        n = sel['number']
        vals = []
        if n.get('min') is not None:
            vals.append(n['min'] - 1)
        if n.get('max') is not None:
            vals.append(n['max'] + 1)
        return vals + ['abc', None]
    if 'text' in sel:
        return ['', '   ', 'x' * 500, '{acct_name}', "it's", '<b>x</b>']
    if 'select' in sel:
        return ['not-an-option', [] if not sel['select'].get('multiple') else ['not-an-option']]
    if fld.get('type') == 'boolean' or 'boolean' in sel:
        return ['yes']
    return []


@pytest.mark.parametrize('step', SETTINGS_STEPS)
async def test_settings_screen_bad_input(step):
    '''Bad values are rejected by the form (schema) or answered with an error message,
    never with an exception or a broken screen'''
    async with Session('one_acct') as s:
        flow = await open_settings_step(s, step)
        fields = []
        def walk(schema, section=None):
            for fld in schema:
                if fld.get('type') == 'expandable':
                    walk(fld.get('schema') or [], fld['name'])
                elif fld['name'] not in ('form_action', 'action_items'):
                    fields.append((section, fld))
        walk(flow.schema())
        name, save = flow.save_choice()
        await flow.close()
        problems = []
        for section, fld in fields:
            for bad in _bad_values(fld):
                g = await s.flow()
                await g.open_step(step)
                data = g.form_defaults()
                target = data.setdefault(section, {}) if section else data
                target[fld['name']] = bad
                if save:
                    data[name] = save
                try:
                    await g.raw(data)
                    problems += [(fld['name'], bad, e) for e in render_errors(g)]
                except data_entry_flow.InvalidData:
                    pass
                except FlowException as err:
                    problems.append((fld['name'], repr(bad)[:40], str(err)[:240]))
                await g.close()
        assert problems == []


async def test_device_fixed_interval_error_stays_on_the_screen():
    '''A Fixed Interval of 1 or 2 minutes is changed to 3 with an error message. The
    message is shown on the same screen, with its texts, and the screen still saves.'''
    async with Session('one_acct') as s:
        f = await open_settings_step(s, 'update_device')
        path = []
        if not f.field('fixed_interval'):
            # v3.8.0: the field is on the screen behind "Update other device parameters"
            for name in ('form_action', 'action_items'):
                for act in f.select_values(name):
                    if 'OTHER DEVICE PARAMETERS' in str(act).upper():
                        path = [(name, act)]
        g = await s.flow()
        await g.open_step('update_device')
        for name, act in path:
            await g.submit(**{name: act})
        if not g.field('fixed_interval'):
            pytest.skip('no Fixed Interval field on the device screens')
        step = g.step
        name, save = g.save_choice()
        try:
            await g.submit(fixed_interval=1, **({name: save} if save else {}))
        except FlowException as err:
            pytest.fail(f"saving Fixed Interval 1 on {step} fails: {err}")
        assert g.type == 'form' and g.step == step, \
            f"the error screen has step_id {g.step!r}, the screen was {step!r}"
        # The error is on the field, or on the section the field is in
        assert g.errors(), 'no error message'
        assert not render_errors(g), render_errors(g)
        try:
            await g.submit(**({name: save} if save else {}))
        except (FlowException, data_entry_flow.UnknownStep) as err:
            pytest.fail(f"saving the screen after the error fails: {err}")


#----------------------------------------------------------------------------------------
#   Two Configure windows
#----------------------------------------------------------------------------------------
async def test_two_windows_each_keep_their_screen():
    '''Two Configure windows (two browser tabs, a phone and a laptop) are two flows. A Save
    in one window is checked against that window's screen and answered to that window.'''
    async with Session('one_acct') as s:
        a = await s.flow()
        b = await s.flow()
        assert a.flow_id != b.flow_id
        await a.open_step('tracking_parameters')
        await b.open_step('format_settings')
        name, save = a.save_choice()
        try:
            await a.submit(**{name: save})
        except data_entry_flow.InvalidData as err:
            pytest.fail(f"window A's Save was checked against window B's screen: {err}")
        assert not render_errors(a), render_errors(a)
        await b.close()
        await a.close()
        assert settings_diff(s.config_at_start, s.config()) == []


async def test_save_in_one_window_other_window_closes_cleanly():
    async with Session('one_acct') as s:
        a = await s.flow()
        b = await s.flow()
        await a.open_step('tracking_parameters')
        name, save = a.save_choice()
        assert save, a.select_values(name)
        await b.open_step('update_device')
        await b.close()             # B closed first, nothing changed in B
        await a.submit(**{name: save})
        assert not render_errors(a), render_errors(a)
        await a.close()
        assert h.NETWORK_ATTEMPTS == []
        assert settings_diff(s.config_at_start, s.config()) == []


#----------------------------------------------------------------------------------------
#   Resubmits (double clicks, the browser's back button after a step)
#----------------------------------------------------------------------------------------
async def test_double_click_form_save():
    '''The second identical POST reaches the screen after the Save: HA rejects it (schema)
    or the screen handles it, the configuration file is not changed'''
    async with Session('one_acct') as s:
        f = await s.flow()
        await f.open_step('tracking_parameters')
        data = f.form_defaults()
        name, save = f.save_choice()
        data[name] = save
        await f.raw(copy.deepcopy(data))
        assert f.step != 'tracking_parameters' or f.errors(), f.result
        try:
            await f.raw(copy.deepcopy(data))
        except (data_entry_flow.InvalidData, data_entry_flow.UnknownStep):
            pass
        await f.close()
        assert settings_diff(s.config_at_start, s.config()) == []


#----------------------------------------------------------------------------------------
#   HA reauth and Repairs
#----------------------------------------------------------------------------------------
def config_flow(s, source):
    flow = Flow(s, source=source, context={'source': source, 'entry_id': s.entry.entry_id,
                                           'unique_id': s.entry.unique_id},
                data=dict(s.entry.data))
    s.flows.append(flow)
    return flow


async def test_reauth_config_flow_entry_point():
    '''HA's reauth notification (Reconfigure on the integration card) opens the config
    flow with source reauth'''
    async with Session('needs_code') as s:
        f = config_flow(s, 'reauth')
        try:
            await f.start()
        except FlowException as err:
            pytest.fail(str(err))
        assert f.type in ('form', 'abort', 'menu'), f.result
        assert not render_errors(f), render_errors(f)
        if f.type == 'form':
            for action in f.actions():
                g = config_flow(s, 'reauth')
                await g.start()
                try:
                    await g.action(action)
                except data_entry_flow.InvalidData:
                    pass
                assert not render_errors(g), (action, render_errors(g))
        assert h.NETWORK_ATTEMPTS == []


def _post_issues(s):
    '''Post the fixable issues with iCloud3's own functions, return the issue_ids'''
    from homeassistant.helpers import issue_registry as ir
    msg = h.ic3('utils.messaging')
    aas = h.ic3('apple_acct.apple_acct_support')
    start_ic3 = h.ic3('startup.start_ic3')
    AppleAcct = next(iter(s.Gb.AppleAcct_by_apple_id.values()))
    devicename = s.Gb.conf_devices[0]['ic3_devicename']
    posts = [
        ('terms_of_use', lambda: aas.post_repair_issue_aa_terms_of_use(AppleAcct)),
        ('update_device', lambda: msg.post_repair_issue_update_device(
                f"device_replaced_{devicename}_abcd1234", devicename,
                'Newer Apple Device detected', 'The device was replaced')),
        ('update_apple_acct', lambda: msg.post_repair_issue_update_apple_acct(
                f"apple_acct_unknown_{AppleAcct.apple_user}", AppleAcct.apple_id,
                'Apple Acct not found', 'Check the Apple Account')),
        ('analytics', lambda: start_ic3.request_analytics_approval()),
    ]
    for name, post in posts:
        try:
            post()
        except AttributeError as err:
            print(f"skip {name}: {err}")
    reg = ir.async_get(s.hass)
    return [(issue.issue_id, issue.translation_key) for (domain, _), issue in reg.issues.items()
            if domain == h.DOMAIN and issue.is_fixable]


def _choice_field(f):
    '''The field a fix flow's first screen asks for: form_action, else the first select
    without a default'''
    if f.actions():
        return 'form_action'
    return next((fld['name'] for fld in f.schema()
                 if ('select' in (fld.get('selector') or {}) or fld.get('type') == 'select')
                 and 'default' not in fld), None)


@pytest.mark.parametrize('scenario', ['terms', 'analytics_ask'])
async def test_repairs_fix_flows(scenario):
    '''Each fixable Repairs issue opens, renders, and every first-screen choice works'''
    repairs = h.ic3('repairs')
    if not hasattr(repairs, 'async_create_fix_flow'):
        pytest.skip('no repairs.async_create_fix_flow')
    async with Session(scenario) as s:
        issues = _post_issues(s)
        assert issues, 'no fixable issues were posted'
        problems = []
        for issue_id, tkey in issues:
            f = await s.repair_flow(issue_id)
            problems += [(issue_id, 'open', e) for e in render_errors(f)]
            if f.type != 'form':
                problems.append((issue_id, 'open', f"opened {f.type}:{f.step}"))
                continue
            name = _choice_field(f)
            choices = f.select_values(name) if name else [None]
            for choice in choices:
                # A fix removes the issue (and answers the analytics question)
                s.Gb.conf_general['analytics_enabled'] = s.scenario.analytics_enabled
                s.Gb.analytics_enabled = s.scenario.analytics_enabled
                _post_issues(s)
                g = await s.repair_flow(issue_id)
                try:
                    if choice is None:
                        await g.submit()
                    else:
                        await g.submit(**{name: choice})
                except data_entry_flow.InvalidData as err:
                    problems.append((issue_id, choice, f"rejected: {err}"))
                    continue
                except FlowException as err:
                    problems.append((issue_id, choice, str(err)[:240]))
                    continue
                problems += [(issue_id, choice, e) for e in render_errors(g)]
                if g.type == 'form':
                    back = [a for a in g.actions() if a in ('back', 'cancel', 'cancel_goto_menu')
                            or a.startswith('rtn_') or a.endswith('_back')]
                    if back:
                        try:
                            await g.action(back[0])
                        except (FlowException, data_entry_flow.InvalidData) as err:
                            problems.append((issue_id, choice, f"back: {str(err)[:200]}"))
                        problems += [(issue_id, f"{choice} back", e) for e in render_errors(g)]
                        if g.type not in ('abort', 'create_entry', 'form', 'menu'):
                            problems.append((issue_id, choice, f"back ended as {g.type}"))
        assert problems == []
        assert h.NETWORK_ATTEMPTS == []


#----------------------------------------------------------------------------------------
#   Not depending on English texts
#----------------------------------------------------------------------------------------
def _fake_translation(en):
    '''en.json with every text changed (placeholders kept): the screens must work the same'''
    import re
    def conv(v):
        if isinstance(v, dict):
            return {k: conv(x) for k, x in v.items()}
        if isinstance(v, str):
            parts = re.split(r'(\{[^{}]*\})', v)
            return ''.join(p if p.startswith('{') else p.upper().replace('A', 'Ä') for p in parts) + ' ·de'
        return v
    return conv(en)


async def test_language_independent_settings_screens():
    '''With a German translation the settings screens show the same fields and choices,
    and saving them does the same'''
    en = json.loads((h.CC_DIR / 'custom_components' / h.DOMAIN / 'translations' / 'en.json').read_text())
    h.prepare_code_copy({'de': _fake_translation(en)})
    seqs = {}
    for lang in ('en', 'de'):
        async with Session('one_acct', language=lang) as s:
            seq = []
            for step in SETTINGS_STEPS:
                f = await s.flow()
                if not f.has_step(step) or await f.open_step(step) is None:
                    continue
                name, save = f.save_choice()
                seq.append((step, f.type, tuple(f.field_names()), name, save))
                if lang == 'de':
                    assert not render_errors(f), render_errors(f)
                if save:
                    try:
                        await f.submit(**{name: save})
                        seq.append((step, 'save', f.type, f.step))
                    except (data_entry_flow.InvalidData, FlowException) as err:
                        seq.append((step, 'save', 'error', str(err)[:80]))
                await f.close()
            seqs[lang] = (seq, settings_diff(s.config_at_start, s.config()))
    assert seqs['en'] == seqs['de']
