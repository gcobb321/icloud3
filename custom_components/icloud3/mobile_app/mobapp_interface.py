

from ..global_variables     import GlobalVariables as Gb
from ..const                import (NOTIFY, EVLOG_NOTICE, DEVICE_TYPES, DEVICE_TRACKER, )
from ..const_config         import (NEXT_UPDATE, CONF_IC3_DEVICENAME, CONF_MOBILE_APP_DEVICE, )
from ..const_char           import (CRLF_DOT, CRLF, NBSP6, NL3D, NL3_DATA, RED_X, GREEN_ALERT, RARROW, )
from ..utils.utils          import (instr, is_empty, list_add, list_to_str, )
from ..utils                import  file_io
from ..utils                import  entity_reg_util as er_util
from ..utils.messaging      import (post_event, post_alert, post_error_msg, post_greenbar_msg,
                                    log_info_msg, log_exception, log_debug_msg,
                                    _evlog, _log, )
from ..utils.rawdata_logging import (shrink_item, )
from ..utils.time_util      import (secs_to_time, secs_since, mins_since, secs_to_time, format_time_age,
                                    format_timer, time_now_secs)
from homeassistant.helpers  import  entity_registry as er, device_registry as dr
from homeassistant.const    import  CONF_WEBHOOK_ID

import json
# from homeassistant.components import ios
# from homeassistant.components.ios import notify
from homeassistant.util             import slugify
from homeassistant.util             import dt as dt_util
from homeassistant.components.mobile_app import notify as mobile_app_notify
from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    ATTR_TITLE_DEFAULT,
)
PUSH_URL = "https://ios-push.home-assistant.io/push"

#--------------------------------------------------------------------
def _device_reg_log_fields(device_reg_data):
    '''
    Return the HA DeviceEntry fields iCloud3 uses as a dict for logging. The
    created_at/modified_at datetimes are converted to the local date/time.
    '''
    if device_reg_data is None:
        return None

    def _local_datetime(_datetime):
        try:
            return dt_util.as_local(_datetime).strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            return str(_datetime)

    # Handles older HA versions with config_entries without the deprecation warning
    return {'id':               shrink_item(device_reg_data.id),
            'config_entry_id':  shrink_item(er_util.device_reg_config_entry_id(device_reg_data)),
            'identifiers':      [(domain, shrink_item(identifier))
                                    for domain, identifier in device_reg_data.identifiers],
            'name':             device_reg_data.name,
            'name_by_user':     device_reg_data.name_by_user,
            'manufacturer':     device_reg_data.manufacturer,
            'model':            device_reg_data.model,
            'hw_version':       device_reg_data.hw_version,
            'sw_version':       device_reg_data.sw_version,
            'disabled_by':      (str(device_reg_data.disabled_by)
                                    if device_reg_data.disabled_by else None),
            'created_at':       _local_datetime(device_reg_data.created_at),
            'modified_at':      _local_datetime(device_reg_data.modified_at),
            }

#--------------------------------------------------------------------
# The ids and webhook_ids are shortened with rawdata_logging.shrink_item ('abcdef……uvwxyz')
# so they can be matched between log records without logging all of it. Anyone with the
# full webhook_id can post data to the HA Mobile App webhook.

#--------------------------------------------------------------------
def _is_mobapp_rawdata_logged():
    '''
    The MobApp setup records are logged during startup (HA or iCloud3 restart) at any
    log level, like the Apple Acct login records, so a user can restart and send the
    log file without changing the log level. After startup they need rawdata.
    '''
    return Gb.is_log_level_rawdata or Gb.is_icloud3_startup_inprocess

#--------------------------------------------------------------------
def log_mobapp_rawdata(title, data, rawdata_only=True):
    '''
    Write the MobApp setup data to the icloud3 log file during startup or when the log
    level is rawdata. It is not passed through rawdata_logging.FILTER_FIELDS since that
    drops most of the entity registry and config entry fields. Each dict item is on its
    own line.

    rawdata_only=False - Always log it (summary). Never pass a webhook_id that has not
        been shortened with shrink_item.
    '''
    if rawdata_only and _is_mobapp_rawdata_logged() is False:
        return

    try:
        if type(data) is dict:
            log_msg = ''.join([f"{NL3_DATA}{k}={v}" for k, v in data.items()])
        else:
            log_msg = f"{NL3_DATA}{data}"

        log_info_msg(f"{title.upper()}{log_msg}")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _mobapp_config_entry_log_fields(config_entry):
    '''
    Return the mobile_app config entry fields that identify the app registration as a
    dict for logging. A new registration (app reinstalled, server removed and added in
    the app) creates a new config entry, webhook_id and device_tracker entity.
    '''
    if config_entry is None:
        return None

    data     = config_entry.data
    app_data = data.get('app_data') or {}

    return {'entry_id':         shrink_item(config_entry.entry_id),
            'title':            config_entry.title,
            'state':            str(config_entry.state),
            'disabled_by':      (str(config_entry.disabled_by)
                                    if config_entry.disabled_by else None),
            'device_name':      data.get('device_name'),
            'device_id':        shrink_item(data.get('device_id')),
            'app_id':           data.get('app_id'),
            'app_name':         data.get('app_name'),
            'app_version':      data.get('app_version'),
            'os_name':          data.get('os_name'),
            'os_version':       data.get('os_version'),
            'manufacturer':     data.get('manufacturer'),
            'model':            data.get('model'),
            'supports_encryption': data.get('supports_encryption'),
            'push_notify':      bool(app_data.get('push_token') or app_data.get('push_url')),
            'webhook_id':       shrink_item(data.get(CONF_WEBHOOK_ID)),
            }
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

    RawData:
    _device_reg_data=DeviceEntry(config_entry_id='01KMMN6EY65GYAG21B3EPJ566N',
    area_id=None, config_subentry_id=None,
    created_at=datetime.datetime(2026, 3, 26, 8, 46, 53, 895557, tzinfo=datetime.timezone.utc), disabled_by=None, id='02839381d462bef3c724e3a88d5cb6b8',
    identifiers={('mobile_app', 'D01C5CE4-0DDB-4352-BC08-FA3B5B22EABB')},
    labels=set(), modified_at=datetime.datetime(2026, 10, 17, 9, 59, 37, 763846,
    tzinfo=datetime.timezone.utc),
    name_by_user='Gary-iPhone-app', name='Gary-iPhone',
    _cache={...}, configuration_url=None, connections=set(), entry_type=None,
    hw_version=None, composite_device_id=None, composite_primary_config_entry=None,
    split_at=None, manufacturer='Apple', model='iPhone19,3', model_id=None,
    has_composite_identifiers=False, serial_number=None, sw_version='27.0.1',
    via_device_id=None, _pending_move=None, _composite_subentries=None)

    Filtered:
    _device_reg_data={'id': '02839381d462bef3c724e3a88d5cb6b8',
    'config_entry_id': '01KMMN6EY65GYAG21B3EPJ566N',
    'identifiers': [('mobile_app', 'D01C5CE4-0DDB-4352-BC08-FA3B5B22EABB')],
    'name': 'Gary-iPhone', 'name_by_user': 'Gary-iPhone-app', 'model': 'iPhone19,3',
    'manufacturer': 'Apple', 'hw_version': None, 'sw_version': '27.0.1',
    'disabled_by': None,
    'created_at': '2026-03-26 04:46:53', 'modified_at': '2026-10-17 05:59:37'}
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

        # All Mobile App registrations, including ones without a device_tracker entity
        # and old ones left over from reinstalling the app
        mobapp_config_entries = Gb.hass.config_entries.async_entries('mobile_app')
        info_summary = {}       # Info level log - entity_id: setup result (no webhook_ids)
        if _is_mobapp_rawdata_logged():
            log_mobapp_rawdata(
                    f"{NL3D}MobApp Integration - {len(mobapp_config_entries)} config entries, "
                    f"{len(dev_trkr_entities)} device_tracker entities",
                    {shrink_item(config_entry.entry_id): _mobapp_config_entry_log_fields(config_entry)
                                        for config_entry in mobapp_config_entries})

        for dev_trkr_entity in dev_trkr_entities:
            mobapp_dname = dev_trkr_entity.entity_id.replace('device_tracker.', '')
            device_id    = dev_trkr_entity.device_id

            # Everything iCloud3 uses to identify and set up this MobApp device. It is
            # logged when the device is set up or skipped (rawdata log level).
            log_title  = f"{NL3D}MobApp device_tracker setup - <{mobapp_dname}>"
            mobapp_log = {'entity': {
                            'entity_id':        dev_trkr_entity.entity_id,
                            'unique_id':        shrink_item(dev_trkr_entity.unique_id),
                            'device_id':        shrink_item(device_id),
                            'config_entry_id':  shrink_item(dev_trkr_entity.config_entry_id),
                            'name':             dev_trkr_entity.name,
                            'original_name':    dev_trkr_entity.original_name,
                            'disabled_by':      (str(dev_trkr_entity.disabled_by)
                                                    if dev_trkr_entity.disabled_by else None),
                            'hidden_by':        (str(dev_trkr_entity.hidden_by)
                                                    if dev_trkr_entity.hidden_by else None),
                            }}

            if device_id is None:
                mobapp_log['result'] = 'SKIPPED - The device_tracker entity has no HA device_id'
                info_summary[dev_trkr_entity.entity_id] = 'SKIPPED - No HA device_id'
                log_mobapp_rawdata(log_title, mobapp_log)
                continue

            # Disabled device_trackers are kept so the error can say it is disabled
            # instead of not found. They are not in the config_flow selection list.
            if dev_trkr_entity.disabled_by:
                Gb.mobapp_id_by_disabled_mobapp_dname[mobapp_dname] = device_id
                mobapp_log['result'] = ( 'SKIPPED - The device_tracker entity is disabled in HA, '
                                        'not in the MobApp selection list')
                info_summary[dev_trkr_entity.entity_id] = \
                        f"SKIPPED - Disabled in HA ({dev_trkr_entity.disabled_by})"
                log_mobapp_rawdata(log_title, mobapp_log)
                continue

            raw_model = 'Unknown'
            device_reg_data = None
            try:
                # Get raw_model from HA device_registry
                device_reg_data = device_registry.async_get(device_id)
                if _is_mobapp_rawdata_logged():
                    mobapp_log['device_reg'] = (_device_reg_log_fields(device_reg_data)
                                                    or 'NOT FOUND in the HA Device Registry')

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

            mobapp_log['state'] = ({'state':         dev_trkr_state.state,
                                    'friendly_name': dev_trkr_state.attributes.get('friendly_name'),
                                    'last_updated':  dt_util.as_local(dev_trkr_state.last_updated)
                                                        .strftime('%Y-%m-%d %H:%M:%S')}
                                    if dev_trkr_state else 'NO STATE - The entity is not loaded in HA')
            mobapp_log['device_info'] = {'mobapp_fname':       mobapp_fname,
                                        'raw_model':          raw_model,
                                        'device_type':        device_type,
                                        'model_display_name': model_display_name}

            config_entry = Gb.hass.config_entries.async_get_entry(dev_trkr_entity.config_entry_id)
            mobapp_log['config_entry'] = (_mobapp_config_entry_log_fields(config_entry)
                                            or 'NOT FOUND - Orphaned entity, the Mobile App '
                                                'registration was removed')

            if config_entry is None or CONF_WEBHOOK_ID not in config_entry.data:
                mobapp_log['result'] = ( 'PARTIAL - The mobile_app config entry or webhook_id was '
                                        'not found, the sensors and notify service can not be '
                                        'matched to the device_tracker')
                info_summary[dev_trkr_entity.entity_id] = (
                        f"{mobapp_fname}, {model_display_name} ({raw_model}), "
                        f"PARTIAL - MobApp config entry "
                        f"{'not found' if config_entry is None else 'has no webhook_id'}, "
                        f"no sensors or notify")
                log_mobapp_rawdata(log_title, mobapp_log)
                continue

            webhook_id = config_entry.data[CONF_WEBHOOK_ID]
            Gb.mobapp_dname_by_webhook_id[webhook_id] = mobapp_dname

            # The watchOS app does not have a last_update_trigger sensor or a notify service
            if (config_entry.data.get('os_name') == 'watchOS'
                    or instr(config_entry.data.get('app_id', ''), 'watchkitapp')):
                list_add(Gb.mobapp_dnames_watchos, mobapp_dname)

            # iOS-last_update_trigger, Android-last_update
            sensors_log = {}
            sensors_log['last_update_trigger'] = \
                _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.last_updt_trig_by_mobapp_dname, ['last_update_trigger', 'last_update'])
            sensors_log['battery_level'] = \
                _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.battery_level_sensors_by_mobapp_dname, ['battery_level'])
            sensors_log['battery_state'] = \
                _set_mobapp_sensor(entity_registry, mobapp_dname, webhook_id,
                                Gb.battery_state_sensors_by_mobapp_dname, ['battery_state'])
            mobapp_log['sensors'] = sensors_log

            # A sensor was not found by its unique_id. List this registration's battery and
            # update sensors with their unique_ids to see what HA actually has.
            if (_is_mobapp_rawdata_logged()
                    and [status for status in sensors_log.values() if status.startswith('NOT FOUND')]):
                mobapp_log['config_entry_sensors'] = {
                        entity.entity_id: (entity.unique_id.replace(f"{webhook_id}_", '<webhook_id>_')
                                            + (f" (DISABLED-{entity.disabled_by})"
                                                    if entity.disabled_by else ''))
                        for entity in er.async_entries_for_config_entry(
                                                entity_registry, config_entry.entry_id)
                        if (entity.domain == 'sensor'
                                and (instr(entity.unique_id, 'battery')
                                    or instr(entity.unique_id, 'last_update')))} \
                    or 'No battery or last_update sensors in this config entry'

            mobapp_log['result'] = ( 'WATCHOS - Added to the MobApp selection list'
                                    if mobapp_dname in Gb.mobapp_dnames_watchos
                                    else 'Added to the MobApp selection list')
            log_mobapp_rawdata(log_title, mobapp_log)

            # 'sensor.x' --> OK, 'DISABLED - sensor.x' --> Disabled, 'NOT FOUND - ...' --> Not Found
            sensor_status = {sensor: ('OK' if status.startswith('sensor.')
                                        else status.split(' - ')[0].title())
                                        for sensor, status in sensors_log.items()}
            info_summary[dev_trkr_entity.entity_id] = (
                    f"{mobapp_fname}, {model_display_name} ({raw_model}), "
                    f"{config_entry.data.get('os_name')} {config_entry.data.get('os_version')}, "
                    f"App-{config_entry.data.get('app_version')}, "
                    f"Trigger-{sensor_status['last_update_trigger']}, "
                    f"BatLevel-{sensor_status['battery_level']}, "
                    f"BatState-{sensor_status['battery_state']}"
                    f"{', watchOS' if mobapp_dname in Gb.mobapp_dnames_watchos else ''}")

        # Mobile App registrations that do not have a device_tracker entity (location
        # turned off in the app, or an old registration whose entity was deleted)
        dev_trkr_entry_ids = [entity.config_entry_id for entity in dev_trkr_entities]
        no_dev_trkr = [f"{entry.title} ({entry.data.get('device_name')})"
                                for entry in mobapp_config_entries
                                if entry.entry_id not in dev_trkr_entry_ids]
        if no_dev_trkr:
            info_summary['No device_tracker entity'] = list_to_str(no_dev_trkr)

        log_mobapp_rawdata(
                f"MobApp Integration > {len(mobapp_config_entries)} registrations, "
                f"{len(dev_trkr_entities)} device_trackers",
                info_summary or 'No Mobile App device_tracker entities',
                rawdata_only=False)

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

    Return - The result for the rawdata log:
        'sensor.gary_iphone_app_battery_level' - Found and used
        'DISABLED - sensor.gary_iphone_app_battery_level'
        'NOT FOUND - unique_id <webhook_id>_battery_level'
    '''
    disabled_entity_ids = []
    for sensor_id in sensor_ids:
        entity_id = entity_registry.async_get_entity_id('sensor', 'mobile_app',
                                                        f"{webhook_id}_{sensor_id}")
        if entity_id is None:
            continue

        if entity_registry.async_get(entity_id).disabled_by:
            Gb.disabled_sensors_by_mobapp_dname.setdefault(mobapp_dname, {})[sensor_ids[0]] = entity_id
            disabled_entity_ids.append(entity_id)
            continue

        sensors_by_mobapp_dname[mobapp_dname] = entity_id
        return entity_id

    if disabled_entity_ids:
        return f"DISABLED - {list_to_str(disabled_entity_ids)}"

    unique_ids = [f"<webhook_id>_{sensor_id}" for sensor_id in sensor_ids]
    return f"NOT FOUND - unique_id {list_to_str(unique_ids)}"

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

    # targets are the registrations with a push token {device_name: webhook_id}. The
    # webhook_id is matched to the device_tracker's config entry
    # (Gb.mobapp_dname_by_webhook_id) in setup_notify_service_name_for_mobapp_devices.
    # registered_targets are the notify.mobile_app_<name> services HA set up.
    # Also logged after startup when the targets are found. icloud3_main only retries this
    # while there are no targets so it is logged once (the delayed setup after HA starts).
    log_mobapp_rawdata(
            f"{NL3D}MobApp Notify Service targets",
            {'targets':             {device_name: shrink_item(webhook_id)
                                        for device_name, webhook_id in mobapp_fname_targets.items()},
             'registered_targets':  list(notify_targets.keys()),
             'device_tracker_webhook_ids':
                                    {shrink_item(webhook_id): mobapp_dname
                                        for webhook_id, mobapp_dname in Gb.mobapp_dname_by_webhook_id.items()},
            },
            rawdata_only=is_empty(mobapp_fname_targets))

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

    notify_match_log = {}
    for mobapp_fname, webhook_id in notify_devices.items():
        mobapp_dname = Gb.mobapp_dname_by_webhook_id.get(webhook_id)
        if mobapp_dname is None:
            notify_match_log[mobapp_fname] = (f"webhook_id {shrink_item(webhook_id)} > "
                                            f"NO MobApp device_tracker with this webhook_id")
            continue

        notify_devicename = slugify(mobapp_fname)
        mobapp_id = Gb.mobapp_id_by_mobapp_dname.get(mobapp_dname)
        if mobapp_id:
            Gb.mobapp_fnames_by_mobapp_id[mobapp_id] = mobapp_fname

        notify_match_log[mobapp_fname] = (f"device_tracker.{mobapp_dname} > "
                                        f"NOT USED by a monitored iCloud3 Device")
        for devicename, Device in Gb.Devices_by_devicename.items():
            if (Device.is_mobapp_monitored is False
                    or Device.mobapp[DEVICE_TRACKER] != f"device_tracker.{mobapp_dname}"):
                continue

            Device.conf_mobapp_fname = mobapp_fname
            Device.mobapp[NOTIFY] = f"mobile_app_{notify_devicename}"
            setup_msg+=(f"{CRLF_DOT}{Device.devicename_fname}{RARROW}"
                        f"{mobapp_fname} ({notify_devicename})")
            notify_match_log[mobapp_fname] = (f"device_tracker.{mobapp_dname} > {devicename}, "
                                            f"notify.{Device.mobapp[NOTIFY]}")
            break

    # Info level, it may run every 5-secs while the notify service is not set up yet
    if notify_match_log:
        log_mobapp_rawdata(f"MobApp Notify Service > iCloud3 Device", notify_match_log,
                            rawdata_only=False)

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
