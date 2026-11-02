'''
Offline tests of the Configure screens that are HA menus (async_show_menu): the main menu,
its Needs attention rows, every row of every menu. They skip themselves when the main
screen is not an HA menu (v3.8.0 has the Menu #1/#2 forms).
'''
import json

import pytest
from homeassistant import data_entry_flow

from support import harness as h
from support.flow import Session, FlowException, settings_diff


def render_errors(flow):
    return [i for i in flow.issues if i[0] == 'ERROR']


def has_attention_rows():
    try:
        return hasattr(h.ic3('configure.const_form_lists'), 'MENU_ACTION_NEEDED_ITEMS')
    except Exception:
        return False


async def main_menu(s):
    flow = await s.flow()
    if flow.type != 'menu':
        pytest.skip(f"the main screen is a {flow.type} ({flow.step}), not an HA menu")
    return flow


@pytest.fixture
def attention_rows():
    if not has_attention_rows():
        pytest.skip('no Needs attention rows (const_form_lists.MENU_ACTION_NEEDED_ITEMS)')


#----------------------------------------------------------------------------------------
#   Main menu: Needs attention rows
#----------------------------------------------------------------------------------------
EXPECTED_ATTENTION = {
    'one_acct':        set(),
    'needs_code':      {'open_action_reauth'},
    'needs_code_text': {'open_action_reauth'},
    'terms':           {'open_action_terms_of_use'},
    'login_failed':    {'open_action_login_failed'},
    'no_devices':      {'open_action_add_devices'},
    'all_inactive':    {'open_action_review_inactive'},
    'some_inactive':   {'open_action_review_inactive_some'},
    'no_data_source':  {'open_action_no_data_source'},
    'analytics_ask':   {'open_action_analytics'},
    'many':            set(),
    'many_mixed':      {'open_action_reauth', 'open_action_terms_of_use', 'open_action_login_failed'},
}

# The step each attention row opens
ATTENTION_TARGET = {
    'open_action_reauth':               'reauth',
    'open_action_terms_of_use':         'reauth',
    'open_action_login_failed':         ('update_apple_acct', 'apple_accounts'),
    'open_action_add_devices':          ('import_apple_devices', 'device_list', 'update_device'),
    'open_action_review_inactive':      'review_inactive_devices',
    'open_action_review_inactive_some': 'review_inactive_devices',
    'open_action_no_data_source':       'update_device',
    'open_action_analytics':            'analytics',
}


@pytest.mark.parametrize('scenario', list(EXPECTED_ATTENTION))
async def test_attention_rows(scenario, attention_rows):
    async with Session(scenario) as s:
        flow = await main_menu(s)
        assert flow.step == 'menu', flow.result
        rows = {o for o in flow.options() if o.startswith('open_action_')}
        assert rows == EXPECTED_ATTENTION[scenario]
        # The status line counts the problems (analytics is a question, not a problem)
        status = flow.result['description_placeholders'].get('status_line', '')
        problems = len(rows - {'open_action_analytics'})
        assert ('attention' in status.lower()) == bool(problems) or not status, status
        for row in sorted(rows):
            f = await s.flow()
            await f.menu(row)
            target = ATTENTION_TARGET[row]
            assert f.step in (target if isinstance(target, tuple) else (target,)), (row, f.step)
            assert not render_errors(f), (row, render_errors(f))
            await f.close()


async def test_no_data_source_row_opens_that_device(attention_rows):
    async with Session('no_data_source') as s:
        flow = await main_menu(s)
        await flow.menu('open_action_no_data_source')
        assert flow.step == 'update_device'
        assert 'Orphan Device' in json.dumps(flow.result, ensure_ascii=False)


@pytest.mark.parametrize('scenario', ['needs_code', 'login_failed', 'no_data_source', 'many_mixed'])
async def test_attention_rows_readable_without_descriptions(scenario, attention_rows):
    '''HA before 2025.10 shows only the row labels (no menu_option_descriptions): they must
    still name the account / device that needs attention'''
    async with Session(scenario) as s:
        f = await main_menu(s)
        ph = f.result['description_placeholders']
        for key, label, desc in f.rendered.rows:
            if not key.startswith('open_action_') or key == 'open_action_analytics':
                continue
            names = [v for k, v in ph.items() if k.endswith(('_acct', '_device'))]
            assert any(n and n in label for n in names) or key in (
                'open_action_add_devices', 'open_action_review_inactive',
                'open_action_add_apple_acct'), (key, label)


#----------------------------------------------------------------------------------------
#   Every row of every menu
#----------------------------------------------------------------------------------------
@pytest.mark.parametrize('scenario', ['one_acct', 'many', 'mobapp_only', 'needs_code'])
async def test_every_menu_row_opens_and_back_returns(scenario):
    '''Each row opens a screen; its back/cancel choice returns to the menu the row is on'''
    async with Session(scenario) as s:
        main = await main_menu(s)
        menus = {'menu': main.options()}
        for opt in main.options():
            if opt.startswith('menu_'):
                f = await s.flow()
                await f.menu(opt)
                menus[opt] = f.options()
                await f.close()
        problems = []
        for menu, options in menus.items():
            for opt in options:
                if opt == 'main_menu' or opt.startswith('menu_'):
                    continue
                f = await s.flow()
                if menu != 'menu':
                    await f.menu(menu)
                try:
                    await f.menu(opt)
                except FlowException as err:
                    problems.append((menu, opt, str(err)[:200]))
                    continue
                problems += [(menu, opt, e) for e in render_errors(f)]
                back = [a for a in (f.actions() if f.type == 'form' else [])
                        if a in ('back', 'cancel', 'cancel_goto_menu') or a.endswith('_back')]
                if back:
                    try:
                        await f.action(back[0])
                    except (FlowException, data_entry_flow.InvalidData) as err:
                        problems.append((menu, opt, f"back: {str(err)[:200]}"))
                        continue
                    if not (f.type == 'menu' and f.step == menu):
                        problems.append((menu, opt, f"back went to {f.type}:{f.step}, expected menu {menu}"))
                await f.close()
        assert problems == []


#----------------------------------------------------------------------------------------
#   Two windows, double clicks
#----------------------------------------------------------------------------------------
async def test_two_windows_do_not_share_menu_state():
    async with Session('one_acct') as s:
        a = await main_menu(s)
        b = await s.flow()
        await a.menu('open_device_list')
        if a.type != 'menu':
            pytest.skip(f"the device list is a {a.type}, not an HA menu")
        await b.menu('menu_tracking')
        await b.menu('open_tracking_parameters')
        a_rows = a.options() if a.type == 'menu' else a.actions()
        # Window B moving on must not change what window A shows / acts on
        dev_rows = [o for o in a_rows if 'device_0' in o or o.endswith('_0')]
        assert dev_rows, a_rows
        await a.menu(dev_rows[0])
        assert a.step == 'update_device'
        back_b = [x for x in b.actions() if 'cancel' in x or x == 'back']
        await b.action(back_b[0])
        assert b.type == 'menu' and b.step == 'menu_tracking', (b.type, b.step)
        assert 'Max iPhone' in json.dumps(a.result, ensure_ascii=False)
        back_a = [x for x in a.actions() if 'cancel' in x or x == 'back']
        await a.action(back_a[0])
        assert a.type == 'menu' and a.step == 'device_list', (a.type, a.step)
        await a.close()
        await b.close()
        assert settings_diff(s.config_at_start, s.config()) == []


async def test_double_click_menu_row():
    '''The second POST of the same menu row reaches the screen that was opened: HA rejects
    it (schema) and the window still works'''
    async with Session('one_acct') as s:
        f = await main_menu(s)
        await f.menu('open_device_list')
        step = f.step
        with pytest.raises((data_entry_flow.InvalidData, data_entry_flow.UnknownStep, FlowException, KeyError)):
            await f.raw({'next_step_id': 'open_device_list'})
        res = await f.manager.async_configure(f.flow_id, None) if f.type == 'form' else f.result
        assert res.get('type') in ('form', 'menu')
        assert f.step == step


#----------------------------------------------------------------------------------------
#   Sign-in screen (fake Apple)
#----------------------------------------------------------------------------------------
@pytest.mark.parametrize('scenario', ['needs_code', 'needs_code_text', 'terms'])
async def test_reauth_screen_code_paths(scenario, attention_rows):
    async with Session(scenario) as s:
        f = await main_menu(s)
        row = 'open_action_terms_of_use' if scenario == 'terms' else 'open_action_reauth'
        await f.menu(row)
        assert f.step == 'reauth'
        assert not render_errors(f), render_errors(f)
        code_field = next((n for n in f.field_names() if 'code' in n.split('.')[-1]), None)
        problems = []
        for code in ('', '12345', '123456', 'abcdef', ' 123 456 '):
            g = await s.flow()
            await g.menu(row)
            for action in g.actions():
                if action in ('back', 'cancel', 'cancel_goto_menu'):
                    continue
                h2 = await s.flow()
                await h2.menu(row)
                changes = {code_field.split('.')[-1]: code} if code_field else {}
                try:
                    await h2.action(action, **changes)
                    problems += [(code, action, e) for e in render_errors(h2)]
                except data_entry_flow.InvalidData:
                    pass
                except FlowException as err:
                    problems.append((code, action, str(err)[:240]))
                await h2.close()
            await g.close()
        assert problems == []
        assert h.NETWORK_ATTEMPTS == []
