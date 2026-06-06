

from ...global_variables    import GlobalVariables as Gb
from ...const               import (CONF_AUTH_CODE, )

from ...utils.utils         import (dict_value_to_list, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ..const_form_lists     import *

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


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
def form_reauth(self, user_input=None, reauth_username=None):
    lists.build_apple_accounts_auth_list(self)

    terms_of_use_update_needed = False
    is_auth_code_needed        = False
    was_auth_code_requested    = False

    AppleAcct, reauth_username = self.get_username_needing_reauth(reauth_username)

    # is_auth_code_needed        = AppleAcct.is_auth_code_needed or AppleAcct.is_challenge_required
    is_auth_code_needed        = AppleAcct.is_auth_code_needed or self.is_another_auth_code_needed()
    was_auth_code_requested    = AppleAcct.was_auth_code_requested
    terms_of_use_update_needed = AppleAcct.terms_of_use_update_needed

    self.actions_list = []
    if terms_of_use_update_needed:
        self.actions_list.append(ACTION_LIST_OPTIONS['accept_terms_of_use'])
    self.actions_list.extend(REAUTH_ACTIONS)

    if self.is_config_flow_handler:
        self.actions_list.append(ACTION_LIST_OPTIONS['goto_ha_auth_done'])
    else:
        self.actions_list.append(ACTION_LIST_OPTIONS['goto_previous'])

    if (Gb.internet_error
            or AppleAcct is None
            or is_auth_code_needed is False):
        default_action = ''
    elif terms_of_use_update_needed:
        default_action = 'accept_terms_of_use'

    elif was_auth_code_requested is False:
        default_action = 'request_auth_code'
    elif is_auth_code_needed or was_auth_code_requested:
        default_action = 'send_auth_code'
    else:
        default_action = ''

    if default_action == '':
        default_action = 'goto_ha_auth_done' if self.is_config_flow_handler else 'goto_previous'

    default_acct_selected = self.apple_acct_auth_items_by_username[reauth_username]

    schema = ({
        vol.Optional('account_selected',
                    default=default_acct_selected):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.apple_acct_auth_items_by_username),
                        mode='dropdown')),
            vol.Optional(CONF_AUTH_CODE, default=' '):
                    selector.TextSelector(),
    })

    # if Gb.fido2_security_keys_enabled:
    #     schema.update({
    #         vol.Required('fido2_key_name',
    #                 default=self.reauth_form_fido2_key_names_list[0]):
    #                 selector.SelectSelector(selector.SelectSelectorConfig(
    #                     options=self.reauth_form_fido2_key_names_list, mode='dropdown')),
    #     })

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
        vol.Optional(CONF_AUTH_CODE, default=' '):
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

    default_acct_selected = self.apple_acct_auth_items_by_username[account_selected]

    default_auth_method = self.AppleAcct.auth_method
    if default_auth_method not in self.aa_auth_methods_by_auth_method:
        default_auth_method = 'push'

    schema = ({
        vol.Optional('account_selected',
                    default=default_acct_selected):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[default_acct_selected],
                        mode='dropdown')),
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

    return vol.Schema(schema)
