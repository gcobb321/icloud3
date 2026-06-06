

from ...global_variables    import GlobalVariables as Gb
from ...const               import (RARROW, ICLOUD, MOBAPP,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                    CONF_DATA_SOURCE, CONF_AUTH_CODE,
                                    CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                    )

from ...utils.utils         import (instr, list_add, is_empty, isnot_empty,
                                    decode_password, dict_value_to_list, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ..const_form_lists     import *
from ...mobile_app          import mobapp_interface

from homeassistant.helpers  import (selector,
                                    entity_registry as er,
                                    device_registry as dr,)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ICLOUD3 APPLE ACCOUNT CONFIG FLOW FORMS
#
#           - form_data_source
#           - form_update_apple_acct
#           - form_delete_apple_acct
#           - form_other_apple_acct_parameters
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              DATA SOURCE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_data_source(self):
    lists.build_apple_accounts_list(self)

    self.actions_list = []
    self.actions_list.extend(APPLE_ACCOUNT_ACTIONS)
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    default_action = self.actions_list_default if self.actions_list_default else 'save'
    self.actions_list_default = ''

    mobile_app_used_default = [MOBILE_APP_USED_HEADER] if instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP) else []
    apple_acct_used_default = [APPLE_ACCT_USED_HEADER] if instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD) else []

    # Build list of all apple accts
    self.apple_acct_items_list= [apple_acct_item
                                    for apple_acct_username, apple_acct_item in self.apple_acct_items_by_username.items()
                                    if apple_acct_username != 'apple_acct_hdr']

    if len(self.apple_acct_items_list) <= 6:
        self.apple_acct_items_displayed = self.apple_acct_items_list
    else:
        _build_apple_accts_displayed_over_5(self)

    if Gb.internet_error is False:
        list_add(self.apple_acct_items_displayed, '➤ ADD A NEW APPLE ACCOUNT')

    default_key  = self.aa_page_item[self.aa_page_no]
    default_item = self.apple_acct_items_by_username.get(default_key)
    if default_item not in self.apple_acct_items_displayed:
        default_item = self.apple_acct_items_displayed[0]

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP):
        if is_empty(Gb.devicenames_x_mobapp_dnames):
            mobapp_interface.get_mobile_app_integration_device_info()

    return vol.Schema({
        vol.Optional('data_source_mobapp',
                    default=mobile_app_used_default):
                    cv.multi_select([MOBILE_APP_USED_HEADER]),
        vol.Optional('data_source_apple_acct',
                    default=apple_acct_used_default):
                    cv.multi_select([APPLE_ACCT_USED_HEADER]),
        vol.Optional('apple_accts',
                    default=default_item):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.apple_acct_items_displayed, mode='list')),
        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#................................................................................................
def _build_apple_accts_displayed_over_5(self):
    '''
    Build the display page and next page line for the Apple Accts list
    when more than 5 apple accounts
    '''
    # Build the list of apple accts to display on this page
    list_from_idx = self.aa_page_no * 5
    self.apple_acct_items_displayed = self.apple_acct_items_list[list_from_idx:list_from_idx+5]

    # Build the list of apple accts to display on the next page
    list_from_idx = list_from_idx + 5
    if list_from_idx >= len(self.apple_acct_items_list):
        list_from_idx = 0

    # Extract owners from the accts list (GaryCobb (username) -> 5 of 7 Tracked Devices))
    account_owners = [apple_acct_list_item.split(RARROW)[0]
                            for apple_acct_list_item in self.apple_acct_items_list]
    account_owners_next_page = (f"➤ OTHER APPLE ACCOUNTS{RARROW}"
                                f"{', '.join(account_owners[list_from_idx:list_from_idx+5])}")
    list_add(self.apple_acct_items_displayed, account_owners_next_page)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DATA SOURCE (APPLE) PARAMETERS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_other_apple_acct_parameters(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    return vol.Schema({
        vol.Required(CONF_SERVER_LOCATION_NEEDED,
                    default=Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED]):
                    # cv.boolean,
                    selector.BooleanSelector(),

        vol.Required('action_items',
                    default=utils_cf.default_action_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            APPLE USERNAME PASSWORD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_apple_acct(self):
    lists.build_apple_accounts_list(self)

    retry_login_AA = [AA    for AA in Gb.AppleAcct_error_by_username.values()
                            if AA.error_next_retry_secs > 0]
    if isnot_empty(retry_login_AA):
        self.actions_list = [ACTION_LIST_OPTIONS['stop_login_retry']]
    else:
        self.actions_list = []
    self.actions_list.extend(USERNAME_PASSWORD_ACTIONS)

    if Gb.internet_error:
        default_action = 'cancel_goto_previous'
    else:
        default_action = 'save_log_into_apple_acct'

    errs_ui = self.errors_user_input
    username   = errs_ui.get(CONF_USERNAME)   or self.conf_apple_acct[CONF_USERNAME] or ' '
    password   = errs_ui.get(CONF_PASSWORD)   or self.conf_apple_acct[CONF_PASSWORD] or ' '
    password   = decode_password(password)
    locate_all = errs_ui.get(CONF_LOCATE_ALL) or self.conf_apple_acct[CONF_LOCATE_ALL]

    if (password.strip() == ''
            or self.add_apple_acct_flag
            or Gb.valid_upw_by_username.get(username, False) is False):
        password_selector = selector.TextSelector()
    else:
        password_selector = selector.TextSelector(selector.TextSelectorConfig(type='password'))

    if Gb.internet_error:
            self.errors['base'] = 'internet_error_no_change'

    if username in self.apple_acct_items_by_username:
        apple_acct_info = self.apple_acct_items_by_username[username].lower()
        if CONF_USERNAME in self.errors:
            pass
        elif instr(apple_acct_info, 'invalid username/password'):
            self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
        elif instr(apple_acct_info, NOT_LOGGED_IN):
            self.errors[CONF_USERNAME] = 'apple_acct_not_logged_into'
        elif instr(apple_acct_info, 'authentication needed'):
            self.errors[CONF_AUTH_CODE] = 'auth_code_needed'
        elif instr(apple_acct_info, 'terms of use'):
            self.errors[CONF_USERNAME] = 'apple_acct_terms_of_use_update_needed'
        self.errors.pop('account_selected', None)
        self.header_msg = ''

    if self.add_apple_acct_flag or username.strip() == '':
        acct_info = '➤ ADD A NEW APPLE ACCOUNT'
    elif username not in self.apple_acct_items_by_username:
        acct_info = self.apple_acct_items_by_username[username] = f"Setting up {username}"
    else:
        _, _, untracked_cnt, untracked_devices = lists.tracked_untracked_form_msg(username)
        acct_info =(f"{self.apple_acct_items_by_username[username]}, "
                    f"Untracked-({untracked_devices})")

    schema = ({
        vol.Optional('account_selected',
                    default=acct_info):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[acct_info], mode='list')),
        vol.Optional(CONF_USERNAME,
                    default=username):
                    selector.TextSelector(),
        vol.Optional(CONF_PASSWORD ,
                    default=password):
                    password_selector,
        })

    if Gb.country_code in ['cn', 'hk'] or Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED]:
        schema.update({
            vol.Optional(CONF_SERVER_LOCATION,
                    default=utils_cf.option_parm_to_text(self, CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(APPLE_SERVER_LOCATION_OPTIONS), mode='dropdown')),
        })

    schema.update({
        vol.Optional('locate_all',
                    default=locate_all):
                    cv.boolean,
        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DELETE APPLE ACCOUNT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_delete_apple_acct(self):
    self.actions_list = APPLE_ACCOUNT_DELETE_ACTIONS.copy()

    username = self.conf_apple_acct[CONF_USERNAME]
    apple_acct_info = self.apple_acct_items_by_username[username]
    if (instr(apple_acct_info, '0 of')
            or instr(apple_acct_info, '1 of 1')
            or instr(apple_acct_info, 'Tracked-()')
            or instr(apple_acct_info, NOT_LOGGED_IN)):
        default_device_action = 'delete_devices'
    else:
        default_device_action = 'reassign_devices'
    _, _, untracked_cnt, untracked_devices = lists.tracked_untracked_form_msg(username)
    acct_info = f"{apple_acct_info}, Untracked-({untracked_devices})"

    return vol.Schema({
        vol.Optional('account_selected',
                    default=acct_info):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[acct_info], mode='list')),
        vol.Required('device_action',
                    default=DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS[default_device_action]):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=dict_value_to_list(DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS),
                            mode='list')),
        vol.Required('action_items',
                    default=utils_cf.default_action_text('cancel_goto_previous')):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })
