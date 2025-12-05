

from ..global_variables import GlobalVariables as Gb
from ..const            import (VERSION, VERSION_BETA, ICLOUD3, ICLOUD3_VERSION, DOMAIN, ICLOUD3_VERSION_MSG,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT, NOTIFY,
                                HOME, ERROR, NONE_FNAME,
                                STATE_TO_ZONE_BASE, CMD_RESET_PYICLOUD_SESSION,
                                EVLOG_ALERT, EVLOG_IC3_STARTING, EVLOG_NOTICE, EVLOG_IC3_STAGE_HDR,
                                ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                CIRCLE_LETTERS_DARK,
                                EVENT_RECDS_MAX_CNT_BASE, EVENT_RECDS_MAX_CNT_ZONE,
                                ALERTS_SENSOR_ATTRS,
                                CRLF, CRLF_DOT, CRLF_CHK, CRLF_SP3_DOT, HDOT, CRLF_SP5_DOT, CRLF_HDOT, LINK, LLINK, RLINK, CRLF_CIRCLE_X,
                                CRLF_SP3_HDOT, CRLF_INDENT, CRLF_X, CRLF_TAB, DOT, CRLF_SP8_HDOT, CRLF_SP8_DOT,
                                CRLF_RED_X, RED_X, CRLF_RED_ALERT, RED_ALERT, CRLF_RED_MARK, CRLF_STAR,
                                CRLF_RED_ALERT, RED_ALERT, YELLOW_ALERT, UNKNOWN,
                                RARROW, NBSP2, NBSP4, NBSP6, CIRCLE_STAR, INFO_SEPARATOR, DASH_20, CHECK_MARK,
                                ICLOUD, FAMSHR,
                                DEVICE_TYPE_FNAME, DEVICE_TYPE_FNAMES,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS,
                                MOBAPP, NO_MOBAPP, ICLOUD_DEVICE_STATUS, TIMESTAMP,
                                INACTIVE_DEVICE,                                 NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
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
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_FAMSHR_DEVICE_ID,
                                CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_ZONE, CONF_NAME,
                                DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                                )

from ..utils                import entity_io
from ..utils.utils          import (instr, is_empty, isnot_empty, yes_no, circle_letter, zone_dname,
                                    is_statzone, isnot_statzone, list_to_str, list_add, list_del, list_keys,
                                    username_id, )
from ..utils.messaging      import (broadcast_info_msg,
                                    post_event, post_alert, post_greenbar_msg,
                                    post_error_msg, post_monitor_msg, update_alert_sensor,
                                    post_internal_error,
                                    log_info_msg, log_debug_msg, log_error_msg, log_warning_msg,
                                    log_data, log_exception, format_filename, log_stack,
                                    internal_error_msg2,
                                    _evlog, _log, more_info, format_header_box,)
from ..utils.dist_util      import (format_dist_km, m_to_um, )
from ..utils.time_util      import (time_now_secs, mins_since, format_timer, format_time_age,
                                    secs_to_hhmm, secs_to_time, )
from ..utils.file_io        import (directory_exists, make_directory,  copy_file,
                                    get_filename_list, get_directory_filename_list,)

from ..apple_acct           import apple_acct_support as aas
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
    Gb.icloud_cookie_directory        = Gb.hass.config.path(STORAGE_DIR, 'icloud3.apple_acct')
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

    if is_empty(Gb.config_parms_update_control):
        return


    # Make copy and Reinitialize so it will not be run again from the 5-secs loop
    config_parms_update_control = Gb.config_parms_update_control.copy()
    Gb.config_parms_update_control = []

    post_event( f"Configuration Loading > "
                f"Type-{list_to_str(config_parms_update_control).title()}")

    if 'restart' in config_parms_update_control:
        post_greenbar_msg(f"Restarting {ICLOUD3_VERSION_MSG}")
        Gb.EvLog.display_user_message('iCloud3 is Restarting')
        post_event(f"{EVLOG_IC3_STARTING}Restart Requested > {ICLOUD3_VERSION_MSG}")
        initialize_data_source_variables()
        Gb.restart_icloud3_request_flag = True
        return

    post_event(f"{EVLOG_IC3_STAGE_HDR}")
    if 'general' in config_parms_update_control:
        set_global_variables_from_conf_parameters()

    if 'special_zone' in Gb.config_parms_update_control:
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

    if 'tracking' in config_parms_update_control:
        post_event("Tracking parameters updated")
        initialize_data_source_variables()

    elif 'devices' in config_parms_update_control:
        post_event("Device parameters updated")
        initialize_data_source_variables()
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
                        f'<br>File-*{evlog_url}*'
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
    Gb.center_in_zone_flag          = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    Gb.display_zone_format          = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    Gb.display_gps_lat_long_flag    = DEFAULT_GENERAL_CONF[CONF_DISPLAY_GPS_LAT_LONG]
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

    Gb.distance_method_waze_flag    = True
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

    initialize_on_initial_load()

#------------------------------------------------------------------------------
def initialize_on_initial_load():
    # Initialize these variables only when starting up
    # Do not initialize them on a restart

    if Gb.initial_icloud3_loading_flag is False:
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
        Gb.picture_www_dirs             = Gb.conf_profile[CONF_PICTURE_WWW_DIRS]

        Gb.password_srp_enabled         = Gb.conf_tracking[CONF_PASSWORD_SRP_ENABLED]

        Gb.um                           = Gb.conf_general[CONF_UNIT_OF_MEASUREMENT]
        Gb.time_format_12_hour          = Gb.conf_general[CONF_TIME_FORMAT].startswith('12')
        Gb.time_format_24_hour          = not Gb.time_format_12_hour
        Gb.device_tracker_state_source  = Gb.conf_general[CONF_DEVICE_TRACKER_STATE_SOURCE]
        Gb.display_zone_format          = Gb.conf_general[CONF_DISPLAY_ZONE_FORMAT]
        Gb.display_gps_lat_long_flag    = Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]
        Gb.center_in_zone_flag          = Gb.conf_general[CONF_CENTER_IN_ZONE]
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
        Gb.discard_poor_gps_inzone_flag = Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]
        Gb.distance_between_device_flag = Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]

        Gb.tfz_tracking_max_distance   = Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]
        Gb.monitored_devices_location_sensors_flag = 'md_location_sensors' in Gb.conf_sensors['monitored_devices']

        # Setup the Stationary Zone location and times
        # The stat_zone_base_lat/long will be adjusted after the Home zone is set up
        Gb.statzone_fname                 = Gb.conf_general[CONF_STAT_ZONE_FNAME].strip()
        Gb.statzone_still_time_secs       = Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] * 60
        Gb.statzone_inzone_interval_secs  = Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL] * 60
        Gb.is_statzone_used               = (14400 > Gb.statzone_still_time_secs > 0)

        # Time Zone offset
        Gb.away_time_zone_1_offset        = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]
        Gb.away_time_zone_1_devices       = Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES].copy()
        Gb.away_time_zone_2_offset        = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]
        Gb.away_time_zone_2_devices       = Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES].copy()

        Gb.log_level                      = Gb.conf_general[CONF_LOG_LEVEL]
        Gb.log_level_devices              = Gb.conf_general[CONF_LOG_LEVEL_DEVICES]

        # update the interval time for each of the interval types (i.e., ipad: 2 hrs, no_mobapp: 15 min)
        inzone_intervals = Gb.conf_general[CONF_INZONE_INTERVALS]
        Gb.inzone_interval_secs = {}
        Gb.inzone_interval_secs[IPHONE]     = inzone_intervals[IPHONE] * 60
        Gb.inzone_interval_secs[IPAD]       = inzone_intervals[IPAD] * 60
        Gb.inzone_interval_secs[WATCH]      = inzone_intervals[WATCH] * 60
        Gb.inzone_interval_secs[IPOD]       = inzone_intervals[IPHONE] * 60
        Gb.inzone_interval_secs[AIRPODS]    = inzone_intervals[AIRPODS] * 60
        Gb.inzone_interval_secs[NO_MOBAPP]  = inzone_intervals[NO_MOBAPP] * 60
        Gb.inzone_interval_secs[CONF_INZONE_INTERVAL] = inzone_intervals['other'] * 60

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

def ha_stopping(dummy_parameter):
    post_event("HA Shutting Down")
    Gb.EvLog.display_user_message("HA Shutting Down, Waiting for HA Startup to Finish")

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
    Gb.encode_password_flag         = Gb.conf_tracking[CONF_ENCODE_PASSWORD]

    Gb.AppleAcct_logging_in_usernames= []

    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'famshr'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('famshr', ICLOUD)
    if instr(Gb.conf_tracking[CONF_DATA_SOURCE], 'mobapp'):
        Gb.conf_tracking[CONF_DATA_SOURCE] = Gb.conf_tracking[CONF_DATA_SOURCE].replace('mobapp', MOBAPP)

    Gb.conf_data_source_ICLOUD    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], ICLOUD)
    Gb.conf_data_source_ICLOUD    = Gb.conf_data_source_ICLOUD
    Gb.conf_data_source_MOBAPP    = instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)

    Gb.use_data_source_ICLOUD     = Gb.conf_data_source_ICLOUD and Gb.username and Gb.password
    Gb.use_data_source_MOBAPP     = Gb.conf_data_source_MOBAPP
    Gb.primary_data_source        = ICLOUD if Gb.use_data_source_ICLOUD else MOBAPP

    Gb.devices                    = Gb.conf_devices
    Gb.icloud_force_update_flag   = False
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
            post_greenbar_msg('568 No data sources have been set up')
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

    Gb.log_debug_flag   = instr(log_level, 'debug')
    Gb.log_rawdata_flag = instr(log_level, 'rawdata')
    Gb.log_rawdata_flag_unfiltered = instr(log_level, 'unfiltered')
    Gb.log_rawdata_flag = Gb.log_rawdata_flag or Gb.log_rawdata_flag_unfiltered
    Gb.log_debug_flag   = Gb.log_debug_flag or Gb.log_rawdata_flag
    Gb.evlog_trk_monitors_flag = Gb.evlog_trk_monitors_flag or instr(log_level, 'eventlog')

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

    Gb.distance_method_waze_flag = Gb.conf_general[CONF_WAZE_USED]
    if Gb.distance_method_waze_flag is False:
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

    if Gb.initial_icloud3_loading_flag:
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

            if instr(evlog_recd, 'const version'):
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
        if Gb.initial_icloud3_loading_flag:
            event.async_track_state_added_domain(Gb.hass, 'zone', zone_handler.ha_added_zone_entity_id)
            event.async_track_state_removed_domain(Gb.hass, 'zone', zone_handler.ha_removed_zone_entity_id)
        if Gb.initial_icloud3_loading_flag is False:
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
            Gb.Waze.__init__(   Gb.distance_method_waze_flag,
                                Gb.waze_min_distance,
                                Gb.waze_max_distance,
                                Gb.waze_realtime,
                                Gb.waze_region)
            Gb.WazeHist.__init__(
                                Gb.waze_history_database_used,
                                Gb.waze_history_max_distance,
                                Gb.waze_history_track_direction)
        else:
            Gb.Waze = Waze(     Gb.distance_method_waze_flag,
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
        device_tracker_entities, device_tracker_entity_data = \
                entity_io.get_entity_registry_data(platform='icloud3', domain=DEVICE_TRACKER)

        old_Devices_by_devicename  = Gb.Devices_by_devicename.copy()
        Gb.Devices                 = []
        Gb.Devices_by_devicename   = {}
        Gb.Devices_by_username     = {}
        Gb.conf_devicenames        = []
        Gb.conf_icloud_dnames      = []
        Gb.devicenames_by_icloud_dname = {}
        Gb.icloud_dnames_by_devicename = {}
        Gb.startup_alerts_by_source = {}

        for conf_device in Gb.conf_devices:
            devicename   = conf_device[CONF_IC3_DEVICENAME]
            device_fname = conf_device[CONF_FNAME]
            icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
            username     = conf_device[CONF_APPLE_ACCOUNT]
            apple_acct   = username_id(username)

            #  Device's Apple Acct was not found in the Apple Accts list. It is invalid or
            # the password has not been verified yet
            if (Gb.use_data_source_ICLOUD
                    and username != ''
                    and icloud_dname != 'None'
                    and username not in Gb.valid_upw_by_username):
                conf_apple_acct, _idx = config_file.conf_apple_acct(username)
                if _idx < 0:
                    error_msg = f"Unknown Apple Acct ({apple_acct})"
                    post_alert( f"{device_fname} > {error_msg}")
                    update_alert_sensor(device_fname, error_msg)

                else:
                    password = conf_apple_acct[CONF_PASSWORD]
                    valid_upw = Gb.ValidateAppleAcctUPW.validate_username_password(username, password)

                    Gb.valid_upw_by_username[username] = valid_upw

            if devicename == '':
                post_greenbar_msg(f"HA device_tracker entity id not configured for {icloud_dname}")
                post_alert( f"CONFIGURATION ALERT > The device_tracker entity id (devicename) "
                            f"has not been configured for {icloud_dname}/"
                            f"{DEVICE_TYPE_FNAME(conf_device[CONF_DEVICE_TYPE])}")
                continue

            Gb.conf_icloud_dnames.append(icloud_dname)
            broadcast_info_msg(f"Setting up Device > {devicename}")

            # Do not set up inactive device
            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE_DEVICE:
                post_event( f"{CIRCLE_STAR} {conf_device[CONF_FNAME]} ({devicename}) > "
                            f"{DEVICE_TYPE_FNAME(conf_device[CONF_DEVICE_TYPE])}, INACTIVE, "
                            f"{CRLF_DOT}iCloud Device-{icloud_dname}"
                            f"{CRLF_DOT}MobApp Entity-{conf_device[CONF_MOBILE_APP_DEVICE]}")
                continue

            # This list is based on the configuration, it will be rebuilt when the devices are verified
            # after the iCloud data has been read. It is also rebuild in config_flow when a device is updated
            devicename  = conf_device.get(CONF_IC3_DEVICENAME)
            Gb.devicenames_by_icloud_dname[icloud_dname] = devicename
            Gb.icloud_dnames_by_devicename[devicename]   = icloud_dname

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, conf_device)
                post_monitor_msg(f"INITIALIZED Device > {Device.fname_devicename}")

            else:
                Device = iCloud3_Device(devicename, conf_device)

                post_monitor_msg(f"ADDED Device > {Device.fname_devicename}")

            Gb.Devices.append(Device)
            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

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

            #  Build the device's configuration evlog  message
            apple_acct_msg = f"{CRLF_SP5_DOT}Apple Account: {apple_acct_msg}"
            icloud_dev_msg = Device.conf_icloud_dname if Device.conf_icloud_dname else '✪ NONE'
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
                            f"{apple_acct_msg}"
                            f"{CRLF_SP5_DOT}iCloud Device: {icloud_dev_msg}"
                            f"{CRLF_SP5_DOT}MobApp Entity: {mobapp_dev_msg}")

            if Device.track_from_base_zone != HOME:
                evlog_msg += f"{CRLF_SP5_DOT}Primary 'Home' Zone: {zone_dname(Device.track_from_base_zone)}"
            if Device.track_from_zones != [HOME]:
                evlog_msg += f"{CRLF_SP5_DOT}Track from Zones: {list_to_str(Device.track_from_zones)}"
            post_event(evlog_msg)

            try:
                # Added the try/except to not generate an error if the device was not in the registry
                # Get the ha device_registry device_id
                Device.ha_device_id = device_tracker_entity_data[f"{DEVICE_TRACKER_DOT}{devicename}"]['device_id']
                Gb.Devices_by_ha_device_id[Device.ha_device_id] = Device

                # Initialize device_tracker entity to display before AppleAcct starts up
                Device.write_ha_device_tracker_state()
            except:
                pass

    except Exception as err:
        log_exception(err)

    _verify_away_time_zone_devicenames()

    Gb.startup_lists['Gb.Devices']                     = Gb.Devices
    Gb.startup_lists['Gb.DeviceTrackers_by_devicename']= Gb.DeviceTrackers_by_devicename
    Gb.startup_lists['Gb.Devices_by_devicename']       = Gb.Devices_by_devicename
    Gb.startup_lists['Gb.conf_devicenames']            = Gb.conf_devicenames
    Gb.startup_lists['Gb.conf_icloud_dnames']          = Gb.conf_icloud_dnames
    Gb.startup_lists['Gb.devicenames_by_icloud_dname'] = Gb.devicenames_by_icloud_dname
    Gb.startup_lists['Gb.icloud_dname_by_devicenames'] = Gb.icloud_dnames_by_devicename

    return

#--------------------------------------------------------------------
def update_devices_non_tracked_fields():
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if Device := Gb.Devices_by_devicename.get(devicename):
            Device.initialize_non_tracking_config_fields(conf_device)

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
                Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES].remove(devicename)
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
                Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES].remove(devicename)
                update_conf_file_flag = True

        if Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0

    if update_conf_file_flag:
        config_file.write_icloud3_configuration_file()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
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
        password = Gb.AppleAcct_password_by_username[username]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices    = conf_apple_acct[CONF_LOCATE_ALL]

        AppleAcct = Gb.AppleAcct_by_username.get(username)
        if Gb.valid_upw_by_username.get(username) is False:
            results_msg += f"{CRLF_RED_X}{username_id(username)}, Not Logged in, Invalid Username-Password"
            alert_msg = EVLOG_ALERT

        elif (AppleAcct is None
                or AppleAcct.AADevData_by_device_id == {}
                or username != AppleAcct.username
                or password != AppleAcct.password
                or apple_server_location != AppleAcct.apple_server_location
                or locate_all_devices != AppleAcct.locate_all_devices):

            AppleAcct = aas.log_into_apple_account(
                                        username,
                                        password,
                                        apple_server_location,
                                        locate_all_devices)

            if AppleAcct:
                if AppleAcct.is_authenticated:
                    results_msg += (f"{CRLF_CHK}{AppleAcct.username_account_owner_short}, "
                                    f"Login Successful, {AppleAcct.auth_method}")
            else:
                results_msg += (f"{CRLF_RED_X}{username_id(username)}, Login Failed, "
                                f"Server Loc-{apple_server_location}")
                alert_msg = EVLOG_ALERT
                update_alert_sensor(username_id(username), "Apple Acct Login Failed")

        else:
            results_msg += f"{CRLF_CHK}{AppleAcct.username_account_owner_short}, Already logged in"

    post_event(f"{alert_msg}Apple Acct > Log in and Authenticate{results_msg}")

    Gb.startup_lists['Gb.AppleAcct_error_by_username'] = Gb.AppleAcct_error_by_username

    # Tell HA to generate reauth needed notification that will be handled
    # handled in config_flow
    if isnot_empty(Gb.AppleAcct_needing_reauth_via_ha):
        try:
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
        except Exception as err:
            log_exception(err)

        AppleAcct.new_2fa_code_already_requested_flag = True
        post_event( f"Apple Acct > {Gb.AppleAcct_needing_reauth_via_ha['account_owner']}, "
                    f"Auth request submitted to HA")

    # Check if the pyicloud_ic3_interface detected the internet is down
    if Gb.internet_error:
        return False

    if (aa_login_error
            or is_empty(AppleAcct.AADevData_by_device_id)):
        pass

    elif is_empty(Gb.devices_without_location_data):
        post_event(f"Apple Acct > All Tracked Devices Located")

    else:
        post_alert( f"Apple Acct > Some Tracked Devices not Located:"
                    f"{CRLF}{NBSP6}{DOT}{list_to_str(Gb.devices_without_location_data)}")

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
                            if Device.verified_flag is False and Device.isnot_inactive]
    unverified_device_usernames = [Device.conf_apple_acct_username
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if (Device.verified_flag is False
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

#------------------------------------------------------------------
def setup_data_source_ICLOUD(retry=False):
    '''
    Cycle through all the apple accounts and match their devices to the iCloud3 Device.
    Then set the device source for each Device.
    Now that all of the devices are set up (natched and unmatched), cycle back througn
    the apple accounts and display the info for all accounts and all devices. This is done
    so an earlier account that has the same device that is tracked by a later account has
    the account info to display.
    '''

    for username, AppleAcct in Gb.AppleAcct_by_username.items():
        if AppleAcct.login_failed:
            if username in Gb.AppleAcct_error_by_username:
                reason = f"{AppleAcct.error_reason}"
                if AppleAcct.error_next_retry_secs > 0:
                    reason += f", Retry at {secs_to_hhmm(AppleAcct.error_next_retry_secs)}"
            else:
                reason =  'Devices not Available'
            post_alert( f"Apple Acct > {username_id(username)}, "
                        f"Login Failed, {reason}")
            update_alert_sensor(username_id(username),
                        f"Apple Login Failed, {reason}")

            continue

        if is_empty(AppleAcct.AADevData_by_device_id):
            AppleAcct.refresh_icloud_data()

        if AppleAcct and Gb.valid_upw_by_username.get(username):
            setup_tracked_devices_for_icloud(AppleAcct)
            set_device_data_source(AppleAcct)

    # Now that all devices are set up, cycle through them again and display the
    # final results in the EvLog
    for username, AppleAcct in Gb.AppleAcct_by_username.items():
        if AppleAcct.login_failed:
            continue

        if AppleAcct and Gb.valid_upw_by_username.get(username):
            _post_evlog_apple_acct_tracked_devices_info(AppleAcct)

    _set_any_Device_alerts()

    if retry:
        for username in Gb.usernames_setup_error_retry_list:
            if AppleAcct := Gb.AppleAcct_by_username.get(username):
                _post_evlog_apple_acct_tracked_devices_info(AppleAcct)

#--------------------------------------------------------------------
def setup_tracked_devices_for_icloud(AppleAcct):
    '''
    The Family Share device data is available from AppleAcct when logging into the iCloud
    account. This routine will get all the available iCloud devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        AppleAcct: Object containing data to be processed. This might be from Gb.AppleAcct (normal/default)
                    or the one created in config_flow if the username was changed.
    '''
    broadcast_info_msg(f"Stage 4 > Set up Apple & MobApp Data Sources")

    if (AppleAcct is None):
        return

    if Gb.conf_data_source_ICLOUD is False:
        post_event("Apple Account > Not used as a data source")
        return

    if Gb.conf_icloud_device_cnt == 0:
        return

    Gb.apple_accounts_flag = (len(Gb.conf_apple_accounts) > 1)

    _check_renamed_find_devices(AppleAcct)
    _match_AppleAcct_devices_to_Device(AppleAcct)
    _check_duplicate_device_names(AppleAcct)
    _check_for_missing_find_devices(AppleAcct)

    owner = AppleAcct.username_base
    Gb.startup_lists[f"{owner}.AppleAcct.device_id_by_icloud_dname"] = \
                        {k: v[:10] for k, v in AppleAcct.device_id_by_icloud_dname.items()}
    Gb.startup_lists[f"{owner}.AppleAcct.icloud_dname_by_device_id"] = \
                        {k[:10]: v for k, v in AppleAcct.icloud_dname_by_device_id.items()}
    Gb.startup_lists[f"Gb.Devices_by_icloud_device_id"]     = \
                        {k[:10]: v for k, v in Gb.Devices_by_icloud_device_id.items()}

#----------------------------------------------------------------------------
def _check_renamed_find_devices(AppleAcct):
    '''
    Return with a list of icloud devices in the conf_devices that are not in
    _AADevData
    '''
    renamed_devices = \
            [(  f"{conf_device[CONF_IC3_DEVICENAME]} > "
                f"Renamed: {conf_device[CONF_FAMSHR_DEVICENAME]} "
                f"{RARROW}{AppleAcct.icloud_dname_by_device_id[conf_device[CONF_FAMSHR_DEVICE_ID]]}")
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_FAMSHR_DEVICE_ID] in AppleAcct.icloud_dname_by_device_id)
                        and conf_device[CONF_APPLE_ACCOUNT] == AppleAcct.username
                        and conf_device[CONF_FAMSHR_DEVICENAME] != \
                                AppleAcct.icloud_dname_by_device_id[conf_device[CONF_FAMSHR_DEVICE_ID]]]


    if renamed_devices == []:
        return

    renamed_devices_str = list_to_str(renamed_devices, CRLF_DOT)

    post_alert( f"ICLOUD DEVICE NAME CHANGED > The iCloud device name returned "
                f"from your Apple iCloud account Family Sharing List has a new name. "
                f"The iCloud3 configuration file will be updated."
                f"{renamed_devices_str}")

    try:
        # Update the iCloud3 configuration file with the new iCloud devicename
        renamed_devices_by_devicename = {}
        for renamed_device in renamed_devices:
            # gary_ipad > Renamed: Gary-iPad → Gary's iPad
            icloud3_icloud_devicename = renamed_device.split(RARROW)
            new_icloud_devicename = icloud3_icloud_devicename[1]
            icloud3_devicename = icloud3_icloud_devicename[0].split(' ')[0]
            renamed_devices_by_devicename[icloud3_devicename] = new_icloud_devicename

        # Set new icloud name in config and internal table, remove the old one
        for devicename, new_icloud_devicename in renamed_devices_by_devicename.items():
            conf_device = config_file.get_conf_device(devicename)

            old_icloud_devicename = conf_device[CONF_FAMSHR_DEVICENAME]
            if old_icloud_devicename in Gb.conf_icloud_dnames:
                Gb.conf_icloud_dnames.remove(old_icloud_devicename)
            Gb.conf_icloud_dnames.append(new_icloud_devicename)

            conf_device[CONF_FAMSHR_DEVICENAME] = \
                AppleAcct.device_id_by_icloud_dname[conf_device[CONF_FAMSHR_DEVICENAME]] = \
                    new_icloud_devicename

            AppleAcct.device_id_by_icloud_dname[new_icloud_devicename] = conf_device[CONF_FAMSHR_DEVICE_ID]
            AppleAcct.device_id_by_icloud_dname.pop(old_icloud_devicename, None)

        config_file.write_icloud3_configuration_file()

    except Exception as err:
        log_exception(err)
        pass


#--------------------------------------------------------------------
def _match_AppleAcct_devices_to_Device(AppleAcct, retry_match_devices=None):
    '''
    Cycle through the AppleAcct raw data and match that item with the
    conf_devices iCloud entry. Then set the data fields to tie it to
    the Device object.
    '''
    evlog_msg = ''
    _AppleDev = AppleAcct.AADevices
    if _AppleDev is None:
        return

    setup_devices = retry_match_devices or AppleAcct.device_id_by_icloud_dname
    owner_device_ids = []
    for pyicloud_dname, device_id in setup_devices.items():
        _AADevData = AppleAcct.AADevData_by_device_id.get(device_id, None)

        broadcast_info_msg(f"Set up iCloud Device > {pyicloud_dname}")

        conf_device = _find_icloud_conf_device(AppleAcct, pyicloud_dname, device_id)

        # iCloud device was not found in configuration, not being used by this AppleAcct username
        if conf_device == {}:
            continue

        # Update the conf_devices for this device if any of the icloud fields have changed
        _update_config_with_icloud_device_fields(conf_device, _AADevData)

        devicename = conf_device[CONF_IC3_DEVICENAME]

        if (devicename not in Gb.Devices_by_devicename
                or conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE):
            continue

        Device = Gb.Devices_by_devicename[devicename]
        if conf_device[CONF_APPLE_ACCOUNT] == '':
            pass
        elif conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
        Gb.devicenames_by_icloud_dname[icloud_dname] = devicename
        Gb.icloud_dnames_by_devicename[devicename]   = icloud_dname


        _AADevData.Device          = Device
        _AADevData.ic3_devicename  = devicename
        Device.AppleAcct           = AppleAcct
        Device.icloud_device_id    = device_id
        Device.icloud_person_id    = _AADevData.device_data['prsId']
        Device.family_share_device = _AADevData.device_data['fmlyShare']

        if Device.family_share_device is False:
            owner_device_ids = Gb.owner_device_ids_by_username.get(AppleAcct.username, [])
            list_add(owner_device_ids, device_id)
            Gb.owner_device_ids_by_username[AppleAcct.username] = owner_device_ids

        Gb.Devices_by_icloud_device_id[device_id] = Device
        Gb.AppleAcct_by_devicename[devicename] = AppleAcct

        # Set verify status to a valid device_id exists instead of always True
        # This will pick up devices in the configuration file that no longer exist
        Device.verified_ICLOUD = device_id in AppleAcct.AADevData_by_device_id
        Gb.icloud_device_verified_cnt += 1

    # Gb.owner_device_ids_by_username[AppleAcct.username] = owner_device_ids

#----------------------------------------------------------------------------
def _check_for_missing_find_devices(AppleAcct):
    '''
    Get all the devices that have the iCloud device configured that are not
    in the AppleAcct devices iCloud list. This  indicates we have a device that
    is tracked via iCloud but that device is not in the Apple Account.
    '''
    devices_conf_this_apple_acct = [devicename
                    for devicename, Device in Gb.Devices_by_devicename.items()
                    if Device.conf_apple_acct_username == AppleAcct.username]
    devices_tracked_apple_acct = [devicename
                    for devicename, Device in Gb.Devices_by_devicename.items()
                    if Device.AppleAcct == AppleAcct]
    devices_not_tracked_apple_acct = [devicename
                    for devicename, Device in Gb.Devices_by_devicename.items()
                    if (Device.conf_apple_acct_username == AppleAcct.username
                            and Device.AppleAcct is None)]

    Gb.startup_lists[f'{AppleAcct.account_owner}.devices_conf_this_apple_acct']   = \
                    devices_conf_this_apple_acct
    Gb.startup_lists[f'{AppleAcct.account_owner}.devices_tracked_apple_acct']     = \
                    devices_tracked_apple_acct
    Gb.startup_lists[f'{AppleAcct.account_owner}.devices_not_tracked_apple_acct'] = \
                    devices_not_tracked_apple_acct

    if devices_not_tracked_apple_acct == []:
        return

    retry_cnt = 0 if AppleAcct.AADevices else 10
    while retry_cnt < 5:
        retry_cnt += 1
        post_greenbar_msg(f"Apple Acct > {AppleAcct.username_id}, Refreshing data (#{retry_cnt})")
        post_alert(f"Apple Acct > Refreshing data to locate missing devices (#{retry_cnt})")
        AppleAcct.refresh_icloud_data()

        # See in the untracked devices are now available
        retry_match_devices = {}
        for devicename in devices_not_tracked_apple_acct:
            icloud_dname = Gb.icloud_dnames_by_devicename[devicename]
            if icloud_dname in AppleAcct.device_id_by_icloud_dname:
                retry_match_devices[icloud_dname] = AppleAcct.device_id_by_icloud_dname[icloud_dname]

        if isnot_empty(retry_match_devices):
            _match_AppleAcct_devices_to_Device(AppleAcct, retry_match_devices=retry_match_devices)

        # Cycle thru the Devices. If there is no Device.AppleAcct, it was not returned from iCloud
        devices_not_tracked_apple_acct = [devicename
                        for devicename, Device in Gb.Devices_by_devicename.items()
                        if (Device.conf_apple_acct_username == AppleAcct.username
                                and Device.AppleAcct is None)]

        if devices_not_tracked_apple_acct == []:
            return

    # Some devices were not set up.
    list_add(Gb.usernames_setup_error_retry_list, AppleAcct.username)

    evlog_msg =(f"Apple Acct > {AppleAcct.account_owner_username}, "
                f"Unsuccessful")
    for devicename in devices_not_tracked_apple_acct:
        Device = Gb.Devices_by_devicename[devicename]
        list_add(Gb.usernames_setup_error_retry_list, AppleAcct.username)

        Device = Gb.Devices_by_devicename[devicename]
        evlog_msg+=(f"{CRLF_DOT}{Device.fname_devicename} > "
                    f"Device-{Device.conf_icloud_dname}")
    post_alert(evlog_msg)
    return

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
                or Device.verified_flag is False
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
                and Device.AppleAcct.device_id_by_icloud_dname.get(Device.conf_icloud_dname) is None):
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
def _post_evlog_apple_acct_tracked_devices_info(AppleAcct):
    '''
    Cycle through the AppleAcct raw data and display the Event Log message for
    the device indicating if it is:
        - tracked (show the devicename that raw data item is tied to)
        - tracked by another username ( show the other username)
        - not tracked
    '''
    try:
        # Cycle thru the devices from those found in the iCloud data. We are not cycling
        # through the AADevData so we get devices without location info
        _AppleDev = AppleAcct.AADevices
        devices_cnt = _AppleDev.devices_cnt if _AppleDev else 0
        devices_assigned_cnt = 0
        owner_icloud_dnames = list_to_str(
                                [_AADevData.fname
                                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                                    if _AADevData.family_share_device is False])
        famshr_dnames_msg = list_to_str(
                                [_AADevData.fname
                                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                                    if _AADevData.family_share_device])

        devices_assigned_msg = devices_not_assigned_msg = devices_assigned_to_msg= reauth_needed_msg = ''

        if AppleAcct.terms_of_use_update_needed:
            reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Accept Terms of Service Needed"
        if AppleAcct.auth_2fa_code_needed:
            reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Authentication Needed"

        sorted_device_id_by_icloud_dname = OrderedDict(sorted(AppleAcct.device_id_by_icloud_dname.items()))

        for pyicloud_icloud_dname, device_id in sorted_device_id_by_icloud_dname.items():
            exception_msg = ''
            _AADevData = AppleAcct.AADevData_by_device_id.get(device_id)
            if _AADevData is None:
                continue

            offline_msg = ''
            if _AADevData.device_status_code != 200:
                offline_msg += f"DeviceStatus-{_AADevData.device_status_msg}, "
            if _AADevData.location_secs == 0:
                offline_msg += f"No Location Found, "
            if offline_msg != '':
                offline_msg = f"{CRLF_HDOT}{offline_msg[:-2]}"

            # If the Device is None, this AppleAcct is not tracked or assigned to another username
            # pyicloud_icloud_dname ending with '.' indicates this is a duplicate device
            devicename = Gb.devicenames_by_icloud_dname.get(pyicloud_icloud_dname)
            Device     = Gb.Devices_by_devicename.get(devicename)

            # Device belongs to another Apple account
            if Device is None or Device.conf_apple_acct_username != AppleAcct.username:
                # If the Device is already assigned to a AppleAcct iCloud device from another username,
                # get that username's account owner and display it
                _AppleAcct = Gb.AppleAcct_by_devicename.get(devicename)
                if _AppleAcct:
                    devices_assigned_to_msg +=(f"{CRLF_HDOT}{pyicloud_icloud_dname}{RARROW}"
                                                f"Tracked By-{_AppleAcct.account_owner_username_short}")
                else:
                    if pyicloud_icloud_dname.endswith('.'):
                        exception_msg = f", {RED_ALERT}DUPLICATE DEVICE"
                    devices_not_assigned_msg +=(f"{CRLF_HDOT}{pyicloud_icloud_dname} "
                                                f"({_AADevData.icloud_device_display_name})"
                                                f"{exception_msg}")
                continue

            devicename = Device.devicename
            exception_msg = ''

            if Device.tracking_mode == INACTIVE_DEVICE:
                exception_msg += ', INACTIVE '

            pyicloud_icloud_dname = pyicloud_icloud_dname.replace('*', '')

            if exception_msg:
                devices_assigned_msg += (f"{msg_symb}"
                                f"{pyicloud_icloud_dname}{RARROW}"
                                f"{Device.fname}"
                                f"{exception_msg} "
                                f"({_AADevData.icloud_device_display_name}"
                                f"{offline_msg}")

                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            exception_msg = ''

            if _AADevData and Gb.log_rawdata_flag:
                log_title = (   f"iCloud Data {AppleAcct.account_name}{LINK}"
                                f"{devicename}/{pyicloud_icloud_dname} "
                                f"({_AADevData.device_identifier})")
                # log_data(log_title, {'filter': _AADevData.device_data})

            devices_assigned_cnt += 1
            msg_symb = f"{CRLF}{NBSP2}{RED_ALERT}" \
                            if pyicloud_icloud_dname.endswith('.') else CRLF_CHK
            device_msg=(f"{msg_symb}"
                        f"{pyicloud_icloud_dname}{RARROW}"
                        f"{Device.fname}/{devicename} ")
            letter_cnt = len(device_msg) - device_msg.count('i') - device_msg.count('l')
            if letter_cnt > 35: device_msg += CRLF_TAB
            device_msg += ( f"({_AADevData.icloud_device_display_name})"
                            f"{exception_msg}"
                            f"{offline_msg}")
            # _evlog(f"{len(device_msg)} {device_msg[:65]}")

            devices_assigned_msg += device_msg

        evlog_msg =(f"Apple Acct > {AppleAcct.account_owner_username}, "
                    f"{devices_assigned_cnt} of {devices_cnt} tracked"
                    f"{reauth_needed_msg}"
                    f"{devices_assigned_msg}")
        if devices_assigned_to_msg != '':
            evlog_msg+=(f"{CRLF_DOT}Family Devices tracked by another Apple Acct:"
                        f"{devices_assigned_to_msg}")
        if devices_not_assigned_msg != '':
            evlog_msg+=(f"{CRLF_X}Not assigned to an iCloud3 Device:"
                        f"{devices_not_assigned_msg}")

        famshr_crlf = CRLF_DOT if AppleAcct.locate_all_devices else CRLF_STAR
        if owner_icloud_dnames:
            evlog_msg += f"{CRLF_DOT} myDevices-{owner_icloud_dnames}"
        if famshr_dnames_msg:
            evlog_msg += f"{famshr_crlf} Family Devices-{famshr_dnames_msg}"
            if AppleAcct.locate_all_devices is False:
                evlog_msg += f"{CRLF_STAR} Family Devices are not located"

        post_event(evlog_msg)

        return

    except Exception as err:
        log_exception(err)

        evlog_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username-Password may be invalid.")
        post_error_msg(evlog_msg)

    return

#--------------------------------------------------------------------
def _find_icloud_conf_device(AppleAcct, pyicloud_dname, device_id):
    '''
    Get the icloud3 device's configuration item. Then see if the raw_model, model
    or model_display_name has changed. If so, update it in the configuration file.

    Return:
        conf_device configuration item or {} if it is not being tracked
    '''
    # Cycle through the config tracked devices and find the matching device.
    update_conf_file_flag = False
    old_icloud_dname = '?'
    try:
        conf_device = [conf_device
                        for conf_device in Gb.conf_devices
                        if (conf_device[CONF_FAMSHR_DEVICENAME] == pyicloud_dname
                            and conf_device[CONF_APPLE_ACCOUNT] == AppleAcct.username)]

        if isnot_empty(conf_device):
            conf_device = conf_device[0]
            conf_device = _check_changed_apple_device_info(AppleAcct, pyicloud_dname, device_id, conf_device)
            return conf_device

        # See if AppleAcct device_id is the same as the conf_famshr_device_id
        update_config_flag = False
        conf_device = [conf_device
                    for conf_device in Gb.conf_devices
                    if conf_device[CONF_FAMSHR_DEVICE_ID] == device_id]

        if isnot_empty(conf_device):
            conf_device = conf_device[0]
            icloud_dname = AppleAcct.icloud_dname_by_device_id[device_id]
            old_icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
            conf_device[CONF_FAMSHR_DEVICENAME] = icloud_dname
            update_config_flag = True

        # See if the FamShr_Devicename is the same as the iC3_devicename
        # and the iC3_Fname is the same as the pyicloud_dname because ofa data error/device info
        # change that was saved in conf_flow. If so, set the FamShr_Devicename to the iC3_Fname
        if update_config_flag is False:
            conf_device = [conf_device
                        for conf_device in Gb.conf_devices
                        if (conf_device[CONF_IC3_DEVICENAME] == conf_device[CONF_FAMSHR_DEVICENAME]
                            and conf_device[CONF_FNAME] == pyicloud_dname
                            and conf_device[CONF_APPLE_ACCOUNT] == AppleAcct.username)]

            if isnot_empty(conf_device):
                conf_device = conf_device[0]
                old_icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
                conf_device[CONF_FAMSHR_DEVICENAME] = conf_device[CONF_FNAME]
                update_config_flag = True

        # See if the FamShr_Devicename is the same as the iC3_devicename
        # and thepyicloud_dname starts with the iC3_Fname, it is a match if only one item
        # change that was saved in conf_flow. If so, set the FamShr_Devicename to the iC3_Fname
        if update_config_flag is False:
            conf_device = [conf_device
                        for conf_device in Gb.conf_devices
                        if (conf_device[CONF_IC3_DEVICENAME] == conf_device[CONF_FAMSHR_DEVICENAME]
                            and conf_device[CONF_APPLE_ACCOUNT] == AppleAcct.username
                            and (conf_device[CONF_FNAME].startswith(pyicloud_dname)
                                or conf_device[CONF_IC3_DEVICENAME] == slugify(pyicloud_dname)))]

            if isnot_empty(conf_device):
                if len(conf_device) == 1:
                    conf_device = conf_device[0]
                    old_icloud_dname = conf_device[CONF_FAMSHR_DEVICENAME]
                    conf_device[CONF_FAMSHR_DEVICENAME] = pyicloud_dname
                    update_config_flag = True

        if update_config_flag:
            conf_device = _check_changed_apple_device_info(AppleAcct, pyicloud_dname, device_id, conf_device)
            config_file.write_icloud3_configuration_file()
            post_alert( f"ICLOUD DEVICE NAME CHANGED > "
                        f"The configured name was not found in any Apple Accounts. A candidate was found"
                        f"{CRLF_DOT}{conf_device[CONF_IC3_DEVICENAME]} > "
                        f"Renamed: {old_icloud_dname}{RARROW}"
                        f"{conf_device[CONF_FAMSHR_DEVICENAME]}")
            return conf_device

    except Exception as err:
        log_exception(err)

    return {}

#--------------------------------------------------------------------
def _check_changed_apple_device_info(AppleAcct, pyicloud_dname, device_id, conf_device):
    # Get the model info from AppleAcct data and update it if necessary
    raw_model, model, model_display_name = \
                    AppleAcct.device_model_info_by_fname[pyicloud_dname]

    if (conf_device[CONF_FAMSHR_DEVICE_ID] != device_id
            or conf_device[CONF_RAW_MODEL] != raw_model
            or conf_device[CONF_MODEL] != model
            or conf_device[CONF_MODEL_DISPLAY_NAME] != model_display_name):
        conf_device[CONF_FAMSHR_DEVICE_ID] = device_id
        conf_device[CONF_RAW_MODEL] = raw_model
        conf_device[CONF_MODEL] = model
        conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name

        config_file.write_icloud3_configuration_file()

    return conf_device

#--------------------------------------------------------------------
def _check_duplicate_device_names(AppleAcct):
    '''
    See if this fname is already used by another device in the iCloud list. If so,
    consider it a duplicate device that would refer to the same iC3 devicename.
    Add a suffix to the fname to be able to keep track of it. Leave the actual
    devicename the original value.

    The device is selected in iC3 config_flow by the device's fname and the fname
    is stored in the configuration file. iCloud3 The fname needs a suffix to keep
    track of all devices in the iCloud account. Otherwise, a duplicate would
    overwrite the original device and the model and other info would be lost.

    This is checked when verifying devices in start_ic3
    '''
    if 'stage4_dup_check_done' in Gb.startup_stage_status_controls: return


    # Cycle thru the duplicates, create an evlog msg
    try:
        _dup_AADevData_by_icloud_dname = {AADevData.fname: AADevData
                                    for AADevData in AppleAcct.AADevData_items
                                    if AADevData.Device and AADevData.fname.endswith('.')}

        if is_empty(_dup_AADevData_by_icloud_dname):
            return

        Gb.startup_lists['_._dup_AADevData_by_icloud_dnames'] = _dup_AADevData_by_icloud_dname.keys()

        dup_devices_msg  = ""
        dup_devices_list = ""

        for icloud_dname, AADevData in _dup_AADevData_by_icloud_dname.items():
            try:
                # Get the AADevData item for the original tracked device (without the dots) to
                # be able to display that device's info
                _AADevData_original = [_AADevData
                                    for _AADevData in AppleAcct.AADevData_items
                                    if _AADevData.fname == AADevData.fname_original][0]

                # Get the tracked device that was duplicated
                _Device = _AADevData_original.Device
                _Device.set_fname_alert(RED_ALERT)

                dup_devices_list += f"{_Device.fname_devicename} > Apple Device-{AADevData.fname_original}, "
                dup_devices_msg += (f"{CRLF_DOT}{_Device.fname_devicename} > "
                                    f"Apple Device-{AADevData.fname_original}, "
                                    f"{CRLF_HDOT}{AADevData.icloud_device_display_name}, Other Device with same name"
                                    f"{CRLF_HDOT}{_AADevData_original.icloud_device_display_name}, Assigned Device being tracked")

            except Exception as err:
                log_exception(err)

        post_alert( f"DUPLICATE APPLE ACCOUNT DEVICES > "
                f"Two Apple Account Devices have the same name that is assigned to an "
                f"iCloud3 tracked device. Review the Configure > Update Devices screen and "
                f"verify the correct Apple Device is assigned."
                f"{dup_devices_msg}"
                f"{CRLF}Rename one of the devices (Settings App > General > About) to remove this notification")
        alert_msg =(f"{_Device.fname} > Two Apple Acct devices with same name "
                f"({AADevData.fname_original}), "
                f"{AADevData.icloud_device_display_name} & "
                f"{_Device.model_display_name}")
        post_greenbar_msg(alert_msg)
        log_warning_msg(f"iCloud3 Alert > {alert_msg}")

        Gb.startup_stage_status_controls.append('stage4_dup_check_done')
    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _update_config_with_icloud_device_fields(conf_device, _AADevData):

    # Get the model info from AppleAcct data and update it if necessary
    raw_model, model, model_display_name = \
                    _AADevData.AppleAcct.device_model_info_by_fname[_AADevData.fname]

    if (conf_device[CONF_FAMSHR_DEVICE_ID] == _AADevData.device_id
            and conf_device[CONF_RAW_MODEL] == raw_model
            and conf_device[CONF_MODEL] == model
            and conf_device[CONF_MODEL_DISPLAY_NAME] == model_display_name):
        return

    conf_device[CONF_FAMSHR_DEVICE_ID] = _AADevData.device_id
    conf_device[CONF_RAW_MODEL] = raw_model
    conf_device[CONF_MODEL] = model
    conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name

    config_file.write_icloud3_configuration_file()

    post_event( f"{EVLOG_NOTICE}Device Config Updated > {conf_device[CONF_FNAME]} "
                f"({conf_device[CONF_IC3_DEVICENAME]}), "
                f"Apple Acct Info Updated-{model_display_name}")

#--------------------------------------------------------------------
def _fname_base(fname):
    '''
    Extract the base name from the fmashr_fname (Gary, Gary {iC3}, Lillian (2), Lillian (3))
    '''
    if instr(fname, '(') is False and instr(fname, ')') is False:
        return fname

    suffix = fname.split('(')[1].split(')')[0]
    if suffix.isnumeric():
        return fname.split('(')[0].strip()

    return fname


#----------------------------------------------------------------------
def get_find_devices_pyicloud(AppleAcct):
    '''
    The device information tables are built when the devices are added the when
    the AADevices object and AADevData objects are created when logging into
    the iCloud account.
    '''
    if AppleAcct is None: AppleAcct = Gb.AppleAcct

    _AppleDev = AppleAcct.AADevices
    return [AppleAcct.device_id_by_icloud_dname,
            AppleAcct.device_id_by_icloud_dname,
            AppleAcct.device_info_by_icloud_dname,
            AppleAcct.device_model_info_by_fname]

#--------------------------------------------------------------------
def set_device_data_source(AppleAcct):
    '''
    Cycle through the devices and change the iCloud data source to MobApp
    if there is a problem with the iCloud setup and the MobApp is available
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        Gb.Devices_by_icloud_device_id = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            data_source = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.icloud_device_id:
                device_id = Device.icloud_device_id
                if device_id in AppleAcct.AADevData_by_device_id:
                    data_source = ICLOUD
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    _AADevData = AppleAcct.AADevData_by_device_id[device_id]

            if (Device.mobapp_monitor_flag and data_source is None):
                data_source = MOBAPP

            if data_source != MOBAPP:
                info_msg = (f"Set AppleAcct Device Id > {Device.devicename}, "
                            f"DataSource-{data_source}, "
                            f"{CRLF}iCloud-({Device.device_id8_icloud})")
                post_monitor_msg(info_msg)

            Device.primary_data_source = data_source

        info_msg = ''
        for _device_id, _AADevData in AppleAcct.AADevData_by_device_id.items():
            info_msg += (f"{_AADevData.name}/{_device_id[:8]}-{_AADevData.data_source}, ")
        if info_msg == '': info_msg = 'None'
        post_monitor_msg(f"AppleAcct Devices > {info_msg}")

    except Exception as err:
        log_exception(err)


#--------------------------------------------------------------------
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
            for _device_type in DEVICE_TYPE_FNAMES.keys():
                if instr(mobapp_fname, _device_type.title()):
                    mobapp_fname = mobapp_fname.replace(
                            _device_type.title(), DEVICE_TYPE_FNAMES[_device_type])
                    break

        Device.conf_mobapp_fname = mobapp_fname
        Gb.devicenames_x_mobapp_dnames[mobapp_fname] = devicename

        # device_tracker entity is disabled
        if mobapp_id in Gb.MobileApp_fnames_disabled:
            update_alert_sensor(Device.fname, f"MobApp Device Disabled ({mobapp_dname})")
            Device.set_fname_alert(RED_ALERT)
            Device.mobapp_device_unavailable_flag = True
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
        Device.mobapp_monitor_flag = True

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

    evlog_msg =(f"Mobile App Devices > "
                f"{devices_monitored_cnt} of {len(Gb.conf_devices)} monitored"
                f"{devices_monitored_msg}"
                f"{devices_not_monitored_msg}"
                f"{CRLF_X}Not assigned to an iCloud3 Device: "
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

    # if Gb.log_debug_flag:
    #     log_debug_msg(f"{Gb.Devices=}")
    #     log_debug_msg(f"{Gb.Devices_by_devicename=}")
    #     log_debug_msg(f"{Gb.conf_devicenames=}")
    #     log_debug_msg(f"{Gb.conf_icloud_dnames=}")
    #     self.devices_not_set_up          = []
    #     self.device_id_by_icloud_dname   = {}       # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
    #     self.icloud_dname_by_device_id   = {}       # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
    #     self.device_info_by_icloud_dname = {}       # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro (iPhone15,2)'}
    #     self.device_model_info_by_fname  = {}       # {'Gary-iPhone': [raw_model,model,model_display_name]}
    #     self.dup_icloud_dname_cnt
    return

#--------------------------------------------------------------------
def set_devices_verified_status():
    '''
    Cycle thru the Devices and set verified status based on data sources
    '''
    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.verified_flag = (Device.verified_ICLOUD
                            or  Device.verified_MOBAPP)

        # If the data source is iCloud and the device is not verified, set the
        # data source to MobApp
        if (Device.verified_flag
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
        else:
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

        if Device.mobapp_monitor_flag:
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
            if _AppleAcct.login_failed:
                pass
            elif (icloud_dname not in _AppleAcct.device_id_by_icloud_dname
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

    for devicename, Device in Gb.Devices_by_devicename.items():
        if (selected_devicenames is None
                or 'all' in selected_devicenames
                or devicename in selected_devicenames):
            pass
        else:
            continue

        if Device.fname in Gb.alerts_sensor_attrs:
            if Device.verified_flag is False:
                Device.evlog_fname_alert_char = RED_ALERT
            else:
                Device.evlog_fname_alert_char = YELLOW_ALERT

        Device.display_info_msg(f"Set Trackable Devices > {devicename}")
        if Device.verified_flag:
            tracking_mode = ''
        else:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_icloud_device_cnt > 0)
            tracking_mode = f"{RED_ALERT}NOT "

        tracking_mode += 'Monitored' if Device.is_monitored else 'Tracked'
        if instr(tracking_mode, 'NOT'):
            tracking_mode = tracking_mode.upper()
        evlog_msg =(f"{Device.fname_devicename} > {Device.devtype_fname}, {tracking_mode}")

        # Device is not in configured Apple acct if it was not matched
        username     = Device.conf_apple_acct_username
        apple_acct   = Device.AppleAcct.account_owner_username if Device.AppleAcct else username_id(username)
        icloud_dname = Device.conf_icloud_dname
        apple_acct_err_msg = icloud_dname_err_msg = ''

        # Get Apple acct owner from AppleAcct
        if username in Gb.AppleAcct_error_by_username:
            pass
        elif (Device.conf_apple_acct_username in Gb.AppleAcct_by_username
                and Device.verified_ICLOUD is False):
            icloud_dname_err_msg = f", {RED_ALERT}Not in Apple Acct"
            log_error_msg(f"iCloud3 Device Configuration Error > "
                    f"{Device.fname_devicename}, "
                    f"{icloud_dname} Not in Apple Acct ({apple_acct})")
        # Not using Apple as a data source
        elif apple_acct == '':
            apple_acct = 'None (NOT SPECIFIED)'

        elif Gb.internet_error:
            pass

        # Apple acct is not found in AppleAcct
        elif Device.conf_apple_acct_username in Gb.AppleAcct_by_username:
            pass

        else:
            apple_acct_err_msg = f", {RED_ALERT}APPLE ACCT ERROR"
            update_alert_sensor(Device.fname, f"Unknown Apple Acct ({apple_acct})")
            log_error_msg(  f"iCloud3 Device Configuration Error > "
                            f"{Device.fname_devicename}, "
                            f"Unknown Apple Acct ({apple_acct})")

        if Gb.internet_error:
            apple_acct_err_msg = f", {RED_ALERT}Not Available"

        # Build the Apple acct evlog msg
        evlog_msg += f"{CRLF_DOT}Apple Acct/iCloud Configuration:"
        if (apple_acct == ''
                and icloud_dname == ''):
            evlog_msg += f"{CRLF_HDOT}Not used as a location data source"

        else:
            evlog_msg+=(f"{CRLF_HDOT}Apple Account: {apple_acct}{apple_acct_err_msg}"
                        f"{CRLF_HDOT}iCloud Device: {icloud_dname}{icloud_dname_err_msg}")

        # Build MobApp evlog config msg
        if Device.mobapp[DEVICE_TRACKER] == '':
            if Device.conf_mobapp_fname:
                evlog_msg += f"{CRLF_RED_ALERT}Mobile App Device > {Device.conf_mobapp_fname}, Not Found"
            else:
                evlog_msg += (  f"{CRLF_DOT}Mobile App Configuration:"
                                f"{CRLF_HDOT}Not used as a location data source")

        else:
            evlog_msg += CRLF_DOT if Device.mobapp_monitor_flag else CRLF_RED_ALERT
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
            device_status = Device.AADevData_icloud.device_data[ICLOUD_DEVICE_STATUS]
            timestamp     = Device.AADevData_icloud.device_data[LOCATION][TIMESTAMP]
            if device_status == '201' and mins_since(timestamp) > 5:
                evlog_msg += (f"{CRLF_RED_ALERT}DEVICE IS OFFLINE > "
                            f"Since-{format_time_age(timestamp)}")
                Device.offline_secs = timestamp

        except Exception as err:
            # log_exception(err)
            pass

        post_event(evlog_msg)

#------------------------------------------------------------------------------
def display_inactive_devices():
    '''
    Display a list of the Inactive devices in the Event Log
    '''

    Gb.inactive_fname_by_devicename = {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE}

    inactive_devices_msg =[( f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]}), "
                            f"{DEVICE_TYPE_FNAME(conf_device[CONF_DEVICE_TYPE])}")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

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
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        Device.display_info_msg("Setup Complete, Locating Device")

    post_event(f"{EVLOG_IC3_STARTING}Initializing {ICLOUD3_VERSION_MSG} > Complete")

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