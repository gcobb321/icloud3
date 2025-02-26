#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles all activities related to updating a device's sensors. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, PLATFORM_SENSOR, ICLOUD3, RARROW,
                                SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                                HOME, HOME_FNAME, NOT_SET, NOT_SET_FNAME, NONE_FNAME,
                                DATETIME_ZERO, HHMMSS_ZERO,
                                BLANK_SENSOR_FIELD, DOT, HDOT, UM_FNAME, NBSP, RED_ALERT,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME, FNAME, BADGE, FROM_ZONE, ZONE,
                                ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                HOME_DISTANCE, ICON,
                                BATTERY, BATTERY_STATUS,
                                WAZE_DISTANCE, WAZE_DISTANCE_ATTR, WAZE_METHOD, WAZE_USED,
                                CALC_DISTANCE, CALC_DISTANCE_ATTR,
                                CONF_TRACK_FROM_ZONES,
                                CONF_IC3_DEVICENAME, CONF_MODEL, CONF_RAW_MODEL, CONF_FNAME,
                                CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE,
                                )
from .const_sensor      import (SENSOR_DEFINITION, SENSOR_GROUPS, SENSOR_LIST_DISTANCE,
                                SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, ICLOUD3_SENSORS,
                                SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS, )

from .helpers.common    import (instr, is_empty, isnot_empty, round_to_zero, isnumber,
                                list_add, )
from .helpers.messaging import (post_event, log_info_msg, log_debug_msg, log_error_msg,
                                log_exception, log_info_msg_HA, log_exception_HA,
                                _evlog, _log, )
from .helpers.time_util import (time_to_12hrtime, time_remove_am_pm, format_timer,
                                format_mins_timer, time_now_secs, datetime_now,
                                secs_to_datetime, secs_to_datetime, datetime_struct_to_secs,
                                adjust_time_hour_values, adjust_time_hour_value)
from .helpers.dist_util import (km_to_mi, m_to_ft, m_to_um, set_precision, reformat_um, )
from .helpers.format    import (icon_circle, icon_box, )
from .helpers           import entity_io
from .support           import config_file
from .support           import start_ic3

from collections        import OrderedDict
from homeassistant      import config_entries, core
from homeassistant.const                import MATCH_ALL
from homeassistant.components.sensor    import SensorEntity
from homeassistant.config_entries       import ConfigEntry
from homeassistant.helpers.entity       import DeviceInfo

from homeassistant.core                 import HomeAssistant
from homeassistant.helpers.icon         import icon_for_battery_level
from homeassistant.helpers              import entity_registry as er, device_registry as dr

import homeassistant.util.dt as dt_util
# from homeassistant.helpers.entity       import Entity

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    '''Set up iCloud3 sensors'''

    # Save the hass `add_entities` call object for use in config_flow for adding new sensors
    Gb.hass = hass
    Gb.async_add_entities_sensor = async_add_entities
    Gb.sensors_created_cnt = 0


    try:
        if Gb.conf_file_data == {}:
            start_ic3.initialize_directory_filenames()
            # start_ic3.load_icloud3_configuration_file()
            await config_file.async_load_icloud3_configuration_file()


        NewSensors = []
        NewSensors.extend(_configure_icloud3_internal_sensors())
        NewSensors.extend(_configure_icloud3_device_sensors())

        # Set the total count of the sensors that will be created
        if Gb.sensors_cnt == 0:
            excluded_sensors_list = _excluded_sensors_list()
            Gb.sensors_cnt = len(NewSensors)
            post_event( f"Sensor Entities > Created-{len(NewSensors)}, "
                        f"Excluded-{len(excluded_sensors_list)}")

        if NewSensors != []:
            async_add_entities(NewSensors, True)
            log_info_msg_HA(f'iCloud3 Sensor Entities: {len(NewSensors)}')

        correct_sensor_entity_ids_with_2_extension()

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def _configure_icloud3_internal_sensors():
    '''
    Create the sensors for the Event Log and Waze Track History
    '''
    NewSensors = []
    Gb.EvLogSensor = Sensor_EventLog(SENSOR_EVENT_LOG_NAME)
    NewSensors.append(Gb.EvLogSensor)

    Gb.WazeHistTrackSensor = Sensor_WazeHistTrack(SENSOR_WAZEHIST_TRACK_NAME)
    NewSensors.append(Gb.WazeHistTrackSensor)

    return NewSensors

#--------------------------------------------------------------------
def _configure_icloud3_device_sensors():
    '''
    Create the sensors for each device being tracked or monitored and
    the sensors associated with each device
    '''
    try:
        NewSensors = []
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]

            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                continue

            if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
                NewSensors.extend(create_tracked_device_sensors(devicename, conf_device))

            elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
                NewSensors.extend(create_monitored_device_sensors(devicename, conf_device))

        return NewSensors
    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def create_tracked_device_sensors(devicename, conf_device, new_sensors_list=None):
    '''
    Add icloud3 sensors that have been selected via config_flow and
    arein the Gb.conf_sensors for each device
    '''
    try:
        NewSensors = []

        if new_sensors_list is None:
            new_sensors_list = []

            for sensor_group, sensor_list in Gb.conf_sensors.items():
                if sensor_group != 'monitored_devices':
                    new_sensors_list.extend(sensor_list)

        # The sensor group is a group of sensors combined under one conf_sensor item
        # Build sensors to be created from the the sensor or the sensor's group
        sensors_list_set = set()
        for sensor in new_sensors_list:
            if sensor in SENSOR_GROUPS:
                sensors_list_set.update(SENSOR_GROUPS[sensor])
            else:
                sensors_list_set.add(sensor)

        if 'last_zone' in sensors_list_set:
            if 'zone' not in Gb.conf_sensors[ZONE]:   sensors_list_set.discard('last_zone')
            if 'zone_name' in Gb.conf_sensors[ZONE]:  sensors_list_set.add('last_zone_name')
            if 'zone_fname' in Gb.conf_sensors[ZONE]: sensors_list_set.add('last_zone_fname')

        NewSensors.extend(_create_device_sensors(devicename, conf_device, sensors_list_set))
        NewSensors.extend(_create_track_from_zone_sensors(devicename, conf_device, sensors_list_set))

        return NewSensors

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def _create_device_sensors(devicename, conf_device, sensors_list):

    NewSensors = []
    devicename_sensors    = Gb.Sensors_by_devicename.get(devicename, {})
    excluded_sensors_list = _excluded_sensors_list()

    # Cycle through the sensor definition names in the list of selected sensors,
    # Get the Sensor entity name and create the sensor.[ic3_devicename]_[sensor_name] entity
    # The sensor_def name is the conf_sensor name set up in the Sensor_definition table.
    # The table contains the actual ha Sensor entity name. That permits support for track-from-zone
    # suffixes.

    for sensor in sensors_list:
        if (sensor not in SENSOR_DEFINITION
                or sensor.startswith('tfz_')):
            continue
        if (instr(sensor, BATTERY)
                and conf_device[CONF_FAMSHR_DEVICENAME] == NONE_FNAME
                and conf_device[CONF_MOBILE_APP_DEVICE] == NONE_FNAME):
            continue

        devicename_sensor = f"{devicename}_{sensor}"
        if devicename_sensor in excluded_sensors_list:
            log_debug_msg(f"Sensor entity Excluded: sensor.{devicename_sensor}")
            continue

        Sensor = None
        if sensor in devicename_sensors:
            # Sensor object might exist, use it to recreate the Sensor entity
            _Sensor = devicename_sensors[sensor]
            if _Sensor.entity_removed_flag:
                Sensor = _Sensor
                log_info_msg(f"Reused Existing sensor.icloud3 entity: {Sensor.entity_id}")
                Sensor.entity_removed_flag = False

        else:
            Sensor = _create_sensor_by_type(devicename, sensor, conf_device)

        if Sensor:
            devicename_sensors[sensor] = Sensor
            NewSensors.append(Sensor)

    Gb.Sensors_by_devicename[devicename] = devicename_sensors

    return NewSensors

#--------------------------------------------------------------------
def _create_track_from_zone_sensors(devicename, conf_device, sensors_list):

    if conf_device[CONF_TRACK_FROM_ZONES] == [HOME]:
        return []

    ha_zones, zone_entity_data   = entity_io.get_entity_registry_data(platform=ZONE)
    devicename_from_zone_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename, {})
    excluded_sensors_list        = _excluded_sensors_list()

    NewSensors = []

    for sensor in sensors_list:
        if (sensor not in SENSOR_DEFINITION
                or sensor.startswith('tfz_') is False):
            continue

        sensor = sensor.replace('tfz_', '')

        # Track_from_zone related sensors
        if (conf_device[CONF_TRACK_FROM_ZONES] == []
                    or HOME not in conf_device[CONF_TRACK_FROM_ZONES]):
                conf_device[CONF_TRACK_FROM_ZONES].append(HOME)

        for from_zone in conf_device[CONF_TRACK_FROM_ZONES]:
            if from_zone not in ha_zones:
                continue

            Sensor = None
            sensor_zone = f"{sensor}_{from_zone}"
            devicename_sensor_zone = f"{devicename}_{sensor}_{from_zone}"

            if devicename_sensor_zone in excluded_sensors_list:
                log_debug_msg(f"Sensor entity Excluded: sensor.{devicename_sensor_zone}")
                continue

            if sensor_zone in devicename_from_zone_sensors:
                continue

            # Sensor object might exist, use it to recreate the Sensor entity
            if sensor_zone in devicename_from_zone_sensors:
                _Sensor = devicename_from_zone_sensors[sensor_zone]
                if _Sensor.entity_removed_flag:
                    Sensor = _Sensor
                    log_info_msg(f"Reused Existing sensor.icloud3 entity: {Sensor.entity_id}")
                    Sensor.entity_removed_flag = False

            Sensor = _create_sensor_by_type(devicename, sensor, conf_device, from_zone)

            if Sensor:
                devicename_from_zone_sensors[sensor_zone] = Sensor
                NewSensors.append(Sensor)

    Gb.Sensors_by_devicename_from_zone[devicename] = devicename_from_zone_sensors

    return NewSensors

#--------------------------------------------------------------------
def create_monitored_device_sensors(devicename, conf_device, new_sensors_list=None):
    '''
        Add icloud3 sensors that have been selected via config_flow and
        arein the Gb.conf_sensors for each device
    '''

    try:
        excluded_sensors_list = _excluded_sensors_list()
        NewSensors = []
        if new_sensors_list is None:
            new_sensors_list = []
            new_sensors_list.extend(Gb.conf_sensors['monitored_devices'])

        # The sensor group is a group of sensors combined under one conf_sensor item
        # Build sensors to be created from the the sensor or the sensor's group
        sensors_list = []
        for sensor in new_sensors_list:
            if sensor in SENSOR_GROUPS:
                sensors_list.extend(SENSOR_GROUPS[sensor])
            else:
                sensors_list.append(sensor)

        devicename_sensors = Gb.Sensors_by_devicename.get(devicename, {})

        # Cycle through the sensor definition names in the list of selected sensors,
        # Get the Sensor entity name and create the sensor.[ic3_devicename]_[sensor_name] entity
        # The sensor_def name is the conf_sensor name set up in the Sensor_definition table.
        # The table contains the actual ha Sensor entity name. That permits support for track-from-zone
        # suffixes.
        for sensor in sensors_list:
            Sensor = None

            devicename_sensor = f"{devicename}_{sensor}"
            if devicename_sensor in excluded_sensors_list:
                log_debug_msg(f"Sensor entity Excluded: sensor.{devicename_sensor}")
                continue

            # Sensor object might exist, use it to recreate the Sensor entity
            if sensor in devicename_sensors:
                _Sensor = devicename_sensors[sensor]
                if _Sensor.entity_removed_flag:
                    Sensor = _Sensor
                    log_info_msg(f"Reused Existing sensor.icloud3 entity: {Sensor.entity_id}")
                    Sensor.entity_removed_flag = False
            else:
                Sensor = _create_sensor_by_type(devicename, sensor, conf_device)

            if Sensor:
                devicename_sensors[sensor] = Sensor
                NewSensors.append(Sensor)

        Gb.Sensors_by_devicename[devicename] = devicename_sensors
        Gb.Sensors_by_devicename_from_zone[devicename] = {}

        return NewSensors

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def _excluded_sensors_list():
    return [sensor_fname.split('(')[1][:-1]
                        for sensor_fname in Gb.conf_sensors['excluded_sensors']
                        if instr(sensor_fname, '(')]

#--------------------------------------------------------------------
def _strip_sensor_def_table_item_prefix(sensor):
    '''
    Remove the prefix for sensor names in the sensor definition table for
    the 'track_from_zone (tfz_)  and 'monitor_device` (md_) sensors.
    '''
    return sensor.replace('tfz_', '').replace('md_', '')

#--------------------------------------------------------------------
def  _create_sensor_by_type(devicename, sensor, conf_device, from_zone=None):
    '''
    Create the Sensor object based on the type of sensor

    Return:
        Sensor Object
    '''
    sensor_type = SENSOR_DEFINITION[sensor][SENSOR_TYPE]
    if sensor_type.startswith('battery'):
        return Sensor_Battery(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('text'):
        return Sensor_Text(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('timestamp'):
        return Sensor_Timestamp(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('timer'):
        return Sensor_Timer(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('distance'):
        return Sensor_Distance(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('zone_info'):
        return Sensor_ZoneInfo(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('zone'):
        return Sensor_Zone(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('info'):
        return Sensor_Info(sensor, devicename, conf_device, from_zone)
    elif sensor_type.startswith('badge'):
        return Sensor_Badge(sensor, devicename, conf_device, from_zone)
    else:
        log_error_msg(f"iCloud3 Sensor Setup Error, Sensor-{sensor} > Invalid Sensor Type-{sensor_type}")
        return None

#--------------------------------------------------------------------
def correct_sensor_entity_ids_with_2_extension(verify=None):
    '''
    Get the iCloud3 sensor entities and see if any end with _2. If so,
    remove the non_2 sensor and rename the _2 sensor to it's correct value

    This is called when the sensors are fist loded (here) and in config_flow (Tools)

    Parameters:
    verify - True --> Return True/False if there are any correctable sensors
    '''
    verify = False if verify is None else True

    # Get all iCloud sensors in hass.states
    entity_ids = entity_io.get_states_entity_ids()
    if is_empty(entity_ids):
        return False

    # Keep sensors that have an '_x' extension (sensor.……_distance_2)
    entity_ids = [entity_id for entity_id in entity_ids
                            if entity_id[-2:-1] == '_']

    if is_empty(entity_ids):
        return False
    if verify:
        return True

    # remove sensor.……_distance and change name sensor.……_distance_2 to sensor.……_distance
    for entity_id in entity_ids:
        entity_id_base = entity_id[:-2]
        eid_base_is_avail = entity_io.is_entity_available(entity_id_base)
        if eid_base_is_avail is False:
            # Ex.: Remove sensor.gary_iphone_home_distance
            entity_io.remove_entity(entity_id_base)

        extn = entity_id.replace(entity_id_base, '')
        log_debug_msg(f"Sensor entity, Named:  {entity_id_base}, (×{extn})")
        # Ex.: Change sensor.gary_iphone_home_distance_2 to sensor.gary_iphone_home_distance
        entity_io.change_entity_id(entity_id, entity_id_base)

    return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#       CONFIGURE ICLOUD3 SENSORS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class DeviceSensor_Base():
    ''' iCloud base device sensor '''

    _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, sensor_base, devicename, conf_device, from_zone=None):
        try:
            self.hass           = Gb.hass
            self.sensor_base    = sensor_base
            self.devicename     = devicename
            self.conf_device    = conf_device
            self.device_sensor  = True
            self.icloud3_sensor = False
            self.sensor_number  = 0


            self.from_zone   = from_zone
            if from_zone:
                self.from_zone_fname = f" ({from_zone.title().replace('_', '').replace(' ', '')})"
                self.sensor          = f"{sensor_base}_{from_zone}"
            else:
                self.from_zone_fname = ''
                self.sensor          = sensor_base

            self.device_id           = Gb.ha_device_id_by_devicename.get(ICLOUD3)
            self.entity_name         = f"{devicename}_{self.sensor}"
            self._attr_unique_id     = f"{DOMAIN}_{self.entity_name}"
            self.entity_id_base      = f"{PLATFORM_SENSOR}.{self.entity_name}"

            # entity_id is changed by ha to the name actually assigned. It will have
            #  a '_2' added to it if it is already in the  entity registry
            self.entity_id           = f"{PLATFORM_SENSOR}.{self.entity_name}"


            self.Device = Gb.Devices_by_devicename.get(devicename)
            if self.Device and from_zone:
                self.FromZone = self.Device.FromZones_by_zone.get(from_zone)
            else:
                self.FromZone = None


            self._attr_force_update = True
            self._unsub_dispatcher  = None
            self._on_remove         = [self.after_removal_cleanup]
            self.entity_removed_flag = False

            self.sensor_type     = self._get_sensor_definition(sensor_base, SENSOR_TYPE).replace(' ', '')
            self.sensor_empty    = self._get_sensor_definition(sensor_base, SENSOR_DEFAULT)
            self.sensor_fname    = (f"{conf_device[FNAME]} "
                                    f"{self._get_sensor_definition(sensor_base, SENSOR_FNAME)}"
                                    f"{self.from_zone_fname}")
            self._attr_native_unit_of_measurement = None

            self._state = self._get_restore_or_default_value(sensor_base)
            self.current_state_value = ''

            Gb.sensors_created_cnt += 1
            self.sensor_number = Gb.sensors_created_cnt

            log_debug_msg(f"Sensor entity, Config: {self.entity_id}, #{self.sensor_number}")

        except Exception as err:
            log_exception(err)
            log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
            log_error_msg(log_msg)

#-------------------------------------------------------------------------------------------
    @property
    def unique_id(self):
        return f"{DOMAIN}_{self.entity_name}"

    @property
    def name(self):
        ''' Sensor friendly name '''
        return self.sensor_fname

    @property
    def devicename_sensor(self):
        '''Sensor friendly name.'''
        return f"{self.entity_id}_{self.sensor}"

    @property
    def fname_entity_name(self):
        '''Sensor friendly name (devicename) '''
        return f"{self.sensor_fname} ({self.entity_name})"

    @property
    def icon(self):
        if self.Device and self.sensor_base in self.Device.sensors_icon:
            return self.Device.sensors_icon[self.sensor_base]

        return self._get_sensor_definition(self.sensor_base, SENSOR_ICON)

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device """
        return DeviceInfo(  identifiers  = {(DOMAIN, self.devicename)},
                            manufacturer = "Apple",
                            model        = self.conf_device[CONF_RAW_MODEL],
                            name         = f"{self.conf_device[CONF_FNAME]} ({self.devicename})",
                        )

#-------------------------------------------------------------------------------------------
    @property
    def sensor_value(self):
        return self._get_sensor_value(self.sensor)

#-------------------------------------------------------------------------------------------
    def _get_extra_attributes(self, sensor):
        '''
        Get the extra attributes for the sensor defined in the
        SENSOR_DEFINITION dictionary
        '''
        extra_attrs = OrderedDict()
        extra_attrs['integration'] = ICLOUD3

        update_time = secs_to_datetime(time_now_secs())
        if self.Device and self.Device.away_time_zone_offset != 0:
            update_time = adjust_time_hour_values(update_time, self.Device.away_time_zone_offset)
        extra_attrs['sensor_updated'] = update_time

        for _sensor in self._get_sensor_definition(sensor, SENSOR_ATTRS):
            _sensor_attr_name = _sensor.replace('_date/time', '')
            _sensor_value = self._get_sensor_value(_sensor)
            try:
                _sensor_value = set_precision(_sensor_value)
            except:
                pass

            if _sensor_attr_name == WAZE_DISTANCE:
                _sensor_attr_name = WAZE_DISTANCE_ATTR
                if self._get_sensor_value(WAZE_METHOD) != WAZE_USED:
                    _sensor_value = self._get_sensor_value(WAZE_METHOD)
            elif _sensor_attr_name == CALC_DISTANCE:
                _sensor_attr_name = CALC_DISTANCE_ATTR

            if _sensor_attr_name == ZONE_DISTANCE_M_EDGE:
                extra_attrs[_sensor_attr_name] = _sensor_value

                if Gb.um_MI:
                    zone_dist_m = self._get_sensor_value(ZONE_DISTANCE_M)
                    if isnumber(zone_dist_m):
                        sensor_value_mi = zone_dist_m*Gb.um_km_mi_factor/1000
                        extra_attrs['distance (miles)'] = set_precision(sensor_value_mi)
                        extra_attrs['distance_units (attributes)'] = 'mi'

            if self.Device and self.Device.away_time_zone_offset != 0:
                _sensor_value = adjust_time_hour_values(_sensor_value, self.Device.away_time_zone_offset)

            extra_attrs[_sensor_attr_name] = _sensor_value

        return extra_attrs

#-------------------------------------------------------------------------------------------
    def _get_sensor_definition(self, sensor, field):
        try:
            sensor = sensor.replace(f"_{self.from_zone}", '')
            return SENSOR_DEFINITION[sensor][field]

        except:
            if field == SENSOR_ATTRS:
                return []
            else:
                return ''

#-------------------------------------------------------------------------------------------
    @property
    def sensor_not_set(self):
        sensor_value = self._get_sensor_value(self.sensor)

        if self.Device is None:
            return True

        if (type(sensor_value) is str
                and (sensor_value.startswith(BLANK_SENSOR_FIELD)
                    or sensor_value.strip() == ''
                    or sensor_value == HHMMSS_ZERO
                    or sensor_value == DATETIME_ZERO
                    or sensor_value == NOT_SET
                    or sensor_value == NOT_SET_FNAME)):
            return True
        else:
            return False

#-------------------------------------------------------------------------------------------
    def _get_sensor_value(self, sensor):
        '''
        Get the sensor value from:
            - Device's attributes/sensor
            - Device's DeviceFmZone attributes/sensors for a zone
        '''

        if self.from_zone:
            return self._get_tfz_sensor_value(sensor)
        else:
            return self._get_device_sensor_value(sensor)

#-------------------------------------------------------------------------------------------
    def _get_device_sensor_value(self, sensor):
        '''']
        Get the sensor value from:
            - Device's attributes/sensor
            - Device's DeviceFmZone attributes/sensors for a zone
        '''

        try:
            if self.Device is None:
                return self._get_restore_or_default_value(sensor)

            sensor_value = self.Device.sensors.get(sensor, None)

            if (sensor_value is None
                    or sensor_value == NOT_SET
                    or type(sensor_value) is str
                        and (sensor_value.strip() == '')):

                return self._get_restore_or_default_value(sensor)

            return sensor_value

        except Exception as err:
            log_exception(err)

        return self._get_restore_or_default_value(sensor)

#-------------------------------------------------------------------------------------------
    def _get_restore_or_default_value(self, sensor):
        '''
        Get a default value that is used when iCloud3 has not started, the Device for the
        sensor has not veen created or the type is text and the value is ''.
        '''
        try:
            if self.from_zone:
                sensor_value = Gb.restore_state_devices[self.devicename]['from_zone'][self.from_zone][sensor]
            else:
                sensor_value = Gb.restore_state_devices[self.devicename]['sensors'][sensor]
        except:
            sensor_value = self._get_sensor_definition(sensor, SENSOR_DEFAULT)

        return sensor_value

#-------------------------------------------------------------------------------------------
    def _get_tfz_sensor_value(self, sensor):
        '''
        Get the sensor value from:
            - Device's DeviceFmZone attributes/sensors for a zone
        '''
        try:
            if (self.Device is None
                    or self.FromZone is None):
                return self._get_restore_or_default_value(sensor)

            # Strip off zone to get the actual tfz dictionary item
            tfz_sensor   = sensor.replace(f"_{self.from_zone}", "")
            sensor_value = self.FromZone.sensors.get(tfz_sensor, None)

            if (sensor_value is None
                    or sensor_value == NOT_SET
                    or (type(sensor_value) is str and sensor_value.strip() == '')):
                return self._get_restore_or_default_value(sensor)

            return sensor_value

        except Exception as err:
            log_exception(err)

        return self._get_restore_or_default_value(sensor)

#-------------------------------------------------------------------------------------------
    def _get_sensor_value_um(self, sensor, value_and_um=True):
        '''
            Get the sensor value and determine if it has a value and unit_of_measurement.

            Return:
                um specified:
                    [sensor_value, um]
                um not specified (value only):
                    [sensor_value, None]
        '''
        sensor_value = self._get_sensor_value(sensor)

        try:
            if instr(sensor_value, ' '):
                value_um_parts = sensor_value.split(' ')
                return float(value_um_parts[0]), (self._get_sensor_um(sensor) or value_um_parts[1])

            elif self.sensor_not_set:
                return sensor_value, None

            else:
                return float(sensor_value), None

        except ValueError:
            return sensor_value, None

        except Exception as err:
            log_exception(err)
            return sensor_value, None

#-------------------------------------------------------------------------------------------
    def _get_sensor_um(self, sensor):
        '''
        Get the sensor's special um override value from:
            - Device's sensors_um dictionary
            - Device's DeviceFmZone sensors_um dictionary for a zone
        '''

        return None

#-------------------------------------------------------------------------------------------
    @property
    def should_poll(self):
        ''' Do not poll to update the sensor '''
        return False

#-------------------------------------------------------------------------------------------
    def update_entity_attribute(self, new_fname=None):
        """ Update entity definition attributes """

        if new_fname is None:
            return

        self.sensor_fname =(f"{new_fname} "
                            f"{self._get_sensor_definition(self.sensor, SENSOR_FNAME)}"
                            f"{self.from_zone_fname}")

        log_debug_msg(f"Sensor entity Changed: {self.entity_id}, {self.sensor_fname}")

        kwargs = {}
        kwargs['original_name'] = self.sensor_fname

        # entity_registry = er.async_get(Gb.hass)
        # entity_registry.async_update_entity(self.entity_id, **kwargs)
        try:
            entity_io.update_entity(self.entity_id, **kwargs)
        except Exception as err:
            # log_exception(err)
            pass

        """
            Typically used:
                name: str | None | UndefinedType = UNDEFINED,
                new_entity_id: str | UndefinedType = UNDEFINED,
                device_id: str | None | UndefinedType = UNDEFINED,
                original_name: str | None | UndefinedType = UNDEFINED,
                config_entry_id: str | None | UndefinedType = UNDEFINED,

            Not used:
                area_id: str | None | UndefinedType = UNDEFINED,
                capabilities: Mapping[str, Any] | None | UndefinedType = UNDEFINED,
                device_class: str | None | UndefinedType = UNDEFINED,
                disabled_by: RegistryEntryDisabler | None | UndefinedType = UNDEFINED,
                entity_category: EntityCategory | None | UndefinedType = UNDEFINED,
                hidden_by: RegistryEntryHider | None | UndefinedType = UNDEFINED,
                icon: str | None | UndefinedType = UNDEFINED,
                new_unique_id: str | UndefinedType = UNDEFINED,
                original_device_class: str | None | UndefinedType = UNDEFINED,
                original_icon: str | None | UndefinedType = UNDEFINED,
                supported_features: int | UndefinedType = UNDEFINED,
                unit_of_measurement: str | None | UndefinedType = UNDEFINED,
    """

#-------------------------------------------------------------------------------------------
    async def async_added_to_hass(self):
        '''
        When adding the entity, check to see if the entity_id (what was really added) is the
        same as entity_id_base (what iC3 wanted to add).

        Note: HA will add an extension (_2) if HA has determined that the entity_id iC3 specified
        already exists (it is in the hass.states.data tables). If so, remove the iC3 base entity
        and rename the one HA created (with _2) to the one iC3 entity_id.
        '''

        log_debug_msg(f"Sensor entity, Added:  {self.entity_id}, #{self.sensor_number}")

        if self.entity_id == self.entity_id_base:
            return

        eid_base_is_avail = entity_io.is_entity_available(self.entity_id_base)
        if eid_base_is_avail is False:
            # Ex.: Remove sensor.gary_iphone_home_distance
            entity_io.remove_entity(self.entity_id_base)

        # Ex.: Change sensor.gary_iphone_home_distance_2 to sensor.gary_iphone_home_distance
        extn = self.entity_id.replace(self.entity_id_base, '')
        log_debug_msg(f"Sensor entity, Named:  {self.entity_id_base}, (×{extn})")
        entity_io.change_entity_id(self.entity_id, self.entity_id_base)

#-------------------------------------------------------------------------------------------
    def after_removal_cleanup(self):
        """
        Cleanup sensor after removal

        Passed in the `self._on_remove` parameter during initialization
        and called by HA after processing the async_remove request

        Make sure entity is removed from the entity_registry and the hass.state.entities
        dictionary.
        """

        log_info_msg(f"Sensor entity, Remove: {self.entity_id}, #{self.sensor_number}")

        entity_io.remove_entity(self.entity_id)
        self.entity_removed_flag = True

        if self.Device is None:
            return

        if self.Device.Sensors_from_zone and self.sensor in self.Device.Sensors_from_zone:
            self.Device.Sensors_from_zone.pop(self.sensor)

        if self.Device.Sensors and self.sensor in self.Device.Sensors:
            self.Device.Sensors.pop(self.sensor)

#-------------------------------------------------------------------------------------------
    def x_remove_entity():
        entity_io.remove_entity(self.entity_id)

#-------------------------------------------------------------------------------------------
    async def async_will_remove_from_hass(self):
        '''Clean up after entity before removal.'''

        if self._unsub_dispatcher:
            for unsub_dispatcher in self._unsub_dispatcher:
                unsub_dispatcher()

#-------------------------------------------------------------------------------------------
    def write_ha_sensor_state(self):
        """Update the entity's state if the state value has changed."""

        try:
            self.schedule_update_ha_state()

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    # async def async_added_to_hass(self):
    #     '''Register state update callback.'''
    #     self._unsub_dispatcher = async_dispatcher_connect(
    #                                     self.hass,
    #                                     signal_device_update,
    #                                     self.async_write_ha_state)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
            return (f"<Sensor: {self.entity_name}>")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Badge(DeviceSensor_Base, SensorEntity):
    '''  Sensor for displaying the device badge items '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['badge'])

    @property
    def native_value(self):
        return  str(self._get_sensor_value(BADGE))

    @property
    def extra_state_attributes(self):
        if self.Device:
            badge_attrs = self.Device.sensor_badge_attrs.copy()
            badge_attrs.update(self._get_extra_attributes(self.sensor))
            return badge_attrs
        else:
            return None

    @property
    def icon(self):
        return self._get_sensor_value(ICON)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_ZoneInfo(DeviceSensor_Base, SensorEntity):
    '''  Sensor for displaying the device zone time/distance items '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS[ZONE])

    @property
    def native_value(self):
        return  self._get_sensor_value(FROM_ZONE).title()

    @property
    def icon(self):
        return icon_box(self.native_value)

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Text(DeviceSensor_Base, SensorEntity):
    '''  Sensor for handling text items '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['text'])

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(self.sensor)

        if instr(self.sensor_type, 'time'):
            if instr(sensor_value, ' '):
                text_um_parts = sensor_value.split(' ')
                sensor_value = text_um_parts[0]
                self._attr_unit_of_measurement = text_um_parts[1]
            else:
                self._attr_unit_of_measurement = None

        # Set to space if empty
        if sensor_value.strip() == '':
            sensor_value = self.sensor_empty        #BLANK_SENSOR_FIELD

        if self.Device and self.Device.away_time_zone_offset != 0:
            sensor_value = adjust_time_hour_values(sensor_value, self.Device.away_time_zone_offset)

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Info(DeviceSensor_Base, SensorEntity):
    '''
        Sensor for handling info sensor messages.
            1.  This will update a specific Device's info sensor using the
                Device.update_info_message('msg') function.
                broadcase_info_msg('msg') function in base.py by entering the
                message into the 'Gb.broadcast_info_msg' field. This lets you display
                an info message during startup before the devices have been created
                or to everyone as a general notification.
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['text'])

    @property
    def native_value(self):
        self._attr_unit_of_measurement = None
        sensor_value = self._get_sensor_value(self.sensor)

        if Gb.broadcast_info_msg and Gb.broadcast_info_msg != '•  ':
            broadcast_info_msg = Gb.broadcast_info_msg
            if self.Device and self.Device.away_time_zone_offset != 0:
                broadcast_info_msg = adjust_time_hour_values(broadcast_info_msg, self.Device.away_time_zone_offset)
            return broadcast_info_msg

        elif self.sensor_not_set:
            return f"◈◈ Starting iCloud3 v{Gb.version} ◈◈"

        else:
            if self.Device and self.Device.away_time_zone_offset != 0:
                sensor_value = adjust_time_hour_values(sensor_value, self.Device.away_time_zone_offset)
            return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Timestamp(DeviceSensor_Base, SensorEntity):
    '''
    Sensor for handling timestamp (mm/dd/yy hh:mm:ss) items
    Sensors: last_update_time, next_update_time, last_located
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['timestamp'])

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(self.sensor)
        state_value=sensor_value

        sensor_value = time_to_12hrtime(sensor_value)
        state_value_12=sensor_value

        if self.Device and self.Device.away_time_zone_offset != 0:
            sensor_value = adjust_time_hour_value(sensor_value, self.Device.away_time_zone_offset)
        state_value_adj=sensor_value
        try:
            # Drop the 'a' or 'p' so the field will fit on an iPhone
            if int(sensor_value.split(':')[0]) >= 10:
                sensor_value = time_remove_am_pm(sensor_value)
        except:
            pass

        return sensor_value

    @property
    def extra_state_attributes(self):
        attrs = self._get_extra_attributes(self.sensor)
        return attrs
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Timer(DeviceSensor_Base, SensorEntity):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['timer'])

    @property
    def native_value(self):
        if instr(self.sensor_type, ','):
            sensor_type_um = self.sensor_type.split(',')[1]
        else:
            sensor_type_um = ''

        sensor_value, unit_of_measurement = self._get_sensor_value_um(self.sensor)

        if sensor_value == 0:
            self._attr_native_unit_of_measurement = 'min'
            return 0

        if unit_of_measurement:
            self._attr_native_unit_of_measurement = unit_of_measurement

        elif sensor_type_um == 'min':
            time_str = format_mins_timer(sensor_value)
            if time_str and instr(time_str, 'd') is False:         # Make sure it is not a 4d2h34m12s item
                time_min_hrs = time_str.split(' ')
                sensor_value = time_min_hrs[0]
                self._attr_native_unit_of_measurement = time_min_hrs[1]

        elif sensor_type_um == 'sec':
            time_str = format_timer(sensor_value)
            if time_str and instr(time_str, 'd') is False:       # Make sure it is not a 4d2h34m12s item
                time_secs_min_hrs = time_str.split(' ')
                sensor_value = time_secs_min_hrs[0]
                self._attr_native_unit_of_measurement = time_secs_min_hrs[1]

        else:
            self._attr_native_unit_of_measurement = 'min'

        try:
            # Try to convert sensor_value to integer. Just return it if it fails.
            if (sensor_value and sensor_value != BLANK_SENSOR_FIELD):
                if sensor_value == int(sensor_value):
                    sensor_value = int(sensor_value)
        except Exception as err:
            pass

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Distance(DeviceSensor_Base, SensorEntity):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['distance'])

    @property
    def native_value(self):
        if instr(self.sensor_type, ','):
            sensor_type_um = self.sensor_type.split(',')[1]

        sensor_value, unit_of_measurement = self._get_sensor_value_um(self.sensor)


        if unit_of_measurement:
            self._attr_native_unit_of_measurement = unit_of_measurement
        elif sensor_type_um == 'm-ft':
            self._attr_native_unit_of_measurement = Gb.um_m_ft
        elif sensor_type_um == 'km-mi':
            self._attr_native_unit_of_measurement = Gb.um
        elif sensor_type_um == 'm':
            self._attr_native_unit_of_measurement = 'm'
        else:
            self._attr_native_unit_of_measurement = Gb.um

        if self._attr_native_unit_of_measurement == 'km':
            if round_to_zero(sensor_value) == 0:
                sensor_value = 0.0
            elif sensor_value > 20:
                sensor_value = round(sensor_value, 0)
            elif sensor_value >= 1:
                sensor_value = round(sensor_value, 2)
            elif instr(self.sensor_type, 'm-ft'):
                sensor_value =  round(sensor_value*1000, 2)
                self._attr_native_unit_of_measurement = 'm'
            else:
                sensor_value =  round(sensor_value, 2)

        elif self._attr_native_unit_of_measurement == 'mi':
            if round_to_zero(sensor_value) == 0:
                sensor_value = 0.0
            elif sensor_value > 20:
                sensor_value = round(sensor_value, 1)
            elif sensor_value > .1:
                sensor_value = round(sensor_value, 2)
            elif instr(self.sensor_type, 'm-ft'):
                sensor_value = round(sensor_value*5280, 2)
                self._attr_native_unit_of_measurement = 'ft'
            else:
                sensor_value = round(sensor_value, 2)

        return sensor_value

#---------------------------------------------------------------
    @property
    def extra_state_attributes(self):
        extra_attrs = self._get_extra_attributes(self.sensor)

        if self.Device and self.sensor in [HOME_DISTANCE, ZONE_DISTANCE]:
            extra_attrs.update(self._format_zone_distance_extra_attrs())
            extra_attrs.update(self._format_devices_distance_extra_attrs())

        return extra_attrs

#---------------------------------------------------------------
    def _format_zone_distance_extra_attrs(self):
        '''
        Get the distance to each zone and build the extra_attributes Zone distance items
        '''
        zone_dist = {}
        sorted_zone_dist = {}
        try:
            for Zone in Gb.HAZones:
                if Zone.is_statzone: continue
                dist = set_precision(self.Device.Distance_km(Zone), Gb.um)
                zone_dist[f"--{Zone.dname}"] = dist

            for Zone in Gb.HAZones:
                if Zone.is_statzone: continue
                dist = set_precision(self.Device.Distance_km(Zone)*1000, Gb.um_m_ft)
                if dist < 500:
                    zone_dist[f"={Zone.dname} ({Gb.um_m_ft})"] = dist

            sorted_zone_dist[f"zones (calculated distance) ({Gb.um})"] = f"{secs_to_datetime(time_now_secs())}"
            sorted_zone_dist.update(dict(sorted(zone_dist.items())))

        except Exception as err:
            # log_exception(err)
            pass

        return sorted_zone_dist

#---------------------------------------------------------------
    def _format_devices_distance_extra_attrs(self):
        '''
        Get the distance to each zone and build the extra_attributes Zone distance items.
        Use distance apart from this device for the distance data.
        {devicename: [distance_m, gps_accuracy_factor, display_text]}
        '''
        fname_dist = {}
        sorted_fname_dist = {}
        try:
            for _devicename, _Device in Gb.Devices_by_devicename.items():
                if _devicename == self.devicename: continue
                dist_m = self.Device.other_device_distance(_devicename)
                fname_dist[f"--{_Device.fname}"] = reformat_um(m_to_um(dist_m))

            for _devicename, _Device in Gb.Devices_by_devicename.items():
                if _devicename == self.devicename: continue
                dist_m = self.Device.other_device_distance(_devicename)
                fname_dist[f"={_Device.fname}"] = set_precision(km_to_mi(dist_m/1000))

            sorted_fname_dist[f"devices (calculated distance) ({Gb.um})"] = \
                        f"{secs_to_datetime(self.Device.dist_to_other_devices_secs)}"
            sorted_fname_dist.update(dict(sorted(fname_dist.items())))

        except Exception as err:
            # log_exception(err)
            pass

        return sorted_fname_dist

#-------------------------------------------------------------------------------------------
    # def _set_precision(self, number, um=None):
    #     '''
    #     Return the distance value as an integer or float value
    #     '''
    #     try:
    #         if isnumber(number) is False:
    #             _evlog(f"zz {self.sensor} {number=} {um=}")
    #             return number

    #         um = um if um else Gb.um
    #         precision = 5 if um in ['km', 'mi'] else 2 if um in ['m', 'ft'] else 4
    #         _evlog(f"aa {self.sensor} {number=} {um=} {precision=}")
    #         number = round(float(number), precision)
    #         _evlog(f"bb {self.sensor} {number=} {um=} {precision=}")

    #     except Exception as err:
    #         pass

    #     return number

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Battery(DeviceSensor_Base, SensorEntity):
    '''
    Sensor for handling battery items (30s)
    Sensors: battery
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS[BATTERY])

    @property
    def icon(self):
        if self.Device:
            battery_level = self.Device.sensors[BATTERY]
            charging      = (self.Device.sensors[BATTERY_STATUS].lower() == "charging")
            return icon_for_battery_level(battery_level, charging)

    @property
    def native_value(self):
        self._attr_native_unit_of_measurement = '%'
        sensor_value =  self._get_sensor_value(self.sensor)

        return sensor_value

    @property
    def extra_state_attributes(self):
        extra_attrs = self._get_extra_attributes(self.sensor)
        extra_attrs.update({'device_class': 'battery', 'state_class': 'measurement'})

        return extra_attrs


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Zone(DeviceSensor_Base, SensorEntity):
    '''
    Sensor for handling zone items
    Sensors:
        zone, zone_name, zone_fname,
        last_zone, last_zone_name, last_zone_fname

    zone or last_zone sensor:
        Attributes = zone_name & zone_fname
    zone_name, zone_fname, last_zone_name, last_zone_fname:
        Attributes = zone
    '''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS[ZONE])

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(f"{self.sensor}")

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3Sensor_Base():
    ''' iCloud Support Sensor Base
        - Event Log
        - Waze History Track
    '''

    # _unrecorded_attributes = frozenset({MATCH_ALL})

    def __init__(self, sensor):
        '''Initialize the Event Log sensor (icloud3_event_log).'''
        entity_reg = er.async_get(Gb.hass)

        self.hass            = Gb.hass
        self.sensor          = sensor

        self.fname           = ICLOUD3_SENSORS[sensor]

        self._device         = DOMAIN
        self.entity_name     = sensor
        self.entity_id       = f"{PLATFORM_SENSOR}.{self.entity_name}"
        self._attr_unique_id = f"{DOMAIN}_{self.entity_name}"

        Gb.sensors_created_cnt += 1
        self.sensor_number = Gb.sensors_created_cnt

        self._unsub_dispatcher = None
        self.current_state_value = ''

        eid_assigned = entity_io.get_assigned_sensor_entity(self._attr_unique_id)
        if eid_assigned and eid_assigned != self.entity_id:
            extn_added = f"+{eid_assigned.replace(self.entity_id, '')}"
            extn_alert = f" {RED_ALERT} Added-`{extn_added}`"
        else:
            extn_alert = ''
        log_debug_msg(  f"Sensor entity, Config: {self.entity_id}{extn_alert}, #{self.sensor_number}")

#..........................................................................................
    @property
    def name(self):
        '''Sensor friendly name.'''
        return self.fname

    @property
    def unique_id(self):
        return f"{self.entity_name}"

    @property
    def device(self):
        return self.unique_id()

    @property
    def device_info(self) -> DeviceInfo:
        """Return information about the device """
        return DeviceInfo(  identifiers = {(DOMAIN, DOMAIN)},
                            manufacturer = 'gcobb321',
                            model        = 'Intergration',
                            name         = 'iCloud3 Integration'
                        )

    @property
    def should_poll(self):
        ''' Do not poll to update the sensor '''
        return False

#-------------------------------------------------------------------------------------------
    async def async_added_to_hass(self):

        log_debug_msg(f"Sensor entity, Added:  {self.entity_id}, #{self.sensor_number}")

#-------------------------------------------------------------------------------------------
    def async_update_sensor(self):
        """Update the entity's state."""
        if Gb.hass is None: return

        try:
            self.schedule_update_ha_state()

        except (RuntimeError, AttributeError):
            pass
        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    async def async_will_remove_from_hass(self):
        '''Clean up after entity before removal.'''
        try:
            self._unsub_dispatcher()

        except TypeError:
            pass
        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<iCloud3Sensor: {self.entity_name}>")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_EventLog(iCloud3Sensor_Base, SensorEntity):

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['event_log'])

    @property
    def icon(self):
        return 'mdi:message-text-clock-outline'

    @property
    def native_value(self):
        '''State value - (devicename:time)'''
        try:
            if Gb.EvLog is None:
                return 'Unavailable'

            time_suffix = (f"{dt_util.now().strftime('%a, %m/%d')}, "
                            f"{dt_util.now().strftime(Gb.um_time_strfmt)}."
                            f"{dt_util.now().strftime('%f')}")

            return (f"{Gb.EvLog.evlog_sensor_state_value}:{time_suffix}")

        except Exception as err:
            log_exception(err)
            return 'Unavailable'

    @property
    def extra_state_attributes(self):
        '''Return default attributes for the iCloud device entity.'''
        update_time = ( f"{dt_util.now().strftime('%a, %m/%d')}, "
                        f"{dt_util.now().strftime(Gb.um_time_strfmt)}."
                        f"{dt_util.now().strftime('%f')}")
        Gb.EvLog.evlog_attrs['update_time'] = update_time

        if Gb.EvLog:
            return Gb.EvLog.evlog_attrs

        return {'log_level_debug': '',
                'filtername': 'Initialize',
                'update_time': update_time,
                'popup_message': 'Starting',
                'names': {'Loading': 'Initializing iCloud3'},
                'logs': [],
                'platform': Gb.operating_mode}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_WazeHistTrack(iCloud3Sensor_Base, SensorEntity):
    '''iCloud Waze History Track GPS Values Sensor.'''

    _unrecorded_attributes = frozenset(SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS['waze_info'])

    @property
    def icon(self):
        return 'mdi:map-check-outline'

    @property
    def native_value(self):
        '''State value - (latitude, longitude)'''
        if Gb.WazeHist is None:
            return 'Not Used'

        return f"{Gb.WazeHist.track_latitude}, {Gb.WazeHist.track_longitude}"

    @property
    def extra_state_attributes(self):
        '''Return default attributes for the iCloud device entity.'''
        if Gb.WazeHist is None:
            return None

        return {'integration': ICLOUD3,
                'records': Gb.WazeHist.track_recd_cnt,
                'updated': datetime_now(),
                'latitude': Gb.WazeHist.track_latitude,
                'longitude': Gb.WazeHist.track_longitude,
                'friendly_name': 'WazeHist'}


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><
