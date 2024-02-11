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
from .const             import (DOMAIN, VERSION, ICLOUD3, RARROW,
                                SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                                HOME, HOME_FNAME, NOT_SET, NOT_SET_FNAME, NONE_FNAME,
                                DATETIME_ZERO, HHMMSS_ZERO,
                                BLANK_SENSOR_FIELD, DOT, HDOT, HDOT2, UM_FNAME, NBSP,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME, FNAME, BADGE, FROM_ZONE,
                                ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                BATTERY, BATTERY_STATUS,
                                CONF_TRACK_FROM_ZONES,
                                CONF_IC3_DEVICENAME, CONF_MODEL, CONF_RAW_MODEL, CONF_FNAME,
                                CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE,
                                )
from .const_sensor      import (SENSOR_DEFINITION, SENSOR_GROUPS, SENSOR_LIST_DISTANCE,
                                SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, )

from .helpers.common    import (instr,  round_to_zero, is_statzone, set_precision, )
from .helpers.messaging import (log_info_msg, log_debug_msg, log_error_msg, log_exception,
                                _trace, _traceha, )
from .helpers.time_util import (time_to_12hrtime, time_remove_am_pm, secs_to_time_str,
                                mins_to_time_str, time_now_secs, datetime_now,
                                secs_to_datetime, adjust_time_hour_values,
                                adjust_time_hour_value)
from .helpers.dist_util import (km_to_mi, m_to_ft, )
from .helpers.format    import (icon_circle, icon_box, )
from collections        import OrderedDict
from .helpers           import entity_io
from .support           import start_ic3
from .support           import recorder_prefilter

from homeassistant.components.sensor    import SensorEntity
from homeassistant.config_entries       import ConfigEntry
from homeassistant.helpers.entity       import DeviceInfo

from homeassistant.core                 import HomeAssistant
from homeassistant.helpers.icon         import icon_for_battery_level
from homeassistant.helpers              import entity_registry as er, device_registry as dr

import homeassistant.util.dt as dt_util
# from homeassistant.helpers.entity       import Entity

import logging
_HA_LOGGER = logging.getLogger(__name__)
# _LOGGER = logging.getLogger(f"icloud3")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    '''Set up iCloud3 sensors'''

    # Save the hass `add_entities` call object for use in config_flow for adding new sensors
    Gb.hass = hass
    Gb.async_add_entities_sensor = async_add_entities

    try:
        if Gb.conf_file_data == {}:
            start_ic3.initialize_directory_filenames()
            start_ic3.load_storage_icloud3_configuration_file()

        NewSensors = []
        Gb.EvLogSensor = Sensor_EventLog('iCloud3 Event Log', SENSOR_EVENT_LOG_NAME)
        if Gb.EvLogSensor:
            NewSensors.append(Gb.EvLogSensor)
        else:
            log_error_msg("Error setting up Event Log Sensor")

        Gb.WazeHistTrackSensor = Sensor_WazeHistTrack('iCloud3 Waze History Track', SENSOR_WAZEHIST_TRACK_NAME)
        if Gb.WazeHistTrackSensor:
            NewSensors.append(Gb.WazeHistTrackSensor)
        else:
            log_error_msg("Error setting up Waze History Track Sensor")

        # Create the selected sensors for each devicename
        # Cycle through each device being tracked or monitored and create it's sensors
        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]

            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                continue

            if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
                NewSensors.extend(create_tracked_device_sensors(devicename, conf_device))

            elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
                NewSensors.extend(create_monitored_device_sensors(devicename, conf_device))

        # Set the total count of the sensors that will be created
        if Gb.sensors_cnt == 0:
            excluded_sensors_list = _excluded_sensors_list()
            Gb.sensors_cnt = len(NewSensors)
            log_info_msg(f'Sensor entities created:  {len(NewSensors)}')
            log_info_msg(f'Sensor entities excluded: {len(excluded_sensors_list)}')

        if NewSensors != []:
            async_add_entities(NewSensors, True)
            _setup_recorder_exclude_sensor_filter(NewSensors)
            _HA_LOGGER.info(f'iCloud3 Sensor entities: {len(NewSensors)}')

    except Exception as err:
        _HA_LOGGER.exception(err)
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def create_tracked_device_sensors(devicename, conf_device, new_sensors_list=None):
    '''
    Add icloud3 sensors that have been selected via config_flow and
    arein the Gb.conf_sensors for each device
    '''
    try:
        NewSensors = []
        Gb.sensors_created_cnt = 0

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
    # Get the sensor entity name and create the sensor.[ic3_devicename]_[sensor_name] entity
    # The sensor_def name is the conf_sensor name set up in the Sensor_definition table.
    # The table contains the actual ha sensor entity name. That permits support for track-from-zone
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
            log_debug_msg(f"Sensor entity excluded: sensor.{devicename_sensor}")
            continue

        Sensor = None
        if sensor in devicename_sensors:
            # Sensor object might exist, use it to recreate the sensor entity
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
                log_debug_msg(f"Sensor entity excluded: sensor.{devicename_sensor_zone}")
                continue

            if sensor_zone in devicename_from_zone_sensors:
                continue

            # Sensor object might exist, use it to recreate the sensor entity
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
        # Get the sensor entity name and create the sensor.[ic3_devicename]_[sensor_name] entity
        # The sensor_def name is the conf_sensor name set up in the Sensor_definition table.
        # The table contains the actual ha sensor entity name. That permits support for track-from-zone
        # suffixes.
        for sensor in sensors_list:
            Sensor = None

            devicename_sensor = f"{devicename}_{sensor}"
            if devicename_sensor in excluded_sensors_list:
                log_debug_msg(f"Sensor entity excluded: sensor.{devicename_sensor}")
                continue

            # Sensor object might exist, use it to recreate the sensor entity
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
def _setup_recorder_exclude_sensor_filter(NewSensors):

    exclude_entities = []

    for Sensor in NewSensors:
        if Sensor.history_exclude_flag:
            exclude_entities.append(Sensor.entity_id)

    if exclude_entities != []:
        recorder_prefilter.add_filter(Gb.hass, exclude_entities)

    return

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
        return Sensor_Battery(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('text'):
        return Sensor_Text(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('timestamp'):
        return Sensor_Timestamp(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('timer'):
        return Sensor_Timer(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('distance'):
        return Sensor_Distance(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('zone_info'):
        return Sensor_ZoneInfo(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('zone'):
        return Sensor_Zone(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('info'):
        return Sensor_Info(devicename, sensor, conf_device, from_zone)
    elif sensor_type.startswith('badge'):
        return Sensor_Badge(devicename, sensor, conf_device, from_zone)
    else:
        log_error_msg('iCloud3 Sensor Setup Error, Sensor-{sensor} > Invalid Sensor Type-{sensor_type}')
        return None

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class SensorBase(SensorEntity):
    ''' iCloud base device sensor '''

    def __init__(self, devicename, sensor_base, conf_device, from_zone=None):
        try:
            self.hass        = Gb.hass
            self.devicename  = devicename
            self.conf_device = conf_device

            self.from_zone   = from_zone
            if from_zone:
                self.from_zone_fname = f" ({from_zone.title().replace('_', '').replace(' ', '')})"
                self.sensor          = f"{sensor_base}_{from_zone}"
            else:
                self.from_zone_fname = ''
                self.sensor          = sensor_base

            self.entity_name     = f"{devicename}_{self.sensor}"
            self.entity_id       = f"sensor.{self.entity_name}"
            self.device_id       = Gb.ha_device_id_by_devicename.get(ICLOUD3)

            self.Device          = Gb.Devices_by_devicename.get(devicename)
            if self.Device and from_zone:
                self.FromZone = self.Device.FromZones_by_zone.get(from_zone)
            else:
                self.FromZone = None


            self._attr_force_update = True
            self._unsub_dispatcher  = None
            self._on_remove         = [self.after_removal_cleanup]
            self.entity_removed_flag = False

            self.sensor_base     = sensor_base
            self.sensor_type     = self._get_sensor_definition(sensor_base, SENSOR_TYPE).replace(' ', '')
            self.sensor_fname    = (f"{conf_device[FNAME]} "
                                    f"{self._get_sensor_definition(sensor_base, SENSOR_FNAME)}"
                                    f"{self.from_zone_fname}")
            self._attr_native_unit_of_measurement = None

            self._state = self._get_restore_or_default_value(sensor_base)
            self.current_state_value = ''

            # Add this sensor to the HA Recorder history exclude entity list
            self.history_exclude_flag = instr(self.sensor_type, 'ha_history_exclude')

            Gb.sensors_created_cnt += 1
            log_debug_msg(f'Sensor entity created: {self.entity_id}, #{Gb.sensors_created_cnt}')

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
        update_time = datetime_now()
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

            if instr(_sensor_attr_name, ZONE_DISTANCE_M_EDGE):
                extra_attrs[_sensor_attr_name] = _sensor_value

                if Gb.um_MI:
                    zone_dist_m = float(self._get_sensor_value(ZONE_DISTANCE_M))
                    sensor_value_mi = zone_dist_m*Gb.um_km_mi_factor/1000
                    extra_attrs['distance_(miles)'] = set_precision(sensor_value_mi)
                    extra_attrs['distance_units_(attributes)'] = 'mi'

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
        Get a default value that is used when iCloud3 has not started or the Device for the
        sensor has not veen created.
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

        log_debug_msg(f"Sensor entity changed: {self.entity_id}, {self.sensor_fname}")

        kwargs = {}
        kwargs['original_name'] = self.sensor_fname

        entity_registry = er.async_get(Gb.hass)
        entity_registry.async_update_entity(self.entity_id, **kwargs)

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
    def remove_entity(self):
        try:
            Gb.hass.async_create_task(self.async_remove(force_remove=True))

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def after_removal_cleanup(self):
        """ Cleanup sensor after removal

        Passed in the `self._on_remove` parameter during initialization
        and called by HA after processing the async_remove request
        """

        log_info_msg(f"Unregistered sensor.icloud3 entity Removed: {self.entity_id}")

        self._remove_from_registries()
        self.entity_removed_flag = True

        if self.Device is None:
            return

        if self.Device.Sensors_from_zone and self.sensor in self.Device.Sensors_from_zone:
            self.Device.Sensors_from_zone.pop(self.sensor)

        if self.Device.Sensors and self.sensor in self.Device.Sensors:
            self.Device.Sensors.pop(self.sensor)

#-------------------------------------------------------------------------------------------
    def _remove_from_registries(self) -> None:
        """ Remove entity/device from registry """

        if not self.registry_entry:
            return

        if entity_id := self.registry_entry.entity_id:
            entity_registry = er.async_get(Gb.hass)
            if entity_id in entity_registry.entities:
                entity_registry.async_remove(self.entity_id)

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
            self.async_write_ha_state()

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
class Sensor_Badge(SensorBase):
    '''  Sensor for displaying the device badge items '''

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


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_ZoneInfo(SensorBase):
    '''  Sensor for displaying the device zone time/distance items '''

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
class Sensor_Text(SensorBase):
    '''  Sensor for handling text items '''

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(self.sensor)

        # if instr(self.sensor_type, 'title'):
        #     sensor_value = sensor_value.title().replace('_', ' ')

        if instr(self.sensor_type, 'time'):
            if instr(sensor_value, ' '):
                text_um_parts = sensor_value.split(' ')
                sensor_value = text_um_parts[0]
                self._attr_unit_of_measurement = text_um_parts[1]
            else:
                self._attr_unit_of_measurement = None

        # Set to space if empty
        if sensor_value.strip() == '':
            sensor_value = BLANK_SENSOR_FIELD

        if self.Device and self.Device.away_time_zone_offset != 0:
            sensor_value = adjust_time_hour_values(sensor_value, self.Device.away_time_zone_offset)

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Info(SensorBase):
    '''
        Sensor for handling info sensor messages.
            1.  This will update a specific Device's info sensor using the
                Device.update_info_message('msg') function.
                broadcase_info_msg('msg') function in base.py by entering the
                message into the 'Gb.broadcast_info_msg' field. This lets you display
                an info message during startup before the devices have been created
                or to everyone as a general notification.
    '''

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
class Sensor_Timestamp(SensorBase):
    '''
    Sensor for handling timestamp (mm/dd/yy hh:mm:ss) items
    Sensors: last_update_time, next_update_time, last_located
    '''

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(self.sensor)
        sensor_value = time_to_12hrtime(sensor_value)
        if self.Device and self.Device.away_time_zone_offset != 0:
            sensor_value = adjust_time_hour_value(sensor_value, self.Device.away_time_zone_offset)

        try:
            # Drop the 'a' or 'p' so the field will fit on an iPhone
            if int(sensor_value.split(':')[0]) >= 10:
                sensor_value = time_remove_am_pm(sensor_value)
        except:
            pass

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Timer(SensorBase):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

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
            time_str = mins_to_time_str(sensor_value)
            if time_str and instr(time_str, 'd') is False:         # Make sure it is not a 4d2h34m12s item
                time_min_hrs = time_str.split(' ')
                sensor_value = time_min_hrs[0]
                self._attr_native_unit_of_measurement = time_min_hrs[1]

        elif sensor_type_um == 'sec':
            time_str = secs_to_time_str(sensor_value)
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
class Sensor_Distance(SensorBase):
    '''
    Sensor for handling timer items (30 secs, 1.5 hrs, 30 mins)
    Sensors: inteval, travel_time, travel_time_mins
    '''

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
                sensor_value = 0
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
                sensor_value = 0
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

    @property
    def extra_state_attributes(self):
        extra_attrs = self._get_extra_attributes(self.sensor)

        if self.Device is None:
            return extra_attrs

        if self.sensor.endswith('distance'):
            extra_attrs.update(self._format_zone_distance_extra_attrs())
            extra_attrs.update(self._format_devices_distance_extra_attrs())

        return extra_attrs

    def _format_zone_distance_extra_attrs(self):
        '''
        Get the distance to each zone and build the extra_attributes Zone distance items
        '''

        dist_attrs = OrderedDict()
        zone_dist_km = {f" - {Zone.dname}": set_precision(self.Device.Distance_km(Zone), 'km')
                                for Zone in Gb.HAZones}
        zone_dist_mi = {zone_da: set_precision(km_to_mi(dist_km), 'mi')
                                for zone_da, dist_km in zone_dist_km.items()}

        zone_dist_m  = {f" - {Zone.dname}*": set_precision(self.Device.Distance_m(Zone), 'm')
                                for Zone in Gb.HAZones
                                if self.Device.Distance_m(Zone) < 500}
        zone_dist_ft = {zone_da: set_precision(m_to_ft(dist_m), 'ft')
                                for zone_da, dist_m in zone_dist_m.items()}

        dist_attrs[f"zone_distance"] = f"({Gb.um}) @{datetime_now()}"
        if Gb.um_KM:
            dist_attrs.update(zone_dist_km)
        else:
            dist_attrs.update(zone_dist_mi)

        if zone_dist_m or zone_dist_ft:
            dist_attrs[f"zone_distance* (< 500m)"] = f"({Gb.um_m_ft}) @{datetime_now()}"
            if Gb.um_KM:
                dist_attrs.update(zone_dist_m)
            else:
                dist_attrs.update(zone_dist_ft)

        return dist_attrs

    def _format_devices_distance_extra_attrs(self):
        '''
        Get the distance to each zone and build the extra_attributes Zone distance items.
        Use distance apart from this device for the distance data.
        {devicename: [distance_m, gps_accuracy_factor, display_text]}
        '''
        dist_attrs = OrderedDict()
        device_dist_m   = {f" - {self._fname(devicename)}": set_precision(dist_to_other_devices[0], 'm')
                                for devicename, dist_to_other_devices in self.Device.dist_to_other_devices.items()
                                if dist_to_other_devices[0] > .001 and dist_to_other_devices[0] < 500}
        device_dist_ft = {device_fn: set_precision(m_to_ft(dist_m), 'ft')
                                for device_fn, dist_m in device_dist_m.items()}

        device_dist_km  = {f" - {self._fname(devicename)}*": set_precision(dist_to_other_devices[0]/1000, 'km')
                                for devicename, dist_to_other_devices in self.Device.dist_to_other_devices.items()
                                if dist_to_other_devices[0] >= 500}
        device_dist_mi = {device_fn: set_precision(km_to_mi(dist_km), 'mi')
                                for device_fn, dist_km in device_dist_km.items()}

        if device_dist_m or device_dist_ft:
            dist_attrs["device_distance (< 500m)"] = (f"({Gb.um_m_ft}) "
                                f"@{secs_to_datetime(self.Device.dist_to_other_devices_secs)}")
            if Gb.um_KM:
                dist_attrs.update(device_dist_m)
            else:
                dist_attrs.update(device_dist_ft)

        if device_dist_km or device_dist_mi:
            dist_attrs["device_distance"] = (f"({Gb.um}) "
                                f"@{secs_to_datetime(self.Device.dist_to_other_devices_secs)}")
            if Gb.um_KM:
                dist_attrs.update(device_dist_km)
            else:
                dist_attrs.update(device_dist_mi)

        return dist_attrs

    def _fname(self, devicename):
        if Device := Gb.Devices_by_devicename.get(devicename):
            return Device.fname_devtype
        else:
            return devicename

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_Battery(SensorBase):
    '''
    Sensor for handling battery items (30s)
    Sensors: battery
    '''

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
class Sensor_Zone(SensorBase):
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

    @property
    def native_value(self):
        sensor_value = self._get_sensor_value(f"{self.sensor}")

        return sensor_value

    @property
    def extra_state_attributes(self):
        return self._get_extra_attributes(self.sensor)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Support_SensorBase(SensorEntity):
    ''' iCloud Support Sensor Base
        - Event Log
        - Waze History Track
    '''

    def __init__(self, fname, entity_name):
        '''Initialize the Event Log sensor (icloud3_event_log).'''
        self.fname             = fname
        self.sensor            = entity_name
        self.entity_name       = entity_name
        self.entity_id         = f"sensor.{self.entity_name}"
        self._unsub_dispatcher = None
        self._device           = DOMAIN
        self.current_state_value = ''
        self.history_exclude_flag = False \
            if self.entity_name == SENSOR_WAZEHIST_TRACK_NAME \
            else True

        Gb.sensors_created_cnt += 1
        log_debug_msg(f'Sensor entity created: {self.entity_id}, #{Gb.sensors_created_cnt}')

        # Add this sensor to the Recorder history exclude entity list
        # try:
        #     ha_history_recorder = Gb.hass.data['recorder_instance']
        #     ha_history_recorder.entity_filter._exclude_e.add(self.entity_id)
        # except:
        #     pass

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

#-------------------------------------------------------------------------------------------
    def __repr__(self):
        return (f"<DeviceSensor: {self.entity_name}>")

    @property
    def should_poll(self):
        ''' Do not poll to update the sensor '''
        return False

#-------------------------------------------------------------------------------------------
    def async_update_sensor(self):
        """Update the entity's state."""

        try:
            self.async_write_ha_state()

        except RuntimeError:
            # Catch a 'RuntimeError: Attribute hass is None for <DeviceSensor: icloud3_event_log>'
            pass
        except Exception as err:
            log_exception(err)

    async def async_will_remove_from_hass(self):
        '''Clean up after entity before removal.'''
        try:
            self._unsub_dispatcher()

        except TypeError:
            pass
        except Exception as err:
            log_exception(err)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_EventLog(Support_SensorBase):

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
        Gb.EvLog.evlog_attrs['update_time'] =\
                            (f"{dt_util.now().strftime('%a, %m/%d')}, "
                            f"{dt_util.now().strftime(Gb.um_time_strfmt)}."
                            f"{dt_util.now().strftime('%f')}")
        if Gb.EvLog:
            return Gb.EvLog.evlog_attrs

        return {'log_level_debug': '',
                'filtername': 'Initialize',
                'update_time': log_update_time,
                'popup_message': 'Starting',
                'names': {'Loading': 'Initializing iCloud3'},
                'logs': [],
                'platform': Gb.operating_mode}


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Sensor_WazeHistTrack(Support_SensorBase):
    '''iCloud Waze History Track GPS Values Sensor.'''

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
