

from ..global_variables import GlobalVariables as Gb
from ..const            import (NOT_HOME_ZONES, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR,
                                IPHONE_DN, IPHONE, IPAD, WATCH, MAC, AIRPODS, ICLOUD, OTHER, HOME, FAMSHR, AUTH_CODE,
                                DEVICE_TYPES, DEVICE_TYPE_DN, DEVICE_TYPE_DNS, DEVICE_TRACKER_DOT,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODES, )
from ..const_config     import (CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCT, CONF_AUTH_METHODS,
                                CURRENT, PUSH, TEXT, TEXT_1, TEXT_2, HWKEY, CONF_APPLE_ACCT,
                                CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE,  CONF_LOCATE_ALL,
                                CONF_TRACK_FROM_ZONES, CONF_PICTURE_WWW_DIRS,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE,
                                CONF_TRACK_FROM_HOME_ZONE, CONF_PICTURE, CONF_DEVICE_TYPE,
                                CONF_INZONE_INTERVALS, CONF_IC3_DEVICENAME, CONF_FNAME,
                                CONF_AADEV_NAME, CONF_MOBILE_APP_DEVICE, CONF_MODEL_DISPLAY_NAME,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL, )
from ..const_char       import (RARROW, CRLF_DOT, DOT, HDOT, CIRCLE_STAR, RED_X,
                                GREEN_ALERT, YELLOW_WARNING, AASEP, )

from ..utils.time_util  import (secs_since, time_now, )
from ..utils.utils      import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                is_statzone, zone_dname, is_between, list_del, list_add,
                                dict_sort_values, apple_user, apple_user, apple_user_dev, apple_id_dev,
                                encode_password, decode_password, )
from ..utils.messaging  import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, )

from ..apple_acct       import apple_acct_support_cf as aascf
from .const_form_lists  import (CF_ALERT, PICTURE_DIR_FILTER, )
from ..startup          import config_file
from ..utils            import file_io
from .                  import utils_cf


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def initialize_lists(self):
    self.icloud_list_text_by_fname      = {}
    self.icloud_list_text_by_fname2     = {}

    # mobile_app device_tracker info used in devices form for mobapp selection
    self.mobapp_list_text_by_entity_id  = {}
    self.picture_by_filename            = {}
    self.zone_name_key_text             = {}
    self.www_directory_list             = []         # www directories for the picture directory filter

    self.device_items_by_devicename     = {}         # List of the devices in the Gb.conf_tracking[device] parameter
    self.apple_acct_items_by_apple_id   = {}         # Selection list for the apple accounts on data_sources screens
    self.apple_acct_auth_items_by_apple_id = {}      # Selection list for the apple accounts reauth screens
    self.aa_auth_methods_by_auth_method = {}         # Authentication methods for an Aple acct
    self.imported_aa_ic3_conf_devices   = {}         # Used on aa_ic3_add_devices screen to add  all unknown aa devices
    self.imported_aadevices_sel_list    = {}         # Used on aa_ic3_add_devices screen to add  all unknown aa devices

    self.away_time_zone_hours_key_text  = {}
    self.away_time_zone_devices_key_text = {}
    self.log_level_devices_key_text     = {}


#--------------------------------------------------------------------
def build_apple_accounts_list(self):
    '''
    Build a list of the Apple Accounts that is used in the data source,
    apple_id/password and reauthentication screens to s select the
    Apple Account or add a new one.

    Parameters:
        include_aadev_names:
            True - Add a list of the devices in the Apple Account and add a
                    new account option


    The list is built:
        - At the start of the forms functions for the Data Sources, Update Apple Acct,
            and Reauth screens
        - When the Apple Acct config is updated
        - When an Apple Acct is deleted
    '''

    self.apple_acct_items_by_apple_id = {}
    self.is_reauth_needed = False
    Gb.conf_apple_acct_cnt = len(Gb.conf_apple_accounts)

    aa_idx = -1
    for conf_apple_acct in Gb.conf_apple_accounts:
        aa_idx += 1
        apple_id = conf_apple_acct[CONF_APPLE_ACCT]
        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

        if aa_idx == 0 and apple_id == '':
            break
        elif AppleAcct is None or apple_id == '':
            continue

        aa_text = _build_aa_text_line(self, AppleAcct, apple_id)
        self.apple_acct_items_by_apple_id[apple_id] = f"{apple_user(apple_id)}{RARROW}{aa_text}"

#...............................................................................
def _build_aa_text_line(self, AppleAcct, apple_id):
    '''
    Build info line for apple acct selection list
    '''

    tracked_cnt, tracked_devices, untracked_cnt, untracked_devices = tracked_untracked_form_msg(apple_id)
    upw_valid = Gb.upw_valid_by_apple_id.get(apple_id, False)
    upw_code  = Gb.upw_code_by_apple_id.get(apple_id, 200)

    aa_text = ''
    if AppleAcct.is_reauth_needed:
        aa_text += f"{CF_ALERT}{utils_cf.tr('auth_needed')} · "
    elif AppleAcct.terms_of_use_update_needed:
        aa_text += f"{CF_ALERT}{utils_cf.tr('auth_terms_of_use_needed')} · "
    elif AppleAcct.auth_failed_503:
        aa_text += f"{CF_ALERT}{utils_cf.tr('aa_status_503')} · "
    elif (tracked_cnt+untracked_cnt) == 0:
        aa_text += f"{CF_ALERT}{utils_cf.tr('aa_status_login_failed_code', code=upw_code)} · "

    aa_text += devices_tracked_text(tracked_cnt, tracked_cnt+untracked_cnt)
    if tracked_devices:
        aa_text += f" ({tracked_devices})"
    return aa_text

def devices_tracked_text(tracked_cnt, device_cnt):
    '''
    2 of 5 devices tracked
    '''
    return utils_cf.tr(f"aa_devices_tracked_{'one' if device_cnt == 1 else 'other'}",
                        tracked=tracked_cnt, total=device_cnt)

#--------------------------------------------------------------------
def build_apple_accounts_auth_list(self):
    '''
    Build a list of the Apple Accounts that is used in the data source,
    apple_id/password and reauthentication screens to s select the
    Apple Account or add a new one.

    Parameters:
        include_aadev_names:
            True - Add a list of the devices in the Apple Account and add a
                    new account option


    The list is built:
        - At the start of the forms functions for the Data Sources, Update Apple Acct,
            and Reauth screens
        - When the Apple Acct config is updated
        - When an Apple Acct is deleted
    '''

    auth_needed_items_by_apple_id = {}
    auth_not_needed_items_by_apple_id = {}
    self.apple_acct_auth_items_by_apple_id = {}
    self.is_reauth_needed = False
    Gb.conf_apple_acct_cnt = len(Gb.conf_apple_accounts)

    aa_idx = -1
    for conf_apple_acct in Gb.conf_apple_accounts:
        aa_idx += 1
        apple_id = conf_apple_acct[CONF_APPLE_ACCT]
        AppleAcct  = Gb.AppleAcct_by_apple_id.get(apple_id)

        if aa_idx == 0 and apple_id == '':
            break
        elif AppleAcct is None or apple_id == '':
            continue

        aa_text = _build_aa_auth_text_line(self, AppleAcct, conf_apple_acct)
        if AppleAcct.is_reauth_needed:
            auth_needed_items_by_apple_id[apple_id] = f"{apple_user(apple_id)} · {aa_text}"
        else:
            auth_not_needed_items_by_apple_id[apple_id] = f"{apple_user(apple_id)} · {aa_text}"

    self.apple_acct_auth_items_by_apple_id = auth_needed_items_by_apple_id
    self.apple_acct_auth_items_by_apple_id.update(auth_not_needed_items_by_apple_id)

#...............................................................................
def _build_aa_auth_text_line(self, AppleAcct, conf_apple_acct):
    build_aa_auth_methods_list(self, AppleAcct)

    if (AppleAcct.current_auth_method in AppleAcct.auth_methods
            and AppleAcct.current_auth_method_value != ''):
        auth_method = AppleAcct.current_auth_method
    else:
        auth_method = PUSH

    aa_text = self.aa_auth_methods_by_auth_method.get(auth_method,
                                self.aa_auth_methods_by_auth_method[PUSH])

    if AppleAcct.terms_of_use_update_needed:
        aa_text += f" · {CF_ALERT}{utils_cf.tr('auth_terms_of_use_needed')}"
    elif AppleAcct.is_reauth_needed:
        aa_text += f" · {CF_ALERT}{utils_cf.tr('auth_needed')}"

    return aa_text

#...............................................................................
def build_aa_auth_methods_list(self, AppleAcct):

    self.aa_auth_methods_by_auth_method = {}
    self.aa_auth_methods_by_auth_method[PUSH] = utils_cf.tr('auth_method_push')

    # Not self.update_auth_method (async, it also writes the config file). This is
    # not async and only needs the auth method updated to build the list.
    if AppleAcct.is_auth_method_PUSH and AppleAcct.hwkey_names != '':
        AppleAcct.update_auth_method(HWKEY)

    for auth_method, method_info in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS].items():
        if method_info == '':
            continue

        if auth_method.startswith(TEXT):
            self.aa_auth_methods_by_auth_method[auth_method] = (
                            utils_cf.tr('auth_method_text', method_info=method_info))

        if auth_method == HWKEY:
            self.aa_auth_methods_by_auth_method[HWKEY] = (
                            utils_cf.tr('auth_method_hwkey', method_info=method_info))

    return self.aa_auth_methods_by_auth_method

#-------------------------------------------------------------------------------------------
def tracked_untracked_form_msg(apple_id):
    '''
    This is used in the config_flow_forms to fill in the tracked and untracked devices
    on the Apple Acct Username Password form
    '''

    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
    if AppleAcct is None:
        return [0, '', 0, '']

    aadev_names = AppleAcct.aadevice_dnames if AppleAcct else []

    devicenames_by_apple_id, aadev_names_by_apple_id = get_conf_device_names_by_apple_id(apple_id)
    tracked_devices = [aadev_name
                            for aadev_name in aadev_names
                            if aadev_name in aadev_names_by_apple_id]
    untracked_devices = [aadev_name
                            for aadev_name in aadev_names
                            if aadev_name not in aadev_names_by_apple_id]

    return [len(tracked_devices), list_to_str(tracked_devices),
            len(untracked_devices), list_to_str(untracked_devices)]

#--------------------------------------------------------------------
def get_conf_device_names_by_apple_id(apple_id):
    '''
    Cycle through the conf_devices and build a list of device names by the
    apple account apple_ids

    Parameter:
        apple_id
    Return:
        {devicenames_by_apple_id}, {aadev_names_by_apple_id}
    '''
    devicenames_by_apple_id = [conf_device[CONF_IC3_DEVICENAME]
                                for conf_device in Gb.conf_devices
                                if conf_device[CONF_APPLE_ACCT] == apple_id]

    aadev_names_by_apple_id = [conf_device[CONF_AADEV_NAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_APPLE_ACCT] == apple_id]

    devicenames_by_apple_id.sort()
    aadev_names_by_apple_id.sort()

    return devicenames_by_apple_id, aadev_names_by_apple_id

#-------------------------------------------------------------------------------------------
def build_devices_list(self):
    '''
    Rebuild the device list for displaying on the devices list form. This is necessary
    since the parameters displayed may have been changed. Update the default values for
    each page for the device selected on each page.
    '''
    self.device_items_by_devicename = {}
    Gb.conf_apple_acct_cnt = len(Gb.conf_apple_accounts)

    # Format all the device info to be listed on the form
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        devicename = devicename.replace(' ', '_')
        self.device_items_by_devicename[devicename] = \
                format_device_list_item(self, conf_device)

    # No devices in config, reset to initial conditions
    if self.device_items_by_devicename == {}:
        self.conf_device_idx  = 0
        return

#-------------------------------------------------------------------------------------------
def format_device_list_item(self, conf_device):
    '''
    Format the text that is displayed for the device on the device_list screen
    (Gary (gary_iphone) → iPhone 16 · Apple: Gary-iPhone · Mobile App: Gary-iPhone)
    '''
    status, model, data_sources, zones = device_info_parts(self, conf_device)
    device_info = [status] if status != utils_cf.tr('dev_status_tracked') else []
    device_info.extend([device_live_status(conf_device)] + data_sources + [model] + zones)

    return (f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]}){RARROW}"
            f"{' · '.join([info for info in device_info if info])}")

#-------------------------------------------------------------------------------------------
def device_info_parts(self, conf_device):
    '''
    The tracking status, model, data sources and zones of a device displayed on the devices
    list and at the top of the device form

    Return:
        status - Tracked, Ⓜ Monitored, 🔸Inactive, 🔸Disabled in HA
        model - iPhone 16
        data_sources - ['Apple: Gary-iPhone', 'Mobile App: Gary-iPhone']
        zones - ['Home override: Cabin', 'Track from: Home, Work'], empty if Home is used
    '''
    if conf_device[CONF_IC3_DEVICENAME] in Gb.ha_disabled_by_by_devicename:
        status = utils_cf.tr('dev_status_disabled')
    elif conf_device[CONF_TRACKING_MODE] == MONITOR:
        status = utils_cf.tr('dev_status_monitored')
    elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
        status = utils_cf.tr('dev_status_inactive')
    else:
        status = utils_cf.tr('dev_status_tracked')

    data_sources = []
    if conf_device[CONF_AADEV_NAME] != 'None':
        _apple_devices_list_key, status_msg = format_apple_acct_device_info(self, conf_device)
        aadev_name = f"{conf_device[CONF_AADEV_NAME]} ({apple_user(conf_device[CONF_APPLE_ACCT])})"
        data_sources.append(utils_cf.tr('dev_source_apple', device=f"{aadev_name}{status_msg}"))

    if conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
        mobapp_dname = conf_device[CONF_MOBILE_APP_DEVICE]
        if mobapp_dname.startswith('ScanFor:'):
            mobapp_device = mobapp_dname
        elif mobapp_dname in Gb.device_info_by_mobapp_dname:
            mobapp_device = Gb.device_info_by_mobapp_dname[mobapp_dname][0]
        else:
            mobapp_device = f"{CF_ALERT}{utils_cf.tr('dev_mobapp_not_found', device=mobapp_dname)}"
        data_sources.append(utils_cf.tr('dev_source_mobapp', device=mobapp_device))

    zones = []
    if conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        zones.append(utils_cf.tr('dev_home_override',
                                    zone=zone_dname(conf_device[CONF_TRACK_FROM_BASE_ZONE])))
    if conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        tfz_fnames = [zone_dname(z) for z in conf_device[CONF_TRACK_FROM_ZONES]]
        zones.append(utils_cf.tr('dev_track_from', zones=list_to_str(tfz_fnames)))

    return status, conf_device[CONF_MODEL_DISPLAY_NAME], data_sources, zones

#-------------------------------------------------------------------------------------------
def device_live_status(conf_device):
    '''
    The zone of a located device and when it was located (Home · located 2 min ago)
    '''
    Device = Gb.Devices_by_devicename.get(conf_device[CONF_IC3_DEVICENAME])
    if (Device is None
            or conf_device[CONF_TRACKING_MODE] == INACTIVE
            or Device.loc_data_secs <= 0):
        return ''

    zone = (utils_cf.tr('dev_zone_away') if Device.loc_data_zone in NOT_HOME_ZONES else
            zone_dname(Device.loc_data_zone))
    # The unit changes where the rounded value reaches the next unit (59.5 min is 1 h)
    secs = secs_since(Device.loc_data_secs)
    if secs < 60:
        located = utils_cf.tr('dev_located_now')
    elif round(secs/60) < 60:
        located = utils_cf.tr('dev_located_mins', mins=round(secs/60))
    elif round(secs/3600) < 24:
        located = utils_cf.tr('dev_located_hrs', hrs=round(secs/3600))
    else:
        located = utils_cf.tr('dev_located_days', days=round(secs/86400))

    return f"{zone} · {located}"

#----------------------------------------------------------------------
def format_apple_acct_device_info(self, conf_device):
    '''
    Format the aadev_name><apple_account field based on the device's
    CONF_AADEV_NAME and CONF_APPLE_ACCOUNT configuration values
    and the status of AppleAcct state and the devices available in AppleAcct

    Input:
        - device confiuration

    Return:
        - aadev_name><apple_account
        - status message

    If this is changed, change the order in
    step_icloud3_device/_resolve_selection_list_items
    '''

    aadev_name  = conf_device[CONF_AADEV_NAME]
    apple_id    = conf_device[CONF_APPLE_ACCT]
    _apple_user = apple_user(apple_id)
    status_msg  = ''

    if AppleAcct := Gb.AppleAcct_by_apple_id.get(apple_id):
        apple_devices_list_key = apple_user_dev(_apple_user, aadev_name)

        if aadev_name in AppleAcct.device_id_by_aadev_dname:
            pass
        elif is_empty(AppleAcct.device_id_by_aadev_dname):
            status_msg = f" {CF_ALERT}{utils_cf.tr('aadev_acct_unavailable')}"
        else:
            status_msg = f" {CF_ALERT}{utils_cf.tr('aadev_not_in_acct')}"

    elif self._is_apple_acct_setup() is False:
        apple_devices_list_key = apple_user_dev('NO.APPLE.ACCTS', aadev_name)
        status_msg = f" {CF_ALERT}{utils_cf.tr('aadev_no_apple_accts')}"

    elif instr(self.data_source, ICLOUD) is False:
        apple_devices_list_key = apple_user_dev(_apple_user, aadev_name)
        status_msg = f" {CF_ALERT}{utils_cf.tr('aadev_data_source_off')}"
    else:
        apple_devices_list_key = apple_user_dev(_apple_user, aadev_name)
        status_msg = f" {CF_ALERT}{utils_cf.tr('aadev_unknown_apple_acct')}"

    return apple_devices_list_key, status_msg

#----------------------------------------------------------------------
async def build_update_device_selection_lists(self, selected_devicename=None):
    '''
    Setup the option lists used to select device parameters

    Parameter:
        selected_device - The iC3 devicename being added or updated on the Update
            Devices screen. This is used to highlight the selected device and
            place it at the top of the finddev device list
    '''

    try:
        await build_icloud_device_selection_list(self, selected_devicename)
        await build_mobapp_entity_selection_list(self, selected_devicename)
        await build_picture_filename_selection_list(self)
        await build_zone_selection_list(self)

    except Exception as err:
        log_exception(err)

#----------------------------------------------------------------------
async def build_icloud_device_selection_list(self, selected_devicename=None):
    '''
    This creates the list of devices used on the update devices screen
    '''
    self.icloud_list_text_by_fname2 = {}
    all_devices_available = {}
    all_devices_not_available = {}
    all_devices_used = {}
    all_devices_this_device = {}
    all_devices_unknown_device = {}
    apple_id_hdr_available = {}
    selected_device_aadev_name = 'None' if is_empty(Gb.conf_devices) else ''
    selected_device_apple_acct = None

    # Get the list of devices with unknown apple accts
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if conf_device[CONF_AADEV_NAME] == 'None':
            continue

        # aadev_name_apple_id, status_msg = \
        apple_id_aadev_name, status_msg = \
                    format_apple_acct_device_info(self, conf_device)

        if status_msg == '':
            continue

        apple_id = conf_device[CONF_APPLE_ACCT] if conf_device[CONF_APPLE_ACCT] != '' else 'NONE'
        device_list_item_key = apple_id_dev(apple_id, devicename)
        all_devices_not_available[device_list_item_key] = (
                    f" ⊘ {apple_id_aadev_name}{AASEP}{apple_user(apple_id)}{status_msg}")

        # Save the FamShr config parameter in case it is not found
        if devicename == selected_devicename:
            selected_device_apple_acct = conf_device[CONF_APPLE_ACCT]
            selected_device_aadev_name  = conf_device[CONF_AADEV_NAME]

    aa_idx = 0
    for conf_apple_account in Gb.conf_apple_accounts:
        apple_id = conf_apple_account[CONF_APPLE_ACCT]
        aa_idx += 1
        aa_idx_dots = '.'*aa_idx

        if Gb.upw_valid_by_apple_id.get(apple_id, False) is False:
            continue

        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
        if AppleAcct is None:
            continue

        devices_available, devices_used, devices_not_available, this_device, longest_aa_line_len = \
                get_icloud_devices_list_avail_used_this(
                        aa_idx, AppleAcct, AppleAcct.account_owner, selected_devicename)


        # Available devices
        devices_cnt  = len(devices_used) + len(devices_available) + len(this_device)
        assigned_cnt = len(devices_used) + len(this_device)

        #🍏 ⛔ 🍎
        apple_id_hdr_available = {f"{aa_idx_dots}hdr": _list_hdr('aadev_list_acct_hdr',
                                    owner=AppleAcct.account_owner, user=AppleAcct.apple_user,
                                    assigned=assigned_cnt, total=devices_cnt)}

        if devices_available == {}:
            devices_available ={f".nodev": f" ⊘ {utils_cf.tr('aadev_list_all_assigned')}"}

        all_devices_available.update(apple_id_hdr_available)
        all_devices_available.update(devices_available)
        all_devices_used.update(devices_used)
        all_devices_not_available.update(devices_not_available)
        all_devices_this_device.update(this_device)

    # This device item line
    if isnot_empty(all_devices_this_device):
        self.icloud_list_text_by_fname2.update(all_devices_this_device)

    self.icloud_list_text_by_fname2.update({'None': utils_cf.tr('aadev_none')})

    if isnot_empty(all_devices_available):
        self.icloud_list_text_by_fname2.update(all_devices_available)

    if 1==1 or isnot_empty(all_devices_used):
        self.icloud_list_text_by_fname2.update({".assigned": _list_hdr('aadev_list_assigned_hdr')})

        self.icloud_list_text_by_fname2.update(dict_sort_values(all_devices_used))

    if isnot_empty(all_devices_not_available):
        self.icloud_list_text_by_fname2.update({".notavail": _list_hdr('aadev_list_not_available_hdr')})

        self.icloud_list_text_by_fname2.update(dict_sort_values(all_devices_not_available))

    self.icloud_list_text_by_fname = self.icloud_list_text_by_fname2.copy()

#----------------------------------------------------------------------
def get_icloud_devices_list_avail_used_this(aa_idx, AppleAcct, apple_acct_owner,
                                                selected_devicename=None):
    '''
    Build the dictionary with the Apple Account devices

    Return:
        [devices_available, devices_used, devices_this_device]
    '''
    this_device = {}
    devices_available = {}
    devices_used = {}
    devices_not_available = {}
    unknown_devices = {}
    available_family = {}
    available_owner = {}
    aa_idx_msg  = f"#{aa_idx} - "
    aa_idx_dots = '.'*aa_idx
    longest_line_len = 0

    devices_assigned = {}
    selected_device_aadev_name = ''
    for _conf_device in Gb.conf_devices:
        devicename  = _conf_device[CONF_IC3_DEVICENAME]
        aadev_name = _conf_device[CONF_AADEV_NAME]
        apple_id  = _conf_device[CONF_APPLE_ACCT]
        if (aadev_name == 'None'
                or AppleAcct.apple_id != apple_id):
            continue

        devices_assigned[aadev_name] = devicename
        devices_assigned[devicename]  = aadev_name

    try:
        for aadev_name, device_model in AppleAcct.device_model_name_by_aadev_dname.items():
            device_id = AppleAcct.device_id_by_aadev_dname[aadev_name]
            AADev = AppleAcct.AADev_by_device_id[device_id]
            conf_apple_acct, conf_aa_idx = config_file.conf_apple_acct(AppleAcct.apple_id)
            family_device = f", {utils_cf.tr('aadev_family_device')}" if AADev.family_share_device else ''
            if family_device and conf_apple_acct[CONF_LOCATE_ALL] is False:
                family_device = utils_cf.tr('aadev_family_device_not_located')

            device_list_item_key  = apple_id_dev(AppleAcct.apple_id, aadev_name)
            _apple_user_device   = apple_user_dev(AppleAcct.apple_user, aadev_name)
            aadev_name_owner       = apple_id_dev(AppleAcct.account_owner, aadev_name)
            aadev_name_owner_model = f"{aadev_name_owner}{family_device}, {device_model}"
            fam_device_model      = f"{family_device}, {device_model}"
            aadev_startup_msg     = f", {CF_ALERT}{AADev.startup_msg}" if AADev.startup_msg else ''

            # If not assigned to an ic3 device
            if aadev_name not in devices_assigned:
                item_line = (f" • {_apple_user_device}{family_device}, "
                            f"{device_model}"
                            f"{aa_idx_dots}"
                            f"{aadev_startup_msg}")
                available_family[device_list_item_key] = item_line
                if len(item_line) > longest_line_len: longest_line_len = len(item_line)
                continue

            # This device
            devicename = devices_assigned[aadev_name]
            if devicename == selected_devicename:
                item_line = (f"{_apple_user_device}{family_device}, "
                            f"{device_model}"
                            f"{aa_idx_dots}")
                this_device[device_list_item_key] = item_line
                if len(item_line) > longest_line_len: longest_line_len = len(item_line)
                continue

            # Assigned to another device
            _assigned_to_fname = icloud_device_assigned_to(AppleAcct, aadev_name)
            item_line = (f" ⊘ {_apple_user_device}{RARROW}"
                        f"{_assigned_to_fname}{family_device}, "
                        f"{device_model}")
            devices_used[device_list_item_key] = item_line
            if len(item_line) > longest_line_len: longest_line_len = len(item_line)

    except Exception as err:
        log_exception(err)

    devices_available.update(dict_sort_values(available_owner))
    devices_available.update(dict_sort_values(available_family))
    devices_not_available.update(dict_sort_values(unknown_devices))

    return (devices_available, devices_used, devices_not_available,
            this_device, longest_line_len)

#----------------------------------------------------------------------
def icloud_device_assigned_to(AppleAcct, aadev_name):
    _assigned_to_fname = [f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]})"
                            for conf_device in Gb.conf_devices
                            if (AppleAcct.apple_id == conf_device[CONF_APPLE_ACCT]
                                    and aadev_name == conf_device[CONF_AADEV_NAME])]

    if _assigned_to_fname:
        return _assigned_to_fname[0]
    else:
        return ''

#----------------------------------------------------------------------
async def build_mobapp_entity_selection_list(self, selected_devicename=None):
    '''
    Cycle through the /config/.storage/core.entity_registry file and return
    the entities for platform ('mobile_app', etc)

    Gb.devicenames_by_mobapp_dname={'gary_iphone_app': 'gary_iphone', 'Gary-iPhone-MobApp': 'gary_iphone'}
    Gb.device_info_by_mobapp_dname={'gary_iphone_app': ['Gary-iPhone-MobApp', 'iPhone17,2', 'iPhone', 'iPhone 16 Pro Max'], ...
    mobapp_devices={'gary_iphone_app': 'Gary-iPhone-MobApp (iPhone17,2); device_tracker.gary_iphone_app'}
    '''

    devices_this_device = {}
    devices_available = {}
    devices_used = {}
    scan_for_mobapp_devices = {}
    self.mobapp_list_text_by_entity_id = {}

    Gb.devicenames_by_mobapp_dname = {}
    Gb.mobapp_dnames_by_devicename = {}
    for _conf_device in Gb.conf_devices:
        devicename = _conf_device[CONF_IC3_DEVICENAME]
        if _conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
            Gb.devicenames_by_mobapp_dname[_conf_device[CONF_MOBILE_APP_DEVICE]] = devicename
            Gb.mobapp_dnames_by_devicename[devicename] = _conf_device[CONF_MOBILE_APP_DEVICE]


    # Build line for all devices (this, available, assigned)
    mobapp_devices ={mobapp_dname:(
                        f" • {mobapp_info[0]} "
                        f"(device_tracker.{mobapp_dname}), "
                        f"{mobapp_info[3]}")
                        for mobapp_dname, mobapp_info in Gb.device_info_by_mobapp_dname.items()}

    for mobapp_dname, mobapp_info in mobapp_devices.items():
        if mobapp_dname not in Gb.devicenames_by_mobapp_dname:
            devices_available[mobapp_dname] = mobapp_info
            continue

        # Get this device
        if (selected_devicename
                and mobapp_dname == self.conf_device[CONF_MOBILE_APP_DEVICE]):
            devices_this_device[mobapp_dname] = mobapp_info[3:]
            continue

        else:
            devicename = Gb.devicenames_by_mobapp_dname[mobapp_dname]
            Device = Gb.Devices_by_devicename.get(devicename)
            if Device:
                fname_devicename = Device.fname_devicename
            elif devicename in Gb.inactive_fname_by_devicename:
                fname_devicename = (f"{Gb.inactive_fname_by_devicename[devicename]} "
                                    f"({utils_cf.tr('dev_status_inactive')})")
            else:
                fname_devicename = f"{CF_ALERT}{devicename} ({utils_cf.tr('unknown')})"

            mobapp_info = f" ⊘ {mobapp_info[2:]}"
            devices_used[mobapp_dname] = (
                        f"{mobapp_info.split(';')[0]}{RARROW}{fname_devicename}")

    try:
        scan_for_mobapp_devices = {
                    f"ScanFor: {_conf_device[CONF_IC3_DEVICENAME]}": (
                    f" • {utils_cf.tr('mobapp_scan_for', devicename=_conf_device[CONF_IC3_DEVICENAME])}")
                        for _conf_device in Gb.conf_devices}

    except Exception as err:
        # log_exception(err)
        scan_for_mobapp_devices = {}

    if devices_available == {}:
        devices_available = {f"nodev": f" ⊘ {utils_cf.tr('mobapp_all_assigned')}"}
    if (selected_devicename
            and is_empty(devices_this_device)
            and self.conf_device[CONF_MOBILE_APP_DEVICE] != 'None'
            and self.conf_device[CONF_MOBILE_APP_DEVICE].startswith('ScanFor:') is False):
        devices_this_device = {'.unknown':
                f"{CF_ALERT}{self.conf_device[CONF_MOBILE_APP_DEVICE]}{RARROW}"
                f"{utils_cf.tr('mobapp_unknown_device')}"}

    if isnot_empty(devices_this_device):
        self.mobapp_list_text_by_entity_id.update(devices_this_device)
    self.mobapp_list_text_by_entity_id.update({'None': utils_cf.tr('mobapp_none')})
    self.mobapp_list_text_by_entity_id.update({'.available': _list_hdr('mobapp_list_available_hdr')})
    self.mobapp_list_text_by_entity_id.update(dict_sort_values(devices_available))
    self.mobapp_list_text_by_entity_id.update({'.assigned': _list_hdr('mobapp_list_assigned_hdr')})
    self.mobapp_list_text_by_entity_id.update(dict_sort_values(devices_used))
    self.mobapp_list_text_by_entity_id.update({'.scanfor': _list_hdr('mobapp_list_scan_for_hdr')})
    self.mobapp_list_text_by_entity_id.update(dict_sort_values(scan_for_mobapp_devices))

    return

#-------------------------------------------------------------------------------------------
async def build_www_directory_filter_list(self):
    '''
    Set up the list of all www directories for selecting those that should be filteredd
    '''

    if self.www_directory_list == []:
        start_dir = 'www'
        self.www_directory_list = await Gb.hass.async_add_executor_job(
                                                file_io.get_directory_list,
                                                start_dir)

#-------------------------------------------------------------------------------------------
async def build_picture_filename_selection_list(self):

    try:
        if self.picture_by_filename != {}:
            return

        start_dir = 'www'
        file_filter = ['png', 'jpg', 'jpeg']
        image_filenames = await Gb.hass.async_add_executor_job(
                                                file_io.get_directory_filename_list,
                                                start_dir,
                                                file_filter)

        await build_www_directory_filter_list(self)

        # Make sure all directories in the filter list still exist,
        # delete it if it does not exist
        www_gb_dirs_unknown = [dir  for dir in Gb.picture_www_dirs
                                    if dir not in self.www_directory_list]
        if isnot_empty(www_gb_dirs_unknown):
            for www_gb_dir_unknown in www_gb_dirs_unknown:
                list_del(Gb.picture_www_dirs, www_gb_dir_unknown)
            Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = Gb.picture_www_dirs

        if Gb.www_evlog_js_directory not in Gb.picture_www_dirs:
            list_add(Gb.picture_www_dirs, Gb.www_evlog_js_directory)

        sorted_image_filenames = []
        over_25_warning_msgs = []
        for image_filename in image_filenames:
            if image_filename.startswith('⛔'):
                over_25_warning_msgs.append(image_filename)
            else:
                sorted_image_filenames.append(f"{image_filename.rsplit('/', 1)[1]}:{image_filename}")
        sorted_image_filenames.sort()
        self.picture_by_filename = {}
        www_dir_idx = 0


        if Gb.picture_www_dirs:
            while www_dir_idx < len(Gb.picture_www_dirs):
                self.picture_by_filename[f".www_dirs{www_dir_idx}"] = "ⓘ " + utils_cf.tr(
                            'picture_dirs', dirs=list_to_str(Gb.picture_www_dirs[www_dir_idx:www_dir_idx+3]))
                www_dir_idx += 3

        for over_25_warning_msg in over_25_warning_msgs:
            www_dir_idx += 1
            self.picture_by_filename[f".www_dirs{www_dir_idx}"] = \
                            f"{CF_ALERT}{over_25_warning_msg.lstrip('⛔ ')}"

        self.picture_by_filename[PICTURE_DIR_FILTER] = f"▶ {utils_cf.tr('picture_dir_filter')}"
        self.picture_by_filename['.available'] = _list_hdr('picture_list_file_names_hdr')
        self.picture_by_filename['None'] = utils_cf.tr('picture_none')

        for sorted_image_filename in sorted_image_filenames:
            image_filename, image_filename_path = sorted_image_filename.split(':')
            self.picture_by_filename[image_filename_path] = \
                        f"{image_filename}{RARROW}{image_filename_path.replace(image_filename, '')}"

    except Exception as err:
        log_exception(err)

#-------------------------------------------------------------------------------------------
async def build_zone_selection_list(self):

    if self.zone_name_key_text != {}:
        return

    fname_zones = []
    for zone, Zone in Gb.HAZones_by_zone.items():
        if is_statzone(zone):
            continue

        passive_msg = ' (Passive)' if Zone.passive else ''
        fname_zones.append(f"{Zone.dname}{passive_msg}|{zone}")

    fname_zones.sort()

    self.zone_name_key_text = {'home': 'Home'}

    for fname_zone in fname_zones:
        fname, zone = fname_zone.split('|')
        self.zone_name_key_text[zone] = fname

#-------------------------------------------------------------------------------------------
def build_away_time_zone_hours_list(self):
    time_hhmmss = time_now()
    ha_time = int(time_hhmmss[0:2])
    for hh in range(ha_time-12, ha_time+13):
        away_hh = hh + 24 if hh < 0 else hh

        if   away_hh == 0: ap_hh = 12; ap = 'a'
        elif away_hh < 12:  ap_hh = away_hh; ap = 'a'
        elif away_hh == 12: ap_hh = 12; ap = 'p'
        else: ap_hh = away_hh - 12; ap = 'p'

        if away_hh >= 24:
            away_hh -= 24
            if   ap_hh == 12: ap = 'a'
            elif ap_hh >= 13: ap_hh -= 12; ap = 'a'

        if Gb.time_format_12_hour:
            time_str = f"{ap_hh:}{time_hhmmss[2:5]}{ap}"
        else:
            time_str = f"{away_hh:02}{time_hhmmss[2:5]}"

        if away_hh == ha_time:
            time_str = utils_cf.tr('away_time_zone_home')
        else:
            time_str = utils_cf.tr('away_time_zone_hours', time=time_str, hours=f"{hh-ha_time:+}")
        self.away_time_zone_hours_key_text[hh-ha_time] = time_str

#-------------------------------------------------------------------------------------------
def build_away_time_zone_devices_list(self):

    self.away_time_zone_devices_key_text = {'none': utils_cf.tr('away_time_zone_not_used'),
                                            'all':  utils_cf.tr('away_time_zone_all_devices')}
    self.away_time_zone_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def build_log_level_devices_list(self):

    self.log_level_devices_key_text = {'all': utils_cf.tr('log_level_all_devices')}
    self.log_level_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def _list_hdr(key, **placeholders):
    '''
    The heading row of a group of a selection list (Available Mobile App devices:)
    '''
    return f"{utils_cf.tr(key, **placeholders)}:"

#-------------------------------------------------------------------------------------------
def devices_selection_list():
    status_key = {TRACK: 'dev_status_tracked', MONITOR: 'dev_status_monitored',
                    INACTIVE: 'dev_status_inactive'}
    return {conf_device[CONF_IC3_DEVICENAME]: (
                    f"{conf_device[CONF_FNAME]} "
                    f"({DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}), "
                    f"{utils_cf.tr(status_key.get(conf_device[CONF_TRACKING_MODE], 'dev_status_tracked'))}")
                for conf_device in Gb.conf_devices
                if conf_device[CONF_IC3_DEVICENAME] in Gb.Devices_by_devicename}


#-------------------------------------------------------------------------------------------
def build_import_apple_devices_selection_list(self):
    '''
    Build the selection list for importing Apple Devices. This includes all items with an item
    key that is used for sorting the list and separating the items into tracked, monitored and
    inactive selection categories.

    item_key = 0,05,Gary-AirPods where:
                Tracking_mode: position in ['track', 'monitor', 'inactive]
                DeviceType   : Position in CONF_MODEL_DISPLAY_NAME
                AppleFName   : Gary-AirPods
    '''
    self.imported_aadevices_sel_list  = {}
    self.imported_aa_ic3_conf_devices = {}
    for AppleAcct in Gb.AppleAcct_by_apple_id.values():
        self.imported_aa_ic3_conf_devices.update(
                        aascf.build_import_devices_config_from_aadevices(self, AppleAcct))

    for sort_key, ic3_conf_device in self.imported_aa_ic3_conf_devices.items():
        apple_id   = ic3_conf_device[CONF_APPLE_ACCT]
        aadev_name  = ic3_conf_device[CONF_AADEV_NAME]
        mobapp_dname = ic3_conf_device.get(CONF_MOBILE_APP_DEVICE)

        sel_line = f"{ic3_conf_device[CONF_FNAME]} ({ic3_conf_device[CONF_IC3_DEVICENAME]}){RARROW}"
        sel_line += (f"{ic3_conf_device[CONF_MODEL_DISPLAY_NAME]} · "
                     f"{utils_cf.tr('dev_source_apple', device=apple_user_dev(apple_id, aadev_name))}")
        if mobapp_dname != 'None':
            sel_line += (" · " + utils_cf.tr('dev_source_mobapp',
                                    device=Gb.device_info_by_mobapp_dname[mobapp_dname][0]))

        self.imported_aadevices_sel_list[sort_key] = sel_line
