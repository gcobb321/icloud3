

from ..global_variables import GlobalVariables as Gb
from ..const            import (RARROW, CRLF_DOT, DOT, HDOT, CIRCLE_STAR, RED_X, INACTIVE_SYMB, MONITOR_SYMB,
                                YELLOW_ALERT, RED_ALERT, YELLOW_WARNING,
                                EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LINK, LLINK, RLINK, LCBRACE, RCBRACE,
                                IPHONE_DN, IPHONE, IPAD, WATCH, MAC, AIRPODS, ICLOUD, OTHER, HOME, FAMSHR,
                                DEVICE_TYPES, DEVICE_TYPE_DN, DEVICE_TYPE_DNS, DEVICE_TRACKER_DOT,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODE_DN, TRACKING_MODES,
                                CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCOUNT,
                                CONF_AUTH_METHODS, CURRENT,
                                PUSH, TEXT, TEXT_1, TEXT_2, HWKEY,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE, CONF_AUTH_CODE, CONF_LOCATE_ALL,
                                CONF_TRACK_FROM_ZONES, CONF_PICTURE_WWW_DIRS,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_MODEL_DISPLAY_NAME,
                                CONF_TRACKING_MODE, TRACKING_MODE_DN,
                                CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                )

from ..utils.utils      import (instr, is_number, is_empty, isnot_empty, list_to_str, str_to_list,
                                is_statzone, zone_dname, is_between, list_del, list_add,
                                sort_dict_by_values, username_id, username_base,
                                encode_password, decode_password, )
from ..utils.messaging  import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, )

from ..apple_acct       import apple_acct_support_cf as aascf
from .const_form_lists  import (NONE_FAMSHR_DICT_KEY_TEXT, MOBAPP_DEVICE_NONE_OPTIONS, AWAY_FROM_ZONE_OPTIONS,
                                REAUTH_AUTH_METHODS, )
from ..startup          import config_file
from ..utils            import file_io


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def build_apple_accounts_list(self):
    '''
    Build a list of the Apple Accounts that is used in the data source,
    username/password and reauthentication screens to s select the
    Apple Account or add a new one.

    Parameters:
        include_aadevice_dnames:
            True - Add a list of the devices in the Apple Account and add a
                    new account option


    The list is built:
        - At the start of the forms functions for the Data Sources, Update Apple Acct,
            and Reauth screens
        - When the Apple Acct config is updated
        - When an Apple Acct is deleted
    '''

    self.apple_acct_items_by_username = {}
    self.is_reauth_needed = False

    aa_idx = -1
    for conf_apple_acct in Gb.conf_apple_accounts:
        aa_idx += 1
        username = conf_apple_acct[CONF_USERNAME]
        AppleAcct = Gb.AppleAcct_by_username.get(username)

        if aa_idx == 0 and username == '':
            break
        elif AppleAcct is None or username == '':
            continue

        aa_text = _build_aa_text_line(self, AppleAcct, username)
        self.apple_acct_items_by_username[username] = f"{username_base(username)}{RARROW}{aa_text}"

#...............................................................................
def _build_aa_text_line(self, AppleAcct, username):
    '''
    Build info line for apple acct selection list
    '''

    tracked_cnt, tracked_devices, untracked_cnt, untracked_devices = tracked_untracked_form_msg(username)
    valid_upw = Gb.valid_upw_by_username.get(username)

    aa_text = ''
    if AppleAcct.is_reauth_needed:
        aa_text += f"{RED_ALERT}AUTH NEEDED, "
    elif AppleAcct.auth_failed_503:
        aa_text += f"{RED_ALERT}APPLE REFUSED RQST-503, "
    elif (tracked_cnt+untracked_cnt) == 0:
        aa_text += f"{RED_ALERT}LOGIN FAILED, "

    aa_text += (f"{tracked_cnt} of "
                f"{tracked_cnt+untracked_cnt} Devices Tracked "
                f"({tracked_devices})")
    return aa_text

#--------------------------------------------------------------------
def build_apple_accounts_auth_list(self):
    '''
    Build a list of the Apple Accounts that is used in the data source,
    username/password and reauthentication screens to s select the
    Apple Account or add a new one.

    Parameters:
        include_aadevice_dnames:
            True - Add a list of the devices in the Apple Account and add a
                    new account option


    The list is built:
        - At the start of the forms functions for the Data Sources, Update Apple Acct,
            and Reauth screens
        - When the Apple Acct config is updated
        - When an Apple Acct is deleted
    '''

    auth_needed_items_by_username = {}
    auth_not_needed_items_by_username = {}
    self.apple_acct_auth_items_by_username = {}
    self.is_reauth_needed = False

    aa_idx = -1
    for conf_apple_acct in Gb.conf_apple_accounts:
        aa_idx += 1
        aausername = conf_apple_acct[CONF_USERNAME]
        AppleAcct  = Gb.AppleAcct_by_username.get(aausername)

        if aa_idx == 0 and aausername == '':
            break
        elif AppleAcct is None or aausername == '':
            continue

        aa_text = _build_aa_auth_text_line(self, AppleAcct, conf_apple_acct)
        if AppleAcct.is_reauth_needed:
            auth_needed_items_by_username[aausername] = \
                f"{username_base(aausername)}{RARROW}{aa_text}"
        else:
            auth_not_needed_items_by_username[aausername] = \
                f"{username_base(aausername)}{RARROW}{aa_text}"

    self.apple_acct_auth_items_by_username = auth_needed_items_by_username
    self.apple_acct_auth_items_by_username.update(auth_not_needed_items_by_username)

#...............................................................................
def _build_aa_auth_text_line(self, AppleAcct, conf_apple_acct):
    build_aa_auth_methods_list(self, AppleAcct)

    aa_text = ''
    if (AppleAcct.current_auth_method in AppleAcct.auth_methods
            and AppleAcct.current_auth_method_value != ''):
        auth_method = AppleAcct.current_auth_method
    else:
        auth_method = PUSH

    aa_text += f"{self.aa_auth_methods_by_auth_method[auth_method]}"

    if AppleAcct.is_reauth_needed:
        aa_text = aa_text.split('> ')[0]
        aa_text += f" {RED_ALERT}AUTH NEEDED"

    return aa_text

#...............................................................................
def build_aa_auth_methods_list(self, AppleAcct):

    self.aa_auth_methods_by_auth_method = {}
    self.aa_auth_methods_by_auth_method[PUSH] = REAUTH_AUTH_METHODS[PUSH]

    if AppleAcct.is_auth_method_PUSH and AppleAcct.hwkey_names != '':
        self.update_auth_method(HWKEY)

    for auth_method, method_info in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS].items():
        if method_info == '':
            continue

        if auth_method.startswith(TEXT):
            self.aa_auth_methods_by_auth_method[auth_method] = (
                            REAUTH_AUTH_METHODS[TEXT].replace('{method_info}', method_info))

        if auth_method == HWKEY:
            self.aa_auth_methods_by_auth_method[HWKEY] = (
                            REAUTH_AUTH_METHODS[HWKEY].replace('{method_info}', method_info))

    return self.aa_auth_methods_by_auth_method

#-------------------------------------------------------------------------------------------
def tracked_untracked_form_msg(aausername):
    '''
    This is used in the config_flow_forms to fill in the tracked and untracked devices
    on the Apple Acct Username Password form
    '''

    AppleAcct = Gb.AppleAcct_by_username.get(aausername)
    if AppleAcct is None:
        return [0, '', 0, '']

    aadevice_dnames = AppleAcct.aadevice_dnames if AppleAcct else []

    devicenames_by_username, aadevice_dnames_by_username = get_conf_device_names_by_username(aausername)
    tracked_devices = [aadevice_dname
                            for aadevice_dname in aadevice_dnames
                            if aadevice_dname in aadevice_dnames_by_username]
    untracked_devices = [aadevice_dname
                            for aadevice_dname in aadevice_dnames
                            if aadevice_dname not in aadevice_dnames_by_username]

    return [len(tracked_devices), list_to_str(tracked_devices),
            len(untracked_devices), list_to_str(untracked_devices)]

#--------------------------------------------------------------------
def get_conf_device_names_by_username(aausername):
    '''
    Cycle through the conf_devices and build a list of device names by the
    apple account usernames

    Parameter:
        username
    Return:
        {devicenames_by_username}, {aadevice_dnames_by_username}
    '''
    devicenames_by_username = [conf_device[CONF_IC3_DEVICENAME]
                                for conf_device in Gb.conf_devices
                                if conf_device[CONF_APPLE_ACCOUNT] == aausername]

    aadevice_dnames_by_username = [conf_device[CONF_FAMSHR_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_APPLE_ACCOUNT] == aausername]

    devicenames_by_username.sort()
    aadevice_dnames_by_username.sort()

    return devicenames_by_username, aadevice_dnames_by_username

#-------------------------------------------------------------------------------------------
def build_devices_list(self):
    '''
    Rebuild the device list for displaying on the devices list form. This is necessary
    since the parameters displayed may have been changed. Update the default values for
    each page for the device selected on each page.
    '''
    self.device_items_by_devicename = {}

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
    '''
    device_text  = (f"{conf_device[CONF_FNAME]}"
                    f" ({conf_device[CONF_IC3_DEVICENAME]}){RARROW}")

    if conf_device[CONF_TRACKING_MODE] == MONITOR:
        device_text += f"{MONITOR_SYMB} MONITOR, "
    elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
        device_text += f"{INACTIVE_SYMB}INACTIVE, "

    if conf_device[CONF_FAMSHR_DEVICENAME] != 'None':
        aadevice_dname_aausername, status_msg = \
                        format_apple_acct_device_info(self, conf_device)
        device_text += (f"AppleDevice–"
                        f"({aadevice_dname_aausername}){status_msg}, ")

    if conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
        mobapp_dname = conf_device[CONF_MOBILE_APP_DEVICE]
        device_text += "MobApp–"
        if mobapp_dname.startswith('ScanFor:'):
            device_text += f"({mobapp_dname}), "
        elif mobapp_dname in Gb.device_info_by_mobapp_dname:
            device_text += f"({Gb.device_info_by_mobapp_dname[mobapp_dname][0]}), "
        else:
            device_text += f"){mobapp_dname} {RED_ALERT}UNKNOWN MOBAPP ENTITY), "

    device_text += f"{conf_device[CONF_MODEL_DISPLAY_NAME]}, "

    if conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        tfhbz = conf_device[CONF_TRACK_FROM_BASE_ZONE]
        device_text +=  f"PrimaryHomeZone–({zone_dname(tfhbz)}), "

    if conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        tfz_fnames = [zone_dname(z) for z in conf_device[CONF_TRACK_FROM_ZONES]]
        device_text +=  f"TrackFromZones–({list_to_str(tfz_fnames)}), "

    # device_text = device_text.replace(' , ', ' ')
    if device_text.endswith(', '): device_text = device_text[:-2]

    return device_text

#----------------------------------------------------------------------
def format_apple_acct_device_info(self, conf_device):
    '''
    Format the aadevice_dname><apple_account field based on the device's
    CONF_FAMSHR_DEVICENAME and CONF_APPLE_ACCOUNT configuration values
    and the status of AppleAcct state and the devices available in AppleAcct

    Input:
        - device confiuration

    Return:
        - aadevice_dname><apple_account
        - status message
    '''

    aadevice_dname = conf_device[CONF_FAMSHR_DEVICENAME]
    aausername     = conf_device[CONF_APPLE_ACCOUNT]
    # aausername_base = f"{aausername}@".split('@')[0]
    status_msg   = ''

    if AppleAcct := Gb.AppleAcct_by_username.get(aausername):
        # aadevice_dname_aausername = f"{aadevice_dname}{AppleAcct.account_owner_link}"
        aadevice_dname_aausername = f"{aadevice_dname}{LINK}{username_id(aausername)}"
        if aadevice_dname in AppleAcct.device_id_by_icloud_dname:
            pass
        elif is_empty(AppleAcct.device_id_by_icloud_dname):
            status_msg = f" {RED_ALERT}APPLE ACCT UNAVAILABLE"
        else:
            status_msg = f" {RED_ALERT}`{aadevice_dname}` DEVICE NOT IN APPLE ACCT"

    elif self._is_apple_acct_setup() is False:
        aadevice_dname_aausername = f"{aadevice_dname}{LINK}NOAPPLEACCTS"
        status_msg = f" {RED_ALERT}NO APPLE ACCTS SET UP"

    elif instr(self.data_source, ICLOUD) is False:
        aadevice_dname_aausername = f"{aadevice_dname}{LINK}{username_id(aausername)}"
        status_msg = f" {RED_ALERT}APPLE DATA SOURCE DISABLED"
    else:
        aadevice_dname_aausername = f"{aadevice_dname}{LINK}{username_id(aausername)}"
        status_msg = f" {RED_ALERT}UNKNOWN APPLE ACCT"

    return aadevice_dname_aausername, status_msg

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
    Create the iCloud object if it does not exist. This will create the
    icloud_info_by_icloud_dname that contains the fname and device info dictionary.
    Then sort this by the lower case fname values so the uppercase items (Watch)
    are not listed before the lower case ones (iPhone).

    This creates the list of devices used on the update devices screen
    '''
    self.icloud_list_text_by_fname2 = {}
    all_devices_available = {}
    all_devices_not_available = {}
    all_devices_used = {}
    all_devices_this_device = {}
    all_devices_unknown_device = {}
    username_hdr_available = {}
    selected_device_aadevice_dname = 'None' if is_empty(Gb.conf_devices) else ''
    selected_device_apple_acct = None

    # Get the list of devices with unknown apple accts
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if conf_device[CONF_FAMSHR_DEVICENAME] == 'None':
            continue

        aadevice_dname_aausername, status_msg = \
                    format_apple_acct_device_info(self, conf_device)

        if status_msg == '':
            continue

        aausername = conf_device[CONF_APPLE_ACCOUNT] if conf_device[CONF_APPLE_ACCOUNT] != '' else 'NONE'
        device_list_item_key = f"{devicename}{LINK}{aausername}"
        all_devices_not_available[device_list_item_key] = (
                    f"{conf_device[CONF_FNAME]} ({devicename}) > "
                    f"{aadevice_dname_aausername}{status_msg}")

        # Save the FamShr config parameter in case it is not found
        if devicename == selected_devicename:
            selected_device_apple_acct   = conf_device[CONF_APPLE_ACCOUNT]
            selected_device_aadevice_dname = conf_device[CONF_FAMSHR_DEVICENAME]

    max_len_aa_owner_msg = 0
    for _AppleAcct in Gb.AppleAcct_by_username.values():
        aa_owner_msg = f"{_AppleAcct.account_owner} ({_AppleAcct.username_base})"
        if len(aa_owner_msg) > max_len_aa_owner_msg:
            max_len_aa_owner_msg = len(aa_owner_msg)
    if max_len_aa_owner_msg < 19: max_len_aa_owner_msg = 19
    final_line_fixed = '_'*(max_len_aa_owner_msg - 19) if max_len_aa_owner_msg > 19 else '?'


    # Get the list of devices with valid apple accounts
    aa_idx = 0

    for conf_apple_account in Gb.conf_apple_accounts:
        aausername = conf_apple_account[CONF_USERNAME]
        aa_idx += 1
        aa_idx_dots = '.'*aa_idx

        if Gb.valid_upw_by_username.get(aausername, False) is False:
            continue

        AppleAcct = Gb.AppleAcct_by_username.get(aausername)
        if AppleAcct is None:
            continue

        if AppleAcct.AADevices is None or AppleAcct.is_AADevices_setup_complete is False:
            _AppleDev = await Gb.hass.async_add_executor_job(
                                    aascf.create_AADevices_config_flow,
                                    AppleAcct)

        if AppleAcct:
            # self._check_finish_v2v3conversion_for_aadevice_dname()

            devices_available, devices_used, devices_not_available, this_device = \
                    get_icloud_devices_list_avail_used_this(
                            aa_idx, AppleAcct, AppleAcct.account_owner, selected_devicename)

            # Available devices
            devices_cnt  = len(devices_used) + len(devices_available) + len(this_device)
            assigned_cnt = len(devices_used) + len(this_device)
            len_aa_owner_msg = len(f"{AppleAcct.account_owner} ({AppleAcct.username_base})")
            final_line       = f"{'_'*int((max_len_aa_owner_msg - len_aa_owner_msg) + 6)}"

            username_hdr_available = {  f"{aa_idx_dots}hdr":
                                        f"🍏 ________ AVAILABLE ______ {AppleAcct.account_owner} "
                                        f"({AppleAcct.username_base}), "
                                        f"{assigned_cnt} of {devices_cnt} Assigned) "
                                        f"{final_line}"}

            if devices_available == {}:
                devices_available ={f"nodev": "All Apple account devices are assigned"}

            all_devices_available.update(username_hdr_available)
            all_devices_available.update(devices_available)
            all_devices_used.update(devices_used)
            all_devices_not_available.update(devices_not_available)
            all_devices_this_device.update(this_device)

    if isnot_empty(all_devices_this_device):
        self.icloud_list_text_by_fname2.update(all_devices_this_device)
        self.icloud_list_text_by_fname2.update({'.dashes': '_'*76 + final_line_fixed})

    self.icloud_list_text_by_fname2.update(NONE_FAMSHR_DICT_KEY_TEXT)

    if isnot_empty(all_devices_not_available):
        self.icloud_list_text_by_fname2.update({".notavail":
                        f"⛔ ________ ICLOUD3 DEVICES WITH APPLE CONFIGURATION ERRORS _____"
                        f"{final_line_fixed}"})
        self.icloud_list_text_by_fname2.update(sort_dict_by_values(all_devices_not_available))

    if isnot_empty(all_devices_available):
        self.icloud_list_text_by_fname2.update(all_devices_available)

    if isnot_empty(all_devices_used):
        self.icloud_list_text_by_fname2.update({".assigned":
                        f"🍎 ______ APPLE DEVICES ASSIGNED TO ANOTHER ICLOUD3 DEVICE ______"
                        f"{final_line_fixed}"})

        self.icloud_list_text_by_fname2.update(sort_dict_by_values(all_devices_used))

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

    devices_assigned = {}
    selected_device_aadevice_dname = ''
    for _conf_device in Gb.conf_devices:
        devicename   = _conf_device[CONF_IC3_DEVICENAME]
        aadevice_dname = _conf_device[CONF_FAMSHR_DEVICENAME]
        aausername     = _conf_device[CONF_APPLE_ACCOUNT]
        if (aadevice_dname == 'None'
                or AppleAcct.username != aausername):
            continue

        devices_assigned[aadevice_dname] = devicename
        devices_assigned[devicename]   = aadevice_dname

    try:
        for aadevice_dname, device_model in AppleAcct.device_model_name_by_icloud_dname.items():
            device_id = AppleAcct.device_id_by_icloud_dname[aadevice_dname]
            _AADevData  = AppleAcct.AADevData_by_device_id[device_id]
            conf_apple_acct, conf_aa_idx = config_file.conf_apple_acct(AppleAcct.username)
            locate_all_sym = '' if conf_apple_acct[CONF_LOCATE_ALL] else 'ⓧ '
            family_device = ', FamilyDevice' if _AADevData.family_share_device else ''
            if family_device  and locate_all_sym:
                family_device = 'FamilyDevice, APPLE ACCT NOT LOCATING ALL DEVICES'

            device_list_item_key = f"{aadevice_dname}{LINK}{AppleAcct.username}"
            aadevice_dname_owner = f"{aadevice_dname}{LINK}{AppleAcct.account_owner}"
            aadevice_dname_owner_model = f"{aadevice_dname_owner}{family_device}, {device_model}"

            # If not assigned to an ic3 device
            if aadevice_dname not in devices_assigned:
                if family_device:
                    available_family[device_list_item_key] = (
                                    f"{locate_all_sym}"
                                    f"{aadevice_dname_owner_model}"
                                    f"{aa_idx_dots}")
                else:
                    available_owner[device_list_item_key] = (
                                    f"{aadevice_dname_owner_model}"
                                    f"{aa_idx_dots}")
                continue

            # Is the icloud device name assigned to the current device being updated
            devicename = devices_assigned[aadevice_dname]
            if devicename == selected_devicename:
                err = RED_ALERT if instr(aadevice_dname_owner_model, 'NOT LOCATING') else ''
                this_device[device_list_item_key] = (
                            f"{err}{aadevice_dname_owner}{family_device}, "
                            f"{device_model}"
                            f"{aa_idx_dots}")
                continue

            # Assigned to another device
            _assigned_to_fname = icloud_device_assigned_to(AppleAcct, aadevice_dname)
            err = RED_ALERT if instr(aadevice_dname_owner_model, 'NOT LOCATING') else ''
            devices_used[device_list_item_key] = (
                            f"{err}{aadevice_dname_owner}{RARROW}"
                            f"{_assigned_to_fname}{family_device}, "
                            f"{device_model}")

    except Exception as err:
        log_exception(err)

    devices_not_available.update(sort_dict_by_values(unknown_devices))
    devices_available.update(sort_dict_by_values(available_owner))
    devices_available.update(sort_dict_by_values(available_family))

    return devices_available, devices_used, devices_not_available, this_device

#----------------------------------------------------------------------
def icloud_device_assigned_to(AppleAcct, aadevice_dname):
    _assigned_to_fname = [f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]})"
                            for conf_device in Gb.conf_devices
                            if (AppleAcct.username == conf_device[CONF_APPLE_ACCOUNT]
                                    and aadevice_dname == conf_device[CONF_FAMSHR_DEVICENAME])]

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

    mobapp_devices ={mobapp_dname:(
                        f"{mobapp_info[0]} "
                        f"(device_tracker.{mobapp_dname}), "
                        f"{mobapp_info[3]}")
                        for mobapp_dname, mobapp_info in Gb.device_info_by_mobapp_dname.items()}

    for mobapp_dname, mobapp_info in mobapp_devices.items():
        if mobapp_dname not in Gb.devicenames_by_mobapp_dname:
            devices_available[mobapp_dname] = mobapp_info
            continue

        if (selected_devicename
                and mobapp_dname == self.conf_device[CONF_MOBILE_APP_DEVICE]):
            devices_this_device[mobapp_dname] = mobapp_info
            continue

        else:
            devicename = Gb.devicenames_by_mobapp_dname[mobapp_dname]
            Device = Gb.Devices_by_devicename.get(devicename)
            if Device:
                fname_devicename = Device.fname_devicename
            elif devicename in Gb.inactive_fname_by_devicename:
                fname_devicename = f"{Gb.inactive_fname_by_devicename[devicename]} (INACTIVE)"
            else:
                fname_devicename = f"{RED_ALERT}{devicename} (UNKNOWN)"

            devices_used[mobapp_dname] = (
                        f"{mobapp_info.split(';')[0]}{RARROW}{fname_devicename}")

    try:
        scan_for_mobapp_devices = {
                    f"ScanFor: {_conf_device[CONF_IC3_DEVICENAME]}": (
                    f"Scan for a Mobile App device starting with > ‘{_conf_device[CONF_IC3_DEVICENAME]}’")
                        for _conf_device in Gb.conf_devices}

    except Exception as err:
        # log_exception(err)
        scan_for_mobapp_devices = {}

    if devices_available == {}:
        devices_available = {f"nodev": "All MobApp devices are assigned"}
    if (selected_devicename
            and is_empty(devices_this_device)
            and self.conf_device[CONF_MOBILE_APP_DEVICE] != 'None'
            and self.conf_device[CONF_MOBILE_APP_DEVICE].startswith('ScanFor:') is False):
        devices_this_device = {'.unknown':
                f"{RED_ALERT}{self.conf_device[CONF_MOBILE_APP_DEVICE]}{RARROW}UNKNOWN MOBILE APP DEVICE"}

    #self.mobapp_list_text_by_entity_id.update({'.this': f"☑️ ⋯⋯⋯ MOBILE APP ASSIGNED TO THIS ICLOUD3 DEVICE ⋯⋯⋯"})
    if isnot_empty(devices_this_device):
        self.mobapp_list_text_by_entity_id.update(devices_this_device)
        self.mobapp_list_text_by_entity_id.update({'.dashes': '═'*51})
    self.mobapp_list_text_by_entity_id.update(MOBAPP_DEVICE_NONE_OPTIONS)
    self.mobapp_list_text_by_entity_id.update({'.available': f"✅ ______ AVAILABLE MOBILE APP DEVICES {'_'*40}"})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_available))
    self.mobapp_list_text_by_entity_id.update({'.assigned': f"🅰️ ______ ASSIGNED TO ANOTHER ICLOUD3 DEVICE {'_'*32} "})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_used))
    self.mobapp_list_text_by_entity_id.update({'.scanfor': f"🔄 ______ SCAN FOR DEVICE TRACKER ENTITY {'_'*38}"})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(scan_for_mobapp_devices))

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
                self.picture_by_filename[f".www_dirs{www_dir_idx}"] = (
                            f"Picture Directories: "
                            f"{list_to_str(Gb.picture_www_dirs[www_dir_idx:www_dir_idx+3])}")
                www_dir_idx += 3

        for over_25_warning_msg in over_25_warning_msgs:
            www_dir_idx += 1
            self.picture_by_filename[f".www_dirs{www_dir_idx}"] = over_25_warning_msg

        self.picture_by_filename['.available'] = f"🔻 ______ PICTURE FILE NAMES {'_'*38}"
        self.picture_by_filename['setup_picture_dir_filter'] = "️️➤ SET PICTURE DIRECTORY FILTER → Select directories with the picture image files"
        self.picture_by_filename.update(self.picture_by_filename_base)

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
    # if self.away_time_zone_hours_key_text != {}:
    #     return

    ha_time = int(Gb.this_update_time[0:2])
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
            time_str = f"{ap_hh:}{Gb.this_update_time[2:]}{ap}"
        else:
            time_str = f"{away_hh:02}{Gb.this_update_time[2:]}"

        if away_hh == ha_time:
            time_str = f"Home Time Zone"
        elif hh < ha_time:
            time_str += f" (-{abs(hh-ha_time):} hours)"
        else:
            time_str += f" (+{abs(ha_time-hh):} hours)"
        self.away_time_zone_hours_key_text[hh-ha_time] = time_str

#-------------------------------------------------------------------------------------------
def build_away_time_zone_devices_list(self):

    self.away_time_zone_devices_key_text = AWAY_FROM_ZONE_OPTIONS.copy()
    self.away_time_zone_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def build_log_level_devices_list(self):

    self.log_level_devices_key_text = {
            'all': 'All Devices - Log RawData for all devices'}
    self.log_level_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def devices_selection_list():
    return {conf_device[CONF_IC3_DEVICENAME]: (
                    f"{conf_device[CONF_FNAME]} "
                    f"({DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}), "
                    f"{TRACKING_MODE_DN[conf_device[CONF_TRACKING_MODE]]}")
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
    for AppleAcct in Gb.AppleAcct_by_username.values():
        self.imported_aa_ic3_conf_devices.update(
                        aascf.build_import_devices_config_from_aadevices(self, AppleAcct))

    for sort_key, ic3_conf_device in self.imported_aa_ic3_conf_devices.items():
        aausername     = ic3_conf_device[CONF_APPLE_ACCOUNT]
        aadevice_dname = ic3_conf_device[CONF_FAMSHR_DEVICENAME]
        mobapp_dname   = ic3_conf_device.get(CONF_MOBILE_APP_DEVICE)

        sel_line = f"{ic3_conf_device[CONF_FNAME]} ({ic3_conf_device[CONF_IC3_DEVICENAME]}){RARROW}"
        sel_line += f"AppleDevice–({aadevice_dname}{LINK}{username_id(aausername)}), "
        if mobapp_dname != 'None':
            sel_line += f"MobApp–({Gb.device_info_by_mobapp_dname[mobapp_dname][0]}), "
        sel_line += f"{ic3_conf_device[CONF_MODEL_DISPLAY_NAME]}"

        self.imported_aadevices_sel_list[sort_key] = sel_line
