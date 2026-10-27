

from ...global_variables    import GlobalVariables as Gb
from ...const               import (ICLOUD, MOBAPP,  AUTH_CODE, )
from ...const_config        import (CONF_AUTH_METHODS, CURRENT, PUSH, HWKEY, )

from ...utils.utils         import (dict_value_to_list, list_del, dict_del, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ..const_form_lists     import *
from ...apple_acct          import apple_acct_support_cf as aascf

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers.selector import (TextSelector, TextSelectorConfig,)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     ICLOUD3 REAUTH FORMS
#
#        - form_reauth
#        - form_reauth_code_from_applecom_login
#        - form_reauth_change_auth_method
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth(self, user_input=None, reauth_apple_id=''):
    lists.build_apple_accounts_auth_list(self)

    terms_of_use_update_needed = False
    is_reauth_needed           = False
    was_auth_code_requested    = False

    # Display the requested acct, otherwise the first one needing authentication
    if reauth_apple_id not in Gb.AppleAcct_by_apple_id:
        reauth_apple_id = None
    AppleAcct, reauth_apple_id = self.get_AppleAcct_reauth_needed(reauth_apple_id)

    is_reauth_needed           = AppleAcct.is_reauth_needed or self.is_another_auth_code_needed()
    was_auth_code_requested    = AppleAcct.was_auth_code_requested
    terms_of_use_update_needed = AppleAcct.terms_of_use_update_needed


    self.actions_list = []

    if terms_of_use_update_needed:
        self.actions_list.append(ACTION_LIST_OPTIONS['accept_terms_of_use'])
        self.errors['base'] = 'apple_acct_terms_of_use_update_needed'
    self.actions_list.extend(REAUTH_ACTIONS)

    if self.menu_item =='config_flow_reauth':
        self.actions_list.append(ACTION_LIST_OPTIONS['exit_ha_reconfigure_reauth'])
        default_action = 'exit_ha_reconfigure_reauth'

    elif self.menu_item == 'apple_accounts':
        self.actions_list.append(ACTION_LIST_OPTIONS['rtn_apple_accounts'])
        default_action = 'rtn_apple_accounts'

    else:
        self.actions_list.append(ACTION_LIST_OPTIONS['menu'])
        default_action = 'menu'

    if terms_of_use_update_needed:
        default_action = 'accept_terms_of_use'
    elif (Gb.internet_error
            or AppleAcct is None
            or is_reauth_needed is False):
        pass
    elif was_auth_code_requested:
        default_action = 'send_auth_code'
        AppleAcct.was_auth_code_requested = False
    elif is_reauth_needed or was_auth_code_requested is False:
        default_action = 'request_auth_code'

    default_acct_selected = self.apple_acct_auth_items_by_apple_id[reauth_apple_id]


    default_auth_code = user_input.get(AUTH_CODE, '') if user_input else ''
    if default_auth_code == '': default_auth_code = ' '

    schema = ({
        vol.Optional('account_selected',
                    default=default_acct_selected):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.apple_acct_auth_items_by_apple_id),
                        mode='dropdown')),
            vol.Optional(AUTH_CODE, default=default_auth_code):
                    selector.TextSelector(),
    })

    if terms_of_use_update_needed:
        schema.update({
            vol.Optional('terms_of_use',
                default=True):
                cv.boolean,
        })

    schema.update({
        vol.Optional('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH CODE BY SIGNING INTO APPLE.COM
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth_code_from_applecom_login(self):
    '''
    Get an auth code by signing into your apple account. Then enter it and send to
    Apple
    '''
    self.actions_list = REAUTH_CODE_FROM_APPLECOM_LOGIN.copy()
    default_action = 'send_auth_code'

    return vol.Schema({
        vol.Optional(AUTH_CODE, default=' '):
                    selector.TextSelector(),

        vol.Required('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
    })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH CHANGE AUTH METHOD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth_change_auth_method(self, account_selected=None):
    self.actions_list = CHANGE_AUTH_METHOD.copy()
    default_action = 'save'

    lists.build_aa_auth_methods_list(self, self.AppleAcct)

    default_acct_selected = self.apple_acct_auth_items_by_apple_id[account_selected]

    default_auth_method = self.AppleAcct.current_auth_method
    if self.aa_auth_methods_by_auth_method.get(HWKEY):
        default_auth_method = HWKEY
        dict_del(self.aa_auth_methods_by_auth_method, PUSH)

    if default_auth_method not in self.aa_auth_methods_by_auth_method:
        default_auth_method = 'push'

    schema = ({
        vol.Optional('account_selected',
                    default=default_acct_selected):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[default_acct_selected],
                        mode='list')),
        vol.Optional('auth_method',
                    default=self.aa_auth_methods_by_auth_method[default_auth_method]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.aa_auth_methods_by_auth_method),
                        mode='list')),
        vol.Optional('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })
                        # options=dict_value_to_list(self.apple_acct_auth_items_by_apple_id),


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER AUTHENTICATION DASHBOARD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_user_auth_dashboard(self, user_input=None):
    self.actions_list = USER_AUTH_DASHBOARD.copy()
    default_action = 'refresh'

    # lists.build_aa_auth_methods_list(self, self.AppleAcct)
    include_acct_items = {}
    if len(self.apple_acct_auth_items_by_apple_id) > 1:
        include_acct_items['all_accts'] = "All Apple Accounts should be on the same Dashboard Card"
    include_acct_items.update(self.apple_acct_auth_items_by_apple_id)

    if user_input is None: user_input = {}
    include_acct = user_input.get('include_acct')
    display_mode = user_input.get('display_mode')
    raw_yaml_code = user_input.get('raw_yaml_code', ' ')

    # 'all_accts' is not in the list when there is only one Apple Acct
    if include_acct not in include_acct_items:
        include_acct = list(include_acct_items.keys())[0]
    default_include_acct = include_acct_items[include_acct]
    display_mode = display_mode or 'always'

    schema = ({
        vol.Optional('include_acct',
                    default=default_include_acct):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(include_acct_items),
                        mode='dropdown')),
        vol.Optional('display_mode',
                    default=USER_AUTH_RAW_YAML_DISPLAY_MODE[display_mode]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(USER_AUTH_RAW_YAML_DISPLAY_MODE), mode='dropdown')),
        vol.Optional('raw_yaml_code',
                    selector.TextSelector(),
                        description={"suggested_value": raw_yaml_code}):
                            selector.TextSelector(selector.TextSelectorConfig(multiline=True)),

        vol.Optional('action_items',
                    default=utils_cf.default_action_text(default_action)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)
