

from ..global_variables  import GlobalVariables as Gb
from ..const             import (PLATFORM_DEVICE_TRACKER, PLATFORM_SENSOR,
                                INACTIVE, TRACK,
                                CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, CONF_TRACK_FROM_ZONES,
                                CONF_EXCLUDED_SENSORS, CONF_SENSORS_MONITORED_DEVICES,
                                HOME, NONE_FNAME, FROM_ZONE, ZONE, SENSORS,
                                TRACK, MONITOR, INACTIVE,
                                BATTERY, BATTERY_STATUS,
                                CONF_IC3_DEVICENAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE,
                                )
from ..const_sensor     import (SENSOR_DEFINITION, SENSOR_GROUPS, SENSOR_LIST_DISTANCE,
                                SENSOR_FNAME, SENSOR_TYPE, SENSOR_ICON,
                                SENSOR_ATTRS, SENSOR_DEFAULT, SENSOR_LIST_ALWAYS, ICLOUD3_SENSORS,
                                SENSOR_TYPE_RECORDER_EXCLUDE_ATTRS, )

from ..utils.utils      import (instr, is_number, is_empty, isnot_empty, list_add, list_del,
                                encode_password, decode_password, )
from ..utils.messaging  import (log_exception, log_debug_msg, log_error_msg, add_log_file_filter,
                                _log, _evlog, )

from ..startup           import config_file
from ..utils             import entity_io
from ..utils             import entity_reg_util as er_util
from ..                  import sensor as ic3_sensor
from ..                  import device_tracker as ic3_device_tracker

from .const_form_lists   import (MENU_KEY_TEXT, ACTION_LIST_ITEMS_KEY_BY_TEXT, ACTION_LIST_OPTIONS,
                                    )

from homeassistant.helpers  import (entity_registry as er,
                                    device_registry as dr, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#      ROUTINES THAT SUPPORT REMOVE SENSOR AND DEVICE_TRACKER ENTITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def identify_new_and_removed_sensors(self, user_input):
    '''
    Add newly checked/delete newly unchecked ha sensor entities
    '''

    sensors_to_add    = []
    sensors_to_remove = []     # base device sensors

    sensors_to_exclude = [config_file.get_excluded_sensor_devicename_sensor(sensor)
                                for sensor in user_input[CONF_EXCLUDED_SENSORS]
                                if sensor not in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]]
    sensors_to_not_exclude = [config_file.get_excluded_sensor_devicename_sensor(sensor)
                                for sensor in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                if sensor not in user_input[CONF_EXCLUDED_SENSORS]]


    sensors_to_add.extend(sensors_to_not_exclude)
    sensors_to_remove.extend(sensors_to_exclude)


    for sensor_group, sensor_list in user_input.items():
        if (sensor_group not in Gb.conf_sensors
                or user_input[sensor_group] == Gb.conf_sensors[sensor_group]
                or sensor_group == CONF_EXCLUDED_SENSORS):
            if user_input[CONF_EXCLUDED_SENSORS] != Gb.conf_sensors[CONF_EXCLUDED_SENSORS]:
                list_add(self.config_parms_update_control, ['xrestart_ha', 'restart'])
            continue

        # Cycle thru the sensors now in the user_input sensor_group
        # Get list of sensors to be added
        for sensor in sensor_list:
            if sensor not in SENSOR_GROUPS['default']:
                sensors_to_add.append(sensor)
            elif sensor not in Gb.conf_sensors[sensor_group]:
                if sensor == 'last_zone':
                    if 'zone'       in Gb.conf_sensors[sensor_group]: sensors_to_add.append('last_zone')
                    if 'zone_name'  in Gb.conf_sensors[sensor_group]: sensors_to_add.append('last_zone_name')
                    if 'zone_fname' in Gb.conf_sensors[sensor_group]: sensors_to_add.append('last_zone_fname')
                else:
                    sensors_to_add.append(sensor)

        # Get list of sensors to be removed
        for sensor in Gb.conf_sensors[sensor_group]:
            if sensor in SENSOR_GROUPS['default']:
                pass
            elif sensor not in sensor_list:
                if sensor == 'last_zone':
                    if 'zone'       in sensor_list: sensors_to_remove.append('last_zone')
                    if 'zone_name'  in sensor_list: sensors_to_remove.append('last_zone_name')
                    if 'zone_fname' in sensor_list: sensors_to_remove.append('last_zone_fname')
                else:
                    sensors_to_remove.append(sensor)

    return sensors_to_add, sensors_to_remove, sensors_to_exclude, sensors_to_not_exclude

#-------------------------------------------------------------------------------------------
def remove_sensors_from_excluded_sensors_list(sensors_to_remove):

    if is_empty(sensors_to_remove):
        return

    for devicename_sensor in sensors_to_remove:
        er_util.remove_Sensor_and_clear_dicts(devicename_sensor)

#-------------------------------------------------------------------------------------------
def remove_device_tracker_and_sensor_entities(self, devicename, rebuild_ic3db_dashboards=True):
    """ Remove a specific device from the ha entity registry

        Remove device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
        associated with the device.

        devicename:
            devicename to be removed
    """
    # Device and sensors are being deleted via config_flow. This is used in the
    # er_util.remove_device_listener to indicate the device is being removed
    # by iCloud3 instead of the user via ha
    self.is_deleting_device = True

    # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
    er_util.update_ha_device_id_by_devicename()
    if Gb.DeviceTrackers_by_devicename.get(devicename) is None:
        return

    if devicename in Gb.Sensors_by_devicename:
        for sensor, Sensor in Gb.Sensors_by_devicename[devicename].copy().items():
            er_util.remove_from_active_and_deleted_entity_registry(Sensor.entity_id)
            er_util.clear_sensor_gb_dicts(Sensor.entity_id)
        #     er_util.remove_sensor(Sensor.entity_id)
        #     del Sensor
        # del Gb.Sensors_by_devicename[devicename]

    if devicename in Gb.Sensors_by_devicename_from_zone:
        for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].copy().items():
            er_util.remove_from_active_and_deleted_entity_registry(Sensor.entity_id)
            er_util.clear_sensor_gb_dicts(Sensor.entity_id)

    if devicename in Gb.DeviceTrackers_by_devicename:
        DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        device_id = DeviceTracker.ha_device_id
        DeviceTracker.remove_device_tracker()
        er_util.remove_from_active_and_deleted_device_registry(device_id)
        er_util.clear_device_gb_dicts(device_id)

    er_util.update_ha_device_id_by_devicename()
    self.is_deleting_device = False
    ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

    if rebuild_ic3db_dashboards:
        self.rebuild_ic3db_dashboards = True

#-------------------------------------------------------------------------------------------
def devices_form_identify_new_and_removed_tfz_zones(self, user_input):
    """ Determine checked/unchecked track_fm_zones """

    new_tfz_zones_list    = []
    remove_tfz_zones_list = []     # base device sensors
    old_tfz_zones_list    = self.conf_device[CONF_TRACK_FROM_ZONES]
    ui_tfz_zones_list     = user_input[CONF_TRACK_FROM_ZONES]

    # Cycle thru the devices tfz zones before the update to get a list of new
    # and removed zones
    for zone in Gb.HAZones_by_zone.keys():
        if zone in ui_tfz_zones_list and zone not in old_tfz_zones_list:
            new_tfz_zones_list.append(zone)
        elif zone in old_tfz_zones_list and zone not in ui_tfz_zones_list:
            remove_tfz_zones_list.append(zone)

    return new_tfz_zones_list, remove_tfz_zones_list

#-------------------------------------------------------------------------------------------
def remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list):
    '''
    Remove the all tfz sensors for all of the just unchecked zones
    This is called when a zone is removed from the tfz list on the Update Devices
    screen and when a tfz zone is deleted from HA and being removed from iCloud3
    in start_ic3 module
    '''

    if remove_tfz_zones_list == []:
        return

    device_tfz_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename)

    if device_tfz_sensors is None:
        return

    # Cycle through the zones that are no longer tracked from for the device, then cycle
    # through the Device's sensor list and remove all track_from_zone sensors ending with
    # that zone.
    removed_sensors = []
    for zone in remove_tfz_zones_list:
        for sensor, Sensor in device_tfz_sensors.copy().items():
            devicename_sensor = f'{devicename}_{sensor}'
            if (sensor.endswith(f"_{zone}")
                    and devicename_sensor not in Gb.Sensors_by_devicename_sensor):
                er_util.remove_sensor(devicename_sensor)

    ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

#-------------------------------------------------------------------------------------------
def update_track_from_zones_sensors(self, user_input):
    '''
    Update track_from zone sensors that were changed on the Update Devices screen.
    Called from config_flow Update Devices Other fields screen
    '''

    devicename = self.conf_device[CONF_IC3_DEVICENAME]
    self.conf_device[CONF_TRACK_FROM_ZONES] = user_input[CONF_TRACK_FROM_ZONES]

    # Remove the new track_fm_zone sensors just unchecked
    if 'remove_tfz_zones' in self.update_device_ha_sensor_entity:
        remove_tfz_zones_list = self.update_device_ha_sensor_entity['remove_tfz_zones']
        remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list)

        if self.conf_device[CONF_TRACK_FROM_ZONES] == ['home']:
            self.conf_device[CONF_TRACK_FROM_ZONES] = []

    # Create the new track_fm_zone sensors just checked
    if 'new_tfz_zones' in self.update_device_ha_sensor_entity:
        new_tfz_zones_list = self.update_device_ha_sensor_entity['new_tfz_zones']
        self.create_device_tracker_sensor_enities_on_exit = True

    ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

#-------------------------------------------------------------------------------------------
def remove_sensor_entities(sensors_to_remove, select_devicename=None):
    """ Delete sensors from the ha entity registry and ic3 dictionaries

        sensors_to_remove:
                list of the sensors to be deleted
        selected_devicename:
                specified       - only delete this devicename's sensors
                not_specified   - delete the sensors in the sensors_to_remove from all devices
    """
    if sensors_to_remove == []:
        return

    # Remove regular sensors
    device_tracking_mode = {k['ic3_devicename']: k['tracking_mode'] for k in Gb.conf_devices}
    for devicename, devicename_sensors in Gb.Sensors_by_devicename.items():
        if (devicename not in device_tracking_mode
                or select_devicename and select_devicename != devicename):
            continue

        # Select normal/monitored sensors from the sensors_to_remove for this device
        if device_tracking_mode[devicename] == 'track':      #Device.is_tracked:
            sensors_list = [k for k in sensors_to_remove if k.startswith('md_') is False]
        elif device_tracking_mode[devicename] == 'monitor':      #Device.is_monitored:
            sensors_list = [k for k in sensors_to_remove if k.startswith('md_') is True]
        else:
            continue

        # The sensor group is a group of sensors combined under one conf_sensor item
        # Build sensors to be removed from the the sensor or the sensor's group
        device_sensors_list = []
        for sensor in sensors_list:
            if sensor in SENSOR_GROUPS:
                device_sensors_list.extend(SENSOR_GROUPS[sensor])
            else:
                device_sensors_list.append(sensor)

        Sensors_list = [v for k, v in devicename_sensors.items() if k in device_sensors_list]
        for Sensor in Sensors_list:
            er_util.remove_Sensor_and_clear_dicts(Sensor.entity_name)

        ic3_sensor.log_sensors_added_deleted('REMOVED', devicename)

    # Remove track_fm_zone sensors
    device_track_from_zones = {k['ic3_devicename']: k['track_from_zones'] for k in Gb.conf_devices}
    for devicename, devicename_sensors in Gb.Sensors_by_devicename_from_zone.items():
        if (devicename not in device_track_from_zones
                or select_devicename and select_devicename != devicename):
            continue

        # Create tfz removal list, tfz_sensor --> sensor_zone
        tfz_sensors_list = [f"{k.replace('tfz_', '')}_{z}"
                                        for k in sensors_to_remove if k.startswith('tfz_')
                                        for z in device_track_from_zones[devicename]]

        Sensors_list = [v for k, v in devicename_sensors.items() if k in tfz_sensors_list]
        for Sensor in Sensors_list:
            er_util.remove_remove_Sensor_and_clear_dicts(Sensor.entity_id)

#--------------------------------------------------------------------------------
def build_all_sensors_list():
    """ Get a list of all sensors from the ic3 config file  """

    sensors_list = []
    for sensor_group, sensor_list in Gb.conf_sensors.items():
        if sensor_group == CONF_EXCLUDED_SENSORS:
            continue

        for sensor in Gb.conf_sensors[sensor_group]:
            sensors_list.append(sensor)

    return sensors_list
