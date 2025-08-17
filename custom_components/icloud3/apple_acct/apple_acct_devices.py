from ..global_variables import GlobalVariables as Gb
from ..const            import (AIRPODS_FNAME, NONE_FNAME,
                                EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS,
                                HHMMSS_ZERO, RARROW, DOT, CRLF, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                ICLOUD, NAME, ID, LOCATION,  ICLOUD_DEVICE_STATUS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_LOG_LEVEL_DEVICES,
                                )
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging  import (post_event, post_monitor_msg, post_error_msg,
                                _evlog, _log,
                                log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                log_data, log_exception, log_data_unfiltered, filter_data_dict, )

from .apple_acct_device_data import PyiCloud_AppleAcctDeviceData

import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Find iCloud Devices service (originally find my iphone)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
REFRESH_ENDPOINT    = "/fmipservice/client/web/refreshClient"
PLAYSOUND_ENDPOINT  = "/fmipservice/client/web/playSound"
MESSAGE_ENDPOINT    = "/fmipservice/client/web/sendMessage"
LOSTDEVICE_ENDPOINT = "/fmipservice/client/web/lostDevice"

class PyiCloud_AppleAcctDevices():
    '''
    The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.
    '''

    def __init__(self,  PyiCloud,
                        PyiCloudSession,
                        params,
                        task="RefreshData",
                        device_id=None, subject=None, message=None,
                        sounds=False, number="", newpasscode=""):

        self.setup_time      = time_now()
        self.PyiCloudSession = PyiCloudSession
        self.PyiCloud        = PyiCloud
        self.username_base   = self.PyiCloud.username_base

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
            if isnot_empty(self.PyiCloud.device_id_by_icloud_dname):
                return
        except:
            pass

        self.refresh_device()

        Gb.devices_not_set_up = self._get_conf_icloud_devices_not_set_up()
        if Gb.devices_not_set_up == []:
            return

        #self.refresh_device()

#----------------------------------------------------------------------------
    def _get_conf_icloud_devices_not_set_up(self):
        '''
        Return a list of devices in the iCloud3 configuration file that are
        not in the  iCloud data returned from Apple.
        '''
        return [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_FAMSHR_DEVICENAME] != NONE_FNAME
                        and conf_device[CONF_FAMSHR_DEVICENAME] not in \
                                self.PyiCloud.device_id_by_icloud_dname)]

#---------------------------------------------------------------------------
    @property
    def is_AADevices_setup_complete(self):
        return self.PyiCloud.is_AADevices_setup_complete

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

#----------------------------------------------------------------------------
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
            if (Gb.internet_error
                    or self.is_AADevices_setup_complete is False):
                return False

            #locate_all_devices = True if locate_all_devices is None else locate_all_devices
            locate_all_devices = locate_all_devices               if locate_all_devices is not None \
                            else self.PyiCloud.locate_all_devices if self.PyiCloud.locate_all_devices is not None \
                            else True

            if requested_by_devicename:
                _Device = Gb.Devices_by_devicename[requested_by_devicename]
                last_update_loc_time = _Device.last_update_loc_time
            else:
                last_update_loc_time = '?'

            if locate_all_devices is False:
                device_msg = f"OwnerDev-{len(Gb.owner_device_ids_by_username.get(self.PyiCloud.username, []))}"
            else:
                device_msg = f"AllDevices-{len(Gb.Devices_by_username.get(self.PyiCloud.username, []))}"

            log_debug_msg( f"Apple Acct > {self.PyiCloud.username_base}, "
                                f"RefreshRequestBy-{requested_by_devicename}, "
                                f"LocateAllDev-{locate_all_devices}, {device_msg}, LastLoc-{last_update_loc_time}")

            url  = f"{self.PyiCloud.findme_url_root}{REFRESH_ENDPOINT}"
            data = {"clientContext":{
                        "fmly": locate_all_devices,
                        "shouldLocate": True,
                        "selectedDevice": device_id,
                        "deviceListVersion": 1, },
                    "accountCountryCode": self.PyiCloud.session_data_token.get("account_country"),
                    "dsWebAuthToken": self.PyiCloud.session_data_token.get("session_token"),
                    "trustToken": self.PyiCloud.session_data_token.get("trust_token", ""),
                    "extended_login": True,}

            try:
                self.devices_data = self.PyiCloudSession.post(url, params=self.params, data=data)

            except Exception as err:
                # log_exception(err)
                self.devices_data = {}
                log_debug_msg(  f"{self.PyiCloud.username_base}, "
                                f"No data returned from iCloud refresh request {err=}")

            if self.PyiCloudSession.response_code == 501:
                self._set_service_available(False)
                post_event( f"{EVLOG_ALERT}iCLOUD ALERT > {self.PyiCloud.account_owner}, "
                            f"Apple Acct Data Source is not available. "
                            f"The web url providing location data returned a "
                            f"Service Not Available error")
                return None

            self.update_device_location_data(requested_by_devicename, self.devices_data.get("content", {}))
            return isnot_empty(self.PyiCloud.AADevData_by_device_id)

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
            self.PyiCloud.last_refresh_secs = time_now_secs()
            self.PyiCloud.update_requested_by = requested_by_devicename
            monitor_msg = f"UPDATED iCloud Data > RequestedBy-{requested_by_devicename}"

            for device_data in devices_data:

                # TEST CODE - Create duplicate device
                # _log("TEST CODE ENABLED")
                # if device_data[NAME] == 'Gary-iPad':
                #     device_data[NAME] = 'Lillian-iPad'
                #     device_data[LOCATION] = {}


                device_data[NAME] = device_data_name = self._remove_special_chars(device_data[NAME])
                        # AADevData._remove_special_chars(device_data[NAME])

                device_id = device_data[ID]
                aadevdata_hdr_msg = ''

                if (device_data_name in Gb.conf_icloud_dnames
                        and requested_by_devicename != 'reload_all_devices'
                        and Gb.start_icloud3_inprocess_flag):
                    pass

                # only check tracked/monitored devices for location data
                elif (LOCATION not in device_data
                        or device_data[LOCATION] == {}
                        or device_data[LOCATION] is None):
                    if device_id not in Gb.devices_without_location_data:
                        list_add(Gb.devices_without_location_data, device_data_name)
                        aadevdata_hdr_msg = 'NO LOCATION'
                        if device_data[ICLOUD_DEVICE_STATUS] == 203:
                            aadevdata_hdr_msg += ', OFFLINE'
                            monitor_msg += f"{CRLF_STAR}OFFLINE > "
                        else:
                            monitor_msg += f"{CRLF_STAR}NO LOCATION > "
                        monitor_msg += (f"{self.PyiCloud.account_owner}, "
                                        f"{device_data_name}/"
                                        f"{device_id[:8]}, "
                                        f"{device_data['modelDisplayName']} "
                                        f"({device_data['rawDeviceModel']})")

                # Create AADevData object if the device_id is not already set up
                if device_id not in self.PyiCloud.AADevData_by_device_id:
                    # if device_data_name == 'Gary-iPad':
                    #     self._create_test_data(device_id, device_data_name, device_data)
                    # else:
                    device_msg = self._create_AADeviceData_object(device_id, device_data_name, device_data)
                    monitor_msg += device_msg
                    #continue

                # The PyiCloudSession is not recreated on a restart if it already is valid but we need to
                # initialize all devices, not just tracked ones on an iC3 restart.
                elif Gb.start_icloud3_inprocess_flag:
                    device_msg = self._initialize_iCloud_AADevData_object(device_id, device_data_name, device_data)
                    monitor_msg += device_msg
                    #continue

                # Non-tracked devices are not updated
                _AADevData = self.PyiCloud.AADevData_by_device_id[device_id]

                _Device = _AADevData.Device
                if (_AADevData.Device is None
                        or LOCATION not in _AADevData.device_data):
                    continue

                _AADevData.save_new_device_data(device_data)

                if _AADevData.location_secs == 0:
                    continue

                if ('all' in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                        or _AADevData.ic3_devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    log_hdr = ( f"{self.PyiCloud.username_base}{LINK}"
                                f"{device_data_name}/{_Device.devicename}{RLINK}, "
                                f"{aadevdata_hdr_msg}, iCloud Data ")
                    log_data(log_hdr, _AADevData.device_data,
                                data_source='icloud', filter_id=self.PyiCloud.username)

                if _AADevData.last_loc_time_gps == _AADevData.loc_time_gps:
                    last_loc_time_gps_msg = last_loc_time_msg = ''
                else:
                    last_loc_time_gps_msg = f"{_AADevData.last_loc_time_gps}{RARROW}"
                    last_loc_time_msg     = f"{_AADevData.last_loc_time}{RARROW}"
                    _Device.loc_time_updates_icloud.append(_AADevData.location_time)

                event_msg =(f"Located > iCloud-"
                            f"{last_loc_time_msg}"
                            f"{_AADevData.location_time}, ")

                if secs_since(_AADevData.location_secs) > _Device.old_loc_threshold_secs + 5:
                    event_msg += f", Old, {format_age(_AADevData.location_secs)}"

                elif _AADevData.battery_level is None:
                    _AADevData.battery_level = 0

                elif _AADevData.battery_level > 0:
                    if _AADevData.battery_level != _Device.dev_data_battery_level:
                        event_msg += f"{_Device.dev_data_battery_level}%{RARROW}"
                    event_msg += f"{_AADevData.battery_level}%"

                if Gb.start_icloud3_inprocess_flag is True:
                    pass

                elif requested_by_devicename == _Device.devicename:
                    _AADevData.last_requested_loc_time_gps = _AADevData.loc_time_gps
                    if last_loc_time_msg:
                        post_event(_Device.devicename, event_msg)

                elif _Device.isin_zone:
                    post_monitor_msg(_Device.devicename, event_msg)

                elif _AADevData.location_secs > 0:
                    post_event(_Device.devicename, event_msg)

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _create_test_data(self, device_id, device_data_name, device_data):
        '''
        Create duplicate devices test data in _AADevData using data from the
        current device
        '''
        device_data_test1 = device_data.copy()
        device_data_test2 = device_data.copy()
        device_data_test1[LOCATION] = device_data[LOCATION].copy()
        device_data_test2[LOCATION] = device_data[LOCATION].copy()

        device_data[LOCATION]['timeStamp'] = 0

        monitor_msg +=\
            self._create_AADeviceData_object(device_id, device_data_name, device_data)

        device_data_test1[NAME] = f"{device_data_name}(1)"
        device_data_test1[ID]   = f"XX1_{device_id}"
        device_data_test1[LOCATION]['timeStamp'] -= 3000000000
        device_data_test1['rawDeviceModel'] = 'iPad8,91'

        monitor_msg +=\
            self._create_AADeviceData_object(device_data_test1[ID], device_data_test1[NAME], device_data_test1)
        device_data_test2[NAME] = f"{device_data_name}(2)"
        device_data_test2[ID]   = f"XX2_{device_id}"
        device_data_test2['rawDeviceModel'] = 'iPad8,92'
        monitor_msg +=\
            self._create_AADeviceData_object(device_data_test2[ID], device_data_test2[NAME], device_data_test2)

#----------------------------------------------------------------------------
    def _create_AADeviceData_object(self, device_id, device_data_name, device_data):

        _AADevData = PyiCloud_AppleAcctDeviceData(device_id,
                                    device_data,
                                    self.PyiCloudSession,
                                    self.params,
                                    'iCloud',
                                    'timeStamp',
                                    self,
                                    device_data_name,)

        self.set_apple_acct_device_data_fields(device_id, _AADevData)

        log_debug_msg(  f"{self.PyiCloud.username_base}, "
                        f"Create AppleAcctDeviceData object, "
                        f"{self.PyiCloud.account_owner}{LINK}{_AADevData.fname}{RLINK}")

        log_hdr = f"{self.PyiCloud.account_name}{LINK}{_AADevData.fname}{RLINK}, AADeviceData"
        log_data(log_hdr, _AADevData.device_data,
                    data_source='icloud', filter_id=self.PyiCloud.username)

        dup_msg = f" as {_AADevData.fname}" if _AADevData.fname_dup_suffix else ''

        return (f"{CRLF_DOT}ADDED > {device_data_name}{dup_msg}, {_AADevData.loc_time_gps}")

#----------------------------------------------------------------------------
    def _initialize_iCloud_AADevData_object(self, device_id, device_data_name, device_data):


        _AADevData = self.PyiCloud.AADevData_by_device_id[device_id]

        # dname = _AADevData._remove_special_chars(_AADevData.name)
        dname = self._remove_special_chars(_AADevData.name)
        self.PyiCloud.dup_icloud_dname_cnt[dname] = 0

        _AADevData.__init__(  device_id,
                            device_data,
                            self.PyiCloudSession,
                            self.params,
                            'iCloud', 'timeStamp',
                            self,
                            device_data_name,)

        self.set_apple_acct_device_data_fields(device_id, _AADevData)

        log_debug_msg(  f"Initialize AADevData_icloud object "
                        f"{self.PyiCloud.username_base}{LINK}<{_AADevData.fname}, "
                        f"{device_data_name}")

        log_hdr = f"{self.PyiCloud.account_name}{LINK}{_AADevData.fname}{RLINK}, iCloud Data"
        log_data(log_hdr, _AADevData.device_data,
                    data_source='icloud', filter_id=self.PyiCloud.username)

        return (f"{CRLF_DOT}INITIALIZED > {device_data_name}, {_AADevData.loc_time_gps}")

#----------------------------------------------------------------------
    def set_apple_acct_device_data_fields(self, device_id, _AADevData):
        '''
        The iCloud dictionaries contain info about the devices that is set
        up when the AADevData object for the device is created. If the iCloud
        object is recreated during error, the device's AADevData object already
        exists and is not recreated. The iCloud dictionaries need to be
        set up again.
        '''
        list_add(self.PyiCloud.AADevData_items, _AADevData)
        self.PyiCloud.AADevData_by_device_id[device_id]             = _AADevData
        self.PyiCloud.device_id_by_icloud_dname[_AADevData.fname]   = device_id
        self.PyiCloud.icloud_dname_by_device_id[device_id]          = _AADevData.fname
        self.PyiCloud.device_info_by_icloud_dname[_AADevData.fname] = _AADevData.icloud_device_info
        self.PyiCloud.device_model_info_by_fname[_AADevData.fname]  = _AADevData.icloud_device_model_info
        self.PyiCloud.device_model_name_by_icloud_dname[_AADevData.fname] = _AADevData.icloud_device_display_name

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')
        name = name.replace(u'\2019', "'")

        return name

#----------------------------------------------------------------------------
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if self.is_AADevices_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.PyiCloud.findme_url_root}{PLAYSOUND_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "clientContext": {"fmly": True}, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
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

        url  = f"{self.PyiCloud.findme_url_root}{MESSAGE_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "sound": sounds,
                "userText": True,
                "text": message, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
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

        url  = f"{self.PyiCloud.findme_url_root}{LOSTDEVICE_ENDPOINT}"
        data = {"text": message,
                "userText": True,
                "ownerNbr": number,
                "lostModeEnabled": True,
                "trackingEnabled": True,
                "device": device_id,
                "passcode": newpasscode, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return (f"<PyiCloud.AADevices: {self.PyiCloud.setup_time}-{self.setup_time}-"
                    f"{self.PyiCloud.account_owner}>")
        except:
            return (f"<PyiCloud.AADevices: NotSetUp>")
