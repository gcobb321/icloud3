
from ..global_variables import GlobalVariables as Gb
from ..const            import (AIRPODS, AIRPODS_DN, NONE_FNAME,
                                EVLOG_NOTICE, EVLOG_ALERT,
                                HHMMSS_ZERO,
                                ICLOUD, NAME, ID,
                                APPLE_SERVER_ENDPOINT,
                                ICLOUD_HORIZONTAL_ACCURACY,
                                LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE, LATITUDE, LONGITUDE,
                                ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                BATTERY_LEVEL, BATTERY_LEVEL_LOW,
                                ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES,
                                DEVICE_DISPLAY_NAMES_FILTERS, REPLACED_DEVICE_OFFLINE_SECS, )
from ..const_config     import (BATTERY_STATUS, CONF_APPLE_ACCT, CONF_APPLE_ACCT, CONF_PASSWORD,
                                CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL, CONF_IC3_DEVICENAME,
                                CONF_FNAME, CONF_AADEV_NAME, CONF_AADEV_DEVICE_ID,
                                CONF_LOG_LEVEL_DEVICES, )
from ..const_char       import (LINK, RLINK, LLINK, DOTS, RARROW, DOT, CRLF, CRLF_DOT, CRLF_STAR,
                                CRLF_CHK, CRLF_HDOT, )
from ..utils.utils      import (instr, is_empty, isnot_empty, list_add, list_del,
                                encode_password, decode_password,
                                apple_user, apple_id_dev, apple_user_dev, )
from ..utils.time_util  import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging  import (_log, log_exception, )
from ..utils            import (gps, )
from .device_name_parser import name_device_type_key

import re
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

DEVICE_DATA_FILTER_OUT = [
    'features', 'scd', 'activationLocked',
    'rm2State', 'pendingRemoveUntilTS', 'repairReadyExpireTS', 'repairReady', 'lostModeCapable', 'wipedTimestamp',
    'encodedDeviceId', 'scdPh', 'locationCapable', 'trackingInfo', 'nwd', 'remoteWipe', 'canWipeAfterLock', 'baUUID',
    'continueButtonTitle', 'alertText', 'cancelButtonTitle', 'createTimestamp',  'alertTitle',
    'lockedTimestamp', 'locFoundEnabled', 'pendingRemove', 'maxMsgChar', 'darkWake', 'wipeInProgress',
    'repairDeviceReason', 'deviceColor', 'deviceDiscoveryId', 'passcodeLength',
    'BTR', 'LLC', 'CLK', 'TEU', 'SND', 'ALS', 'CLT', 'PRM', 'SVP', 'SPN', 'XRM', 'NWF', 'CWP',
    'MSG', 'LOC', 'LME', 'LMG', 'LYU', 'LKL', 'LST', 'LKM', 'WMG', 'SCA', 'PSS', 'EAL', 'LAE', 'PIN',
    'LCK', 'REM', 'MCS', 'REP', 'KEY', 'KPD', 'WIP',
]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   AADev Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable AppleAcct.AADev_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud_AppleAcctDevice():
    '''
    AADev stores all the device data for each Apple Acct

    Parameters:
        - device_id = iCloud device id of the device
        - device_data = data received from Apple
        - iCloudSession = AppleAcct instance that authenticates and gets the data
        - params = ?
        - data_source = 'iCloud'
        - timestamp_field = name of the location timestamp field in device_data
        - AADevices = AADevices object that created this AADev object
        - device_data_name = name of the device in device_data (Gary-iPhone)
    '''

    def __init__(self, device_id,
                        device_data,
                        iCloudSession,
                        params,
                        data_source,
                        timestamp_field,
                        AADevices):

        self.setup_time      = time_now()
        self.device_id       = device_id
        self.device_data     = device_data
        self.params          = params
        self.data_source     = data_source
        self.timestamp_field = timestamp_field

        self.AADevices       = AADevices           # iCloud object creating this AADev object
        self.AppleAcct       = AADevices.AppleAcct # AppleAcct object (Apple Acct) with the device data
        self.iCloudSession   = iCloudSession

        self.apple_id        = self.AppleAcct.apple_id
        self.name            = self._remove_special_chars(device_data[NAME])
        self.dname           = self.name
        self.apple_id_dev    = apple_id_dev(self.apple_id, self.dname)
        self.apple_user_dev  = apple_user_dev(self.apple_id, self.name)

        self.device_data['name']  = self.name

        self.model_display_name = self.filtered_model_display_name()
        self.raw_model       = device_data['rawDeviceModel'].replace('_', ',')        # "iPhone17,2"
        self.model           = device_data['deviceClass']
        self.device_type     = device_data['deviceClass'].lower()
        self.model_no        = self.raw_model_no
        self.reset_accessories_model_info()

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
        self.missing_since_secs = 0     # Time the device was first not in the Apple acct's device list

        self.save_device_retired_fields(device_data)
        self.device_data[DATA_SOURCE] = self.data_source

        Gb.model_display_name_by_raw_model[self.raw_model] = self.model_display_name

        self.initialize_resettable_fields()
        self._add_ic3_items_to_device_data()

#----------------------------------------------------------------------
    def initialize_resettable_fields(self):

        self.dname                = self.name
        self.device_data['dname'] = self.dname
        self.apple_id_dev         = apple_id_dev(self.apple_id, self.dname)
        self.is_duplicate_dname   = False

        self.Device               = None
        self.ic3_devicename       = ''
        self.device_data[CONF_IC3_DEVICENAME] = self.ic3_devicename

        self.active               = False
        self.evlog_alert_char     = ''
        self.startup_msg          = ''

#----------------------------------------------------------------------
    def reset_accessories_model_info(self):
        if self.raw_model.startswith(AIRPODS_DN):
            self.model       = AIRPODS_DN
            self.device_type = AIRPODS

        elif self.raw_model.startswith('AirTags'):
            self.model       = 'AirTags'
            self.device_type = 'airtags'

#----------------------------------------------------------------------
    @property
    def device_id8(self):
        return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def dname_device_id(self):
        return f"{self.dname} ({self.device_id8})"

#----------------------------------------------------------------------
    @property
    def devicename(self):
        if Device := Gb.Devices_by_icloud_device_id.get(self.device_id):
            return Device.devicename
        elif self.is_data_source_ICLOUD:
            return self.dname
        else:
            return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def family_share_device(self):
        return self.device_data['fmlyShare']

#......................................................................
    def _find_conf_device_devicename(self, field, field_value):
        '''
        Cycle through the conf_devices and return the ic3_devicename that matches
        the requested field/field_value
        '''

        idx = -1
        for conf_device in Gb.conf_devices:
            idx += 1
            if (conf_device[CONF_APPLE_ACCT] == self.AppleAcct.apple_id
                    and conf_device[field] == field_value):
                return conf_device[CONF_IC3_DEVICENAME], idx

        return '', -1

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')
        return name

#----------------------------------------------------------------------
    def save_device_retired_fields(self, device_data):
        '''
        Save the fields that indicate the device was retired (unpaired, erased or
        being removed from the Apple acct). They are removed from device_data by
        DEVICE_DATA_FILTER_OUT when it is updated.
        '''
        self.activation_locked = device_data.get('activationLocked')
        self.pending_remove    = device_data.get('pendingRemove') is True
        self.wiped_timestamp   = device_data.get('wipedTimestamp')

#----------------------------------------------------------------------
    @property
    def is_retired(self):
        '''
        The device was unpaired or erased (Activation Lock turned off), or is being
        removed from the Apple acct. Activation Lock is always on for an iPhone,
        iPad or Watch with Find My enabled.
        '''
        return (self.pending_remove
                or self.wiped_timestamp not in [None, 0, '']
                or (self.activation_locked is False
                    and self.device_class in ['iPhone', 'iPad', 'Watch']))

#----------------------------------------------------------------------
    @property
    def is_offline_stale(self):
        '''
        The device is not online and has not been located for more than an hour.
        Apple does not return a location for a device that has been offline for a
        while (location_secs=0, secs_since(0) is 0).
        '''
        return (self.device_status_code != 200
                and (self.location_secs == 0
                    or secs_since(self.location_secs) > REPLACED_DEVICE_OFFLINE_SECS))

#----------------------------------------------------------------------
    @property
    def prs_id(self):
        '''
        Apple person id of the device's owner. None is the Apple acct owner,
        otherwise it is the Family Sharing member (key of userInfo.membersInfo)
        '''
        return self.device_data.get('prsId')

#----------------------------------------------------------------------
    @property
    def owner_first_name(self):
        return self.AppleAcct.first_name_by_prs_id.get(self.prs_id, '')

#----------------------------------------------------------------------
    @property
    def owner_device_key(self):
        '''
        Owner, device type and the name without the model or possessive. A newer
        device with Apple's default name has the same key as the device it replaced:
            ('NDM0NTU2NzE3', 'Watch', 'lillian-watch') for "Lillian-Watch" and
            "Lillian's Apple Watch"
        '''
        return (self.prs_id,
                self.device_class,
                name_device_type_key(self.name, self.device_class, self.owner_first_name))

#----------------------------------------------------------------------
    @property
    def device_info(self):
        return f"{self.dname} ({self.device_identifier})"

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
            if self.device_data.get('rawDeviceModel').startswith(AIRPODS_DN):
                device_class = AIRPODS_DN
            else:
                device_class = self.device_data.get('deviceClass', '')

            return (f"{self.model_display_name}; {self.raw_model}").replace("’", "'")

        else:
            return self.name.replace("’", "'")

#----------------------------------------------------------------------
    @property
    def device_class(self):
        if self.device_data.get('rawDeviceModel').startswith(AIRPODS_DN):
            return AIRPODS_DN
        else:
            return self.device_data.get('deviceClass', '')

#----------------------------------------------------------------------
    def filtered_model_display_name(self):
        display_name = self.device_data['deviceDisplayName']
        for from_str, to_str in DEVICE_DISPLAY_NAMES_FILTERS.items():
            display_name = display_name.replace(from_str, to_str)

        idx = display_name.find('-inch')
        if idx > 0:
            display_name = display_name[:idx-3] + display_name[idx+5:]

        return display_name

#----------------------------------------------------------------------
    @property
    def raw_model_no(self):
        model_no = 0
        try:
            # Strip the leading letters, keep the first number
            # (iPhone16,4 --> 16, MacBookPro6,3 --> 6, AirPods,8212 --> 8212)
            match = re.match(r'[A-Za-z]+[_,]?(\d+)', self.raw_model)
            if match:
                model_no = int(match.group(1))
        except Exception as err:
            log_exception(err)
            pass

        return model_no

#----------------------------------------------------------------------
    @property
    def aadevice_model_info(self):
        return [self.raw_model,                         # iPhone15,2
                self.device_data['modelDisplayName'],   # iPhone
                self.model_display_name]                # iPhone 14 Pro

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
    def save_new_device_data(self, new_device_data):
        '''Update the device data.'''
        new_device_data[CONF_IC3_DEVICENAME] = self.Device.devicename
        new_device_data['Device']            = self.Device
        new_device_data['dname']             = self.dname

        self.status_code = 0  #device_data.get('snd', []).get('status_code', 0)
        new_device_data[DATA_SOURCE]         = self.data_source
        if self.AppleAcct.china_gps_coordinates != '':
            new_device_data = self.convert_GCJ02_BD09_to_WGS84(new_device_data)

        try:
            self.save_device_retired_fields(new_device_data)
            new_device_data = {k: v for k, v in new_device_data.items()
                                        if k not in DEVICE_DATA_FILTER_OUT}

            self.device_data = new_device_data

            self._add_ic3_items_to_device_data()

        except Exception as err:
            log_exception(err)

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
    def _add_ic3_items_to_device_data(self):
        '''
        Add location, battery and status items that are used by iCloud3 to the
        device data so the device data fields do not have to be reformatted later.

        The following fields are created:
            [ICLOUD_DEVICE_STATUS]
            [LOCATION][TIMESTAMP]
            [LOCATION][LOCATION_TIME]
            [BATTERY_LEVEL]
            [BATTERY_STATUS]

        '''

        try:
            self.last_loc_time     = self.location_time
            self.last_loc_time_gps = f"{self.location_time}/±{self.gps_accuracy}m"
        except:
            self.last_loc_time_gps = ''

            self.status_code = self.device_data[ICLOUD_DEVICE_STATUS] = \
                int(self.device_data.get('deviceStatus', '0'))

        try:
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
            return f"{self.name} ({self.model_display_name})"
        except:
            return f"<AADev: Undefined>"
