

from ...global_variables    import GlobalVariables as Gb
from ...const_config        import (CONF_VERSION, CONF_APPLE_ACCT, CONF_PASSWORD, CONF_LOCATE_ALL,
                                    CONF_SERVER_LOCATION,
                                    CONF_SERVER_LOCATION_NEEDED, )
from ...const_char          import (RARROW, )

from ...utils.utils         import (is_empty, isnot_empty,
                                    decode_password, )
from ...utils.messaging     import (_log, log_info_msg, log_exception, log_debug_msg,
                                    post_event, post_alert, post_greenbar_msg, update_alert_sensor,)

from ..                     import utils_cf
from ..                     import selection_lists as lists
from ...apple_acct          import apple_acct_support_cf as aascf
from ..const_form_lists     import *

from homeassistant.helpers  import (selector,
                                    entity_registry as er,
                                    device_registry as dr,)
import homeassistant.helpers.config_validation as cv
import voluptuous as vol


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           ICLOUD3 APPLE ACCOUNT CONFIG FLOW FORMS
#
#           - apple_accounts_menu_options
#           - apple_acct_heading
#           - form_update_apple_acct
#           - form_delete_apple_acct
#           - form_other_apple_acct_parameters
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#              APPLE ACCOUNTS LIST
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def apple_accounts_menu_options(self):
    '''
    Build the Apple Accounts menu. Each Apple Account on the current page is a menu row
    (name, information below it) that opens the Apple Account menu. Adding an Apple
    Account and Back are listed below them.

    Return:
        {option: label}, label=None uses the strings.json label
        placeholders for the strings.json labels
    '''
    lists.build_apple_accounts_list(self)

    apple_ids = [apple_id for apple_id in self.apple_acct_items_by_apple_id.keys()
                            if apple_id != 'apple_acct_hdr']

    page_cnt = max(1, -(-len(apple_ids) // APPLE_ACCT_LIST_PAGE_SIZE))
    if self.aa_page_no >= page_cnt:
        self.aa_page_no = 0
    from_idx = self.aa_page_no * APPLE_ACCT_LIST_PAGE_SIZE
    self.apple_acct_items_displayed = apple_ids[from_idx:from_idx + APPLE_ACCT_LIST_PAGE_SIZE]

    menu_options = {}
    placeholders = {}
    for slot, apple_id in enumerate(self.apple_acct_items_displayed):
        acct_name, _acct_info = _split_list_item(self.apple_acct_items_by_apple_id[apple_id])
        acct_status = apple_acct_status(apple_id)
        menu_options[f"apple_accounts_acct_{slot}"] = (f"{CF_ALERT}{acct_name}"
                                                        if CF_ALERT in acct_status else acct_name)
        placeholders[f"acct_{slot}"] = acct_status

    if page_cnt > 1:
        next_page_from_idx = (from_idx + APPLE_ACCT_LIST_PAGE_SIZE) % (page_cnt * APPLE_ACCT_LIST_PAGE_SIZE)
        menu_options['apple_accounts_next_page'] = None
        placeholders['accounts'] = ', '.join(
                    [self.apple_acct_items_by_apple_id[apple_id].split(RARROW)[0]
                        for apple_id in apple_ids[next_page_from_idx:next_page_from_idx + APPLE_ACCT_LIST_PAGE_SIZE]])

    if Gb.internet_error is False:
        menu_options['apple_accounts_add'] = None
    menu_options['apple_accounts_back'] = None

    return menu_options, placeholders

#................................................................................................
def _split_list_item(list_item):
    '''
    Split an Apple Accounts list item into the name displayed on the menu row and the
    information displayed below it (GaryCobb (gcobb321) → 4 of 7 iCloud Devices Tracked, ...)
    '''
    name, _, info = list_item.partition(RARROW)
    return name.strip(), info.strip()


#................................................................................................
def apple_acct_status(apple_id, with_device_cnt=True):
    '''
    The login status and tracked device count of an Apple Account displayed below its
    name (Logged in · 2 of 10 devices tracked)
    '''
    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
    error_AppleAcct = Gb.AppleAcct_error_by_apple_id.get(apple_id)
    tracked_cnt, _, untracked_cnt, _ = lists.tracked_untracked_form_msg(apple_id)
    devices_tracked = lists.devices_tracked_text(tracked_cnt, tracked_cnt + untracked_cnt)
    if with_device_cnt is False:
        devices_tracked = ''

    if AppleAcct and AppleAcct.is_reauth_needed:
        return f"{CF_ALERT}{utils_cf.tr('auth_needed')}{_dot(devices_tracked)}"
    if AppleAcct and AppleAcct.terms_of_use_update_needed:
        return f"{CF_ALERT}{utils_cf.tr('auth_terms_of_use_needed')}{_dot(devices_tracked)}"
    if AppleAcct and AppleAcct.auth_failed_503:
        return f"{CF_ALERT}{utils_cf.tr('aa_status_503')}"
    if error_AppleAcct:
        return CF_ALERT + utils_cf.tr('aa_status_login_failed_retrying'
                                if error_AppleAcct.error_next_retry_secs > 0 else
                            'aa_status_login_failed')
    if aascf.is_apple_acct_logged_into(apple_id):
        return f"{utils_cf.tr('aa_status_logged_in')}{_dot(devices_tracked)}"

    return utils_cf.tr('aa_status_not_logged_in')

def _dot(text):
    return f" · {text}" if text else ''

#................................................................................................
def apple_acct_heading(self, import_hint=True):
    '''
    The name and information of the Apple Account being updated (self.conf_apple_acct)
    displayed at the top of the Apple Account forms

    Return:
        description placeholders {form_title, acct_name, acct_info}
    '''
    lists.build_apple_accounts_list(self)

    apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]
    if self.add_apple_acct_flag or apple_id.strip() == '':
        return {'form_title': utils_cf.tr('title_add_apple_acct'),
                'acct_name': utils_cf.tr('new_apple_acct'),
                'acct_info': f"\n{utils_cf.tr('aa_add_info')}"}

    if apple_id not in self.apple_acct_items_by_apple_id:
        self.apple_acct_items_by_apple_id[apple_id] = (
                    f"{apple_id}{RARROW}{utils_cf.tr('aa_status_setting_up')}")

    acct_name, _acct_info = _split_list_item(self.apple_acct_items_by_apple_id[apple_id])

    return {'form_title': utils_cf.tr('title_apple_acct'),
            'acct_name': acct_name, 'acct_info': _apple_acct_info(apple_id, import_hint)}

def _apple_acct_info(apple_id, import_hint=True):
    '''
    The status, the tracked devices and the number of untracked devices of the Apple
    Account displayed after its name:
        · Logged in
        Tracked (2 of 10): Gary-iPhone, Gary-iPad
        8 more devices aren't tracked. Add them with Devices → Import devices
    '''
    tracked_cnt, tracked_devices, untracked_cnt, _ = lists.tracked_untracked_form_msg(apple_id)
    device_cnt = tracked_cnt + untracked_cnt
    acct_info = _dot(apple_acct_status(apple_id, with_device_cnt=False))

    one_other = lambda cnt: 'one' if cnt == 1 else 'other'
    if tracked_cnt > 0:
        acct_info += "\n" + utils_cf.tr('aa_info_tracked', tracked=tracked_cnt, total=device_cnt,
                                        devices=tracked_devices)
    if untracked_cnt > 0:
        untracked_msg = (utils_cf.tr(f"aa_info_more_untracked_{one_other(untracked_cnt)}",
                                        cnt=untracked_cnt)
                            if tracked_cnt > 0 else
                         utils_cf.tr(f"aa_info_none_tracked_{one_other(device_cnt)}",
                                        total=device_cnt))
        acct_info += f"\n{untracked_msg}"
        if import_hint:
            acct_info += f". {utils_cf.tr(f'aa_info_import_hint_{one_other(untracked_cnt)}')}"

    return acct_info


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            OTHER APPLE PARAMETERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_other_apple_acct_parameters(self):
    '''
    The Other Apple Account Parameters screen opened from the Update Apple Account screen
    in HA Repairs
    '''
    return vol.Schema({
        **_other_apple_acct_parameters_schema(self),

        **utils_cf.submit_back_field(self, 'save', 'rtn_update_apple_acct',
                                        'the_apple_acct'),
        })

def _other_apple_acct_parameters_schema(self):
    '''
    The Other Apple Account Parameters fields. They are in the Advanced section of the
    Update Apple Account screen and on the Other Apple Account Parameters screen opened
    from HA Repairs.
    '''
    return {
        vol.Required(CONF_SERVER_LOCATION_NEEDED,
                    default=Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED]):
                    selector.BooleanSelector(),

        vol.Optional(CONF_SERVER_LOCATION,
                default=utils_cf.option_parm_key(self, CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)):
                utils_cf.select(APPLE_SERVER_LOCATION_OPTIONS, translation_key='server_location', mode='dropdown'),
        }


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            APPLE USERNAME PASSWORD
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def reauth_action_label_key(self):
    '''
    The label (selector.cf_text) of the action that opens the Authenticate screen, by the
    Apple Account's state
    '''
    apple_id  = self.conf_apple_acct[CONF_APPLE_ACCT]
    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

    if AppleAcct and AppleAcct.terms_of_use_update_needed:
        return 'action_accept_terms_of_use'
    if AppleAcct and AppleAcct.is_reauth_needed:
        return 'action_reauth_now'
    if aascf.is_apple_acct_logged_into(apple_id) is False:
        return 'action_auth_options_sign_in_first'
    return 'action_auth_options'

#................................................................................................
def form_update_apple_acct(self):
    lists.build_apple_accounts_list(self)

    # The Update Apple Account screen opened from HA Repairs is the only screen of the
    # repair, the Other parameters are on their own screen
    if self.is_repair_flow:
        retry_login_AA = [AA    for AA in Gb.AppleAcct_error_by_apple_id.values()
                                if AA.error_next_retry_secs > 0]

        actions = {'save_log_into_apple_acct': utils_cf.tr('submit_save_log_into_apple_acct')}
        # Authentication can only be done on a saved Apple Acct that is valid and logged
        # into. A new acct or one whose login failed has to be saved/logged into first.
        if aascf.is_apple_acct_logged_into(self.conf_apple_acct[CONF_APPLE_ACCT]):
            actions['authenticate_apple_acct'] = utils_cf.tr(reauth_action_label_key(self))
        if isnot_empty(retry_login_AA):
            actions['stop_login_retry'] = utils_cf.tr('action_stop_login_retry')
        actions['other_apple_acct_parameters'] = utils_cf.tr('action_other_apple_acct_parameters')
        actions['exit_repair'] = utils_cf.tr('back_exit_repair')

        default_action = 'exit_repair' if Gb.internet_error else 'save_log_into_apple_acct'
        action_field = utils_cf.form_action_field(self, actions, default_action)

    # If the configuration file is at it's initial condition, this screen is displayed
    # instead of the Apple Accounts list and Back returns to the main menu. If no
    # apple_id/password is entered, the iCloud data source is disabled until one is.
    elif is_empty(Gb.conf_apple_accounts) or self.add_apple_acct_flag:
        if is_empty(Gb.conf_apple_accounts):
            back_action, back_destination = 'menu', utils_cf.menu_name(self)
        else:
            back_action, back_destination = 'rtn_apple_accounts', 'apple_accounts'
        action_field = utils_cf.submit_back_field(self, 'save_log_into_apple_acct', back_action,
                                        back_destination, submit_destination='apple_accounts')

    else:
        other_actions = {'authenticate_apple_acct': utils_cf.tr(reauth_action_label_key(self))}
        error_AppleAcct = Gb.AppleAcct_error_by_apple_id.get(self.conf_apple_acct[CONF_APPLE_ACCT])
        if error_AppleAcct and error_AppleAcct.error_next_retry_secs > 0:
            other_actions['stop_login_retry'] = utils_cf.tr('action_stop_login_retry')
        other_actions['delete_apple_acct'] = utils_cf.tr('action_delete_apple_acct')

        action_field = utils_cf.submit_back_field(self, 'save_log_into_apple_acct', 'rtn_apple_accounts',
                                        'apple_accounts', other_actions=other_actions)

    errs_ui = self.errors_user_input
    apple_id   = errs_ui.get(CONF_APPLE_ACCT)   or self.conf_apple_acct[CONF_APPLE_ACCT] or ' '
    password   = errs_ui.get(CONF_PASSWORD)   or self.conf_apple_acct[CONF_PASSWORD] or ' '
    password   = decode_password(password)
    locate_all = errs_ui.get(CONF_LOCATE_ALL) or self.conf_apple_acct[CONF_LOCATE_ALL]

    password_selector = selector.TextSelector(selector.TextSelectorConfig(type='password'))

    if Gb.internet_error:
            self.errors['base'] = 'internet_error_no_change'

    if apple_id in self.apple_acct_items_by_apple_id:
        self.errors.pop('account_selected', None)
        self.header_msg = ''

    schema = ({
        vol.Optional(CONF_APPLE_ACCT,
                    default=apple_id):
                    selector.TextSelector(),
        vol.Optional(CONF_PASSWORD ,
                    default=password):
                    password_selector,
        })

    # The Apple server location is in the Advanced section, the Update Apple Account
    # screen opened from HA Repairs displays it when it is needed
    if (self.is_repair_flow is False
            or Gb.country_code in ['cn', 'hk']
            or Gb.conf_tracking[CONF_SERVER_LOCATION_NEEDED]):
        schema.update({
            vol.Optional(CONF_SERVER_LOCATION,
                    default=utils_cf.option_parm_key(self, CONF_SERVER_LOCATION, APPLE_SERVER_LOCATION_OPTIONS)):
                    utils_cf.select(APPLE_SERVER_LOCATION_OPTIONS, translation_key='server_location', mode='dropdown'),
        })

    schema.update({
        vol.Optional('locate_all',
                    default=locate_all):
                    cv.boolean,
        })

    if self.is_repair_flow:
        return vol.Schema({**schema, **action_field})

    return utils_cf.sectioned_schema(self, schema, [
            (ADVANCED_SECTION, [CONF_SERVER_LOCATION], False),
            ],
            action_field)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           DELETE APPLE ACCOUNT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_delete_apple_acct(self):
    # The devices are kept when iCloud3 devices use the Apple Account, the account's tracked
    # device count is 0 when it is not signed in
    apple_id = self.conf_apple_acct[CONF_APPLE_ACCT]
    devicenames, _ = lists.get_conf_device_names_by_apple_id(apple_id)
    if is_empty(devicenames):
        default_device_action = 'delete_devices'
    elif len(Gb.conf_apple_accounts) > 1:
        default_device_action = 'reassign_devices'
    else:
        default_device_action = 'set_devices_inactive'

    return vol.Schema({
        vol.Required('device_action',
                    default=default_device_action):
                    utils_cf.select(DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS,
                                    translation_key='delete_apple_acct_devices', mode='list'),
        **utils_cf.submit_back_field(self, 'delete_apple_acct', 'cancel_goto_previous',
                                        'the_apple_acct', submit_destination='apple_accounts',
                                        default_action='back'),
        })



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            IMPORT APPLE DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def form_import_apple_devices(self, user_input=None, aa_apple_id=None):
    lists.build_import_apple_devices_selection_list(self)

    imported_aadevices_track           = []
    imported_aadevices_monitor         = []
    imported_aadevices_inactive        = []
    default_imported_aadevices_track   = []
    default_imported_aadevices_monitor = []

    for item_key, sel_line in self.imported_aadevices_sel_list.items():
        tracking_mode = int(item_key[0])
        option_item   = [{"label": sel_line, "value": item_key}]

        match tracking_mode:
            case 0:
                imported_aadevices_track.extend(option_item)
                default_imported_aadevices_track.append(item_key)
            case 1:
                imported_aadevices_monitor.extend(option_item)
                default_imported_aadevices_monitor.append(item_key)
            case 2:
                imported_aadevices_inactive.extend(option_item)

    schema = {}
    if isnot_empty(imported_aadevices_track):
        schema.update({
            vol.Optional('imported_aadevices_track',
                    default=default_imported_aadevices_track):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=imported_aadevices_track,
                        multiple=True, mode='list')),})
    if isnot_empty(imported_aadevices_monitor):
        schema.update({
            vol.Optional('imported_aadevices_monitor',
                    default=default_imported_aadevices_monitor):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=imported_aadevices_monitor,
                        multiple=True, mode='list')),})
    if isnot_empty(imported_aadevices_inactive):
        schema.update({
            vol.Optional('imported_aadevices_inactive',
                    default=[]):
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=imported_aadevices_inactive,
                        multiple=True, mode='list')),})

    # Import is opened from the Devices screen or after an Apple Account is added
    if self.menu_item == 'apple_accounts':
        back_action, back_dest = 'rtn_apple_accounts', 'apple_accounts'
    else:
        back_action, back_dest = 'rtn_device_list', 'device_list'
    schema.update({
        **utils_cf.submit_back_field(self, 'add_imported_apple_devices', back_action,
                                        back_dest, submit_destination='device_list'),})

    return vol.Schema(schema)
