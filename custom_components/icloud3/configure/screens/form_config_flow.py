

from ...global_variables    import GlobalVariables as Gb
from ...const               import (DEVICE_TYPES_TRACK_MONITOR, MONITOR, TRACK, INACTIVE, )
from ...const_config        import (CONF_AADEV_NAME, CONF_APPLE_ACCT, CONF_DEVICE_TYPE, CONF_FNAME, CONF_MOBILE_APP_DEVICE, CONF_VERSION, CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, )

from ...utils.utils         import (apple_user, list_to_str, list_add, list_del, isnot_empty,
                                    dict_value_to_list, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ...startup             import config_file
from ..                     import utils_cf
from ..const_form_lists     import *

from homeassistant.helpers  import (selector,
                                    entity_registry as er,
                                    device_registry as dr,)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from .                      import form_apple_acct
from ...apple_acct          import apple_acct_support_cf as aascf

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     GENERAL CONFIG FLOW FORMS
#
#       - form_config_option_user
#       - form_menu
#       - form_confirm_action
#       - exit_icloud3_configure
#       - form_restart_ha
#       - form_restart_ha_reload_icloud3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             USER - INITIAL ADD INTEGRATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_config_option_user(self):


    if (Gb.conf_profile[CONF_VERSION] >=1
            and (isnot_empty(Gb.conf_apple_accounts)
                or isnot_empty(Gb.conf_devices))):
        schema = {
            vol.Required('reset_tracking', default=False): bool,
            # vol.Required('reset_general', default=False): bool,
        }
    else:
        schema = {}

    schema.update({
        vol.Required('continue', default=True): bool
    })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def menu_options(self, menu_id):
    '''
    Build the menu options for the menu_id menu. The main menu starts with the Action
    Needed items for the current configuration.
    '''
    if menu_id != MAIN_MENU:
        return MENU_TREE[menu_id].copy()

    return [f"open_{action_item}" for action_item in self.needs_attention] + MENU_TREE[MAIN_MENU]

#...............................................................................
def build_needs_attention(self):
    '''
    The Needs attention rows at the top of the main menu. Each one opens the screen that
    fixes it (async_step_open_action_xxx --> open_menu_item).

    Sets:
        self.needs_attention - The action items
        self.needs_attention_placeholders - The names in the row labels
        self.needs_attention_terms_apple_id, self.needs_attention_reauth_apple_id,
                self.needs_attention_devicename - The Apple Accounts and device the
                action_terms_of_use, action_reauth and action_no_data_source rows open
    '''
    action_items = []
    placeholders = {}
    device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()
    # Inactive devices that can't be tracked (AirPods, iPods) are not on the Review
    # inactive devices screen
    review_inactive_cnt = len([conf_device  for conf_device in Gb.conf_devices
                                            if (conf_device[CONF_TRACKING_MODE] == INACTIVE
                                                and conf_device[CONF_DEVICE_TYPE] in DEVICE_TYPES_TRACK_MONITOR)])
    self.needs_attention_terms_apple_id  = ''
    self.needs_attention_reauth_apple_id = ''
    self.needs_attention_devicename      = ''

    if Gb.conf_data_source_ICLOUD:
        terms_AppleAcct = next((AppleAcct for AppleAcct in Gb.AppleAcct_by_apple_id.values()
                                    if AppleAcct.terms_of_use_update_needed), None)
        reauth_apple_id = aascf.reauth_needed_apple_id()
        # An account needing both is opened by the Terms of Use row, its screen also
        # requests the code
        if terms_AppleAcct:
            action_items.append('action_terms_of_use')
            placeholders['terms_acct'] = terms_AppleAcct.account_owner
            self.needs_attention_terms_apple_id = terms_AppleAcct.apple_id
        if reauth_apple_id and reauth_apple_id != self.needs_attention_terms_apple_id:
            action_items.append('action_reauth')
            placeholders['reauth_acct'] = Gb.AppleAcct_by_apple_id[reauth_apple_id].account_owner \
                                            if reauth_apple_id in Gb.AppleAcct_by_apple_id else reauth_apple_id
            self.needs_attention_reauth_apple_id = reauth_apple_id

    if Gb.conf_data_source_ICLOUD and (self.apple_id == '' or self.password == ''):
        action_items.append('action_add_apple_acct')

    else:
        login_failed_apple_ids = aascf.login_failed_apple_ids() if Gb.conf_data_source_ICLOUD else []
        if login_failed_apple_ids:
            action_items.append('action_login_failed')
            placeholders['login_failed_acct'] = apple_user(login_failed_apple_ids[0])
            placeholders['login_failed_status'] = form_apple_acct.apple_acct_status(login_failed_apple_ids[0])

        no_data_source_devices = [conf_device   for conf_device in Gb.conf_devices
                                                if (conf_device[CONF_TRACKING_MODE] != INACTIVE
                                                    and conf_device.get(CONF_AADEV_NAME, '') in ['', 'None']
                                                    and conf_device.get(CONF_MOBILE_APP_DEVICE, '') in ['', 'None'])]
        if no_data_source_devices:
            action_items.append('action_no_data_source')
            placeholders['no_source_device'] = no_data_source_devices[0][CONF_FNAME]
            self.needs_attention_devicename  = no_data_source_devices[0][CONF_IC3_DEVICENAME]

        if device_cnt == 0:
            action_items.append('action_add_devices')
        elif review_inactive_cnt == 0:
            pass
        elif device_cnt == inactive_device_cnt:
            action_items.append('action_review_inactive')
        else:
            action_items.append('action_review_inactive_some')
            placeholders['inactive_cnt'] = review_inactive_cnt

    if Gb.analytics_enabled is None:
        action_items.append('action_analytics')

    self.needs_attention = action_items
    self.needs_attention_placeholders = placeholders

    return action_items

#...............................................................................
def menu_status_line(self):
    '''
    The configuration summary at the top of the main menu:
        2 Apple Accounts · 5 devices tracked · 1 monitored · 1 needs attention
    '''
    def _cnt_text(key, cnt):
        return utils_cf.tr(f"{key}_{'one' if cnt == 1 else 'other'}", cnt=cnt)

    tracked_cnt   = len([conf_device  for conf_device in Gb.conf_devices
                                      if conf_device[CONF_TRACKING_MODE] == TRACK])
    monitored_cnt = len([conf_device  for conf_device in Gb.conf_devices
                                      if conf_device[CONF_TRACKING_MODE] == MONITOR])
    status_items = []
    if Gb.conf_data_source_ICLOUD:
        status_items.append(_cnt_text('status_apple_accts', len([conf_apple_acct
                                    for conf_apple_acct in Gb.conf_apple_accounts
                                    if conf_apple_acct[CONF_APPLE_ACCT] != ''])))
    status_items.append(_cnt_text('status_tracked', tracked_cnt))
    if monitored_cnt > 0:
        status_items.append(_cnt_text('status_monitored', monitored_cnt))
    # The analytics opt-in row is a question, not a problem
    needs_attention_cnt = len([action_item  for action_item in self.needs_attention
                                            if action_item != 'action_analytics'])
    if needs_attention_cnt:
        status_items.append(_cnt_text('status_needs_attention', needs_attention_cnt))

    return ' · '.join(status_items)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             MENU
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_confirm_action(self, action_items=None):
    '''
    confirm_action form uses information in the self.confirm_action{}
    '''

    try:
        if action_items is None:
            actions_list = CONFIRM_ACTIONS.copy()
            actions_list_default = len(actions_list) - 1    # LAST ITEM
        else:
            actions_list = action_items
            actions_list_default = self.confirm_action.get('action_items_default') or 0

        action_desc = self.confirm_action.get('action_desc') or \
                    'Do you want to perform the selected action?'

        return vol.Schema({
            vol.Required('action_desc',
                    default=action_desc):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[action_desc], mode='list')),
            vol.Required('action_items',
                    default=actions_list[actions_list_default]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=actions_list, mode='list')),
            })
    except Exception as err:
        log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             EXIT ICLOUD3 CONFIGURE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def form_exit_icloud3_configure_settings(self):
#     self.actions_list = EXIT_ICLOUD3_CONFIGURE_SETTINGS.copy()

#     device_cnt, inactive_device_cnt, inactive_pct = config_file.device_cnts()
#     if inactive_device_cnt == 0:
#         self.actions_list['review_inactive_devices'].pop()
#     else:
#         inactive_devices = [conf_device[CONF_IC3_DEVICENAME]
#                     for conf_device in Gb.conf_devices
#                     if conf_device[CONF_TRACKING_MODE] == INACTIVE]

#         # self.actions_list['review_inactive_devices'].replace(
#         self.actions_list[0] = \
#             self.actions_list[0].replace(
#                     '^add-text^', list_to_str(inactive_devices))

#     return vol.Schema({
#         vol.Required('action_items',
#                     default=utils_cf.default_action_text('exit')):
#                     selector.SelectSelector(selector.SelectSelectorConfig(
#                         options=self.actions_list, mode='list')),
#         })
