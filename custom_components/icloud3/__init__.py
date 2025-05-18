

from .global_variables  import GlobalVariables as Gb
from .const             import (ICLOUD3, DOMAIN, ICLOUD3_VERSION_MSG,
                                PLATFORMS, ICLOUD3, MODE_PLATFORM, MODE_INTEGRATION, CONF_VERSION,
                                CONF_SETUP_ICLOUD_SESSION_EARLY, CONF_EVLOG_BTNCONFIG_URL,
                                SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                                EVLOG_IC3_STARTING, VERSION, VERSION_BETA,)


from .utils.messaging   import (_evlog, _log, open_ic3log_file_init, open_ic3log_file, post_monitor_msg,
                                            post_evlog_greenbar_msg, post_startup_alert,
                                            log_info_msg, log_debug_msg, log_error_msg,
                                            log_exception_HA, log_exception)
from .utils.time_util   import (time_now_secs, calculate_time_zone_offset, )
from .utils.file_io     import (async_make_directory, async_directory_exists, async_copy_file,
                                            read_json_file, save_json_file,
                                            async_rename_file, async_delete_directory,
                                            make_directory, directory_exists, copy_file, file_exists,
                                            rename_file, move_files, )

from .apple_acct        import pyicloud_ic3_interface
from .apple_acct.pyicloud_ic3 import (PyiCloudValidateAppleAcct, )
from .icloud3_main      import iCloud3
from .startup           import start_ic3
from .startup           import config_file
from .                  import device_tracker as ic3_device_tracker
from .startup           import restore_state
from .tracking.service_handler import register_icloud3_services
from .tracking          import event_log

#--------------------------------------------------------------------
import asyncio
from re         import match

from homeassistant.config_entries         import ConfigEntry
from homeassistant.const                  import EVENT_HOMEASSISTANT_STARTED, EVENT_HOMEASSISTANT_STOP
from homeassistant.core                   import HomeAssistant
from homeassistant.helpers.typing         import ConfigType
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers                import (area_registry as ar, )
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
#   PLATFORM MODE - STARTED FROM CONFIGURATION.YAML 'DEVICE_TRACKER/PLATFORM: ICLOUD3 STATEMENT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>><><><><><><><><><>

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Old way of setting up the iCloud tracker with platform: icloud3 statem a ent."""
    hass.data.setdefault(DOMAIN, {})
    Gb.hass   = hass
    Gb.config = config

    try:
        device_trackers = config.get('device_tracker')
        if device_trackers:
            for tracker in device_trackers:
                if tracker['platform'] != DOMAIN:
                    continue

                Gb.ha_config_platform_stmt = True
                Gb.operating_mode = MODE_PLATFORM

                # Initialize the config/.storage/icloud3/configuration file before the config_flow
                # has set up the integration
                start_ic3.initialize_directory_filenames()
                await Gb.hass.async_add_executor_job(
                                        config_file.load_icloud3_configuration_file)
                # await config_file.async_load_icloud3_configuration_file()

                if Gb.conf_profile[CONF_VERSION] == 1:
                    Gb.HALogger.warning(f"Starting iCloud3 v{VERSION}{VERSION_BETA} > "
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
    icloud3_started = await Gb.hass.async_add_executor_job(
                                            Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_msg =(f"{ICLOUD3_VERSION_MSG} Started")
        log_info_msg(log_msg)
        Gb.HALogger.info(f"Gb.HALogger-Setting up {ICLOUD3_VERSION_MSG}")

    else:
        log_msg =(f"{ICLOUD3_VERSION_MSG} - Failed to Start")
        log_error_msg(log_msg)
        Gb.HALogger.info(f"Setting up {ICLOUD3_VERSION_MSG}, Failed")

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

        ic3_device_tracker.get_ha_device_ids_from_device_registry(Gb.hass)
        start_ic3.initialize_directory_filenames()

        await Gb.hass.async_add_executor_job(config_file.load_icloud3_configuration_file)

        start_ic3.set_log_level(Gb.log_level)
        await Gb.hass.async_add_executor_job(open_ic3log_file_init)

        # new_log_file = Gb.log_debug_flag
        # await Gb.hass.async_add_executor_job(open_ic3log_file, new_log_file)

        Gb.evlog_btnconfig_url = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.evlog_version       = Gb.conf_profile['event_log_version']
        Gb.EvLog               = event_log.EventLog(Gb.hass)

        Gb.EvLog.post_event(
                f"{EVLOG_IC3_STARTING}Loading > {ICLOUD3_VERSION_MSG}, "
                f"{dt_util.now().strftime('%A, %b %d')}")

        Gb.HALogger.info(f"Setting up {ICLOUD3_VERSION_MSG}{VERSION_BETA}")
        log_info_msg(f"Setting up {ICLOUD3} v{VERSION}{VERSION_BETA}")

        if Gb.restart_ha_flag:
            log_error_msg("iCloud3 > Waiting for HA restart to remove legacy \
                            devices before continuing")
            return False

        await async_get_ha_location_info(hass)
        start_ic3.initialize_data_source_variables()
        await Gb.hass.async_add_executor_job(restore_state.load_icloud3_restore_state_file)


        # config_file.count_lines_of_code(Gb.icloud3_directory)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        try:
            # _log(f"{Gb.hass.data['lovelace']=}")
            pass

        except Exception as err:
            log_exception(err)
        #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        Gb.EvLog.display_user_message(f"Starting {ICLOUD3_VERSION_MSG}")
        calculate_time_zone_offset()
        Gb.PyiCloudValidateAppleAcct = PyiCloudValidateAppleAcct()
        Gb.username_valid_by_username = {}
        if Gb.use_data_source_ICLOUD:
            # v3.0 --> v3.1 file location change
            if Gb.conf_tracking['setup_icloud_session_early']:
                await Gb.hass.async_add_executor_job(move_icloud_cookies_to_icloud3_apple_acct)
                await Gb.hass.async_add_executor_job(pyicloud_ic3_interface.check_all_apple_accts_valid_upw)

        # Create device_tracker entities if devices have been configure
        # Otherwise, this is done in config_flow when the first device is set up
        if Gb.conf_devices != []:
            await Gb.hass.config_entries.async_forward_entry_setups(
                                entry,
                                ['device_tracker'])

        # Create sensor entities
        await Gb.hass.config_entries.async_forward_entry_setups(
                                entry,
                                ['sensor'])

        # Do not start if loading/initialization failed
        if successful_startup is False:
            log_error_msg(
                    f"iCloud3 Initialization Failed, configuration file "
                    f"{Gb.icloud3_config_filename} failed to load.")
            log_error_msg("Verify the configuration file and delete it manually if necessary")
            return False

        Gb.EvLog.post_event(
                f"{EVLOG_IC3_STARTING}Starting > {ICLOUD3_VERSION_MSG}, "
                f"{dt_util.now().strftime('%A, %b %d')}")

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

    Gb.iCloud3  = iCloud3()

    # These will run concurrently while HA is starting everything else
    Gb.EvLog.post_event('Start HA Startup/Stop Listeners')
    Gb.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STARTED, start_ic3.ha_startup_completed)
    Gb.hass.bus.async_listen_once(
            EVENT_HOMEASSISTANT_STOP, start_ic3.ha_stopping)

    Gb.EvLog.post_event('Start iCloud3 Services Executor Job')
    Gb.hass.async_add_executor_job(register_icloud3_services)

    Gb.initial_icloud3_loading_flag = True
    log_debug_msg('START iCloud3 Initial Load Executor Job (iCloud3.start_icloud3)')

    icloud3_started = await Gb.hass.async_add_executor_job(Gb.iCloud3.start_icloud3)

    if icloud3_started:
        log_info_msg(f"{ICLOUD3_VERSION_MSG} Startup Complete")
        Gb.HALogger.info(f"Setting up {ICLOUD3_VERSION_MSG}, Complete")
    else:
        log_error_msg(f"{ICLOUD3_VERSION_MSG} Initialization Failed")
        Gb.HALogger.info(f"Setting up {ICLOUD3_VERSION_MSG}, Failed")

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

#-------------------------------------------------------------------------------------------
def move_icloud_cookies_to_icloud3_apple_acct():
    '''
    iCloud3 v3.1 uses the '.../apple_acct.ic3' cookie directory instead of the '.../icloud'
    directory to avoid conflicts with Apple Account integrations (iCloud, HomeKit, etc)

    Rename the '.../icloud' cookie directory to '.../apple_acct.ic3' if the old
    '.../icloud/session/username.tpw' file exists (this is unique to iCloud3).

    if the '.../icloapple_acct.ic3/' directory does not exist. create it.
    '''
    try:

        v31_cookie_dir = f"{Gb.icloud_cookie_directory}"
        v31_cookie_dir_exists = directory_exists(v31_cookie_dir)
        if v31_cookie_dir_exists:
            return

        make_directory(v31_cookie_dir)
        v30_cookie_dir = Gb.hass.config.path(Gb.ha_storage_directory, 'icloud')
        v30_cookie_dir_exists = directory_exists(v30_cookie_dir)
        Gb.HALogger.info(f"{v30_cookie_dir=} {v30_cookie_dir_exists=}")

        if v30_cookie_dir_exists is False:
            return

        username, _password, _locate_all = config_file.apple_acct_username_password(0)
        if username == "":
            return

        cookie_filename = "".join([c for c in username if match(r"\w", c)])
        Gb.HALogger.info(f"{cookie_filename=}")

        v30_cookie_filename     = f"{v30_cookie_dir}/{cookie_filename}"
        v30_cookie_tpw_filename = f"{v30_cookie_dir}/session/{cookie_filename}.tpw"
        v30_session_filename    = f"{v30_cookie_dir}/session/{cookie_filename}"
        v30_tpw_file_exists     = directory_exists(v30_cookie_tpw_filename)
        v31_cookie_filename     = f"{v31_cookie_dir}/{cookie_filename}"
        v31_cookie_tpw_filename = f"{v31_cookie_dir}/{cookie_filename}.tpw"
        v31_session_filename    = f"{v31_cookie_dir}/{cookie_filename}.session"

        Gb.HALogger.info(f"{v30_cookie_filename =}")
        Gb.HALogger.info(f"{v30_cookie_tpw_filename =}")
        Gb.HALogger.info(f"{v30_session_filename=}")

        if v30_tpw_file_exists is False:
            return

        Gb.HALogger.info(f"{v30_cookie_filename} --> {v31_session_filename}")
        data = read_json_file(v30_session_filename)
        save_json_file(v31_session_filename, data)

        Gb.HALogger.info(f"{v30_cookie_tpw_filename} --> {v31_cookie_tpw_filename}")
        data = read_json_file(v30_cookie_tpw_filename)
        save_json_file(v31_cookie_tpw_filename, data)

        Gb.HALogger.info(f"{v30_cookie_filename} --> {v31_cookie_filename}")
        with open(v30_cookie_filename, 'r') as v30_file:
            data = v30_file.read()

        with open(v31_cookie_filename, 'w') as v31_file:
            v31_file.write(data)

        post_monitor_msg(f"Cookie Directory > Directory and files were copied "
                        f"from `{v30_cookie_dir}` to `{v31_cookie_dir}`")

    except Exception as err:
        log_exception(err)
        pass

#-------------------------------------------------------------------------------------------
# def set_up_default_area_id():
    # Get Personal Devices area id
    # area_reg = ar.async_get(hass)
    # if Gb.conf_devices == []:
    #     area_data = area_reg.async_get_or_create('Personal Device')
    # else:
    #     area_data = area_reg.async_get_area_by_name('Personal Device')
    # Gb.area_id_personal_device = area_data.id if area_data else None
