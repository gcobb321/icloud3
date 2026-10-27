

from ..global_variables import GlobalVariables as Gb
from ..const            import (ICLOUD3, DOMAIN,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT, NOTIFY,
                                HOME, ERROR, NONE_FNAME,
                                STATE_TO_ZONE_BASE, CMD_RESET_PYICLOUD_SESSION,
                                EVLOG_ALERT, EVLOG_ATTENTION, EVLOG_NOTICE, EVLOG_IC3_STAGE_HDR,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                EVENT_RECDS_MAX_CNT_BASE, EVENT_RECDS_MAX_CNT_ZONE,
                                UNKNOWN,
                                ICLOUD, FAMSHR,
                                DEVICE_TYPE_DN, DEVICE_TYPE_DNS,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS, MAC, IPAD_CELL, WATCH_WIFI, OTHER,
                                IPHONE_DN, IPAD_DN, IPOD_DN, WATCH_DN, AIRPODS_DN, MAC_DN,
                                MOBAPP, NO_MOBAPP, ICLOUD_DEVICE_STATUS, TIMESTAMP,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODE_DN,
                                NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
                                LOCATION, LATITUDE, RADIUS,
                                ID,
                                BATTERY_LEVEL,
                                PICTURE_WWW_STANDARD_DIRS,
                                DEVICE_TRACKER_STATE_SOURCE_DESC,
                                ERR_UNKNOWN_AA, ERR_UNKNOWN_MOBAPP, ERR_UNKNOWN,
                                ERR_ICLOUD_DISABLED, ERR_NOT_AVAIL, ERR_NOT_IN_AA, ERR_NOT_IN_MOBAPP,
                                ERR_NOT_USED, ERR_OFFLINE, ERR_NOT_DATA_SOURCE, ERR_NOT_CONFIG,
                                ERR_DISABLED_HA, ERR_USERNAME_PW, ERR_INACTIVE, )
from ..const_config     import (TRIGGER, ZONE, BATTERY_STATUS, CONF_ENCODE_PASSWORD, CONF_VERSION,
                                CONF_VERSION_INSTALL_DATE, CONF_EVLOG_CARD_DIRECTORY,
                                CONF_EVLOG_CARD_PROGRAM, CONF_EVLOG_BTNCONFIG_URL,
                                CONF_PICTURE_WWW_DIRS, CONF_APPLE_ACCT, CONF_APPLE_ACCT,
                                CONF_PASSWORD, CONF_DATA_SOURCE, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL,
                                CONF_MODEL_DISPLAY_NAME, CONF_INZONE_INTERVALS,
                                CONF_TRACK_FROM_ZONES, CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL,
                                CONF_MOBAPP_ALIVE_INTERVAL, CONF_GPS_ACCURACY_THRESHOLD,
                                CONF_OLD_LOCATION_THRESHOLD, CONF_OLD_LOCATION_ADJUSTMENT,
                                CONF_TFZ_TRACKING_MAX_DISTANCE, CONF_TRACK_FROM_BASE_ZONE_USED,
                                CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_TRAVEL_TIME_FACTOR, CONF_PASSTHRU_ZONE_TIME,
                                CONF_DISTANCE_BETWEEN_DEVICES, CONF_LOG_LEVEL,
                                CONF_LOG_LEVEL_DEVICES, CONF_DISPLAY_ZONE_FORMAT,
                                CONF_DEVICE_TRACKER_STATE_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                CONF_PASSWORD_SRP_ENABLED, CONF_CENTER_IN_ZONE,
                                CONF_DISCARD_POOR_GPS_INZONE, CONF_WAZE_USED, CONF_WAZE_REGION,
                                CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE, CONF_WAZE_REALTIME,
                                CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION, CONF_STAT_ZONE_FNAME,
                                CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,
                                CONF_DISPLAY_TEXT_AS, CONF_IC3_DEVICENAME, CONF_FNAME,
                                CONF_AADEV_NAME, CONF_AADEV_DEVICE_ID, CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_ZONE, CONF_NAME, CONF_ANALYTICS_ENABLED, DEFAULT_GENERAL_CONF,
                                DEFAULT_TRACKING_CONF, )
from ..const_char       import (CIRCLE_LETTERS_DARK, CRLF, CRLF_DOT, CRLF_CHK, CRLF_SP3_DOT, HDOT,
                                CRLF_SP5_DOT, CRLF_HDOT, LINK, LLINK, RLINK, CRLF_CIRCLE_X,
                                CIRCLE_X, CRLF_SP3_HDOT, CRLF_INDENT, CRLF_X, CRLF_TAB, DOT,
                                CRLF_SP8_HDOT, CRLF_SP8_DOT, CRLF_RED_X, RED_X, CRLF_RED_ALERT,
                                CRLF_RED_ALERT2, RED_ALERT, CRLF_RED_MARK, CRLF_STAR, GREEN_ALERT,
                                YELLOW_WARNING, INACTIVE_SYMB, RARROW, NBSP2, NBSP4, NBSP6,
                                CIRCLE_STAR, INFO_SEPARATOR, DASH_20, CHECK_MARK, )

from ..utils                import entity_io
from ..utils.utils          import (instr, is_empty, isnot_empty, yes_no, circle_letter, zone_dname,
                                    is_statzone, isnot_statzone, apple_user, apple_user_dev,
                                    list_to_str, list_add, list_del, list_keys, list_sort,
                                    dict_del, dict_sort, dict_reverse_sort, )
from ..utils.messaging      import (broadcast_info_msg, add_log_file_filter,
                                    post_event, post_alert, post_greenbar_msg, post_dotted_line,
                                    post_error_msg, post_monitor_msg, update_alert_sensor,
                                    post_repair_issue, clear_repair_issue, clear_repair_issues,
                                    post_repair_issue_update_device,
                                    register_repair_fix_handler,
                                    FIX_ACTION_ANALYTICS_APPROVAL, ANALYTICS_APPROVAL_ISSUE_ID,
                                    post_config_error, clear_config_error, alert_key_for,
                                    log_info_msg, log_debug_msg, log_error_msg, log_warning_msg,
                                    log_exception, format_filename, log_stack,
                                    internal_error_msg2,
                                    _evlog, _log, more_info, format_header_box,)
from ..utils.dist_util      import (format_dist_km, m_to_um, )
from ..utils.time_util      import (time_now_secs, mins_since, format_timer, format_time_age,
                                    format_age, secs_to_hhmm, secs_to_time, )
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
from ..support              import service_handler
from ..support              import test_controls as TEST
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
        Gb.hass.loop.create_task(update_lovelace_resource_event_log_js_entry())
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
async def update_lovelace_resource_event_log_js_entry(new_evlog_dir=None, silent=False):
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
        log_error_msg(  "An unknown error was encountered updating the Lovelace "
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

    Gb.alerts_sensor                = 'none'
    Gb.alerts_by_alert_key          = {}
    Gb.icloud3_reload_requested     = False
    Gb.startup_msg                  = []

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
def ha_startup_completed(dummy_parameter):

    # HA may have not set up the notify service before iC3 starts. If so, the mobile_app
    # Notify entity was not setup either. Do it now.
    #
    # Run from async_at_started in __init__ in an executor thread. If iCloud3 is still
    # starting, stage 5 sets up the notify service names itself and the 5-min retry in
    # icloud3_main does it if the service was not available yet.
    Gb.ha_started = True

    event_msg = "Home Assistant Startup Complete"
    if Gb.is_icloud3_startup_inprocess:
        event_msg += ", iCloud3 is still starting"
    post_event(f"{EVLOG_NOTICE}{event_msg}")
    log_info_msg(event_msg)

    if Gb.is_icloud3_startup_inprocess or Gb.conf_data_source_MOBAPP is False:
        return

    mobapp_interface.get_mobile_app_integration_device_info(ha_started_check=True)
    mobapp_interface.setup_notify_service_name_for_mobapp_devices()

#------------------------------------------------------------------------------
def ha_stopping(dummy_parameter):
    post_event("HA Shutting Down")
    Gb.EvLog.display_user_message("HA Shutting Down")

#------------------------------------------------------------------------------
def ha_restart(dummp_parameter):
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
    Set up icloud apple_id/password and devices from the configuration parameters
    '''
    # apple_id, password, locate_all = \
    #         config_file.apple_acct_apple_id_password(0)
    conf_apple_acct, _idx = config_file.conf_apple_acct(0)
    conf_apple_id = conf_apple_acct[CONF_APPLE_ACCT]
    conf_password = conf_apple_acct[CONF_PASSWORD]

    Gb.apple_id                     = conf_apple_id
    Gb.apple_user                = apple_user(Gb.apple_id)
    Gb.password                     = conf_password
    Gb.is_password_encoded         = Gb.conf_tracking[CONF_ENCODE_PASSWORD]

    Gb.AppleAcct_logging_in_apple_ids= []

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'mobapp'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP)

    Gb.conf_data_source_ICLOUD    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)
    # Gb.conf_data_source_ICLOUD    = Gb.conf_data_source_ICLOUD
    Gb.conf_data_source_MOBAPP    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)

    Gb.use_data_source_ICLOUD     = (Gb.conf_data_source_ICLOUD and Gb.apple_id != '' and Gb.password != '')
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
            and (Gb.apple_id == '' or Gb.password == '')):
        alert_msg =("ICLOUD USERNAME-PASSWORD ERROR > The apple_id or password has not "
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
            Gb.WazeHist.open_waze_history_database(Gb.wazehist_database_filename)
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

#------------------------------------------------------------------------------
def request_analytics_approval():
    '''
    Add the iCloud3 Analytics approval request to HA Settings > Repairs if sending the
    Analytics data has not been enabled or disabled (analytics_enabled is None).
    repairs.iCloud3AnalyticsRepairFlow displays the iCloud3 Analytics description with
    an Enable/Disable selection:
        - Submit  - analytics_enabled = True/False, the configuration file is updated
                    and the issue is removed
        - Close   - Nothing is changed, the issue stays in Repairs

    The issue is removed if it was answered on the iCloud3 Configure > Analytics screen.
    '''
    try:
        if Gb.conf_general.get(CONF_ANALYTICS_ENABLED) is not None:
            clear_repair_issue(ANALYTICS_APPROVAL_ISSUE_ID)
            return

        post_repair_issue(
                issue_id   = ANALYTICS_APPROVAL_ISSUE_ID,
                alert_key  = 'icloud3^analytics_approval',
                title      = 'iCloud3 Analytics, Approval Requested',
                alert_msg  = '',
                fix_action = FIX_ACTION_ANALYTICS_APPROVAL,
                translation_key = ANALYTICS_APPROVAL_ISSUE_ID,
                translation_placeholders = {})

    except Exception as err:
        log_exception(err)

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


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   CREATE THE DEVICES OBJECT FROM THE DEVICE PARAMETERS IN THE
#   CONFIGURATION FILE
#
#   Set up the devices to be tracked and it's associated information
#   for the configuration line entry. This will fill in the following
#   fields based on the extracted devicename:
#       device_type
#       friendly_name
#       sensor.picture name
#       device tracking flags
#       tracked_devices list
#   These fields may be overridden by the routines associated with the
#   operating mode (icloud, mobapp)
#
#------------------------------------------------------------------------------
def setup_validate_apple_accts_upw():
    return

    if Gb.ValidateAppleAcctUPW is None:
        Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()
        Gb.upw_valid_by_apple_id = {}
        Gb.upw_code_by_apple_id = {}

#------------------------------------------------------------------------------
def create_Devices_object():

    try:
        er_util.set_ha_device_id_x_devicename()

        old_Devices_by_devicename      = Gb.Devices_by_devicename.copy()
        Gb.Devices                     = []
        Gb.Devices_by_devicename       = {}
        Gb.Devices_by_apple_id         = {}
        Gb.conf_devicenames            = []
        Gb.conf_icloud_dnames          = []
        Gb.devicenames_by_aadev_dname  = {}
        Gb.aadev_dnames_by_devicename  = {}
        Gb.startup_alerts_by_source    = {}

        # Update the ha_device_id_x_devicename dict and correct any
        # disabled device conflicts between iCloud3 and the ha_device_reg

        for conf_device in Gb.conf_devices:
            devicename   = conf_device[CONF_IC3_DEVICENAME]
            device_fname = conf_device[CONF_FNAME]
            aadev_name   = conf_device[CONF_AADEV_NAME]
            apple_id     = conf_device[CONF_APPLE_ACCT]
            apple_acct   = apple_user(apple_id)

            # This should never happen, but...
            if devicename == '':
                post_greenbar_msg(f"HA device_tracker entity id not configured for {aadev_name}")
                post_alert( f"CONFIGURATION ALERT > The device_tracker entity id {devicename} "
                            f"has not been configured for {aadev_name} "
                            f"({DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])})")
                continue

            Gb.conf_icloud_dnames.append(aadev_name)
            broadcast_info_msg(f"Setting up Device > {devicename}")

            # Do not set up inactive device or one disabled in HA
            if devicename in Gb.ha_disabled_by_by_devicename:
                do_not_track_reason = ERR_DISABLED_HA
            elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
                do_not_track_reason = ERR_INACTIVE
            else:
                do_not_track_reason = ''

            if do_not_track_reason:
                post_event( f"{INACTIVE_SYMB}{conf_device[CONF_FNAME]} ({devicename}) > "
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}, "
                            f"{do_not_track_reason}"
                            f"{CRLF_SP5_DOT}Apple Device-{aadev_name} ({conf_device[CONF_MODEL_DISPLAY_NAME]})"
                            f"{CRLF_SP5_DOT}MobApp Entity-{conf_device[CONF_MOBILE_APP_DEVICE]}")
                continue

            # This list is based on the configuration, it will be rebuilt when the devices are verified
            # after the iCloud data has been read. It is also rebuild in config_flow when a device is updated
            Gb.devicenames_by_aadev_dname[aadev_name] = devicename
            Gb.aadev_dnames_by_devicename[devicename] = aadev_name

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                post_monitor_msg(f"INITIALIZE Device > {devicename}")
                Device = old_Devices_by_devicename[devicename]

                Device.__init__(devicename, conf_device)

            else:
                post_monitor_msg(f"ADD Device > {devicename}")

                Device = iCloud3_Device(devicename, conf_device)

            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

            if conf_device[CONF_TRACKING_MODE] == INACTIVE:
                continue

            _display_stage3_event_log_device_info(Device)

            # Initialize device_tracker entity to display before AppleAcct starts up
            Device.write_ha_device_tracker_state()

    except Exception as err:
        log_exception(err)

    _verify_away_time_zone_devicenames()
    _log_device_dictionaries()

    return

#--------------------------------------------------------------------
def _display_stage3_event_log_device_info(Device):

    try:
        if Gb.use_data_source_ICLOUD is False:
            Device.status_msg[ICLOUD] = ERR_NOT_AVAIL

        #........................................
        apple_acct_msg = (  (f"{apple_user(Device.conf_apple_acct_apple_id)}"
                            f"{Device.status_msg.get(CONF_APPLE_ACCT, '')}") or '✪ NONE')

        icloud_dev_msg = f"{Device.conf_icloud_dname} ({Device.model_display_name})" \
                            if Device.conf_icloud_dname else '✪ NONE'

        mobapp_dev_msg = (Device.mobapp[DEVICE_TRACKER]) or '✪ NONE'

        if ((apple_acct_msg == '✪ NONE' or icloud_dev_msg == '✪ NONE')
                and mobapp_dev_msg == '✪ NONE'):
            monitored_msg = f"{RED_ALERT}NO DATA SOURCE"

        elif Device.is_monitored:
            monitored_msg = 'Monitored'
        else:
            monitored_msg = 'Tracked'

        evlog_msg = (   f"{CHECK_MARK}{Device.fname_devicename} > {Device.devtype_fname}, {monitored_msg}"
                        f"{CRLF_SP5_DOT}Apple Account: {apple_acct_msg}"
                        f"{CRLF_SP5_DOT}Apple Device: {icloud_dev_msg}"
                        f"{CRLF_SP5_DOT}MobApp Entity: {mobapp_dev_msg}")

        if Device.track_from_base_zone != HOME:
            evlog_msg += f"{CRLF_SP5_DOT}Primary 'Home' Zone: {zone_dname(Device.track_from_base_zone)}"
        if Device.track_from_zones != [HOME]:
            evlog_msg += f"{CRLF_SP5_DOT}Track from Zones: {list_to_str(Device.track_from_zones)}"
        post_event(evlog_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def update_devices_non_tracked_fields():
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if Device := Gb.Devices_by_devicename.get(devicename):
            Device.initialize_non_tracking_config_fields(conf_device)

#--------------------------------------------------------------------
def _log_device_dictionaries():

    Gb.startup_lists['Gb.Devices']                     = Gb.Devices
    Gb.startup_lists['Gb.DeviceTrackers_by_devicename']= Gb.DeviceTrackers_by_devicename
    Gb.startup_lists['Gb.Devices_by_devicename']       = Gb.Devices_by_devicename
    Gb.startup_lists['Gb.ha_device_id_x_devicename']  = Gb.ha_device_id_x_devicename
    Gb.startup_lists['Gb.conf_devicenames']            = Gb.conf_devicenames
    Gb.startup_lists['Gb.conf_icloud_dnames']          = Gb.conf_icloud_dnames
    Gb.startup_lists['Gb.devicenames_by_aadev_dname'] = Gb.devicenames_by_aadev_dname
    Gb.startup_lists['Gb.icloud_dname_by_devicenames'] = Gb.aadev_dnames_by_devicename

#--------------------------------------------------------------------
def _verify_away_time_zone_devicenames():
    '''
    Verify the devicenames in the Away time zone fields
    '''
    update_conf_file_flag = False

    if ('none' in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]
            or 'all' in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
        pass
    else:
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                list_del(Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES], devicename)
                update_conf_file_flag = True

        if Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0

    if ('none' in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]
            or 'all' in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
        pass
    else:
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                list_del(Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES], devicename)
                update_conf_file_flag = True

        if Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0

    if update_conf_file_flag:
        config_file.write_icloud3_configuration_file()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SET UP ICLOUD3 ACCOUNTS/DEVICES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def validate_upw_all_apple_accts():

    Gb.ValidateAppleAcctUPW.validate_upw_all_apple_accts()

    # Get list of all unique Apple Acct apple_ids in config. It must be set before the
    # Devices are checked for an unknown Apple Acct below. It is empty on a restart
    # (apple_acct_support reset), every Device would have an unknown Apple Acct.
    Gb.conf_apple_ids = [apple_account[CONF_APPLE_ACCT]
                                for apple_account in Gb.conf_apple_accounts
                                if (apple_account[CONF_APPLE_ACCT] in Gb.upw_valid_by_apple_id
                                        and apple_account[CONF_APPLE_ACCT] != '')]

    # Report the unknown Apple Accts before the Devices are checked. A Device using one
    # is an Apple Acct error, not a Device error, and a Device issue is not created.
    unknown_apple_acct_apple_ids = report_unknown_apple_accounts()

    for Device in Gb.Devices:
        if Gb.internet_error:
            pass

        elif Gb.use_data_source_ICLOUD is False:
            Device.status_msg[ICLOUD] = ERR_NOT_AVAIL
            if Device.conf_apple_acct_apple_id != '':
                Device.status_msg[CONF_APPLE_ACCT] = ERR_UNKNOWN

        elif (Device.conf_apple_acct_apple_id == ''
                or Device.conf_icloud_dname == ''):
            pass

        elif Device.conf_apple_acct_apple_id not in Gb.conf_apple_ids:
            Device.status_msg[CONF_APPLE_ACCT] = ERR_UNKNOWN

            alert_key = alert_key_for(Device.devicename, 'Unknown Apple Acct')

            # An inactive Device only gets the status_msg, not an issue
            if (Gb.conf_data_source_ICLOUD
                    and Device.isnot_inactive
                    and alert_key not in Device.alerts_by_alert_key
                    and Device.conf_apple_acct_apple_id not in unknown_apple_acct_apple_ids):
                post_config_error(
                    Source      = Device,
                    source_name = Device.fname,
                    error       = 'Unknown Apple Acct',
                    error_item  = Device.conf_apple_acct_apple_user,
                    message     = ( 'The Apple Account assigned to the iCloud3 Device could not be '
                                    'found or an error occurred logging in. Verify the correct '
                                    'Apple Account device was selected for this iCloud3 Device.'),
                    details     = ( f"{CRLF_DOT}{Device.fname_devicename} > AppleAcct: "
                                    f"{Device.conf_apple_acct_apple_user}"),
                    repair_step = 'update_device')

        elif Gb.upw_valid_by_apple_id.get(Device.conf_apple_acct_apple_id, False) is False:
            Device.status_msg[CONF_APPLE_ACCT] = ERR_USERNAME_PW

#--------------------------------------------------------------------
def log_into_apple_accounts():
    '''
    Verify that all Apple Account AppleAcct objects have been created
    '''
    if Gb.use_data_source_ICLOUD is False:
        return False

    if is_empty(Gb.conf_apple_ids):
        return False

    # Setup access to the Apple acct if is is not already setup or anything
    # has changed
    aa_login_error = ''
    results_msg    = ''
    alert_msg      = ''
    Gb.AppleAccts  = []
    for apple_id in Gb.conf_apple_ids:
        conf_apple_acct, _idx = config_file.conf_apple_acct(apple_id)
        password              = Gb.AppleAcct_password_by_apple_id[apple_id]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices    = conf_apple_acct[CONF_LOCATE_ALL]

        post_dotted_line()

        upw_valid = Gb.upw_valid_by_apple_id.get(apple_id, True)
        upw_code  = Gb.upw_code_by_apple_id.get(apple_id, 0)

        if upw_valid is False and upw_code in [401, 401.1, 403, 421.1, 423, 503]:
            post_event( f"{apple_user(apple_id)} > Not Setting up Apple Account"
                        f"{CRLF_DOT}Failed to validate Username/Password ({upw_code})")
            continue

        post_event( f"{apple_user(apple_id)} > Setting up Apple Account")

        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

        # Initial check to see if AppleAcct is available
        can_reuse_AppleAcct = (
            Gb.was_icloud3_reloaded is True
            and AppleAcct is not None
            and isnot_empty(AppleAcct.AADev_by_device_id)
            and apple_id == AppleAcct.apple_id
            and password == AppleAcct.password
            and apple_server_location == AppleAcct.apple_server_location
            and locate_all_devices == AppleAcct.locate_all_devices)

        # Second check to see if AppleAcct is has no exceptions and can be reused
        if can_reuse_AppleAcct:
            can_reuse_AppleAcct = (
                AppleAcct.is_AADevices_setup_complete
                and AppleAcct.is_authenticated
                and aas.is_authentication_2fa_code_needed(AppleAcct) is False
                and Gb.AppleAcct_error_by_apple_id.get(apple_id, False) is False
                and Gb.iCloudSession_by_apple_id.get(apple_id, None is not None)
                and Gb.upw_valid_by_apple_id.get(apple_id, False)
                and AppleAcct.login_successful is True
                and AppleAcct.auth_failed_503 is False)

        if Gb.upw_valid_by_apple_id.get(apple_id) is False:
            upw_code = Gb.upw_code_by_apple_id.get(apple_id, 200)
            if upw_code == 503:
                post_alert(f"Login Failed, Apple Refused the Signin Request, Try again later ({upw_code})")
            else:
                post_alert(f"Login Failed, Invalid Username/Password ({upw_code})")

        elif can_reuse_AppleAcct is False:
            AppleAcct = aas.log_into_apple_account(
                                        apple_id,
                                        password,
                                        apple_server_location,
                                        locate_all_devices)

            if AppleAcct:
                apple_login_msg = 'Login Successful'

            else:
                post_event( f"{CRLF_RED_X} Login Failed, "
                            f"Server Loc-{apple_server_location}")
                alert_msg = EVLOG_ALERT
                update_alert_sensor(Source=apple_id, name=apple_user(apple_id),
                                    error='login_failed',
                                    alert_msg=f"{apple_user(apple_id)} > Apple Acct Login Failed")

        else:
            apple_login_msg = 'Already logged in'

        if AppleAcct and AppleAcct.apple_id == apple_id:
            _check_apple_acct_status_issues(AppleAcct)

        if AppleAcct and AppleAcct.login_successful:
            if AppleAcct.is_authenticated:
                reauth_in_days, reauth_msg = AppleAcct.get_next_reauth_in_days_info_msg()
                AppleAcct.issue_reauth_in_days_alert_msg()
                post_event( f"{apple_login_msg}"
                            f"{CRLF_DOT}Authentication Method-{AppleAcct.login_auth_method}"
                            f"{CRLF_DOT}{reauth_msg}")

            setup_tracked_devices_for_icloud(AppleAcct)

        post_event(f"{AppleAcct.apple_user} > Setting up Apple Account, Complete")

    Gb.startup_lists['Gb.AppleAcct_error_by_apple_id'] = Gb.AppleAcct_error_by_apple_id

    # Check if the pyicloud_ic3_interface detected the internet is down
    if (Gb.internet_error
            or is_empty(Gb.AppleAccts)):
        return False

    if isnot_empty(Gb.devices_without_location_data):
        post_event( f"Apple Acct > Location data is not available for:"
                    f"{CRLF}{NBSP6}{DOT}{list_to_str(Gb.devices_without_location_data)}")
        post_dotted_line()

    return True

#------------------------------------------------------------------
def _check_apple_acct_status_issues(AppleAcct):
    '''
    Post or remove the HA Repairs issues for an Apple Acct problem that stops
    iCloud locations until the user does something with Apple:
        - Apple's updated Terms of Use need to be accepted (Submit accepts them)
        - The Apple Acct is locked (notice)

    An issue is only removed after a successful login. A failed login (internet
    or Apple server error) does not say if the problem was fixed.
    '''
    if Gb.internet_error:
        return

    # TEST CODE - Simulate Apple asking for the Terms of Use
    # global TEST.TERMS_OF_USE_NEEDED_USERNAME
    if TEST.TERMS_OF_USE_NEEDED_USERNAME in (AppleAcct.apple_id, AppleAcct.apple_user):
        TEST.TERMS_OF_USE_NEEDED_USERNAME = None
        AppleAcct.terms_of_use_update_needed = True
        post_event( f"{EVLOG_ALERT}TEST > Apple Acct > {AppleAcct.apple_user}, "
                    f"Accept Terms of Use needed is simulated")

    if AppleAcct.terms_of_use_update_needed:
        aas.post_repair_issue_aa_terms_of_use(AppleAcct)
    elif AppleAcct.is_authenticated:
        aas.clear_repair_issue_aa_terms_of_use(AppleAcct)

    locked_issue_id = aas.apple_acct_repair_issue_id(aas.REPAIR_ISSUE_ACCT_LOCKED, AppleAcct)
    if AppleAcct.account_locked:
        post_repair_issue(
                issue_id   = locked_issue_id,
                alert_key  = AppleAcct.apple_id,
                title      = "Apple Acct is Locked",
                alert_msg  = '',
                severity   = 'error',
                translation_key = aas.REPAIR_ISSUE_ACCT_LOCKED,
                translation_placeholders = {'account': AppleAcct.apple_user})
    elif AppleAcct.is_authenticated:
        clear_repair_issue(locked_issue_id)

#............................................................................
def repair_issue_fix_aa_terms_of_use(fix_data):
    '''
    Repairs Submit handler for aas.post_repair_issue_aa_terms_of_use. Accept Apple's
    Terms of Use (sends 'I Agree' to Apple) and restart iCloud3. Runs in an executor
    thread.
    '''
    apple_id  = fix_data.get('apple_id')
    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

    if AppleAcct is None:
        post_alert(f"HA Repairs > Accept Terms of Use, "
                    f"Apple Acct is no longer available ({apple_user(apple_id)})")
        return False

    # Accepted somewhere else (Configure screen, www.icloud.com)
    if AppleAcct.terms_of_use_update_needed is False:
        AppleAcct.terms_of_use_repair_issue_posted = False
        return True

    # The accountLogin request (log_into_account) runs AppleAcct._handle_accept_terms_of_use,
    # it accepts the terms when terms_of_use_accepted is True. refresh_session=True
    # skips the session token validation, authenticate() returns before accountLogin
    # is done when the token is still valid.
    AppleAcct.terms_of_use_accepted = True
    AppleAcct.authenticate(refresh_session=True)

    if AppleAcct.terms_of_use_update_needed:
        post_error_msg( f"{EVLOG_ALERT}Apple Acct > {AppleAcct.apple_user}, "
                        f"HA Repairs > Apple did not accept the Terms of Use")
        return False

    AppleAcct.terms_of_use_repair_issue_posted = False
    post_event( f"Apple Acct > {AppleAcct.apple_user}, "
                f"HA Repairs > Terms of Use accepted, Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('accept_terms_of_use', repair_issue_fix_aa_terms_of_use)

#------------------------------------------------------------------
def are_all_devices_verified(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''


    # Get a list of all tracked devices that have not been set up by icloud or the Mobile App
    unverified_devices = [Device.fname_devicename
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.was_verified is False and Device.isnot_inactive]
    unverified_device_apple_ids = [Device.conf_apple_acct_apple_id
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if (Device.was_verified is False
                                    and Device.isnot_inactive)]

    Gb.apple_ids_setup_error_retry_list   = list(set(unverified_device_apple_ids))
    Gb.devicenames_setup_error_retry_list = list(set(unverified_devices))

    Gb.startup_lists['_.apple_ids_setup_error_retry_list']   = Gb.apple_ids_setup_error_retry_list
    Gb.startup_lists['_.devicenames_setup_error_retry_list'] = Gb.devicenames_setup_error_retry_list

    if is_empty(unverified_devices):
        return True

    if retry:
        post_greenbar_msg("Some Tracked Devices could not be verified. Restart may be needed.")
        alert_msg = ("Some Tracked Devices could not be verified. Review and correct "
                    "any configuration errors. Then restart iCloud3")
    else:
        alert_msg = "UNVERIFIED DEVICES ALERT > Some Tracked Devices could not be verified."
    alert_msg += (f"{CRLF_DOT}Unverified Devices > {list_to_str(unverified_devices)}")
    post_alert(alert_msg)

    return False

#--------------------------------------------------------------------
def setup_tracked_devices_for_icloud(AppleAcct):
    '''
    The Family Share device data is available from AppleAcct when logging into the iCloud
    account. This routine will get all the available Apple devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        AppleAcct: Object containing data to be processed. This might be from Gb.AppleAcct (normal/default)
                    or the one created in config_flow if the apple_id was changed.
    '''

    if Gb.conf_data_source_ICLOUD is False:
        post_event("Apple Account > Not used as a data source")
        return

    if Gb.conf_icloud_device_cnt == 0:
        return

    try:
        _reassign_unknown_apple_acct_devices(AppleAcct)

        missing_aadev_devices = _get_conf_devices_apple_did_not_locate(AppleAcct)
        if isnot_empty(missing_aadev_devices):
            _refresh_icloud_data_retry(AppleAcct, missing_aadev_devices)

        _set_device_data_source(AppleAcct)
        _verify_conf_apple_device_parameters(AppleAcct)
        _match_AppleAcct_devices_to_Device(AppleAcct)

        _post_evlog_apple_acct_devices_info(AppleAcct)

    except Exception as err:
        log_exception(err)

    owner = AppleAcct.apple_user
    Gb.startup_lists[f"{owner}.AppleAcct.device_id_by_aadev_dname"] = \
                        {k: v[:10] for k, v in AppleAcct.device_id_by_aadev_dname.items()}
    Gb.startup_lists[f"{owner}.AppleAcct.aadev_dname_by_device_id"] = \
                        {k[:10]: v for k, v in AppleAcct.aadev_dname_by_device_id.items()}
    Gb.startup_lists[f"Gb.Devices_by_icloud_device_id"]     = \
                        {k[:10]: v for k, v in Gb.Devices_by_icloud_device_id.items()}

#----------------------------------------------------------------------------
def _reassign_unknown_apple_acct_devices(AppleAcct):
    '''
    A device's Apple Account is not in the configuration (Stage 3 posted the
    'Unknown Apple Acct' error) but its Apple Device (device_id) is in this Apple
    Account. Assign the device to this Apple Account so it is matched and tracked
    with the other devices in this startup.

    Only the device_id is used. A device with the same name may be another device.
    '''
    conf_apple_ids = [conf_apple_acct[CONF_APPLE_ACCT]
                            for conf_apple_acct in Gb.conf_apple_accounts]
    assigned_device_ids = [conf_device[CONF_AADEV_DEVICE_ID]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCT] in conf_apple_ids]

    for conf_device in Gb.conf_devices:
        try:
            old_apple_id = conf_device[CONF_APPLE_ACCT]
            device_id    = conf_device[CONF_AADEV_DEVICE_ID]

            if (old_apple_id == ''
                    or old_apple_id in conf_apple_ids
                    or device_id in assigned_device_ids):
                continue

            AADev = AppleAcct.AADev_by_device_id.get(device_id)
            if AADev is None or AADev.Device:
                continue

            _change_config_to_apple_acct(AppleAcct, conf_device, AADev, old_apple_id)
            list_add(assigned_device_ids, device_id)

        except Exception as err:
            log_exception(err)

#............................................................................
def _change_config_to_apple_acct(AppleAcct, conf_device, AADev, old_apple_id):
    '''
    Update the iCloud3 configuration and the Device with the Apple Account the
    device was found in. Remove the Stage 3 'Unknown Apple Acct' error and its
    Repairs issue and post a Repairs notice that the configuration was changed.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname  = conf_device[CONF_FNAME]

    conf_device[CONF_APPLE_ACCT] = AppleAcct.apple_id
    config_file.write_icloud3_configuration_file()

    if Device := Gb.Devices_by_devicename.get(devicename):
        Device.conf_apple_acct_apple_id = AppleAcct.apple_id
        Device.status_msg.pop(CONF_APPLE_ACCT, None)
        list_del(Gb.Devices_by_apple_id.get(old_apple_id, []), Device)
        Gb.Devices_by_apple_id[AppleAcct.apple_id] = \
                list_add(Gb.Devices_by_apple_id.get(AppleAcct.apple_id, []), Device)

    AADev.startup_msg = 'APPLE ACCT UPDATED'

    clear_config_error(Source=devicename, error='Unknown Apple Acct')

    post_config_error(
                Source      = Device,
                source      = devicename,
                source_name = dev_fname,
                error       = 'Apple Account Updated',
                error_item  = AppleAcct.apple_user,
                message     = ( 'The Apple Account assigned to the iCloud3 Device is not in the '
                                'configuration. Its Apple Device was found in another Apple '
                                'Account. The configuration was updated to use that Apple Account.'),
                details     = ( f"{CRLF_DOT}{apple_user(old_apple_id)}{RARROW}{AppleAcct.apple_user}"
                                f"{CRLF_DOT}Apple Device: {_name_model(AADev)}"),
                repair_step = 'notice',
                translation_key = REPAIR_ISSUE_APPLE_ACCT_REASSIGNED,
                translation_placeholders = {
                                'device': dev_fname,
                                'old_apple_acct': apple_user(old_apple_id),
                                'new_apple_acct': AppleAcct.apple_user,
                                'apple_device': _name_model(AADev)})

#............................................................................
def _get_conf_devices_apple_did_not_locate(AppleAcct):
    aadev_names = [_AADev.name for _AADev in AppleAcct.AADev_items]
    missing_aadev_devices = {}
    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCT] != AppleAcct.apple_id:
            continue

        devicename = conf_device[CONF_IC3_DEVICENAME]
        device_id  = conf_device[CONF_AADEV_DEVICE_ID]
        aadev_name = conf_device[CONF_AADEV_NAME]

        if (aadev_name not in aadev_names
                and device_id not in AppleAcct.AADev_by_device_id):
            missing_aadev_devices[devicename] = aadev_name

    return missing_aadev_devices

#----------------------------------------------------------------------------
def _verify_conf_apple_device_parameters(AppleAcct):
    '''
    Check the apple acct devices name and device_id. Update the conf if the name
    was changed or if the name was assigned to another device. Then see if a newer
    device replaced the tracked device (_check_for_replacement_device).
    '''
    # Test Code - Do not update a newer device when starting up. This will test
    # detected a newer device when the device data is refreshed
    # if Gb.is_icloud3_initial_startup:
    #     return

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCT] != AppleAcct.apple_id:
            continue

        try:
            conf_device_id  = conf_device[CONF_AADEV_DEVICE_ID]
            conf_aadev_name = conf_device[CONF_AADEV_NAME]
            broadcast_info_msg(f"Verifying Apple Device > {conf_aadev_name}")

            # Get Device specified in config file using the device_id
            AADev = AppleAcct.AADev_by_device_id.get(conf_device_id)

            # The config AA device was found using the device_id but this device is now a
            # duplicate. This means a newer device with the same name and owner has
            # been added to the Apple Acct (current config=iPhone16, AA data=iPhone18).
            # Change the ic3_devicename to now use the newer device .
            if AADev and AADev.is_duplicate_dname:
                NewerAADev = _find_newer_same_name_device(AppleAcct, AADev)
                if NewerAADev:
                    _change_config_to_new_device(AppleAcct, NewerAADev, conf_device)
                continue

            # The config AA device with this device_id is no longer in the Apple Acct
            # device list (it was removed), get the AA device that now has the config
            # name (Gary-iPhone) if it exists
            if AADev is None:
                device_id  = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
                AADev  = AppleAcct.AADev_by_device_id.get(device_id)

                # An AA device was found with the same name, change config to it
                # If it is not found, _match_AppleAcct_devices_to_Device posts the
                # Unknown Apple Device error and creates an alert and repair issue later
                if AADev:
                    _change_config_to_new_device(AppleAcct, AADev, conf_device)

                continue

            # The config file device_id was found, make sure the config model fields are
            # this device's. They will be wrong if the device_id was changed without them.
            # Only the raw_model is compared, the model_display_name format varies
            # ('iPadPro4', 'iPad Pro 4').
            if (conf_device[CONF_RAW_MODEL].replace('_', ',')
                    != AADev.raw_model.replace('_', ',')):
                _change_config_model_fields(conf_device, AADev)

            # The config file device_id was found, see if it was renamed. The dname has
            # the owner's name if another family member has a device with the same name.
            if conf_aadev_name != AADev.dname:
                _change_config_to_new_device_name(AppleAcct, conf_device, AADev.dname)
                continue

            # if conf_device[CONF_TRACKING_MODE] != INACTIVE:
            # The AA device was not found using the config name or replaced with a device
            # with the same name. Review the devices available and see if there is a
            # device with another name that matches the parameters of the one being checked
            _check_for_replacement_device(AppleAcct, conf_device, AADev)

        except Exception as err:
            log_exception(err)
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Error verifying Apple Acct Device"
                        f"{CRLF_DOT}{conf_aadev_name}, "
                        f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")

#............................................................................
def _find_newer_same_name_device(AppleAcct, AADev):
    '''
    Return the device with the same name and owner that is not a duplicate. It is
    the newest device with that name (_resolve_duplicate_dnames).
    '''
    for _AADev in AppleAcct.AADev_by_device_id.values():
        if (_AADev
                and _AADev.active
                and _AADev.is_duplicate_dname is False
                and _AADev.name == AADev.name
                and _AADev.prs_id == AADev.prs_id):
            return _AADev

    return None

#............................................................................
def _check_for_replacement_device(AppleAcct, conf_device, AADev):
    '''
    See if a newer device that is not tracked replaced the tracked device. We are
    chedking for a device that was not restored from a backup when the device was
    being set up. The 'configure as new' gets Apple's default name ("Lillian's Apple Watch").

    Candidates: Same owner and device type (not AirPods or accessories), a higher
        model number, not tracked by an iCloud3 device.
    Name match: The candidate's name is the tracked device's name without the model
        or possessive ('s) (device_name_parser.name_device_type_key).
    Retired: The tracked device was unpaired, erased or is being removed.
    Offline: The tracked device has been offline for more than an hour.

        Name match, retired or offline  - Track the newer device
        Name match, both are online     - Repairs issue, Submit tracks the newer device
        No name match, retired, 1 found - Repairs issue, Submit tracks the newer device
        More than 1 found               - Repairs notice listing them

    An HA Repair Issue is created notifying the user of the config change if there
    is no clear winner.

    Issues that no longer apply are removed. Issues posted again keep their HA
    'Ignore' state.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    issue_id_prefix = f"{REPAIR_ISSUE_DEVICE_REPLACED}_{devicename}"

    # The same rules are used by AADevices._request_restart_if_tracked_device_replaced
    # during a refresh so a restart it requests reassigns the device here
    candidates, name_matches = AppleAcct.AADevices.find_replacement_devices(AADev)
    if candidates is None:
        clear_repair_issues(issue_id_prefix)
        return

    old_device_status_msg = (
                'unpaired or erased' if AADev.is_retired else
                'offline for more than 1 hour' if AADev.is_offline_stale else
                'online and available')

    issue_id = None

    # If there is only 1 match, and the config device is retired or offline,
    # change the config to the new device
    if len(name_matches) == 1:
        NewAADev = name_matches[0]
        if AADev.is_retired or AADev.is_offline_stale:
            _change_config_to_new_device(AppleAcct, NewAADev, conf_device)
        else:
            issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADev,
                                                NewAADev, old_device_status_msg)

    # If there are no matches but there is 1 candidate device that may work, the config
    # is not changed but a Repair Issue is created. Submitting the Repair Issue will
    # accept the new device as the replacement and update the config
    elif len(name_matches) == 0 and len(candidates) == 1 and AADev.is_retired:
        issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADev,
                                                candidates[0], old_device_status_msg)

    elif len(name_matches) > 1 or (len(candidates) > 1 and AADev.is_retired):
        issue_id = _post_repair_issue_no_aa_device_assignment(
                                                issue_id_prefix, conf_device, AADev,
                                                name_matches or candidates,
                                                old_device_status_msg)

    clear_repair_issues(issue_id_prefix, keep_issue_ids=[issue_id])

#............................................................................
# HA Repairs issues for a newer Apple device. The issue's text is in 'issues' in
# strings.json & translations/en.json. The translation key is the issue_id prefix.
REPAIR_ISSUE_DEVICE_REPLACED          = 'device_replaced'
REPAIR_ISSUE_DEVICE_REASSIGNED        = 'device_reassigned'
REPAIR_ISSUE_APPLE_ACCT_REASSIGNED    = 'apple_acct_reassigned'

def _name_model(AADev):
    return f"{AADev.name} ({AADev.model_display_name})"

#............................................................................
def _post_repair_issue_aa_device_assignment(AppleAcct, conf_device, AADev, NewAADev,
                                            old_device_status_msg):
    '''
    Post the Repairs issue asking to track the newer device. Submit runs
    _fix_repair_issue_aa_device_assignment.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname  = conf_device[CONF_FNAME]

    issue_id = post_repair_issue(
                issue_id   = f"{REPAIR_ISSUE_DEVICE_REPLACED}_{devicename}_{NewAADev.device_id8}",
                alert_key  = devicename,
                title      = "Newer Apple Device detected",
                alert_msg  = '',
                fix_action = 'reassign_apple_device',
                fix_data   = {  'apple_id': AppleAcct.apple_id,
                                'device_id': NewAADev.device_id,
                                'name_model': _name_model(NewAADev)},
                translation_key = REPAIR_ISSUE_DEVICE_REPLACED,
                translation_placeholders = {
                                'device': dev_fname,
                                'old_device': _name_model(AADev),
                                'old_device_status': old_device_status_msg,
                                'new_device': _name_model(NewAADev)})

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF_DOT}{_name_model(AADev)}{RARROW}{_name_model(NewAADev)}")

    return issue_id

#............................................................................
def _fix_repair_issue_aa_device_assignment(fix_data):
    '''
    Repairs Submit handler for _post_repair_issue_aa_device_assignment. Track the newer
    device and restart iCloud3. Runs in an executor thread.
    '''
    devicename  = fix_data.get('devicename')
    name_model  = fix_data.get('name_model')
    AppleAcct   = Gb.AppleAcct_by_apple_id.get(fix_data.get('apple_id'))
    AADev   = AppleAcct.AADev_by_device_id.get(fix_data.get('device_id')) if AppleAcct else None
    conf_device = [_conf_device for _conf_device in Gb.conf_devices
                            if _conf_device[CONF_IC3_DEVICENAME] == devicename]

    if AADev is None or conf_device == []:
        post_alert(devicename,  f"HA Repairs > Newer Apple Device is no longer available, "
                                f"{CRLF_DOT}{name_model}")
        return False

    _change_config_to_new_device(AppleAcct, AADev, conf_device[0], post_notice=False)

    post_event(devicename,
                f"HA Repairs > Newer Apple Device will now be tracked, "
                f"{AADev.name} ({AADev.model_display_name}), Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('reassign_apple_device', _fix_repair_issue_aa_device_assignment)

#............................................................................
def  _post_repair_issue_no_aa_device_assignment(
                                        issue_id_prefix, conf_device, AADev,
                                        found_AADev_items, old_device_status_msg):
    '''
    Post the Repairs issue listing the newer devices when the correct one could not
    be selected. Submit opens the Update Device screen so one can be selected.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname  = conf_device[CONF_FNAME]
    found_devices = [_name_model(_AADev) for _AADev in found_AADev_items]

    issue_id = post_repair_issue_update_device(
                    issue_id   = f"{issue_id_prefix}_multiple",
                    alert_key  = devicename,
                    title      = "Newer Apple Devices detected",
                    message    = (
                        f"A newer version of one of your Apple Devices is available. Several "
                        f"candidates were found and the correct one could not be selected."
                        f"\n\nConfigured Apple Device for **{dev_fname}**:"
                        f"\n- {_name_model(AADev)} ({old_device_status_msg})"
                        f"\n\nAvailable Apple Devices:\n"
                        + ''.join([f"\n- {found_device}" for found_device in found_devices])
                        + f"\n\nSelect the correct Apple Device on the *Update Device* screen."))

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Current device:"
                f"{CRLF_DOT}{_name_model(AADev)} ({old_device_status_msg})"
                f"{CRLF}Candidates:"
                f"{CRLF_DOT}{CRLF_DOT.join(found_devices)}")

    # Returned so _check_for_replacement_device keeps this issue instead of removing it
    return issue_id

#............................................................................
def _change_config_to_new_device(AppleAcct, AADev, conf_device, post_notice=True):
    '''
    Track the newer device. Update the iCloud3 configuration with the new device's
    device_id, name and model.

    post_notice:
        True - Post the 'Newer Apple Device detected' notice in HA Repairs, the
            alerts sensor and the Event Log. Submit acknowledges and removes it.
        False - The change was requested in HA Repairs
    '''
    try:
        devicename     = conf_device[CONF_IC3_DEVICENAME]
        dev_fname      = conf_device[CONF_FNAME]
        old_aadev_name = conf_device[CONF_AADEV_NAME]
        old_model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]

        conf_device[CONF_AADEV_DEVICE_ID]    = AADev.device_id
        conf_device[CONF_DEVICE_TYPE]        = AADev.device_type.lower()
        conf_device[CONF_RAW_MODEL]          = AADev.raw_model
        conf_device[CONF_MODEL]              = AADev.model
        conf_device[CONF_MODEL_DISPLAY_NAME] = AADev.model_display_name

        _update_Device_model_fields(conf_device)

        if old_aadev_name != AADev.dname:
            _change_config_to_new_device_name(AppleAcct, conf_device, AADev.dname,
                                                write_config_file=False, post_msg=False)

        config_file.write_icloud3_configuration_file()

        AADev.startup_msg = 'UPGRADED'

        if post_notice:
            old_device = f"{old_aadev_name} ({old_model_display_name})"
            post_repair_issue(
                        issue_id   = f"{REPAIR_ISSUE_DEVICE_REASSIGNED}_{devicename}_{AADev.device_id8}",
                        alert_key  = devicename,
                        title      = "Newer Apple Device detected, Configuration updated",
                        alert_msg  = '',
                        translation_key = REPAIR_ISSUE_DEVICE_REASSIGNED,
                        translation_placeholders = {
                                'device': dev_fname,
                                'old_device': old_device,
                                'new_device': _name_model(AADev)})

            post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Configuration updated, New device will be tracked:"
                f"{CRLF_DOT}{old_device}{RARROW}{_name_model(AADev)}")

    except Exception as err:
        log_exception(err)

#............................................................................
def _change_config_model_fields(conf_device, AADev):
    '''
    The config device_id is the Apple device but the model fields are for another
    device. Update the config, the Device and the HA device registry model.
    '''
    try:
        old_model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]

        conf_device[CONF_DEVICE_TYPE]        = AADev.device_type.lower()
        conf_device[CONF_RAW_MODEL]          = AADev.raw_model
        conf_device[CONF_MODEL]              = AADev.model
        conf_device[CONF_MODEL_DISPLAY_NAME] = AADev.model_display_name
        _update_Device_model_fields(conf_device)

        config_file.write_icloud3_configuration_file()

        post_event( f"{conf_device[CONF_FNAME]} > Apple Device Model updated, "
                    f"{AADev.name}{CRLF_DOT}{old_model_display_name}{RARROW}"
                    f"{AADev.model_display_name} ({AADev.raw_model})")

    except Exception as err:
        log_exception(err)

#............................................................................
def _update_Device_model_fields(conf_device):
    '''
    The Device and its device_tracker entity are set up from the configuration in
    Stage 2, before the Apple acct devices are verified and the newer device is
    assigned. Update their model fields and the HA device registry model from the
    updated configuration.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]

    for _Device in [Gb.Devices_by_devicename.get(devicename),
                    Gb.DeviceTrackers_by_devicename.get(devicename)]:
        if _Device is None:
            continue
        _Device.device_type        = conf_device[CONF_DEVICE_TYPE]
        _Device.raw_model          = conf_device[CONF_RAW_MODEL]
        _Device.model              = conf_device[CONF_MODEL]
        _Device.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]

    er_util.update_device_model(devicename, conf_device[CONF_RAW_MODEL])

#............................................................................
def _change_config_to_new_device_name(AppleAcct, conf_device, new_icloud_dname,
                                        write_config_file=True, post_msg=True):
    try:
        # Update the iCloud3 configuration file with the new Apple devicename
        # Set new icloud name in config and internal table, remove the old one:
        old_icloud_dname = conf_device[CONF_AADEV_NAME]
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if Device := Gb.Devices_by_devicename.get(devicename):
            Device.conf_icloud_dname = new_icloud_dname

        dict_del(Gb.devicenames_by_aadev_dname, old_icloud_dname)
        list_del(Gb.conf_icloud_dnames, old_icloud_dname)
        list_add(Gb.conf_icloud_dnames, new_icloud_dname)
        Gb.aadev_dnames_by_devicename[devicename] = new_icloud_dname
        Gb.devicenames_by_aadev_dname[new_icloud_dname] = devicename

        conf_device[CONF_AADEV_NAME] = new_icloud_dname

        if write_config_file:
            config_file.write_icloud3_configuration_file()

        if post_msg:
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Updating Apple Acct Device Name"
                        f"{CRLF_DOT}{old_icloud_dname}{RARROW}{new_icloud_dname}")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _match_AppleAcct_devices_to_Device(AppleAcct, retry_match_devicenames=None):
    '''
    Cycle through the AppleAcct raw data and match that item with the
    conf_devices iCloud entry. Then set the data fields to tie it to
    the Device object.
    '''
    evlog_msg = ''
    unmatched_devicenames = []
    AADevice = AppleAcct.AADevices
    if AADevice is None:
        return

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCT] != AppleAcct.apple_id:
            continue

        devicename      = conf_device[CONF_IC3_DEVICENAME]
        device_id       = conf_device[CONF_AADEV_DEVICE_ID]
        conf_aadev_name = conf_device[CONF_AADEV_NAME]
        Device          = Gb.Devices_by_devicename.get(devicename)

        if Device is None or Device.is_inactive:
            continue

        if retry_match_devicenames and devicename not in retry_match_devicenames:
            continue

        broadcast_info_msg(f"Matching Apple Device > {conf_aadev_name}")

        AADev = AppleAcct.AADev_by_device_id.get(device_id)

        # The device_id is not in the Apple Acct Devices list
        if AADev is None:
            device_id = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
            AADev     = AppleAcct.AADev_by_device_id.get(device_id)

        # The same aadev_name is there, the device name now belongs to another device
        if AADev is None:
            list_add(unmatched_devicenames, conf_aadev_name)

            post_config_error(
                Source      = Device,
                source_name = Device.fname,
                error       = 'Unknown Apple Device',
                error_item  = apple_user_dev(Device.conf_apple_acct_apple_id, conf_aadev_name),
                message     = ( 'The Apple Device assigned to the iCloud3 Device could '
                                'found in the Apple iCloud Data. Verify the correct '
                                'Apple Device was selected for this iCloud3 Device.'),
                details     = ( f"{CRLF_DOT}{Device.fname_devicename} > Apple Device: "
                                f"{apple_user_dev(Device.conf_apple_acct_apple_id, conf_aadev_name)} "
                                f"({conf_device[CONF_MODEL_DISPLAY_NAME]})"),
                repair_step = 'update_device')

            continue

        Gb.devicenames_by_aadev_dname[conf_aadev_name] = devicename
        Gb.aadev_dnames_by_devicename[devicename]      = conf_aadev_name

        AADev.Device           = Device
        AADev.ic3_devicename   = devicename
        Device.AppleAcct           = AppleAcct
        Device.icloud_device_id    = device_id

        Device.icloud_person_id    = AADev.device_data['prsId']
        Device.family_share_device = AADev.device_data['fmlyShare']
        AADev.device_data[CONF_IC3_DEVICENAME] = devicename
        AADev.device_data['dname'] = AADev.dname

        Gb.Devices_by_icloud_device_id[device_id] = Device
        Gb.AppleAcct_by_devicename[devicename]    = AppleAcct

        if Device.family_share_device is False:
            owner_device_ids = Gb.famshr_device_ids_by_apple_id.get(AppleAcct.apple_id, [])
            list_add(owner_device_ids, device_id)
            Gb.famshr_device_ids_by_apple_id[AppleAcct.apple_id] = owner_device_ids

        # Set verify status to a valid device_id exists instead of always True
        # This will pick up devices in the configuration file that no longer exist
        Device.verified_ICLOUD = device_id in AppleAcct.AADev_by_device_id
        Gb.icloud_device_verified_cnt += 1

    return unmatched_devicenames

#----------------------------------------------------------------------------
def _refresh_icloud_data_retry(AppleAcct, missing_aadev_devices=None):
    '''
    Get all the devices that have the Apple device configured that are not
    in the AppleAcct devices list. This  indicates we have a device that
    is tracked via Apple but that device is not in the Apple Account.
    '''

    event_msg =(f"Devices not Found in Apple Data")
    for _devicename, aadev_name in missing_aadev_devices.items():
        devicename = _devicename

        Device = Gb.Devices_by_devicename[devicename]
        event_msg += f"{CRLF_RED_ALERT2}{Device.fname}{RARROW}{Device.conf_icloud_dname}"
    post_event(event_msg)

    try:
        retry_cnt = 0 if AppleAcct.AADevices else 10
        while retry_cnt < 5:
            retry_cnt += 1

            event_msg = (   f"Refreshing Apple Data (#{retry_cnt}), "
                            f"Missing-{list_to_str(list(missing_aadev_devices.values()))}")
            post_greenbar_msg(event_msg)
            post_event(f"{event_msg}")

            AppleAcct.refresh_icloud_data()

            missing_aadev_devices = _get_conf_devices_apple_did_not_locate(AppleAcct)
            if is_empty(missing_aadev_devices):
                post_event("All Devices Found, Continuing with Setup")
                return

    except Exception as err:
        log_exception(err)

    event_msg =(f"Devices still not Found, Continuing with Setup")
    for devicename, aadev_name in missing_aadev_devices.items():
        Device = Gb.Devices_by_devicename[devicename]
        event_msg += f"{CRLF_RED_ALERT2}{Device.fname}{RARROW}{Device.conf_icloud_dname}"
    post_event(event_msg)

#--------------------------------------------------------------------
def _post_evlog_apple_acct_devices_info(AppleAcct):
    '''
    Cycle through the AppleAcct raw data and display the Event Log message for
    the device indicating if it is:
        - tracked (show the devicename that raw data item is tied to)
        - tracked by another apple_id ( show the other apple_id)
        - not tracked
    '''
    _post_family_share_info(AppleAcct)
    _post_not_assigned_info(AppleAcct)
    _post_tracked_devices_info(AppleAcct)

#--------------------------------------------------------------------
def _post_tracked_devices_info(AppleAcct):
    devices_assigned_msg = reauth_needed_msg = aadev_startup_msg= ''
    devices_assigned_cnt = 0

    if AppleAcct.terms_of_use_update_needed:
        reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Accept Terms of Service Needed"
    if AppleAcct.is_reauth_needed:
        reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Authentication Needed"

    device_cnt = len(AppleAcct.AADev_by_device_id)
    AADev_tracked =  {AADev.dname: AADev
                            for _, AADev in AppleAcct.AADev_by_device_id.items()
                            if AADev.Device}

    dict_sort(AADev_tracked)

    for aadev_dname, AADev in AADev_tracked.items():
        try:
            aadev_startup_msg = ''
            aadev_startup_msg= f", {RED_ALERT}{AADev.startup_msg}" if AADev.startup_msg else ''

            # If the Device is None, this AppleAcct is not tracked or assigned to another apple_id
            # aadevice_dname ending with '.' indicates this is a duplicate device
            try:
                devicename = AADev.ic3_devicename
                Device     = AADev.Device
                if Device is None:
                    continue

                if Device.tracking_mode == INACTIVE:
                    aadev_startup_msg += f', {INACTIVE_SYMB}INACTIVE'

                devices_assigned_msg += (
                            f"{CRLF_CHK}{AADev.name}{RARROW}"
                            f"{Device.fname} "
                            f"({AADev.model_display_name})"
                            f"{aadev_startup_msg}")

                if AADev and Gb.is_log_level_rawdata:
                    log_title =(f"AADevice Data "
                                f"{apple_user_dev(AppleAcct.account_name, devicename)}/"
                                f"{aadev_dname} "
                                f"({AADev.device_identifier})")

            except Exception as err:
                log_exception(err)
            devices_assigned_cnt += 1

        except Exception as err:
            log_exception(err)
            post_error_msg( f"{EVLOG_ALERT}Apple Acct {AppleAcct.apple_user} > "
                            f"{CRLF_DOT}{aadev_dname} Error Listing Device Info")

    evlog_msg =(f"Tracked Devices, "
                f"{devices_assigned_cnt} of {device_cnt}"
                f"{reauth_needed_msg}"
                f"{devices_assigned_msg}")

    post_event(evlog_msg)

#--------------------------------------------------------------------
def _post_family_share_info(AppleAcct):
    owner_icloud_dnames =[_AADev.dname
                    for device_id, _AADev in AppleAcct.AADev_by_device_id.items()
                    if _AADev.family_share_device is False]
    famshr_dnames_msg = [_AADev.dname
                    for device_id, _AADev in AppleAcct.AADev_by_device_id.items()
                    if _AADev.family_share_device]
    devices_assigned_to_other_aa = [
                    f"{conf_device[CONF_AADEV_NAME]} ({apple_user(conf_device[CONF_APPLE_ACCT])})"
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_AADEV_NAME] in AppleAcct.device_id_by_aadev_dname.items()
                        and conf_device[CONF_APPLE_ACCT] != AppleAcct.apple_id)]

    list_sort(owner_icloud_dnames)
    list_sort(famshr_dnames_msg)
    list_sort(devices_assigned_to_other_aa)

    devices_assigned_to_msg = ''
    if isnot_empty(devices_assigned_to_other_aa):
        devices_assigned_to_msg = ( f"{CRLF_DOT}Family Devices tracked by another Apple Acct:"
                                    f"{list_to_str(devices_assigned_to_other_aa)}")

    family_not_located_msg = ''
    if AppleAcct.locate_all_devices is False:
        family_not_located_msg = f"{CRLF_STAR} Family Devices are not located"

    post_event( f"Family Sharing List Info"
                f"{CRLF_DOT} myDevices-{list_to_str(owner_icloud_dnames)}"
                f"{CRLF_DOT} Family Devices-{list_to_str(famshr_dnames_msg)}"
                f"{family_not_located_msg}"
                f"{devices_assigned_to_msg}")

#--------------------------------------------------------------------
def _post_not_assigned_info(AppleAcct):
    devices_not_assigned     = {}
    for aadev_dname, device_id in AppleAcct.device_id_by_aadev_dname.items():
        AADev = AppleAcct.AADev_by_device_id.get(device_id)

        if AADev and AADev.Device is None:
            devices_not_assigned[aadev_dname] = AADev

    dict_sort(devices_not_assigned)

    devices_not_assigned_msg = ''
    for aadev_dname, AADev in devices_not_assigned.items():
        aadev_msg = f", {RED_ALERT}{AADev.startup_msg}" if AADev.startup_msg else \
                    f", Located-{format_age(AADev.location_secs)} "

        devices_not_assigned_msg +=(f"{CRLF_DOT}{aadev_dname} "
                                    f"({AADev.model_display_name})"
                                    f"{aadev_msg}")

    if devices_not_assigned_msg != '':
        post_event( f"Apple Devices Not Assigned to iCloud Device"
                    f"{devices_not_assigned_msg}")

#--------------------------------------------------------------------
def _set_device_data_source(AppleAcct):
    '''
    Cycle through the devices and change the iCloud data source to MobApp
    if there is a problem with the iCloud setup and the MobApp is available
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        for devicename, Device in Gb.Devices_by_devicename.items():
            data_source = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.icloud_device_id:
                device_id = Device.icloud_device_id
                if device_id in AppleAcct.AADev_by_device_id:
                    data_source = ICLOUD
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    AADev = AppleAcct.AADev_by_device_id[device_id]

            if (Device.is_mobapp_monitored and data_source is None):
                data_source = MOBAPP

            if data_source != MOBAPP:
                info_msg = (f"Set AppleAcct Device Id > {Device.devicename}, "
                            f"DataSource-{data_source}, "
                            f"{CRLF}iCloud-({Device.device_id8_icloud}), "
                            f"{Device.model_display_name}")
                post_monitor_msg(info_msg)

            Device.primary_data_source = data_source

        info_msg = ''
        for _device_id, AADev in AppleAcct.AADev_by_device_id.items():
            info_msg += (f"{AADev.name}/{_device_id[:8]}-{AADev.data_source}, ")
        if info_msg == '': info_msg = 'None'
        post_monitor_msg(f"AppleAcct Devices > {info_msg}")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def report_unknown_apple_accounts():
    '''
    Post an Apple Acct error for each Apple Acct assigned to a Device that is not in
    the Apple Accts configuration. Run before the Devices are checked in
    validate_upw_all_apple_accts so a Device error is not also posted for them.

    Return:
        List of the unknown Apple Acct apple_ids that were reported
    '''
    # Gb.conf_apple_ids only has the Apple Accts that were validated, it is not
    # complete if they could not be validated
    if (Gb.conf_data_source_ICLOUD is False
            or Gb.internet_error):
        return []

    # Get the list of apple accts that have been configured in conf_devices that are not in
    # conf_apple_accts. An issue is not created if all of the Devices using it are inactive,
    # their status_msg is set in validate_upw_all_apple_accts.
    unknown_apple_accts = [apple_id for apple_id, Devices in Gb.Devices_by_apple_id.items()
                                    if (apple_id not in Gb.conf_apple_ids
                                            and any(Device.isnot_inactive for Device in Devices))]
    if is_empty(unknown_apple_accts):
        return []

    for apple_id in unknown_apple_accts:
        devices_list = [Device.fname for Device in Gb.Devices_by_apple_id[apple_id]
                                    if Device.isnot_inactive]
        devices_cnt  = len(devices_list)
        apple_acct_status = unknown_apple_acct_status(apple_id)

        match apple_acct_status:
            case 'deleted':
                cause_msg = (f'was set up in iCloud3 and was removed from the iCloud3 '
                            f'Configuration. It is still assigned to the Device(s). Add the '
                            f'Apple Account again or select the correct Apple Account for '
                            f'the Device(s).')
            case 'exists':
                cause_msg = (f'is an Apple Account but it is not set up in the iCloud3 '
                            f'Configuration. Add the Apple Account or select the correct '
                            f'Apple Account for the Device(s).')
            case 'not_found':
                cause_msg = (f'is not an Apple Account, Apple did not find it. The Apple '
                            f'Account was probably entered incorrectly. Select the correct '
                            f'Apple Account for the Device(s).')
            case _:
                cause_msg = (f'is not set up in the iCloud3 Configuration file and needs to be '
                            f'added. This can be caused by:'
                            f'{CRLF_DOT}The Apple Account needs to be added.'
                            f'{CRLF_DOT}The Apple Account was deleted but still assigned to the Device.'
                            f'{CRLF_DOT}The iCloud3 Device Apple Acct selection needs to be corrected.')

        post_config_error(
            Source      = apple_id,
            source_name = apple_user(apple_id),
            error       = 'Unknown Apple Acct',
            error_item  = f'Used by {devices_cnt} Devices',
            message     = ( f'The Apple Account assigned to {devices_cnt} iCloud3 Device(s) '
                            f'{cause_msg}'
                            f'{CRLF}{CRLF}iCloud Location data will not be used for these devices until this is corrected.'),
            details     = ( f'{CRLF_DOT}Apple Acct: {apple_user(apple_id)}'
                            f'{CRLF_DOT}Devices……: {list_to_str(devices_list)}'),
            fix_data    = {'apple_acct_status': apple_acct_status},
            repair_step = 'update_apple_acct')

    return unknown_apple_accts

#--------------------------------------------------------------------
def unknown_apple_acct_status(apple_id):
    '''
    Determine why an Apple Acct assigned to a Device is not in the configuration. The
    local session files are checked first. Apple is only asked if there are none.

    Return:
        'deleted'   - The session files exist. It was a valid Apple Acct that was set
                        up in iCloud3 and then removed from the configuration
        'exists'    - Apple has the apple_id, it was never set up in iCloud3
        'not_found' - Apple does not have the apple_id (entered incorrectly or mangled)
        ''          - Unknown (internet error, Apple's answer was not clear)
    '''
    try:
        if aas.apple_acct_session_files_exist(apple_id):
            apple_acct_status = 'deleted'

        else:
            if Gb.ValidateAppleAcctUPW is None:
                Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()

            apple_id_exists   = Gb.ValidateAppleAcctUPW.apple_id_exists(apple_id)
            apple_acct_status = {True: 'exists', False: 'not_found'}.get(apple_id_exists, '')

    except Exception as err:
        log_exception(err)
        apple_acct_status = ''

    post_monitor_msg(f"Unknown Apple Acct > {apple_user(apple_id)}, Status-{apple_acct_status or 'Unknown'}")

    return apple_acct_status


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP MOBAPP DEVICE -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def setup_tracked_devices_for_mobapp():
    '''
    Get the MobApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.
    '''

    Gb.mobapp_device_verified_cnt = 0
    devices_monitored_cnt = 0
    devices_monitored_msg = devices_not_monitored_msg = devices_not_assigned_msg = ''
    unmatched_mobapp_devices = Gb.mobapp_id_by_mobapp_dname.copy()
    verified_mobapp_fnames = []

    post_dotted_line()
    tracked_msg = ( f"Mobile App Devices > "
                    f"{Gb.conf_mobapp_device_cnt} of "
                    f"{len(Gb.conf_devices)} used by iCloud3")

    Gb.devicenames_x_mobapp_dnames = {}
    for devicename, Device in Gb.Devices_by_devicename.items():
        broadcast_info_msg(f"Set up Mobile App Devices > {devicename}")

        conf_mobapp_dname = Device.mobapp[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')
        Gb.devicenames_x_mobapp_dnames[devicename] = None

        if conf_mobapp_dname in ['', 'None']:
            Device.initialize_mobapp_device_tracker_entity_name()
            continue

        # Check if the specified mobapp device tracker is valid and in the entity registry
        title = message = detail = ''
        repair_issue = False
        if conf_mobapp_dname.startswith('ScanFor: ') is False:
            if conf_mobapp_dname in Gb.mobapp_id_by_mobapp_dname:
                mobapp_dname = conf_mobapp_dname
                Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
                Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename

            else:
                repair_issue = True
                Device.status_msg[CONF_MOBILE_APP_DEVICE] = ERR_UNKNOWN
                Device.set_button_prefix_icon(GREEN_ALERT)

        else:
            mobapp_dname = _scan_for_for_mobapp_device( devicename, Device, conf_mobapp_dname)
            if mobapp_dname:
                Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
                Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename
            else:
                repair_issue = True
                Device.status_msg[CONF_MOBILE_APP_DEVICE] = ERR_UNKNOWN
                Device.set_button_prefix_icon(YELLOW_WARNING)

        if repair_issue:
            post_config_error(
                Source      = Device,
                source_name = Device.fname,
                error       = 'Unknown MobApp Device',
                error_item  = conf_mobapp_dname,
                message     = ( 'The Mobile App device assigned to the iCloud3 Device could ot be found '
                                'in the HA Device Registry. Verify that the Mobile App device '
                                'is configured and was selected for this iCloud3 Device.'),
                details     = ( f"{CRLF_DOT}{Device.fname_devicename} > MobApp: {conf_mobapp_dname}"),
                repair_step = 'update_device')



    for devicename, Device in Gb.Devices_by_devicename.items():
        mobapp_dname = Gb.devicenames_x_mobapp_dnames[devicename]
        if mobapp_dname is None:
            continue

        mobapp_id = Gb.mobapp_id_by_mobapp_dname[mobapp_dname]

        # Get fname from MobileApp integration if it is started, otherwise build one for now
        # and reset it when the MobileApp is checked again after HA has started
        if mobapp_id in Gb.mobapp_fnames_by_mobapp_id:
            mobapp_fname = Gb.mobapp_fnames_by_mobapp_id[mobapp_id]
        else:
            mobapp_fname = f"{mobapp_dname.replace('_', ' ').title()}"

            # Fix device type (iphone --> Iphone --> iPhone)
            for _device_type in DEVICE_TYPE_DNS.keys():
                if instr(mobapp_fname, _device_type.title()):
                    mobapp_fname = mobapp_fname.replace(
                            _device_type.title(), DEVICE_TYPE_DNS[_device_type])
                    break

        Device.conf_mobapp_fname = mobapp_fname
        Gb.devicenames_x_mobapp_dnames[mobapp_fname] = devicename

        # device_tracker entity is disabled
        if (mobapp_id in Gb.MobileApp_fnames_disabled
                or TEST.MOBAPP_DISABLED):
            TEST.MOBAPP_DISABLED = False
            Device.set_button_prefix_icon(GREEN_ALERT)
            Device.is_mobapp_device_unavailable = True

            post_config_error(
                    Source      = Device,
                    source_name = Device.fname,
                    error       = 'MobApp Device Disabled',
                    error_item  = mobapp_dname,
                    message     = ( 'An assigned Mobile App device is Disabled and will not be used for '
                                    'for device tracking, zone exit/enter monitoring and battery information.'),
                    details     = ( f"{CRLF_DOT}{Device.fname_devicename} > MobApp: {mobapp_dname}"),
                    repair_step = 'alert')

            continue

        # Build errors message, can still use the Mobile App for zone changes but sensors are not monitored
        if (Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, '') == ''
                or TEST.MOBAPP_BATTERY_ENTITY_ERROR
                or instr(Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')
                or Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, '') == ''
                or instr(Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')):
            TEST.MOBAPP_BATTERY_ENTITY_ERROR = False
            Device.set_button_prefix_icon(GREEN_ALERT)

            post_config_error(
                Source      = Device,
                source_name = Device.fname,
                error       = 'MobApp Sensor Unavailable',
                error_item  = mobapp_dname,
                message     = ( 'An assigned Mobile App device was found in the HA Device Registry '
                                'but its battery sensors were not. The Mobile App device will be used '
                                'for tracking only.'),
                details     = ( f"{CRLF_DOT}{Device.fname_devicename} > MobApp: {mobapp_dname}"),
                repair_step = 'alert')

        verified_mobapp_fnames.append(mobapp_fname)
        Gb.mobapp_device_verified_cnt += 1
        Device.verified_MOBAPP = True
        Device.is_mobapp_monitored = True

        # Set raw_model that will get picked up by device_tracker and set in the device registry if it is still
        # at it's default value. Normally, raw_model is set when setting up FamShr if that is available, FmF does not
        # set raw_model since it is only shared via an email addres or phone number. This will also be saved in the
        # iCloud3 configuration file.
        mobapp_fname, raw_model, model, model_display_name = \
                Gb.device_info_by_mobapp_dname[mobapp_dname]

        # MobAoo model_display_name is the same as the model. If the device has a congig entry
        # use the config_model_display_name value and update the dictionary
        if (model_display_name != Device.model_display_name
            and Device.model_display_name != ''):
            model_display_name = Device.model_display_name
            Gb.device_info_by_mobapp_dname[mobapp_dname] = [mobapp_fname, raw_model, model, model_display_name]

        if ((raw_model and Device.raw_model != raw_model)
                or (model and Device.model != model)
                or (model_display_name and Device.model_display_name != model_display_name)):

            for conf_device in Gb.conf_devices:
                if conf_device[CONF_MOBILE_APP_DEVICE] == mobapp_dname:
                    if raw_model:
                        Device.raw_model = conf_device[CONF_RAW_MODEL] = raw_model
                    if model:
                        Device.model = conf_device[CONF_MODEL] = model
                    if model_display_name:
                        Device.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
                    config_file.write_icloud3_configuration_file()
                    break

        # Setup mobapp entities with data or to be monitored
        Gb.Devices_by_mobapp_dname[mobapp_dname] = Device
        Device.mobapp[DEVICE_TRACKER] = f"device_tracker.{mobapp_dname}"
        Device.mobapp[TRIGGER]        = f"sensor.{Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, '')}"
        Device.mobapp[BATTERY_LEVEL]  = Device.sensors['mobapp_sensor-battery_level'] = \
                                        f"sensor.{Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, '')}"
        Device.mobapp[BATTERY_STATUS] = Device.sensors['mobapp_sensor-battery_status'] = \
                                        f"sensor.{Gb.battery_state_sensors_by_mobapp_dname.get(mobapp_dname, '')}"

        device_msg = (  f"{CRLF_CHK}{mobapp_fname}{RARROW}"
                        f"{Device.fname}/{devicename}")
        if len(device_msg) > 40: device_msg += CRLF_TAB
        device_msg += f" ({model_display_name})"

        devices_monitored_cnt += 1
        devices_monitored_msg += device_msg

        # Remove the mobapp device from the list since we know it is tracked
        if mobapp_dname in unmatched_mobapp_devices:
            unmatched_mobapp_devices.pop(mobapp_dname)

    mobapp_interface.setup_notify_service_name_for_mobapp_devices()

    # Devices in the list were not matched with an iCloud3 device or are disabled
    # Setup not monitored message
    for mobapp_dname, mobapp_id in unmatched_mobapp_devices.items():
        devicename = Gb.devicenames_x_mobapp_dnames.get(mobapp_dname, 'unknown')
        Device     = Gb.Devices_by_devicename.get(devicename)
        conf_mobapp_dname = Device.conf_device[CONF_MOBILE_APP_DEVICE] if Device else ''

        try:
            mobapp_fname = Gb.device_info_by_mobapp_dname[mobapp_dname][0]
            mobapp_model = Gb.device_info_by_mobapp_dname[mobapp_dname][3]

        except Exception as err:
            log_exception(err)
            Device.status_msg[CONF_MOBILE_APP_DEVICE] = ERR_UNKNOWN
            mobapp_fname = f"{mobapp_dname}{ERR_UNKNOWN}"
            update_alert_sensor(Source=Device, error='unknown_mobapp',
                                alert_msg=( f"{Device.fname} > Unknown Mobile App Device "
                                            f"{mobapp_dname})"))
            mobapp_model = ''

        crlf_sym = CRLF_X
        duplicate_msg = ' (DUPLICATE NAME)' if mobapp_fname in verified_mobapp_fnames else ''
        status_msg = ''
        if Device:
            status_msg = "Not Monitored"

            if mobapp_id in Gb.mobapp_fnames_disabled:
                if Device:
                    Device.status_msg[CONF_MOBILE_APP_DEVICE] = ERR_DISABLED_HA
                    status_msg += ERR_DISABLED_HA
                    crlf_sym    = CRLF_RED_ALERT
                else:
                    status_msg += ERR_DISABLED_HA
        else:
            crlf_sym = CRLF_HDOT

        device_msg = (f"{crlf_sym}{mobapp_fname} ({mobapp_model})")
        if Device:
            Device.set_button_prefix_icon(GREEN_ALERT)
            device_msg += f", {Device.devicename}, "
            if len(device_msg) > 40: device_msg += CRLF_TAB
        device_msg += f"{status_msg}{duplicate_msg}"

        if crlf_sym == CRLF_X:
            devices_not_monitored_msg += device_msg
        else:
            devices_not_assigned_msg += device_msg

    if devices_not_assigned_msg != '':
        f"{CRLF_X}Not assigned to an iCloud3 Device: "
        f"{devices_not_assigned_msg}"

    evlog_msg =(f"Mobile App Devices > "
                f"{devices_monitored_cnt} of {len(Gb.conf_devices)} monitored"
                f"{devices_monitored_msg}"
                f"{devices_not_monitored_msg}"
                f"{devices_not_assigned_msg}")
    post_event(evlog_msg)


    return

#--------------------------------------------------------------------
def _scan_for_for_mobapp_device(devicename, Device, conf_mobapp_dname):
    '''
    The conf_mobapp_dname parameter starts with 'ScanFor: '. Scan the list of mobapp
    devices and find the one that starts with the ic3_devicename value

    Return:
        mobapp device_tracker entity name - if it was found
        None - More than one entity or no entities were found
    '''

    scanfor_mobapp_dname = conf_mobapp_dname.replace('ScanFor: ', '')

    matched_mobapp_devices = [k for k, v in Gb.mobapp_id_by_mobapp_dname.items()
                    if k.startswith(scanfor_mobapp_dname) and v.startswith('DISABLED') is False]

    Gb.startup_lists['_.matched_mobapp_devices'] = matched_mobapp_devices

    if TEST.SCAN_FOR_DUPLICATE:
        matched_mobapp_devices = [f'{scanfor_mobapp_dname}_TEST-1',f'{scanfor_mobapp_dname}_TEST-2',]

    if len(matched_mobapp_devices) == 1:
        return matched_mobapp_devices[0]

    else:
        if is_empty(matched_mobapp_devices):
            matched_mobapp_devices = ['No Devices']

        post_config_error(
                Source      = Device,
                source_name = Device.fname,
                error       = 'Mobile App ScanFor Device Failed',
                error_item  = conf_mobapp_dname,
                message     = ( f'The Mobile App device parameter for this device is assigned '
                                f'by scanning the HA Device Registry for a Mobile App Device '
                                f'starting with the Device name ({scanfor_mobapp_dname}_xxx). '
                                f'No devices or more than one device was found. '
                                f"{CRLF_DOT}Found-{list_to_str(matched_mobapp_devices)}"
                                f'{CRLF}{CRLF}The actual device to be used needs to be selected '
                                f'instead of scanning for a device.'),
                details     = ( f"{CRLF_DOT}{Device.fname_devicename} > MobApp: {conf_mobapp_dname}"),
                repair_step = 'update_device')

    return None

#--------------------------------------------------------------------
def log_debug_stage_4_results():

    # if Gb.is_log_level_debug:
    #     log_debug_msg(f"{Gb.Devices=}")
    #     log_debug_msg(f"{Gb.Devices_by_devicename=}")
    #     log_debug_msg(f"{Gb.conf_devicenames=}")
    #     log_debug_msg(f"{Gb.conf_icloud_dnames=}")
    #     self.devices_not_set_up          = []
    #     self.device_id_by_aadev_dname   = {}       # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
    #     self.aadev_dname_by_device_id   = {}       # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
    #     self.device_info_by_aadev_dname = {}       # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro (iPhone15,2)'}
    #     self.device_model_info_by_aadev_dname  = {}       # {'Gary-iPhone': [raw_model,model,model_display_name]}
    #     self.dup_icloud_dname_cnt
    return

#--------------------------------------------------------------------
def set_devices_verified_status():
    '''
    Cycle thru the Devices and set verified status based on data sources
    '''
    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.was_verified = (Device.verified_ICLOUD
                            or  Device.verified_MOBAPP)

        # If the data source is iCloud and the device is not verified, set the
        # data source to MobApp
        if (Device.was_verified
                and Device.is_data_source_ICLOUD
                and Device.verified_ICLOUD is False
                and Device.verified_MOBAPP):
            Device.primary_data_source = MOBAPP


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def identify_tracked_monitored_devices():
    '''
    Cycle thru the devices and determinine the tracked and monitored ones
    '''
    Gb.Devices_by_devicename_tracked   = {}
    Gb.Devices_by_devicename_monitored = {}
    for devicename, Device in Gb.Devices_by_devicename.items():
        if Device.is_tracked:
            Gb.Devices_by_devicename_tracked[devicename] = Device
        elif Device.is_monitored:
            Gb.Devices_by_devicename_monitored[devicename] = Device

    Gb.startup_lists['Gb.Devices_by_devicename_tracked']   = Gb.Devices_by_devicename_tracked
    Gb.startup_lists['Gb.Devices_by_devicename_monitored'] = Gb.Devices_by_devicename_monitored

#------------------------------------------------------------------------------
def _refresh_all_devices_sensors():
    '''
    Rewrite all device sensors in case anything changed diuring config update
    '''
    for Device in Gb.Devices:
        Device.write_ha_sensors_state()

#------------------------------------------------------------------------------
def setup_trackable_devices():
    '''
    Display a list of all the devices that are tracked and their tracking information
    '''

    # Initialize distance_to_other_devices, add other devicenames to this Device's field
    for devicename, Device in Gb.Devices_by_devicename_tracked.items():
        for _devicename, _Device in Gb.Devices_by_devicename.items():
            if devicename != _devicename:
                Device.dist_to_other_devices[_devicename] = [0, 0, 0, '0m/00:00:00']
                Device.near_device_distance         = 0       # Distance to the NearDevice device
                Device.near_device_checked_secs     = 0       # When the nearby devices were last updated
                Device.dist_apart_msg               = ''      # Distance to all other devices msg set in icloud3_main
                Device.dist_apart_msg_by_devicename = {}

        if Device.is_mobapp_monitored:
            Gb.used_data_source_MOBAPP = True

            mobapp_attrs = mobapp_data_handler.get_mobapp_device_trkr_entity_attrs(Device)
            if mobapp_attrs:
                mobapp_data_handler.update_mobapp_data_from_entity_attrs(Device, mobapp_attrs)

        # Set a flag indicating there is a tracked device that does not use the Mobile App
        elif Device.is_tracked:
            Gb.device_not_monitoring_mobapp = True

        # Device is not in configured Apple acct if it was not matched
        apple_id     = Device.conf_apple_acct_apple_id
        apple_acct   = apple_user(apple_id)
        icloud_dname = Device.conf_icloud_dname

        # Get Apple acct owner from AppleAcct
        if apple_id in Gb.AppleAcct_by_apple_id:
            _AppleAcct = Gb.AppleAcct_by_apple_id[apple_id]

            if (_AppleAcct.login_successful
                    and icloud_dname not in _AppleAcct.device_id_by_aadev_dname
                    and Gb.internet_error is False):
                Device.verified_ICLOUD = False
                # update_alert_sensor(Device.fname, (
                #         f"{icloud_dname} > Not in Apple Acct ({apple_acct})"))

    if Gb.use_data_source_ICLOUD is False:
        if Gb.conf_data_source_ICLOUD:
            post_event("Data Source > Apple Account not available")
        else:
            post_event("Data Source > Apple Account not used")

    if Gb.conf_data_source_MOBAPP is False:
        post_event("Data Source > Mobile App not used")

#------------------------------------------------------------------------------
def display_all_devices_config_info(selected_devicenames=None):
    '''
    Display the devices configuration in the Event Log.

    selected_devicenames:
        - A list of devices to display in the Event Log
        - If updating devices in config_flow, the updated devicename is in config_parms_update_control field that is
            controlling the iCloud3 update/restart. Only display the updated device
        - 'all' or None - Display all devices
    '''

    for devicename, Device in dict_reverse_sort(Gb.Devices_by_devicename).items():
        if (selected_devicenames is None
                or 'all' in selected_devicenames
                or devicename in selected_devicenames):
            pass
        else:
            continue

        if Device.alerts_by_alert_key:
            if Device.was_verified is False:
                Device.set_button_prefix_icon(RED_ALERT)
            else:
                Device.set_button_prefix_icon(GREEN_ALERT)

        if Device.was_verified:
            tracking_mode = ''
        else:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_icloud_device_cnt > 0)
            tracking_mode = f"{RED_ALERT}NOT "

        if Device.is_tracked:
            tracking_mode += 'Tracked'
            tracked_data_source = []
            if Device.verified_ICLOUD: list_add(tracked_data_source, 'iCloud')
            if Device.verified_MOBAPP: list_add(tracked_data_source, 'MobApp')
            if tracked_data_source:
                tracking_mode += f" ({list_to_str(tracked_data_source)})"

        elif Device.is_monitored:
            tracking_mode += 'Monitored'
        if instr(tracking_mode, 'NOT'):
            tracking_mode = tracking_mode.upper()
        evlog_msg =(f"{Device.fname_devicename} > {Device.model_display_name}, {tracking_mode}")

        evlog_msg += _build_apple_acct_info_section(devicename, Device)
        evlog_msg += _build_mobapp_info_section(devicename, Device)
        evlog_msg += _build_other_parameters_info_section(devicename, Device)

        post_event(evlog_msg)

#..............................................................................
def _build_apple_acct_info_section(devicename, Device):
    '''
    Build the Apple Account info portion of the device's configuration
    '''
    evlog_msg =(f"{CRLF_DOT}Apple Acct Configuration: "
                f"{Device.status_msg.get(ICLOUD, '')}")

    # Device is not in configured Apple acct if it was not matched
    _apple_user = Device.conf_apple_acct_apple_user

    apple_acct_msg = ''
    apple_owner    = ''
    if Gb.conf_data_source_ICLOUD is False:
        evlog_msg += f"{INACTIVE_SYMB}NOT USED AS A DATA SOURCE"

    elif Device.AppleAcct is None:
        apple_acct_msg = f", {INACTIVE_SYMB}NOT AVAILABLE"
        apple_owner = _apple_user

    else:
        apple_owner = Device.AppleAcct.apple_id_account_owner

    if _apple_user == '' or apple_owner == '':
        evlog_msg += f"{CRLF_HDOT}Acct Owner...: No Apple Device Assigned"
        return evlog_msg

    elif Gb.use_data_source_ICLOUD is False:
        apple_acct_msg = f", {INACTIVE_SYMB}ICLOUD DISABLED"

    elif Device.AADev_icloud is None:
        apple_acct_msg = (f"{CRLF_RED_ALERT}DEVICE IS NOT CONFIGURED")

    #evlog_msg += f"{CRLF_HDOT}Acct Owner...: {_apple_user}{apple_acct_msg}"
    #evlog_msg += (  f"{CRLF_HDOT}Acct Owner...: {_apple_user}"
    evlog_msg += (  f"{CRLF_HDOT}Acct Owner...: {apple_owner}"
                    f"{Device.status_msg.get(CONF_APPLE_ACCT, '')}")

    icloud_dname = Device.conf_icloud_dname

    icloud_dname_msg = ''
    if (Device.conf_apple_acct_apple_id in Gb.AppleAcct_by_apple_id
            and Device.verified_ICLOUD is False):
        icloud_dname_msg = ERR_NOT_IN_AA
        log_error_msg(  f"UNKNOWN APPLE DEVICE > {Device.fname_devicename}, "
                        f"{icloud_dname}  Not in Apple Acct ({_apple_user})")


    if Device.AADev_icloud:
        device_status = Device.AADev_icloud.device_data[ICLOUD_DEVICE_STATUS]
        timestamp     = Device.AADev_icloud.device_data[LOCATION][TIMESTAMP]
        if device_status == '201' and mins_since(timestamp) > 5:
            icloud_dname_msg += (f"{CRLF}{ERR_OFFLINE} > "
                                f"Since-{format_time_age(timestamp)}")
            Device.offline_secs = timestamp

    evlog_msg += f"{CRLF_HDOT}Device Name: {icloud_dname}{icloud_dname_msg}"

    return evlog_msg

#..............................................................................
def _build_mobapp_info_section(devicename, Device):

    evlog_msg = f"{CRLF_DOT}Mobile App Configuration: "

    # MobApp set up for Device but MobApp data source disabled in config
    conf_device_msg = ha_device_msg = ''
    if Gb.conf_data_source_MOBAPP is False:
        evlog_msg += ERR_NOT_DATA_SOURCE

    # MobApp config entry is None, Not used
    if Device.conf_device[CONF_MOBILE_APP_DEVICE] == 'None':
        evlog_msg += f"{CRLF_HDOT}MobApp Device: No MobApp Device Assigned"
        return evlog_msg

    conf_device_msg = Device.status_msg.get(CONF_MOBILE_APP_DEVICE, '')
    trigger_entity  = Device.mobapp[TRIGGER][7:] or 'UNKNOWN'
    bat_lev_entity  = Device.mobapp[BATTERY_LEVEL][7:] or 'UNKNOWN'
    notify_entity   = Device.mobapp[NOTIFY] or 'WAITING FOR NOTIFY SVC TO START"'

    evlog_msg += (  f"{CRLF_HDOT}MobApp Device: {Device.conf_mobapp_fname}{ha_device_msg}"
                    f"{CRLF_HDOT}Device Tracker..: {Device.mobapp[DEVICE_TRACKER]}{conf_device_msg}"
                    f"{CRLF_HDOT}Action Trigger...: {trigger_entity}"
                    f"{CRLF_HDOT}Battery Sensor..: {bat_lev_entity}"
                    f"{CRLF_HDOT}Notifications.....: {notify_entity}")

    return evlog_msg

#..............................................................................
def _build_other_parameters_info_section(devicename, Device):

    # Build evlog msg for the tracking parameters
    evlog_msg = f"{CRLF_DOT}Other Parameters:"
    evlog_msg += f"{CRLF_HDOT}inZone Interval: {format_timer(Device.inzone_interval_secs)}"
    if Device.fixed_interval_secs > 0:
        evlog_msg += f"{CRLF_HDOT}Fixed Interval: {format_timer(Device.fixed_interval_secs)}"
    if 'none' not in Device.log_zones:
        log_zones_fname = [zone_dname(zone) for zone in Device.log_zones]
        log_zones = list_to_str(log_zones_fname)
        log_zones = f"{log_zones.replace(', Name-', f'{RARROW}(')}.csv)"
        evlog_msg += f"{CRLF_HDOT}Log Zone Activity: {log_zones}"

    if Device.track_from_base_zone != HOME:
            evlog_msg += f"{CRLF_HDOT}Primary Track from Zone: {zone_dname(Device.track_from_base_zone)}"
    if Device.track_from_zones != [HOME]:
        tfz_fnames = [zone_dname(zone) for zone in Device.track_from_zones]
        evlog_msg += (f"{CRLF_HDOT}Track from Zones: {list_to_str(tfz_fnames)}")
    if Device.away_time_zone_offset != 0:
        plus_minus = '+' if Device.away_time_zone_offset > 0 else ''
        evlog_msg += (f"{CRLF_HDOT}Away Time Zone: HomeZone {plus_minus}{Device.away_time_zone_offset} hours")

    return evlog_msg

#------------------------------------------------------------------------------
def display_inactive_devices():
    '''
    Display a list of the Inactive devices in the Event Log
    '''

    Gb.inactive_fname_by_devicename = {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE}

    inactive_devices_msg =[( f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]}), "
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE]

    Gb.startup_lists['Gb.inactive_fname_by_devicename'] = Gb.inactive_fname_by_devicename

    if is_empty(Gb.inactive_fname_by_devicename):
        return

    evlog_msg = f"Inactive/Untracked Devices > "
    evlog_msg+= list_to_str(inactive_devices_msg, separator=CRLF_DOT)
    post_event(evlog_msg)

    if len(Gb.inactive_fname_by_devicename) == len(Gb.conf_devices):
        post_greenbar_msg('All devices are Inactive and nothing will be tracked')
        post_alert( f"ALL DEVICES ARE INACTIVE > "
                    f"{more_info('all_devices_inactive')}")

#------------------------------------------------------------------------------
def display_object_lists():
    '''
    Display the object list values
    '''
    broadcast_info_msg(f"Logging Initial Monitor Info")
    monitor_msg = (f"StatZones-{list_to_str(Gb.StatZones_by_zone.keys())}")
    post_monitor_msg(monitor_msg)

    monitor_msg = (f"Devices-{list_to_str(Gb.Devices_by_devicename.keys())}")
    post_monitor_msg(monitor_msg)

    for Device in Gb.Devices:
        monitor_msg = (f"Device-{Device.devicename}, "
                        f"FromZones-{list_to_str(Device.FromZones_by_zone.keys())}")
        post_monitor_msg(monitor_msg)

    monitor_msg = (f"Zones-{list_to_str(Gb.Zones_by_zone.keys())}")
    post_monitor_msg(monitor_msg)

#--------------------------------------------------------------------
def dump_startup_lists_to_log(debug_log_title=None):
    '''
    Cycle thru the Gb.startup_lists dictionary that contains internal lists and
    dictionaries. Write all items to the icloud3-0.log file
    '''
    if Gb.startup_lists == {}:  return

    if debug_log_title:
        log_debug_msg(f"{format_header_box(debug_log_title)}")

    _startup_lists = Gb.startup_lists.copy()
    for field, values in _startup_lists.items():
        log_debug_msg(f"{field}={values}")

    # Check to see if any items were added by another task while writing the list to the
    # log. That can generate a 'RuntimeError: dictionary changed size during iteration'
    items_start = len(_startup_lists)
    items_end   = len(Gb.startup_lists)
    if items_end > items_start:
        cnt = -1
        for field, values in _startup_lists.items():
            cnt += 1
            if cnt >= items_start:
                log_debug_msg(f"{field}={values}")


    if debug_log_title:
        log_debug_msg(f"{format_header_box(debug_log_title)}")

    Gb.startup_lists = {}

#------------------------------------------------------------------------------
def display_platform_operating_mode_msg():
    if Gb.ha_config_platform_stmt is False:
        return

    if Gb.conf_profile[CONF_VERSION] == 1:
        alert_msg =("HA tried to start iCloud3 from a configuration.yaml file statement. "
                    "It was ignored.")
    else:
        post_greenbar_msg('HA configuration.yaml contains a `platform: iCloud3` that can be deleted')
        alert_msg = (f"{EVLOG_ALERT}HA CONFIG CHANGE NEEDED > iCloud3 is an HA Integration. Delete the 'platform: icloud3` "
                "configuration parameters in the HA `configuration.yaml` file.")

    post_event(alert_msg)

#------------------------------------------------------------------------------
def post_restart_icloud3_complete_msg():
    post_event(f"{EVLOG_ATTENTION}Initializing {Gb.icloud3_version_msg} > Complete")

    Gb.EvLog.update_event_log_display("")

#------------------------------------------------------------------------------
def dump_gb_dictionaries_to_icloud_log():
    pass

    Gb.startup_lists['Gb.Devices_by_devicename_tracked']   = Gb.Devices_by_devicename_tracked
    Gb.startup_lists['Gb.Devices_by_devicename_monitored'] = Gb.Devices_by_devicename_monitored
    Gb.startup_lists['Gb.devicenames_by_mobapp_dname']  = Gb.devicenames_by_mobapp_dname
    Gb.startup_lists['Gb.mobile_app_device_fnames']  = Gb.mobile_app_device_fnames
    Gb.startup_lists['Gb.mobapp_fnames_by_mobapp_id'] = Gb.mobapp_fnames_by_mobapp_id
    Gb.startup_lists['Gb.mobapp_ids_by_mobapp_fname'] = Gb.mobapp_ids_by_mobapp_fname
    Gb.startup_lists['Gb.mobapp_fnames_disabled']    = Gb.mobapp_fnames_disabled
    Gb.startup_lists['Gb.model_display_name_by_raw_model']    = Gb.model_display_name_by_raw_model
