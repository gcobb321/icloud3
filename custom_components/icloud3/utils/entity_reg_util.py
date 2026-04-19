from ..global_variables import GlobalVariables as Gb
from ..const            import (PLATFORMS, PLATFORM_DEVICE_TRACKER, PLATFORM_SENSOR,
                                DOMAIN, SENSOR, ICLOUD3,
                                CONF_DEVICES, CONF_TRACKING_MODE, INACTIVE,
                                BASE, CONF_EXCLUDED_SENSORS, )
from ..const_sensor     import (ICLOUD3_INTERNAL_SENSORS_ID, SENSOR_DEFINITION, )
from .utils             import (instr, is_empty, isnot_empty, dict_del,
                                list_add, list_del, list_to_str, set_to_list, )
from .messaging         import (log_info_msg, log_debug_msg, log_exception, log_debug_msg,
                                log_error_msg, log_data,
                                _evlog, _log, )
from .time_util         import (secs_to_time, time_now_secs, )

from ..startup          import config_file

from dataclasses                    import dataclass, asdict
from homeassistant.config_entries   import ConfigEntry
from homeassistant.core             import HomeAssistant, callback
from homeassistant.helpers          import entity_registry as er, device_registry as dr
# from homeassistant.helpers.event    import async_track_device_registry_updated_event


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    Entity State and Attributes functions
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
@callback
def async_handle_update_device_registry(event: dr.EventDeviceRegistryUpdatedData):
    '''
    Handle device registry updates:

    When a device is disabled on the integrations screen by the user:
        entity_registry:
        1.  All of the device's sensors are moved to the deleted_entity dict. This
            fires the sensor handler below.
        2.  The device_tracker entity dsabled_by is set to 'device' and moved to
            the deleted_sensors dict.

        device_registry:
        3.  The device_tracker disabled_by is set to 'user' and moved to the
            deleted_devices dict.

        iCloud3 configuration:
        1.  The device is set to 'Inactive'.
        2.  iCloud3 is restarted.
    '''

    try:
        action      = event.data['action']
        device_id   = event.data['device_id']
        device_data = get_device(device_id)

        if (device_data is None
                or device_data.primary_config_entry != Gb.config_entry_id):
            return

        # Being deleted by iCloud3 Config Flow, cancel listener handler
        if (Gb.OptionsFlowHandler and Gb.OptionsFlowHandler.is_deleting_device):
            return
        if Gb.was_icloud3_reloaded:
            return

        Device = Gb.Devices_by_ha_device_id.get(device_id)
        if Device is None:
            return

        devicename = Device.devicename

        log_debug_msg(  f'Device Registry Update ({device_id[:8]}) > Action-{action}, Device-{devicename}, '
                        f'Name-{device_data.name}, DisabledBy-{device_data.disabled_by}')

        if action == "update":
            # If disabled_by is now None, it was just enabled and HA will
            # schedule an icloud3 reload
            if (Gb.is_icloud3_startup_inprocess is False
                    and device_data.disabled_by is None):
                Gb.icloud3_reload_requested = True
                Gb.icloud3_reload_requested_secs = time_now_secs() + 30

            if device_data.disabled_by is not None:
                if Device.DeviceTracker is None:
                    remove_from_active_and_deleted_device_registry(device_id)
                    clear_device_gb_dicts(device_id)

        elif action == "remove":
            Device.pause_tracking()

            Gb.was_icloud3_restart_requested = True

    except Exception as err:
        log_exception(err)

#-------------------------------------------------------------------------------------------
@callback
def async_handle_update_entity_registry(event: er.EventEntityRegistryUpdatedData):
    '''
    Handle entity registry updates. This is called by HA after the sensor is deleted and
    the sensor.[sensor].after_removal_cleanup function has been done.

    When a sensor is disabled on the integrations screen by the user:
        1.  HA deletes the sensor and calls the sensor.on_removal function
        1.  entity_registry - The sensors.[entity_id].disabled is disabled_by is set to 'user'
            and moved to the deleted_devices dictionary.
        2.  entity_registry - The devices_tracker.[device_id].disabled_by is set to 'device'
            and moved to the deleted_sensors dictionary.
        3.  device_registry - The devices_tracker.[device_id].disabled_by is set to 'user'
            and moved to the deleted_devices dictionary.

    When a sensor is reenabled on the integrations screen by the user:
        1.  Remove it from the configuration excluded_sensors list.
        2.  HA will reload iCloud3 in 30-secs so the sensor will be recreated.

    '''

    try:
        action       = event.data['action']
        entity_id    = event.data['entity_id']
        entity_data  = get_entity(entity_id)

        if (entity_data is None
                or entity_data.config_entry_id != Gb.config_entry_id):
            return

        devicename_sensor = entity_id_base(entity_id)
        devicename, sensor_base = get_devicename_sensor_base(devicename_sensor)
        log_debug_msg(f'Sensor Entity Registry ({entity_id}) > Action-{action}')

        Sensor = Gb.Sensors_by_devicename_sensor.get(devicename_sensor)

        # Being deleted by iCloud3, ignore event
        if Gb.OptionsFlowHandler and Gb.OptionsFlowHandler.is_deleting_device:
            return

        scan_entity_reg_for_icloud3_items()

        if action == "update":
            # If disabled_by is now None, it was just enabled and HA will schedule a restart
            if entity_data.disabled_by is None:
                Gb.icloud3_reload_requested = True
                Gb.icloud3_reload_requested_secs = time_now_secs() + 30
                _remove_disabled_entity_from_excluded_sensor_list(entity_data)

            if entity_data.disabled_by is not None:
                device_id = entity_data.device_id

                # If deleting the device, it's Device.DeviceTracker variable
                # is set to None. If deleting only a sensor from a device and the
                #  device is still tracking other sensors, add this sensor to
                # the excluded list so u will not be created on the next restart.
                Device = Gb.Devices_by_devicename.get(devicename)
                if Device and Device.DeviceTracker is not None:
                    _add_disabled_entity_to_excluded_sensor_list(entity_data)

                remove_from_active_and_deleted_entity_registry(entity_id)
                clear_sensor_gb_dicts(entity_id)

        elif action == "remove":
            pass

    except Exception as err:
        log_exception(err)

#................................................................................
def _add_disabled_entity_to_excluded_sensor_list(entity_data):

    entity_id = entity_data.entity_id
    devicename_sensor = entity_id_base(entity_id)

    list_add(Gb.conf_sensors[CONF_EXCLUDED_SENSORS], devicename_sensor)
    excluded_list_changed = config_file.rebuild_excluded_sensors_fname_sensors_list()

    if excluded_list_changed:
        config_file.write_icloud3_configuration_file()

#................................................................................
def _remove_disabled_entity_from_excluded_sensor_list(entity_data):

    entity_id = entity_data.entity_id
    devicename_sensor = entity_id_base(entity_id)

    for excluded_item in Gb.conf_sensors[CONF_EXCLUDED_SENSORS].copy():
        if instr(excluded_item, devicename_sensor):
            list_del(Gb.conf_sensors[CONF_EXCLUDED_SENSORS], excluded_item)
            break

    # list_del(Gb.conf_device_sensors[CONF_EXCLUDED_SENSORS], excluded_item)

    config_file.write_icloud3_configuration_file()

#-------------------------------------------------------------------------------------------
def enable_disabled_device(device_id):
    '''
    Enabled a device that is disabled. This is called from device.py and
    device_tracker.py during startup
    '''
    if device_id is None:
        return False

    try:
        device_reg = dr.async_get(Gb.hass)
        device_data = device_reg.async_get(device_id)
        if device_data.disabled_by is not None:
            device_reg.async_update_device(device_id, disabled_by=None)
            return True

    except Exception as err:
        pass

    return False
#-------------------------------------------------------------------------------------------
def enable_disabled_entity(entity_id):
    '''
    Enabled a sensor that is disabled. This is called from sensor.py and
    right before the sensor is created during startup
    '''
    if entity_id is None:
        return False

    try:
        entity_reg  = er.async_get(Gb.hass)
        entity_data = entity_reg.async_get(entity_id)
        if entity_data.disabled_by is not None:
            entity_reg.async_update_entity(entity_id, disabled_by=None)
            return True

    except Exception as err:
        pass

    return False

#-------------------------------------------------------------------------------------------
def is_device_disabled(device_id):
    # Detect if device is disabled
    device_reg = dr.async_get(Gb.hass)
    device = device_reg.async_get(device_id)

    if device and device.disabled_by:
        # Device is disabled
        pass

#-------------------------------------------------------------------------------------------
def is_entity_disabled_by_device(entity_id):
# Detect when device is disabled by user

    # Check if an entity is disabled due to its device being disabled
    entity_reg   = er.async_get(Gb.hass)
    entity_data = entity_reg.async_get(entity_id)

    if entity_data and entity_data.disabled_by == er.EntityEntryDisabler.DEVICE:
        # Entity is disabled because its device is disabled
        pass

#-------------------------------------------------------------------------------------------
def async_delete_device_and_entities(device_id):
    # Purging Entities When Device is Deleted
    # Device has been deleted - clean up all associated entities
    entity_reg = er.async_get(Gb.hass)

    # Get all entities associated with this device
    entities = er.async_entries_for_device(entity_reg, device_id)

    # Completely remove each entity, do not add to entity deleted list
    for entity in entities:
        entity_reg.async_remove(entity.entity_id, force_remove=True)

    # Optionally also remove the device completely
    device_reg = dr.async_get(Gb.hass)
    device_reg.async_remove_device(device_id)



#-------------------------------------------------------------------------------------------
async def async_cleanup_orphaned_entities():
    """Clean up orphaned entities for this integration."""
    entity_reg = er.async_get(Gb.hass)
    device_reg = dr.async_get(Gb.hass)

    # Get all entities for your config entry
    entities = er.async_entries_for_config_entry(entity_reg, Gb.config_entry_id)

    for entity in entities:
        is_orphaned = False

        # Check if entity's device still exists
        if entity.device_id:
            device = device_reg.async_get(entity.device_id)
            if not device:
                is_orphaned = True

        # Check if entity's config entry still exists (should always exist in this context)
        if entity.config_entry_id != Gb.config_entry_id:
            is_orphaned = True

        # Remove orphaned entity
        if is_orphaned:
            entity_reg.async_remove(entity.entity_id, force_remove=True)




# Automatic Cleanup on Config Entry Removal
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
# async def async_unload_entry(hass: HomeAssistant, entry) -> bool:
    """Unload a config entry."""

    # Your normal unload logic...
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Clean up all entities and devices
        entity_reg = er.async_get(hass)
        device_reg = dr.async_get(hass)

        # Remove all entities for this config entry
        entities = er.async_entries_for_config_entry(entity_reg, Gb.config_entry_id)
        for entity in entities:
            entity_reg.async_remove(entity.entity_id, force_remove=True)

        # Remove all devices for this config entry
        devices = dr.async_entries_for_config_entry(device_reg, Gb.config_entry_id)
        for device in devices:
            device_reg.async_remove_device(device.id)

    return unload_ok

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ENTITY REGISTRY MAINTENANCE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def entity_id_base(entity_id):
    '''
    Get the sensor_name_base from the entity_id
        entity_id=sensor.gary_iphone_distance --> gary_iphone_distance

    This will generate an error if the entity_id is really the entity_key for the
    deleted entities dict
        entity_id=('sensor', 'icloud3', 'icloud3_lillian_ipad_badge')
    '''
    try:
        return entity_id.split('.')[1]
    except:
        return None

#................................................................................
def get_entity(entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        return entity_reg.async_get(entity_id)

    except:
        return None

#................................................................................
def get_device_entity_ids(device_id):
        entity_reg = er.async_get(Gb.hass)
        entity_ids = [entity_key for entity_key, entity_data in entity_reg.entities.items()
                                    if entity_data.device_id == device_id]

        return entity_ids

#................................................................................
def get_device_deleted_entity_keys(device_id):
        entity_reg = er.async_get(Gb.hass)
        entity_keys = [entity_key for entity_key, entity_data in entity_reg.deleted_entities.items()
                                    if entity_data.device_id == device_id]

        return entity_keys

#................................................................................
def remove_from_active_and_deleted_entity_registry(entity_id):
    '''
    Remove the entity registry active and deleted dict
    '''
    log_debug_msg(f'Sensor Entity Registry Update ({entity_id}) > Remove from Active & Deleted List')

    remove_sensor(entity_id)
    remove_deleted_entity(entity_id)


#................................................................................
def clear_sensor_gb_dicts(entity_id, force_clear=False):

    platform, devicename_sensor = entity_id.split('.')

    # Clear all the sensor dicts if it has been deleted
    if force_clear is True:
        pass
    elif devicename_sensor in Gb.Sensors_by_devicename_sensor:
        return

    devicename, sensor_base = get_devicename_sensor_base(devicename_sensor)

    dict_del(Gb.Sensors_by_devicename_sensor, devicename_sensor)
    dict_del(Gb.Sensors_by_devicename, devicename, sensor_base)
    dict_del(Gb.Sensors_by_devicename_from_zone, devicename, sensor_base)

    if devicename not in Gb.sensors_removed_by_devicename:
        Gb.sensors_removed_by_devicename[devicename] = []

    list_add(Gb.sensors_removed_by_devicename[devicename], sensor_base)

#................................................................................
def remove_sensor(entity_id):

    # See if the entity is a deleted entity that has no Sensor
    entity_reg = er.async_get(Gb.hass)
    if entity_id not in entity_reg.entities:
        return

    devicename_sensor = entity_id_base(entity_id)
    Sensor = Gb.Sensors_by_devicename_sensor.get(devicename_sensor)

    try:
        entity_reg.async_remove(entity_id)

    except Exception as err:
        log_exception(err)
        pass

    try:
        if Gb.hass.states.async_available(entity_id) is False:
            Gb.hass.async_add_executor_job(Gb.hass.states.remove, entity_id)

    except Exception as err:
        log_exception(err)
        pass

#................................................................................
def remove_deleted_entity(entity_key):

    if type(entity_key) is str:
        if instr(entity_key, '.'):
            platform, entity_id = entity_key.split('.')
        else:
            platform = PLATFORM_SENSOR
            entity_id = entity_key

        entity_key = (platform, DOMAIN, f"{DOMAIN}_{entity_id}")

    entity_reg = er.async_get(Gb.hass)
    if entity_key not in entity_reg.deleted_entities:
        return

    try:
        entity_reg.deleted_entities.pop(entity_key, None)
        entity_reg.async_schedule_save()

    except Exception as err:
        log_exception(err)
        pass
#....................................................................
def get_assigned_sensor_entity(unique_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        return entity_reg.async_get_entity_id(PLATFORM_SENSOR, DOMAIN, unique_id)

    except:
        return None

#................................................................................
def change_entity_id(from_entity_id, to_entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg.async_update_entity(from_entity_id, new_entity_id=to_entity_id)
    except KeyError:
        pass
    except Exception as err:
        log_exception(err)

#................................................................................
def update_entity(entity_id, **kwargs):
    try:
        if instr(entity_id,'.') is False:
            entity_id = f'sensor.{entity_id}'

        entity_reg = er.async_get(Gb.hass)
        entity_reg.async_update_entity(entity_id, **kwargs)

    except Exception as err:
        log_exception(err)
        return False

#................................................................................
def is_entity_available(entity_id):
    try:
        entity_reg = er.async_get(Gb.hass)
        entity_reg._entity_id_available(entity_id, None)
    except:
        return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEVICE REGISTRY MAINTENANCE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_device(device_id):
    try:
        device_reg = dr.async_get(Gb.hass)
        return device_reg.async_get(device_id)

    except:
        return None

#............................................................................................
def remove_device(device_id):
    try:
        device_reg = dr.async_get(Gb.hass)
        if device_id in device_reg.devices:
            device_reg.async_remove_device(device_id)

    except Exception as err:
        log_exception(err)

#................................................................................
def remove_deleted_device(device_id):
    try:
        device_reg = dr.async_get(Gb.hass)
        if device_id in device_reg.deleted_devices:
            deleted_entity = device_reg.deleted_devices.pop(device_id, None)
            device_reg.async_schedule_save()

    except Exception as err:
        log_exception(err)
        pass

#-------------------------------------------------------------------------------------------
def remove_from_active_and_deleted_device_registry(device_id):
    """ Remove entity/device from registry """

    log_debug_msg(f'Device Registry Update ({device_id[:8]}) > Remove from Active & Deleted List')

    remove_device(device_id)
    remove_deleted_device(device_id)

#-------------------------------------------------------------------------------------------
def clear_device_gb_dicts(device_id):
    update_ha_device_id_by_devicename()

    if device_id not in Gb.devicename_by_ha_device_id:
        return

    devicename = Gb.devicename_by_ha_device_id[device_id]

    dict_del(Gb.devicename_by_ha_device_id, device_id)
    dict_del(Gb.ha_device_id_by_devicename, devicename)

    if devicename in Gb.DeviceTrackers_by_devicename:
        DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        if DeviceTracker:
            DeviceTracker.remove_device_tracker()
            dict_del(Gb.DeviceTrackers_by_devicename, devicename)
            del DeviceTracker


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    UPDATE VARIOUS DEVICE AND ENTITY REGISTRY INTERNAL DICTIONARIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

#-------------------------------------------------------------------------------------------
def update_ha_device_id_by_devicename():
    '''
    Get the device_id by devicename from the device_registry
    '''
    extract_icloud3_device_registry_items(scan_active_items=True)
    Gb.ha_device_id_by_devicename = \
        extract_item_from_device_reg_items('active', 'device_id', PLATFORM_DEVICE_TRACKER)

#-------------------------------------------------------------------
def extract_item_from_device_reg_items(status, data_item, platform):
    '''
    Cycle through the Gb.entity_reg_items_by_status[status] dictionary and
    build a data_item_by_devicename dictionary for the specifiec data_item
    for each devicename.

    status: active, disabled, etc
    data_item: field to extract ()'device_id', 'entity_id', etc)
    platform: device_tracker, sensor
    '''
    ic3_entity_items_dict = Gb.entity_reg_items_by_status

    if status not in ic3_entity_items_dict:
        return {}

    return {devicename: sensor_data[data_item]
                        for devicename, device_sensors in ic3_entity_items_dict[status].items()
                            for sensor, sensor_data in device_sensors.items()
                            if sensor_data['platform'] == platform}

#-------------------------------------------------------------------
def device_sensors(devicename):
    '''
    Cycle the non-deleted statuses and get a list of all sensors belonging
    to a devicename.
    '''
    if devicename not in Gb.ha_device_id_by_devicename:
        return []

    entity_reg_items = Gb.entity_reg_items_by_status

    device_id = Gb.ha_device_id_by_devicename[devicename]
    device_sensors = [reg_data['entity_id']
                            for status, devicename_sensors in entity_reg_items.items()
                            if status.startswith('delete') is False
                            for devicename, device_sensors in devicename_sensors.items()
                            for sensor, reg_data in device_sensors.items()
                            if reg_data['device_id'] == device_id]

    return device_sensors

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#    EXTRACT ALL ICLOUD3 ENTITIES (SENSOR & DEVICE_TRACKER) FROM THE ENTITY REGISTRY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
ENTITY_STATUS_TYPES = [
        'active',
        'inactive',
        'other',
        'disabled',
        'orphaned',
        'suffix_error',
        'deleted_devices',
        'deleted_sensors']
DELETED_ENTITY_STATUS_TYPES = [
        'deleted_devices',
        'deleted_sensors']
ACTIVE_ENTITY_STATUS_TYPES = [status    for status in ENTITY_STATUS_TYPES
                                        if status not in DELETED_ENTITY_STATUS_TYPES]

def scan_entity_reg_for_icloud3_items(log_results=False):
    '''
    Get all iCloud3 sensors and device_trackers in the entity_registry. This includes:
        - orphaned: The 'config_entry_id' value is different than the loaded iCloud3 integration
        - disabled: The 'disabled_by' field is set
        - id_error: Entities where the 'entity_id' ends with a '_2' or '_#' suffix
        - deleted: Items from the'deleted_entities' dictionary

    Set Gb.entity_reg_items_by_status[status][devicename][sensor_base] = entity_item dictionary

    core.entity_registry
    Normal entity (device_tracker.gary_iphone):
    {"aliases":[],"area_id":null,"categories":{},"capabilities":null,"config_entry_id":"01JVRX6TFZRYRRMAHHE8MPYKB3",
    "config_subentry_id":null,"created_at":"2025-01-09T19:47:38.570717+00:00","device_class":null,
    "device_id":"801538ed695d4a4c3c8396c00099a519","disabled_by":null,"entity_category":"diagnostic",
    "entity_id":"device_tracker.gary_iphone","hidden_by":null,"icon":null,"id":"3ee724d40e73e18a5c4fd7ab57ecdf02",
    "has_entity_name":false,"labels":[],"modified_at":"2026-01-11T19:41:13.174426+00:00","name":null,
    "options":{"cloud.google_assistant":{"should_expose":false},"cloud.alexa":{"should_expose":false}},"original_device_class":null,"original_icon":"mdi:account","original_name":"Gary","platform":"icloud3",
    "suggested_object_id":"gary_iphone","supported_features":0,"translation_key":null,"unique_id":"icloud3_gary_iphone",
    "previous_unique_id":null,"unit_of_measurement":null},

    ACTIVE ENTITY, key = entity_id = sensor.gary_iphone_battery:
    {"aliases":[],"area_id":null,"categories":{},"capabilities":null,
    "config_entry_id":"01JVRX6TFZRYRRMAHHE8MPYKB3","config_subentry_id":null,
    "created_at":"2025-01-09T19:47:39.452471+00:00","device_class":null,
    "device_id":"801538ed695d4a4c3c8396c00099a519","disabled_by":null,"entity_category":null,
    "entity_id":"sensor.gary_iphone_battery","hidden_by":null,"icon":null,
    "id":"c9103dfe61ab6b55f22a085fa84343e3","has_entity_name":false,"labels":[],
    "modified_at":"2026-01-11T19:41:36.036095+00:00","name":null,
    "options":{"cloud.google_assistant":{"should_expose":false},
    "cloud.alexa":{"should_expose":false}},
    "original_device_class":null,"original_icon":null,"original_name":"Gary Battery",
    "platform":"icloud3","suggested_object_id":"gary_iphone_battery","supported_features":0,
    "translation_key":null,"unique_id":"icloud3_gary_iphone_battery",
    "previous_unique_id":null,"unit_of_measurement":null},

    DELETED ENTITY, key=(platform, domain, unique_id) = ('sensor', 'icloud3', 'icloud3_gary_airpods_zone_fname')
    {"aliases":[],"area_id":null,"categories":{},"config_entry_id":"01JVRX6TFZRYRRMAHHE8MPYKB3",
    "config_subentry_id":null,"created_at":"2025-09-19T17:22:21.949710+00:00",
    "device_class":null,"disabled_by":null,"disabled_by_undefined":false,
    "entity_id":"sensor.lillian_airpods_vertical_accuracy","hidden_by":null,
    "hidden_by_undefined":false,"icon":null,"id":"ea9c11e6eeaf2def59f11a49cba6093c",
    "labels":[],"modified_at":"2026-01-15T22:52:11.953850+00:00","name":null,
    "options":{"cloud.google_assistant":{"should_expose":false},
    "cloud.alexa":{"should_expose":false}},"options_undefined":false,"invalid_ic3_timestamp":null,
    "platform":"icloud3","unique_id":"icloud3_lillian_airpods_vertical_accuracy"},
    '''

    Gb.entity_reg_items_by_status = {}
    extract_icloud3_active_registry_items()
    extract_icloud3_deleted_registry_items()

    combine_device_tracker_deleted_device_and_sensor_items()
    sort_invalid_ic3_entities()

    if log_results:
        log_icloud3_registry_items(show_deleted=True)
        # log_icloud3_registry_items(show_details=True, show_deleted=True)

#-------------------------------------------------------------------
def extract_icloud3_active_registry_items(log_results=False):
    for status in ACTIVE_ENTITY_STATUS_TYPES:
        if status in Gb.entity_reg_items_by_status:
            Gb.entity_reg_items_by_status[status] = {}

    extract_icloud3_device_registry_items(scan_active_items=True)
    extract_icloud3_entity_registry_items(scan_active_items=True)

    if log_results:
        log_icloud3_registry_items(show_deleted=True)

#-------------------------------------------------------------------
def extract_icloud3_deleted_registry_items():
    for status in DELETED_ENTITY_STATUS_TYPES:
        if status in Gb.entity_reg_items_by_status:
            Gb.entity_reg_items_by_status[status] = {}
    extract_icloud3_device_registry_items(scan_active_items=False)
    extract_icloud3_entity_registry_items(scan_active_items=False)

#-------------------------------------------------------------------
def combine_device_tracker_deleted_device_and_sensor_items():
    '''
    Cycle thru the deleted_sensors devices looking for device_tracker items (the sensor name starts
    with '*', i.e., *gary_iphone). Then see if there is also a deleted_device for the same device (the
    sensor name starts with '#', i.e., #gary_iphone). If the device is in both the deleted_sensors and
    deleted_devices dictionaries, change the deleted_sensor to a deleted_device so it shows up in the
    correct status category.

    set ['deleted_sensors'][devicename][*gary_iphone] --> ['deleted_devices'][devicename][#gary_iphone]
    del ['deleted_sensors'][devicename][*gary_iphone]
    '''
    ic3_entity_items_dict = Gb.entity_reg_items_by_status
    if 'deleted_devices' not in  ic3_entity_items_dict:
        return

    for devicename, device_sensors in ic3_entity_items_dict['deleted_sensors'].copy().items():
        if devicename in ic3_entity_items_dict['deleted_devices']:
            device_sensors = ic3_entity_items_dict['deleted_sensors'].pop(devicename)
            ic3_entity_items_dict['deleted_devices'][devicename].update(device_sensors)

#--------------------------------------------------------------------
def sort_invalid_ic3_entities():
    ic3_entity_items_dict = {}
    for status, devicename_sensors in Gb.entity_reg_items_by_status.items():
        ic3_entity_items_dict[status] = {}
        sorted_devicename_sensors = dict(sorted(devicename_sensors.items()))
        for devicename, device_sensors in sorted_devicename_sensors.items():
            ic3_entity_items_dict[status][devicename] = {}
            sorted_device_sensors = dict(sorted(device_sensors.items()))
            ic3_entity_items_dict[status][devicename] = sorted_device_sensors

    Gb.entity_reg_items_by_status = ic3_entity_items_dict

#-------------------------------------------------------------------
#   SCAN CORE.ENTITY_REGISTRY
#--------------------------------------------------------------------
def extract_icloud3_entity_registry_items(scan_active_items):
    '''
    Cycle thru the entity registry, extract the platform=icloud3 entities.
    Determine if it is valid and, if not, extract the devicename and error_type
    and build the Gb.entity_reg_items_by_status item.

    Determine if we are cycling tury the active or deleted entity dictionary by
    checking to see if the 'original_name' field exists.
    '''

    ic3_entity_items_dict = Gb.entity_reg_items_by_status

    entity_reg = er.async_get(Gb.hass)
    if scan_active_items:
        entities = entity_reg.entities
    else:
        entities = entity_reg.deleted_entities

    # entity_key is the entity_id for active_entities and (platform, domain, unpque_id)
    # for deleted_entities
    for entity_key, entity_data in entities.items():
        if _is_icloud3_entity_item(entity_data) is False:
            continue

        RegData = _set_entity_reg_data(entity_key, entity_data)
        status  = _get_entity_status(scan_active_items, RegData)
        RegData.status = status

        devicename     = RegData.devicename

        # The device_tracker entity in the sensor entity_registry is managed by the device_registry
        # module but will be provided for information. Get it's device_tracker devicename instead
        # of the one with the sensor data in case it has a _2 suffix.
        if RegData.platform == PLATFORM_DEVICE_TRACKER:
            RegData.sensor_base = f'.er:{RegData.sensor_base}'

        if status not in ic3_entity_items_dict:
            ic3_entity_items_dict[status] = {}
        if devicename not in ic3_entity_items_dict[status]:
            ic3_entity_items_dict[status][devicename] = {}

        ic3_entity_items_dict[status][devicename][RegData.sensor_base] = asdict(RegData)

    return

#--------------------------------------------------------------------
def _is_icloud3_entity_item(entity_data):

    return (entity_data.platform == DOMAIN
            and entity_data.entity_id not in ICLOUD3_INTERNAL_SENSORS_ID)

#--------------------------------------------------------------------
def _get_entity_status(scan_active_items, RegData):

    if ('disabled' in Gb.entity_reg_items_by_status
            and RegData.devicename  in Gb.entity_reg_items_by_status['disabled']
            and RegData.sensor_base in Gb.entity_reg_items_by_status['disabled'][RegData.devicename]):
        return 'disabled'
    if RegData.disabled_by is not None:
        return 'disabled'
    if scan_active_items is False:
        return  'deleted_sensors'
    if RegData.config_entry_id != Gb.config_entry_id:
        return 'orphaned'
    if (RegData.entity_id[-2:-1] == '_'
            and RegData.entity_id.startswith(PLATFORM_SENSOR)):
        return 'suffix_error'

    if RegData.devicename in Gb.inactive_fname_by_devicename:
        return 'inactive'

    if (RegData.device_id in Gb.devicename_by_ha_device_id
            or RegData.sensor_base in Gb.Sensors_by_devicename.get(RegData.devicename, {})
            or RegData.devicename in Gb.DeviceTrackers_by_devicename):
        return 'active'

    return 'other'

#--------------------------------------------------------------------
def _set_entity_reg_data(entity_key, entity_data):

    platform, sensor_name   = entity_data.entity_id.split('.')
    devicename, sensor_base = get_devicename_sensor_base(sensor_name)

    # device_id is not specified for a deleted entity
    try:
        device_id = entity_data.device_id
    except:
        device_id = None

    data_item = {}
    data_item['entity_id']       = entity_data.entity_id       # sensor.lillian_ipad_badge
    data_item['devicename']      = devicename                  # lillian_ipad
    data_item['sensor_name']     = sensor_name                 # lillian_ipad_badge
    data_item['sensor_base']     = sensor_base                 # badge
    data_item['unique_id']       = entity_data.unique_id       # icloud_lillian_ipad_badge
    data_item['device_id']       = device_id                   # cf5b6825965dc8c6f643c...
    data_item['entity_key']      = entity_key
    data_item['config_entry_id'] = entity_data.config_entry_id # 01JVRX6TFZRYRRMAHHE8MPYKB3
    data_item['disabled_by']     = entity_data.disabled_by     # None, user
    data_item['status']          = None                        # active, disabled, deleted_device, ...
    data_item['domain']          = entity_data.platform        # icloud3
    data_item['platform']        = platform                    # device_tracker, sensor

    RegData = iCloud3RegistryData(**data_item)

    return RegData

#--------------------------------------------------------------------
def get_devicename_sensor_base(devicename_sensor_name):

    devicename = extract_devicename_from_entity_id(devicename_sensor_name)

    if devicename == devicename_sensor_name:
        return devicename, devicename

    return devicename, devicename_sensor_name.replace(f'{devicename}_', '')

#--------------------------------------------------------------------
def extract_devicename_from_entity_id(devicename_sensor_name):
    '''
    Cycle through the Sensor Definition table and find the sensor definition name in the
    sensor_name string. The devicename will preceed the sensor def name.

    Return:
        - devicename
    '''
    small_posx = 999

    # Get the smallest position of the sensor name from the definition table in the sensor name
    # being searched to handle names like 'name' and 'zone_name'
    for sensor_def_name in SENSOR_DEFINITION.keys():
        posx = devicename_sensor_name.find(f'_{sensor_def_name}')
        if posx > 0 and posx < small_posx:
            small_posx = posx

    if small_posx == 999:
        return devicename_sensor_name

    return devicename_sensor_name[:small_posx]

#--------------------------------------------------------------------
#   SCAN CORE.DEVICE_REGISTRY
#--------------------------------------------------------------------
def extract_icloud3_device_registry_items(scan_active_items):
    '''
    Cycle thru the entity registry, extract the platform=icloud3 entities.
    Determine if it is valid and, if not, extract the devicename and error_type
    and build the Gb.entity_reg_items_by_status item.

    Determine if we are cycling tury the active or deleted entity dictionary by
    checking to see if the 'original_name' field exists.

    core.device_registry
    Normal device (gary_iphone):
    {"area_id":null,"config_entries":["01JVRX6TFZRYRRMAHHE8MPYKB3"],
    "config_entries_subentries":{"01JVRX6TFZRYRRMAHHE8MPYKB3":[null]},"configuration_url":null,
    "connections":[],"created_at":"2024-11-05T22:07:55.366545+00:00","disabled_by":null,
    "entry_type":null,"hw_version":null,"id":"801538ed695d4a4c3c8396c00099a519",
    "identifiers":[["icloud3","gary_iphone"]],"labels":[],"manufacturer":"Apple",
    "model":"iPhone17,2","model_id":null,"modified_at":"2026-01-26T08:02:15.019773+00:00",
    "name_by_user":"","name":"Gary (gary_iphone)",
    "primary_config_entry":"01JVRX6TFZRYRRMAHHE8MPYKB3","serial_number":null,
    "sw_version":null,"via_device_id":null},

    Deleted device (gary_ipad_mini):
    {"area_id":null,"config_entries":["01JVRX6TFZRYRRMAHHE8MPYKB3"],
    "config_entries_subentries":{"01JVRX6TFZRYRRMAHHE8MPYKB3":[null]},"connections":[],
    "created_at":"2025-08-02T14:11:40.004111+00:00","disabled_by":null,
    "disabled_by_undefined":false,"identifiers":[["icloud3","gary_ipad_mini"]],
    "id":"70623119582105336f4d529e47bf0c95","labels":[],
    "modified_at":"2025-08-16T20:58:35.029526+00:00","name_by_user":null,
    "orphaned_timestamp":null},
    '''
    try:
        ic3_entity_items_dict = Gb.entity_reg_items_by_status

        device_reg = dr.async_get(Gb.hass)
        if scan_active_items:
            devices = device_reg.devices
        else:
            devices = device_reg.deleted_devices

        for device_id, device_data in list(devices.items()):
            if _is_icloud3_device_recd(device_data) is False:
                continue

            RegData = _set_device_reg_data(device_data)
            status  = _get_device_status(scan_active_items, RegData)
            RegData.status = status

            sensor_base_er = f'.er:{RegData.devicename}'  # Sensor name for device_tracker in entiry reg
            sensor_base_dr = f'.dr:{RegData.devicename}'  # Sensor name for device_tracker in device reg

            if status not in ic3_entity_items_dict:
                ic3_entity_items_dict[status] = {}
            if RegData.devicename not in ic3_entity_items_dict[status]:
                ic3_entity_items_dict[status][RegData.devicename] = {}

            ic3_entity_items_dict[status][RegData.devicename][sensor_base_dr] = asdict(RegData)

    except Exception as err:
        log_exception(err)

    return

#--------------------------------------------------------------------
def _set_device_reg_data(device_data):

    domain, devicename = _get_domain_devicename(device_data)

    data_item = {}
    data_item['entity_id']       = f'{PLATFORM_DEVICE_TRACKER}.{devicename}'
    data_item['devicename']      = devicename
    data_item['sensor_name']     = f'{PLATFORM_DEVICE_TRACKER}_{devicename}'
    data_item['sensor_base']     = devicename
    data_item['unique_id']       = None
    data_item['device_id']       = device_data.id
    data_item['entity_key']      = None
    data_item['config_entry_id'] = set_item(device_data.config_entries)
    data_item['disabled_by']     = device_data.disabled_by
    data_item['status']          = None
    data_item['domain']          = domain
    data_item['platform']        = PLATFORM_DEVICE_TRACKER

    RegData = iCloud3RegistryData(**data_item)

    return RegData

#--------------------------------------------------------------------
def _get_device_status(scan_active_items, RegData):

    if RegData.disabled_by is not None:
        return 'disabled'
    if scan_active_items is False:
        return  'deleted_devices'
    if RegData.config_entry_id != Gb.config_entry_id:
        return 'orphaned'
    if RegData.devicename[-2:-1] == '_':
        return 'suffix_error'
    if RegData.devicename in Gb.inactive_fname_by_devicename:
        return 'inactive'
    if RegData.devicename in Gb.DeviceTrackers_by_devicename:
        return 'active'

    return 'other'

#--------------------------------------------------------------------
def _is_icloud3_device_recd(device_data):
    # "identifiers":[["icloud3","gary_iphone"]]
    domain, devicename = _get_domain_devicename(device_data)

    if domain != DOMAIN or devicename == DOMAIN:
        return False

    return True

#--------------------------------------------------------------------
def _get_domain_devicename(device_data):
    '''
    The iCloud3 identifiers are ['icloud3', devicename] when the device entity was created. HA stores them
    internally as a set so we have to do a little extra work to get them.

    "identifiers":{("icloud3","gary_iphone")}
    '''
    try:
        identifier = set_item(device_data.identifiers)
        if is_empty(identifier):
            return None, None

        domain, devicename = identifier

        return domain, devicename

    except Exception as err:
        pass

    return None, None

def set_item(set_value):

    set_list = set_to_list(set_value)
    if isnot_empty(set_list):
        return set_to_list(set_value)[0]

    return []

#--------------------------------------------------------------------
#   LOG THE DEVICE/ENTITY REGISTRY ITEMS TO THE ICLOUD3.LOG FILE
#--------------------------------------------------------------------
def log_icloud3_registry_items(show_details=False, show_deleted=False, entity_reg_items=None):
    '''
    Log the entity_reg_items_by_status items to the icloud3,log file
    '''

    log_msg = f'\nICLOUD3 DEVICE & ENTITY REGISTRY INFO'

    for status in ENTITY_STATUS_TYPES:
        if (status not in Gb.entity_reg_items_by_status
                or is_empty(Gb.entity_reg_items_by_status[status])):
            continue
        if show_deleted is False and status not in ACTIVE_ENTITY_STATUS_TYPES:
            continue

        if show_details is False:
            log_msg += (f'\n{status.upper()}')

        devicename_sensors = Gb.entity_reg_items_by_status[status]
        for devicename, device_sensors in devicename_sensors.items():
            if show_details is False:
                sensors = [sensor for sensor in device_sensors.keys()]
                device_msg = f'\n  - {devicename} ({list_to_str(sensors)})'

            else:
                device_msg = (f'\n{status.upper()} ({devicename})')
                for sensor, reg_data in device_sensors.items():
                    device_msg += (f'\n  - {sensor} {reg_data}')

            log_msg += device_msg

    log_info_msg(log_msg)

#--------------------------------------------------------------------
#   DATACLASS TO HOLE THE DEVICE/ENTITY REGISTRY ITEMS
#--------------------------------------------------------------------
@dataclass
class iCloud3RegistryData:

    entity_id:        str       # sensor.lillian_ipad_badge
    devicename:       str       # lillian_ipad
    sensor_name:      str       # lillian_ipad_badge
    sensor_base:      str       # badge
    unique_id:        str       # icloud_lillian_ipad_badge
    device_id:        str       # cf5b6825965dc8c6f643c...
    entity_key:       str       # entity_id, device_id, [domain, platform, unique_id]
    config_entry_id:  str       # 01JVRX6TFZRYRRMAHHE8MPYKB3
    disabled_by:      str       # None, user
    status:           str       # active, disabled, deleted_device, ...
    domain:           str       # icloud3
    platform:         str       # device_tracker, sensor
