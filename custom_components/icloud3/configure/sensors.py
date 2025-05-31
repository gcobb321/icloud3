

from ..global_variables  import GlobalVariables as Gb
from ..const             import (INACTIVE_DEVICE, TRACK_DEVICE,
                                CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, CONF_TRACK_FROM_ZONES,
                                CONF_EXCLUDED_SENSORS, MONITOR_DEVICE,
                                )
from ..const_sensor     import (SENSOR_GROUPS )

from ..utils.utils    import (instr, isnumber, is_empty, isnot_empty, list_add, list_del,
                                encode_password, decode_password, )
from ..utils.messaging import (log_exception, log_debug_msg, log_info_msg, add_log_file_filter,
                                _log, _evlog, )

from ..utils              import entity_io
# from ..utils              import file_io
from ..                  import sensor as ic3_sensor
from ..                  import device_tracker as ic3_device_tracker

from .form_lists_def     import (MENU_KEY_TEXT, ACTION_LIST_ITEMS_KEY_BY_TEXT, ACTION_LIST_OPTIONS,
                                    )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#      ROUTINES THAT SUPPORT ADD & REMOVE SENSOR AND DEVICE_TRACKER ENTITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def remove_and_create_sensors(self, user_input):
    """ Remove unchecked sensor entities and create newly checked sensor entities """

    new_sensors_list, remove_sensors_list = \
            sensor_form_identify_new_and_removed_sensors(self, user_input)
    remove_sensor_entity(remove_sensors_list)

    for conf_device in Gb.conf_devices:
        devicename  = conf_device[CONF_IC3_DEVICENAME]
        create_sensor_entity(devicename, conf_device, new_sensors_list)

#-------------------------------------------------------------------------------------------
def create_device_tracker_and_sensor_entities(self, devicename, conf_device):
    """ Create a device and all of it's sensors in the ha entity registry

        Create device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
        associated with the device.
    """

    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
        return

    NewDeviceTrackers = []
    DeviceTracker     = None
    ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
    if devicename in Gb.DeviceTrackers_by_devicename:
        DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
    else:
        DeviceTracker = ic3_device_tracker.iCloud3_DeviceTracker(devicename, conf_device)

    if DeviceTracker is None:
        return

    ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
    Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
    NewDeviceTrackers.append(DeviceTracker)

    Gb.async_add_entities_device_tracker(NewDeviceTrackers, True)

    sensors_list = build_all_sensors_list()
    create_sensor_entity(devicename, conf_device, sensors_list)
    self.devices_added_deleted_flag = True

#-------------------------------------------------------------------------------------------
def remove_device_tracker_entity(self, devicename):
    """ Remove a specific device from the ha entity registry

        Remove device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
        associated with the device.

        devicename:
            devicename to be removed
    """
    # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
    ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
    if devicename not in Gb.DeviceTrackers_by_devicename:
        return

    try:
        for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
            entity_io.remove_entity(Sensor.entity_id)
    except:
        pass

    try:
        for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
            entity_io.remove_entity(Sensor.entity_id)
    except:
        pass

    try:
        DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        DeviceTracker.remove_device_tracker()
    except:
        pass

    ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)

    self.devices_added_deleted_flag = True

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
    for zone in remove_tfz_zones_list:
        for sensor, Sensor in device_tfz_sensors.copy().items():
            if (sensor.endswith(f"_{zone}")
                    and Sensor.entity_removed_flag is False):
                entity_io.remove_entity(Sensor.entity_id)

#-------------------------------------------------------------------------------------------
def create_track_fm_zone_sensor_entity(self, devicename, new_tfz_zones_list):
    """ Add tfz sensors for all zones that were just checked

        This must be done after the devices user_input parameters have been updated
    """
    if new_tfz_zones_list == []:
        return

    # Cycle thru each new zone and then cycle thru the track_from_zone sensors
    # Then add that sensor for the zones just checked
    sensors_list = []
    for sensor in Gb.conf_sensors[CONF_TRACK_FROM_ZONES]:
        sensors_list.append(sensor)

    NewZones = ic3_sensor.create_tracked_device_sensors(devicename, self.conf_device, sensors_list)

    if NewZones is not []:
        Gb.async_add_entities_sensor(NewZones, True)

#-------------------------------------------------------------------------------------------
def _update_track_from_zones_sensors(self, user_input):

    devicename = self.conf_device[CONF_IC3_DEVICENAME]
    self.conf_device[CONF_TRACK_FROM_ZONES] = user_input[CONF_TRACK_FROM_ZONES]

    # Remove the new track_fm_zone sensors just unchecked
    if 'remove_tfz_zones' in self.update_device_ha_sensor_entity:
        remove_tfz_zones_list = self.update_device_ha_sensor_entity['remove_tfz_zones']
        remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list)

    # Create the new track_fm_zone sensors just checked
    if 'new_tfz_zones' in self.update_device_ha_sensor_entity:
        new_tfz_zones_list = self.update_device_ha_sensor_entity['new_tfz_zones']
        create_track_fm_zone_sensor_entity(self, devicename, new_tfz_zones_list)

#-------------------------------------------------------------------------------------------
def sensor_form_identify_new_and_removed_sensors(self, user_input):
    """ Add newly checked/delete newly unchecked ha sensor entities """

    new_sensors_list    = []
    remove_sensors_list = []     # base device sensors
    if user_input[CONF_EXCLUDED_SENSORS] == []:
        user_input[CONF_EXCLUDED_SENSORS] = ['None']

    _log(f"{user_input=}")
    _log(f"{Gb.conf_sensors=}")
    for sensor_group, sensor_list in user_input.items():
        if (sensor_group not in Gb.conf_sensors
                or user_input[sensor_group] == Gb.conf_sensors[sensor_group]
                or sensor_group == CONF_EXCLUDED_SENSORS):
            if user_input[CONF_EXCLUDED_SENSORS] != Gb.conf_sensors[CONF_EXCLUDED_SENSORS]:
                list_add(self.config_parms_update_control, ['restart_ha', 'restart'])
            continue

        # Cycle thru the sensors now in the user_input sensor_group
        # Get list of sensors to be added
        for sensor in sensor_list:
            if sensor not in SENSOR_GROUPS['default']:
                new_sensors_list.append(sensor)
                _log(f"{sensor_group} {sensor} {new_sensors_list=}")
            elif sensor not in Gb.conf_sensors[sensor_group]:
                if sensor == 'last_zone':
                    if 'zone'       in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone')
                    if 'zone_name'  in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_name')
                    if 'zone_fname' in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_fname')
                else:
                    new_sensors_list.append(sensor)
                _log(f"{sensor_group} {sensor} {new_sensors_list=}")

        # Get list of sensors to be removed
        # _log(f"{sensor_group=} {Gb.conf_sensors[sensor_group]=}")
        for sensor in Gb.conf_sensors[sensor_group]:
            if sensor in SENSOR_GROUPS['default']:
                pass
            elif sensor not in sensor_list:
                if sensor == 'last_zone':
                    if 'zone'       in sensor_list: remove_sensors_list.append('last_zone')
                    if 'zone_name'  in sensor_list: remove_sensors_list.append('last_zone_name')
                    if 'zone_fname' in sensor_list: remove_sensors_list.append('last_zone_fname')
                else:
                    remove_sensors_list.append(sensor)
                _log(f"{sensor_group} {sensor} {remove_sensors_list=}")

    _log(f"236 {new_sensors_list=}")
    _log(f"237 {remove_sensors_list=}")
    return new_sensors_list, remove_sensors_list

#-------------------------------------------------------------------------------------------
def remove_sensor_entity(remove_sensors_list, select_devicename=None):
    """ Delete sensors from the ha entity registry and ic3 dictionaries

        remove_sensors_list:
                list of the sensors to be deleted
        selected_devicename:
                specified       - only delete this devicename's sensors
                not_specified   - delete the sensors in the remove_sensors_list from all devices
    """
    _log(f"{remove_sensors_list=}")
    if remove_sensors_list == []:
        return

    # Remove regular sensors
    device_tracking_mode = {k['ic3_devicename']: k['tracking_mode'] for k in Gb.conf_devices}
    for devicename, devicename_sensors in Gb.Sensors_by_devicename.items():
        _log(f"{devicename} {devicename_sensors=}")
        if (devicename not in device_tracking_mode
                or select_devicename and select_devicename != devicename):
            continue

        # Select normal/monitored sensors from the remove_sensors_list for this device
        if device_tracking_mode[devicename] == 'track':      #Device.is_tracked:
            sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is False]
        elif device_tracking_mode[devicename] == 'monitor':      #Device.is_monitored:
            sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is True]
        else:
            sensors_list = []
        _log(f"{devicename} {device_tracking_mode[devicename]} {sensors_list=}")

        # The sensor group is a group of sensors combined under one conf_sensor item
        # Build sensors to be removed from the the sensor or the sensor's group
        device_sensors_list = []
        for sensor in sensors_list:
            if sensor in SENSOR_GROUPS:
                device_sensors_list.extend(SENSOR_GROUPS[sensor])
            else:
                device_sensors_list.append(sensor)

        _log(f"{devicename} {device_sensors_list=}")
        Sensors_list = [v for k, v in devicename_sensors.items() if k in device_sensors_list]
        for Sensor in Sensors_list:
            if Sensor.entity_removed_flag is False:
                entity_io.remove_entity(Sensor.entity_id)

    # Remove track_fm_zone sensors
    device_track_from_zones = {k['ic3_devicename']: k['track_from_zones'] for k in Gb.conf_devices}
    for devicename, devicename_sensors in Gb.Sensors_by_devicename_from_zone.items():
        if (devicename not in device_track_from_zones
                or select_devicename and select_devicename != devicename):
            continue

        # Create tfz removal list, tfz_sensor --> sensor_zone
        tfz_sensors_list = [f"{k.replace('tfz_', '')}_{z}"
                                        for k in remove_sensors_list if k.startswith('tfz_')
                                        for z in device_track_from_zones[devicename]]

        Sensors_list = [v for k, v in devicename_sensors.items() if k in tfz_sensors_list]
        for Sensor in Sensors_list:
            if Sensor.entity_removed_flag is False:
                entity_io.remove_entity(Sensor.entity_id)

#-------------------------------------------------------------------------------------------
def create_sensor_entity(devicename, conf_device, new_sensors_list):
    """ Add sensors that were just checked """

    if new_sensors_list == []:
        return

    if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
        sensors_list = [v for v in new_sensors_list if v.startswith('md_') is False]
        NewSensors = ic3_sensor.create_tracked_device_sensors(devicename, conf_device, sensors_list)

    elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
        sensors_list = [v for v in new_sensors_list if v.startswith('md_') is True]
        NewSensors = ic3_sensor.create_monitored_device_sensors(devicename, conf_device, sensors_list)
    else:
        return

    Gb.async_add_entities_sensor(NewSensors, True)

#-------------------------------------------------------------------------------------------
def build_all_sensors_list():
    """ Get a list of all sensors from the ic3 config file  """

    sensors_list = []
    for sensor_group, sensor_list in Gb.conf_sensors.items():
        if sensor_group == CONF_EXCLUDED_SENSORS:
            continue

        for sensor in Gb.conf_sensors[sensor_group]:
            sensors_list.append(sensor)

    return sensors_list
