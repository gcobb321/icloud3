"""GitHub Custom Component."""
import asyncio

# from homeassistant.components import history
# from homeassistant.const import CONF_DOMAINS, CONF_ENTITIES, CONF_EXCLUDE, CONF_INCLUDE


from homeassistant.config_entries         import ConfigEntry
from homeassistant.const                  import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core                   import HomeAssistant
from homeassistant.helpers.typing         import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers                import (area_registry as ar, )
import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import homeassistant.util.location  as ha_location_info
import os
import logging


from .const import (DOMAIN, PLATFORMS, ICLOUD3, MODE_PLATFORM, MODE_INTEGRATION, CONF_VERSION,
                    CONF_SETUP_ICLOUD_SESSION_EARLY, CONF_EVLOG_BTNCONFIG_URL,
                    SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                    EVLOG_IC3_STARTING, VERSION, )

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

# from .const_sensor import (HA_EXCLUDE_SENSORS, )

from .global_variables              import GlobalVariables as Gb
from .helpers.messaging             import (_trace, _traceha, open_ic3log_file_init,
                                            post_evlog_greenbar_msg, post_startup_alert,
                                            log_info_msg, log_debug_msg, log_error_msg,
                                            log_exception_HA, log_exception)
from .helpers.time_util             import (time_now_secs, )
from .support.v2v3_config_migration import iCloud3_v2v3ConfigMigration
from .support                       import start_ic3
from .support                       import config_file
from .support                       import restore_state
from .support.service_handler       import register_icloud3_services
from .support                       import pyicloud_ic3_interface
from .support                       import event_log
from .support                       import recorder_prefilter
from .icloud3_main                  import iCloud3
from .                              import config_flow

Gb.HARootLogger = logging.getLogger("")
Gb.HALogger     = logging.getLogger(__name__)

successful_startup = True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Old way of setting up the iCloud tracker with platform: icloud3 statement."""
    hass.data.setdefault(DOMAIN, {})
    Gb.hass   = hass
    Gb.config = config

    try:
        device_trackers = config.get('device_tracker')
        if device_trackers:
            for tracker in device_trackers:
                if tracker['platform'] == DOMAIN:
                    Gb.ha_config_platform_stmt = True
                    Gb.operating_mode = MODE_PLATFORM

                    # Initialize the config/.storage/icloud3/configuration file before the config_glow
                    # has set up the integration
                    start_ic3.initialize_directory_filenames()
                    config_file.load_storage_icloud3_configuration_file()

                    if Gb.conf_profile[CONF_VERSION] == 1:
                        Gb.HALogger.warning(f"Starting iCloud3 v{VERSION} > "
                                            "Detected a `platform: icloud3` statement in the "
                                            "configuration.yaml file. This is depreciated and "
                                            "should be removed.")

    except Exception as err:
        # log_exception(err)
        # log_exception_HA(err)
        pass


    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP PROCESS TO START ICLOUD3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def start_icloud3(event=None):
    Gb.initial_icloud3_loading_flag = True
    log_debug_msg(f'START iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')
    icloud3_started = await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_msg =(f"iCloud3 v{Gb.version} Started")
        log_info_msg(log_msg)
        Gb.HALogger.info(f"Gb.HALogger-Setting up iCloud3 v{Gb.version}")
        # Gb.HALogger.info(f"# Gb.HALogger-Setting up iCloud3 v{Gb.version}")
    else:
        log_msg =(f"iCloud3 v{Gb.version} - Failed to Start")
        log_error_msg(log_msg)
        Gb.HALogger.info(f"Setting up iCloud3 v{Gb.version}, Failed")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
#
#   INTEGRATION MODE - STARTED FROM CONFIGURATION > INTEGRATIONS ENTRY
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """ Set up the iCloud3 integration from a ConfigEntry integration """

    try:
        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN][entry.unique_id] = DOMAIN
        if entry.unique_id is None:
            hass.config_entries.async_update_entry(entry, unique_id=DOMAIN)
        hass_data = dict(entry.data)

        # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
        # unsub_options_update_listener = entry.add_update_listener(options_update_listener)
        # hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        # hass.data[DOMAIN][entry.entry_id] = hass_data


        Gb.hass           = hass
        Gb.config_entry   = entry
        Gb.entry_id       = entry.entry_id
        Gb.operating_mode = MODE_INTEGRATION
        Gb.PyiCloud       = None
        Gb.start_icloud3_inprocess_flag = True

        start_ic3.initialize_directory_filenames()

        await Gb.hass.async_add_executor_job(
                config_file.load_storage_icloud3_configuration_file)

        start_ic3.set_log_level(Gb.log_level)

        Gb.evlog_btnconfig_url = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.evlog_version       = Gb.conf_profile['event_log_version']
        Gb.EvLog               = event_log.EventLog(Gb.hass)

        await Gb.hass.async_add_executor_job(
                open_ic3log_file_init)

        Gb.HALogger.info(f"Setting up iCloud3 v{Gb.version}")
        log_info_msg(f"Setting up iCloud3 v{VERSION}")

        if Gb.restart_ha_flag:
            log_error_msg("iCloud3 > Waiting for HA restart to remove legacy \
                            devices before continuing")
            return False

        await async_get_ha_location_info(hass)

        recorder_prefilter.add_filter(hass, [SENSOR_EVENT_LOG_NAME])

        start_ic3.initialize_icloud_data_source()
        await Gb.hass.async_add_executor_job(
                restore_state.load_storage_icloud3_restore_state_file)

        # config_file.count_lines_of_code(Gb.icloud3_directory)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:


            pass

        except Exception as err:
            log_exception(err)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        # set_up_default_area_id()

        # Create device_tracker entities if devices have been configure
        # Otherwise, this is done in config_flow when the first device is set up
        if Gb.conf_devices != []:
            await Gb.hass.config_entries.async_forward_entry_setups(
                    entry, ['device_tracker'])

        # Create sensor entities
        await Gb.hass.config_entries.async_forward_entry_setups(
                    entry, ['sensor'])

        # Do not start if loading/initialization failed
        if successful_startup is False:
            log_error_msg(f"iCloud3 Initialization Failed, configuration file "
                            f"{Gb.icloud3_config_filename} failed to load.")
            log_error_msg("Verify the configuration file and delete it manually if necessary")
            return False

        # Store a reference to the unsubscribe function to cleanup if an entry is unloaded.
        unsub_options_update_listener = entry.add_update_listener(options_update_listener)
        hass_data["unsub_options_update_listener"] = unsub_options_update_listener
        hass.data[DOMAIN][entry.entry_id] = hass_data

    except Exception as err:
        log_exception(err)
        return False

    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #
    #   SETUP PROCESS TO START ICLOUD3
    #
    #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    Gb.EvLog.display_user_message(f"Starting iCloud3 v{Gb.version}")
    Gb.EvLog.post_event(f"{EVLOG_IC3_STARTING}iCloud3 v{Gb.version} > Starting, "
                        f"{dt_util.now().strftime('%A, %b %d')}")

    Gb.iCloud3  = iCloud3()

    # These will run concurrently while HA is starting everything else
    Gb.EvLog.post_event('Start HA Startup/Stop Listeners')
    Gb.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, start_ic3.ha_startup_completed)
    Gb.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, start_ic3.ha_stopping)

    Gb.EvLog.post_event('Start iCloud3 Services Executor Job')
    Gb.hass.async_add_executor_job(register_icloud3_services)

    if (Gb.primary_data_source_ICLOUD and Gb.conf_tracking[CONF_SETUP_ICLOUD_SESSION_EARLY]):
        Gb.EvLog.post_event('Start iCloud Account Session Executor Job')
        Gb.hass.async_add_executor_job(
                pyicloud_ic3_interface.create_PyiCloudService_executor_job)

    Gb.initial_icloud3_loading_flag = True
    log_debug_msg('START iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')

    icloud3_started = \
        await Gb.hass.async_add_executor_job(
                Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_info_msg(f"iCloud3 v{Gb.version} Startup Complete")
        Gb.HALogger.info(f"Setting up iCloud3 v{Gb.version}, Complete")
    else:
        log_error_msg(f"iCloud3 v{Gb.version} Initialization Failed")
        Gb.HALogger.info(f"Setting up iCloud3 v{Gb.version}, Failed")

    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>
async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)

#-------------------------------------------------------------------------------------------
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, "sensor")]))

    # Remove options_update_listener.
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"]()

    # Remove config entry from domain.
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

#-------------------------------------------------------------------------------------------
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
            Gb.country_code = Gb.ha_location_info['country_code'].lower()
            Gb.use_metric   = Gb.ha_location_info['use_metric']
        except Exception as err:
            log_exception(err)
            pass

# def set_up_default_area_id():
    # Get Personal Devices area id
    # area_reg = ar.async_get(hass)
    # if Gb.conf_devices == []:
    #     area_data = area_reg.async_get_or_create('Personal Device')
    # else:
    #     area_data = area_reg.async_get_area_by_name('Personal Device')
    # Gb.area_id_personal_device = area_data.id if area_data else None
