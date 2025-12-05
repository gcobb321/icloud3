
from homeassistant.helpers          import (selector, entity_registry as er, device_registry as dr,)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol

from ..global_variables import GlobalVariables as Gb
from ..const            import (RED_ALERT, LINK, RLINK, RARROW,
                                IPHONE, IPAD, WATCH, AIRPODS, ICLOUD, OTHER, HOME, NONE,
                                DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES, MOBAPP, NO_MOBAPP,
                                INACTIVE_DEVICE, HOME_DISTANCE,
                                PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                CONF_VERSION,
                                CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_BTNCONFIG_URL,
                                CONF_APPLE_ACCOUNT, CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL, CONF_TOTP_KEY,
                                CONF_DATA_SOURCE, CONF_VERIFICATION_CODE,
                                CONF_SERVER_LOCATION, CONF_SERVER_LOCATION_NEEDED,
                                CONF_TRACK_FROM_ZONES, CONF_LOG_ZONES,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_PICTURE, CONF_ICON, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL, CONF_MOBAPP_ALIVE_INTERVAL,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD, CONF_OLD_LOCATION_ADJUSTMENT,
                                CONF_TRAVEL_TIME_FACTOR, CONF_TFZ_TRACKING_MAX_DISTANCE,
                                CONF_PASSTHRU_ZONE_TIME, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                CONF_DISCARD_POOR_GPS_INZONE, CONF_PASSWORD_SRP_ENABLED,
                                CONF_DISTANCE_BETWEEN_DEVICES,
                                CONF_WAZE_USED, CONF_WAZE_SERVER, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_SENSORS_MONITORED_DEVICES,
                                CONF_SENSORS_DEVICE,
                                CONF_SENSORS_TRACKING_UPDATE, CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                CONF_SENSORS_TRACKING_OTHER, CONF_SENSORS_ZONE,
                                CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS,
                                CF_PROFILE,
                                )

from ..utils.utils      import (instr, isbetween, list_to_str, list_add, list_del, is_empty, isnot_empty,
                                zone_dname, decode_password, dict_value_to_list,
                                six_item_list, six_item_dict, )
from ..utils.messaging  import (log_exception, log_debug_msg, log_info_msg,
                                _log, _evlog,
                                post_event, post_alert, post_monitor_msg, )
from ..utils.time_util  import (format_timer, )

from .                  import utils_configure as utils
from .                  import selection_lists as lists
from .const_form_lists  import *
from ..configure        import dashboard_builder as dbb
from ..mobile_app       import mobapp_interface
from ..startup          import config_file

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
def form_menu(self):
    menu_title = MENU_PAGE_TITLE[self.menu_page_no]
    menu_action_items = MENU_ACTION_ITEMS.copy()
    if self.rebuild_ic3db_dashboards:
        dbb.load_ic3db_dashboards_from_ha_data(self)

        if isnot_empty(self.ic3db_Dashboards_by_dbname):
            list_del(menu_action_items, MENU_KEY_TEXT['exit'])
            list_add(menu_action_items, MENU_KEY_TEXT['exit_update_dashboards'])

    if self.menu_page_no == 0:
        menu_key_text  = MENU_KEY_TEXT_PAGE_0
        menu_action_items[1] = MENU_KEY_TEXT['next_page_1']

        if (self.username == '' or self.password == ''):
            self.menu_item_selected[0] = MENU_KEY_TEXT['data_source']
        elif (self.username and self.password
                and (self._device_cnt() == 0 or self._device_cnt() == self._inactive_device_cnt())):
            self.menu_item_selected[0] = MENU_KEY_TEXT['device_list']
    else:
        menu_key_text  = MENU_KEY_TEXT_PAGE_1
        menu_action_items[1] = MENU_KEY_TEXT['next_page_0']

    return vol.Schema({
        vol.Required("menu_items",
                    default=self.menu_item_selected[self.menu_page_no]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=menu_key_text, mode='list')),
        vol.Required("action_items",
                    default=menu_action_items[0]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=menu_action_items, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#             CONFIRM ACTION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_confirm_action(self, action_desc=None):
    '''
    confirm_action form uses information in the self.confirm_action{}
    '''

    actions_list = CONFIRM_ACTIONS.copy()
    actions_list_default = 'confirm_return_no'
    action_desc = action_desc if action_desc is not None else\
                    'Do you want to perform the selected action?'

    return vol.Schema({
        vol.Required('action_desc',
                    default=action_desc):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[action_desc], mode='list')),
        vol.Required('action_items',
                    default=utils.action_default_text(actions_list_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=actions_list, mode='list')),
        })

#------------------------------------------------------------------------
def form_restart_icloud3(self):
    self.actions_list = []
    restart_default='restart_ic3_now'

    if 'restart_ha' in self.config_parms_update_control:
        restart_default='restart_ha'
        self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    else:
        restart_default='restart_ic3_now'
        self.actions_list.append(ACTION_LIST_OPTIONS['restart_ic3_now'])

    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ic3_later'])

    actions_list_default = utils.action_default_text(restart_default)
    if self._inactive_device_cnt() > 0:
        inactive_devices = [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]
        inactive_devices_list = \
            ACTION_LIST_OPTIONS['review_inactive_devices'].replace(
                    '^add-text^', list_to_str(inactive_devices))
        self.actions_list.append(inactive_devices_list)
        # if self._set_inactive_devices_header_msg() in ['all', 'most']:
        #     actions_list_default = inactive_devices_list

    self.actions_list.append(ACTION_LIST_OPTIONS['goto_menu'])

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              REVIEW INACTIVE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_review_inactive_devices(self, start_cnt=None):

    self.actions_list = []
    start_cnt = 0 if start_cnt is None else start_cnt
    self.inactive_devices_key_text = {}
    inactive_device_list = [conf_device[CONF_IC3_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

    cnt = 0
    inactive_device_cnt = len(inactive_device_list)
    for conf_device in Gb.conf_devices[start_cnt:start_cnt+5]:
        if conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE:
            continue
        cnt += 1

        self.inactive_devices_key_text.update({
                conf_device[CONF_IC3_DEVICENAME]: self._format_device_list_item(conf_device)})

    if inactive_device_cnt > start_cnt + 5 and start_cnt == 0:
        next_4_devicenames = list_to_str(inactive_device_list[start_cnt+5:])
        next_4_msg = (f" #{start_cnt+6}-#{inactive_device_cnt} ({next_4_devicenames})")
        next_page_msg = ACTION_LIST_OPTIONS['next_page_devices'].replace('^add-text^', next_4_msg)
        self.actions_list.append(next_page_msg)

    self.actions_list.extend(REVIEW_INACTIVE_DEVICES)
    return vol.Schema({
        vol.Required('inactive_devices',
                    default=[]):
                    cv.multi_select(self.inactive_devices_key_text),

        vol.Required('action_items',
                    default=utils.action_default_text('goto_previous')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


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
    list_add(self.apple_acct_items_displayed, '➤ ADD A NEW APPLE ACCOUNT')

    default_key  = self.aa_page_item[self.aa_page_no]
    default_item = self.apple_acct_items_by_username.get(default_key)
    if default_item not in self.apple_acct_items_displayed:
        default_item = self.apple_acct_items_displayed[0]

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP):
        if is_empty(Gb.devicenames_x_mobapp_dnames):
            mobapp_interface.get_mobile_app_integration_device_info()
        # if is_empty(Gb.devicenames_x_mobapp_dnames):
        #     self.errors['data_source_mobapp'] = 'mobile_app_error'

    return vol.Schema({
        vol.Optional('data_source_mobapp',
                    default=mobile_app_used_default):
                    cv.multi_select([MOBILE_APP_USED_HEADER]),
        # vol.Optional('data_source',
        #             default=Gb.conf_tracking[CONF_DATA_SOURCE].replace(' ', '').split(',')):
        #             cv.multi_select(DATA_SOURCE_OPTIONS),
        vol.Optional('data_source_apple_acct',
                    default=apple_acct_used_default):
                    cv.multi_select([APPLE_ACCT_USED_HEADER]),
        vol.Optional('apple_accts',
                    default=default_item):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.apple_acct_items_displayed, mode='list')),
        vol.Required('action_items',
                    default=utils.action_default_text(default_action)):
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
def form_data_source_parameters(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    return vol.Schema({
        # vol.Required(CONF_PASSWORD_SRP_ENABLED,
        #             default=Gb.conf_tracking[CONF_PASSWORD_SRP_ENABLED]):
        #             # cv.boolean,
        #             selector.BooleanSelector(),
        vol.Required(CONF_SERVER_LOCATION_NEEDED,
                    default=Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED]):
                    # cv.boolean,
                    selector.BooleanSelector(),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            APPLE USERNAME PASSWORD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_apple_acct(self):
    lists.build_apple_accounts_list(self)

    retry_login_AA = [AA for AA in Gb.AppleAcct_error_by_username.values() if AA.error_next_retry_secs > 0]
    if isnot_empty(retry_login_AA):
        self.actions_list = [ACTION_LIST_OPTIONS['stop_login_retry']]
    else:
        self.actions_list = []
    self.actions_list.extend(USERNAME_PASSWORD_ACTIONS)

    if Gb.internet_error:
        action_default = 'cancel_goto_previous'
    else:
        action_default = 'save_log_into_apple_acct'

    errs_ui = self.errors_user_input
    username   = errs_ui.get(CONF_USERNAME)   or self.conf_apple_acct[CONF_USERNAME] or ' '
    password   = errs_ui.get(CONF_PASSWORD)   or self.conf_apple_acct[CONF_PASSWORD] or ' '
    password   = decode_password(password)
    locate_all = errs_ui.get(CONF_LOCATE_ALL) or self.conf_apple_acct[CONF_LOCATE_ALL]
    totp_key   = errs_ui.get(CONF_TOTP_KEY)   or self.conf_apple_acct[CONF_TOTP_KEY] or ' '

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
            self.errors[CONF_USERNAME] = 'verification_code_needed'
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
            vol.Required(CONF_SERVER_LOCATION,
                    default=utils.option_parm_to_text(self, CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(APPLE_SERVER_LOCATION_OPTIONS), mode='dropdown')),
        })

    schema.update({
        vol.Optional('locate_all',
                    default=locate_all):
                    cv.boolean,
        vol.Required('action_items',
                    default=utils.action_default_text(action_default)):
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
                    default=utils.action_default_text('cancel_goto_previous')):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            REAUTH
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_reauth(self, reauth_username=None):
    lists.build_apple_accounts_list(self)

    terms_of_use_update_needed = False
    auth_2fa_code_needed       = False
    request_2fa_code_needed    = False
    for AppleAcct in Gb.AppleAcct_by_username.values():
        if AppleAcct.terms_of_use_update_needed:
            terms_of_use_update_needed = True
        else:
            if AppleAcct.auth_2fa_code_needed or AppleAcct.username == reauth_username:
                auth_2fa_code_needed = True
            if AppleAcct.is_challenge_required:
                request_2fa_code_needed = True

    self.actions_list     = []
    if terms_of_use_update_needed:
        self.actions_list.append(ACTION_LIST_OPTIONS['accept_terms_of_use'])
    self.actions_list.extend(REAUTH_ACTIONS)

    if Gb.internet_error:
        action_list_default = 'goto_previous'
    elif terms_of_use_update_needed:
        action_list_default = 'accept_terms_of_use'
    elif auth_2fa_code_needed:
        action_list_default = 'send_verification_code'
    elif request_2fa_code_needed:
        action_list_default = 'request_verification_code'
    else:
        action_list_default = 'goto_previous'


    # Get the first acct (No Apple accts are set up or no Apple acct is selected)
    # or get the acct that needs to be authenticated
    # Requesting a new code will set the selected acct. Use it to deselect the acct
    if reauth_username is not None and reauth_username != '':
        self.apple_acct_reauth_username = reauth_username
        self.conf_apple_acct, self.aa_idx = \
                        config_file.conf_apple_acct(reauth_username)

    elif (instr(str(self.apple_acct_items_by_username), 'AUTHENTICATION')
            or instr(str(self.apple_acct_items_by_username), 'TERMS OF USE')):
        usernames = [username
                        for username, acct_info in self.apple_acct_items_by_username.items()
                        if (instr(acct_info, 'AUTHENTICATION')
                                or instr(acct_info, 'TERMS OF USE'))]
        self.apple_acct_reauth_username = usernames[0]
        self.conf_apple_acct, self.aa_idx = \
                        config_file.conf_apple_acct(self.apple_acct_reauth_username)

    elif (is_empty(self.apple_acct_items_by_username)
            or is_empty(Gb.conf_apple_accounts)
            or self.apple_acct_reauth_username not in self.apple_acct_items_by_username):
        self.conf_apple_acct, self.aa_idx = \
                        config_file.conf_apple_acct(0)
        self.apple_acct_reauth_username = self.conf_apple_acct[CONF_USERNAME]


    elif isnot_empty(self.conf_apple_acct):
        self.apple_acct_reauth_username = self.conf_apple_acct[CONF_USERNAME]

    else:
        self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(0)
        self.apple_acct_reauth_username = self.conf_apple_acct[CONF_USERNAME]

    # Set the default list from the username list or an error
    default_acct_selected = ''
    if self.apple_acct_reauth_username in Gb.AppleAcct_by_username:
        default_acct_selected = self.apple_acct_items_by_username[self.apple_acct_reauth_username]
        AppleAcct = Gb.AppleAcct_by_username.get(self.apple_acct_reauth_username)

        if AppleAcct and AppleAcct.login_successful is False:
            action_list_default = 'log_into_apple_acct'

    # If No Apple accts are set up yet
    elif is_empty(self.apple_acct_items_by_username):
        default_acct_selected = 'No Apple Accounts have been set up'
        self.apple_acct_items_by_username = {'.noacctssetup': default_acct_selected}
        self.errors[CONF_USERNAME] = 'apple_acct_not_set_up'
        action_list_default = 'goto_previous'
        AppleAcct = None

    else:
        default_acct_selected = list(self.apple_acct_items_by_username.values())[0]
        action_list_default = 'goto_previous'
        AppleAcct = self.AppleAcct or None

    # _log(f'{AppleAcct=} {AppleAcct.fido2_key_names=}')
    if Gb.fido2_security_keys_enabled is False:
        self.reauth_form_fido2_key_names_list = [
                        'Not Available > Security Key Authentication has not been implemented']
    elif AppleAcct.fido2_key_names:
        self.reauth_form_fido2_key_names_list = AppleAcct.fido2_key_names.copy()
    else:
        self.reauth_form_fido2_key_names_list = [
                        'None or Expired > Refresh Security Key List if using Security Keys']

    schema = ({
        vol.Optional('account_selected',
                    default=default_acct_selected):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.apple_acct_items_by_username),
                        mode='dropdown')),
            vol.Optional(CONF_VERIFICATION_CODE, default=' '):
                    selector.TextSelector(),
    })

    if Gb.fido2_security_keys_enabled:
        schema.update({
            vol.Required('fido2_key_name',
                    default=self.reauth_form_fido2_key_names_list[0]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.reauth_form_fido2_key_names_list, mode='dropdown')),
        })

    if terms_of_use_update_needed:
        schema.update({
            vol.Optional('terms_of_use',
                default=True):
                cv.boolean,
        })

    schema.update({
        vol.Optional('action_items',
                    default=utils.action_default_text(action_list_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DEVICE LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_device_list(self):
    action_default = 'update_device'
    self.actions_list = DEVICE_LIST_ACTIONS.copy()

    # Build list of all devices
    self.device_items_list = [device_item for device_item in self.device_items_by_devicename.values()]

    if is_empty(self.device_items_list):
        pass
    elif len(self.device_items_list) <= 6:
        self.device_items_displayed = self.device_items_list
    else:
        _build_device_items_displayed_over_5(self)
    list_add(self.device_items_displayed, '➤ ADD A NEW DEVICE')

    default_key  = self.dev_page_item[self.dev_page_no]
    default_item = self.device_items_by_devicename.get(default_key)
    if default_item not in self.device_items_displayed:
        default_item = self.device_items_displayed[0]

    return vol.Schema({
            vol.Required('devices',
                        default=default_item):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=self.device_items_displayed, mode='list')),
            vol.Required('action_items',
                    default=utils.action_default_text(action_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
    })

#................................................................................................
def _build_device_items_displayed_over_5(self):
    '''
    Build the display page and next page line for the Apple Accts list
    when more than 5 apple accounts
    '''
    # Build the list of apple accts to display on this page
    list_from_idx = self.dev_page_no * 5
    self.device_items_displayed = self.device_items_list[list_from_idx:list_from_idx+5]

    # Build the list of devices to display on the next page
    list_from_idx = list_from_idx + 5
    if list_from_idx >= len(self.device_items_list):
        list_from_idx = 0

    # Extract fname (devicename) from the devices list (Gary (gary_iphone) → ...))
    device_fnames = [device_item.split(RARROW)[0]
                            for device_item in self.device_items_list]
    device_fnames_next_page = (f"➤ OTHER DEVICES{RARROW}"
                                f"{', '.join(device_fnames[list_from_idx:list_from_idx+5])}")
    list_add(self.device_items_displayed, device_fnames_next_page)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ADD DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_add_device(self):
    self.actions_list = DEVICE_ADD_ACTIONS.copy()

    devicename    = utils.parm_or_device(self, CONF_IC3_DEVICENAME) or ' '
    icloud3_fname = utils.parm_or_device(self, CONF_FNAME) or ' '

    # iCloud Devices list default item
    apple_acct    = utils.parm_or_device(self, CONF_APPLE_ACCOUNT)
    icloud_dname  = utils.parm_or_device(self, CONF_FAMSHR_DEVICENAME)
    if icloud_dname == 'None'  or devicename == '':
        device_list_item_key = 'None'
    else:
        device_list_item_key = f"{icloud_dname}{LINK}{apple_acct}"

    device_list_item_text = self.icloud_list_text_by_fname.get(device_list_item_key)
    if device_list_item_text is None:
        device_list_item_text = self.icloud_list_text_by_fname['None']

    # Mobile App Devices list setup
    mobapp_device = utils.parm_or_device(self, CONF_MOBILE_APP_DEVICE)
    mobapp_list_text_by_entity_id = self.mobapp_list_text_by_entity_id.copy()
    if '.unknown' in mobapp_list_text_by_entity_id:
        default_mobile_app_device = mobapp_list_text_by_entity_id['.unknown']
    else:
        default_mobile_app_device = mobapp_list_text_by_entity_id[mobapp_device]

    # Picture list setup
    picture_filename = utils.parm_or_device(self, CONF_PICTURE)
    default_picture_filename = self.picture_by_filename.get(picture_filename)
    if default_picture_filename is None:
        picture_filename = 'None'
        default_picture_filename = self.picture_by_filename['None']

    return vol.Schema({
        vol.Required(CONF_IC3_DEVICENAME,
                    default=devicename):
                    selector.TextSelector(),
        vol.Required(CONF_FNAME,
                    default=icloud3_fname):
                    selector.TextSelector(),
        vol.Required(CONF_FAMSHR_DEVICENAME,
                    default=device_list_item_text):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.icloud_list_text_by_fname), mode='dropdown')),
        vol.Required(CONF_MOBILE_APP_DEVICE,
                    default=default_mobile_app_device):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
        vol.Required(CONF_PICTURE,
                    default=default_picture_filename):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.picture_by_filename), mode='dropdown')),
        vol.Required(CONF_ICON,
                    default=utils.parm_or_device(self, CONF_ICON)):
                    selector.IconSelector(),
        vol.Required(CONF_TRACKING_MODE,
                    default=utils.option_parm_to_text(self, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRACKING_MODE_OPTIONS), mode='dropdown')),
        vol.Required('action_items',
                default=utils.action_default_text('add_device')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE DEVICE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_device(self):

    # Build Other Tracking Parameters values text
    log_zones_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_LOG_ZONES] if zone.startswith('name') is False]
    tfz_fnames = [zone_dname(zone) for zone in self.conf_device[CONF_TRACK_FROM_ZONES]]
    device_type_fname = DEVICE_TYPE_FNAME(utils.parm_or_device(self, CONF_DEVICE_TYPE))
    otp_msg =  (f"Type ({device_type_fname}), "
                f"inZoneInterval ({format_timer(self.conf_device[CONF_INZONE_INTERVAL]*60)})")
    otp_msg += ", FixedInterval"
    if self.conf_device[CONF_FIXED_INTERVAL] > 0:
        otp_msg += f" ({format_timer(self.conf_device[CONF_FIXED_INTERVAL]*60)})"
    otp_msg += ", LogZones"
    if self.conf_device[CONF_LOG_ZONES] != [NONE]:
        otp_msg += f" ({list_to_str(log_zones_fnames)})"
    otp_msg += ", TrackFromZone"
    if self.conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        otp_msg += f" ({list_to_str(tfz_fnames)})"
    otp_msg += ", PrimaryTrackFromZone"
    if self.conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        otp_msg += f" ({zone_dname(self.conf_device[CONF_TRACK_FROM_BASE_ZONE])})"
    otp_action_item = ACTION_LIST_OPTIONS[
                'update_other_device_parameters'].replace('^otp_msg', otp_msg)

    error_key = ''
    self.errors = self.errors or {}
    self.actions_list = []
    self.actions_list.append(otp_action_item)
    self.actions_list.append(ACTION_LIST_OPTIONS['save'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_menu'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_select_device'])


    devicename    = utils.parm_or_device(self, CONF_IC3_DEVICENAME)
    icloud3_fname = utils.parm_or_device(self, CONF_FNAME) or ' '

    # iCloud Devices list default item
    apple_acct    = utils.parm_or_device(self, CONF_APPLE_ACCOUNT)
    icloud_dname  = utils.parm_or_device(self, CONF_FAMSHR_DEVICENAME)
    if icloud_dname == 'None' or devicename == '':
        device_list_item_key = 'None'
    else:
        icloud_dname_apple_acct, status_msg = \
                        lists.format_apple_acct_device_info(self, self.conf_device)

        if status_msg == '':
            device_list_item_key = f"{icloud_dname}{LINK}{apple_acct}"
        else:
            device_list_item_key = f"{devicename}{LINK}{apple_acct}"

    device_list_item_text = self.icloud_list_text_by_fname.get(device_list_item_key)
    if device_list_item_text is None:
        device_list_item_text = self.icloud_list_text_by_fname['None']

    # Check the icloud_dname and mobile app devicename for any errors
    self._validate_data_source_selections(self.conf_device)

    # Mobile App Devices list default item
    mobapp_device = utils.parm_or_device(self, CONF_MOBILE_APP_DEVICE)
    mobapp_list_text_by_entity_id = self.mobapp_list_text_by_entity_id.copy()
    if '.unknown' in mobapp_list_text_by_entity_id:
        default_mobile_app_device = mobapp_list_text_by_entity_id['.unknown']
    else:
        default_mobile_app_device = mobapp_list_text_by_entity_id[mobapp_device]

    # Picture list setup
    _picture_by_filename = {}
    picture_filename = utils.parm_or_device(self, CONF_PICTURE)
    default_picture_filename = self.picture_by_filename.get(picture_filename)
    if default_picture_filename is None:
        self.errors[CONF_PICTURE] = 'unknown_picture'
        default_picture_filename = (f"{RED_ALERT}{picture_filename}{RARROW}FILE NOT FOUND")
        _picture_by_filename[picture_filename] = default_picture_filename
        _picture_by_filename['.www_err'] = '═'*47

    _picture_by_filename.update(self.picture_by_filename)

    if Gb.internet_error:
            self.errors['base'] = 'internet_error'
    elif self.errors != {}:
        self.errors['base'] = 'unknown_value'

    if utils.parm_or_device(self, CONF_TRACKING_MODE) == INACTIVE_DEVICE:
        self.errors[CONF_TRACKING_MODE] = 'inactive_device'

    log_zones_key_text = {'none': 'None'}
    log_zones_key_text.update(self.zone_name_key_text)
    log_zones_key_text.update(LOG_ZONES_KEY_TEXT)

    schema = {
        vol.Required(CONF_IC3_DEVICENAME,
                    default=utils.parm_or_device(self, CONF_IC3_DEVICENAME)):
                    selector.TextSelector(),
        vol.Required(CONF_FNAME,
                    default=utils.parm_or_device(self, CONF_FNAME)):
                    selector.TextSelector(),
        vol.Required(CONF_FAMSHR_DEVICENAME,
                    default=device_list_item_text):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.icloud_list_text_by_fname), mode='dropdown')),
        vol.Required(CONF_MOBILE_APP_DEVICE,
                    default=default_mobile_app_device):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
        vol.Required(CONF_PICTURE,
                    default=default_picture_filename):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(_picture_by_filename), mode='dropdown')),
        }
    if utils.parm_or_device(self, CONF_PICTURE) == 'None':
        schema.update({
            vol.Required(CONF_ICON,
                    default=utils.parm_or_device(self, CONF_ICON)):
                    selector.IconSelector(),
        })
    schema.update({
        vol.Required(CONF_TRACKING_MODE,
                    default=utils.option_parm_to_text(self, CONF_TRACKING_MODE, TRACKING_MODE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRACKING_MODE_OPTIONS), mode='dropdown')),
        })

    schema.update({
        vol.Required('action_items',
                default=utils.action_default_text('save')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),
        })

    return vol.Schema(schema)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            UPDATE OTHER DEVICE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_update_other_device_parameters(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['save'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_previous'])

    log_zones_key_text = {'none': 'None'}
    log_zones_key_text.update(self.zone_name_key_text)
    log_zones_key_text.update(LOG_ZONES_KEY_TEXT)

    device_type_fname = DEVICE_TYPE_FNAME(utils.parm_or_device(self, CONF_DEVICE_TYPE))
    return vol.Schema({
            vol.Required(CONF_DEVICE_TYPE,
                    default=utils.option_parm_to_text(self, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAMES)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DEVICE_TYPE_FNAMES), mode='dropdown')),
            vol.Required(CONF_INZONE_INTERVAL,
                    default=self.conf_device[CONF_INZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
            vol.Required(CONF_FIXED_INTERVAL,
                    default=self.conf_device[CONF_FIXED_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=480, step=5, unit_of_measurement='minutes')),
            vol.Optional(CONF_LOG_ZONES,
                    default=utils.parm_or_device(self, CONF_LOG_ZONES)):
                    cv.multi_select(six_item_dict(log_zones_key_text)),
            vol.Required(CONF_TRACK_FROM_ZONES,
                    default=utils.parm_or_device(self, CONF_TRACK_FROM_ZONES)):
                    cv.multi_select(six_item_dict(self.zone_name_key_text)),
            vol.Required(CONF_TRACK_FROM_BASE_ZONE,
                    default=utils.option_parm_to_text(self, CONF_TRACK_FROM_BASE_ZONE,
                                                self.zone_name_key_text, conf_device=True)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DASHBOARD BUILDER FORM
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_dashboard_builder(self):
    dbname = self.ui_selected_dbname
    self.actions_list = []
    action_default = 'create_dashboard'
    self.actions_list.append(ACTION_LIST_OPTIONS['create_dashboard'])
    self.actions_list.append(ACTION_LIST_OPTIONS['cancel_goto_menu'])

    # Set default dashboard to current dashboard, the previous dashboard or 'add'
    default_dbname = self.dbf_dashboard_key_text[dbname]

    default_main_view_style = DASHBOARD_MAIN_VIEW_STYLE_OPTIONS[RESULT_SUMMARY]

    self.dbf_main_view_devices_key_text = {}
    self.dbf_main_view_devices_key_text.update(DASHBOARD_MAIN_VIEW_DEVICES_BASE)
    self.dbf_main_view_devices_key_text.update(lists.devices_selection_list())
    # main_view_devices = self.main_view_info_dnames_by_dbname.get(dbname, ALL_DEVICES)

    # if is_empty(self.ui_main_view_dnames):
    self.ui_main_view_dnames = [ALL_DEVICES]

    return vol.Schema({
        vol.Required('selected_dashboard',
                    default=default_dbname):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.dbf_dashboard_key_text), mode='list')),
        # vol.Optional('main_view_desc',
        #             default=False):
        #             selector.BooleanSelector(),
        vol.Required('main_view_style',
                    default=default_main_view_style):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DASHBOARD_MAIN_VIEW_STYLE_OPTIONS), mode='dropdown')),
        vol.Required('main_view_devices',
                    default=self.ui_main_view_dnames):
                    cv.multi_select(six_item_dict(self.dbf_main_view_devices_key_text)),

        vol.Required('action_items',
                    default=utils.action_default_text(action_default)):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           TOOLS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tools(self):
    self.actions_list = TOOL_LIST_ITEMS.copy()
    action_default = 'goto_menu'

    lists.build_log_level_devices_list(self)
    if Gb.conf_general[CONF_LOG_LEVEL_DEVICES] != 'all':
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = [
                                    devicename for devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                                    if devicename in Gb.Devices_by_devicename]
    if is_empty(Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
        Gb.conf_general[CONF_LOG_LEVEL_DEVICES] = ['all']

    return vol.Schema({
        vol.Required(CONF_LOG_LEVEL,
                    default=utils.option_parm_to_text(self, CONF_LOG_LEVEL, LOG_LEVEL_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(LOG_LEVEL_OPTIONS), mode='dropdown')),
        vol.Required(CONF_LOG_LEVEL_DEVICES,
                    default=Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    cv.multi_select(six_item_dict(self.log_level_devices_key_text)),

        vol.Required('action_items',
                    default=utils.action_default_text(action_default)):
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            ACTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_actions(self):
    debug_OPTIONS = ACTIONS_DEBUG_ITEMS.copy()
    if Gb.log_debug_flag:
        debug_OPTIONS.pop('debug_start')
    else:
        debug_OPTIONS.pop('debug_stop')
    if Gb.log_rawdata_flag:
        debug_OPTIONS.pop('rawdata_start')
    else:
        debug_OPTIONS.pop('rawdata_stop')

    return vol.Schema({
        vol.Optional('ic3_actions', default=[]):
                    cv.multi_select(ACTIONS_IC3_ITEMS),
                    # selector.SelectSelector(selector.SelectSelectorConfig(
                    #     options=dict_value_to_list(ACTIONS_IC3_ITEMS), mode='list')),
        vol.Optional('debug_actions', default=[]):
                    cv.multi_select(debug_OPTIONS),
                    # selector.SelectSelector(selector.SelectSelectorConfig(
                    #     options=dict_value_to_list(debug_OPTIONS), mode='list')),
        vol.Optional('other_actions', default=[]):
                    cv.multi_select(ACTIONS_OTHER_ITEMS),
                    # selector.SelectSelector(selector.SelectSelectorConfig(
                    #     options=dict_value_to_list(ACTIONS_OTHER_ITEMS), mode='list')),
        vol.Optional('action_items', default=[]):
                    cv.multi_select(ACTIONS_ACTION_ITEMS),
                    # selector.SelectSelector(selector.SelectSelectorConfig(
                    #     options=dict_value_to_list(ACTIONS_ACTION_ITEMS), mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRACKING PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_tracking_parameters(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    return vol.Schema({
        vol.Required(CONF_DISTANCE_BETWEEN_DEVICES,
                    default=Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]):
                    selector.BooleanSelector(),
        vol.Optional(CONF_DISCARD_POOR_GPS_INZONE,
                    default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]):
                    selector.BooleanSelector(),
        vol.Required(CONF_GPS_ACCURACY_THRESHOLD,
                    default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=300, step=5, unit_of_measurement='m')),
        vol.Required(CONF_OLD_LOCATION_THRESHOLD,
                    default=Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=1, max=60, step=1, unit_of_measurement='minutes')),
        vol.Required(CONF_OLD_LOCATION_ADJUSTMENT,
                    default=Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=60, step=1, unit_of_measurement='minutes')),
        vol.Required(CONF_MAX_INTERVAL,
                    default=Gb.conf_general[CONF_MAX_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=480, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_EXIT_ZONE_INTERVAL,
                    default=Gb.conf_general[CONF_EXIT_ZONE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=.5, max=10, step=.5, unit_of_measurement='minutes')),
        vol.Required(CONF_MOBAPP_ALIVE_INTERVAL,
                    default=Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=15, max=240, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_OFFLINE_INTERVAL,
                    default=Gb.conf_general[CONF_OFFLINE_INTERVAL]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=240, step=5, unit_of_measurement='minutes')),
        vol.Required(CONF_TFZ_TRACKING_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=1, max=100, unit_of_measurement='Km')),
        vol.Required(CONF_TRAVEL_TIME_FACTOR,
                    default=utils.option_parm_to_text(self, CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT), mode='dropdown')),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              FORMAT SETTINGS & ICLOUD3 DIRECTORIES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_format_settings(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()
    self._set_example_zone_name()

    self.picture_by_filename = {}
    if PICTURE_WWW_STANDARD_DIRS in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
        Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = []

    return vol.Schema({
        vol.Required(CONF_DISPLAY_ZONE_FORMAT,
                    default=utils.option_parm_to_text(self, CONF_DISPLAY_ZONE_FORMAT, DISPLAY_ZONE_FORMAT_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DISPLAY_ZONE_FORMAT_OPTIONS), mode='dropdown')),
        vol.Required(CONF_DEVICE_TRACKER_STATE_SOURCE,
                    default=utils.option_parm_to_text(self, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(DEVICE_TRACKER_STATE_SOURCE_OPTIONS), mode='dropdown')),
        vol.Required(CONF_UNIT_OF_MEASUREMENT,
                    default=utils.option_parm_to_text(self, CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list( UNIT_OF_MEASUREMENT_OPTIONS), mode='dropdown')),
        vol.Required(CONF_TIME_FORMAT,
                    default=utils.option_parm_to_text(self, CONF_TIME_FORMAT, TIME_FORMAT_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(TIME_FORMAT_OPTIONS), mode='dropdown')),
        vol.Required(CONF_PICTURE_WWW_DIRS,
                    default=Gb.conf_profile[CONF_PICTURE_WWW_DIRS] or self.www_directory_list):
                    cv.multi_select(six_item_list(self.www_directory_list)),
        vol.Required(CONF_DISPLAY_GPS_LAT_LONG,
                    default=Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]):
                    # cv.boolean,
                    selector.BooleanSelector(),

        vol.Required('evlog_header',
                    default=IC3_DIRECTORY_HEADER):
                    # cv.multi_select([IC3_DIRECTORY_HEADER]),
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=[IC3_DIRECTORY_HEADER], mode='list')),
        vol.Required(CONF_EVLOG_CARD_DIRECTORY,
                    default=utils.parm_or_error_msg(self, CONF_EVLOG_CARD_DIRECTORY, conf_group=CF_PROFILE)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.www_directory_list), mode='dropdown')),
        vol.Optional(CONF_EVLOG_BTNCONFIG_URL,
                    default=f"{utils.parm_or_error_msg(self, CONF_EVLOG_BTNCONFIG_URL, conf_group=CF_PROFILE)} "):
                    selector.TextSelector(),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           CHANGE DEVICE ORDER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_change_device_order(self):
    self.actions_list = [
            ACTION_LIST_OPTIONS['move_up'],
            ACTION_LIST_OPTIONS['move_down']]
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
        vol.Required('device_desc',
                    default=self.cdo_devicenames[self.cdo_curr_idx]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.cdo_devicenames, mode='list')),
        vol.Required('action_items',
                    default=utils.action_default_text(self.actions_list_default)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           PICTURE IMAGE FILTER
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_picture_dir_filter(self):
    self.actions_list = [
            ACTION_LIST_OPTIONS['save'],
            ACTION_LIST_OPTIONS['goto_previous']]

    # self.picture_by_filename = {}
    if PICTURE_WWW_STANDARD_DIRS in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
        Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = []

    www_group_1 = {}
    www_group_2 = {}
    www_group_3 = {}
    www_group_4 = {}
    www_group_5 = {}
    conf_www_group_1 = []
    conf_www_group_2 = []
    conf_www_group_3 = []
    conf_www_group_4 = []
    conf_www_group_5 = []
    for dir in self.www_directory_list:
        if len(www_group_1) < 5:
            www_group_1[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_1, dir)
        elif len(www_group_2) < 5:
            www_group_2[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_2, dir)
        elif len(www_group_3) < 5:
            www_group_3[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_3, dir)
        elif len(www_group_4) < 5:
            www_group_4[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_4, dir)
        elif len(www_group_5) < 5:
            www_group_5[dir] = dir
            if dir in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                list_add(conf_www_group_5, dir)

    schema = {
        vol.Required('www_group_1',
                    default=conf_www_group_1):
                    cv.multi_select(www_group_1)}

    if isnot_empty(www_group_2):
        schema.update({
            vol.Required('www_group_2',
                    default=conf_www_group_2):
                    cv.multi_select(www_group_2),})
    if isnot_empty(www_group_3):
        schema.update({
            vol.Required('www_group_3',
                    default=conf_www_group_3):
                    cv.multi_select(www_group_3),})
    if isnot_empty(www_group_4):
        schema.update({
            vol.Required('www_group_4',
                    default=conf_www_group_4):
                    cv.multi_select(www_group_4),})
    if isnot_empty(www_group_5):
        schema.update({
            vol.Required('www_group_5',
                    default=conf_www_group_5):
                    cv.multi_select(www_group_5),})

    schema.update({
        vol.Required('action_items',
                default=utils.action_default_text('save')):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=self.actions_list, mode='list')),})

    return vol.Schema(schema)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            AWAY TIME ZONE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_away_time_zone(self):
    self.actions_list = []
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
        vol.Required(CONF_AWAY_TIME_ZONE_1_DEVICES,
                    default=Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
                    cv.multi_select(six_item_dict(self.away_time_zone_devices_key_text)),
        vol.Required(CONF_AWAY_TIME_ZONE_1_OFFSET,
                    default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

        vol.Required(CONF_AWAY_TIME_ZONE_2_DEVICES,
                    default=Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
                    cv.multi_select(six_item_dict(self.away_time_zone_devices_key_text)),
        vol.Required(CONF_AWAY_TIME_ZONE_2_OFFSET,
                    default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_display_text_as(self):
    self.dta_selected_idx = self.dta_selected_idx_page[self.dta_page_no]
    if self.dta_selected_idx <= 4:
        dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                        if k <= 4]
        dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                        if k >= 5]
    else:
        dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                        if k >= 5]
        dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                        if k <= 4]

    dta_next_page_display_items = ", ".join(dta_next_page_display_list)
    next_page_text = ACTION_LIST_OPTIONS['next_page_items']
    next_page_text = next_page_text.replace('^add-text^', dta_next_page_display_items)

    self.actions_list = [next_page_text]
    self.actions_list.extend([ACTION_LIST_OPTIONS['select_text_as']])
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    return vol.Schema({
        vol.Required(CONF_DISPLAY_TEXT_AS,
                    default=self.dta_working_copy[self.dta_selected_idx]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dta_page_display_list)),
        vol.Required('action_items',
                    default=utils.action_default_text('select_text_as')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISPLAY TEXT AS UPDATE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_display_text_as_update(self):
    self.actions_list = [ACTION_LIST_OPTIONS['clear_text_as']]
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    if instr(self.dta_working_copy[self.dta_selected_idx], '>'):
        text_from_to_parts = self.dta_working_copy[self.dta_selected_idx].split('>')
        text_from = text_from_to_parts[0].strip()
        text_to   = text_from_to_parts[1].strip()
    else:
        text_from = ''
        text_to   = ''

    return vol.Schema({
        vol.Optional('text_from',
                    default=text_from):
                    selector.TextSelector(),
        vol.Optional('text_to'  ,
                    default=text_to):
                    selector.TextSelector(),
        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            INZONE INTERVALS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_inzone_intervals(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()
    return vol.Schema({
        vol.Optional(IPHONE,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPHONE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(IPAD,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][IPAD]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(WATCH,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][WATCH]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(AIRPODS,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][AIRPODS]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(NO_MOBAPP,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][NO_MOBAPP]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),
        vol.Optional(OTHER,
                    default=Gb.conf_general[CONF_INZONE_INTERVALS][OTHER]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=5, max=480, step=5, unit_of_measurement='minutes')),

        vol.Optional('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            WAZE MAIN
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_waze_main(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    wuh_default  = [WAZE_USED_HEADER] if Gb.conf_general[CONF_WAZE_USED] else []
    whuh_default = [WAZE_HISTORY_USED_HEADER] if Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED] else []
    return vol.Schema({
        vol.Optional(CONF_WAZE_USED,
                    default=wuh_default):
                    cv.multi_select([WAZE_USED_HEADER]),
        vol.Optional(CONF_WAZE_SERVER,
                    default=utils.option_parm_to_text(self, CONF_WAZE_SERVER, WAZE_SERVER_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(WAZE_SERVER_OPTIONS), mode='dropdown')),
        vol.Optional(CONF_WAZE_MIN_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_MIN_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=100, step=5, unit_of_measurement='km')),
        vol.Optional(CONF_WAZE_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=1000, step=5, unit_of_measurement='km')),
        vol.Optional(CONF_WAZE_REALTIME,
                    default=Gb.conf_general[CONF_WAZE_REALTIME]):
                    selector.BooleanSelector(),

        vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                    default=whuh_default):
                    cv.multi_select([WAZE_HISTORY_USED_HEADER]),
        vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                    default=Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]):
                    selector.NumberSelector(selector.NumberSelectorConfig(
                        min=0, max=1000, step=5, unit_of_measurement='km')),
        vol.Required(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                    default=utils.option_parm_to_text(self, CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                                        WAZE_HISTORY_TRACK_DIRECTION_OPTIONS)):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=dict_value_to_list(WAZE_HISTORY_TRACK_DIRECTION_OPTIONS), mode='dropdown')),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SPECIAL ZONES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_special_zones(self):
    self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

    try:
        pass_thru_zone_used  = (Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] > 0)
        stat_zone_used       = (Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] > 0)
        track_from_base_zone_used = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]

        ptzh_default = [PASSTHRU_ZONE_HEADER] if pass_thru_zone_used else []
        szh_default  = [STAT_ZONE_HEADER] if stat_zone_used else []
        tfzh_default = [TRK_FROM_HOME_ZONE_HEADER] if track_from_base_zone_used else []

        return vol.Schema({
            vol.Required('stat_zone_header',
                        default=szh_default):
                        cv.multi_select([STAT_ZONE_HEADER]),
            vol.Required(CONF_STAT_ZONE_FNAME,
                        default=utils.parm_or_error_msg(self, CONF_STAT_ZONE_FNAME)):
                        selector.TextSelector(),
            vol.Required(CONF_STAT_ZONE_STILL_TIME,
                        default=Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=60, unit_of_measurement='minutes')),
            vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                        default=Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=5, max=60, step=5, unit_of_measurement='minutes')),

            vol.Optional('passthru_zone_header',
                        default=ptzh_default):
                        cv.multi_select([PASSTHRU_ZONE_HEADER]),
            vol.Required(CONF_PASSTHRU_ZONE_TIME,
                        default=Gb.conf_general[CONF_PASSTHRU_ZONE_TIME]):
                        selector.NumberSelector(selector.NumberSelectorConfig(
                            min=0, max=5, step=.5, unit_of_measurement='minutes')),

            vol.Optional(CONF_TRACK_FROM_BASE_ZONE_USED,
                        default=tfzh_default):
                        cv.multi_select([TRK_FROM_HOME_ZONE_HEADER]),
            vol.Required(CONF_TRACK_FROM_BASE_ZONE,
                        default=utils.option_parm_to_text(self, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),
            vol.Optional(CONF_TRACK_FROM_HOME_ZONE,
                        default=Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
                        # cv.boolean,
                        selector.BooleanSelector(),

            vol.Required('action_items',
                        default=utils.action_default_text('save')):
                        selector.SelectSelector(selector.SelectSelectorConfig(
                            options=self.actions_list, mode='list')),
            })
    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_sensors(self, user_input=None):
    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['exclude_sensors'])
    self.actions_list.append(ACTION_LIST_OPTIONS['set_to_default_sensors'])
    self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

    self.set_default_sensors(Gb.conf_sensors)
    sensors = user_input if user_input is not None else Gb.conf_sensors

    if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
        Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

    return vol.Schema({
        vol.Required(CONF_SENSORS_DEVICE,
                    default=sensors[CONF_SENSORS_DEVICE]):
                    cv.multi_select(CONF_SENSORS_DEVICE_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_UPDATE,
                    default=sensors[CONF_SENSORS_TRACKING_UPDATE]):
                    cv.multi_select(CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_TIME,
                    default=sensors[CONF_SENSORS_TRACKING_TIME]):
                    cv.multi_select(CONF_SENSORS_TRACKING_TIME_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_DISTANCE,
                    default=sensors[CONF_SENSORS_TRACKING_DISTANCE]):
                    cv.multi_select(CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT),
        vol.Required(CONF_SENSORS_ZONE,
                    default=sensors[CONF_SENSORS_ZONE]):
                    cv.multi_select(CONF_SENSORS_ZONE_KEY_TEXT),
        vol.Required(CONF_SENSORS_OTHER,
                    default=sensors[CONF_SENSORS_OTHER]):
                    cv.multi_select(CONF_SENSORS_OTHER_KEY_TEXT),
        # vol.Required(CONF_SENSORS_TRACK_FROM_ZONES,
        #             default=sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
        #             cv.multi_select(CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT),
        vol.Required(CONF_SENSORS_MONITORED_DEVICES,
                    default=sensors[CONF_SENSORS_MONITORED_DEVICES]):
                    cv.multi_select(CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT),
        vol.Required(CONF_SENSORS_TRACKING_OTHER,
                    default=sensors[CONF_SENSORS_TRACKING_OTHER]):
                    cv.multi_select(CONF_SENSORS_TRACKING_OTHER_KEY_TEXT),
        vol.Optional(CONF_EXCLUDED_SENSORS,
                    default=sensors[CONF_EXCLUDED_SENSORS]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=Gb.conf_sensors[CONF_EXCLUDED_SENSORS], mode='list', multiple=True)),

        vol.Required('action_items',
                    default=utils.action_default_text('save')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            EXCLUDE SENSORS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_exclude_sensors(self):
    self.actions_list = SENSORS_EXCLUDE_ACTIONS_.copy()

    if self.sensors_list_filter == '?':
        filtered_sensors_fname_list = [f"None Displayed - Enter a Filter or `all` \
                        to display all sensors ({len(self.sensors_fname_list)} Sensors)"]
        filtered_sensors_list_default = []
    else:
        self.sensors_list_filter.replace('?', '')
        if self.sensors_list_filter.lower() == 'all':
            filtered_sensors_fname_list = [sensor_fname
                            for sensor_fname in self.sensors_fname_list
                            if sensor_fname not in self.excluded_sensors]
        else:
            filtered_sensors_fname_list = list(set([sensor_fname
                            for sensor_fname in self.sensors_fname_list
                            if ((instr(sensor_fname.lower(), self.sensors_list_filter)
                                and sensor_fname not in self.excluded_sensors))]))

        filtered_sensors_list_default = list(set([sensor_fname
                            for sensor_fname in filtered_sensors_fname_list
                            if sensor_fname in self.excluded_sensors]))

        filtered_sensors_fname_list.sort()
        if filtered_sensors_fname_list == []:
            filtered_sensors_fname_list = [f"No Sensors found containing \
                                                '{self.sensors_list_filter}'"]

    return vol.Schema({
        vol.Optional(CONF_EXCLUDED_SENSORS,
                    default=self.excluded_sensors):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.excluded_sensors, mode='list', multiple=True)),
        vol.Optional('filter',
                    default=self.sensors_list_filter):
                    selector.TextSelector(),
        vol.Optional('filtered_sensors',
                    default=filtered_sensors_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=filtered_sensors_fname_list, mode='list', multiple=True)),

        vol.Required('action_items',
                    default=utils.action_default_text('filter_sensors')):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA IC3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_restart_ha(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    # self.actions_list.append(ACTION_LIST_OPTIONS['restart_icloud3'])
    self.actions_list.append(ACTION_LIST_OPTIONS['goto_menu'])
    self.actions_list.append(ACTION_LIST_OPTIONS['exit'])

    actions_list_default = utils.action_default_text('restart_ha')

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
        })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            RESTART HA, RELOAD ICLOUD3
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_restart_ha_reload_icloud3(self):

    self.actions_list = []
    self.actions_list.append(ACTION_LIST_OPTIONS['restart_ha'])
    # self.actions_list.append(ACTION_LIST_OPTIONS['reload_icloud3'])
    self.actions_list.append(ACTION_LIST_OPTIONS['exit'])

    actions_list_default = utils.action_default_text('exit')

    return vol.Schema({
        vol.Required('action_items',
                    default=actions_list_default):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=self.actions_list, mode='list')),
                })
