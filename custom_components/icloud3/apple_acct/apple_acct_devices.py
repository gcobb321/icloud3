from ..global_variables import GlobalVariables as Gb
from ..const            import (AIRPODS_DN, NONE_FNAME,
                                EVLOG_NOTICE, EVLOG_ALERT,
                                HHMMSS_ZERO,
                                ICLOUD, NAME, ID, LOCATION, ICLOUD_DEVICE_STATUS, DEVICE_TYPES,
                                MISSING_DEVICE_RESTART_IN_SECS, MISSING_DEVICE_INTERVAL_SECS, )
from ..const_config     import (CONF_IC3_DEVICENAME, CONF_FNAME, CONF_AADEV_NAME,
                                CONF_AADEV_DEVICE_ID, CONF_DEVICE_TYPE, CONF_APPLE_ACCT,
                                CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_LOG_LEVEL_DEVICES, )
from ..const_char       import (LINK, RLINK, LLINK, DOTS, RED_X, RARROW, DOT, CRLF, CRLF_DOT,
                                CRLF_STAR, CRLF_CHK, CRLF_HDOT, )
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del, list_to_str,
                                dict_sort,
                                apple_user, apple_id_dev, apple_user_dev, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                secs_since, format_secs_since, format_age, format_time_age,
                                format_timer, )
from ..utils.messaging  import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                post_greenbar_msg, _evlog, _log,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_exception, update_alert_sensor, )
from ..utils.rawdata_logging import (log_data, )

from .apple_acct_device import iCloud_AppleAcctDevice
from .                  import icloud_requests_io  as icloud_io
from ..tracking         import determine_interval as det_interval
from ..support          import test_controls as TEST

import copy
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

#--------------------------------------------------------------------


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Find iCloud Devices service (originally find my iphone)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
REFRESH_ENDPOINT    = "/fmipservice/client/web/refreshClient"
PLAYSOUND_ENDPOINT  = "/fmipservice/client/web/playSound"
MESSAGE_ENDPOINT    = "/fmipservice/client/web/sendMessage"
LOSTDEVICE_ENDPOINT = "/fmipservice/client/web/lostDevice"

class iCloud_AppleAcctDevices():
    '''
    The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.
    '''

    def __init__(self,  AppleAcct,
                        iCloudSession,
                        params,
                        task="RefreshData",
                        device_id=None, subject=None, message=None,
                        sounds=False, number="", newpasscode=""):

        self.setup_time      = time_now()
        self.iCloudSession   = iCloudSession
        self.AppleAcct       = AppleAcct
        self.apple_user      = self.AppleAcct.apple_user

        self.params       = params
        self.task         = task
        self.device_id    = device_id
        self.devices_data = {}

        Gb.devices_without_location_data = []

        self.timestamp_field = 'timeStamp'
        self.data_source     = ICLOUD

        fmiDict =   {"clientContext":
                        { "appName": "Home Assistant", "appVersion": "0.118",
                        "inactiveTime": 1, "apiVersion": "2.2.2" }
                    }

        if task == "PlaySound":
            if device_id:
                self.play_sound(device_id, subject)
            return

        elif task == "Message":
            if device_id:
                self.display_message(device_id, subject, message)
            return

        elif task == "LostDevice":
            if device_id:
                self.lost_device(device_id, number, message, newpasscode="")
            return

        try:
            # This will generate an error if the table has not been defined from (init or start_ic3)
            # Init may be in the process of setting up the table and iCloud but then start_ic3/Stage 4
            # thinks it is not done and resets everything.
            if isnot_empty(self.AppleAcct.device_id_by_aadev_dname):
                return
        except:
            pass

        self.refresh_device()

        Gb.devices_not_set_up = self._get_conf_icloud_devices_not_set_up()
        if Gb.devices_not_set_up == []:
            return

#----------------------------------------------------------------------------
    def _get_conf_icloud_devices_not_set_up(self):
        '''
        Return a list of devices in the iCloud3 configuration file that are
        not in the  iCloud data returned from Apple.
        '''
        return [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_AADEV_NAME] != NONE_FNAME
                        and conf_device[CONF_AADEV_NAME] not in \
                                self.AppleAcct.device_id_by_aadev_dname)]

#---------------------------------------------------------------------------
    @property
    def is_AADevices_setup_complete(self):
        return self.AppleAcct.is_AADevices_setup_complete

#---------------------------------------------------------------------------
    @property
    def devices_cnt(self):
        # Simulate no devices returned for the first 4 tries
        # if Gb.get_FAMSHR_devices_retry_cnt < 4:
        #     return 0

        if 'content' in self.devices_data:
            return len(self.devices_data.get('content', {}))
        else:
            return 0

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Refresh Device Data - Get New Data from Apple
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def refresh_device(self, requested_by_devicename=None,
                            locate_all_devices=None, device_id=None):
        '''
        Refreshes the FindMyiPhoneService endpoint,
        This ensures that the location data is up-to-date.

        requested_by_devicename:
            = 'reload_all_devices' - Reload all devices during startup instead of
                only devices that have already been verified
            = devicename - Device that is requesting new location data
        device_id:
            = refresh/locate this device
            = None - Refresh/located all devices in Family Sharing list
        locate_all_devices:
            = True - Locate all devices in the Family Sharing list (overrides device selection)
            = False - Locate only the devices belonging to this Apple acct
        '''
        try:
            AppleAcct = self.AppleAcct
            if (Gb.internet_error
                    or self.is_AADevices_setup_complete is False):
                return False

            if locate_all_devices is None:
                if AppleAcct.locate_all_devices is not None:
                    locate_all_devices = AppleAcct.locate_all_devices
                else:
                    locate_all_devices = True

            if requested_by_devicename:
                _Device = Gb.Devices_by_devicename[requested_by_devicename]
                last_update_loc_time = _Device.last_update_loc_time
            else:
                last_update_loc_time = '?'

            if locate_all_devices is False:
                device_msg = f"FamShrDev-{len(Gb.famshr_device_ids_by_apple_id.get(AppleAcct.apple_id, []))}"
            else:
                device_msg = f"AllDevices-{len(Gb.Devices_by_apple_id.get(AppleAcct.apple_id, []))}"

            log_debug_msg( f"Apple Acct > {AppleAcct.apple_user}, "
                                f"RefreshRequestBy-{requested_by_devicename}, "
                                f"LocateAllDev-{locate_all_devices}, {device_msg}, LastLoc-{last_update_loc_time}")

            url  = f"{AppleAcct.findme_url_root}{REFRESH_ENDPOINT}"
            data = {"clientContext":{
                        "fmly": locate_all_devices,
                        "shouldLocate": True,
                        "selectedDevice": device_id,
                        "deviceListVersion": 1, },
                    "accountCountryCode": AppleAcct.token_pw_data.get("account_country"),
                    "dsWebAuthToken": AppleAcct.token_pw_data.get("session_token"),
                    "trustToken": AppleAcct.token_pw_data.get("trust_token", ""),
                    "extended_login": True,}

            try:
                self.devices_data = icloud_io.post(AppleAcct, url, params=self.params, data=data)

            except Exception as err:
                log_exception(err)
                self.devices_data = {}
                log_debug_msg(  f"{AppleAcct.apple_user}, "
                                f"No data returned from iCloud refresh request {err=}")

            if AppleAcct.response_code == 501:
                self._set_service_available(False)
                post_alert( f"iCLOUD ALERT > {AppleAcct.account_owner}, "
                            f"Apple Acct Data Source is not available. "
                            f"The web url providing location data returned a "
                            f"Service Not Available error")
                return None

            self._save_owner_first_names()

            devices_data = self.devices_data.get("content", {})

            # TEST CODE - Add a test device before the AADev objects are created
            # so it is set up as a new device
            if TEST.NEWER_DEV_EXISTING_DEVICE_NAME and isnot_empty(devices_data):
                self._add_test_device_data(devices_data)

            # TEST CODE - Remove a tracked device to simulate a wiped or removed device
            if (TEST.MISSING_DEV_DEVICE_NAME
                    and Gb.is_icloud3_startup_inprocess is False
                    and isnot_empty(devices_data)):
                self._remove_test_device_data(devices_data)

            if isnot_empty(devices_data):
                self._create_AADeviceData_objects(devices_data)

            self.update_device_location_data(requested_by_devicename, devices_data)

            if (Gb.is_icloud3_startup_inprocess is False
                    and Gb.was_icloud3_restart_requested is False):
                self._request_restart_if_tracked_device_missing(devices_data, locate_all_devices)
                self._request_restart_if_tracked_device_replaced()

            return isnot_empty(self.AppleAcct.AADev_by_device_id)

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _add_test_device_data(self, devices_data):
        '''
        TEST CODE - Add a copy of the TEST.NEWER_DEV_EXISTING_DEVICE_NAME device to the Apple data
        for each TEST.NEWER_DEV_SIMULATED_NEW_DEVICE_NAME name with a test device_id and the
        TEST.NEWER_DEV_SIMULATED_NEW_RAW_MODEL model. The device_id is the same on every refresh so
        each test device is only created once.
        '''
        try:
            source_device_data = [device_data for device_data in devices_data
                                    if self._remove_special_chars(device_data[NAME]) == TEST.NEWER_DEV_EXISTING_DEVICE_NAME]
            if is_empty(source_device_data):
                log_debug_msg(f"TEST > Device to copy was not found, {TEST.NEWER_DEV_EXISTING_DEVICE_NAME}")
                return

            source_device_data = source_device_data[0]
            new_device_names   = TEST.NEWER_DEV_SIMULATED_NEW_DEVICE_NAME
            if isinstance(new_device_names, str):
                new_device_names = [new_device_names]

            device_ids = [device_data[ID] for device_data in devices_data]
            for test_no, new_device_name in enumerate(new_device_names, start=1):
                test_device_id = f"TEST{test_no}-{source_device_data[ID][6:]}"
                if test_device_id in device_ids:
                    continue

                # deepcopy, the location is a dict and must not be shared with the real device
                test_device_data       = copy.deepcopy(source_device_data)
                test_device_data[NAME] = new_device_name
                test_device_data[ID]   = test_device_id
                if TEST.NEWER_DEV_SIMULATED_NEW_RAW_MODEL:
                    test_device_data['rawDeviceModel'] = TEST.NEWER_DEV_SIMULATED_NEW_RAW_MODEL
                devices_data.append(test_device_data)

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _remove_test_device_data(self, devices_data):
        '''
        TEST CODE - Remove the TEST.MISSING_DEV_DEVICE_NAME device from the Apple data so
        it is not in the device list, the same as a device that was wiped or removed
        from the Apple acct. The list is changed in place.
        '''
        try:
            for device_data in devices_data[:]:
                if self._remove_special_chars(device_data[NAME]) == TEST.MISSING_DEV_DEVICE_NAME:
                    devices_data.remove(device_data)
                    log_debug_msg(f"TEST > Device removed from Apple data, {TEST.MISSING_DEV_DEVICE_NAME}")

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def update_device_location_data(self, requested_by_devicename=None, devices_data=None):
        '''
        devices_data is the iCloud response['content'] data for all devices in the iCloud list.
        Cycle through them, determine if the data is good and update each devices with the new location
        info.
        '''
        if devices_data is None:
            return

        try:
            self.AppleAcct.last_refresh_secs = time_now_secs()
            self.AppleAcct.update_requested_by = requested_by_devicename
            monitor_msg = f"UPDATED iCloud Data > RequestedBy-{requested_by_devicename}"

            for device_data in devices_data:
                device_data[NAME] = device_data_name = self._remove_special_chars(device_data[NAME])
                device_id         = device_data[ID]
                aadevdata_hdr_msg = ''

                Device = Gb.Devices_by_icloud_device_id.get(device_id)

                if (device_data_name in Gb.conf_icloud_dnames
                        and requested_by_devicename != 'reload_all_devices'
                        and Gb.is_icloud3_startup_inprocess):
                    pass

                elif Gb.was_icloud3_reloaded:
                    Device = Gb.Devices_by_icloud_device_id.get(device_id)
                    if Device and Device.is_inactive:
                        pass

                # only check tracked/monitored devices for location data
                elif (LOCATION not in device_data
                        or device_data[LOCATION] == {}
                        or device_data[LOCATION] is None):
                    if device_id not in Gb.devices_without_location_data:
                        list_add(Gb.devices_without_location_data, device_data_name)

                        aadevdata_hdr_msg = 'NO LOCATION'
                        if device_data[ICLOUD_DEVICE_STATUS] == 201:
                            aadevdata_hdr_msg += ', OFFLINE'
                            monitor_msg += f"{CRLF_STAR}OFFLINE > "
                        else:
                            monitor_msg += f"{CRLF_STAR}NO LOCATION > "
                        monitor_msg += (f"{self.AppleAcct.account_owner}, "
                                        f"{device_data_name}/"
                                        f"{device_id[:8]}, "
                                        f"{device_data['modelDisplayName']} "
                                        f"({device_data['rawDeviceModel']})")

                if Device is None or Device.is_inactive:
                    continue

                # # Create AADev object if the device_id is not already set up
                AADev = self.AppleAcct.AADev_by_device_id[device_id]

                AADev.save_new_device_data(device_data)
                #  Check Device.is_inactive now so it is created and in selection lists later
                if (AADev.Device is None
                        or LOCATION not in AADev.device_data):
                    continue

                if AADev.location_secs == 0:
                    continue

                if ('all' in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                        or AADev.ic3_devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    log_hdr = ( f"{apple_user_dev(self.AppleAcct.apple_user, device_data_name)}/"
                                f"{Device.devicename}, "
                                f"{aadevdata_hdr_msg}, iCloud Data ")
                    log_data(log_hdr, AADev.device_data,
                                data_source='icloud', filter_id=self.AppleAcct.apple_id)

                if AADev.last_loc_time_gps == AADev.loc_time_gps:
                    last_loc_time_gps_msg = last_loc_time_msg = ''
                else:
                    last_loc_time_gps_msg = f"{AADev.last_loc_time_gps}{RARROW}"
                    last_loc_time_msg     = f"{AADev.last_loc_time}{RARROW}"
                    Device.loc_time_updates_icloud.append(AADev.location_time)

                event_msg =(f"Located > iCloud-"
                            f"{last_loc_time_msg}"
                            f"{AADev.location_time}, ")

                if secs_since(AADev.location_secs) > Device.old_loc_threshold_secs + 5:
                    event_msg += f", Old, {format_age(AADev.location_secs)}"

                elif AADev.battery_level is None:
                    AADev.battery_level = 0

                elif AADev.battery_level > 0:
                    if AADev.battery_level != Device.dev_data_battery_level:
                        event_msg += f"{Device.dev_data_battery_level}%{RARROW}"
                    event_msg += f"{AADev.battery_level}%"

                if Gb.is_icloud3_startup_inprocess is True:
                    pass

                elif requested_by_devicename == Device.devicename:
                    AADev.last_requested_loc_time_gps = AADev.loc_time_gps
                    if last_loc_time_msg:
                        post_event(Device.devicename, event_msg)

                elif Device.isin_zone:
                    post_monitor_msg(Device.devicename, event_msg)

                elif AADev.location_secs > 0:
                    post_event(Device.devicename, event_msg)

        except Exception as err:
            log_exception(err)

#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Create Apple Device Data Objects
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _create_AADeviceData_objects(self, devices_data):
        '''
        Create the AADev object for a new device and update the name of a device
        that was renamed in the Apple acct. If a device was added or renamed, the
        duplicate names are resolved and the name lookup tables are rebuilt.
        '''
        new_AADev_items     = []
        renamed_AADev_items = []

        for device_data in devices_data:
            device_id         = device_data[ID]
            device_data[NAME] = device_data_name = self._remove_special_chars(device_data[NAME])

            AADev = self.AppleAcct.AADev_by_device_id.get(device_id)
            if AADev is None:
                self._create_AADeviceData_object(device_id, device_data)
                AADev = self.AppleAcct.AADev_by_device_id[device_id]
                AADev.active = True
                new_AADev_items.append(AADev)

            elif AADev.name != device_data_name:
                post_event( f"Apple Acct > {self.AppleAcct.apple_user}, "
                            f"Device Renamed > {AADev.name}{RARROW}{device_data_name}")
                AADev.name = AADev.device_data[NAME] = device_data_name
                renamed_AADev_items.append(AADev)

        if is_empty(new_AADev_items) and is_empty(renamed_AADev_items):
            return

        self._resolve_duplicate_dnames()
        self._rebuild_aadev_by_dname_dicts()

        if Gb.is_icloud3_startup_inprocess is False:
            self._request_restart_if_tracked_device_changed(
                                    new_AADev_items, renamed_AADev_items)

#----------------------------------------------------------------------------
    def _save_owner_first_names(self):
        '''
        Save the first name of the Apple acct owner (userInfo) and of each Family
        Sharing member (userInfo.membersInfo, the key is the device's prsId)
        '''
        if type(self.devices_data) is not dict:
            return

        user_info = self.devices_data.get('userInfo') or {}
        if 'firstName' in user_info:
            self.AppleAcct.first_name_by_prs_id[None] = user_info['firstName']

        for prs_id, member_info in (user_info.get('membersInfo') or {}).items():
            self.AppleAcct.first_name_by_prs_id[prs_id] = member_info.get('firstName', '')

#----------------------------------------------------------------------------
    def _resolve_duplicate_dnames(self):
        '''
        Set each device's dname, the unique name used in the iCloud3 configuration
        and the name lookup tables.
            - Same owner (prsId) and name: A newer device was restored from the older
              device's backup. The newest device (model number, then location time)
              keeps the name. Each older device gets another '.' suffix and is flagged
              as a duplicate so the tracked device is reassigned to the newest device.
            - Different owners and the same name: A Family Sharing member's device
              gets the owner's first name, 'iPhone (Lillian)'. The Apple acct owner's
              device keeps the name. They are not duplicates.
        The dnames are set from the Apple device name each time so this can be run
        again when a device is added or renamed.
        '''
        AADev_items = [AADev
                    for AADev in self.AppleAcct.AADev_by_device_id.values()
                    if AADev and AADev.active]

        # Newest first within the name and owner. The device_id makes the order the
        # same each time if the model and location time are the same.
        AADev_items.sort(key=lambda AADev: (
                                    AADev.name, AADev.prs_id or '',
                                    -AADev.model_no, -AADev.location_secs,
                                    AADev.device_id))

        AADev_items_by_name = {}
        for AADev in AADev_items:
            AADev_items_by_name.setdefault(AADev.name, []).append(AADev)

        for name, same_name_AADev_items in AADev_items_by_name.items():
            prs_ids = {AADev.prs_id for AADev in same_name_AADev_items}
            is_multiple_owners = len(prs_ids) > 1

            dname_dots_by_prs_id = {}
            for AADev in same_name_AADev_items:
                startup_msg = []
                AADev.dname = name

                if is_multiple_owners and AADev.prs_id:
                    owner_name = AADev.owner_first_name or AADev.prs_id[:6]
                    AADev.dname += f" ({owner_name})"

                if AADev.prs_id in dname_dots_by_prs_id:
                    dname_dots_by_prs_id[AADev.prs_id] += '.'
                    AADev.dname += dname_dots_by_prs_id[AADev.prs_id]
                    AADev.is_duplicate_dname = True
                    list_add(startup_msg, 'DUPLICATE')
                else:
                    dname_dots_by_prs_id[AADev.prs_id] = ''
                    AADev.is_duplicate_dname = False

                if AADev.location_secs == 0:
                    list_add(startup_msg, 'NOT LOCATED')
                if AADev.device_status_code == 201:
                    list_add(startup_msg, 'OFFLINE')

                AADev.device_data['dname'] = AADev.dname
                AADev.apple_id_dev         = apple_id_dev(AADev.apple_id, AADev.dname)
                AADev.startup_msg = list_to_str(startup_msg)

#----------------------------------------------------------------------------
    def _rebuild_aadev_by_dname_dicts(self):
        '''
        Rebuild the name lookup tables from the current dnames so names that were
        changed are removed. The new tables are built and then replace the old ones
        so the config flow never sees an empty table.
        '''
        AppleAcct = self.AppleAcct
        AADev_items                  = []
        aadev_dname_by_device_id         = {}
        device_id_by_aadev_dname         = {}
        device_info_by_aadev_dname       = {}
        device_model_info_by_aadev_dname = {}
        device_model_name_by_aadev_dname = {}

        for device_id, AADev in AppleAcct.AADev_by_device_id.items():
            if AADev is None or AADev.active is False:
                continue

            dname = AADev.dname
            AADev_items.append(AADev)
            aadev_dname_by_device_id[device_id]     = dname
            device_id_by_aadev_dname[dname]         = device_id
            device_info_by_aadev_dname[dname]       = AADev.device_info
            device_model_info_by_aadev_dname[dname] = AADev.aadevice_model_info
            device_model_name_by_aadev_dname[dname] = AADev.model_display_name

        AppleAcct.AADev_items                  = AADev_items
        AppleAcct.aadev_dname_by_device_id         = aadev_dname_by_device_id
        AppleAcct.device_id_by_aadev_dname         = device_id_by_aadev_dname
        AppleAcct.device_info_by_aadev_dname       = device_info_by_aadev_dname
        AppleAcct.device_model_info_by_aadev_dname = device_model_info_by_aadev_dname
        AppleAcct.device_model_name_by_aadev_dname = device_model_name_by_aadev_dname

#----------------------------------------------------------------------------
    def _request_restart_if_tracked_device_changed(self, new_AADev_items,
                                                        renamed_AADev_items):
        '''
        Restart iCloud3 when a new or renamed device affects a tracked device so it
        can be reassigned (start_ic3._verify_conf_apple_device_parameters):
            - A tracked device was renamed
            - The device has the name of a tracked device (a newer device that was
              restored from the tracked device's backup)
            - The device has the same owner, device type and Apple default name as a
              tracked device (a newer device that was set up as a new device)
        Other new devices are listed in the Event Log. They can be added in Configure.
        '''
        conf_devices = [conf_device for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCT] == self.AppleAcct.apple_id]
        tracked_device_ids = [conf_device[CONF_AADEV_DEVICE_ID] for conf_device in conf_devices]
        tracked_names      = [conf_device[CONF_AADEV_NAME] for conf_device in conf_devices]
        tracked_owner_keys = [AADev.owner_device_key
                                for AADev in [self.AppleAcct.AADev_by_device_id.get(device_id)
                                                    for device_id in tracked_device_ids]
                                if AADev]

        restart_reasons = []
        for AADev in renamed_AADev_items:
            if AADev.device_id in tracked_device_ids:
                list_add(restart_reasons, f"{AADev.name}, Tracked device was renamed")

        for AADev in new_AADev_items + renamed_AADev_items:
            if AADev.device_id in tracked_device_ids:
                continue
            if AADev.name in tracked_names:
                list_add(restart_reasons, f"{AADev.name}, Has a tracked device's name")
            elif AADev.owner_device_key in tracked_owner_keys:
                list_add(restart_reasons, f"{AADev.name}, May replace a tracked device")

        if restart_reasons:
            post_event( f"Apple Acct > {self.AppleAcct.apple_user}, "
                        f"Tracked Device Changed, Restarting iCloud3"
                        f"{CRLF_DOT}{CRLF_DOT.join(restart_reasons)}")
            Gb.was_icloud3_restart_requested = True
            return

        new_devices_msg = [f"{AADev.dname} ({AADev.model_display_name})"
                                for AADev in new_AADev_items]
        if new_devices_msg:
            post_event( f"Apple Acct > {self.AppleAcct.apple_user}, "
                        f"New Apple Device Detected, It can be tracked by adding it "
                        f"in iCloud3 Configure > iCloud3 Devices"
                        f"{CRLF_DOT}{CRLF_DOT.join(new_devices_msg)}")

#----------------------------------------------------------------------------
    def find_replacement_devices(self, AADev):
        '''
        Return the devices that may have replaced the tracked device (AADev):
            candidates   - Same owner and device type, a higher model number, not a
                           duplicate and not tracked by an iCloud3 device
            name_matches - Candidates with the tracked device's name without the model
                           or possessive ("Lillian's Apple Watch" for "Lillian-Watch")
        Returns (None, None) for AirPods and accessories, they are not replaced.

        Used by start_ic3._check_for_replacement_device and by the refresh check
        (_request_restart_if_tracked_device_replaced) so both use the same rules.
        '''
        if AADev.device_class in ['Accessory', AIRPODS_DN]:
            return None, None

        tracked_device_ids = [conf_device[CONF_AADEV_DEVICE_ID] for conf_device in Gb.conf_devices]
        candidates = [_AADev
                        for _AADev in self.AppleAcct.AADev_by_device_id.values()
                        if (_AADev
                            and _AADev.active
                            and _AADev.device_id not in tracked_device_ids
                            and _AADev.is_duplicate_dname is False
                            and _AADev.prs_id == AADev.prs_id
                            and _AADev.device_class == AADev.device_class
                            and _AADev.model_no > AADev.model_no)]
        name_matches = [_AADev for _AADev in candidates
                            if _AADev.owner_device_key == AADev.owner_device_key]

        return candidates, name_matches

#----------------------------------------------------------------------------
    def _request_restart_if_tracked_device_replaced(self):
        '''
        A newer device that was already in the Apple acct when iCloud3 started is not
        new or renamed, so _create_AADeviceData_objects does not see it. Check each
        tracked device during the refresh. If it is now retired (unpaired, erased) or
        has been offline for more than an hour and one device has its name, restart
        iCloud3 so start_ic3._verify_conf_apple_device_parameters tracks the newer
        device. After that, the tracked device is the newer one and this does not
        request another restart.
        '''
        restart_reasons = []
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_APPLE_ACCT] != self.AppleAcct.apple_id:
                continue

            AADev = self.AppleAcct.AADev_by_device_id.get(conf_device[CONF_AADEV_DEVICE_ID])
            if (AADev is None
                    or AADev.is_duplicate_dname
                    or (AADev.is_retired or AADev.is_offline_stale) is False):
                continue

            _, name_matches = self.find_replacement_devices(AADev)
            if name_matches and len(name_matches) == 1:
                list_add(restart_reasons,
                        f"{AADev.name} ({AADev.model_display_name}){RARROW}"
                        f"{name_matches[0].name} ({name_matches[0].model_display_name})")

        if restart_reasons:
            post_alert( f"Apple Acct > {self.AppleAcct.apple_user}, "
                        f"Newer Apple Device detected, Restarting iCloud3"
                        f"{CRLF_DOT}{CRLF_DOT.join(restart_reasons)}")
            Gb.was_icloud3_restart_requested = True

#----------------------------------------------------------------------------
    def _request_restart_if_tracked_device_missing(self, devices_data, locate_all_devices):
        '''
        A tracked device that was wiped, removed from the Apple acct or had Find My
        turned off is no longer in the device list. Its AADev keeps the last data
        it had so it is never retired or offline. An offline device (on an airplane)
        is still in the list and is not missing.

        The device is checked every 15-mins. If it is still missing after 1-hour (4
        refreshes, other devices may refresh it too), restart iCloud3. The startup
        (start_ic3._verify_conf_apple_device_parameters) changes the config to the
        device with the same name or posts the Unknown Apple Device error with a
        Repairs issue.

        A refresh is not used if it did not return any devices or if it was for the
        acct owner's devices only (locate_all_devices=False), the Family Sharing
        devices are not in it.
        '''
        if is_empty(devices_data):
            return

        device_ids = [device_data[ID] for device_data in devices_data]

        restart_reasons = []
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_APPLE_ACCT] != self.AppleAcct.apple_id:
                continue

            device_id = conf_device[CONF_AADEV_DEVICE_ID]
            AADev = self.AppleAcct.AADev_by_device_id.get(device_id)
            Device    = Gb.Devices_by_icloud_device_id.get(device_id)
            if AADev is None or Device is None or Device.is_inactive:
                continue

            if device_id in device_ids:
                if AADev.missing_since_secs > 0:
                    post_event(Device,
                                f"Apple Device Found > {AADev.dname}, "
                                f"Missing-{format_age(AADev.missing_since_secs)}")
                AADev.missing_since_secs = 0
                Device.set_button_prefix_icon('')
                continue

            if (locate_all_devices is False
                    and AADev.device_data.get('fmlyShare', False)):
                continue

            if AADev.missing_since_secs == 0:
                AADev.missing_since_secs = Gb.this_update_secs or time_now_secs()
                det_interval.update_all_device_fm_zone_sensors_interval(
                                                Device, MISSING_DEVICE_INTERVAL_SECS)
                Device.set_button_prefix_icon(RED_X)
                update_alert_sensor(Source=Device, error='missing_aadevice',
                                    alert_msg=( f"{Device.devicename} > "
                                                f"Apple Device no longer available ({AADev.dname})"))
                Gb.restart_at_secs = time_now_secs() + MISSING_DEVICE_RESTART_IN_SECS
                post_event( f"{EVLOG_ALERT}Apple Device > Device is No Longer Available, > "
                            f"{AADev.dname} ({AADev.model_display_name}), "
                            f"RecheckAt-{Device.next_update_time} "
                            f"({format_timer(MISSING_DEVICE_INTERVAL_SECS)}), "
                            f"iCloud3 will restart at "
                            f"{secs_to_time(Gb.restart_at_secs)}")
                continue

            # The location prefetch requests the data up to 15-secs before the
            # next update time so the 4th 15-min refresh is a little less than 1-hour
            if secs_since(AADev.missing_since_secs) >= MISSING_DEVICE_RESTART_IN_SECS - 60:
                list_add(restart_reasons,
                        f"{Device.fname} > {AADev.dname} ({AADev.model_display_name}), "
                        f"Missing-{format_age(AADev.missing_since_secs)}")

        if restart_reasons:
            post_alert( f"Apple Acct > {self.AppleAcct.apple_user}, "
                        f"Tracked Apple Device is not in the Apple Acct, Restarting iCloud3"
                        f"{CRLF_DOT}{CRLF_DOT.join(restart_reasons)}")
            Gb.was_icloud3_restart_requested = True

#----------------------------------------------------------------------------
    def _create_AADeviceData_object(self, device_id, device_data):

        AADev = iCloud_AppleAcctDevice(device_id,
                                    device_data,
                                    self.iCloudSession,
                                    self.params,
                                    'iCloud',
                                    'timeStamp',
                                    self)

        self.AppleAcct.AADev_by_device_id[device_id] = AADev

        dup_msg = ''
        log_debug_msg(  f"{self.AppleAcct.apple_user}, "
                        f"Create AppleAcctDeviceData object, "
                        f"{apple_user_dev(self.AppleAcct.apple_user, AADev.dname)}"
                        f"{dup_msg}")

        log_hdr = f"{apple_user_dev(self.AppleAcct.apple_user, AADev.dname)}, AADeviceData"
        log_data(log_hdr, AADev.device_data,
                    data_source='icloud', filter_id=self.AppleAcct.apple_id)



#----------------------------------------------------------------------------
    def _initialize_iCloud_AADev_object(self, device_id, device_data):

        AADev = self.AppleAcct.AADev_by_device_id[device_id]

        dname = self._remove_special_chars(AADev.name)
        self.AppleAcct.dup_icloud_dname_cnt[dname] = 0

        AADev.__init__(  device_id,
                            device_data,
                            self.iCloudSession,
                            self.params,
                            'iCloud', 'timeStamp',
                            self, )

        self.set_apple_acct_device_data_fields(device_id, AADev)

        post_greenbar_msg(f"Apple Acct > {self.AppleAcct.apple_user}, {AADev.dname}")
        log_debug_msg(  f"Initialize AADev_icloud object "
                        f"{apple_user_dev(self.AppleAcct.apple_user, AADev.dname)}")

        log_hdr = f"{apple_user_dev(self.AppleAcct.account_name, AADev.dname)}, iCloud Data"
        log_data(log_hdr, AADev.device_data,
                    data_source='icloud', is_log_level_rawdata=True, filter_id=self.AppleAcct.apple_id)

#----------------------------------------------------------------------
    def set_apple_acct_device_data_fields(self, device_id, AADev):
        '''
        The iCloud dictionaries contain info about the devices that is set
        up when the AADev object for the device is created. If the iCloud
        object is recreated during error, the device's AADev object already
        exists and is not recreated. The iCloud dictionaries need to be
        set up again.
        '''
        return

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')

        return name

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#   Device Service Call Handlers - Find Phone, Lost Phone Alerts
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if self.is_AADevices_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.AppleAcct.findme_url_root}{PLAYSOUND_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "clientContext": {"fmly": True}, }

        icloud_io.post(self.AppleAcct, url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def display_message(self, device_id, subject="iCloud Service Alert",
                        message="This is a note", sounds=False):
        '''
        Send a request to the device to display a message.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if self.is_AADevices_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.AppleAcct.findme_url_root}{MESSAGE_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "sound": sounds,
                "userText": True,
                "text": message, }

        icloud_io.post(self.AppleAcct, url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def lost_device(self, device_id, number,
                        message="This iPhone has been lost. Please call me.",
                        newpasscode=""):
        '''
        Send a request to the device to trigger 'lost mode'.

        The device will show the message in `text`, and if a number has
        been passed, then the person holding the device can call
        the number without entering the pass
        '''
        if self.is_AADevices_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.AppleAcct.findme_url_root}{LOSTDEVICE_ENDPOINT}"
        data = {"text": message,
                "userText": True,
                "ownerNbr": number,
                "lostModeEnabled": True,
                "trackingEnabled": True,
                "device": device_id,
                "passcode": newpasscode, }

        icloud_io.post(self.AppleAcct, url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def _create_test_data(self, device_id, device_data):
        '''
        Create duplicate devices test data in _AADev using data from the
        current device
        '''
        device_data_test1 = device_data.copy()
        device_data_test2 = device_data.copy()
        device_data_test1[LOCATION] = device_data[LOCATION].copy()
        device_data_test2[LOCATION] = device_data[LOCATION].copy()

        device_data[LOCATION]['timeStamp'] = 0

        self._create_AADeviceData_object(device_id, device_data)

        device_data_test1[NAME] = f"TestDevice-1"
        device_data_test1[ID]   = f"XX1_{device_id}"
        device_data_test1[LOCATION]['timeStamp'] -= 3000000000
        device_data_test1['rawDeviceModel'] = 'iPad8,91'
        self._create_AADeviceData_object(device_data_test1[ID], device_data_test1)

        device_data_test2[NAME] = f"TestDevice-2"
        device_data_test2[ID]   = f"XX2_{device_id}"
        device_data_test2['rawDeviceModel'] = 'iPad8,92'
        self._create_AADeviceData_object(device_data_test2[ID], device_data_test2)

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return (f"<AppleAcct.AADevices: {self.AppleAcct.setup_time}-{self.setup_time}-"
                    f"{self.AppleAcct.account_owner}>")
        except:
            return (f"<AppleAcct.AADevices: NotSetUp>")
