

from ..global_variables import GlobalVariables as Gb
from ..const            import (ICLOUD3, DOMAIN,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT,
                                HOME, ERROR, NONE_FNAME,
                                STATE_TO_ZONE_BASE, CMD_RESET_PYICLOUD_SESSION,
                                EVLOG_ALERT, EVLOG_ATTENTION, EVLOG_NOTICE, EVLOG_IC3_STAGE_HDR,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                CIRCLE_LETTERS_DARK,
                                EVENT_RECDS_MAX_CNT_BASE, EVENT_RECDS_MAX_CNT_ZONE,
                                ALERTS_SENSOR_ATTRS,
                                CRLF, CRLF_DOT, CRLF_CHK, CRLF_SP3_DOT, HDOT, CRLF_SP5_DOT, CRLF_HDOT, LINK, LLINK, RLINK, CRLF_CIRCLE_X, CIRCLE_X,
                                CRLF_SP3_HDOT, CRLF_INDENT, CRLF_X, CRLF_TAB, DOT, CRLF_SP8_HDOT, CRLF_SP8_DOT,
                                CRLF_RED_X, RED_X, CRLF_RED_ALERT, CRLF_RED_ALERT2, RED_ALERT, CRLF_RED_MARK, CRLF_STAR,
                                CRLF_RED_ALERT, RED_ALERT, YELLOW_ALERT, UNKNOWN, INACTIVE_SYMB,
                                RARROW, NBSP2, NBSP4, NBSP6, CIRCLE_STAR, INFO_SEPARATOR, DASH_20, CHECK_MARK,
                                ICLOUD, FAMSHR,
                                DEVICE_TYPE_DN, DEVICE_TYPE_DNS,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS, MAC, IPAD_CELL, WATCH_WIFI, OTHER,
                                IPHONE_DN, IPAD_DN, IPOD_DN, WATCH_DN, AIRPODS_DN, MAC_DN,
                                MOBAPP, NO_MOBAPP,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODE_DN,
                                NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
                                LATITUDE, RADIUS,
                                TRIGGER,
                                ZONE, ID,
                                BATTERY_LEVEL, BATTERY_STATUS,
                                CONF_ENCODE_PASSWORD,
                                CONF_VERSION,  CONF_VERSION_INSTALL_DATE,
                                CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM, CONF_EVLOG_BTNCONFIG_URL,
                                PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                CONF_APPLE_ACCOUNT, CONF_USERNAME, CONF_PASSWORD,
                                CONF_DATA_SOURCE, CONF_LOCATE_ALL, CONF_SERVER_LOCATION,
                                CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_INZONE_INTERVALS, CONF_TRACK_FROM_ZONES,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                CONF_MOBAPP_ALIVE_INTERVAL, CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD,
                                CONF_OLD_LOCATION_ADJUSTMENT,
                                CONF_TFZ_TRACKING_MAX_DISTANCE,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_TRAVEL_TIME_FACTOR, CONF_PASSTHRU_ZONE_TIME, CONF_DISTANCE_BETWEEN_DEVICES,
                                CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_DESC,
                                CONF_DISPLAY_GPS_LAT_LONG, CONF_PASSWORD_SRP_ENABLED,
                                CONF_CENTER_IN_ZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE,
                                CONF_STAT_ZONE_BASE_LONGITUDE, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_AADEV_NAME,
                                CONF_AADEV_DEVICE_ID,
                                CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_ZONE, CONF_NAME, CONF_ANALYTICS_ENABLED,
                                DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                                )

from ..utils                import entity_io
from ..utils.utils          import (instr, is_empty, isnot_empty, yes_no, circle_letter, zone_dname,
                                    is_statzone, isnot_statzone, username_id,
                                    list_to_str, list_add, list_del, list_keys, list_sort,
                                    dict_del, dict_sort, )
from ..utils.messaging      import (broadcast_info_msg, add_log_file_filter,
                                    post_event, post_alert, post_greenbar_msg, post_dotted_line,
                                    post_error_msg, post_monitor_msg, update_alert_sensor,
                                    post_repair_issue, clear_repair_issues, register_repair_fix_handler,
                                    post_internal_error,
                                    log_info_msg, log_error_msg, log_warning_msg,
                                    log_data, log_exception, format_filename, log_stack,
                                    internal_error_msg2, close_ic3log_file,
                                    _evlog, _log, more_info,)
from ..utils.dist_util      import (format_dist_km, m_to_um, )
from ..utils.time_util      import (time_now_secs, format_timer,
                                    secs_to_hhmm, secs_to_time, )
from ..utils                import entity_reg_util as er_util
from ..utils.file_io        import (directory_exists, make_directory,  copy_file,
                                    get_filename_list, get_directory_filename_list,)

from ..apple_acct           import apple_acct_support as aas
from ..apple_acct           import apple_acct_support_cf as aascf
from ..apple_acct.apple_acct_upw import ValidateAppleAcctUPW
from ..device               import iCloud3_Device
from ..mobile_app           import mobapp_interface
from ..mobile_app           import mobapp_data_handler
from ..startup              import config_file
from .mobapp_resolver       import (AMBIGUOUS, DISABLED, RENAMED, RESERVED,
                                    resolve_mobapp_dname, )
from ..support              import service_handler
from ..tracking             import zone_handler
from ..tracking.waze        import Waze
from ..tracking.waze_history import WazeRouteHistory as WazeHist

from ..zone                 import iCloud3_Zone

#--------------------------------------------------------------------
from collections           import OrderedDict
from homeassistant.helpers import event
from homeassistant.util    import slugify


import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger(DOMAIN)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- INITIALIZATION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def initialize_directory_filenames():
    """ Set up common directories and file names """


    # icloud3_config_dir                = f"{DOMAIN}.config"
    icloud3_config_dir                = f"{DOMAIN}"
    Gb.ha_config_directory            = Gb.hass.config.path()
    Gb.ha_storage_directory           = Gb.hass.config.path(STORAGE_DIR)
    Gb.ha_storage_icloud3             = Gb.hass.config.path(STORAGE_DIR, icloud3_config_dir)
    Gb.icloud3_config_filename        = Gb.hass.config.path(STORAGE_DIR, icloud3_config_dir, 'configuration')
    Gb.icloud3_restore_state_filename = Gb.hass.config.path(STORAGE_DIR, icloud3_config_dir, 'restore_state')
    Gb.wazehist_database_filename     = Gb.hass.config.path(STORAGE_DIR, icloud3_config_dir, 'waze_location_history.db')
    Gb.icloud3_directory              = Gb.hass.config.path('custom_components', DOMAIN)
    Gb.entity_registry_file           = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY)
    Gb.icloud_cookies_directory        = Gb.hass.config.path(STORAGE_DIR, 'icloud3.apple_acct')
    Gb.icloud_session_directory       = Gb.hass.config.path(STORAGE_DIR, 'icloud3.apple_acct')

    # Note: The Event Log  directory & filename are initialized in config_file.py
    # after the configuration file has been read

#------------------------------------------------------------------------------
#
#   ICLOUD3 CONFIGURATION PARAMETERS WERE UPDATED VIA CONFIG_FLOW
#
#   Determine the type of parameters that were updated and reset the variables or
#   devices based on the type of changes.
#
#------------------------------------------------------------------------------
def handle_config_parms_update():

    # if is_empty(Gb.config_parms_update_control):
    #     return


    # Make copy and Reinitialize so it will not be run again from the 5-secs loop
    config_parms_update_control = Gb.config_parms_update_control.copy()
    Gb.config_parms_update_control = []

    post_event( f"Configuration Loading > "
                f"Type-{list_to_str(config_parms_update_control).title()}")

    if 'restart' in config_parms_update_control:
        post_greenbar_msg(f"Restarting iCloud3 {Gb.icloud3_version_msg}")
        Gb.EvLog.display_user_message('iCloud3 is Restarting')
        post_event(f"{EVLOG_ATTENTION}iCloud3 Restart Requested ({Gb.icloud3_version_msg})")
        initialize_data_source_variables()
        Gb.was_icloud3_restart_requested = True
        return

    post_event(f"{EVLOG_IC3_STAGE_HDR}")
    if 'general' in config_parms_update_control:
        set_global_variables_from_conf_parameters()

    if 'special_zone' in config_parms_update_control:
        set_zone_display_as()

    if 'evlog' in config_parms_update_control:
        post_event('Processing Event Log Settings Update')
        Gb.evlog_btnconfig_url = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        # This runs in the 5-second executor thread. loop.create_task() is not
        # thread-safe and raises RuntimeError there, which also skipped the
        # remaining configuration branches below.
        Gb.hass.add_job(update_lovelace_resource_event_log_js_entry)
        # Gb.hass.async_add_executor_job(update_lovelace_resource_event_log_js_entry)
        check_ic3_event_log_file_version()
        Gb.EvLog.setup_event_log_trackable_device_info()

    if 'reauth' in config_parms_update_control:
        Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION

    if 'waze' in config_parms_update_control:
        set_waze_conf_parameters()

    if ('tracking' in config_parms_update_control
            or 'devices' in config_parms_update_control):
        post_event("Tracking parameters updated")
        initialize_data_source_variables()

    if 'devices' in config_parms_update_control:
        post_event("Device parameters updated")
        update_devices_non_tracked_fields()
        Gb.EvLog.setup_event_log_trackable_device_info()

        _refresh_all_devices_sensors()
        display_all_devices_config_info(config_parms_update_control)

        stage_title = f'Device Configuration Summary'
        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message('')

    post_event(f"{EVLOG_IC3_STAGE_HDR}Configuration Changes Applied")

#------------------------------------------------------------------------------
#
#   UPDATE LOVELACE RESOURCES FOR EVENT LOG CARD
#
#------------------------------------------------------------------------------
async def update_lovelace_resource_event_log_js_entry(_new_evlog_dir=None, silent=False):
    '''
    Check the lovelace resource for an icloud3_event-log-card.js entry.
    If found, it is already set up and there is nothing to do.
    If not found, add it to the lovelace resource so the user does not
        have to manually add it. The browser needs to be refreshed so also
        generate a broadcast message.

    Resources are stored as part of the StorageCollection:
        Resources object = Gb.hass.data["lovelace"].resources
        Add Resource    - Resources.async_create_item({'res_type': 'module', 'url': evlog_url})
        Update Resource - Resources.async_update_item(evlog_resource_id, {'url': evlog_url})
        Delete Resource - Resources.async_delete_item((evlog_resource_id)
    '''
    try:
        Resources = None
        try:
            Resources = Gb.hass.data['lovelace'].resources
        except Exception as err:
            post_alert( f"iCLOUD3 LOVELACE RESOURCES SETUP ERROR > "
                        f"Lovelace has not been set up. iCloud3 can not set up the "
                        f"Lovelace Resource for the Event-Log-Card")
            log_exception(err)
            return

        if Resources is None:
            return

        if Resources.loaded is False:
            await Resources.async_load()
            Resources.loaded = True

        evlog_url =(f"{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}/"
                    f"{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}")
        evlog_url = evlog_url.replace('www', '/local')
        evlog_url = evlog_url.replace('/local//local', '/local')
        evlog_resource_id = None

        for item in Resources.async_items():
            # EvLog is in resources, nothing to do
            if item['url'] == evlog_url:
                return

            # EvLog is in resources but in another directory
            if (item['url'].endswith(Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])
                    and item['url'] != evlog_url):
                evlog_resource_id = item['id']
                evlog_url_old = item['url']
                break

        update_msg = ''
        # Update the existing entry
        if evlog_resource_id:
            await Resources.async_update_item(evlog_resource_id, {'url': evlog_url})
            update_msg=(f"{CRLF}From: {evlog_url_old}"
                        f"{CRLF}To....: {evlog_url}")

        # Add to the Resources list
        else:
            await Resources.async_create_item({'res_type': 'module', 'url': evlog_url, })
            update_msg = f"{CRLF}Added: {evlog_url}"

        # Resources.loaded = False
        await Resources.async_load()
        Resources.loaded = True

        if silent is False:
            post_alert( f"LOVELACE RESOURCES UPDATED > "
                        f"{update_msg}")

            title       = 'Action Required - Clear Browser Cache'
            message     = (f'The Event Log Custom Card was added to the Lovelace Resource list.'
                        f'<br>Fil{evlog_url}*'
                        f'<br><br>Clear the browser cache before adding the Event Log Card'
                        f'<br>1. Press Ctrl+Shift+Del'
                        f'<br>2. On the Settings tab, check Clear Images and Files'
                        f'<br>3. Click Clear Data/Clear Now'
                        f'<br>4. Select the Home Assistant tab, then Refresh the display')
            service_handler.set_ha_notification(title, message, issue=False)

    except Exception as err:
        log_exception(err)
        log_error_msg(  "iCloud3 > An unknown error was encountered updating the Lovelace "
                        "Resources. Lovelace probably has not finished loading or is not "
                        "available. The Lovelace for the iCloud3 Event Log card will have to "
                        "be done manually. ")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 0
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   VARIABLE DEFINITION & INITIALIZATION FUNCTIONS
#
#------------------------------------------------------------------------------
def define_tracking_control_fields():
    Gb.trigger                         = {}       #device update trigger
    Gb.info_notification               = ''
    Gb.broadcast_msg                   = ''

#------------------------------------------------------------------------------
#
#   SET GLOBAL VARIABLES BACK TO THEIR INITIAL CONDITION
#
#------------------------------------------------------------------------------
def initialize_global_variables():

    # Configuration parameters that can be changed in config_ic3.yaml
    Gb.um                           = DEFAULT_GENERAL_CONF[CONF_UNIT_OF_MEASUREMENT]
    Gb.time_format_12_hour          = True
    Gb.time_format_24_hour          = False
    Gb.um_km_mi_factor              = .62137
    Gb.um_m_ft                      = 'ft'
    Gb.um_kph_mph                   = 'mph'
    Gb.um_time_strfmt               = '%I:%M:%S'
    Gb.um_time_strfmt_ampm          = '%I:%M:%S%P'
    Gb.um_date_time_strfmt          = '%Y-%m-%d %H:%M:%S'

    # Configuration parameters
    Gb.device_tracker_state_source  = DEFAULT_GENERAL_CONF[CONF_DEVICE_TRACKER_STATE_SOURCE]
    Gb.is_loc_centered_in_zone      = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    Gb.display_zone_format          = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    Gb.is_gps_lat_long_displayed    = DEFAULT_GENERAL_CONF[CONF_DISPLAY_GPS_LAT_LONG]
    Gb.max_interval_secs            = DEFAULT_GENERAL_CONF[CONF_MAX_INTERVAL] * 60
    Gb.offline_interval_secs        = DEFAULT_GENERAL_CONF[CONF_OFFLINE_INTERVAL] * 60
    Gb.exit_zone_interval_secs      = DEFAULT_GENERAL_CONF[CONF_EXIT_ZONE_INTERVAL] * 60
    Gb.mobapp_alive_interval_secs   = DEFAULT_GENERAL_CONF[CONF_MOBAPP_ALIVE_INTERVAL] * 3600
    Gb.travel_time_factor           = DEFAULT_GENERAL_CONF[CONF_TRAVEL_TIME_FACTOR]
    Gb.is_track_from_base_zone_used = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE_USED]
    Gb.track_from_base_zone         = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE]
    Gb.track_from_home_zone         = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_HOME_ZONE]
    Gb.gps_accuracy_threshold       = DEFAULT_GENERAL_CONF[CONF_GPS_ACCURACY_THRESHOLD]
    Gb.old_location_threshold       = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_THRESHOLD] * 60
    Gb.old_location_adjustment      = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_ADJUSTMENT] * 60
    # Gb.password_srp_enabled         = DEFAULT_TRACKING_CONF[CONF_PASSWORD_SRP_ENABLED]

    Gb.tfz_tracking_max_distance    = DEFAULT_GENERAL_CONF[CONF_TFZ_TRACKING_MAX_DISTANCE]

    Gb.is_waze_dist_method_used    = True
    Gb.waze_region                  = DEFAULT_GENERAL_CONF[CONF_WAZE_REGION]
    Gb.waze_max_distance            = DEFAULT_GENERAL_CONF[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance            = DEFAULT_GENERAL_CONF[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime                = DEFAULT_GENERAL_CONF[CONF_WAZE_REALTIME]
    Gb.waze_history_database_used   = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_DATABASE_USED]
    Gb.waze_history_max_distance    = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_track_direction = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    # Tracking method control vaiables
    # Used to reset Gb.primary_data_source after pyicloud/icloud account successful reset
    # Will be changed to MOBAPP if pyicloud errors
    Gb.data_source_ICLOUD           = False
    Gb.data_source_MOBAPP           = False
    Gb.used_data_source_ICLOUD      = False
    Gb.used_data_source_MOBAPP      = False
    Gb.any_data_source_MOBAPP_none  = False

    Gb.alerts_sensor        = 'none'
    Gb.alerts_sensor_attrs  = {}
    Gb.icloud3_reload_requested      = False

    initialize_on_initial_load()

#------------------------------------------------------------------------------
def initialize_on_initial_load():
    # Initialize these variables only when starting up
    # Do not initialize them on a restart

    if Gb.is_icloud3_initial_startup is False:
        return

    Gb.log_level = 'info'

#------------------------------------------------------------------------------
#
#   INITIALIZE THE GLOBAL VARIABLES WITH THE CONFIGURATION FILE PARAMETER
#   VALUES
#
#------------------------------------------------------------------------------
def set_global_variables_from_conf_parameters(evlog_msg=True):
    '''
    Set the iCloud3 variables from the configuration parameters
    '''

    try:
        config_evlog_msg = "Configure iCloud3 Operations >"
        config_evlog_msg += f"{CRLF_DOT}Load configuration parameters"

        initialize_data_source_variables()
        Gb.InternetError.reset_internet_error()

        Gb.www_evlog_js_directory       = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
        Gb.www_evlog_js_filename        = Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]
        Gb.evlog_btnconfig_url          = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.evlog_version                = Gb.conf_profile['event_log_version']
        if Gb.www_evlog_js_directory not in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
            list_add(Gb.conf_profile[CONF_PICTURE_WWW_DIRS], Gb.www_evlog_js_directory)
        Gb.picture_www_dirs             = Gb.conf_profile[CONF_PICTURE_WWW_DIRS]

        Gb.password_srp_enabled         = Gb.conf_tracking[CONF_PASSWORD_SRP_ENABLED]

        Gb.um                           = Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]
        Gb.time_format_12_hour          = Gb.conf_general[CONF_TIME_FORMAT].startswith('12')
        Gb.time_format_24_hour          = not Gb.time_format_12_hour
        Gb.device_tracker_state_source  = Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE]
        Gb.display_zone_format          = Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]
        Gb.is_gps_lat_long_displayed    = Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]
        Gb.is_loc_centered_in_zone      = Gb.conf_general[CONF_CENTER_IN_ZONE]
        Gb.max_interval_secs            = Gb.conf_general[CONF_MAX_INTERVAL] * 60
        Gb.exit_zone_interval_secs      = Gb.conf_general[CONF_EXIT_ZONE_INTERVAL] * 60
        Gb.offline_interval_secs        = Gb.conf_general[CONF_OFFLINE_INTERVAL] * 60
        Gb.mobapp_alive_interval_secs   = Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL] * 3600
        Gb.travel_time_factor           = Gb.conf_general[CONF_TRAVEL_TIME_FACTOR]
        Gb.passthru_zone_interval_secs  = Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] * 60
        Gb.is_passthru_zone_used        = (14400 > Gb.passthru_zone_interval_secs > 0)   # time > 0 and < 4 hrs
        Gb.old_location_threshold       = Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD] * 60
        Gb.old_location_adjustment      = Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT] * 60
        Gb.is_track_from_base_zone_used = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]
        Gb.track_from_base_zone         = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE]
        Gb.track_from_home_zone         = Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]
        Gb.gps_accuracy_threshold       = Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]
        Gb.is_poor_gps_inzone_discarded = Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]
        Gb.is_dist_between_devices_calc = Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]

        Gb.tfz_tracking_max_distance   = Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]
        Gb.monitored_devices_location_sensors_flag = 'md_location_sensors' in Gb.conf_sensors['monitored_devices']

        # Setup the Stationary Zone location and times
        # The stat_zone_base_lat/long will be adjusted after the Home zone is set up
        Gb.statzone_fname                 = Gb.conf_general[CONF_STAT_ZONE_FNAME].strip()
        Gb.statzone_still_time_secs       = Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] * 60
        Gb.statzone_inzone_interval_secs  = Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] * 60
        Gb.is_statzone_used               = (14400 > Gb.statzone_still_time_secs > 0)

        # Away Time Zone offset
        Gb.away_time_zone_1_offset        = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]
        Gb.away_time_zone_1_devices       = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES].copy()
        Gb.away_time_zone_2_offset        = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]
        Gb.away_time_zone_2_devices       = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES].copy()

        Gb.analytics_enabled              = Gb.conf_general[CONF_ANALYTICS_ENABLED]
        Gb.log_level                      = Gb.conf_general[CONF_LOG_LEVEL]
        Gb.log_level_devices              = Gb.conf_general[CONF_LOG_LEVEL_DEVICES]

        # update the interval time for each of the interval types (i.e., ipad: 2 hrs, no_mobapp: 15 min)
        inzone_intervals                    = Gb.conf_general[CONF_INZONE_INTERVALS]
        Gb.inzone_interval_secs = {}
        Gb.inzone_interval_secs[IPHONE]     = inzone_intervals[IPHONE] * 60
        Gb.inzone_interval_secs[IPAD]       = inzone_intervals[IPAD] * 60
        Gb.inzone_interval_secs[IPAD_CELL]  = inzone_intervals[IPAD_CELL] * 60
        Gb.inzone_interval_secs[WATCH]      = inzone_intervals[WATCH] * 60
        Gb.inzone_interval_secs[WATCH_WIFI] = inzone_intervals[WATCH_WIFI] * 60
        Gb.inzone_interval_secs[MAC]        = inzone_intervals[MAC] * 60
        Gb.inzone_interval_secs[AIRPODS]    = inzone_intervals[AIRPODS] * 60
        Gb.inzone_interval_secs[NO_MOBAPP]  = inzone_intervals[NO_MOBAPP] * 60
        Gb.inzone_interval_secs[OTHER]      = inzone_intervals[OTHER] * 60
        Gb.inzone_interval_secs[CONF_INZONE_INTERVAL] = inzone_intervals[OTHER] * 60

        Gb.EvLog.display_text_as = {}
        for display_text_as in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
            if instr(display_text_as, '>'):
                from_to_text = display_text_as.split('>')
                Gb.EvLog.display_text_as[from_to_text[0].strip()] = from_to_text[1].strip()
        config_evlog_msg += f"{CRLF_DOT}Set Display Text As Fields ({len(Gb.EvLog.display_text_as)} used)"

        set_waze_conf_parameters()

        # Set other fields and flags based on configuration parameters
        set_primary_data_source(Gb.primary_data_source)
        config_evlog_msg += (   f"{CRLF_DOT}Set Default Tracking Method "
                                f"({Gb.primary_data_source})")

        set_log_level(Gb.log_level)

        config_evlog_msg += f"{CRLF_DOT}Initialize Debug Control ({Gb.log_level})"


        set_um_formats()
        config_evlog_msg += f"{CRLF_DOT}Set Unit of Measure Formats ({Gb.um})"

        event_recds_max_cnt = set_event_recds_max_cnt()
        config_evlog_msg += f"{CRLF_DOT}Set Event Log Record Limits ({event_recds_max_cnt} Events)"

        config_evlog_msg += f"{CRLF_DOT}Device Tracker State Value Source "
        etds = Gb.device_tracker_state_source
        config_evlog_msg += f"{CRLF_INDENT}({DEVICE_TRACKER_STATE_SOURCE_DESC.get(etds, etds)})"

        if evlog_msg:
            post_event(config_evlog_msg)

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
#
#   HOMEASSISTANT STARTED EVENT
#
#   This is fired when Home Assistant is started and is used to complete any
#   setup tasks that were not completed since iCloud3 can start before HA
#   startup is complete.
#
#------------------------------------------------------------------------------
def ha_startup_completed(_dummy_parameter):

    # HA may have not set up the notify service before iC3 starts. If so, the mobile_app
    # Notify entity was not setup either. Do it now.
    Gb.ha_started = True
    mobapp_interface.get_mobile_app_integration_device_info(ha_started_check=True)
    mobapp_interface.setup_notify_service_name_for_mobapp_devices()

#------------------------------------------------------------------------------
def ha_stopping(_dummy_parameter):
    post_event("HA Shutting Down")
    Gb.EvLog.display_user_message("HA Shutting Down")
    close_ic3log_file()

#------------------------------------------------------------------------------
def ha_restart(_dummy_parameter):
    Gb.hass.services.call("homeassistant", "restart")

#------------------------------------------------------------------------------
#
#   SET THE GLOBAL DATA SOURCES
#
#   This is used during the startup routines and in other routines when errors occur.
#
#------------------------------------------------------------------------------
def initialize_data_source_variables():
    '''
    Set up icloud username/password and devices from the configuration parameters
    '''
    # username, password, locate_all = \
    #         config_file.apple_acct_username_password(0)
    conf_apple_acct, _idx = config_file.conf_apple_acct(0)
    conf_username = conf_apple_acct[CONF_USERNAME]
    conf_password = conf_apple_acct[CONF_PASSWORD]

    Gb.username                     = conf_username
    Gb.username_base                = username_id(Gb.username)
    Gb.password                     = conf_password
    Gb.is_password_encoded         = Gb.conf_tracking[CONF_ENCODE_PASSWORD]

    Gb.AppleAcct_logging_in_usernames= []

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'mobapp'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP)

    Gb.conf_data_source_ICLOUD    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)
    # Gb.conf_data_source_ICLOUD    = Gb.conf_data_source_ICLOUD
    Gb.conf_data_source_MOBAPP    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)

    Gb.use_data_source_ICLOUD     = (Gb.conf_data_source_ICLOUD and Gb.username != '' and Gb.password != '')
    Gb.use_data_source_MOBAPP     = Gb.conf_data_source_MOBAPP
    Gb.primary_data_source        = ICLOUD if Gb.use_data_source_ICLOUD else MOBAPP

    Gb.devices                    = Gb.conf_devices
    Gb.is_force_icloud_update     = False
    Gb.get_ICLOUD_devices_retry_cnt = 0

#------------------------------------------------------------------------------
def set_primary_data_source(data_source):
    '''
    Set up tracking method. These fields will be reset based on the device_id's available
    for the Device once the icloud tracking method is set up.
    '''

    if (Gb.conf_profile[CONF_VERSION] > 0
            and Gb.use_data_source_ICLOUD
            and (Gb.username == '' or Gb.password == '')):
        alert_msg =("ICLOUD USERNAME-PASSWORD ERROR > The username or password has not "
                    "been set up, iCloud Location Services will not be used. ")

        if Gb.conf_data_source_MOBAPP:
            data_source = MOBAPP
            alert_msg += "Device tracking will be done using Mobile App location data. "
        else:
            data_source = ''
            post_greenbar_msg('No data sources have been set up')
            alert_msg += "No data sources have been set up, tracking will not be done."
            error_msg = ("iCloud3 Error > Devices will not be tracked. Location data "
                        "has not been set up")
            post_error_msg(error_msg)
        post_alert(alert_msg)

    if data_source in [ICLOUD]:
        Gb.use_data_source_ICLOUD = Gb.conf_data_source_ICLOUD

#------------------------------------------------------------------------------
#
#   INITIALIZE THE UNIT_OF_MEASURE FIELDS
#
#------------------------------------------------------------------------------
def set_um_formats():
    #Define variables, lists & tables
    Gb.um_MI = (Gb.um == 'mi')
    Gb.um_KM = not Gb.um_MI

    if Gb.um_MI:
        Gb.um_km_mi_factor = 0.62137
        Gb.um_m_ft         = 'ft'
        Gb.um_kph_mph      = 'mph'
    else:
        Gb.um_km_mi_factor = 1
        Gb.um_m_ft         = 'm'
        Gb.um_kph_mph      = 'kph'

    if Gb.time_format_12_hour:
        Gb.um_time_strfmt       = '%I:%M:%S'
        Gb.um_time_strfmt_ampm  = '%I:%M:%S%P'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %I:%M:%S'
        Gb.um_day_date_time_srtfmt = '%a, %b %-d, %-I:%M:%S %p'
    else:
        Gb.um_time_strfmt       = '%H:%M:%S'
        Gb.um_time_strfmt_ampm  = '%H:%M:%S'
        Gb.um_date_time_strfmt  = '%Y-%m-%d %H:%M:%S'
        Gb.um_day_date_time_srtfmt = '%a, %b %-d, %H:%M:%S'

#------------------------------------------------------------------------------
def set_event_recds_max_cnt():
    '''
    Set te initial Event Log Table Record Limit. This will be updated after the devices
    are initialized and the Event Log attributes are then reset.
    '''
    event_recds_max_cnt = EVENT_RECDS_MAX_CNT_BASE
    for conf_device in Gb.conf_devices:
        event_recds_max_cnt += \
                EVENT_RECDS_MAX_CNT_ZONE*len(conf_device[CONF_TRACK_FROM_ZONES])

    if event_recds_max_cnt > Gb.EvLog.event_recds_max_cnt:
        Gb.EvLog.event_recds_max_cnt = event_recds_max_cnt
    return Gb.EvLog.event_recds_max_cnt

#------------------------------------------------------------------------------
#
#   INITIALIZE THE DEBUG CONTROL FLAGS
#
#   Decode the log_level: debug parameter
#      debug            - log 'debug' messages to the log file under the 'info' type
#      debug_rawdata    - log data read from records to the log file
#      eventlog         - Add debug items to ic3 event log
#      debug+eventlog   - Add debug items to HA log file and ic3 event log
#
#------------------------------------------------------------------------------
def set_log_level(log_level):

    log_level = log_level.lower()

    # Log level can be set on Event Log > Actions in service_handler.py which overrides
    # the configuration/log_level parameter. The current log_level is preserved in the
    # log_debug/rawdata_flag _restart in service_handler (Restart) to reassign any log
    # level overrides on an iC3 restart

    Gb.is_log_level_debug   = instr(log_level, 'debug')
    Gb.is_log_level_rawdata = instr(log_level, 'rawdata')
    Gb.is_log_level_rawdata_unfiltered = instr(log_level, 'unfiltered')
    Gb.is_log_level_rawdata = Gb.is_log_level_rawdata or Gb.is_log_level_rawdata_unfiltered
    Gb.is_log_level_debug   = Gb.is_log_level_debug or Gb.is_log_level_rawdata
    Gb.is_evlog_trk_monitors_displayed = Gb.is_evlog_trk_monitors_displayed or instr(log_level, 'eventlog')

    if Gb.iC3Logger:
        Gb.iC3Logger.propagate = (Gb.conf_general[CONF_LOG_LEVEL] == 'debug-ha')

#------------------------------------------------------------------------------
def update_conf_file_log_level(log_level):
    Gb.conf_general[CONF_LOG_LEVEL] = log_level
    config_file.write_icloud3_configuration_file()

#------------------------------------------------------------------------------
#
#   Initialize the Waze parameters
#
#------------------------------------------------------------------------------
def set_waze_conf_parameters():
    Gb.waze_max_distance = Gb.conf_general[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance = Gb.conf_general[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime     = Gb.conf_general[CONF_WAZE_REALTIME]
    Gb.waze_region       = Gb.conf_general[CONF_WAZE_REGION]

    Gb.is_waze_dist_method_used = Gb.conf_general[CONF_WAZE_USED]
    if Gb.is_waze_dist_method_used is False:
        Gb.waze_history_database_used = False
    else:
        Gb.waze_history_database_used = Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED]

    Gb.waze_history_max_distance    = Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_track_direction = Gb.conf_general[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    # Update Waze & WazeHist with updated parameters
    create_Waze_object()

    if Gb.WazeHist:
        if Gb.waze_history_database_used and Gb.WazeHist.connection is None:
            Gb.WazeHist.open_waze_history_database()
        if Gb.waze_history_database_used is False and Gb.WazeHist.connection:
            Gb.WazeHist.close_waze_history_database()

#------------------------------------------------------------------------------
def set_zone_display_as():
    '''
    Set the zone display_as config format. Refresh the display_as for each zone if the
    config format value changed. But don't do this on the initial load. It will be
    done when the zone is created.

    '''

    if Gb.is_icloud3_initial_startup:
        return

    zone_msg = ''
    Gb.zones_dname = NON_ZONE_ITEM_LIST.copy()

    # Update any regular zones with any fname/display_as changes
    for zone, Zone in Gb.HAZones_by_zone.items():
        if Zone.is_statzone:
            continue

        Zone.setup_zone_display_name()

        if Zone.radius_m > 1:
            if Zone.passive:
                crlf_dot_x = CRLF_X
                passive_msg = ', Passive Zone'
            else:
                crlf_dot_x = CRLF_DOT
                passive_msg = ''
            zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                        f"{Zone.dname} (r{Zone.radius_m}m){passive_msg}")

    # Update the Stationary Zone with any changes
    for StatZone in Gb.StatZones:
        crlf_dot_x = CRLF_X if StatZone.passive else CRLF_DOT
        zone_msg +=(f"{crlf_dot_x}{StatZone.zone}, "
                    f"{StatZone.dname} (r{StatZone.radius_m}m)")

    log_msg =  (f"Set up Zones > zone, Display ({Gb.display_zone_format})")
    post_event(f"{log_msg}{zone_msg}")

#------------------------------------------------------------------------------
#
#   LOAD HA CONFIGURATION.YAML FILE
#
#   Load the configuration.yaml file and save it's contents. This contains the default
#   parameter values used to reset the configuration when iCloud3 is restarted.
#
#   'load_ha_config_parameters' is run in device_tracker.__init__ when iCloud3 starts
#   'reinitialize_config_parameters' is run in device_tracker.start_icloud3 when iCloud3
#   starts or is restarted before the config_ic3.yaml parameter file is processed
#
#------------------------------------------------------------------------------
def load_ha_config_parameters(ha_config_yaml_and_defaults):
    Gb.config_parm_initial_load = {k:v for k, v in ha_config_yaml_and_defaults.items()}
    reinitialize_config_parameters()

def reinitialize_config_parameters():
    Gb.config_parm = Gb.config_parm_initial_load.copy()

#------------------------------------------------------------------------------
#
#   CHECK THE IC3 EVENT LOG VERSION BEING USED
#
#   Read the icloud3-event-log-card.js file in the iCloud3 directory and the
#   Lovelace Custom Card directory (default=www/custom_cards) and extract
#   the current version (Version=x.x.x (mm.dd.yyyy)) comment entry before
#   the first 'class' statement. If the version in the ic3 directory is
#   newer than the www/custom_cards directory, copy the ic3 version
#   to the www/custom_cards directory.
#
#   The custom_cards directory can be changed using the event_log_card_directory
#   parameter.
#
#------------------------------------------------------------------------------
def check_ic3_event_log_file_version():
    try:
        ic3_evlog_js_directory = Gb.hass.config.path(Gb.icloud3_directory, 'event_log_card')
        ic3_evlog_js_filename  = Gb.hass.config.path(Gb.icloud3_directory, 'event_log_card',
                                                        Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])
        www_evlog_js_directory = Gb.hass.config.path(Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY])
        www_evlog_js_filename  = Gb.hass.config.path(Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY],
                                                        Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])

        ic3_evlog_js_directory_msg = f"{DOMAIN}/event_log_card"
        ic3_evlog_js_filename_msg  = ic3_evlog_js_filename
        www_evlog_js_directory_msg = www_evlog_js_directory
        www_evlog_js_filename_msg  = www_evlog_js_filename

        ic3_version, ic3_beta_version, ic3_version_text = _read_event_log_card_js_file(ic3_evlog_js_filename)
        www_version, www_beta_version, www_version_text = _read_event_log_card_js_file(www_evlog_js_filename)

        if ic3_version_text == 'Not Installed':
            Gb.version_evlog = f' Not Found: {ic3_evlog_js_filename_msg}'
            event_msg =(f"{EVLOG_ALERT}iCloud3 Event Log > "
                        f"{CRLF_DOT}Current Version Installed-v{www_version_text}"
                        f"{CRLF_DOT}WARNING: SOURCE FILE NOT FOUND"
                        f"{CRLF_DOT}...{ic3_evlog_js_filename_msg}")
        else:
            Gb.version_evlog = ic3_version_text

        # Event log card is not in iCloud3 directory. Nothing to do.
        if ic3_version == 0:
            return

        # Event Log card does not exist in www directory. Copy it from iCloud3 directory
        # Make sure the /config/www and config/CONF_EVLOG_CARD_DIRECTORY exists. Create them if needed
        if www_version == 0:
            config_www_directory = Gb.hass.config.path('www')
            make_directory(config_www_directory)
            make_directory(www_evlog_js_directory)

        current_version_installed_flag = True
        if ic3_version > www_version:
            current_version_installed_flag = False
        elif ic3_version == www_version:
            if ic3_beta_version == 0:
                pass
            elif ic3_beta_version > www_beta_version:
                current_version_installed_flag = False

        if current_version_installed_flag:
            event_msg =(f"iCloud3 Event Log > "
                        f"{CRLF_DOT}Current Version Installed-v{www_version_text}"
                        f"{CRLF_DOT}File-{format_filename(www_evlog_js_filename_msg)}")
            # The _l is a html command and will stop the msg from displaying
            post_event(event_msg.replace('_', '_ '))

            if Gb.evlog_version != www_version_text:
                Gb.evlog_version = Gb.conf_profile['event_log_version'] = www_version_text
                config_file.write_icloud3_configuration_file()

            return

        try:
            _copy_image_files_to_www_directory(ic3_evlog_js_directory, www_evlog_js_directory)
            copy_file(ic3_evlog_js_filename, www_evlog_js_filename)

            Gb.evlog_version = Gb.conf_profile['event_log_version'] = www_version_text
            config_file.write_icloud3_configuration_file()

            post_greenbar_msg('Event Log was updated. Browser refresh needed')
            event_msg =(f"{EVLOG_ALERT}"
                        f"BROWSER REFRESH NEEDED > iCloud3 Event Log was updated to v{ic3_version_text}"
                        f"{more_info('refresh_browser')}"
                        f"{CRLF}{'-'*75}"
                        f"{CRLF_DOT}Old Version.. - v{www_version_text}"
                        f"{CRLF_DOT}New Version - v{ic3_version_text}"
                        f"{CRLF_DOT}Copied From - {format_filename(ic3_evlog_js_directory_msg)}/"
                        f"{CRLF_DOT}Copied To.... - {format_filename(www_evlog_js_directory_msg)}/")
            # The _l is a html command and will stop the msg from displaying
            post_event(event_msg.replace('_', '_ '))

            Gb.info_notification = (f"Event Log Card updated to v{ic3_version_text}. "
                        "See Event Log for more info.")
            title       = (f"iCloud3 Event Log Card updated to v{ic3_version_text}")
            message     = ("Refresh the Mobile App to load the new version. "
                        "Select HA Sidebar > APP Configuration. Scroll down. Select Refresh "
                        "Frontend Cache. Select Done. Pull down to refresh App.")
            Gb.broadcast_msg = {
                        "title": title,
                        "message": message,
                        "data": {"subtitle": "Event Log needs to be refreshed"}}

        except Exception as err:
            log_exception(err)

    except Exception as err:
        log_exception(err)

#------------------------------------------------------------------------------
def _read_event_log_card_js_file(evlog_filename):
    '''
    Read the records in the the evlog_filename extract the version in the record
    with the javascript 'const version' in it (const version = '3.1.28' or '3.1.28b1').

    Return:
        version - A numeric value of the version text (3.1.28 = 30128
        version_beta - Value after the 'b' or '' if not a beta
        version_beta_text - Value in the 'const version' statement

        0, 0, "Unknown" if the 'const version' was not found
        0, 0, "Not Installed" if the 'icloud3-event-log-card.js' file was not found
    '''
    try:
        if directory_exists(evlog_filename) == False:
            return (0, 0, 'Not Installed')

        #Cycle thru the file looking for the line with the 'const version'
        evlog_file = open(evlog_filename)

        recd_no = 0
        for evlog_recd in evlog_file:
            recd_no += 1

            if (instr(evlog_recd, 'const version')
                    or instr(evlog_recd, 'this._version')):
                break

            #exit if find 'class' recd before 'version' recd
            elif recd_no > 50:
                return (0, 0, ' Unknown')

        evlog_recd          = evlog_recd.replace(' ', '').replace('"','|').replace("'","|")
        version_number_beta = evlog_recd.split('|')[1]

        if instr(version_number_beta, 'b'):
            version_number      = version_number_beta.split('b')[0]
            version_beta        = int(version_number_beta.split('b')[1])
        else:
            version_number      = version_number_beta
            version_beta        = 0

        version_parts = (f"{version_number}.0.0").split('.')
        version  = 0
        version += int(version_parts[0])*10000
        version += int(version_parts[1])*100
        version += int(version_parts[2])*1

    except FileNotFoundError:
        return (0, 0, 'Not Installed')

    except Exception as err:
        log_exception(err)
        return (0, 0, ERROR)

    evlog_file.close()

    return (version, version_beta, version_number_beta)

#------------------------------------------------------------------------------
def _copy_image_files_to_www_directory(ic3_evlog_js_directory, www_evlog_directory):
    '''
    Copy any image files from the icloud3/event_log directory to the /www/[event_log_directory]
    '''
    try:
        image_extensions = ['png', 'jpg', 'jpeg']
        image_dir_filenames = get_filename_list(
                                start_dir=f"{Gb.icloud3_directory}/event_log_card/",
                                file_extn_filter=['png', 'jpg', 'jpeg'])

        for image_filename in image_dir_filenames:
            copy_file(  f"{ic3_evlog_js_directory}/{image_filename}",
                        f"{www_evlog_directory}/{image_filename}")

    except Exception as err:
        log_exception(err)
        return

#------------------------------------------------------------------------------
def copy_icloud3_theme_file():
    ic3_theme_file      = Gb.hass.config.path(Gb.icloud3_directory, 'theme', 'icloud3_theme', 'icloud3.yaml')
    ha_themes_file      = Gb.hass.config.path('themes', 'icloud3_theme', 'icloud3.yaml')
    ha_themes_directory = Gb.hass.config.path('themes', 'icloud3_theme')

    make_directory(ha_themes_directory)
    copy_file(ic3_theme_file, ha_themes_file)

    Gb.hass.services.call('frontend', 'reload_themes', {})

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   LOAD THE ZONE DATA FROM HA
#
#   Retrieve the zone entity attributes from HA and initialize Zone object
#   that is used when a Device is located
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_Zones_object():
    '''
    Get the zone names from HA, fill the zone tables
    '''

    try:
        if Gb.is_icloud3_initial_startup:
            event.async_track_state_added_domain(Gb.hass, 'zone', zone_handler.ha_added_zone_entity_id)
            event.async_track_state_removed_domain(Gb.hass, 'zone', zone_handler.ha_removed_zone_entity_id)
        if Gb.is_icloud3_initial_startup is False:
            Gb.hass.services.call(ZONE, "reload")
    except:
        pass

    Gb.state_to_zone = STATE_TO_ZONE_BASE.copy()
    OldZones_by_zone = Gb.Zones_by_zone.copy()

    Gb.Zones           = []
    Gb.Zones_by_zone   = {}
    Gb.HAZones         = []
    Gb.HAZones_by_zone = {}
    Gb.zones_dname     = NON_ZONE_ITEM_LIST.copy()

    # PSEUDO ZONES - Create zones for Away, Unknown, None, etc that do not really exist
    # These zones/states. Radius=0 is used to bypass normal zone processing.
    for zone, display_as in NON_ZONE_ITEM_LIST.items():
        if zone in OldZones_by_zone:
            Zone = OldZones_by_zone[zone]
            Zone.__init__(zone)
        else:
            zone_data ={ZONE: zone, NAME: display_as, TITLE: display_as, FNAME: display_as,
                        FRIENDLY_NAME: display_as, RADIUS: 0, 'ha_zone': False}
            Zone = iCloud3_Zone(zone, zone_data)

    # HA ZONES - Create or reinitialize them on a restart
    # zone_entity_ids1 = Gb.hass.states.entity_ids(ZONE)
    # er_zones, zone_entity_data = entity_io.get_entity_registry_data(platform=ZONE)
    # yaml_zones = [zone for zone in zone_entity_ids if zone.replace('zone.', '') not in er_zones]

    zone_entity_ids = entity_io.ha_zone_entity_ids()

    # Add HA zones that are saved in the HA Entity Registry. This does not include
    # current Stationary Zones
    zone_msg = ''
    Gb.ha_zone_settings_check_secs = time_now_secs()
    for zone_entity_id in zone_entity_ids:
        zone = zone_entity_id.replace('zone.', '')
        if is_statzone(zone):
            continue

        # Update Zone data if it already exists, else add a new one.
        # Zone will be a regular Zone or a StatZone object. Reinitialize the correct one.
        if zone in OldZones_by_zone:
            Zone = OldZones_by_zone[zone]
            Zone.__init__(zone) #, zone_data)
        else:
            Zone = iCloud3_Zone(zone)

        if Zone.radius_m > 0:
            r_ft = f"/{m_to_um(Zone.radius_m)}" if Gb.um_MI else ""
            if Zone.passive:
                crlf_dot_x = CRLF_X
                passive_msg = ', Passive Zone'
            else:
                crlf_dot_x = CRLF_DOT
                passive_msg = ''
            zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                        f"{Zone.dname} (r{Zone.radius_m}m{r_ft}){passive_msg}")

        if zone == HOME:
            Gb.HomeZone = Zone

    # STATIONARY ZONES - Add them back to tables if they may already exist if this is a restart
    for zone, Zone in OldZones_by_zone.items():
        if isnot_statzone(zone) or Zone.is_ha_zone is False:
            continue

        list_add(Gb.Zones, Zone)
        list_add(Gb.HAZones, Zone)
        Gb.Zones_by_zone[zone]   = Zone
        Gb.HAZones_by_zone[zone] = Zone
        Gb.zones_dname[zone]     = Zone.dname

        crlf_dot_x = CRLF_X if Zone.passive else CRLF_DOT
        r_ft = f"/{m_to_um(Zone.radius_m)}" if Gb.um_MI else ""
        zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                    f"{Zone.dname} (r{Zone.radius_m}m{r_ft})")

    log_msg =  f"Setting up Zones > zone, Display ({Gb.display_zone_format})"
    post_event(f"{log_msg}{zone_msg}")

    if Gb.is_track_from_base_zone_used and Gb.track_from_base_zone != HOME:
        post_event( f"Primary 'Home' Zone > {zone_dname(Gb.track_from_base_zone)} "
                    f"{circle_letter(Gb.track_from_base_zone)}")

    evlog_msg = "Setting up Special Zone Parameters >"
    if Gb.is_passthru_zone_used:
        evlog_msg += f"{CRLF_DOT}Enter Zone Delay > DelayTime-{format_timer(Gb.passthru_zone_interval_secs)}"
    else:
        evlog_msg += f"{CRLF_DOT}ENTER ZONE DELAY IS NOT USED"

    dist = Gb.HomeZone.distance_km(Gb.statzone_base_latitude, Gb.statzone_base_longitude)

    if Gb.is_statzone_used:
        r_ft = f"/{m_to_um(Gb.HomeZone.radius_m)}" if Gb.um_MI else ""
        evlog_msg += (  f"{CRLF_DOT}Stationary Zone > {Gb.statzone_fname} (r{Gb.HomeZone.radius_m}m{r_ft}), "
                        f"{CRLF_HDOT}DistMoveLimit-{format_dist_km(Gb.statzone_dist_move_limit_km)}, "
                        f"DistFromAnotherZone-{format_dist_km(Gb.statzone_min_dist_from_zone_km)}")
    else:
        evlog_msg += f"{CRLF_DOT}STATIONARY ZONES ARE NOT USED"
    post_event(evlog_msg)

    # Cycle thru the Device's conf and get all zones that are tracked from for all devices
    Gb.TrackedZones_by_zone = {}
    for conf_device in Gb.conf_devices:
        for from_zone in conf_device[CONF_TRACK_FROM_ZONES]:
            if from_zone in Gb.HAZones_by_zone:
                Gb.TrackedZones_by_zone[from_zone] = Gb.Zones_by_zone[from_zone]

    Gb.startup_lists['Gb.Zones'] = Gb.Zones

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 1
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   INITIALIZE THE WAZE FIELDS
#
#------------------------------------------------------------------------------
def create_Waze_object():
    '''
    Create the Waze object even if Waze is not used.
    Also st up the WazeHist object here to keep object creation together
    '''
    try:
        if Gb.Waze:
            Gb.Waze.__init__(   Gb.is_waze_dist_method_used,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            # Re-initialising the object drops its old SQLite connection. Close it
            # first so the -wal/-shm locks do not survive a config reload.
            if Gb.WazeHist.connection is not None:
                Gb.WazeHist.close_waze_history_database()
            Gb.WazeHist.__init__(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)
        else:
            Gb.Waze = Waze(     Gb.is_waze_dist_method_used,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist = WazeHist(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)

    except Exception as err:
        log_exception(err)


# Kept at the end so start_ic3.<name> call sites work after the move to start_ic3_apple.
from .start_ic3_apple import (  # noqa: E402,F401
    setup_validate_apple_accts_upw, create_Devices_object,
    update_devices_non_tracked_fields, _log_device_dictionaries,
    _verify_away_time_zone_devicenames, log_into_apple_accounts,
    are_all_devices_verified, setup_tracked_devices_for_icloud,
    _get_conf_devices_apple_did_not_locate, _verify_conf_apple_device_parameters,
    _find_newer_same_name_device, _check_for_replacement_device,
    _post_repair_issue_aa_device_assignment, _fix_repair_issue_aa_device_assignment,
    _fix_repair_issue_clear_mobapp_mapping, _post_repair_issue_no_aa_device_assignment,
    _change_config_to_new_device, _update_Device_model_fields,
    _change_config_to_new_device_name, _match_AppleAcct_devices_to_Device,
    _refresh_icloud_data_retry, _set_any_Device_alerts,
    _post_evlog_apple_acct_devices_info, _post_tracked_devices_info,
    _post_family_share_info, _post_not_assigned_info, _set_device_data_source,
)

from .start_ic3_display import (  # noqa: E402,F401
    display_all_devices_config_info,
    display_inactive_devices,
    display_object_lists,
    dump_startup_lists_to_log,
    display_platform_operating_mode_msg,
    post_restart_icloud3_complete_msg,
)

# Kept at the end so start_ic3.<name> call sites work after the move to start_ic3_mobapp.
from .start_ic3_mobapp import (  # noqa: E402,F401
    setup_tracked_devices_for_mobapp, _scan_for_for_mobapp_device,
    _display_any_mobapp_errors, log_debug_stage_4_results,
    set_devices_verified_status, identify_tracked_monitored_devices,
    _refresh_all_devices_sensors, setup_trackable_devices,
)
