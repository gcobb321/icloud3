

from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOTIFY, EVLOG_NOTICE, NEXT_UPDATE, DEVICE_TYPES,
                                    CRLF_DOT, CRLF, NBSP6, NL3D, RED_X, YELLOW_ALERT, RARROW,
                                    CONF_IC3_DEVICENAME, CONF_MOBILE_APP_DEVICE)
from ..utils.utils          import (instr, is_empty, list_add, list_to_str, )
from ..utils                import  file_io
from ..utils.messaging      import (post_event, post_alert, post_error_msg, post_greenbar_msg,
                                    log_info_msg, log_exception, log_data, log_debug_msg,
                                    log_data_unfiltered, _evlog, _log, )
from ..utils.time_util      import (secs_to_time, secs_since, mins_since, secs_to_time, format_time_age,
                                    format_timer, time_now_secs)
from homeassistant.helpers  import  entity_registry as er, device_registry as dr

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
    Gb.mobapp_id_by_mobapp_dname      = {}
    Gb.mobapp_dname_by_mobapp_id      = {}
    Gb.device_info_by_mobapp_dname    = {}  # [mobapp_fname, raw_model, model, model_display_name]
                                            # ['Gary-iPhone (MobApp), iPhone15,2', 'iPhone', 'iPhone 14 Pro']
    Gb.last_updt_trig_by_mobapp_dname = {}
    Gb.mobile_app_notify_devicename   = []
    Gb.battery_level_sensors_by_mobapp_dname = {}
    Gb.battery_state_sensors_by_mobapp_dname = {}

    device_registry = dr.async_get(Gb.hass)

    try:
        entity_reg_data = file_io.read_json_file(Gb.entity_registry_file)
        mobile_app_entities = [x for x in entity_reg_data['data']['entities']
                                    if x['platform'] == 'mobile_app']
        dev_trkr_entities = [x for x in mobile_app_entities
                                if x['entity_id'].startswith('device_tracker')]

        for dev_trkr_entity in dev_trkr_entities:
            if 'device_id' not in dev_trkr_entity: continue

            mobapp_dname = dev_trkr_entity['entity_id'].replace('device_tracker.', '')
            dup_cnt = 1
            while mobapp_dname in Gb.mobapp_id_by_mobapp_dname:
                dup_cnt += 1
                mobapp_dname = f"{mobapp_dname} ({dup_cnt})"
            if dup_cnt > 1:
                alert_msg = (f"Duplicate Mobile App devices in Entity Registry for "
                            f"{dev_trkr_entity['entity_id']}")
                post_greenbar_msg(alert_msg)


            raw_model = 'Unknown'
            device_id = dev_trkr_entity['device_id']
            try:
                # Get raw_model from HA device_registry
                device_reg_data = device_registry.async_get(device_id)

                log_title = (f"{NL3D}MobApp device_registry entry - <{mobapp_dname}>)")
                log_data_unfiltered(log_title, str(device_reg_data)) #, log_rawdata_flag=True)

                raw_model = device_reg_data.model

            except Exception as err:
                log_exception(err)
                pass

            model_display_name = Gb.model_display_name_by_raw_model.get(raw_model, raw_model)
            Gb.mobapp_id_by_mobapp_dname[mobapp_dname] = dev_trkr_entity['device_id']
            Gb.mobapp_dname_by_mobapp_id[dev_trkr_entity['device_id']] = mobapp_dname

            _device_types = [_device_type for _device_type in DEVICE_TYPES
                                        if (instr(raw_model, _device_type)
                                                or instr(dev_trkr_entity['name'], _device_type)
                                                or instr(dev_trkr_entity['original_name'], _device_type))]
            device_type = _device_types[0] if _device_types else raw_model

            mobapp_fname = dev_trkr_entity['name'] or dev_trkr_entity['original_name']
            Gb.device_info_by_mobapp_dname[mobapp_dname] = \
                    [mobapp_fname, raw_model, device_type, model_display_name]    # Gary-iPhone, iPhone15,2; iPhone; iPhone 14 Pro

            log_title = (f"MobApp entity_registry entry - <{mobapp_dname}>)")
            log_data(log_title, dev_trkr_entity, log_rawdata_flag=True)

        last_updt_trigger_sensors = _extract_mobile_app_entities(mobile_app_entities, '_last_update_trigger')
        battery_level_sensors     = _extract_mobile_app_entities(mobile_app_entities, '_battery_level')
        battery_state_sensors     = _extract_mobile_app_entities(mobile_app_entities, '_battery_state')

        Gb.last_updt_trig_by_mobapp_dname        = _extract_sensor_entities(last_updt_trigger_sensors)
        Gb.battery_level_sensors_by_mobapp_dname = _extract_sensor_entities(battery_level_sensors)
        Gb.battery_state_sensors_by_mobapp_dname = _extract_sensor_entities(battery_state_sensors)

        Gb.startup_lists['Gb.mobapp_id_by_mobapp_dname'] = {k: v for k, v in Gb.mobapp_id_by_mobapp_dname.items()}
        Gb.startup_lists['Gb.mobapp_dname_by_mobapp_id'] = {k: v for k, v in Gb.mobapp_dname_by_mobapp_id.items()}
        Gb.startup_lists['Gb.device_info_by_mobapp_dname']           = Gb.device_info_by_mobapp_dname
        Gb.startup_lists['Gb.last_updt_trig_by_mobapp_dname']        = Gb.last_updt_trig_by_mobapp_dname
        Gb.startup_lists['Gb.battery_level_sensors_by_mobapp_dname'] = Gb.battery_level_sensors_by_mobapp_dname
        Gb.startup_lists['Gb.battery_state_sensors_by_mobapp_dname'] = Gb.battery_state_sensors_by_mobapp_dname

    except Exception as err:
        log_exception(err)

    return

#-----------------------------------------------------------------------------------------------------
def _extract_mobile_app_entities(mobile_app_entities, entity_name):
    '''
    Extract mobile_app entities fields (dictionary) for the specific type
    of entity (_last_update_trigger, _battery_state

    Return - A list of the mobile_app entities
    '''
    return [x   for x in mobile_app_entities
                if instr(x['unique_id'], entity_name)]

#-----------------------------------------------------------------------------------------------------
def _extract_sensor_entities(sensor_entities):
    '''
    Cycle through all of the sensor_entities (Ex. all last_updt_trigger_sensors) and
    select the ones with device_ids that are Mobile App devices.

    Example: {'gary_iphone_app': 'gary_iphone_app_last_update_trigger',
                'gary_ipad_2': 'gary_ipad_last_update_trigger'}}

    Return - A dictionary of the sensor entity for the specific mobapp device
    '''
    return  {Gb.mobapp_dname_by_mobapp_id[sensor['device_id']]: _entity_name_disabled_by(sensor)
                                for sensor in sensor_entities
                                if sensor['device_id'] in Gb.mobapp_dname_by_mobapp_id}

#-----------------------------------------------------------------------------------------------------
def _entity_name(entity_id):
    return entity_id.replace('sensor.', '')

def x_entity_name_disabled_by(sensor):
    disabled_prefix = ''    if sensor['disabled_by'] is None \
                            else f"{RED_X}DISABLED SENSOR{CRLF}{NBSP6}{NBSP6}{NBSP6}"

    return f"{disabled_prefix}{sensor['entity_id'].replace('sensor.', '')}"

def _entity_name_disabled_by(sensor):
    if sensor['disabled_by']:
        list_add(Gb.mobapp_fnames_disabled, sensor['device_id'])

    return sensor['entity_id'].replace('sensor.', '')

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
    mobapp_notify_service = Gb.hass.data['mobile_app']['notify']
    notify_targets = mobapp_notify_service.registered_targets
    mobapp_fname_targets = mobapp_notify_service.targets
    Gb.mobile_app_notify_devicenames = list(mobapp_fname_targets.keys())

    if is_empty(notify_targets):
        log_info_msg("Mobile App Notify Service has not been set up yet. iCloud3 will retry later.")

    return mobapp_fname_targets

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   GET MOBILE APP DEVICE FNAME
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def get_mobile_app_integration_device_info(ha_started_check=False):
    '''
    Check to see if the Mobile App Integration is installed.
        - If it is, set the Device.conf_mobapp_fname to the value in the Mobile App Integration
        - If it is not, a temporary name will be assigned for display in Stage 4 and this will
            be rechedked when ha has finished loading.

    {'d7f4264ab72046285ca92c0946f381e167a6ba13292eef17d4f60a4bf0bd654c':
    DeviceEntry(area_id=None, config_entries={'ad5c8f66b14fda011107827b383d4757'},
    configuration_url=None, connections=set(), disabled_by=None, entry_type=None,
    hw_version=None, id='93e3d6b65eb05072dcb590b46c02d920',
    identifiers={('mobile_app', '1A9EAFA3-2448-4F37-B069-3B3A1324EFC5')},
    manufacturer='Apple', model='iPad8,9', name_by_user='Gary-iPad-app',
    name='Gary-iPad', serial_number=None, suggested_area=None, sw_version='17.2',
    via_device_id=None, is_new=False),
    '''
    try:
        return
        #if Gb.conf_data_source_MOBAPP is False:
        #    return True

        if 'mobile_app' in Gb.hass.data:
            Gb.MobileApp_data  = Gb.hass.data['mobile_app']
            mobile_app_devices = Gb.MobileApp_data.get('devices', {})

            Gb.MobileApp_device_fnames      = []
            Gb.MobileApp_fnames_x_mobapp_id = {}
            Gb.MobileApp_fnames_disabled    = []
            for device_id, device_entry in mobile_app_devices.items():
                if device_entry.disabled_by is None:
                    list_add(Gb.MobileApp_device_fnames, device_entry.name_by_user)
                    list_add(Gb.MobileApp_device_fnames, device_entry.name)
                    Gb.MobileApp_fnames_x_mobapp_id[device_entry.id] = device_entry.name_by_user or device_entry.name
                    Gb.MobileApp_fnames_x_mobapp_id[device_entry.name]         = device_entry.id
                    Gb.MobileApp_fnames_x_mobapp_id[device_entry.name_by_user] = device_entry.id
                else:
                    list_add(Gb.MobileApp_fnames_disabled, device_entry.id)
                    list_add(Gb.MobileApp_fnames_disabled, device_entry.name)
                    list_add(Gb.MobileApp_fnames_disabled, device_entry.name_by_user)

            if Gb.MobileApp_device_fnames:
                ha_started_check = True
                log_debug_msg(  f"Mobile App Integration Started-True"
                                f"Devices-{list_to_str(Gb.MobileApp_device_fnames)}")

        Gb.startup_lists['Gb.MobileApp_device_fnames']   = Gb.MobileApp_device_fnames
        Gb.startup_lists['Gb.MobileApp_fnames_disabled'] = Gb.MobileApp_fnames_disabled
        Gb.startup_lists['Gb.MobileApp_fnames_x_mobapp_id'] = \
                            {k: v for k, v in Gb.MobileApp_fnames_x_mobapp_id.items()}

        if len(Gb.MobileApp_device_fnames) == Gb.conf_mobapp_device_cnt:
            return True

        if len(Gb.MobileApp_device_fnames) == 0:
            msg = f"Mobile App Integration Started-False > Temporary names assigned. "
            if ha_started_check is False:
                msg += f"Will recheck after HA is started"
            post_event(msg)
            return

        post_event(f"Mobile App Integration Started-True")

        # Cycle thru conf_devices and update the Device's mobapp_fname
        mobapp_fname_update_msg = ''

        for conf_device in Gb.conf_devices:
            conf_mobapp_dname = conf_device[CONF_MOBILE_APP_DEVICE]
            if conf_mobapp_dname == 'None':
                continue

            Device = Gb.Devices_by_devicename[conf_device[CONF_IC3_DEVICENAME]]
            mobapp_id = Gb.mobapp_id_by_mobapp_dname.get(conf_mobapp_dname)
            if mobapp_id:
                if Device.conf_mobapp_fname != '':
                    mobapp_fname_update_msg += (f"{CRLF_DOT}{Device.fname} > "
                                                f"{Device.conf_mobapp_fname}{RARROW}"
                                                f"{Gb.MobileApp_fnames_x_mobapp_id[mobapp_id]}")
                Device.conf_mobapp_fname = Gb.MobileApp_fnames_x_mobapp_id[mobapp_id]

        if mobapp_fname_update_msg:
            post_event(f"Mobile App Integration Name Assigned >{mobapp_fname_update_msg}")

    except Exception as err:
        log_exception(err)
        return False

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
    for mobapp_fname, mobapp_id in notify_devices.items():
        notify_devicename = slugify(mobapp_fname)
        Gb.mobapp_fnames_by_mobapp_id[mobapp_id] = mobapp_fname

        for devicename, Device in Gb.Devices_by_devicename.items():
            if (Device.mobapp_monitor_flag is False
                    or Gb.conf_data_source_MOBAPP is False):
                    # or Device.mobapp[NOTIFY] != ''):
                continue

            if instr(notify_devicename, devicename) or instr(devicename, notify_devicename):
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
            return

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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Using the mobapp tracking method or iCloud is disabled
#   Trigger the mobapp to send a location request transaction
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def request_location(Device, is_alive_check=False, force_request=False):
    '''
    Send location request to phone. Check to see if one has been sent but not responded to
    and, if true, set interval based on the retry count.
    '''

    if (Gb.used_data_source_MOBAPP is False
            or Device.mobapp_monitor_flag is False
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
            Device.display_info_msg(event_msg)
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
def request_sensor_update(Device):
    '''
    Request the mobapp to update it's sensors
    '''
    #if mins_since(Device.mobapp_request_sensor_update_secs) > 15:
    Device.mobapp_request_sensor_update_secs = time_now_secs()

    message = {"message": "command_update_sensors"}
    message_sent_ok = send_message_to_device(Device, message)

    return message_sent_ok
