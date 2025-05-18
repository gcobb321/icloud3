

from ..global_variables import GlobalVariables as Gb
from ..const            import (RARROW, PHDOT, CRLF_DOT, DOT, HDOT, PHDOT, CIRCLE_STAR, RED_X,
                                YELLOW_ALERT, RED_ALERT, EVLOG_NOTICE, EVLOG_ALERT, EVLOG_ERROR, LINK, LLINK, RLINK,
                                IPHONE_FNAME, IPHONE, IPAD, WATCH, MAC, AIRPODS, ICLOUD, OTHER, HOME, FAMSHR,
                                DEVICE_TYPES, DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES, DEVICE_TRACKER_DOT,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCOUNT, CONF_TOTP_KEY,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE, CONF_VERIFICATION_CODE, CONF_LOCATE_ALL,
                                CONF_TRACK_FROM_ZONES,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE, CONF_FMF_EMAIL,CONF_FMF_DEVICE_ID,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                )

from ..utils.utils      import (instr, isnumber, is_empty, isnot_empty, list_to_str, str_to_list,
                                is_statzone, zone_dname, isbetween, list_del, list_add,
                                sort_dict_by_values,
                                encode_password, decode_password, )
from ..utils.messaging  import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, )

from .                  import icloud
from .form_lists_def    import (NONE_FAMSHR_DICT_KEY_TEXT, MOBAPP_DEVICE_NONE_OPTIONS, )
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
        include_icloud_dnames:
            True - Add a list of the devices in the Apple Account and add a
                    new account option
    '''

    self.apple_acct_items_by_username = {}
    self.is_verification_code_needed = False

    aa_idx = -1
    for apple_account in Gb.conf_apple_accounts:
        aa_idx += 1
        username = apple_account[CONF_USERNAME]
        devicenames_by_username, icloud_dnames_by_username = \
                    self.get_conf_device_names_by_username(username)
        devices_assigned_cnt = len(devicenames_by_username)

        if aa_idx == 0 and username == '':
            break
        elif username == '':
            continue
        else:
            valid_upw = Gb.username_valid_by_username.get(username)
            PyiCloud = Gb.PyiCloud_by_username.get(username)
            if PyiCloud is None or PyiCloud.is_DeviceSvc_setup_complete is False:
                aa_text = f"{username}{RARROW}{RED_ALERT}"
                if valid_upw is False:
                    aa_text += 'NOT LOGGED IN, INVALID USERNAME/PASSWORD'
                elif instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD) is False:
                    aa_text += 'NOT LOGGED IN, APPLE DATA SOURCE DISABLED'
                elif valid_upw is None:
                    aa_text += 'NOT LOGGED INTO THIS APPLE ACCOUNT'
                else:
                    aa_text += 'NOT LOGGED IN DUE TO ANOTHER ERROR, SEE EVENT LOG'
                self.apple_acct_items_by_username[username] = aa_text
                continue

        aa_text = f"{PyiCloud.account_owner_username.split('@')[0]}{RARROW}"
        if PyiCloud.requires_2fa:
            self.is_verification_code_needed = True
            aa_text += f"{RED_ALERT} AUTHENTICATION NEEDED, "

        aa_text += (f"{devices_assigned_cnt} of "
                    f"{len(PyiCloud.icloud_dnames)} iCloud Devices Tracked "
                    f"{self.tracked_untracked_form_msg(username)[0]}")

        self.apple_acct_items_by_username[username] = aa_text

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

    if conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
        device_text += " Ⓜ MONITOR, "
    elif conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
        device_text += "✪ INACTIVE, "

    if conf_device[CONF_FAMSHR_DEVICENAME] != 'None':
        icloud_dname_apple_acct, status_msg = \
                        format_apple_acct_device_info(self, conf_device)
        device_text += (f"iCloud > "
                        f"({icloud_dname_apple_acct}{status_msg}), ")

    if conf_device[CONF_MOBILE_APP_DEVICE] != 'None':
        mobapp_dname = conf_device[CONF_MOBILE_APP_DEVICE]
        device_text += "MobApp > "
        if mobapp_dname.startswith('ScanFor:'):
            device_text += f"({mobapp_dname}), "
        elif mobapp_dname in Gb.device_info_by_mobapp_dname:
            device_text += f"({Gb.device_info_by_mobapp_dname[mobapp_dname][0]}), "
        else:
            device_text += f"{mobapp_dname} ({RED_ALERT}UNKNOWN MOBAPP ENTITY), "

    if conf_device[CONF_TRACK_FROM_BASE_ZONE] != HOME:
        tfhbz = conf_device[CONF_TRACK_FROM_BASE_ZONE]
        device_text +=  f"PrimaryHomeZone > {zone_dname(tfhbz)}, "

    if conf_device[CONF_TRACK_FROM_ZONES] != [HOME]:
        tfz_fnames = [zone_dname(z) for z in conf_device[CONF_TRACK_FROM_ZONES]]
        device_text +=  f"TrackFromZones > {list_to_str(tfz_fnames)}, "

    # device_text = device_text.replace(' , ', ' ')
    if device_text.endswith(', '): device_text = device_text[:-2]

    return device_text

#----------------------------------------------------------------------
def format_apple_acct_device_info(self, conf_device):
    '''
    Format the icloud_dname><apple_account field based on the device's
    CONF_FAMSHR_DEVICENAME and CONF_APPLE_ACCOUNT configuration values
    and the status of PyiCloud state and the devices available in PyiCloud

    Input:
        - device confiuration

    Return:
        - icloud_dname><apple_account
        - status message
    '''

    icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
    apple_acct   = conf_device[CONF_APPLE_ACCOUNT]
    apple_acct_base = f"{apple_acct}@".split('@')[0]
    status_msg   = ''

    if PyiCloud := Gb.PyiCloud_by_username.get(apple_acct):
        icloud_dname_apple_acct = f"{icloud_dname}{PyiCloud.account_owner_link}"
        if icloud_dname in PyiCloud.device_id_by_icloud_dname:
            pass
        elif is_empty(PyiCloud.device_id_by_icloud_dname):
            status_msg = f" {RED_ALERT}APPLE ACCT UNAVAILABLE"
        else:
            status_msg = f" {RED_ALERT}`{icloud_dname}` DEVICE NOT IN APPLE ACCT"

    elif self._is_apple_acct_setup() is False:
        icloud_dname_apple_acct = f"{icloud_dname}{LINK}NOAPPLEACCTS{RLINK}"
        status_msg = f" {RED_ALERT}NO APPLE ACCTS SET UP"

    elif instr(self.data_source, ICLOUD) is False:
        icloud_dname_apple_acct = f"{icloud_dname}{LINK}{apple_acct_base}{RLINK}"
        status_msg = f" {RED_ALERT}APPLE DATA SOURCE DISABLED"
    else:
        icloud_dname_apple_acct = f"{icloud_dname}{LINK}{apple_acct_base}{RLINK}"
        status_msg = f" {RED_ALERT}UNKNOWN APPLE ACCT"

    return icloud_dname_apple_acct, status_msg

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

        # _xtraceha(f"{self.icloud_list_text_by_fname=}")
        # _xtraceha(f"{self.mobapp_list_text_by_entity_id=}")
        # _xtraceha(f"{self.conf_device=}")
        # _xtraceha(f"{self.zone_name_key_text=}")

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
    # self.icloud_list_text_by_fname2 = NONE_FAMSHR_DICT_KEY_TEXT.copy()
    self.icloud_list_text_by_fname2 = {}
    all_devices_available = {}
    all_devices_not_available = {}
    all_devices_used = {}
    all_devices_this_device = {}
    all_devices_unknown_device = {}
    username_hdr_available = {}
    selected_device_icloud_dname = 'None' if is_empty(Gb.conf_devices) else ''
    selected_device_apple_acct = None

    # Get the list of devices with unknown apple accts
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if conf_device[CONF_FAMSHR_DEVICENAME] == 'None':
            continue

        icloud_dname_apple_acct, status_msg = \
                    format_apple_acct_device_info(self, conf_device)

        if status_msg == '':
            continue

        # if Gb.username_valid_by_username.get(conf_device[CONF_APPLE_ACCOUNT], False) is False:
        apple_acct = conf_device[CONF_APPLE_ACCOUNT] if conf_device[CONF_APPLE_ACCOUNT] != '' else 'NONE'
        device_list_item_key = f"{devicename}{LINK}{apple_acct}"
        all_devices_not_available[device_list_item_key] = (
                    f"{conf_device[CONF_FNAME]} ({devicename}) > "
                    f"{icloud_dname_apple_acct}{status_msg}")

        # Save the FamShr config parameter in case it is not found
        if devicename == selected_devicename:
            selected_device_apple_acct   = conf_device[CONF_APPLE_ACCOUNT]
            selected_device_icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]

    max_len_aa_owner_msg = 0
    for _PyiCloud in Gb.PyiCloud_by_username.values():
        aa_owner_msg = f"{_PyiCloud.account_owner} ({_PyiCloud.username_base})"
        if len(aa_owner_msg) > max_len_aa_owner_msg:
            max_len_aa_owner_msg = len(aa_owner_msg)
    if max_len_aa_owner_msg < 26: max_len_aa_owner_msg = 26
    final_dots_fixed = '⋯'*(max_len_aa_owner_msg - 27) if max_len_aa_owner_msg > 27 else ''


    # Get the list of devices with valid apple accounts
    aa_idx = 0

    for apple_acct in Gb.conf_apple_accounts:
        username = apple_acct[CONF_USERNAME]
        aa_idx += 1
        aa_idx_dots = '.'*aa_idx

        if Gb.username_valid_by_username.get(username, False) is False:
            continue

        PyiCloud = Gb.PyiCloud_by_username.get(username)
        if PyiCloud is None:
            continue

        if PyiCloud.DeviceSvc is None or PyiCloud.is_DeviceSvc_setup_complete is False:
            _AppleDev = await Gb.hass.async_add_executor_job(
                                    icloud.create_DeviceSvc_config_flow,
                                    PyiCloud)

        if PyiCloud:
            # self._check_finish_v2v3conversion_for_icloud_dname()

            devices_available, devices_used, devices_not_available, this_device = \
                    get_icloud_devices_list_avail_used_this(
                            aa_idx, PyiCloud, PyiCloud.account_owner, selected_devicename)

            # Available devices
            devices_cnt  = len(devices_used) + len(devices_available) + len(this_device)
            assigned_cnt = len(devices_used) + len(this_device)
            len_aa_owner_msg = len(f"{PyiCloud.account_owner} ({PyiCloud.username_base})")

            final_dots       = f"{'⋯'*int((max_len_aa_owner_msg - len_aa_owner_msg)*.4)}"

            username_hdr_available = {  f"{aa_idx_dots}hdr":
                                        f"🍏 ⋯⋯⋯ AVAILABLE ⋯⋯⋯ {PyiCloud.account_owner} "
                                        f"({PyiCloud.username_base}), "
                                        f"{assigned_cnt} of {devices_cnt} Assigned ⋯⋯⋯{final_dots} 🍏"}


            if devices_available == {}:
                devices_available = {f"{aa_idx_dots}nodev": f"{CIRCLE_STAR} All Apple account devices are assigned"}

            all_devices_available.update(username_hdr_available)
            all_devices_available.update(devices_available)
            all_devices_used.update(devices_used)
            all_devices_not_available.update(devices_not_available)
            all_devices_this_device.update(this_device)

    if isnot_empty(all_devices_this_device):
        #self.icloud_list_text_by_fname2.update({f".thisdevice":
        #               f"☑️ ⋯⋯⋯ APPLE DEVICE ASSIGNED TO THIS ICLOUD3 DEVICE ⋯⋯⋯ ☑️"})
        self.icloud_list_text_by_fname2.update(all_devices_this_device)
        self.icloud_list_text_by_fname2.update({'.dashes': '═'*51})

    self.icloud_list_text_by_fname2.update(NONE_FAMSHR_DICT_KEY_TEXT)

    if isnot_empty(all_devices_not_available):
        self.icloud_list_text_by_fname2.update({".notavail":
                        f"⛔ ⋯⋯⋯ ICLOUD3 DEVICES WITH APPLE CONFIGURATION ERRORS ⋯⋯⋯⋯{final_dots_fixed} ⛔"})
        self.icloud_list_text_by_fname2.update(sort_dict_by_values(all_devices_not_available))

    if isnot_empty(all_devices_available):
        self.icloud_list_text_by_fname2.update(all_devices_available)

    if isnot_empty(all_devices_used):
        self.icloud_list_text_by_fname2.update({".assigned":
                        f"🅰️ ⋯⋯⋯ APPLE DEVICES ASSIGNED TO ANOTHER ICLOUD3 DEVICE ⋯⋯⋯{final_dots_fixed}⋯ 🅰️"})
        self.icloud_list_text_by_fname2.update(sort_dict_by_values(all_devices_used))

    self.icloud_list_text_by_fname = self.icloud_list_text_by_fname2.copy()

#----------------------------------------------------------------------
def get_icloud_devices_list_avail_used_this(aa_idx, PyiCloud, apple_acct_owner,
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
    selected_device_icloud_dname = ''
    for _conf_device in Gb.conf_devices:
        devicename   = _conf_device[CONF_IC3_DEVICENAME]
        icloud_dname = _conf_device[CONF_FAMSHR_DEVICENAME]
        username     = _conf_device[CONF_APPLE_ACCOUNT]
        if (icloud_dname == 'None'
                or PyiCloud.username != username):
            continue

        devices_assigned[icloud_dname] = devicename
        devices_assigned[devicename]   = icloud_dname

    try:
        for icloud_dname, device_model in PyiCloud.device_model_name_by_icloud_dname.items():
            device_id = PyiCloud.device_id_by_icloud_dname[icloud_dname]
            _RawData  = PyiCloud.RawData_by_device_id[device_id]
            conf_apple_acct, conf_aa_idx = config_file.conf_apple_acct(PyiCloud.username)
            locate_all_sym = '' if conf_apple_acct[CONF_LOCATE_ALL] else 'ⓧ '
            family_device = ', FamilyDevice' if _RawData.family_share_device else ''
            if family_device  and locate_all_sym:
                family_device = 'FamilyDevice, APPLE ACCT NOT LOCATING ALL DEVICES'

            device_list_item_key = f"{icloud_dname}{LINK}{PyiCloud.username}"
            icloud_dname_owner   = f"{icloud_dname}{LINK}{PyiCloud.account_owner}{RLINK}"
            icloud_dname_owner_model = f"{icloud_dname_owner}{family_device}, {device_model}"

            # If not assigned to an ic3 device
            if icloud_dname not in devices_assigned:
                if family_device:
                    available_family[device_list_item_key] = (
                                    f"{locate_all_sym}"
                                    f"{icloud_dname_owner_model}"
                                    f"{aa_idx_dots}")
                else:
                    available_owner[device_list_item_key] = (
                                    f"{icloud_dname_owner_model}"
                                    f"{aa_idx_dots}")
                continue

            # Is the icloud device name assigned to the current device being updated
            devicename = devices_assigned[icloud_dname]
            if devicename == selected_devicename:
                err = RED_ALERT if instr(icloud_dname_owner_model, 'NOT LOCATING') else ''
                this_device[device_list_item_key] = (
                            f"{err}{icloud_dname_owner}{family_device}, "
                            f"{device_model}"
                            f"{aa_idx_dots}")
                continue

            # Assigned to another device
            _assigned_to_fname = icloud_device_assigned_to(PyiCloud, icloud_dname)
            err = RED_ALERT if instr(icloud_dname_owner_model, 'NOT LOCATING') else ''
            devices_used[device_list_item_key] = (
                            f"{err}{icloud_dname_owner}{RARROW}"
                            f"{_assigned_to_fname}{family_device}, "
                            f"{device_model}")

    except Exception as err:
        log_exception(err)

    devices_not_available.update(sort_dict_by_values(unknown_devices))
    devices_available.update(sort_dict_by_values(available_owner))
    devices_available.update(sort_dict_by_values(available_family))

    return devices_available, devices_used, devices_not_available, this_device

#----------------------------------------------------------------------
def icloud_device_assigned_to(PyiCloud, icloud_dname):
    _assigned_to_fname = [f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]})"
                            for conf_device in Gb.conf_devices
                            if (PyiCloud.username == conf_device[CONF_APPLE_ACCOUNT]
                                    and icloud_dname == conf_device[CONF_FAMSHR_DEVICENAME])]

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
        devices_available = {f"nodev": f"{CIRCLE_STAR} All MobApp devices are assigned"}
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
    self.mobapp_list_text_by_entity_id.update({'.available': f"✅ ⋯⋯⋯ AVAILABLE MOBILE APP DEVICES {'⋯'*17} ✅"})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_available))
    self.mobapp_list_text_by_entity_id.update({'.assigned': f"🅰️ ⋯⋯⋯ ASSIGNED TO ANOTHER ICLOUD3 DEVICE {'⋯'*13} 🅰️"})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(devices_used))
    self.mobapp_list_text_by_entity_id.update({'.scanfor': f"🔄 ⋯⋯⋯ SCAN FOR DEVICE TRACKER ENTITY {'⋯'*16} 🔄"})
    self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(scan_for_mobapp_devices))

    return

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
                            f"Source Directories: "
                            f"{list_to_str(Gb.picture_www_dirs[www_dir_idx:www_dir_idx+3])}")
                www_dir_idx += 3

        for over_25_warning_msg in over_25_warning_msgs:
            www_dir_idx += 1
            self.picture_by_filename[f".www_dirs{www_dir_idx}"] = over_25_warning_msg

        self.picture_by_filename['.available'] = f"✅ ⋯⋯⋯ DEVICE PICTURE FILE NAMES {'⋯'*16} ✅"
        self.picture_by_filename['setup_dir_filter'] = "➤ FILTER IMAGE DIRECTORIES > Select directories with the picture image files"
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
    if self.away_time_zone_hours_key_text != {}:
        return

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

    self.away_time_zone_devices_key_text = {
                    'none': 'None > All devices are at Home',
                    'all': 'All > All device are away from home'}
    self.away_time_zone_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def build_log_level_devices_list(self):

    self.log_level_devices_key_text = {
            'all': 'All Devices - Add RawData for all devices to the `icloud.log` log file'}
    self.log_level_devices_key_text.update(devices_selection_list())

#-------------------------------------------------------------------------------------------
def devices_selection_list():
    return {conf_device[CONF_IC3_DEVICENAME]: (
                    f"{conf_device[CONF_FNAME]} "
                    f"({DEVICE_TYPE_FNAME(conf_device[CONF_DEVICE_TYPE])})")
                for conf_device in Gb.conf_devices
                if conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE}




#----------------------------------------------------------------------
async def build_trusted_devices_list(self):
    return
#     '''
#     Build a list of the trusted devices for the Apple account
#     '''
#     try:
#         return {}
#         _log(f"BUILD BEF TRUSTED DEVICES")
#         trusted_devices = await self.hass.async_add_executor_job(
#                         getattr, self.PyiCloud, "trusted_devices")
#         # trusted_devices = trusted_devices_json.json()
#         _log(f"BUILD AFT TRUSTED DEVICES")
#         _log(f"{trusted_devices=}")

#         trusted_devices_key_text = {}
#         for i, device in enumerate(trusted_devices):
#             trusted_devices_key_text[i] = self.PyiCloud.device.get(
#                 "deviceName", f"SMS to {device.get('phoneNumber')}")

#         _log(f"{trusted_devices_key_text=}")

#         return trusted_devices_key_text

#     except Exception as err:
#         log_exception(err)

#     return {}