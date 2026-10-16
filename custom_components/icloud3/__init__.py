

from .global_variables  import GlobalVariables as Gb
from .const             import (ICLOUD3, DOMAIN,
                                PLATFORMS, PLATFORM_DEVICE_TRACKER, PLATFORM_SENSOR,
                                CRLF, RED_ALERT, INACTIVE,
                                CONF_FNAME, CONF_TRACKING_MODE,
                                MODE_PLATFORM, MODE_INTEGRATION, CONF_VERSION,
                                EVLOG_ATTENTION, EVLOG_ALERT, VERSION, VERSION_BETA,)


from .utils.messaging   import (_evlog, _log, async_open_ic3log_file_init,
                                post_event, post_monitor_msg, post_greenbar_msg, post_alert,
                                log_info_msg, log_debug_msg, log_error_msg, log_data_unfiltered,
                                log_exception_HA, log_exception, add_log_file_filter)
from .utils.time_util   import (time_now_secs, time_now, secs_to, secs_since, secs_to_hhmm,
                                calculate_time_zone_offset, format_day_date_time_now, )
from .utils.file_io     import (read_json_file, save_json_file,
                                make_directory, directory_exists, )
from .utils             import entity_reg_util as er_util

from .                  import device_tracker as ic3_device_tracker
from .                  import sensor as ic3_sensor
from .apple_acct.internet_error import InternetConnection_ErrorHandler
from .apple_acct.apple_acct_upw import ValidateAppleAcctUPW
from .icloud3_main      import iCloud3
from .startup           import start_ic3
from .startup           import config_file
from .startup           import restore_state
from .support.service_handler import register_icloud3_services
from .support.event_log import EventLog
from .support           import hacs_ic3
from .support           import analytics


#--------------------------------------------------------------------
import asyncio
from re import match
from importlib import reload

from homeassistant.config_entries       import ConfigEntry
from homeassistant.const                import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core                 import HomeAssistant, CoreState
from homeassistant.exceptions           import HomeAssistantError
from homeassistant.helpers.event        import async_track_device_registry_updated_event
from homeassistant.helpers.start        import async_at_started
from homeassistant.helpers              import (entity_registry as er, device_registry as dr,
                                                area_registry as ar, )
from homeassistant.helpers.typing       import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import homeassistant.util.location  as ha_location_info


CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)
import logging
Gb.HARootLogger = logging.getLogger("")
Gb.HALogger     = logging.getLogger(__name__)

successful_startup = True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   INTEGRATION MODE - STARTED FROM CONFIGURATION > INTEGRATIONS ENTRY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """ Set up the iCloud3 integration from a ConfigEntry integration """

    # Is 'icloud3' already in hass.data
    Gb.was_icloud3_reloaded = DOMAIN in hass.data.get(DOMAIN, {})

    if Gb.was_icloud3_reloaded:
        # Reloading/restarting, reinitialization is not needed
        if entry.entry_id != Gb.config_entry_id:
            setup_hass_icloud3_domain(hass, entry)
        await async_start_icloud3(None)
    else:
        # Initial load, initialize iCloud3 an wait for HA to finish starting up
        setup_hass_icloud3_domain(hass, entry)
        await async_initialize_icloud3(hass, entry)
        entry.async_on_unload(async_at_started(Gb.hass, async_start_icloud3))

    return True

#................................................................................
def setup_hass_icloud3_domain(hass, entry):
    '''
    Save the hass and entry variables in Gb. for future use
    Set up the hass[DOMAIN] entry items
    '''

    Gb.hass            = hass
    Gb.config_entry    = entry
    Gb.config_entry_id = entry.entry_id

    Gb.hass.data.setdefault(DOMAIN, {})

    if entry.entry_id not in Gb.hass.data[DOMAIN]:
        Gb.hass.data[DOMAIN][entry.entry_id] = {}
    Gb.hass.data[DOMAIN][entry.unique_id] = DOMAIN
    if entry.unique_id is None:
        Gb.hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)

    # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    Gb.hass.data[DOMAIN]["unsub_options_update_listener"] = unsub_options_update_listener

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   INITIALIZE ICLOUD3 OPERATIONS WHEN HA FIRST LOADS ICLOUD3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_initialize_icloud3(hass, entry):
    Gb.operating_mode  = MODE_INTEGRATION
    start_ic3.initialize_directory_filenames()

    await async_open_ic3log_file_init()
    await config_file.async_load_icloud3_configuration_file()

    Gb.EvLog                = EventLog()
    Gb.iCloud3              = iCloud3()
    Gb.InternetError        = InternetConnection_ErrorHandler()
    Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()
    post_event( f"{Gb.icloud3_attention_msg} > Initial Start-up")

    await async_create_device_tracker_sensor_platforms()
    Gb.is_icloud3_initial_startup = True
    await start_icloud3_on_init_load_only()
    await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3_stage_1_2_3_prep_to_config_device)

    Gb.hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, start_ic3.ha_stopping)

    if Gb.hass.state is CoreState.running:
        # iCloud3 was added on the Integrations screen, or the config entry was reloaded,
        # while HA was already running. EVENT_HOMEASSISTANT_STARTED has already been
        # fired and will not be fired again. `async_at_started` runs async_start_icloud3
        # right now instead of waiting for an event that will never come. Waiting for it
        # left stages 4-6 unrun and Gb.is_icloud3_startup_inprocess set until HA restarted.
        log_info_msg('HA is already running, starting iCloud3 now')
    else:
        Gb.EvLog.display_user_message("Waiting for HA Startup to Finish Loading")
        post_greenbar_msg("Waiting for HA Startup to Finish Loading")

    # entry.async_on_unload(async_at_started(Gb.hass, async_start_icloud3))

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   START ICLOUD3 CONFIGURATION - SETUP AND BEGIN TRACKING DEVICES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''
This is run when:
    - HA is being restarted and the EVENT_HOMEASSISTANT_STARTED is fired
    - iCloud3 is being reloaded at the beginning of the async_setup_entry function
'''
async def async_start_icloud3(dummy_parameter):
    startup_test_code()

    if Gb.was_icloud3_reloaded:
        starting_msg = 'Reloading'
        log_info_msg(f"{'<'*30}{'>'*30}")
        log_info_msg(f"\n\n{'🔶'*5} ICLOUD3 IS RELOADING {'🔶'*5}\n\n")
        log_info_msg(f"{'<'*30}{'>'*30}")

        await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3_stage_1_2_3_prep_to_config_device)
    else:
        starting_msg = 'Starting'
        post_greenbar_msg(  f"Setting up Devices ({len(Gb.conf_devices)}) "
                            f"& Sensors ({ic3_sensor.total_sensors_cnt()})")

    Gb.icloud3_reload_requested = False

    try:
        Gb.HALogger.info(f"Setting up {Gb.icloud3_version_msg}, {starting_msg}")
        log_info_msg(f"Setting up {Gb.icloud3_version_msg}, {starting_msg}")

        await async_create_devices_tracker_and_sensor_entities()

        log_debug_msg('Start iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')

        # Now, start iCloud3 operations in it's own thread instead of running in the Event Loop.
        # You can not do asyncio/await functions but the requests can now be run without creating
        # an HA blocking call error.
        # icloud3_started = await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3)
        icloud3_started = await Gb.hass.async_add_executor_job(
                                            Gb.iCloud3.start_icloud3_stage_4_5_6_load_aa_device_to_locate)

        if icloud3_started:
            log_info_msg(f"{Gb.icloud3_version_msg} Start up Complete")
            Gb.HALogger.info(f"Setting up {Gb.icloud3_version_msg}, Complete")

            if analytics.is_analytics_send_due():
                Gb.hass.async_create_task(analytics.async_send_analytics_data())
        else:
            log_error_msg(f"{Gb.icloud3_version_msg} Initialization Failed")
            Gb.HALogger.info(f"Setting up {Gb.icloud3_version_msg}, Failed")

    except Exception as err:
        log_exception(err)

    startup_test_code_after_complete()

#-------------------------------------------------------------------------------------------
async def start_icloud3_on_init_load_only():
    try:
        await async_get_ha_location_info(Gb.hass)
        calculate_time_zone_offset()
        setup_event_listeners()

        if Gb.is_ha_restart_needed:
            log_error_msg("iCloud3 > Waiting for HA restart to remove legacy "
                            "devices before continuing")
            return False

        await hacs_ic3.check_hacs_icloud3_update_available()
        await start_ic3.update_lovelace_resource_event_log_js_entry()

        Gb.EvLog.display_user_message("Registering Services")
        Gb.EvLog.post_event('Seting up iCloud3 Actions/Services')
        Gb.hass.async_add_executor_job(register_icloud3_services)

        if Gb.count_lines_of_code:
            config_file.count_lines_of_code('custom_components/icloud3')
            Gb.count_lines_of_code = False

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
async def async_get_ha_location_info(hass):
    if location_info := await ha_location_info.async_detect_location_info(
            async_get_clientsession(hass)):

        Gb.ha_location_info = {
            "country_code": location_info.country_code,
            "region_code": location_info.region_code,
            "zip_code": location_info.zip_code,
            "region_name": location_info.region_name,
            "city": location_info.city,
            "time_zone": location_info.time_zone,
            "latitude": location_info.latitude,
            "longitude": location_info.longitude,
            "use_metric": location_info.use_metric,
        }

        try:
            log_debug_msg(f"HA Location Data > {Gb.ha_location_info}")
            Gb.country_code = Gb.ha_location_info['country_code'].lower()
            Gb.use_metric   = Gb.ha_location_info['use_metric']
        except Exception as err:
            log_exception(err)
            pass


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#   LISTENER, DEVICE & SENSOR SUPPORT FUNCTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
def setup_event_listeners():

    # Device Registry Event
    if "update_device_registry" not in Gb.hass.data[DOMAIN]:
        cancel_listener_func = Gb.hass.bus.async_listen(
                                        dr.EVENT_DEVICE_REGISTRY_UPDATED,
                                        er_util.async_handle_update_device_registry)

        log_debug_msg(f"Add Listener > (update_device_registry)")
        Gb.hass.data[DOMAIN][Gb.config_entry_id]["update_device_registry"] = cancel_listener_func

    # Entity (Sensor) Registry Event
    if "update_entity_registry" not in Gb.hass.data[DOMAIN]:
        cancel_listener_func = Gb.hass.bus.async_listen(
                                        er.EVENT_ENTITY_REGISTRY_UPDATED,
                                        er_util.async_handle_update_entity_registry)

        log_debug_msg(f"Add Listener > (update_entity_registry)")
        Gb.hass.data[DOMAIN][Gb.config_entry_id]["update_entity_registry"] = cancel_listener_func


#-------------------------------------------------------------------------------------------
async def async_create_device_tracker_sensor_platforms():
    '''
    Create iCloud3 internal sensors (icloud3_event_log, icloud3_alerts, icloud3_wazehist_track)
    All other device sensors are created after the devices are created
    '''
    if Gb.was_icloud3_reloaded:
        return

    post_event('Setting up device_tracker and sensor entities')

    await Gb.hass.config_entries.async_forward_entry_setups(Gb.config_entry, [PLATFORM_DEVICE_TRACKER])
    await Gb.hass.config_entries.async_forward_entry_setups(Gb.config_entry, [PLATFORM_SENSOR])

#-------------------------------------------------------------------------------------------
async def async_create_devices_tracker_and_sensor_entities():
    '''
    Create device_tracker entities if devices have been configure
    Otherwise, this is done in config_flow when the first device is set up
    Create sensor entities for all devices
    '''

    if Gb.conf_devices != []:
        await ic3_device_tracker.async_create_Device_Tracker_objects()
        await ic3_sensor.async_create_Sensor_objects()

#-------------------------------------------------------------------------------------------
async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    '''Handle options update.'''

    await hass.config_entries.async_reload(config_entry.entry_id)

#-------------------------------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    '''
    When disabled sensors are reenabled, HA will schedule an unload in 30s followed
    by a reload. The er_util.async_handle_update_entity_registry function is called when
    the sensor is enabled and sets the Gb.icloud3_reload_requested to True. This prevents
    all of the DeviceTracker and Sensor objects from being unloaded and deleted here.
    '''
    if Gb.was_icloud3_reloaded:
        return True

    if Gb.icloud3_reload_requested:
        Gb.icloud3_reload_requested = False
        return True

    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(
            *[  hass.config_entries.async_forward_entry_unload(entry, PLATFORM_DEVICE_TRACKER),
                hass.config_entries.async_forward_entry_unload(entry, PLATFORM_SENSOR)]
            ))

    # Remove options_update_listener.
    log_debug_msg(f"Remove Listener > unsub_options_update_listener")
    log_debug_msg(f"Remove Listener > update_device_registry")
    log_debug_msg(f"Remove Listener > update_entity_registry")

    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()
    hass.data[DOMAIN][entry.entry_id]["update_device_registry"]()
    hass.data[DOMAIN][entry.entry_id]["update_entity_registry"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

#-------------------------------------------------------------------------------------------
async def async_remove_config_entry_device(hass: HomeAssistant,
# Swap these two statements to turn this off. HA looks the function up by name, so the
# 'x_' name makes it invisible and HA no longer offers Delete on the Integrations screen.
# Requires an HA restart - `supports_remove_device` is cached and a reload will not reset it.
# async def x_async_remove_config_entry_device(hass: HomeAssistant,
                                            config_entry: ConfigEntry,
                                            device_entry: dr.DeviceEntry) -> bool:
    '''
    HA calls this when the user clicks Delete on a device on the Integrations screen.

    This is the only unambiguous 'the user deleted this device' signal HA provides.
    iCloud3's own device registry removals (config_flow device deletion, the entity
    registry cleanup tools) call dr.async_remove_device directly and do not come through
    here, so nothing has to be suppressed or flagged.

    Note: Simply defining this function is what makes HA offer the Delete option on the
    Integrations screen (config_entries.support_remove_from_device).

    A device iCloud3 is still tracking is not deleted here. Deleting it would leave the
    iCloud3 configuration file and the HA registries out of sync, so the request is
    rejected and the user is directed to the iCloud3 configuration screen, which deletes
    the device, all of it's sensors and both registry entries together.

    Raising HomeAssistantError displays it's message on the Integrations screen.
    Returning False displays HA's generic 'rejected by integration' message instead.

    A device iCloud3 does not know about is an orphaned registry entry. Return True so
    HA can delete it.

    The test is whether the devicename is in the iCloud3 configuration file, NOT whether
    there is a Device object for it. A device that is disabled on the Integrations screen,
    or whose Tracking Mode is Inactive, has no Device object but is still configured in
    iCloud3. Testing Gb.Devices_by_devicename let those two be deleted here without any
    message, which is what leaves the configuration file and the registries out of sync.

    Note: Disabling the device on the Integrations screen does not come through here at
    all - HA provides no way to reject that. It is handled in
    er_util.async_handle_update_device_registry, which restarts iCloud3. The restart
    rereads the device registry and does not recreate the disabled device. The iCloud3
    configuration is not changed, so enabling the device brings it back as it was.
    '''
    try:
        # identifiers={('icloud3', 'gary_iphone')}
        devicename = next((identifier[1]
                            for identifier in device_entry.identifiers
                            if identifier[0] == DOMAIN), None)

        conf_device = config_file.get_conf_device(devicename)

        if conf_device is None:
            log_info_msg(   f'Device Registry Update > {devicename}, Delete Device, '
                            f'Not an iCloud3 Device, Deleted')
            return True

        device_fname = conf_device.get(CONF_FNAME) or devicename

        # The message text is in translations/en.json under `exceptions`. Passing no
        # message to HomeAssistantError makes HA build it from the translation_key.
        if devicename in Gb.ha_disabled_by_by_devicename:
            translation_key = 'device_delete_not_allowed_disabled'
        elif conf_device.get(CONF_TRACKING_MODE) == INACTIVE:
            translation_key = 'device_delete_not_allowed_inactive'
        else:
            translation_key = 'device_delete_not_allowed'

        log_info_msg(   f'Device Registry Update > {devicename}, Delete Device, '
                        f'Rejected, Use the iCloud3 Configuration screen')

        raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key=translation_key,
                translation_placeholders={'device_fname': device_fname})

    except HomeAssistantError:
        raise

    except Exception as err:
        log_exception(err)

    return True

#-------------------------------------------------------------------------------------------
def startup_test_code():
    '''
    Run some test code during startup

        #_log(f"{Gb.hass.data=}")
        # _log(f"{Gb.hass.data['hassio_network_info']=}")

        # _log(f"{Gb.hass.data['lovelace']=}")
        # instance = Gb.hass.data['recorder_instance']
        # _log(f"{instance.entity_filter=}")

    '''

    try:
        pass
        # from .utils             import entity_io
        # er_util.scan_entity_reg_for_icloud3_items()


    except Exception as err:
        log_exception(err)

#-------------------------------------------------------------------------------------------
def startup_test_code_after_complete():
    '''
    Run some test code after startup is complete
    '''

    try:
        pass

    except Exception as err:
        log_exception(err)

#-------------------------------------------------------------------------------------------

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

# async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
#     """Old way of setting up the iCloud tracker with platform: icloud3 statem a ent."""
#     hass.data.setdefault(DOMAIN, {})
#     Gb.hass   = hass
#     Gb.config = config

#     try:
#         device_trackers = config.get('device_tracker')
#         if device_trackers:
#             for tracker in device_trackers:
#                 if tracker['platform'] != DOMAIN:
#                     continue

#                 Gb.ha_config_platform_stmt = True
#                 Gb.operating_mode = MODE_PLATFORM

#                 # Initialize the config/.storage/icloud3/configuration file before the config_flow
#                 # has set up the integration
#                 start_ic3.initialize_directory_filenames()
#                 await config_file.async_load_icloud3_configuration_file()

#                 if Gb.conf_profile[CONF_VERSION] == 1:
#                     Gb.HALogger.warning(f"Starting iCloud3 v{VERSION}{VERSION_BETA} > "
#                                         "Detected a `platform: icloud3` statement in the "
#                                         "configuration.yaml file. This is depreciated and "
#                                         "should be removed.")

#     except Exception as err:
#         # log_exception(err)
#         # log_exception_HA(err)
#         pass

#     return True
