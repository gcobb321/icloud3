
from ..global_variables import GlobalVariables as Gb
from ..const            import (AIRPODS_FNAME, NONE_FNAME,
                                EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS,
                                HHMMSS_ZERO, RARROW, DOT, CRLF, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                ICLOUD, NAME, ID,
                                APPLE_SERVER_ENDPOINT,
                                ICLOUD_HORIZONTAL_ACCURACY,
                                LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE, LATITUDE, LONGITUDE,
                                ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW,
                                ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES,
                                CONF_USERNAME, CONF_APPLE_ACCOUNT,
                                CONF_PASSWORD, CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_FAMSHR_DEVICE_ID, CONF_LOG_LEVEL_DEVICES,
                                DEVICE_DISPLAY_NAMES_FILTERS
                                )
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del,
                                encode_password, decode_password, username_id, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging  import (log_exception, )
from ..utils            import gps

import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

DEVICE_DATA_FILTER_OUT = [
    'features', 'scd',
    'rm2State', 'pendingRemoveUntilTS', 'repairReadyExpireTS', 'repairReady', 'lostModeCapable', 'wipedTimestamp',
    'encodedDeviceId', 'scdPh', 'locationCapable', 'trackingInfo', 'nwd', 'remoteWipe', 'canWipeAfterLock', 'baUUID',
    'snd', 'continueButtonTitle', 'alertText', 'cancelButtonTitle', 'createTimestamp',  'alertTitle',
    'lockedTimestamp', 'locFoundEnabled', 'lostDevice', 'pendingRemove', 'maxMsgChar', 'darkWake', 'wipeInProgress',
    'repairDeviceReason', 'deviceColor', 'deviceDiscoveryId', 'activationLocked', 'passcodeLength',
    ]
    # 'BTR', 'LLC', 'CLK', 'TEU', 'SND', 'ALS', 'CLT', 'PRM', 'SVP', 'SPN', 'XRM', 'NWF', 'CWP',
    # 'MSG', 'LOC', 'LME', 'LMG', 'LYU', 'LKL', 'LST', 'LKM', 'WMG', 'SCA', 'PSS', 'EAL', 'LAE', 'PIN',
    # 'LCK', 'REM', 'MCS', 'REP', 'KEY', 'KPD', 'WIP',



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   AADevData Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable AppleAcct.AADevData_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud_AppleAcctDeviceData():
    '''
    AADevData stores all the device data for each Apple Acct

    Parameters:
        - device_id = iCloud device id of the device
        - device_data = data received from Apple
        - iCloudSession = AppleAcct instance that authenticates and gets the data
        - params = ?
        - data_source = 'iCloud'
        - timestamp_field = name of the location timestamp field in device_data
        - AADevices = AADevices object that created this AADevData object
        - device_data_name = name of the device in device_data (Gary-iPhone)
    '''

    def __init__(self, device_id,
                        device_data,
                        iCloudSession,
                        params,
                        data_source,
                        timestamp_field,
                        AADevices,
                        device_data_name,):

        self.setup_time    = time_now()
        self.AppleAcct     = AADevices.AppleAcct # AppleAcct object (Apple Acct) with the device data
        self.iCloudSession = iCloudSession

        # __init__ is run several times during to initialize the AADevData fields
        # Initialize the identity fields on the initial create
        if device_id not in self.AppleAcct.AADevData_by_device_id:
            self.device_id       = device_id
            self.params          = params
            self.data_source     = data_source
            self.timestamp_field = timestamp_field
            self.AADevices       = AADevices           # iCloud object creating this AADevData object

        try:
            # Only update the device name fields when the AADevData object is created
            # or when it was changed on the device and iCloud3 was restarted. Setting
            # it up again if the AADevData is just being reinstalled creates errors
            # detecting duplicate names.
            name_update_flag = (self.name != device_data_name)
        except:
            name_update_flag = True

        if name_update_flag:
            self.name            = device_data_name
            self.fname_original  = ''                               # Original dname after cleanup
            self.fname_dup_suffix= ''                               # Suffix added to fname if duplicates
            self.fname           = self.device_data_fname_dup_check # Clean up fname and check for duplicates

        self.evlog_alert_char= ''
        self.ic3_devicename  = Gb.devicenames_by_icloud_dname.get(self.fname, '')
        self.Device          = Gb.Devices_by_devicename.get(self.ic3_devicename)

        self.device_data     = device_data
        self.status_code     = 0

        self.update_secs     = time_now_secs()
        self.location_secs   = 0
        self.location_time   = HHMMSS_ZERO
        self.last_used_location_secs = 0
        self.last_loc_time           = ''               # location_time_gps_acc from last general update
        self.last_loc_time_gps       = ''               # location_time_gps_acc from last general update
        self.last_used_location_time = HHMMSS_ZERO
        self.last_requested_loc_time_gps = ''           # location_time_gps_acc from last time requested

        self.battery_level = 0

        self.set_located_time_battery_info()
        self.device_data[DATA_SOURCE] = self.data_source
        self.device_data[CONF_IC3_DEVICENAME] = self.ic3_devicename
        self.raw_model = self.device_data.get('rawDeviceModel', self.device_class).replace('_', '')

        Gb.model_display_name_by_raw_model[self.raw_model] = self.icloud_device_display_name

#----------------------------------------------------------------------
    @property
    def device_id8(self):
        return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def fname_device_id(self):
        return f"{self.fname} ({self.device_id8})"

#----------------------------------------------------------------------
    @property
    def devicename(self):
        if Device := Gb.Devices_by_icloud_device_id.get(self.device_id):
            return Device.devicename
        elif self.is_data_source_ICLOUD:
            return self.fname
        else:
            return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def family_share_device(self):
        return self.device_data['fmlyShare']

#----------------------------------------------------------------------
    @property
    def device_data_fname_dup_check(self):
        '''
        Determine if the iCloud device being set up is the same name as one that has already
        been set up. Is so, add periods('.') to the end of the fname to make it unique.
        Also set the fname suffix value.
        '''
        # Remove non-breakable space and right quote mark
        dname = self.fname_original = self._remove_special_chars(self.name)

        # This is a tracked and configured device if the device_id is already used
        conf_devicename = self._find_conf_device_devicename(CONF_FAMSHR_DEVICE_ID, self.device_id)
        if conf_devicename:
            return dname

        # It is ok if dname has not been seen
        if dname not in self.AppleAcct.device_id_by_icloud_dname:
            return dname

        # This is not a tracked and configured device if the dname is not used
        # but maybe a dupe because the dname is found with a different device_id
        conf_devicename = self._find_conf_device_devicename(CONF_FAMSHR_DEVICENAME, dname)
        if conf_devicename == '':
            found_before = (dname in self.AppleAcct.device_id_by_icloud_dname)
            if found_before is False:
                return dname

        # Dupe dname, it has not been seen and dname has been used
        # Add a period to dname to make it unique
        _dname = f"{dname}."
        while _dname in self.AppleAcct.device_id_by_icloud_dname:
            _dname += '.'
        self.fname_dup_suffix = _dname.replace(dname, '')

        return _dname

#......................................................................
    def _find_conf_device_devicename(self, field, field_value):
        '''
        Cycle through the conf_devices and return the ic3_devicename that matches
        the requested field/field_value
        '''
        conf_devicename = [conf_device[CONF_IC3_DEVICENAME]
                                for conf_device in Gb.conf_devices
                                if (conf_device[CONF_APPLE_ACCOUNT] == self.AppleAcct.username
                                    and conf_device[field] == field_value)]

        if conf_devicename:
            return conf_devicename[0]
        else:
            return ''

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')
        name = name.replace(u'\2019', "'")
        return name

#----------------------------------------------------------------------
    @property
    def icloud_device_info(self):
        return f"{self.fname} ({self.device_identifier})"

#----------------------------------------------------------------------
    @property
    def device_status_code(self):
        return int(self.device_data.get(ICLOUD_DEVICE_STATUS, '0'))
#----------------------------------------------------------------------
    @property
    def device_status_msg(self):
        status_code = self.device_data.get(ICLOUD_DEVICE_STATUS, '0')
        return (f"{DEVICE_STATUS_CODES.get(status_code, 'Unknown')}/"
                f"{status_code}")

#----------------------------------------------------------------------
    @property
    def device_identifier(self):
        '''
        Format device name:
            - iPhone 14,2; iPhone15,2)
            - Gary-iPhone
        '''
        if self.is_data_source_ICLOUD:
            display_name = self.device_data['deviceDisplayName'].split(' (')[0]
            display_name = display_name.replace('Series ', '')
            if self.device_data.get('rawDeviceModel').startswith(AIRPODS_FNAME):
                device_class = AIRPODS_FNAME
            else:
                device_class = self.device_data.get('deviceClass', '')

            return (f"{self.icloud_device_display_name}; {self.raw_model}").replace("’", "'")

        else:
            return self.name.replace("’", "'")

#----------------------------------------------------------------------
    @property
    def device_class(self):
        if self.device_data.get('rawDeviceModel').startswith(AIRPODS_FNAME):
            return AIRPODS_FNAME
        else:
            return self.device_data.get('deviceClass', '')

#----------------------------------------------------------------------
    @property
    def icloud_device_display_name(self):
        display_name = self.device_data['deviceDisplayName']
        for from_str, to_str in DEVICE_DISPLAY_NAMES_FILTERS.items():
            display_name = display_name.replace(from_str, to_str)

        idx = display_name.find('-inch')
        if idx > 0:
            display_name = display_name[:idx-3] + display_name[idx+5:]

        #v3.3 - Remove spaces from display name
        return display_name.replace(' ', '')

#----------------------------------------------------------------------
    @property
    def icloud_device_model_info(self):
        return [self.device_data['rawDeviceModel'].replace("_", ""),    # iPhone15,2
                self.device_data['modelDisplayName'],                   # iPhone
                self.icloud_device_display_name]                        # iPhone 14 Pro

#----------------------------------------------------------------------
    @property
    def is_data_source_ICLOUD(self):
        return (self.data_source in [ICLOUD])

    @property
    def loc_time_gps(self):
        return f"{self.location_time}/±{self.gps_accuracy}m"

    @property
    def gps_accuracy(self):
        """ Get location gps accuracy or 9999 if not available """

        try:
            return round(self.location[ICLOUD_HORIZONTAL_ACCURACY])
        except:
            return 9999

    @property
    def is_gps_poor(self):
        return (self.gps_accuracy > Gb.gps_accuracy_threshold
                    or self.gps_accuracy == 9999)

    @property
    def is_gps_good(self):
        return not self.is_gps_poor

    @property
    def gps_accuracy_msg(self):
        """ GPS Accuracy text if available or unknown """
        if self.gps_accuracy == 9999:
            return  'Unknown'
        return round(self.gps_accuracy)

#----------------------------------------------------------------------------
    def save_new_device_data(self, device_data):
        '''Update the device data.'''
        if self.AppleAcct.china_gps_coordinates != '':
            device_data = self.convert_GCJ02_BD09_to_WGS84(device_data)

        try:
            self.last_loc_time     = self.location_time
            self.last_loc_time_gps = f"{self.location_time}/±{self.gps_accuracy}m"
        except:
            self.last_loc_time_gps = ''

        try:
            self.status_code = device_data['snd']['status_code']
        except:
            pass

        filtered_device_data = {k: v    for k, v in device_data.items()
                                        if k not in DEVICE_DATA_FILTER_OUT}

        # self.device_data.clear()
        self.device_data.update(filtered_device_data)
        self.set_located_time_battery_info()

        self.device_data[DATA_SOURCE] = self.data_source
        return

#----------------------------------------------------------------------------
    def status(self, additional_fields=[]):
        '''
        Returns status information for device.
        This returns only a subset of possible properties.
        '''
        self.AADevices.refresh_device(requested_by_devicename=self.device_id)

        fields = ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]
        fields += additional_fields

        properties = {}
        for field in fields:
            properties[field] = self.location.get(field)

        return properties

#----------------------------------------------------------------------------
    @property
    def is_offline(self):
        return self.device_data[ICLOUD_DEVICE_STATUS] == 201

#----------------------------------------------------------------------------
    @property
    def is_location_data_available(self):
        return not (LOCATION not in self.device_data
                    or self.device_data[LOCATION] == {}
                    or self.device_data[LOCATION] is None)
#----------------------------------------------------------------------------
    def convert_GCJ02_BD09_to_WGS84(self, device_data):

        latitude  = device_data[LOCATION][LATITUDE]
        longitude = device_data[LOCATION][LONGITUDE]

        if self.AppleAcct.china_gps_coordinates == 'GCJ02':
            latitude, longitude = gps.gcj_to_wgs(latitude, longitude)
        elif self.AppleAcct.china_gps_coordinates == 'BD09':
            latitude, longitude = gps.bd_to_wgs(latitude, longitude)

        return device_data

#----------------------------------------------------------------------------
    def set_located_time_battery_info(self):

        try:
            self.device_data[CONF_IC3_DEVICENAME] = self.ic3_devicename

            if self.is_location_data_available:
                self.device_data[LOCATION][TIMESTAMP] = int(self.device_data[LOCATION][self.timestamp_field] / 1000)
                self.device_data[LOCATION][LOCATION_TIME] = secs_to_time(self.device_data[LOCATION][TIMESTAMP])
                self.location_secs = self.device_data[LOCATION][TIMESTAMP]
                self.location_time = self.device_data[LOCATION][LOCATION_TIME]
            else:
                self.device_data[LOCATION] = {self.timestamp_field: 0}
                self.device_data[LOCATION][TIMESTAMP] = 0
                self.device_data[LOCATION][LOCATION_TIME] = HHMMSS_ZERO
                self.location_secs = 0
                self.location_time = HHMMSS_ZERO

            # This will create old location for testing
            # if self.name=='Gary-iPhone':
            #     raise AppleAcctAPIResponseException('test error', 404)
            #     self.device_data[LOCATION][TIMESTAMP]     = int(self.device_data[LOCATION][self.timestamp_field] / 1000) - 600
            #     _evlog('gary_iphone', f"Reduce loc time to {secs_to_time(self.device_data[LOCATION][TIMESTAMP])}")


        except TypeError:
            # This will happen if there is no location data in device_data
            self.device_data[LOCATION] = {TIMESTAMP: 0, LOCATION_TIME: HHMMSS_ZERO}
            self.location_secs = 0
            self.location_time = HHMMSS_ZERO

        except Exception as err:
            log_exception(err)
            self.device_data[LOCATION] = {TIMESTAMP: 0, LOCATION_TIME: HHMMSS_ZERO}
            self.location_secs = 0
            self.location_time = HHMMSS_ZERO

        self.update_secs = time_now_secs()

        # Reformat and convert batteryStatus and batteryLevel
        try:
            self.battery_level  = self.device_data.get(ICLOUD_BATTERY_LEVEL, 0)
            self.battery_level  = round(self.battery_level*100)
            self.battery_status = self.device_data[ICLOUD_BATTERY_STATUS]
            if self.battery_level > 99:
                self.battery_status = 'Charged'
            elif self.battery_status in ['Charging', 'Unknown']:
                pass
            elif self.battery_level > 0 and self.battery_level < BATTERY_LEVEL_LOW:
                self.battery_status = 'Low'

            self.device_data[BATTERY_LEVEL]  = self.battery_level
            self.device_data[BATTERY_STATUS] = self.battery_status
        except:
            pass

#----------------------------------------------------------------------------
    @property
    def data(self):
        '''Returns all of the device's data'''
        return self.device_data

    @property
    def location(self):
        '''Return the device's location data'''
        return self.device_data["location"]

    def __repr__(self):
        try:
            return f"<AADevData: {self.setup_time}-{self.AppleAcct.username_base}-{self.name}-{self.device_id[:8]}"
        except:
            return f"<AADevData: Undefined>"
