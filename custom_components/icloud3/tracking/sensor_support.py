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

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, PLATFORM_SENSOR, ICLOUD3, RARROW,
                                SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                                HOME, HOME_FNAME, NOT_SET, NOT_SET_FNAME, NONE_FNAME,
                                DATETIME_ZERO, HHMMSS_ZERO,
                                BLANK_SENSOR_FIELD, DOT, HDOT, UM_FNAME, NBSP, RED_ALERT,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME, FNAME, BADGE, FROM_ZONE, ZONE,
                                ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                HOME_DISTANCE,
                                BATTERY, BATTERY_STATUS,
                                WAZE_DISTANCE, WAZE_DISTANCE_ATTR, WAZE_METHOD, WAZE_USED,
                                CALC_DISTANCE, CALC_DISTANCE_ATTR,
                                CONF_TRACK_FROM_ZONES,
                                CONF_IC3_DEVICENAME, CONF_MODEL, CONF_RAW_MODEL, CONF_FNAME,
                                CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE,
                                )
from ..const_sensor     import (SENSOR_DEFINITION, SENSOR_GROUPS, SENSOR_LIST_DISTANCE,
                                SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, ICLOUD3_SENSORS,
                                SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS, )

from ..utils            import entity_io
from ..utils.utils      import (instr, is_empty, isnot_empty, round_to_zero, isnumber,
                                list_add, )
from ..utils.messaging  import (post_event, log_info_msg, log_debug_msg, log_error_msg,
                                log_exception, log_info_msg_HA, log_exception_HA,  _evlog, _log, )

from ..sensor           import (Sensor_EventLog, Sensor_WazeHistTrack,
                                Sensor_Battery, Sensor_Text, Sensor_Timestamp, Sensor_Timer,
                                Sensor_Distance, Sensor_ZoneInfo, Sensor_Zone, Sensor_Info,
                                Sensor_Badge, )

#--------------------------------------------------------------------
from homeassistant.helpers   import entity_registry as er, device_registry as dr

import homeassistant.util.dt as dt_util


#--------------------------------------------------------------------
def create_icloud3_sensors():
    '''
    Create iCloud3 internal sensors (event_log and waze_history_track sensors)
    '''
    NewSensors = []
    Gb.EvLogSensor = Sensor_EventLog(SENSOR_EVENT_LOG_NAME)
    if Gb.EvLogSensor:
        NewSensors.append(Gb.EvLogSensor)
    else:
        log_error_msg("Error setting up Event Log Sensor")

    Gb.WazeHistTrackSensor = Sensor_WazeHistTrack(SENSOR_WAZEHIST_TRACK_NAME)
    if Gb.WazeHistTrackSensor:
        NewSensors.append(Gb.WazeHistTrackSensor)
    else:
        log_error_msg("Error setting up Waze History Track Sensor")

    return NewSensors

#--------------------------------------------------------------------
def create_device_sensors():
    '''
    Create sensors for each device being track or monitored
    '''

    NewSensors = []
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]

        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            continue

        if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
            NewSensors.extend(create_tracked_device_sensors(devicename, conf_device))

        elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            NewSensors.extend(create_monitored_device_sensors(devicename, conf_device))

    # except Exception as err:
    #     log_exception(err)
    #     log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
    #     log_error_msg(log_msg)

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

        NewSensors.extend(_create_device_base_sensors(devicename, conf_device, sensors_list_set))
        NewSensors.extend(_create_track_from_zone_sensors(devicename, conf_device, sensors_list_set))

        return NewSensors

    except Exception as err:
        log_exception(err)
        log_msg = (f"►INTERNAL ERROR (UpdtSensorUpdate-{err})")
        log_error_msg(log_msg)

#--------------------------------------------------------------------
def _create_device_base_sensors(devicename, conf_device, sensors_list):

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
        sensor_def = []
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
                list_add(sensor_def, [devicename, sensor, conf_device])

            if Sensor:
                Sensor = _create_sensor_by_type(devicename, sensor, conf_device)
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
def rename_all_entity_id_x_to_entity_id_base():

    # _log(f"{Gb.Sensors_by_devicename=}")
    # _log(f"{Gb.Sensors_by_devicename_from_zone=}")

    eid_x_Sensors = []
    for devicename, device_sensors in Gb.Sensors_by_devicename.items():
        for sensor_name, Sensor in device_sensors.items():
            # _log(f"{devicename} {sensor_name} {Sensor} {Sensor.entity_id=} {Sensor.entity_id_base=}")
            if Sensor.entity_id != Sensor.entity_id_base:
                list_add(eid_x_Sensors, Sensor)
    # _log(f"{eid_x_Sensors=}")

    if isnot_empty(eid_x_Sensors):
        # entity_reg = er.async_get(Gb.hass)
        for Sensor in eid_x_Sensors:
        #     _log(f"RENAME  {Sensor.entity_id=} --> {Sensor.entity_id_base}")
        #     new_entity_id = Sensor.entity_id_base
            try:
                # _log(f"DELETE  {Sensor.entity_id_base=}")

                # entity_reg.async_remove(Sensor.entity_id_base)
                # entity_reg._unindex_entry(Sensor.entity_id_base, None)
                entity_io.remove_entity(Sensor.entity_id_base)
                # _log(f"DELETED {Sensor.entity_id_base=}")
            except KeyError as err:
                pass
            except Exception as err:
                log_exception(err)
                pass

            try:
                # _log(f"DELETE  {Sensor.entity_id=}")
                # entity_reg.async_remove(Sensor.entity_id)
                # entity_reg._unindex_entry(Sensor.entity_id, None)
                entity_io.remove_entity(Sensor.entity_id)
                # _log(f"DELETED {Sensor.entity_id=}")
            except KeyError as err:
                pass
            except Exception as err:
                log_exception(err)
                pass

    return eid_x_Sensors

        #     # Gb.hass.async_add_executor_job(
        #     #                     entity_reg.async_update_entity,
        #     #                     Sensor.entity_id,
        #     #                     new_entity_id)
        #     try:
        #         entity_reg.async_update_entity(Sensor.entity_id, new_entity_id=new_entity_id)
        #     except Exception as err:
        #         log_exception(err)

        #     _log(f"RENAMED {Sensor.entity_id=} --> {Sensor.entity_id_base}")
        #     Sensor.entity_id = Sensor.entity_id_base
        # Gb.async_add_entities_sensor(eid_x_Sensors, True)