

from ..global_variables import GlobalVariables as Gb
from ..const            import (ICLOUD3, DOMAIN,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT, NOTIFY,
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
                                MOBAPP, NO_MOBAPP, ICLOUD_DEVICE_STATUS, TIMESTAMP,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODE_DN,
                                NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
                                LOCATION, LATITUDE, RADIUS,
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
                                    dict_del, dict_sort, dict_reverse_sort, )
from ..utils.messaging      import (broadcast_info_msg, add_log_file_filter,
                                    post_event, post_alert, post_greenbar_msg, post_dotted_line,
                                    post_error_msg, post_monitor_msg, update_alert_sensor,
                                    post_repair_issue, clear_repair_issues, register_repair_fix_handler,
                                    post_internal_error,
                                    log_info_msg, log_debug_msg, log_error_msg, log_warning_msg,
                                    log_data, log_exception, format_filename, log_stack,
                                    internal_error_msg2,
                                    _evlog, _log, more_info, format_header_box,)
from ..utils.dist_util      import (format_dist_km, m_to_um, )
from ..utils.time_util      import (time_now_secs, mins_since, format_timer, format_time_age,
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
def ha_startup_completed(dummy_parameter):

    # HA may have not set up the notify service before iC3 starts. If so, the mobile_app
    # Notify entity was not setup either. Do it now.
    Gb.ha_started = True
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
        Gb.valid_upw_by_username = {}

#------------------------------------------------------------------------------
def create_Devices_object():

    try:
        # _set_ha_device_id_x_devicename()
        er_util.set_ha_device_id_x_devicename()

        old_Devices_by_devicename      = Gb.Devices_by_devicename.copy()
        Gb.Devices                     = []
        Gb.Devices_by_devicename       = {}
        Gb.Devices_by_username         = {}
        Gb.conf_devicenames            = []
        Gb.conf_icloud_dnames          = []
        Gb.devicenames_by_aadev_dname = {}
        Gb.aadev_dnames_by_devicename= {}
        Gb.startup_alerts_by_source    = {}

        # Update the ha_device_id_x_devicename dict and correct any
        # disabled device conflicts between iCloud3 and the ha_device_reg

        for conf_device in Gb.conf_devices:
            devicename   = conf_device[CONF_IC3_DEVICENAME]
            device_fname = conf_device[CONF_FNAME]
            aadev_name = conf_device[CONF_AADEV_NAME]
            username     = conf_device[CONF_APPLE_ACCOUNT]
            apple_acct   = username_id(username)

            # # Device's Apple Acct was not found in the Apple Accts list. It is invalid or
            # # the password has not been verified yet
            # if (Gb.use_data_source_ICLOUD
            #         and username != ''
            #         and aadev_name != 'None'
            #         and username not in Gb.valid_upw_by_username):
            #     conf_apple_acct, _idx = config_file.conf_apple_acct(username)
            #     if _idx < 0:
            #         error_msg = f"Unknown Apple Acct ({apple_acct})"
            #         post_alert( f"{device_fname} > {error_msg}")
            #         update_alert_sensor(device_fname, error_msg)

            #     else:
            #         # Open Apple Acct, Create Apple Acct Objects and login
            #         password = conf_apple_acct[CONF_PASSWORD]
            #         valid_upw = Gb.ValidateAppleAcctUPW.validate_username_password(username, password)

            #         Gb.valid_upw_by_username[username] = valid_upw

            if devicename == '':
                post_greenbar_msg(f"HA device_tracker entity id not configured for {aadev_name}")
                post_alert( f"CONFIGURATION ALERT > The device_tracker entity id (devicename) "
                            f"has not been configured for {aadev_name}/"
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}")
                continue

            Gb.conf_icloud_dnames.append(aadev_name)
            broadcast_info_msg(f"Setting up Device > {devicename}")

            # Do not set up inactive device or one disabled in HA
            if devicename in Gb.ha_disabled_by_by_devicename:
                do_not_track_reason = f'{INACTIVE_SYMB}HA.DISABLED'
            elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
                do_not_track_reason = f'{INACTIVE_SYMB}INACTIVE'
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

            Gb.Devices.append(Device)
            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE:
                continue

            # If Apple acct specified, make sure it is configured and this device is available
            if Device.conf_apple_acct_username in ['', 'None']:
                apple_acct_msg = '✪ NONE'

            elif Gb.internet_error:
                apple_acct_msg =f"{Device.conf_apple_acct_username_id}, INTERNERT UNAVAILABLE"

            elif Device.conf_apple_acct_username not in Gb.valid_upw_by_username:
                apple_acct_msg =f"{RED_ALERT}{Device.conf_apple_acct_username}, UNKNOWN APPLE ACCT"

            elif Gb.valid_upw_by_username.get(Device.conf_apple_acct_username, False) is False:
                apple_acct_msg = f"{RED_ALERT}{Device.conf_apple_acct_username}, INVALID USERNAME/PW"

            else:
                apple_acct_msg = Device.conf_apple_acct_username_id

            #  Build the device's configuration evlog message
            # apple_acct_msg = f"{CRLF_SP5_DOT}Apple Account: {apple_acct_msg}"
            if Device.conf_icloud_dname:
                icloud_dev_msg = f"{Device.conf_icloud_dname} ({Device.model_display_name})"
            else:
                icloud_dev_msg = '✪ NONE'
            mobapp_dev_msg = Device.mobapp[DEVICE_TRACKER] \
                                    if Device.mobapp[DEVICE_TRACKER] else '✪ NONE'
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

            # Initialize device_tracker entity to display before AppleAcct starts up
            Device.write_ha_device_tracker_state()

    except Exception as err:
        log_exception(err)

    _verify_away_time_zone_devicenames()
    _log_device_dictionaries()

    return

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
def log_into_apple_accounts():
    '''
    Verify that all Apple Account AppleAcct objects have been created
    '''
    if Gb.use_data_source_ICLOUD is False:
        return False

    if is_empty(Gb.conf_usernames):
        return False

    # Setup access tp the Apple acct if is is not already setup or anything
    # has changed
    aa_login_error = ''
    results_msg    = ''
    alert_msg      = ''
    for username in Gb.conf_usernames:
        conf_apple_acct, _idx = config_file.conf_apple_acct(username)
        password              = Gb.AppleAcct_password_by_username[username]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices    = conf_apple_acct[CONF_LOCATE_ALL]

        post_dotted_line()
        post_event( f"Setting up Apple Account > {username_id(username)}")

        AppleAcct = Gb.AppleAcct_by_username.get(username)

        # Initial check to see if AppleAcct is available
        can_reuse_AppleAcct = (
            Gb.was_icloud3_reloaded is True
            and AppleAcct is not None
            and isnot_empty(AppleAcct.AADevData_by_device_id)
            and username == AppleAcct.username
            and password == AppleAcct.password
            and apple_server_location == AppleAcct.apple_server_location
            and locate_all_devices == AppleAcct.locate_all_devices)

        # Second check to see if AppleAcct is has no exceptions and can be reused
        if can_reuse_AppleAcct:
            can_reuse_AppleAcct = (
                AppleAcct.is_AADevices_setup_complete
                and AppleAcct.is_authenticated
                and aas.is_authentication_2fa_code_needed(AppleAcct) is False
                and Gb.AppleAcct_error_by_username.get(username, False) is False
                and Gb.iCloudSession_by_username.get(username, None is not None)
                and Gb.valid_upw_by_username.get(username, False)
                and AppleAcct.login_successful is True
                and AppleAcct.auth_failed_503 is False)

        if Gb.valid_upw_by_username.get(username) is False:
            post_alert(f"Logged Failed, Invalid Username/Password")

        elif can_reuse_AppleAcct is False:
            AppleAcct = aas.log_into_apple_account(
                                        username,
                                        password,
                                        apple_server_location,
                                        locate_all_devices)

            if AppleAcct:
                apple_login_msg = 'Login Successful'

            else:
                post_event( f"{CRLF_RED_X} Login Failed, "
                            f"Server Loc-{apple_server_location}")
                alert_msg = EVLOG_ALERT
                update_alert_sensor(username_id(username), "Apple Acct Login Failed")

        else:
            apple_login_msg = 'Already logged in'

        if AppleAcct and AppleAcct.login_successful:
            if AppleAcct.is_authenticated:
                reauth_in_days, reauth_msg = AppleAcct.get_next_reauth_in_days_info_msg()
                AppleAcct.issue_reauth_in_days_alert_msg()
                post_event( f"{apple_login_msg}"
                            f"{CRLF_DOT}Authentication Method-{AppleAcct.login_auth_method}"
                            f"{CRLF_DOT}{reauth_msg}")

            setup_tracked_devices_for_icloud(AppleAcct)

        post_event( f"Setting up Apple Account > {username_id(AppleAcct.username_id)}, Complete")

    Gb.startup_lists['Gb.AppleAcct_error_by_username'] = Gb.AppleAcct_error_by_username

    # Check if the pyicloud_ic3_interface detected the internet is down
    if Gb.internet_error:
        return False

    if (aa_login_error
            or AppleAcct is None
            or is_empty(AppleAcct.AADevData_by_device_id)):
        pass

    elif isnot_empty(Gb.devices_without_location_data):
        post_event( f"Apple Acct > Location data is not available for:"
                    f"{CRLF}{NBSP6}{DOT}{list_to_str(Gb.devices_without_location_data)}")
        post_dotted_line()

    return True

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
    unverified_device_usernames = [Device.conf_apple_acct_username
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if (Device.was_verified is False
                                    and Device.isnot_inactive)]

    Gb.usernames_setup_error_retry_list   = list(set(unverified_device_usernames))
    Gb.devicenames_setup_error_retry_list = list(set(unverified_devices))

    Gb.startup_lists['_.usernames_setup_error_retry_list']   = Gb.usernames_setup_error_retry_list
    Gb.startup_lists['_.devicenames_setup_error_retry_list'] = Gb.devicenames_setup_error_retry_list

    if is_empty(unverified_devices):
        return True

    if retry:
        post_greenbar_msg("1444 Some Tracked Devices could not be verified. Restart may be needed.")
        alert_msg = ("Some Tracked Devices could not be verified. Review and correct "
                    "any configuration errors. Then restart iCloud3")
    else:
        alert_msg = "UNVERIFIED DEVICES ALERT > Some Tracked Devices could not be verified."
    alert_msg += (f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
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
                    or the one created in config_flow if the username was changed.
    '''

    if Gb.conf_data_source_ICLOUD is False:
        post_event("Apple Account > Not used as a data source")
        return

    if Gb.conf_icloud_device_cnt == 0:
        return

    try:
        missing_aadev_devices = _get_conf_devices_apple_did_not_locate(AppleAcct)
        if isnot_empty(missing_aadev_devices):
            _refresh_icloud_data_retry(AppleAcct, missing_aadev_devices)

        _set_device_data_source(AppleAcct)
        _verify_conf_apple_device_parameters(AppleAcct)
        _match_AppleAcct_devices_to_Device(AppleAcct)

        _post_evlog_apple_acct_devices_info(AppleAcct)

    except Exception as err:
        log_exception(err)

    owner = AppleAcct.username_base
    Gb.startup_lists[f"{owner}.AppleAcct.device_id_by_aadev_dname"] = \
                        {k: v[:10] for k, v in AppleAcct.device_id_by_aadev_dname.items()}
    Gb.startup_lists[f"{owner}.AppleAcct.aadev_dname_by_device_id"] = \
                        {k[:10]: v for k, v in AppleAcct.aadev_dname_by_device_id.items()}
    Gb.startup_lists[f"Gb.Devices_by_icloud_device_id"]     = \
                        {k[:10]: v for k, v in Gb.Devices_by_icloud_device_id.items()}

#----------------------------------------------------------------------------
def _get_conf_devices_apple_did_not_locate(AppleAcct):
    aadev_names = [_AADevData.name for _AADevData in AppleAcct.AADevData_items]
    missing_aadev_devices = {}
    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        devicename = conf_device[CONF_IC3_DEVICENAME]
        device_id  = conf_device[CONF_AADEV_DEVICE_ID]
        aadev_name = conf_device[CONF_AADEV_NAME]

        if (aadev_name not in aadev_names
                and device_id not in AppleAcct.AADevData_by_device_id):
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
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        try:
            conf_device_id  = conf_device[CONF_AADEV_DEVICE_ID]
            conf_aadev_name = conf_device[CONF_AADEV_NAME]
            broadcast_info_msg(f"Verifying Apple Device > {conf_aadev_name}")

            # Get Device specified in config file using the device_id
            AADevData = AppleAcct.AADevData_by_device_id.get(conf_device_id)

            # The config AA device was found using the device_id but this device is now a
            # duplicate. This means a newer device with the same name and owner has
            # been added to the Apple Acct (current config=iPhone16, AA data=iPhone18).
            # Change the ic3_devicename to now use the newer device .
            if AADevData and AADevData.is_duplicate_dname:
                NewerAADevData = _find_newer_same_name_device(AppleAcct, AADevData)
                if NewerAADevData:
                    _change_config_to_new_device(AppleAcct, NewerAADevData, conf_device)
                continue

            # The config AA device with this device_id is no longer in the Apple Acct
            # device list (it was removed), get the AA device that now has the config
            # name (Gary-iPhone) if it exists
            if AADevData is None:
                device_id  = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
                AADevData  = AppleAcct.AADevData_by_device_id.get(device_id)

                # An AA device was found with the same name, change config to it
                if AADevData:
                    _change_config_to_new_device(AppleAcct, AADevData, conf_device)

                # The AA device with the config name (Gary-iPhone) is no longer in
                # the Apple Acct devices list. Make sure the login was successful and
                # all devices were returned instead of Apple returning a partial device list
                elif AppleAcct.login_successful is False:
                    post_alert( f"{conf_device[CONF_FNAME]} > "
                                f"Device was not found"
                                f"{CRLF_DOT}{conf_aadev_name}, "
                                f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")
                continue

            # The config file device_id was found, see if it was renamed. The dname has
            # the owner's name if another family member has a device with the same name.
            if conf_aadev_name != AADevData.dname:
                _change_config_to_new_device_name(AppleAcct, conf_device, AADevData.dname)
                continue

            # if conf_device[CONF_TRACKING_MODE] != INACTIVE:
            # The AA device was not found using the config name or replaced with a device
            # with the same name. Review the devices available and see if there is a
            # device with another name that matches the parameters of the one being checked
            _check_for_replacement_device(AppleAcct, conf_device, AADevData)

        except Exception as err:
            log_exception(err)
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Error verifying Apple Acct Device"
                        f"{CRLF_DOT}{conf_aadev_name}, "
                        f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")

#............................................................................
def _find_newer_same_name_device(AppleAcct, AADevData):
    '''
    Return the device with the same name and owner that is not a duplicate. It is
    the newest device with that name (_resolve_duplicate_dnames).
    '''
    for _AADevData in AppleAcct.AADevData_by_device_id.values():
        if (_AADevData
                and _AADevData.active
                and _AADevData.is_duplicate_dname is False
                and _AADevData.name == AADevData.name
                and _AADevData.prs_id == AADevData.prs_id):
            return _AADevData

    return None

#............................................................................
def _check_for_replacement_device(AppleAcct, conf_device, AADevData):
    '''
    See if a newer device that is not tracked replaced the tracked device. We are
    chedking for a device that was not restored from a backup when the device was
    being set up. The 'configure as new' gets Apple's default name ("Lillian's Apple Watch").

    Candidates: Same owner and device type (not AirPods or accessories), a higher
        model number, not tracked by an iCloud3 device.
    Name match: The candidate's name is the tracked device's name without the model
        or possessive ('s) (device_name_parser.owner_device_name_key).
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
    dev_fname      = conf_device[CONF_FNAME]
    issue_id_prefix = f"device_replaced_{devicename}"

    # The same rules are used by AADevices._request_restart_if_tracked_device_replaced
    # during a refresh so a restart it requests reassigns the device here
    candidates, name_matches = AppleAcct.AADevices.find_replacement_devices(AADevData)
    if candidates is None:
        clear_repair_issues(issue_id_prefix)
        return

    old_device_msg = f"{AADevData.name} ({AADevData.model_display_name})"
    old_device_status_msg = (
                'unpaired or erased' if AADevData.is_retired else
                'offline for more than 1 hour' if AADevData.is_offline_stale else
                'online and available')

    issue_id = None

    # If there is only 1 match, and the config device is retired or offline,
    # change the config to the new device
    if len(name_matches) == 1:
        NewAADevData = name_matches[0]
        if AADevData.is_retired or AADevData.is_offline_stale:
            _change_config_to_new_device(AppleAcct, NewAADevData, conf_device)
        else:
            issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADevData,
                                                NewAADevData, old_device_status_msg)

    # If there are no matches but there is 1 candidate device that may work, the config
    # is not changed but a Repair Issue is created. Submitting the Repair Issue will
    # accept the new device as the replacement and update the config
    elif len(name_matches) == 0 and len(candidates) == 1 and AADevData.is_retired:
        issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADevData,
                                                candidates[0], old_device_status_msg)

    elif len(name_matches) > 1 or (len(candidates) > 1 and AADevData.is_retired):
        found_AADevData_items = name_matches or candidates
        found_devices_msg     = CRLF_DOT.join([f"{_AADevData.name} ({_AADevData.model_display_name})"
                                                for _AADevData in found_AADevData_items])
        issue_id = _post_repair_issue_no_aa_device_assignment(
                                                issue_id_prefix, devicename, dev_fname,
                                                old_device_msg, old_device_status_msg,
                                                found_devices_msg)

    clear_repair_issues(issue_id_prefix, keep_issue_ids=[issue_id])

#............................................................................
def _post_repair_issue_aa_device_assignment(AppleAcct, conf_device, AADevData, NewAADevData,
                                            old_device_status_msg):
    '''
    Post the Repairs issue asking to track the newer device. Submit runs
    _fix_repair_issue_aa_device_assignment.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname  = conf_device[CONF_FNAME]
    name_model = f"{NewAADevData.name} ({NewAADevData.model_display_name})"

    issue_id = post_repair_issue(
                issue_id   = f"device_replaced_{devicename}_{NewAADevData.device_id8}",
                alert_key  = devicename,
                title      = f"{dev_fname}, Newer Apple Device detected",
                alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                f"The iCloud3 Configuration needs to be updated to use "
                                f"the newer device."
                                f"{CRLF}{CRLF}Change Apple Device for *{dev_fname}*:"
                                f"{CRLF_DOT}{AADevData.name} ({AADevData.model_display_name}){RARROW}"
                                f"{NewAADevData.name} ({NewAADevData.model_display_name})"
                                f"{CRLF}{CRLF}Click Submit to confirm this selection and "
                                f"update the configuration for *{dev_fname}*"),
                fix_action = 'reassign_apple_device',
                fix_data   = {  'username': AppleAcct.username,
                                'device_id': NewAADevData.device_id,
                                'name_model': name_model})

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF_DOT}{AADevData.name} ({AADevData.model_display_name}){RARROW}"
                f"{NewAADevData.name} ({NewAADevData.model_display_name})")

    return issue_id

#............................................................................
def _fix_repair_issue_aa_device_assignment(fix_data):
    '''
    Repairs Submit handler for _post_repair_issue_aa_device_assignment. Track the newer
    device and restart iCloud3. Runs in an executor thread.
    '''
    devicename  = fix_data.get('devicename')
    name_model  = fix_data.get('name_model')
    AppleAcct   = Gb.AppleAcct_by_username.get(fix_data.get('username'))
    AADevData   = AppleAcct.AADevData_by_device_id.get(fix_data.get('device_id')) if AppleAcct else None
    conf_device = [_conf_device for _conf_device in Gb.conf_devices
                            if _conf_device[CONF_IC3_DEVICENAME] == devicename]

    if AADevData is None or conf_device == []:
        post_alert(devicename,  f"HA Repairs > Newer Apple Device is no longer available, "
                                f"{CRLF_DOT}{name_model}")
        return False

    _change_config_to_new_device(AppleAcct, AADevData, conf_device[0], post_notice=False)

    post_event(devicename,
                f"HA Repairs > Newer Apple Device will now be tracked, "
                f"{AADevData.name} ({AADevData.model_display_name}), Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('reassign_apple_device', _fix_repair_issue_aa_device_assignment)

#............................................................................
def  _post_repair_issue_no_aa_device_assignment(
                                        issue_id_prefix, devicename, dev_fname,
                                        old_device_msg, old_device_status_msg,
                                        found_devices_msg):

    issue_id = post_repair_issue(
                    issue_id   = f"{issue_id_prefix}_multiple",
                    alert_key  = devicename,
                    title      = f"{dev_fname}, Newer Apple Devices detected",
                    alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                    f"Several candidates have been identifiedd and the "
                                    f"correct one could not be selected."
                                    f"{CRLF}{CRLF}Configured Apple Device for *{dev_fname}*:"
                                    f"{CRLF_DOT}{old_device_msg} ({old_device_status_msg})"
                                    f"{CRLF}{CRLF}Available Devices:"
                                    f"{CRLF_DOT}{found_devices_msg}"
                                    f"{CRLF}{CRLF}Select the correct Apple Device on the *iCloud3 "
                                    f"Update Device* Configuration screen for *{dev_fname}*."))

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Current device:"
                f"{CRLF_DOT}{old_device_msg} ({old_device_status_msg})"
                f"{CRLF}Candidates:"
                f"{CRLF_DOT}{found_devices_msg}")

    # Returned so _check_for_replacement_device keeps this issue instead of removing it
    return issue_id

#............................................................................
def _change_config_to_new_device(AppleAcct, AADevData, conf_device, post_notice=True):
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

        conf_device[CONF_AADEV_DEVICE_ID]    = AADevData.device_id
        conf_device[CONF_DEVICE_TYPE]        = AADevData.device_type.lower()
        conf_device[CONF_RAW_MODEL]          = AADevData.raw_model
        conf_device[CONF_MODEL]              = AADevData.model
        conf_device[CONF_MODEL_DISPLAY_NAME] = AADevData.model_display_name
        _update_Device_model_fields(conf_device)

        if old_aadev_name != AADevData.dname:
            _change_config_to_new_device_name(AppleAcct, conf_device, AADevData.dname,
                                                write_config_file=False, post_msg=False)

        config_file.write_icloud3_configuration_file()

        AADevData.startup_msg = 'UPGRADED'

        if post_notice:
            post_repair_issue(
                        issue_id   = f"device_reassigned_{devicename}_{AADevData.device_id8}",
                        alert_key  = devicename,
                        title      = f"{dev_fname}, Newer Apple Device detected",
                        alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                        f"The iCloud3 configuration was updated to use "
                                        f"the newer device."
                                        f"{CRLF}{CRLF}Updated Apple Device for *{dev_fname}*:"
                                        f"{CRLF_DOT}{old_aadev_name} ({old_model_display_name}){RARROW}"
                                        f"{AADevData.name} ({AADevData.model_display_name})"
                                        f"{CRLF}{CRLF}If this is wrong, change the name of the device "
                                        f"in the *Settings App* to another name. Then select it on the "
                                        f"*iCloud3 Update Device* Configuration screen for *{dev_fname}*"))

            post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Configuration updated, New device will be tracked:"
                f"{CRLF_DOT}{old_aadev_name} ({old_model_display_name}){RARROW}"
                f"{AADevData.name} ({AADevData.model_display_name})")

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
    missing_aadev_devicenames = []
    AADevice = AppleAcct.AADevices
    if AADevice is None:
        return

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
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

        AADevData = AppleAcct.AADevData_by_device_id.get(device_id)

        # The device_id is not in the Apple Acct Devices list
        if AADevData is None:
            device_id  = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
            AADevData  = AppleAcct.AADevData_by_device_id.get(device_id)

        # The same aadev_name is there, the device name now belongs to another device
        if AADevData is None:
            list_add(missing_aadev_devicenames, conf_aadev_name)
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Error Matching Apple Acct Device"
                        f"{CRLF_DOT}{conf_aadev_name}, "
                        f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")
            continue

        Gb.devicenames_by_aadev_dname[conf_aadev_name] = devicename
        Gb.aadev_dnames_by_devicename[devicename]      = conf_aadev_name

        AADevData.Device           = Device
        AADevData.ic3_devicename   = devicename
        Device.AppleAcct           = AppleAcct
        Device.icloud_device_id    = device_id

        Device.icloud_person_id    = AADevData.device_data['prsId']
        Device.family_share_device = AADevData.device_data['fmlyShare']
        AADevData.device_data[CONF_IC3_DEVICENAME] = devicename
        AADevData.device_data['dname'] = AADevData.dname

        Gb.Devices_by_icloud_device_id[device_id] = Device
        Gb.AppleAcct_by_devicename[devicename]    = AppleAcct

        if Device.family_share_device is False:
            owner_device_ids = Gb.owner_device_ids_by_username.get(AppleAcct.username, [])
            list_add(owner_device_ids, device_id)
            Gb.owner_device_ids_by_username[AppleAcct.username] = owner_device_ids

        # Set verify status to a valid device_id exists instead of always True
        # This will pick up devices in the configuration file that no longer exist
        Device.verified_ICLOUD = device_id in AppleAcct.AADevData_by_device_id
        Gb.icloud_device_verified_cnt += 1

    return missing_aadev_devicenames

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

            event_msg = f"Refreshing Location Data (#{retry_cnt})"
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
def _set_any_Device_alerts():
    '''
    Set Alerts for devices
    '''

    device_not_found_msg = ''
    apple_acct_not_found_msg = ''
    apple_acct_login_failed_devices = ''

    for Device in Gb.Devices:
        # Device's Apple acct error
        if (Device.conf_apple_acct_username == ''
                or Device.conf_icloud_dname == ''
                or Device.was_verified is False
                or Device.conf_apple_acct_username in Gb.AppleAcct_error_by_username):
            continue

        if Device.conf_apple_acct_username not in Gb.AppleAcct_by_username:
            Device.set_fname_alert(YELLOW_ALERT)
            apple_acct_not_found_msg += (
                    f"{CRLF_DOT}Apple Acct-{Device.conf_apple_acct_username_id} > "
                    f"{Device.fname_devicename}")

            update_alert_sensor(Device.fname, (
                    f"{Device.conf_icloud_dname} "
                    f"Apple Acct Login Problem ({Device.conf_apple_acct_username_id})"))

        # Device's Apple acct ok but device not in Apple acct
        elif (Device.AppleAcct
                and Device.AppleAcct.device_id_by_aadev_dname.get(Device.conf_icloud_dname) is None):
            Device.set_fname_alert(YELLOW_ALERT)
            error_msg = (
                    f"{Device.conf_icloud_dname} "
                    f"Not in Apple Acct ({Device.AppleAcct.username_base})")
            device_not_found_msg += (f"{CRLF_DOT}{Device.fname_devicename} > {error_msg}")
            update_alert_sensor(Device.fname, error_msg)

            log_error_msg(f"iCloud3 Device Configuration Error > "
                        f"{Device.fname_devicename}, {error_msg}")

    if Gb.internet_error:
        return

    if device_not_found_msg:
        post_alert( f"APPLE ACCOUNT DEVICE NOT FOUND > "
                    f"A device was not found in it's Apple Acct, iCloud Location will not be used:"
                    f"{device_not_found_msg}")
    if apple_acct_not_found_msg:
        post_alert( f"APPLE ACCOUNT NOT LOGGED INTO > "
                    f"A device's Apple Acct was not logged into, iCloud Location will not be used:"
                    f"{apple_acct_not_found_msg}")

#--------------------------------------------------------------------
def _post_evlog_apple_acct_devices_info(AppleAcct):
    '''
    Cycle through the AppleAcct raw data and display the Event Log message for
    the device indicating if it is:
        - tracked (show the devicename that raw data item is tied to)
        - tracked by another username ( show the other username)
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

    device_cnt = len(AppleAcct.AADevData_by_device_id)
    AADevData_tracked =  {AADevData.dname: AADevData
                            for _, AADevData in AppleAcct.AADevData_by_device_id.items()
                            if AADevData.Device}

    dict_sort(AADevData_tracked)

    for aadev_dname, AADevData in AADevData_tracked.items():
        try:
            aadev_startup_msg = ''
            aadev_startup_msg= f", {RED_ALERT}{AADevData.startup_msg}" if AADevData.startup_msg else ''

            # If the Device is None, this AppleAcct is not tracked or assigned to another username
            # aadevice_dname ending with '.' indicates this is a duplicate device
            try:
                devicename = AADevData.ic3_devicename
                Device     = AADevData.Device
                if Device is None:
                    continue

                if Device.tracking_mode == INACTIVE:
                    aadev_startup_msg += f', {INACTIVE_SYMB}INACTIVE'

                devices_assigned_msg += (
                            f"{CRLF_CHK}{AADevData.name}{RARROW}"
                            f"{Device.fname} "
                            f"({AADevData.model_display_name})"
                            f"{aadev_startup_msg}")

                if AADevData and Gb.is_log_level_rawdata:
                    log_title =(f"AADevice Data {AppleAcct.account_name}{LINK}"
                                f"{devicename}/{aadev_dname} "
                                f"({AADevData.device_identifier})")

            except Exception as err:
                log_exception(err)
            devices_assigned_cnt += 1

        except Exception as err:
            log_exception(err)
            post_error_msg( f"{EVLOG_ALERT}Apple Acct {AppleAcct.username_id} > "
                            f"{CRLF_DOT}{aadev_dname} Error Listing Device Info")

    evlog_msg =(f"Tracked Devices, "
                f"{devices_assigned_cnt} of {device_cnt}"
                f"{reauth_needed_msg}"
                f"{devices_assigned_msg}")

    post_event(evlog_msg)

#--------------------------------------------------------------------
def _post_family_share_info(AppleAcct):
    owner_icloud_dnames =[_AADevData.dname
                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                    if _AADevData.family_share_device is False]
    famshr_dnames_msg = [_AADevData.dname
                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                    if _AADevData.family_share_device]
    devices_assigned_to_other_aa = [
                    f"{conf_device[CONF_AADEV_NAME]} ({username_id(conf_device[CONF_APPLE_ACCOUNT])})"
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_AADEV_NAME] in AppleAcct.device_id_by_aadev_dname.items()
                        and conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username)]

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
        AADevData = AppleAcct.AADevData_by_device_id.get(device_id)
        # if AADevData is None or AADevData.Device:
        #     continue
        if AADevData and AADevData.Device is None:
            devices_not_assigned[aadev_dname] = AADevData

    dict_sort(devices_not_assigned)

    devices_not_assigned_msg = ''
    for aadev_dname, AADevData in devices_not_assigned.items():
        aadev_msg = f", {RED_ALERT}{AADevData.startup_msg}" if AADevData.startup_msg else ''
        devices_not_assigned_msg +=(f"{CRLF_DOT}{aadev_dname} "
                                    f"({AADevData.model_display_name})"
                                    f"{aadev_msg}")

    if devices_not_assigned_msg != '':
        post_event( f"Devices Not Tracked"
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

        # Gb.Devices_by_icloud_device_id = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            data_source = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.icloud_device_id:
                device_id = Device.icloud_device_id
                if device_id in AppleAcct.AADevData_by_device_id:
                    data_source = ICLOUD
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    AADevData = AppleAcct.AADevData_by_device_id[device_id]

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
        for _device_id, AADevData in AppleAcct.AADevData_by_device_id.items():
            info_msg += (f"{AADevData.name}/{_device_id[:8]}-{AADevData.data_source}, ")
        if info_msg == '': info_msg = 'None'
        post_monitor_msg(f"AppleAcct Devices > {info_msg}")

    except Exception as err:
        log_exception(err)


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

    mobapp_error_mobile_app_msg = ''
    mobapp_error_search_msg     = ''
    mobapp_error_disabled_msg   = ''
    mobapp_error_not_found_msg  = ''
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
        if conf_mobapp_dname.startswith('ScanFor: ') is False:
            if conf_mobapp_dname in Gb.mobapp_id_by_mobapp_dname:
                mobapp_dname = conf_mobapp_dname
                Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
                Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename

            else:
                update_alert_sensor(Device.fname, f"Unknown MobApp Device ({conf_mobapp_dname})")
                Device.set_fname_alert(RED_ALERT)
                mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                f"Assigned to {Device.fname_devicename}")
        else:
            mobapp_dname = _scan_for_for_mobapp_device( devicename, Device, conf_mobapp_dname)
            if mobapp_dname:
                Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
                Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename
            else:
                update_alert_sensor(Device.fname, f"Unknown ScanFor MobApp Device ({conf_mobapp_dname})")
                Device.set_fname_alert(RED_ALERT)
                mobapp_error_search_msg += (f"{CRLF_X}{conf_mobapp_dname}_??? > "
                                            f"Assigned to {Device.fname_devicename}")

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
        if mobapp_id in Gb.MobileApp_fnames_disabled:
            update_alert_sensor(Device.fname, f"MobApp Device Disabled ({mobapp_dname})")
            Device.set_fname_alert(RED_ALERT)
            Device.is_mobapp_device_unavailable = True
            mobapp_error_disabled_msg += (  f"{CRLF_DOT}{mobapp_dname} > "
                                            f"Assigned to-{Device.fname_devicename}")
            continue

        # Build errors message, can still use the Mobile App for zone changes but sensors are not monitored
        if (Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, '') == ''
                or instr(Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')
                or Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, '') == ''
                or instr(Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')):
            Device.set_fname_alert(RED_ALERT)
            mobapp_error_mobile_app_msg += (f"{CRLF_DOT}{mobapp_dname} > "
                                            f"Assigned to {Device.fname_devicename}")

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
            mobapp_fname = f"{RED_ALERT}{mobapp_dname} (UNKNOWN DEVICE)"
            update_alert_sensor(mobapp_dname, "Unknown Mobile App Device")
            mobapp_model = ''

        crlf_sym = CRLF_X
        duplicate_msg = ' (DUPLICATE NAME)' if mobapp_fname in verified_mobapp_fnames else ''
        status_msg = ''
        if Device:
            status_msg = "Not Monitored"

            if mobapp_id in Gb.mobapp_fnames_disabled:
                if Device:
                    status_msg  = ", DISABLED IN MOBAPP"
                    crlf_sym    = CRLF_RED_ALERT
                else:
                    status_msg += ', Disabled in MobApp'
        else:
            crlf_sym = CRLF_HDOT
            # status_msg = 'Not used'

        device_msg = (f"{crlf_sym}{mobapp_fname} ({mobapp_model})")
        if Device:
            Device.set_fname_alert(RED_ALERT)
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

    _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_search_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg)

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

    conf_mobapp_dname = conf_mobapp_dname.replace('ScanFor: ', '')

    matched_mobapp_devices = [k for k, v in Gb.mobapp_id_by_mobapp_dname.items()
                    if k.startswith(conf_mobapp_dname) and v.startswith('DISABLED') is False]

    Gb.startup_lists['_.matched_mobapp_devices'] = matched_mobapp_devices

    if len(matched_mobapp_devices) == 1:
        return matched_mobapp_devices[0]

    elif len(matched_mobapp_devices) == 0:
        return None

    elif len(matched_mobapp_devices) > 1:
        mobapp_dname = matched_mobapp_devices[-1]
        post_greenbar_msg( f"Mobile App device_tracker entity scan found several devices: "
                            f"{Device.fname_devicename}")

        post_alert( f"DUPLICATE MOBAPP DEVICES FOUND > More than one Device Tracker Entity "
                    f"was found during the scan of the HA Device Registry."
                    f"{CRLF_X}AssignedTo-{Device.fname_devicename}"
                    f"{CRLF}{more_info('mobapp_error_multiple_devices_on_scan')}"
                    f"{CRLF}{'-'*75}"
                    f"{CRLF}Count-{len(matched_mobapp_devices)}, "
                    f"{CRLF}Entities-{', '.join(matched_mobapp_devices)}, "
                    f"{CRLF}Monitored-{mobapp_dname}")

        log_error_msg(f"iCloud3 Error > Mobile App Config Error > Dev Trkr Entity not found "
                    f"during scan_for {conf_mobapp_dname}_???. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")
        return mobapp_dname

    return None

#--------------------------------------------------------------------
def _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_scan_for_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg):

    if mobapp_error_mobile_app_msg:
        post_greenbar_msg( f"Mobile App Integration missing trigger or battery sensors"
                            f"{mobapp_error_mobile_app_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBILE APP INTEGRATION (Mobile App) SET UP PROBLEM > The Mobile App "
                    f"Integration `last_update_trigger` and `battery_level` sensors are disabled or "
                    f"were not found during the scan of the HA Entities Registry for a Device."
                    f"iCloud3 will use the Mobile App for Zone (State) changes but update triggers and/or "
                    f"battery information will not be available for these devices."
                    f"{mobapp_error_mobile_app_msg}"
                    f"{more_info('mobapp_error_mobile_app_msg')}")

        log_error_msg(f"iCloud3 Error > The Mobile App Integration has not been set up or the "
                    f"battery_level or last_update_trigger sensor entities were not found."
                    f"{mobapp_error_mobile_app_msg}")

    if mobapp_error_scan_for_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_scan_for_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBAPP DEVICE NOT FOUND > An MobApp device_tracker "
                    f"entity was not found in the `Scan for mobile_app devices` in the HA Device Registry."
                    f"{mobapp_error_scan_for_msg}"
                    f"{more_info('mobapp_error_scan_for_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_scan_for_msg}. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_not_found_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_not_found_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBAPP DEVICE NOT FOUND > The device tracker entity "
                    f"was not found during the scan of the HA Device Registry."
                    f"{mobapp_error_not_found_msg}"
                    f"{more_info('mobapp_error_not_found_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity was not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_not_found_msg}. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_disabled_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity disabled"
                            f"{mobapp_error_disabled_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBILE APP DEVICE DISABLED > The device tracker entity "
                    f"is disabled so the mobile_app last_update_trigger and bettery_level sensors "
                    f"can not be monitored. iCloud3 will not use the Mobile App for these devices."
                    f"{mobapp_error_disabled_msg}"
                    f"{more_info('mobapp_error_disabled_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity is disabled and "
                    f"can not be monitored by iCloud3."
                    f"{mobapp_error_disabled_msg}"
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

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
        username     = Device.conf_apple_acct_username
        apple_acct   = username_id(username)
        icloud_dname = Device.conf_icloud_dname

        # Get Apple acct owner from AppleAcct
        if username in Gb.AppleAcct_by_username:
            _AppleAcct = Gb.AppleAcct_by_username[username]

            if (_AppleAcct.login_successful
                    and icloud_dname not in _AppleAcct.device_id_by_aadev_dname
                    and Gb.internet_error is False):
                Device.verified_ICLOUD = False
                update_alert_sensor(Device.fname, (
                        f"{icloud_dname} Not in Apple Acct ({apple_acct})"))

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

        if Device.fname in Gb.alerts_sensor_attrs:
            if Device.was_verified is False:
                Device.evlog_fname_alert_char = RED_ALERT
            else:
                Device.evlog_fname_alert_char = YELLOW_ALERT

        if Device.was_verified:
            tracking_mode = ''
        else:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_icloud_device_cnt > 0)
            tracking_mode = f"{RED_ALERT}NOT "

        tracking_mode += 'Monitored' if Device.is_monitored else 'Tracked'
        if instr(tracking_mode, 'NOT'):
            tracking_mode = tracking_mode.upper()
        evlog_msg =(f"{Device.fname_devicename} > {Device.model_display_name}, {tracking_mode}")

        # Device is not in configured Apple acct if it was not matched
        username     = Device.conf_apple_acct_username
        apple_acct   = Device.AppleAcct.username_account_owner if Device.AppleAcct else username_id(username)
        icloud_dname = Device.conf_icloud_dname
        apple_acct_err_msg = icloud_dname_err_msg = ''

        # Get Apple acct owner from AppleAcct
        if username == '' or username in Gb.AppleAcct_error_by_username:
            pass
        elif (Device.conf_apple_acct_username in Gb.AppleAcct_by_username
                and Device.verified_ICLOUD is False):
            icloud_dname_err_msg = f", {RED_ALERT}Not in Apple Acct"
            log_error_msg(f"iCloud3 Device Configuration Error > "
                    f"{Device.fname_devicename}, "
                    f"{icloud_dname} Not in Apple Acct ({apple_acct})")
        # Not using Apple as a data source
        elif apple_acct == '' or apple_acct.startswith('Not used'):
            apple_acct = 'None (NOT SPECIFIED)'

        elif Gb.internet_error:
            pass

        # Apple acct is not found in AppleAcct
        elif Device.conf_apple_acct_username in Gb.AppleAcct_by_username:
            pass

        elif Gb.use_data_source_ICLOUD is False:
            apple_acct_err_msg = f", {INACTIVE_SYMB}ICLOUD DISABLED"

        else:
            apple_acct_err_msg = f", {RED_ALERT}APPLE ACCT ERROR"
            update_alert_sensor(Device.fname, f"Unknown Apple Acct ({apple_acct})")
            log_error_msg(  f"iCloud3 Device Configuration Error > "
                            f"{Device.fname_devicename}, "
                            f"Unknown Apple Acct ({apple_acct})")

        if Gb.internet_error:
            apple_acct_err_msg = f", {RED_ALERT}Not Available"

        # Build the Apple acct evlog msg
        evlog_msg += f"{CRLF_DOT}Apple Account Configuration:"

        if apple_acct == '' and icloud_dname == '':
            evlog_msg += f"{CRLF_HDOT}Not used as a location data source"

        else:
            evlog_msg+=(f"{CRLF_HDOT}Acct Owner...: {apple_acct}{apple_acct_err_msg}"
                        f"{CRLF_HDOT}Device Name: {icloud_dname}{icloud_dname_err_msg}")

        # Build MobApp evlog config msg
        if Device.mobapp[DEVICE_TRACKER] == '':
            if Device.conf_mobapp_fname:
                evlog_msg += f"{CRLF_RED_ALERT}Mobile App Device > {Device.conf_mobapp_fname}, Not Found"
            else:
                evlog_msg += (  f"{CRLF_DOT}Mobile App Configuration:"
                                f"{CRLF_HDOT}Not used as a location data source")

        else:
            evlog_msg += CRLF_DOT if Device.is_mobapp_monitored else CRLF_RED_ALERT
            evlog_msg += f"Mobile App Configuration:"

            trigger_entity = Device.mobapp[TRIGGER][7:] or 'UNKNOWN'
            bat_lev_entity = Device.mobapp[BATTERY_LEVEL][7:] or 'UNKNOWN'
            notify_entity  = Device.mobapp[NOTIFY] or 'WAITING FOR NOTIFY SVC TO START"'
            evlog_msg += (  f"{CRLF_HDOT}MobApp Device: {Device.conf_mobapp_fname}"
                            f"{CRLF_HDOT}Device Tracker..: {Device.mobapp[DEVICE_TRACKER]}"
                            f"{CRLF_HDOT}Action Trigger...: {trigger_entity}"
                            f"{CRLF_HDOT}Battery Sensor..: {bat_lev_entity}"
                            f"{CRLF_HDOT}Notifications.....: {notify_entity}")

        # Build evlog m sg for the tracking parameters
        evlog_msg += f"{CRLF_DOT}Other Parameters:"
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

        try:
            if Gb.use_data_source_ICLOUD:
                if Device.AADevData_icloud is None:
                    evlog_msg += (f"{CRLF_RED_ALERT}DEVICE IS NOT CONFIGURED")
                else:
                    device_status = Device.AADevData_icloud.device_data[ICLOUD_DEVICE_STATUS]
                    timestamp     = Device.AADevData_icloud.device_data[LOCATION][TIMESTAMP]
                    if device_status == '201' and mins_since(timestamp) > 5:
                        evlog_msg += (f"{CRLF_RED_ALERT}DEVICE IS OFFLINE > "
                                    f"Since-{format_time_age(timestamp)}")
                        Device.offline_secs = timestamp

        except Exception as err:
            log_exception(err)
            pass

        post_event(evlog_msg)

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
