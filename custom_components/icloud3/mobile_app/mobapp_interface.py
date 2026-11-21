

from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOTIFY, EVLOG_NOTICE, DEVICE_TYPES, DEVICE_TRACKER, )
from ..const_config         import (NEXT_UPDATE, CONF_IC3_DEVICENAME, CONF_MOBILE_APP_DEVICE, )
from ..const_char           import (CRLF_DOT, CRLF, NBSP6, NL3D, RED_X, GREEN_ALERT, RARROW, )
from ..utils.utils          import (instr, is_empty, list_add, list_to_str, )
from ..utils                import  file_io
from ..utils.messaging      import (post_event, post_alert, post_error_msg, post_greenbar_msg,
                                    log_info_msg, log_exception, log_debug_msg,
                                    _evlog, _log, )
from ..utils.rawdata_logging import (log_data, log_data_unfiltered, )
from ..utils.time_util      import (secs_to_time, secs_since, mins_since, secs_to_time, format_time_age,
                                    format_timer, time_now_secs)
from homeassistant.helpers  import  entity_registry as er, device_registry as dr
from homeassistant.const    import  CONF_WEBHOOK_ID

import json
# from homeassistant.components import ios
# from homeassistant.components.ios import notify
from homeassistant.util             import slugify
from homeassistant.components.mobile_app import notify as mobile_app_notify
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
)
PUSH_URL = "https://ios-push.home-assistant.io/push"
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Cycle through HA entity registry and get mobile_app device info that
#   can be monitored for the config_flow mobapp device selection list and
#   setting up the Device object
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def get_entity_registry_mobile_app_devices():
    '''
    Get the mobile_app device_tracker entities and the sensors that belong to them.

    HA links all of a mobile_app registration's entities through its config entry. The
    sensor unique_id is '<webhook_id>_<sensor_id>' (mobile_app/webhook.py _gen_unique_id).
    The sensors are found with an exact unique_id lookup so a sensor from another
    registration (old add/delete/add of the app) or another sensor with a similar
    name (watch_battery_level, volume_level_alarm) is never selected.
    '''
    Gb.mobapp_id_by_mobapp_dname      = {}
    Gb.mobapp_dname_by_mobapp_id      = {}
    Gb.mobapp_id_by_disabled_mobapp_dname = {}
    Gb.mobapp_dname_by_webhook_id     = {}
    Gb.device_info_by_mobapp_dname    = {}  # [mobapp_fname, raw_model, model, model_display_name]
                                            # ['Gary-iPhone (MobApp), iPhone15,2', 'iPhone', 'iPhone 14 Pro']
    Gb.last_updt_trig_by_mobapp_dname = {}
    Gb.mobile_app_notify_devicename   = []
    Gb.battery_level_sensors_by_mobapp_dname = {}
    Gb.battery_state_sensors_by_mobapp_dname = {}
    Gb.disabled_sensors_by_mobapp_dname      = {}
    Gb.mobapp_dnames_watchos                 = []

    device_registry = dr.async_get(Gb.hass)
    entity_registry = er.async_get(Gb.hass)

    try:
        dev_trkr_entities = [entity for entity in entity_registry.entities.values()
                                if (entity.platform == 'mobile_app'
                                        and entity.domain == 'device_tracker')]

        for dev_trkr_entity in dev_trkr_entities:
            if dev_trkr_entity.device_id is None: continue

            mobapp_dname = dev_trkr_entity.entity_id.replace('device_tracker.', '')
            device_id    = dev_trkr_entity.device_id

            # Disabled device_trackers are kept so the error can say it is disabled
            # instead of not found. They are not in the config_flow selection list.
            if dev_trkr_entity.disabled_by:
                Gb.mobapp_id_by_disabled_mobapp_dname[mobapp_dname] = device_id
                continue

            raw_model = 'Unknown'
            device_reg_data = None
            try:
                # Get raw_model from HA device_registry
                device_reg_data = device_registry.async_get(device_id)

                log_title = (f"{NL3D}MobApp device_registry entry - <{mobapp_dname}>)")
                log_data_unfiltered(log_title, str(device_reg_data)) #, is_log_level_rawdata=True)

                raw_model = device_reg_data.model

            except Exception as err:
                log_exception(err)
                pass

            model_display_name = Gb.model_display_name_by_raw_model.get(raw_model, raw_model)
            Gb.mobapp_id_by_mobapp_dname[mobapp_dname] = device_id
            Gb.mobapp_dname_by_mobapp_id[device_id] = mobapp_dname

            _device_types = [_device_type for _device_type in DEVICE_TYPES
                                        if (instr(raw_model, _device_type)
                                                or instr(dev_trkr_entity.name, _device_type)
                                                or instr(dev_trkr_entity.original_name, _device_type))]
            device_type = _device_types[0] if _device_types else raw_model

            # Use the name HA displays. A renamed device only changes the device's
            # name_by_user and the entity's friendly_name. The entity's original_name
            # keeps the name the app registered with (Lillian-iPhone-app Apple Watch).
            # The entity's name may be '' instead of None.
            dev_trkr_state = Gb.hass.states.get(dev_trkr_entity.entity_id)
            mobapp_fname = ((dev_trkr_state and dev_trkr_state.attributes.get('friendly_name'))
                                or (device_reg_data and device_reg_data.name_by_user)
                                or dev_trkr_entity.name
                                or dev_trkr_entity.original_name
                                or mobapp_dname)
            Gb.device_info_by_mobapp_dname[mobapp_dname] = \
                    [mobapp_fname, raw_model, device_type, model_display_name]    # Gary-iPhone, iPhone15,2; iPhone; iPhone 14 Pro

            log_title = (f"MobApp entity_registry entry - <{mobapp_dname}>)")
            log_data(log_title, dev_trkr_entity.as_partial_dict, is_log_level_rawdata=True)

            config_entry = Gb.hass.config_entries.async_get_entry(dev_trkr_entity.config_entry_id)
            if config_entry is None or CONF_WEBHOOK_ID not in config_entry.data:
                continue

            webhook_id = config_entry.data[CONF_WEBHOOK_ID]
            Gb.mobapp_dname_by_webhook_id[webhook_id] = mobapp_dname

            # The watchOS app does not have a last_update_trigger sensor or a notify service
            if (config_entry.data.get('os_name') == 'watchOS'
                    or instr(config_entry.data.get('app_id', ''), 'watchkitapp')):
                list_add(Gb.mobapp_dnames_watchos, mobapp_dname)

            # iOS-last_update_trigger, Android-last_update
            _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.last_updt_trig_by_mobapp_dname, ['last_update_trigger', 'last_update'])
            _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.battery_level_sensors_by_mobapp_dname, ['battery_level'])
            _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.battery_state_sensors_by_mobapp_dname, ['battery_state'])

        Gb.startup_lists['Gb.mobapp_id_by_mobapp_dname'] = {k: v for k, v in Gb.mobapp_id_by_mobapp_dname.items()}
        Gb.startup_lists['Gb.mobapp_dname_by_mobapp_id'] = {k: v for k, v in Gb.mobapp_dname_by_mobapp_id.items()}
        Gb.startup_lists['Gb.mobapp_id_by_disabled_mobapp_dname']    = Gb.mobapp_id_by_disabled_mobapp_dname
        Gb.startup_lists['Gb.device_info_by_mobapp_dname']           = Gb.device_info_by_mobapp_dname
        Gb.startup_lists['Gb.last_updt_trig_by_mobapp_dname']        = Gb.last_updt_trig_by_mobapp_dname
        Gb.startup_lists['Gb.battery_level_sensors_by_mobapp_dname'] = Gb.battery_level_sensors_by_mobapp_dname
        Gb.startup_lists['Gb.battery_state_sensors_by_mobapp_dname'] = Gb.battery_state_sensors_by_mobapp_dname
        Gb.startup_lists['Gb.disabled_sensors_by_mobapp_dname']      = Gb.disabled_sensors_by_mobapp_dname
        Gb.startup_lists['Gb.mobapp_dnames_watchos']                 = Gb.mobapp_dnames_watchos

    except Exception as err:
        log_exception(err)

    return

#-----------------------------------------------------------------------------------------------------
def _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id, sensors_by_mobapp_dname, sensor_ids):
    '''
    Find the mobapp device's sensor using its unique_id (<webhook_id>_<sensor_id>) and add
    it to the sensors_by_mobapp_dname dictionary. A disabled sensor is added to
    Gb.disabled_sensors_by_mobapp_dname[mobapp_dname][sensor_ids[0]] instead.

    Example: Gb.battery_level_sensors_by_mobapp_dname['gary_iphone_app'] = 'sensor.gary_iphone_app_battery_level'
    '''
    for sensor_id in sensor_ids:
        entity_id = entity_registry.async_get_entity_id('sensor', 'mobile_app',
                                                        f"{webhook_id}_{sensor_id}")
        if entity_id is None:
            continue

        if entity_registry.async_get(entity_id).disabled_by:
            Gb.disabled_sensors_by_mobapp_dname.setdefault(mobapp_dname, {})[sensor_ids[0]] = entity_id
            continue

        sensors_by_mobapp_dname[mobapp_dname] = entity_id
        return

#-----------------------------------------------------------------------------------------------------
def _get_mobile_app_notify_devices():
    '''
    Get the mobile_app_[devicename] notify services entries from ha that are used to
    send notifications to a device.

    notify_targets={
        'Lillian-iPhone-app': '7ada3fe77c0db7b47703d27452bd7cce324afe731ea9cdf76c7b11905528a4dd',
        'Gary-iPhone-app': 'fc79dc30d9d8da0f726228caf6c575fc96dae7255d526d3654efbb35465bdd6e',
        'Gary-iPad-app': '7f8496d4c94b958b7d091e5438353ac5795323b1b261815b4573f690f1b7b7ff'}

    '''
    # The mobile_app Integration sets up it's notify platform in a separate task that HA
    # does not wait for, so it may not be there yet when iCloud3 is starting
    mobapp_notify_service = Gb.hass.data.get('mobile_app', {}).get('notify')
    if mobapp_notify_service is None:
        log_info_msg("Mobile App Notify Service has not been set up yet. iCloud3 will retry later.")
        return {}

    notify_targets = mobapp_notify_service.registered_targets
    mobapp_fname_targets = mobapp_notify_service.targets
    Gb.mobile_app_notify_devicenames = list(mobapp_fname_targets.keys())

    if is_empty(notify_targets):
        log_info_msg("Mobile App Notify Service has not been set up yet. iCloud3 will retry later.")

    return mobapp_fname_targets

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   DEVICE NOTIFY SERVICE HANDLERS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def setup_notify_service_name_for_mobapp_devices(post_evlog_msg=False):
    '''
    Get the MobApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.

    Parameters:
        post_evlog_msg -
                Post an event msg indicating the notify device names were set up. This is done
                when they are set up when this is run after HA has started


    '''
    notify_devices = _get_mobile_app_notify_devices()

    setup_msg = ''

    # Cycle thru the ha notify names and match them up with a device. This function runs
    # while iC3 is starting and again when ha has started. HA may run iC3 before
    # 'notify.mobile_app' so running again when ha has started makes sure they are set up.
    #
    # The notify targets are {device_name: webhook_id} from the mobile_app config entry. HA
    # names the service 'mobile_app_<slugify(device_name)>' (notify/legacy.py). The webhook_id
    # is the same config entry as the device_tracker so they are matched on it, not by name.
    if Gb.conf_data_source_MOBAPP is False:
        return

    for mobapp_fname, webhook_id in notify_devices.items():
        mobapp_dname = Gb.mobapp_dname_by_webhook_id.get(webhook_id)
        if mobapp_dname is None:
            continue

        notify_devicename = slugify(mobapp_fname)
        mobapp_id = Gb.mobapp_id_by_mobapp_dname.get(mobapp_dname)
        if mobapp_id:
            Gb.mobapp_fnames_by_mobapp_id[mobapp_id] = mobapp_fname

        for devicename, Device in Gb.Devices_by_devicename.items():
            if (Device.is_mobapp_monitored is False
                    or Device.mobapp[DEVICE_TRACKER] != f"device_tracker.{mobapp_dname}"):
                continue

            Device.conf_mobapp_fname = mobapp_fname
            Device.mobapp[NOTIFY] = f"mobile_app_{notify_devicename}"
            setup_msg+=(f"{CRLF_DOT}{Device.devicename_fname}{RARROW}"
                        f"{mobapp_fname} ({notify_devicename})")
            break

    if setup_msg and post_evlog_msg:
        post_event(f"Delayed MobApp Notifications Setup Completed > {setup_msg}")

#--------------------------------------------------------------------
def send_message_to_device(Device, service_data):
    '''
    Send a message to the device. An example message is:
        service_data = {
            "title": "iCloud3/MobApp Zone Action Needed",
            "message": "The iCloud3 Stationary Zone may "\
                "not be loaded in the MobApp. Force close "\
                "the MobApp from the Mobile App Switcher. "\
                "Then restart the MobApp to reload the HA zones. "\
                f"Distance-{dist_fm_zone_m} m, "
                f"StatZoneTestDist-{zone_radius * 2} m",
            "data": {"subtitle": "Stationary Zone Exit "\
                "Trigger was not received"}}
    '''
    try:
        if Device.mobapp[NOTIFY] == '':
            return False

        if service_data.get('message') != "request_location_update":
            post_event(Device,
                        f"{EVLOG_NOTICE}Sending Message to Device > "
                        f"Message-{service_data.get('message')}")

        Gb.hass.services.call("notify", Device.mobapp[NOTIFY], service_data)

        return True

    except Exception as err:
        log_exception(err)
        event_msg =(f"iCloud3 Error > An error occurred sending a message to device "
                    f"{Device.mobapp[NOTIFY]} via the Notify service. "
                    f"{CRLF_DOT}Message-{str(service_data)}")
        if instr(err, "notify/none"):
            event_msg += (f"{CRLF_DOT}The devicename can not be found")
        else:
            event_msg += f"{CRLF_DOT}Error-{err}"
        post_error_msg(Device.devicename, event_msg)

    return False

#--------------------------------------------------------------------
def test_send_message_to_devices():
    '''
    Send a message to the device. An example message is
    '''
    # service_data = {
    #         "title": "iCloud3/MobApp Message Test",
    #         "message": "Push message text",
    #         "data": {"subtitle": "Stationary Zone Exit "\
    #             "Trigger was not received"}}

    message = {
        "title": "iCloud3/MobApp Message Test",
        "message": "Push message text",
        "data": {
            "subtitle": "Subtitle goes here",
            "subject": "Subject for long text"
        }
    }

    for Device in Gb.Devices:
        if Device.mobapp.get(NOTIFY, '') == '': continue

        message['data']['subtitle'] = f"Sent to-{Device}"
        sent_ok = send_message_to_device(Device, message)
        post_alert( f"TEST MOBAPP NOTIFY-{Device}, Sent-{sent_ok}, "
                    f"{CRLF_DOT}To-{Device.mobapp.get(NOTIFY)}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Using the mobapp tracking method or iCloud is disabled
#   Trigger the mobapp to send a location request transaction
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def request_location(Device, is_alive_check=False, force_request=False, user_request=False):
    '''
    Send location request to phone. Check to see if one has been sent but not responded to
    and, if true, set interval based on the retry count.

    user_request:
        True - Requested from the EvLog > Actions > Locate from Mobile App. The response
        is used even if the device has not moved (mobapp_data_handler). A tracking request
        is used that way only when the MobApp is the only location data source.
    '''

    if (Gb.used_data_source_MOBAPP is False
            or Device.is_mobapp_monitored is False
            or Device.mobapp[NOTIFY] == ''
            or Device.is_offline):
        return

    devicename = Device.devicename

    try:
        # Do not send a request if one has already been sent until it is older than the offline interval
        # mod-7/5/2022-add 1200 chk, add loc_data_secs > inzone_secs
        send_msg_interval_secs = max(Gb.offline_interval_secs, 1800)
        if force_request:
            pass

        elif (Device.mobapp_request_loc_last_secs > 0
                and secs_since(Device.mobapp_request_loc_last_secs) < send_msg_interval_secs):
            return

        elif Device.is_mobapp_data_good:

            return

        if is_alive_check:
            event_msg =(f"MobApp Alive Check > Location Requested, "
                        f"LastContact-{format_time_age(Device.mobapp_data_secs)}")

            if Device.mobapp_request_loc_last_secs > 0:
                event_msg +=  f", LastRequest-{format_time_age(Device.mobapp_request_loc_last_secs)}"
        else:
            event_msg =(f"MobApp Loc > Requested, "
                        f"LastLocated-{format_time_age(Device.mobapp_data_secs)}")
            if Device.old_loc_cnt > 2:
                event_msg += f", OldThreshold-{format_timer(Device.old_loc_threshold_secs)}"
        post_event(Device, event_msg)

        if Device.mobapp_request_loc_first_secs == 0:
            Device.mobapp_request_loc_first_secs = Gb.this_update_secs
        message = {"message": "request_location_update"}
        message_sent_ok = send_message_to_device(Device, message)

        #Gb.hass.async_create_task(
        #    Gb.hass.services.async_call('notify',  entity_id, service_data))

        if message_sent_ok:
            Device.mobapp_request_loc_last_secs = Gb.this_update_secs
            Device.mobapp_request_loc_sent_secs = Gb.this_update_secs
            Device.write_ha_sensor_state(NEXT_UPDATE, 'LOC RQSTD')

            if (user_request
                    or (is_alive_check is False
                        and Device.is_data_source_ICLOUD is False)):
                Device.mobapp_request_loc_pending_secs = time_now_secs()
        else:
            Device.mobapp_request_loc_last_secs = 0
            Device.mobapp_request_loc_sent_secs = 0
            post_event(Device, f"{EVLOG_NOTICE}{event_msg} > Failed to send message")

    except Exception as err:
        log_exception(err)
        error_msg = (f"iCloud3 Error > An error occurred sending a location request > "
                    f"Device-{Device.fname_devicename}, Error-{err}")
        post_error_msg(devicename, error_msg)

#-----------------------------------------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def request_sensor_update(Device):
#     '''
#     Request the mobapp to update it's sensors
#     '''
#     #if mins_since(Device.mobapp_request_sensor_update_secs) > 15:
#     Device.mobapp_request_sensor_update_secs = time_now_secs()

#     message = {"message": "command_update_sensors"}
#     message_sent_ok = send_message_to_device(Device, message)

#     return message_sent_ok
