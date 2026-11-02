

from ...global_variables    import GlobalVariables as Gb
from ...const               import (ICLOUD, MOBAPP,  AUTH_CODE, )
from ...const_config        import (CONF_AUTH_METHODS, CURRENT, PUSH, HWKEY, )

from ...utils.utils         import (list_del, dict_del, apple_user, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ..const_form_lists     import *
from ...apple_acct          import apple_acct_support_cf as aascf

from homeassistant.helpers  import selector
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#     ICLOUD3 REAUTH FORMS
#
#        - is_reauth_form_needed
#        - reauth_heading
#        - form_reauth
#        - reauth_options_menu_options
#        - form_reauth_code_from_applecom_login
#        - form_reauth_change_auth_method
#        - form_user_auth_dashboard
#
#   The authentication screen of an Apple Account is the reauth form while Apple is
#   waiting for a code or its Terms of Use need accepting, otherwise it is the
#   Authentication options menu (reauth_options).
#
#   The Action field (FORM_ACTION) values are the action items handled by the
#   step_reauth steps, the labels are the selector.cf_text reauth_[action] texts.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def is_reauth_form_needed(AppleAcct):
    '''
    True when the Apple Account needs the reauth form: Apple is waiting for a code or
    the Terms of Use need accepting
    '''
    return (AppleAcct is not None
            and (AppleAcct.is_reauth_needed or AppleAcct.terms_of_use_update_needed))

def _auth_method_key(AppleAcct):
    if AppleAcct.is_auth_method_HWKEY:
        return 'hwkey'
    if AppleAcct.is_auth_method_TEXT:
        return 'text'
    return 'push'

#................................................................................................
def reauth_heading(self, AppleAcct):
    '''
    The Apple Account, its authentication status and one information line displayed at
    the top of the authentication screens

    Return:
        description placeholders {acct_name, acct_status, acct_info}
    '''
    if AppleAcct is None:
        return {'acct_name': '', 'acct_status': '', 'acct_info': ''}

    method_key  = _auth_method_key(AppleAcct)
    method_info = AppleAcct.current_auth_method_value

    if AppleAcct.is_reauth_needed:
        acct_status = utils_cf.tr(f"reauth_status_waiting{'_hwkey' if method_key == 'hwkey' else ''}")
        acct_info   = utils_cf.tr(f"reauth_enter_{method_key}", method_info=method_info)
    elif AppleAcct.terms_of_use_update_needed:
        acct_status = utils_cf.tr('reauth_status_terms')
        acct_info   = utils_cf.tr('reauth_info_terms')
    elif aascf.is_apple_acct_logged_into(AppleAcct.apple_id):
        acct_status = utils_cf.tr('reauth_status_signed_in')
        acct_info   = utils_cf.tr(f"reauth_method_{method_key}", method_info=method_info)
    else:
        acct_status = utils_cf.tr('aa_status_not_logged_in')
        acct_info   = ''

    return {'acct_name': apple_user(AppleAcct.apple_id),
            'acct_status': acct_status,
            'acct_info': acct_info}

#................................................................................................
def form_reauth(self, AppleAcct):
    '''
    The code entry form of an Apple Account Apple is waiting for a code for or whose
    Terms of Use need accepting. A security key has no code field, it is touched after
    the authentication is selected.
    '''
    is_waiting = AppleAcct.is_reauth_needed
    is_hwkey   = AppleAcct.is_auth_method_HWKEY
    terms_of_use_update_needed = AppleAcct.terms_of_use_update_needed

    schema = {}
    if is_waiting and is_hwkey is False:
        schema[vol.Optional(AUTH_CODE, default=' ')] = selector.TextSelector()
    if terms_of_use_update_needed:
        schema[vol.Optional('terms_of_use', default=True)] = cv.boolean

    actions = {}
    if terms_of_use_update_needed:
        actions['accept_terms_of_use'] = utils_cf.tr('reauth_accept_terms_of_use')
    if is_waiting:
        if is_hwkey:
            actions['send_auth_code']    = utils_cf.tr('reauth_send_hwkey')
            actions['request_auth_code'] = utils_cf.tr('reauth_request_hwkey')
        else:
            actions['send_auth_code']    = utils_cf.tr('reauth_send_auth_code')
            actions['request_auth_code'] = utils_cf.tr('reauth_request_auth_code')
            actions['auth_code_from_applecom_login'] = utils_cf.tr('reauth_auth_code_from_applecom_login')
        actions['change_auth_method'] = utils_cf.tr('reauth_change_auth_method')

    back_action, back_label = reauth_back_action(self)
    actions[back_action] = back_label

    # Send is preselected after a code was requested, otherwise Request. Entering a code
    # sends it whichever is selected.
    if terms_of_use_update_needed:
        default_action = 'accept_terms_of_use'
    elif Gb.internet_error or is_waiting is False:
        default_action = back_action
    elif AppleAcct.was_auth_code_requested:
        default_action = 'send_auth_code'
        AppleAcct.was_auth_code_requested = False
    else:
        default_action = 'request_auth_code'

    schema.update(utils_cf.form_action_field(self, actions, default_action))

    return vol.Schema(schema)

#................................................................................................
def reauth_options_menu_options(self, AppleAcct):
    '''
    The Authentication options menu of a signed in Apple Account

    Return:
        {option: label}, label=None uses the strings.json label
        placeholders for the strings.json labels and descriptions
    '''
    menu_options = {}
    placeholders = {'auth_method': '', 'request_info': ''}

    if AppleAcct is not None:
        lists.build_aa_auth_methods_list(self, AppleAcct)
        placeholders['auth_method'] = self.aa_auth_methods_by_auth_method.get(
                                            AppleAcct.current_auth_method,
                                            self.aa_auth_methods_by_auth_method[PUSH])

        if (aascf.is_apple_acct_logged_into(AppleAcct.apple_id)
                and Gb.internet_error is False):
            if AppleAcct.is_auth_method_HWKEY:
                menu_options['reauth_options_request_code'] = utils_cf.tr('reauth_request_hwkey')
                placeholders['request_info'] = utils_cf.tr('reauth_request_info_hwkey')
            else:
                menu_options['reauth_options_request_code'] = None
                placeholders['request_info'] = utils_cf.tr('reauth_request_info')
        menu_options['reauth_change_auth_method'] = None
        menu_options['user_auth_dashboard'] = None

    menu_options['reauth_options_back'] = reauth_back_action(self)[1]

    return menu_options, placeholders

#................................................................................................
def reauth_back_action(self):
    '''
    The action and label that leave the authentication screen for the screen it was
    opened from
    '''
    if self.menu_item == 'config_flow_reauth':
        return 'exit_ha_reconfigure_reauth', utils_cf.tr('reauth_close')
    if getattr(self, 'is_repair_flow', False):
        return 'rtn_apple_accounts', utils_cf.tr('reauth_back_repair')
    if self.menu_item == 'apple_accounts':
        return 'rtn_update_apple_acct', utils_cf.tr('back', dest=utils_cf.destination_name('the_apple_acct'))
    return 'menu', utils_cf.tr('back', dest=utils_cf.destination_name('menu'))

def reauth_destination(self):
    '''
    The dest_[key] text key of the authentication screen the Change method, apple.com
    and Dashboard card screens return to
    '''
    return 'reauth' if is_reauth_form_needed(self.AppleAcct) else 'reauth_options'


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH CODE BY SIGNING INTO APPLE.COM
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth_code_from_applecom_login(self):
    '''
    Get an auth code by signing into your apple account. Then enter it and send to
    Apple
    '''
    return vol.Schema({
        vol.Optional(AUTH_CODE, default=' '):
                    selector.TextSelector(),

        **utils_cf.form_action_field(self, {
                    'send_auth_code': utils_cf.tr('reauth_send_auth_code'),
                    'goto_previous':  _back_to_reauth_label(self)},
                    'send_auth_code'),
    })

def _back_to_reauth_label(self):
    return utils_cf.tr('back', dest=utils_cf.destination_name(reauth_destination(self)))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH CHANGE AUTH METHOD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth_change_auth_method(self):
    lists.build_aa_auth_methods_list(self, self.AppleAcct)

    default_auth_method = self.AppleAcct.current_auth_method
    if self.aa_auth_methods_by_auth_method.get(HWKEY):
        default_auth_method = HWKEY
        dict_del(self.aa_auth_methods_by_auth_method, PUSH)

    if default_auth_method not in self.aa_auth_methods_by_auth_method:
        default_auth_method = 'push'

    return vol.Schema({
        vol.Optional('auth_method',
                    default=default_auth_method):
                    utils_cf.select(self.aa_auth_methods_by_auth_method, mode='list'),

        **utils_cf.form_action_field(self, {
                    'save':                utils_cf.tr('reauth_save_auth_method',
                                                dest=utils_cf.destination_name(reauth_destination(self))),
                    'refresh_hwkey_names': utils_cf.tr('reauth_refresh_hwkey_names'),
                    'goto_previous':       _back_to_reauth_label(self)},
                    'save'),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            USER AUTHENTICATION DASHBOARD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_user_auth_dashboard(self, user_input=None):
    if user_input is None: user_input = {}
    display_mode = user_input.get('display_mode') or 'always'
    raw_yaml_code = user_input.get('raw_yaml_code', ' ')

    # The Apple Account selection is only displayed when there is more than one
    schema = {}
    if len(self.apple_acct_auth_items_by_apple_id) > 1:
        include_acct_items = {'all_accts': utils_cf.tr('user_auth_all_accts'),
                                **self.apple_acct_auth_items_by_apple_id}
        include_acct = user_input.get('include_acct')
        if include_acct not in include_acct_items:
            include_acct = 'all_accts'
        schema[vol.Optional('include_acct', default=include_acct)] = \
                    utils_cf.select(include_acct_items)

    schema.update({
        vol.Optional('display_mode',
                    default=display_mode):
                    utils_cf.select(USER_AUTH_RAW_YAML_DISPLAY_MODES,
                                translation_key='user_auth_display_mode'),
        vol.Optional('raw_yaml_code',
                        description={"suggested_value": raw_yaml_code}):
                            selector.TextSelector(selector.TextSelectorConfig(multiline=True)),

        **utils_cf.form_action_field(self, {
                    'refresh':       utils_cf.tr('reauth_refresh_card'),
                    'goto_previous': _back_to_reauth_label(self)},
                    'refresh'),
        })

    return vol.Schema(schema)
