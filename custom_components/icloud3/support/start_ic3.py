

from ..global_variables import GlobalVariables as Gb
from ..const            import (ICLOUD3,
                                STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY,
                                DEVICE_TRACKER, DEVICE_TRACKER_DOT, NOTIFY,
                                HOME, ERROR, NONE_FNAME,
                                STATE_TO_ZONE_BASE, CMD_RESET_PYICLOUD_SESSION,
                                EVLOG_ALERT, EVLOG_IC3_STARTING, EVLOG_NOTICE, EVLOG_IC3_STAGE_HDR,
                                EVENT_RECDS_MAX_CNT_BASE, EVENT_RECDS_MAX_CNT_ZONE,
                                CRLF, CRLF_DOT, CRLF_CHK, CRLF_SP3_DOT, CRLF_SP5_DOT, CRLF_HDOT,
                                CRLF_SP3_STAR, CRLF_INDENT, CRLF_X, CRLF_TAB, DOT, CRLF_SP8_HDOT, CRLF_SP8_DOT,
                                CRLF_RED_X, RED_X, CRLF_STAR, YELLOW_ALERT, UNKNOWN,
                                RARROW, NBSP4, NBSP6, CIRCLE_STAR, INFO_SEPARATOR, DASH_20, CHECK_MARK,
                                ICLOUD, FMF, FAMSHR, APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE,
                                DEVICE_TYPE_FNAME,
                                IPHONE, IPAD, IPOD, WATCH, AIRPODS,
                                MOBAPP, NO_MOBAPP, ICLOUD_DEVICE_STATUS, TIMESTAMP,
                                INACTIVE_DEVICE, DATA_SOURCE_FNAME,
                                NAME, FNAME, TITLE, RADIUS, NON_ZONE_ITEM_LIST, FRIENDLY_NAME,
                                LOCATION, LATITUDE, RADIUS,
                                TRIGGER,
                                ZONE, ID,
                                BATTERY_LEVEL, BATTERY_STATUS,
                                CONF_ENCODE_PASSWORD,
                                CONF_VERSION,  CONF_VERSION_INSTALL_DATE,
                                CONF_EVLOG_CARD_DIRECTORY, CONF_EVLOG_CARD_PROGRAM, CONF_EVLOG_BTNCONFIG_URL,
                                PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                CONF_USERNAME, CONF_PASSWORD,
                                CONF_DATA_SOURCE, CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX,
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
                                CONF_DISPLAY_GPS_LAT_LONG,
                                CONF_CENTER_IN_ZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_WAZE_USED, CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE,
                                CONF_STAT_ZONE_BASE_LONGITUDE, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                CONF_FAMSHR_DEVICE_ID, CONF_FAMSHR_DEVICE_ID2, CONF_FMF_DEVICE_ID,
                                CONF_MOBILE_APP_DEVICE, CONF_FMF_EMAIL,
                                CONF_TRACKING_MODE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_ZONE, CONF_NAME,
                                DEFAULT_GENERAL_CONF,
                                )
from ..device               import iCloud3_Device
from ..zone                 import iCloud3_Zone
from ..support              import config_file
from ..helpers              import entity_io
from ..support              import mobapp_interface
from ..support              import mobapp_data_handler
from ..support              import service_handler
from ..support              import zone_handler
from ..support              import stationary_zone as statzone
from ..support.waze         import Waze
from ..support.waze_history import WazeRouteHistory as WazeHist
from ..helpers.common       import (instr, format_gps, circle_letter, zone_dname,
                                    is_statzone, isnot_statzone, list_to_str, list_add, list_del, )
from ..helpers.messaging    import (broadcast_info_msg,
                                    post_event, post_error_msg, post_monitor_msg, post_startup_alert,
                                    post_internal_error,
                                    log_info_msg, log_debug_msg, log_error_msg, log_warning_msg,
                                    log_rawdata, log_exception, format_filename,
                                    internal_error_msg2,
                                    _trace, _traceha, more_info, )
from ..helpers.dist_util    import (format_dist_km, m_to_um, )
from ..helpers.time_util    import (time_now_secs, format_timer, format_time_age, format_age, )

import os
import json
import shutil
import traceback
from datetime               import timedelta, date, datetime
from collections            import OrderedDict
from homeassistant.helpers  import event
from homeassistant.core     import Event, HomeAssistant, ServiceCall, State, callback
from homeassistant.util     import slugify
from re import match

import logging
# _LOGGER = logging.getLogger(__name__)
_LOGGER = logging.getLogger('icloud3')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- INITIALIZATION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def initialize_directory_filenames():
    """ Set up common directories and file names """


    Gb.ha_config_directory            = Gb.hass.config.path()
    Gb.ha_storage_directory           = Gb.hass.config.path(STORAGE_DIR)
    Gb.ha_storage_icloud3             = Gb.hass.config.path(STORAGE_DIR, 'icloud3')
    Gb.icloud3_config_filename        = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'configuration')
    Gb.icloud3_restore_state_filename = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'restore_state')
    Gb.wazehist_database_filename     = Gb.hass.config.path(STORAGE_DIR, 'icloud3', 'waze_location_history.db')
    Gb.icloud3_directory              = Gb.hass.config.path('custom_components', 'icloud3')
    Gb.entity_registry_file           = Gb.hass.config.path(STORAGE_DIR, STORAGE_KEY_ENTITY_REGISTRY)

    # Note: The Event Log  directory & filename are initialized in config_file.py
    # after the configuration file has been read

    #Set up pyicloud cookies directory & file names
    Gb.icloud_cookies_dir  = Gb.hass.config.path(STORAGE_DIR, 'icloud')
    Gb.icloud_cookies_file = "".join([c for c in Gb.username if match(r"\w", c)])
    if not os.path.exists(Gb.icloud_cookies_dir):
        os.makedirs(Gb.icloud_cookies_dir)

#------------------------------------------------------------------------------
#
#   ICLOUD3 CONFIGURATION PARAMETERS WERE UPDATED VIA CONFIG_FLOW
#
#   Determine the type of parameters that were updated and reset the variables or
#   devices based on the type of changes.
#
#------------------------------------------------------------------------------
def process_config_flow_parameter_updates():

    if Gb.config_flow_updated_parms == {''}:
        return

    # Make copy and Reinitialize so it will not be run again from the 5-secs loop
    config_flow_updated_parms = Gb.config_flow_updated_parms
    Gb.config_flow_updated_parms = {''}

    event_msg =(f"Configuration Loading > "
                f"Type-{list_to_str(config_flow_updated_parms).title()}")
    post_event(event_msg)

    if 'restart' in config_flow_updated_parms:
        initialize_icloud_data_source()
        Gb.restart_icloud3_request_flag = True
        return

    post_event(f"{EVLOG_IC3_STAGE_HDR}")
    if 'general' in config_flow_updated_parms:
        set_global_variables_from_conf_parameters()

    if 'zone_formats' in config_flow_updated_parms:
        set_zone_display_as()

    if 'evlog' in Gb.config_flow_updated_parms:
        post_event('Processing Event Log Settings Update')
        Gb.evlog_btnconfig_url = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.hass.loop.create_task(update_lovelace_resource_event_log_js_entry())
        check_ic3_event_log_file_version()
        Gb.EvLog.setup_event_log_trackable_device_info()

    # stage_title = f'Configuration Changes Loaded'
    # post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")

    if 'reauth' in config_flow_updated_parms:
        Gb.evlog_action_request = CMD_RESET_PYICLOUD_SESSION

    if 'waze' in config_flow_updated_parms:
        set_waze_conf_parameters()

    if 'tracking' in config_flow_updated_parms:
        post_event("Tracking parameters updated")
        initialize_icloud_data_source()

    elif 'devices' in config_flow_updated_parms:
        post_event("Device parameters updated")
        initialize_icloud_data_source()
        update_devices_non_tracked_fields()
        Gb.EvLog.setup_event_log_trackable_device_info()

        _refresh_all_devices_sensors()
        _display_all_devices_config_info()

        stage_title = f'Device Configuration Summary'
        post_event(f"{EVLOG_IC3_STAGE_HDR}{stage_title}")
        Gb.EvLog.display_user_message('')

    post_event(f"{EVLOG_IC3_STAGE_HDR}Configuration Changes Applied")
    Gb.config_flow_updated_parms = {''}

#------------------------------------------------------------------------------
#
#   UPDATE LOVELACE RESOURCES FOR EVENT LOG CARD
#
#------------------------------------------------------------------------------
async def update_lovelace_resource_event_log_js_entry(new_evlog_dir=None):
    '''
    Check the lovelace resource for an icloud3_event-log-card.js entry.
    If found, it is already set up and there is nothing to do.
    If not found, add it to the lovelace resource so the user does not
        have to manually add it. The browser needs to be refreshed so also
        generate a broadcast message.

    Resources are stored as part of the StorageCollection:
        Resources object = Gb.hass.data["lovelace"]["resources"]
        Add Resource    - Resources.async_create_item({'res_type': 'module', 'url': evlog_url})
        Append Resource - Resources.data.append({'type': 'module', 'url': evlog_url})
        Update Resource - Resources.async_update_item(evlog_resource_id, {'url': evlog_url})
        Delete Resource - Resources.async_delete_item((evlog_resource_id)
    '''
    try:
        Resources = Gb.hass.data["lovelace"]["resources"]
        if Resources:
            if not Resources.loaded:
                await Resources.async_load()
                Resources.loaded = True

            www_evlog_js_directory = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
            evlog_url = (   f"{Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]}/"
                            f"{Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]}")
            evlog_url = evlog_url.replace('www', '/local')
            evlog_resource_id = None
            update_lovelace_resources = True

            for item in Resources.async_items():
                # EvLog is in resources, nothing to do
                if item['url'] == evlog_url:
                    update_lovelace_resources = False
                # EvLog is in resources but in another directory
                if (item['url'].endswith(Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM])
                        and item['url'] != evlog_url):
                    evlog_resource_id = item['id']
                    evlog_url_old = item['url']

            update_msg = ''
            if update_lovelace_resources:
                # Update the exicting entry
                if evlog_resource_id:
                    if getattr(Resources, "async_update_item", None):
                        await Resources.async_update_item(evlog_resource_id, {'url': evlog_url})
                        update_msg=(f"{CRLF}From: {evlog_url_old}"
                                    f"{CRLF}To....: {evlog_url}")

                # Create a new entry if this is the first Resources item
                elif getattr(Resources, "async_create_item", None):
                    await Resources.async_create_item({'res_type': 'module', 'url': evlog_url, })
                    update_msg = f"{CRLF}Added: {evlog_url}"

                # Add to the Resources list if it already exists
                elif (getattr(Resources, "data", None)
                        and getattr(Resources.data, "append", None)):
                    Resources.data.append({'type': 'module', 'url': evlog_url, })
                    update_msg = f"{CRLF}Added: {evlog_url}"

                Resources.loaded = False

                post_event( f"{EVLOG_ALERT}LOVELACE RESOURCES UPDATED > "
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

    except:
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
    Gb.um                              = DEFAULT_GENERAL_CONF[CONF_UNIT_OF_MEASUREMENT]
    Gb.time_format_12_hour             = True
    Gb.time_format_24_hour             = False
    Gb.um_km_mi_factor                 = .62137
    Gb.um_m_ft                         = 'ft'
    Gb.um_kph_mph                      = 'mph'
    Gb.um_time_strfmt                  = '%I:%M:%S'
    Gb.um_time_strfmt_ampm             = '%I:%M:%S%P'
    Gb.um_date_time_strfmt             = '%Y-%m-%d %H:%M:%S'

    # Configuration parameters
    Gb.device_tracker_state_source     = DEFAULT_GENERAL_CONF[CONF_DEVICE_TRACKER_STATE_SOURCE]
    Gb.center_in_zone_flag             = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    Gb.display_zone_format             = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    Gb.display_gps_lat_long_flag       = DEFAULT_GENERAL_CONF[CONF_DISPLAY_GPS_LAT_LONG]
    Gb.distance_method_waze_flag       = True
    Gb.max_interval_secs               = DEFAULT_GENERAL_CONF[CONF_MAX_INTERVAL] * 60
    Gb.offline_interval_secs           = DEFAULT_GENERAL_CONF[CONF_OFFLINE_INTERVAL] * 60
    Gb.exit_zone_interval_secs         = DEFAULT_GENERAL_CONF[CONF_EXIT_ZONE_INTERVAL] * 60
    Gb.mobapp_alive_interval_secs      = DEFAULT_GENERAL_CONF[CONF_MOBAPP_ALIVE_INTERVAL] * 3600
    Gb.travel_time_factor              = DEFAULT_GENERAL_CONF[CONF_TRAVEL_TIME_FACTOR]
    Gb.is_track_from_base_zone_used    = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE_USED]
    Gb.track_from_base_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE]
    Gb.track_from_home_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_HOME_ZONE]
    Gb.gps_accuracy_threshold          = DEFAULT_GENERAL_CONF[CONF_GPS_ACCURACY_THRESHOLD]
    Gb.old_location_threshold          = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_THRESHOLD] * 60
    Gb.old_location_adjustment         = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_ADJUSTMENT] * 60

    Gb.tfz_tracking_max_distance      = DEFAULT_GENERAL_CONF[CONF_TFZ_TRACKING_MAX_DISTANCE]

    Gb.waze_region                     = DEFAULT_GENERAL_CONF[CONF_WAZE_REGION]
    Gb.waze_max_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MAX_DISTANCE]
    Gb.waze_min_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MIN_DISTANCE]
    Gb.waze_realtime                   = DEFAULT_GENERAL_CONF[CONF_WAZE_REALTIME]
    Gb.waze_history_database_used      = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_DATABASE_USED]
    Gb.waze_history_max_distance       = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAX_DISTANCE]
    Gb.waze_history_track_direction    = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    # Tracking method control vaiables
    # Used to reset Gb.primary_data_source after pyicloud/icloud account successful reset
    # Will be changed to MOBAPP if pyicloud errors
    Gb.data_source_FAMSHR           = False
    Gb.data_source_FMF              = False
    Gb.data_source_MOBAPP           = False
    Gb.used_data_source_FMF         = False
    Gb.used_data_source_FAMSHR      = False
    Gb.used_data_source_MOBAPP      = False
    Gb.any_data_source_MOBAPP_none  = False

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
        config_event_msg = "Configure iCloud3 Operations >"
        config_event_msg += f"{CRLF_DOT}Load configuration parameters"

        initialize_icloud_data_source()

        Gb.www_evlog_js_directory       = Gb.conf_profile[CONF_EVLOG_CARD_DIRECTORY]
        Gb.www_evlog_js_filename        = Gb.conf_profile[CONF_EVLOG_CARD_PROGRAM]
        Gb.evlog_btnconfig_url          = Gb.conf_profile[CONF_EVLOG_BTNCONFIG_URL].strip()
        Gb.evlog_version                = Gb.conf_profile['event_log_version']
        Gb.picture_www_dirs             = Gb.conf_profile[CONF_PICTURE_WWW_DIRS]
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
        Gb.statzone_base_latitude         = Gb.conf_general[CONF_STAT_ZONE_BASE_LATITUDE]
        Gb.statzone_base_longitude        = Gb.conf_general[CONF_STAT_ZONE_BASE_LONGITUDE]
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
        config_event_msg += f"{CRLF_DOT}Set Display Text As Fields ({len(Gb.EvLog.display_text_as)} used)"

        set_waze_conf_parameters()

        # Set other fields and flags based on configuration parameters
        set_primary_data_source(Gb.primary_data_source)
        config_event_msg += (   f"{CRLF_DOT}Set Default Tracking Method "
                                f"({DATA_SOURCE_FNAME.get(Gb.primary_data_source, Gb.primary_data_source)})")

        set_log_level(Gb.log_level)

        config_event_msg += f"{CRLF_DOT}Initialize Debug Control ({Gb.log_level})"

        set_um_formats()
        config_event_msg += f"{CRLF_DOT}Set Unit of Measure Formats ({Gb.um})"

        event_recds_max_cnt = set_event_recds_max_cnt()
        config_event_msg += f"{CRLF_DOT}Set Event Log Record Limits ({event_recds_max_cnt} Events)"

        config_event_msg += f"{CRLF_DOT}Device Tracker State Value Source "
        etds = Gb.device_tracker_state_source
        config_event_msg += f"{CRLF_INDENT}({DEVICE_TRACKER_STATE_SOURCE_DESC.get(etds, etds)})"

        if evlog_msg:
            post_event(config_event_msg)

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
    check_mobile_app_integration(ha_started_check=True)
    setup_notify_service_name_for_mobapp_devices(post_event_msg=True)

def ha_stopping(dummy_parameter):
    post_event("HA Shutting Down")

def ha_restart(dummp_parameter):
    Gb.hass.services.call("homeassistant", "restart")
#------------------------------------------------------------------------------
#
#   SET THE GLOBAL DATA SOURCES
#
#   This is used during the startup routines and in other routines when errors occur.
#
#------------------------------------------------------------------------------
def initialize_icloud_data_source():
    '''
    Set up icloud username/password and devices from the configuration parameters
    '''
    Gb.username                     = Gb.conf_tracking[CONF_USERNAME].lower()
    Gb.username_base                = Gb.username.split('@')[0]
    Gb.password                     = Gb.conf_tracking[CONF_PASSWORD]
    Gb.encode_password_flag         = Gb.conf_tracking[CONF_ENCODE_PASSWORD]
    Gb.icloud_server_endpoint_suffix= \
        icloud_server_endpoint_suffix(Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX])

    Gb.conf_data_source_FAMSHR     = instr(Gb.conf_tracking[CONF_DATA_SOURCE], FAMSHR)
    Gb.conf_data_source_FMF        = instr(Gb.conf_tracking[CONF_DATA_SOURCE], FMF)
    Gb.conf_data_source_MOBAPP     = instr(Gb.conf_tracking[CONF_DATA_SOURCE], MOBAPP)
    Gb.conf_data_source_ICLOUD      = Gb.conf_data_source_FAMSHR or Gb.conf_data_source_FMF
    Gb.primary_data_source_ICLOUD   = Gb.conf_data_source_ICLOUD
    Gb.primary_data_source          = ICLOUD if Gb.primary_data_source_ICLOUD else MOBAPP
    Gb.devices                      = Gb.conf_devices
    Gb.icloud_force_update_flag     = False

    Gb.stage_4_no_devices_found_cnt = 0

def icloud_server_endpoint_suffix(endpoint_suffix):
    '''
    Determine the suffix to be used based on the country_code and the value of the
    configuration file field.
    '''
    if endpoint_suffix != '':
        return endpoint_suffix.replace('.', '')

    if Gb.country_code in APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE:
        return Gb.country_code.lower()

    return ''

#------------------------------------------------------------------------------
def set_primary_data_source(data_source):
    '''
    Set up tracking method. These fields will be reset based on the device_id's available
    for the Device once the famshr and fmf tracking methods are set up.
    '''
    if (Gb.conf_profile[CONF_VERSION] > 0
            and Gb.primary_data_source_ICLOUD
            and (Gb.username == '' or Gb.password == '')):
        alert_msg =(f"{EVLOG_ALERT}ICLOUD USERNAME/PASSWORD ERROR > The username or password has not "
                    f"been set up, iCloud Location Services will not be used. ")

        if Gb.conf_data_source_MOBAPP:
            data_source = MOBAPP
            alert_msg += f"Device tracking will be done using Mobile App location data. "
        else:
            data_source = ''
            post_startup_alert('No data sources have been set up')
            alert_msg += f"No data sources have been set up, tracking will not be done."
            error_msg = ("iCloud3 Error > Devices will not be tracked. Location data "
                        "has not been set up")
            post_error_msg(error_msg)
        post_event(alert_msg)

    if data_source in [FAMSHR, FMF, ICLOUD]:
        Gb.primary_data_source_ICLOUD = Gb.conf_data_source_FAMSHR or Gb.conf_data_source_FMF

#------------------------------------------------------------------------------
def check_mobile_app_integration(ha_started_check=None):
    '''
    Check to see if the Mobile App Integration is installed. If not, the mobapp
    Tracking method is not available. Also, set the Gb.mobile_app variables

    Return:
        True - It is installed or not needed
        False - It is not installed

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
        if Gb.conf_data_source_MOBAPP is False:
            return True

        if 'mobile_app' in Gb.hass.data:
            Gb.MobileApp_data  = Gb.hass.data['mobile_app']
            mobile_app_devices = Gb.MobileApp_data.get('devices', {})

            Gb.mobile_app_device_fnames  = []
            Gb.mobapp_fnames_x_mobapp_id = {}
            Gb.mobapp_fnames_disabled    = []
            for device_id, device_entry in mobile_app_devices.items():
                if device_entry.disabled_by is None:
                    Gb.mobile_app_device_fnames = list_add(Gb.mobile_app_device_fnames, device_entry.name_by_user)
                    Gb.mobile_app_device_fnames = list_add(Gb.mobile_app_device_fnames, device_entry.name)
                    Gb.mobapp_fnames_x_mobapp_id[device_entry.id] = device_entry.name_by_user or device_entry.name
                    Gb.mobapp_fnames_x_mobapp_id[device_entry.name] = device_entry.id
                    Gb.mobapp_fnames_x_mobapp_id[device_entry.name_by_user] = device_entry.id
                else:
                    Gb.mobapp_fnames_disabled = list_add(Gb.mobapp_fnames_disabled, device_entry.id)
                    Gb.mobapp_fnames_disabled = list_add(Gb.mobapp_fnames_disabled, device_entry.name)
                    Gb.mobapp_fnames_disabled = list_add(Gb.mobapp_fnames_disabled, device_entry.name_by_user)

            if Gb.mobile_app_device_fnames:
                ha_started_check = True
                event_msg =(f"Checking Mobile App Integration > Loaded, "
                            f"Devices-{list_to_str(Gb.mobile_app_device_fnames)}")
                post_event(event_msg)

        Gb.debug_log['Gb.mobile_app_device_fnames']  = Gb.mobile_app_device_fnames
        Gb.debug_log['Gb.mobapp_fnames_x_mobapp_id'] = Gb.mobapp_fnames_x_mobapp_id
        Gb.debug_log['Gb.mobapp_fnames_disabled']    = Gb.mobapp_fnames_disabled

        if len(Gb.mobile_app_device_fnames) == Gb.conf_mobapp_device_cnt:
            return True

        # If the check is being done when HA startup is finished and Mobile App is still
        # not loaded, it is not available and the Mobile App data source is not available.
        # Display an error message since there are devices that use the Mobile App.
        if ha_started_check is None:
            event_msg =(f"Checking Mobile App Integration > Not Loaded. "
                        f"Will check again when HA is started")
            post_event(event_msg)
            return

        # Mobile App Integration not loaded
        if len(Gb.mobile_app_device_fnames) == 0:
            Gb.conf_data_source_MOBAPP = False

        # Cycle thru conf_devices since the Gb.Device
        mobile_app_error_msg = ''
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_MOBILE_APP_DEVICE] == 'None':
                continue
            Device = Gb.Devices_by_devicename[conf_device[CONF_IC3_DEVICENAME]]
            if Device.conf_mobapp_fname not in Gb.mobile_app_device_fnames:
                Device.mobapp_monitor_flag = False
                mobile_app_error_msg +=(f"{CRLF_DOT}{conf_device[CONF_MOBILE_APP_DEVICE]}"
                                        f"{RARROW}Assigned to {Device.fname_devicename}")

        if mobile_app_error_msg:
            # post_event( f"{EVLOG_ALERT}MOBILE APP INTEGRATION ERROR > Mobile App devices have been "
            #             f"configured but the Mobile App Integration has not been installed or an "
            #             f"Mobile App device is not available. "
            #             f"The Mobile App will not be used as a data source for that device."
            #             f"{mobile_app_error_msg}")
            return False

    except Exception as err:
        log_exception(err)
        return False

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
    config_file.write_storage_icloud3_configuration_file()

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
        # StatZone.initialize_updatable_items()
        # StatZone.write_ha_zone_state(StatZone.attrs)

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

        # The _l is a html command and will stop the msg from displaying
        ic3_evlog_js_directory_msg = "icloud3/event_log_card".replace('_log', '___log')
        ic3_evlog_js_filename_msg  = ic3_evlog_js_filename.replace('_log', '___log')
        www_evlog_js_directory_msg = www_evlog_js_directory.replace('_log', '___log')
        www_evlog_js_filename_msg  = www_evlog_js_filename.replace('_log', '___log')

        ic3_version, ic3_beta_version, ic3_version_text = _read_event_log_card_js_file(ic3_evlog_js_filename)
        www_version, www_beta_version, www_version_text = _read_event_log_card_js_file(www_evlog_js_filename)

        if ic3_version_text == 'Not Installed':
            Gb.version_evlog = f' Not Found: {ic3_evlog_js_filename_msg}'
            event_msg =(f"iCloud3 Event Log > "
                        f"{CRLF_DOT}Current Version Installed-v{www_version_text}"
                        f"{CRLF_DOT}WARNING: SOURCE FILE NOT FOUND"
                        f"{CRLF_DOT}...{ic3_evlog_js_filename_msg}")
            post_event(event_msg)
        else:
            Gb.version_evlog = ic3_version_text

        # Event log card is not in iCloud3 directory. Nothing to do.
        if ic3_version == 0:
            return

        # Event Log card does not exist in www directory. Copy it from iCloud3 directory
        # Make sure the /config/www and config/CONF_EVLOG_CARD_DIRECTORY exists. Create them if needed
        if www_version == 0:
            config_www_directory = Gb.hass.config.path('www')
            if os.path.exists(config_www_directory) is False:
                os.mkdir(config_www_directory)
            if os.path.exists(www_evlog_js_directory) is False:
                os.mkdir(www_evlog_js_directory)

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
            post_event(event_msg)

            if Gb.evlog_version != www_version_text:
                Gb.evlog_version = Gb.conf_profile['event_log_version'] = www_version_text
                config_file.write_storage_icloud3_configuration_file()

            return

        try:
            _copy_image_files_to_www_directory(www_evlog_js_directory)
            shutil.copy(ic3_evlog_js_filename, www_evlog_js_filename)

            Gb.evlog_version = Gb.conf_profile['event_log_version'] = www_version_text
            config_file.write_storage_icloud3_configuration_file()

            post_startup_alert('Event Log was updated. Browser refresh needed')
            event_msg =(f"{EVLOG_ALERT}"
                        f"BROWSER REFRESH NEEDED > iCloud3 Event Log was updated to v{ic3_version_text}"
                        f"{more_info('refresh_browser')}"
                        f"{CRLF}{'-'*75}"
                        f"{CRLF_DOT}Old Version.. - v{www_version_text}"
                        f"{CRLF_DOT}New Version - v{ic3_version_text}"
                        f"{CRLF_DOT}Copied From - {format_filename(ic3_evlog_js_directory_msg)}/"
                        f"{CRLF_DOT}Copied To.... - {format_filename(www_evlog_js_directory_msg)}/")
            post_event(event_msg)

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
        if os.path.exists(evlog_filename) == False:
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
def _copy_image_files_to_www_directory(www_evlog_directory):
    '''
    Copy any image files from the icloud3/event_log directory to the /www/[event_log_directory]
    '''
    try:
        image_extensions = ['png', 'jpg', 'jpeg']
        image_filenames = [f'{Gb.icloud3_directory}/event_log_card/{x}'
                                    for x in os.listdir(f"{Gb.icloud3_directory}/event_log_card/")
                                    if instr(x, '.') and x.rsplit('.', 1)[1] in image_extensions]

        for image_filename in image_filenames:
            shutil.copy(image_filename, www_evlog_directory)

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
    Gb.zones_dname = NON_ZONE_ITEM_LIST.copy()

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

        Gb.Zones   = list_add(Gb.Zones, Zone)
        Gb.HAZones = list_add(Gb.HAZones, Zone)
        Gb.Zones_by_zone[zone]   = Zone
        Gb.HAZones_by_zone[zone] = Zone
        Gb.zones_dname[zone]     = Zone.dname

        crlf_dot_x = CRLF_X if Zone.passive else CRLF_DOT
        r_ft = f"/{m_to_um(Zone.radius_m)}" if Gb.um_MI else ""
        zone_msg +=(f"{crlf_dot_x}{Zone.zone}, "
                    f"{Zone.dname} (r{Zone.radius_m}m{r_ft})")

    log_msg =  f"Set up Zones > zone, Display ({Gb.display_zone_format})"
    post_event(f"{log_msg}{zone_msg}")

    if Gb.is_track_from_base_zone_used and Gb.track_from_base_zone != HOME:
        event_msg = (   f"Primary 'Home' Zone > {zone_dname(Gb.track_from_base_zone)} "
                        f"{circle_letter(Gb.track_from_base_zone)}")
        post_event(event_msg)

    event_msg = "Special Zone Setup >"
    if Gb.is_passthru_zone_used:
        event_msg += f"{CRLF_DOT}Enter Zone Delay > DelayTime-{format_timer(Gb.passthru_zone_interval_secs)}"
    else:
        event_msg += f"{CRLF_DOT}ENTER ZONE DELAY IS NOT USED"

    dist = Gb.HomeZone.distance_km(Gb.statzone_base_latitude, Gb.statzone_base_longitude)

    if Gb.is_statzone_used:
        event_msg += (  f"{CRLF_DOT}Stationary Zone > "
                        f"Radius-{Gb.HomeZone.radius_m}m, "
                        f"DistMoveLimit-{format_dist_km(Gb.statzone_dist_move_limit_km)}, "
                        f"MinDistFromAnotherZone-{format_dist_km(Gb.statzone_min_dist_from_zone_km)}")
    else:
        event_msg += f"{CRLF_DOT}STATIONARY ZONES ARE NOT USED"

    post_event(event_msg)

    # Cycle thru the Device's conf and get all zones that are tracked from for all devices
    Gb.TrackedZones_by_zone = {}
    for conf_device in Gb.conf_devices:
        for from_zone in conf_device[CONF_TRACK_FROM_ZONES]:
            if from_zone in Gb.HAZones_by_zone:
                Gb.TrackedZones_by_zone[from_zone] = Gb.Zones_by_zone[from_zone]

    Gb.debug_log['Gb.Zones'] = Gb.Zones

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
#       fmf email address
#       sensor.picture name
#       device tracking flags
#       tracked_devices list
#   These fields may be overridden by the routines associated with the
#   operating mode (fmf, icloud, mobapp)
#
#------------------------------------------------------------------------------
def create_Devices_object():

    try:
        device_tracker_entities, device_tracker_entity_data = \
                entity_io.get_entity_registry_data(platform='icloud3', domain=DEVICE_TRACKER)

        old_Devices_by_devicename = Gb.Devices_by_devicename.copy()
        Gb.Devices                 = []
        Gb.Devices_by_devicename   = {}
        Gb.conf_devicenames        = []
        Gb.conf_famshr_devicenames = []

        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            if devicename == '':
                post_startup_alert(f"HA device_tracker entity id not configured for {conf_device[CONF_FAMSHR_DEVICENAME]}")
                alert_msg =(f"{EVLOG_ALERT}CONFIGURATION ALERT > The device_tracker entity id (devicename) "
                            f"has not been configured for {conf_device[CONF_FAMSHR_DEVICENAME]}/"
                            f"{conf_device[CONF_DEVICE_TYPE]}")
                post_event(alert_msg)
                continue

            Gb.conf_famshr_devicenames.append(conf_device[CONF_FAMSHR_DEVICENAME])
            broadcast_info_msg(f"Set up Device > {devicename}")

            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE_DEVICE:
                event_msg = (f"{CIRCLE_STAR}{devicename} > {conf_device[CONF_FNAME]}/{conf_device[CONF_DEVICE_TYPE]}, INACTIVE, "
                            f"{CRLF_SP3_DOT}FamShr Device-{conf_device[CONF_FAMSHR_DEVICENAME]}"
                            # f"{CRLF_SP3_DOT}FmF Device-{conf_device[CONF_FMF_EMAIL]}"
                            f"{CRLF_SP3_DOT}MobApp Entity-{conf_device[CONF_MOBILE_APP_DEVICE]}")
                post_event(event_msg)
                continue

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, conf_device)
                post_monitor_msg(f"INITIALIZED Device > {Device.fname} ({devicename})")
            else:
                Device = iCloud3_Device(devicename, conf_device)
                post_monitor_msg(f"ADDED Device > {Device.fname} ({devicename})")

            Gb.Devices.append(Device)
            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

            famshr_dev_msg = Device.conf_famshr_name if Device.conf_famshr_name else 'None'
            fmf_dev_msg    = Device.conf_fmf_email if Device.conf_fmf_email else 'None'
            mobapp_dev_msg = Device.mobapp[DEVICE_TRACKER] \
                                    if Device.mobapp[DEVICE_TRACKER] else 'Not Monitored'
            monitored_msg  = '(Monitored)' if Device.is_monitored else '(Tracked)'

            event_msg = (   f"{CHECK_MARK}{devicename} > {Device.fname_devtype} {monitored_msg}"
                            f"{CRLF_SP5_DOT}FamShr Device: {famshr_dev_msg}"
                            # f"{CRLF_SP5_DOT}FmF Device: {fmf_dev_msg}"
                            f"{CRLF_SP5_DOT}MobApp Entity: {mobapp_dev_msg}")

            if Device.track_from_base_zone != HOME:
                event_msg += f"{CRLF_SP5_DOT}Primary 'Home' Zone: {zone_dname(Device.track_from_base_zone)}"
            if Device.track_from_zones != [HOME]:
                event_msg += f"{CRLF_SP5_DOT}Track from Zones: {', '.join(Device.track_from_zones)}"
            post_event(event_msg)

            try:
                # Added the try/except to not generate an error if the device was not in the registry
                # Get the ha device_registry device_id
                Device.ha_device_id = device_tracker_entity_data[f"{DEVICE_TRACKER_DOT}{devicename}"]['device_id']
                Gb.Devices_by_ha_device_id[Device.ha_device_id] = Device

                # Initialize device_tracker entity to display before PyiCloud starts up
                Device.write_ha_device_tracker_state()
            except:
                pass

        _verify_away_time_zone_devicenames()

    except Exception as err:
        log_exception(err)

    Gb.debug_log['Gb.Devices'] = Gb.Devices
    Gb.debug_log['Gb.DevDevices_by_devicename'] = Gb.Devices_by_devicename
    Gb.debug_log['Gb.conf_devicenames'] = Gb.conf_devicenames
    Gb.debug_log['Gb.conf_famshr_devicenames'] = Gb.conf_famshr_devicenames

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
    if Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] != 'none':
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES].remove(devicename)
                update_conf_file_flag = False
        if Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0

    if Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] != 'none':
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES].remove(devicename)
                update_conf_file_flag = False
        if Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0

    if update_conf_file_flag:
        config_file.write_storage_icloud3_configuration_file()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

def setup_tracked_devices_for_famshr(PyiCloud=None):
    '''
    The Family Share device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FamShr devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        PyiCloud: Object containing data to be processed. This might be from Gb.PyiCloud (normal/default)
                    or the one created in config_flow if the username was changed.
    '''
    broadcast_info_msg(f"Stage 3 > Set up Family Share Devices")

    if PyiCloud is None:
        PyiCloud = Gb.PyiCloud
    if PyiCloud is None:
        return

    PyiCloud = Gb.PyiCloud
    _FamShr = PyiCloud.FamilySharing

    if Gb.conf_data_source_FAMSHR is False:
        event_msg = "Family Sharing Devices > Not used as a data source"
        post_event(event_msg)
        return

    if Gb.conf_famshr_device_cnt == 0:
        return

    elif _FamShr is None or _FamShr.famshr_fname_by_device_id == {}:
        Gb.stage_4_no_devices_found_cnt += 1
        if Gb.stage_4_no_devices_found_cnt > 10:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_famshr_device_cnt > 0)
            event_msg =(f"ICLOUD FAMILY SHARING DEVICES ERROR > "
                        f"{CRLF_DOT}No devices were returned from iCloud Account "
                        f"Family Sharing List, Retry #{Gb.stage_4_no_devices_found_cnt}")
            post_event(f"{EVLOG_ALERT}{event_msg}")
        return False

    Gb.debug_log['FamShr.device_id_by_famshr_fname'] = {k: v[:10] for k, v in _FamShr.device_id_by_famshr_fname.items()}
    Gb.debug_log['FamShr.famshr_fname_by_device_id'] = {k[:10]: v for k, v in _FamShr.famshr_fname_by_device_id.items()}

    _check_renamed_famshr_devices(_FamShr)
    _check_conf_famshr_devices_not_set_up(_FamShr)
    _check_duplicate_device_names(PyiCloud, _FamShr)
    _display_devices_verification_status(PyiCloud, _FamShr)

#----------------------------------------------------------------------------
def _check_renamed_famshr_devices(_FamShr):
    '''
    Return with a list of famshr devices in the conf_devices that are not in
    _RawData
    '''
    renamed_devices = [(f"{conf_device[CONF_IC3_DEVICENAME]} > "
                        f"Renamed: {conf_device[CONF_FAMSHR_DEVICENAME]} "
                        f"{RARROW}{_FamShr.famshr_fname_by_device_id[conf_device[CONF_FAMSHR_DEVICE_ID]]}")
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_FAMSHR_DEVICE_ID] in _FamShr.famshr_fname_by_device_id)
                        and conf_device[CONF_FAMSHR_DEVICENAME] != \
                                _FamShr.famshr_fname_by_device_id[conf_device[CONF_FAMSHR_DEVICE_ID]]]

    if renamed_devices == []:
        return

    renamed_devices_str = list_to_str(renamed_devices, CRLF_DOT)

    log_msg = ( f"{EVLOG_ALERT}FAMSHR DEVICE NAME CHANGED > The FamShr device name returned "
                f"from your Apple iCloud account Family Sharing List has a new name. "
                f"The iCloud3 configuration file will be updated."
                f"{renamed_devices_str}")
    post_event(log_msg)

    try:
        # Update the iCloud3 configuration file with the new FamShr devicename
        renamed_devices_by_devicename = {}
        for renamed_device in renamed_devices:
            # gary_ipad > Renamed: Gary-iPad → Gary's iPad
            icloud3_famshr_devicename = renamed_device.split(RARROW)
            new_famshr_devicename = icloud3_famshr_devicename[1]
            icloud3_devicename = icloud3_famshr_devicename[0].split(' ')[0]
            renamed_devices_by_devicename[icloud3_devicename] = new_famshr_devicename

        # Set new famshr name in config and internal table, remove the old one
        for devicename, new_famshr_devicename in renamed_devices_by_devicename.items():
            conf_device = config_file.get_conf_device(devicename)

            old_famshr_devicename = conf_device[CONF_FAMSHR_DEVICENAME]
            if old_famshr_devicename in Gb.conf_famshr_devicenames:
                Gb.conf_famshr_devicenames.remove(old_famshr_devicename)
            Gb.conf_famshr_devicenames.append(new_famshr_devicename)

            conf_device[CONF_FAMSHR_DEVICENAME] = \
                _FamShr.device_id_by_famshr_fname[conf_device[CONF_FAMSHR_DEVICENAME]] = \
                    new_famshr_devicename

            _FamShr.device_id_by_famshr_fname[new_famshr_devicename] = conf_device[CONF_FAMSHR_DEVICE_ID]
            _FamShr.device_id_by_famshr_fname.pop(old_famshr_devicename, None)

        config_file.write_storage_icloud3_configuration_file()

    except Exception as err:
        log_exception(err)
        pass

#----------------------------------------------------------------------------
def _check_conf_famshr_devices_not_set_up(_FamShr):
    devices_not_set_up = [ (f"{conf_device[CONF_IC3_DEVICENAME]} > "
                            f"Unknown: {conf_device[CONF_FAMSHR_DEVICENAME]}")
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_FAMSHR_DEVICENAME] != NONE_FNAME
                        and conf_device[CONF_FAMSHR_DEVICENAME] not in _FamShr.device_id_by_famshr_fname)]

    if devices_not_set_up == []:
        return []

    Gb.debug_log['_.devices_not_set_up'] = devices_not_set_up

    devices_not_set_up_str = list_to_str(devices_not_set_up, CRLF_X)
    post_startup_alert( f"FamShr Config Error > Device not found"
                        f"{devices_not_set_up_str.replace(CRLF_X, CRLF_DOT)}")
    log_msg = ( f"{EVLOG_ALERT}FAMSHR DEVICES ERROR > Your Apple iCloud Account Family Sharing List did "
                f"not return any information for some of configured devices. FamShr will not be used "
                f"to track these devices."
                f"{devices_not_set_up_str}"
                f"{more_info('famshr_device_not_available')}")
    post_event(log_msg)
    log_error_msg(f"iCloud3 Error > Some FamShr Devices were not Initialized > "
                f"{devices_not_set_up_str.replace(CRLF, ', ')}. "
                f"See iCloud3 Event Log > Startup Stage 4 for more info.")

#--------------------------------------------------------------------
def _display_devices_verification_status(PyiCloud, _FamShr):
    try:
        # Cycle thru the devices from those found in the iCloud data. We are not cycling
        # through the PyiCloud_RawData so we get devices without location info
        event_msg =(f"iCloud Acct Family Sharing Devices > "
                    f"{Gb.conf_famshr_device_cnt} of "
                    f"{len(_FamShr.device_id_by_famshr_fname)} used by iCloud3")

        Gb.famshr_device_verified_cnt   = 0
        Gb.devicenames_x_famshr_devices = {}
        sorted_device_id_by_famshr_fname = OrderedDict(sorted(_FamShr.device_id_by_famshr_fname.items()))
        for famshr_fname, device_id in sorted_device_id_by_famshr_fname.items():

            _RawData = PyiCloud.RawData_by_device_id_famshr.get(device_id, None)

            try:
                raw_model, model, model_display_name = \
                                        _FamShr.device_model_info_by_fname[famshr_fname]
            except:
                log_debug_msg(  f"Error extracting device info, "
                                f"source-{_FamShr.device_model_info_by_fname[famshr_fname]}, "
                                f"fname-{famshr_fname}")
                continue

            broadcast_info_msg(f"Set up FamShr Device > {famshr_fname}")

            conf_device = _verify_conf_device(famshr_fname, device_id, _FamShr)

            devicename  = conf_device.get(CONF_IC3_DEVICENAME)
            famshr_name = conf_device.get(CONF_FAMSHR_DEVICENAME)
            Gb.devicenames_x_famshr_devices[devicename]  = famshr_name
            Gb.devicenames_x_famshr_devices[famshr_name] = devicename
            _RawData.ic3_devicename = devicename
            _RawData.Device = Gb.Devices_by_devicename.get(devicename)

            exception_msg = ''
            if devicename is None:
                exception_msg = 'Not Assigned to an iCloud3 Device'

            elif conf_device.get(CONF_TRACKING_MODE, False) == INACTIVE_DEVICE:
                exception_msg += 'INACTIVE, '

            elif _RawData is None:
                Device = Gb.Devices_by_devicename.get(devicename)
                if Device:
                    Gb.reinitialize_icloud_devices_flag = (Gb.conf_famshr_device_cnt > 0)
                exception_msg += 'Not Assigned to an iCloud3 Device, '

            famshr_fname = famshr_fname.replace('*', '')

            if exception_msg:
                event_msg += (  f"{CRLF_X}"
                                f"{famshr_fname}, {model_display_name} ({raw_model}) >"
                                f"{CRLF_SP8_HDOT}{exception_msg}")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            exception_msg = ''
            if _RawData.is_offline:
                exception_msg = f", OFFLINE"

            if _RawData.is_location_data_available is False:
                PyiCloud.FamilySharing.refresh_client()
                if _RawData.is_location_data_available is False:
                    if Device:
                        Gb.reinitialize_icloud_devices_flag = (Gb.conf_famshr_device_cnt > 0)
                    exception_msg = f", NO LOCATION DATA"

            if _RawData and Gb.log_rawdata_flag:
                log_title = (   f"FamShr PyiCloud Data (device_data -- "
                                f"{devicename}/{famshr_fname}), "
                                f"{model_display_name} ({raw_model})")
                log_rawdata(log_title, {'filter': _RawData.device_data})

            # if devicename not in Gb.Devices_by_devicename:
            Device = Gb.Devices_by_devicename.get(devicename)
            if Device is None:
                if exception_msg == '': exception_msg = ', Unknown Device or Other Device setup error'
                event_msg += (  f"{CRLF_X}{famshr_fname}, {model_display_name} ({raw_model}) >"
                                f"{CRLF_SP8_HDOT}{devicename}"
                                f"{exception_msg}")
                continue

            # Device = Gb.Devices_by_devicename[devicename]
            Device.device_id_famshr = device_id

            # rc9 Set verify status to a valid device_id exists instead of always True
            # This will pick up devices in the configuration file that no longer exist
            #Device.verified_flag = device_id in PyiCloud.RawData_by_device_id
            Device.verified_FAMSHR = device_id in PyiCloud.RawData_by_device_id

            # link paired devices (iPhone <--> Watch)
            Device.paired_with_id = _RawData.device_data['prsId']
            if Device.paired_with_id is not None:
                if Device.paired_with_id in Gb.PairedDevices_by_paired_with_id:
                    Gb.PairedDevices_by_paired_with_id[Device.paired_with_id].append(Device)
                else:
                    Gb.PairedDevices_by_paired_with_id[Device.paired_with_id] = [Device]

            Gb.Devices_by_icloud_device_id[device_id] = Device

            Gb.famshr_device_verified_cnt += 1

            event_msg += (  f"{CRLF_CHK}"
                            f"{famshr_fname}, {model_display_name} ({raw_model}) >"
                            f"{CRLF_SP8_HDOT}{devicename}, {Device.fname} "
                            f"{Device.tracking_mode_fname}"
                            f"{exception_msg}")

        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return

#--------------------------------------------------------------------
def _verify_conf_device(famshr_fname, device_id, _FamShr):
    '''
    Get the this famshr device's configuration item. Then see if the raw_model, model
    or model_display_name has changed. If so, update it in the configuration file.

    Return:
        conf_device configuration item or {} if it is not being tracked
    '''
    # Cycle through the config tracked devices and find the matching device.
    update_conf_file_flag = False
    try:
        conf_device = [conf_device  for conf_device in Gb.conf_devices
                                    if famshr_fname == conf_device[CONF_FAMSHR_DEVICENAME]][0]
    except:
        return {}

    # Get the model info from PyiCloud data and update it if necessary
    raw_model, model, model_display_name = \
                    _FamShr.device_model_info_by_fname[famshr_fname]

    if (conf_device[CONF_RAW_MODEL] != raw_model
            or conf_device[CONF_MODEL] != model
            or conf_device[CONF_MODEL_DISPLAY_NAME] != model_display_name):
        conf_device[CONF_RAW_MODEL] = raw_model
        conf_device[CONF_MODEL] = model
        conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
        update_conf_file_flag = True

    if conf_device[CONF_FAMSHR_DEVICE_ID] != device_id:
        conf_device[CONF_FAMSHR_DEVICE_ID] = device_id

    if update_conf_file_flag:
        config_file.write_storage_icloud3_configuration_file()

    return conf_device

#--------------------------------------------------------------------
def _check_duplicate_device_names(PyiCloud, _FamShr):
    '''
    See if this fname is already used by another device in the FamShr list. If so,
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

    # rc9 Reworked duplicate device message and will now display all dup devices
    # Make a list of all device fnames without the (##) suffix that was added on
    try:
        famshr_fnames_base  = [_fname_base(famshr_fname)
                                    for famshr_fname in _FamShr.device_id_by_famshr_fname.keys()]

        # Count each one, then drop the ones with a count = 1 to keep the duplicates
        famshr_fnames_count = {famshr_fname:famshr_fnames_base.count(famshr_fname)
                                    for famshr_fname in famshr_fnames_base}

        famshr_fnames_dupes = [famshr_fname_base
                                    for famshr_fname_base, famshr_fname_count in famshr_fnames_count.items()
                                    if famshr_fname_count > 1]
    except Exception as err:
        # log_exception(err)
        return

    Gb.debug_log['_.famshr_fnames_base']  = famshr_fnames_base
    Gb.debug_log['_.famshr_fnames_count'] = famshr_fnames_count
    Gb.debug_log['_.famshr_fnames_dupes'] = famshr_fnames_dupes

    if famshr_fnames_dupes == []:
        return

    # Cycle thru the duplicates, create an evlog msg, select the one located most recent
    try:
        dup_devices_msg = ""
        dups_found_msg = ""
        famshr_fname_last_located_by_base_fname = {}
        for famshr_fname_base in famshr_fnames_dupes:
            _RawData_by_famshr_fname = {_RawData.fname:_RawData
                                        for device_id, _RawData in PyiCloud.RawData_by_device_id_famshr.items()
                                        if (_RawData.fname == famshr_fname_base
                                            or _RawData.fname.startswith(f"{famshr_fname_base}("))}

            dup_devices_msg += f"{CRLF_DOT}{famshr_fname_base}"
            located_last_secs = 0
            for famshr_fname, _RawData in _RawData_by_famshr_fname.items():
                if _RawData.location_secs > located_last_secs:
                    located_last_secs = _RawData.location_secs
                    famshr_fname_last_located_by_base_fname[famshr_fname_base] = famshr_fname

                dup_devices_msg += (f"{CRLF_HDOT}{famshr_fname} > "
                                    f"Located-{format_age(_RawData.location_secs)} "
                                    f"({_RawData.device_data['rawDeviceModel']})")

            if famshr_fname_base in famshr_fname_last_located_by_base_fname:
                dup_devices_msg += (f"{CRLF_HDOT}Last Located > {famshr_fname_last_located_by_base_fname[famshr_fname_base]}")
    except:
        if dup_devices_msg:
            dup_devices_msg += (f"{CRLF_HDOT}Last Located > Could not be determined")


    if dup_devices_msg  == "":  return

    dups_found_msg =(f"{EVLOG_ALERT}DUPLICATE FAMSHR DEVICES > There are several devices in the "
                f"iCloud Account Family Sharing list with the same or similar names. The unused devices should be reviewed and "
                f"removed. The Devices are:"
                f"{dup_devices_msg}")

    # Cycle thru dup names, get conf_devices entry for the one matching the famshr_fname_base and update it
    # famshr_fname_last_located_by_base_fname = {'Gary-iPad': 'Gary_iPad(2)'}
    update_conf_file_flag = False
    devices_updated_msg = f"{EVLOG_ALERT}UPDATED CONFIGURATION > Duplicate FamShr device updated to last located device > "
    for famshr_fname_base, famshr_fname_last_located in famshr_fname_last_located_by_base_fname.items():
        conf_device = [_conf_device for _conf_device in Gb.conf_devices
                                    if (_conf_device[CONF_FAMSHR_DEVICENAME].startswith(famshr_fname_base)
                                        and _conf_device[CONF_FAMSHR_DEVICENAME] != famshr_fname_last_located)]

        try:
            if conf_device != []:
                conf_device = conf_device[0]
                devices_updated_msg += (f"{CRLF_DOT}{conf_device[CONF_IC3_DEVICENAME]} > "
                                        f"{conf_device[CONF_FAMSHR_DEVICENAME]}{RARROW}"
                                        f"{famshr_fname_last_located}")

                conf_device[CONF_FAMSHR_DEVICENAME] = famshr_fname_last_located
                conf_device[CONF_FAMSHR_DEVICE_ID]  = _FamShr.device_id_by_famshr_fname[famshr_fname_last_located]
                update_conf_file_flag = True
                Device = Gb.Devices_by_devicename[conf_device[CONF_IC3_DEVICENAME]]
                Device.set_fname_alert(YELLOW_ALERT)

        except Exception as err:
            event_msg =( f"Error resolving similar device names, "
                        f"{famshr_fname_base}/{famshr_fname_last_located}, "
                        f"{err}")
            post_event(event_msg)

    # Print dups msg with info and update config file
    if update_conf_file_flag:
        dups_found_msg += more_info('famshr_dup_devices')
        post_event(dups_found_msg)

        config_file.write_storage_icloud3_configuration_file()
        post_event(devices_updated_msg)
        post_startup_alert(devices_updated_msg.replace(EVLOG_ALERT, '').replace(CRLF_DOT, CRLF_HDOT))
        log_warning_msg(f"iCloud3 > {devices_updated_msg}")

    # Config is OK. Just print dups msg as an alert
    elif dups_found_msg:
        post_event(dups_found_msg)

    Gb.startup_stage_status_controls.append('stage4_dup_check_done')

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

#--------------------------------------------------------------------
def setup_tracked_devices_for_fmf(PyiCloud=None):
    '''
    The Find-my-Friends device data is available from PyiCloud when logging into the iCloud
    account. This routine will get all the available FmF devices from the email contacts/following/
    followed data. The devices are then cycled through to be matched with the tracked devices
    and their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        PyiCloud: Object containing data to be processed. This might be from Gb.PyiCloud (normal/default)
                    or the one created in config_flow if the username was changed.
    '''
    return

    broadcast_info_msg(f"Stage 3 > Set up Find-my-Friends Devices")

    # devices_desc             = get_fmf_devices(PyiCloud)
    # device_id_by_fmf_email   = devices_desc[0]
    # fmf_email_by_device_id   = devices_desc[1]
    # device_info_by_fmf_email = devices_desc[2]

    if PyiCloud is None:
        PyiCloud = Gb.PyiCloud
    if PyiCloud is None:
        return

    PyiCloud = Gb.PyiCloud
    _FmF = PyiCloud.FindMyFriends

    event_msg = "Find-My-Friends Devices > "
    if Gb.conf_data_source_FMF is False:
        event_msg += "Not used as a data source"
        post_event(event_msg)
        return
    event_msg += f"{Gb.conf_fmf_device_cnt} of {len(Gb.conf_devices)} iCloud3 Devices Configured"
    post_event(event_msg)
    if Gb.conf_fmf_device_cnt == 0:
        return

    elif _FmF is None or _FmF.device_id_by_fmf_email == {}:
        event_msg += "NO DEVICES FOUND"
        post_event(f"{EVLOG_ALERT}{event_msg}")
        return

    try:
        Gb.fmf_device_verified_cnt = 0

        # Cycle through all the FmF devices in the iCloud account
        exception_event_msg = ''
        device_fname_by_device_id = {}
        sorted_device_id_by_fmf_email = OrderedDict(sorted(_FmF.device_id_by_fmf_email.items()))
        for fmf_email, device_id in sorted_device_id_by_fmf_email.items():
            broadcast_info_msg(f"Set up FmF Device > {fmf_email}")
            devicename    = ''
            device_fname  = ''
            _RawData      = None
            exception_msg = ''

            # Cycle througn the tracked devices and find the matching device
            # Verify the device_id in the configuration with the found
            # device and display a configuration error msg later if something
            # doesn't match
            for device in Gb.conf_devices:
                conf_fmf_email = device[CONF_FMF_EMAIL].split(" >")[0].strip()

                if conf_fmf_email == fmf_email:
                    devicename   = device[CONF_IC3_DEVICENAME]
                    device_fname = device[CONF_FNAME]
                    device_type  = device[CONF_DEVICE_TYPE]
                    _RawData = PyiCloud.RawData_by_device_id_fmf[device_id]

                    if device[CONF_FMF_DEVICE_ID] != device_id:
                        device[CONF_FMF_DEVICE_ID] = device_id
                    break

            crlf_mark = CRLF_DOT
            if _RawData is None:
                exception_msg = 'Not Tracked'

            elif device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                exception_msg = 'INACTIVE'
                crlf_mark = CRLF_X

            if exception_msg:
                exception_event_msg += (f"{crlf_mark}{fmf_email}{RARROW}{exception_msg}")
                continue

            # If no location info in pyiCloud data but tracked device is matched, refresh the
            # data and see if it is locatable now. If so, all is OK. If not, set to verified but
            # display no location exception msg in EvLog
            exception_msg = ''
            if _RawData.is_location_data_available is False:
                exception_msg = f", NO LOCATION DATA"

                PyiCloud.FindMyFriends.refresh_client()

            if _RawData and Gb.log_rawdata_flag:
                log_title = (f"FmF PyiCloud Data (device_data -- {devicename}/{fmf_email})")
                log_rawdata(log_title, {'data': _RawData.device_data})

            device_type = ''
            # The tracked or monitored device has been matched with available devices, mark it as verified.
            if devicename in Gb.Devices_by_devicename:
                Device               = Gb.Devices_by_devicename[devicename]
                device_fname_by_device_id[device_id] = Device.fname
                device_type          = Device.device_type
                #Device.verified_flag = True
                Device.verified_FMF = True
                Device.device_id_fmf = device_id
                Gb.Devices_by_icloud_device_id[device_id] = Device
                Gb.fmf_device_verified_cnt += 1

                event_msg += (  f"{CRLF_CHK}"
                                f"{fmf_email}{RARROW}{devicename}, "
                                f"{DEVICE_TYPE_FNAME.get(device_type, device_type)}"
                                f"{exception_msg}")
            else:
                event_msg += (  f"{CRLF_X}"
                                f"{fmf_email}{RARROW}{devicename}, "
                                f"{DEVICE_TYPE_FNAME.get(device_type, device_type)}"
                                f"{exception_msg}")

        # Replace known device_ids whith the actual name
        for device_id, device_fname in device_fname_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(  f"({device_id})", \
                                                                f"({device_fname_by_device_id[device_id]})")

        # Remove any unknown device_ids
        for device_id, fmf_email in _FmF.fmf_email_by_device_id.items():
            exception_event_msg = exception_event_msg.replace(f"({device_id})", "")

        event_msg += exception_event_msg
        post_event(event_msg)

        return

    except Exception as err:
        log_exception(err)

        event_msg =(f"iCloud3 Error from iCloud Loc Svcs > "
            "Error Authenticating account or no data was returned from "
            "iCloud Location Services. iCloud access may be down or the "
            "Username/Password may be invalid.")
        post_error_msg(event_msg)

    return

#----------------------------------------------------------------------
def get_famshr_devices_pyicloud(PyiCloud):
    '''
    The device information tables are built when the devices are added the when
    the FamilySharing object and RawData objects are created when logging into
    the iCloud account.
    '''
    if PyiCloud is None: PyiCloud = Gb.PyiCloud

    _FamShr = PyiCloud.FamilySharing
    return [_FamShr.device_id_by_famshr_fname,
            _FamShr.famshr_fname_by_device_id,
            _FamShr.device_info_by_famshr_fname,
            _FamShr.device_model_info_by_fname]

#----------------------------------------------------------------------
def get_fmf_devices_pyicloud(PyiCloud):
    '''
    The device information tables are built when the devices are added the when
    the FamilySharing object and RawData objects are created when logging into
    the iCloud account.
    '''

    if PyiCloud is None: PyiCloud = Gb.PyiCloud

    _FmF = PyiCloud.FindMyFriends
    return (_FmF.device_id_by_fmf_email,
            _FmF.fmf_email_by_device_id,
            _FmF.device_info_by_fmf_email)


#--------------------------------------------------------------------
# def set_device_data_source_mobapp():
#     '''
#     The Global tracking method is mobapp so set all Device's tracking method
#     to mobapp
#     '''
#     if Gb.conf_data_source_MOBAPP is False:
#         returnYou

#     for Device in Gb.Devices:
#         Device.data_source = 'mobapp'

#--------------------------------------------------------------------
def set_device_data_source_famshr_fmf(PyiCloud=None):
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        if PyiCloud is None: PyiCloud = Gb.PyiCloud

        Gb.Devices_by_icloud_device_id = {}
        devicename_not_tracked = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            data_source = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.device_id_famshr:
                device_id = Device.device_id_famshr
                if device_id in PyiCloud.RawData_by_device_id:
                    data_source = FAMSHR
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    _RawData = PyiCloud.RawData_by_device_id[device_id]

            if Device.device_id_fmf:
                device_id = Device.device_id_fmf
                if device_id in PyiCloud.RawData_by_device_id:
                    if data_source is None:
                        data_source = FMF
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    _RawData = PyiCloud.RawData_by_device_id[device_id]

            if (Device.mobapp_monitor_flag and data_source is None):
                data_source = MOBAPP

            if data_source != MOBAPP:
                info_msg = (f"Set PyiCloud Device Id > {Device.devicename}, "
                            f"DataSource-{data_source}, "
                            f"{CRLF}FamShr-({Device.device_id8_famshr}), "
                            f"FmF-({Device.device_id8_fmf})")
                post_monitor_msg(info_msg)

            #Device.data_source = data_source
            Device.primary_data_source = data_source

        info_msg = (f"PyiCloud Devices > ")
        for _device_id, _RawData in PyiCloud.RawData_by_device_id.items():
            info_msg += (f"{_RawData.name}/{_device_id[:8]}-{_RawData.data_source}, ")
        post_monitor_msg(info_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def tune_device_data_source_famshr_fmf():
    '''
    The goal is to get either all fmf or all famshr to minimize the number of
    calls to iCloud Web Services by pyicloud_ic3. Look at the fmf and famshr
    devices to see if:
    1. If all devices are fmf or all devices are famshr:
            Do not make any changes
    2. If set to fmf but it also has a famshr id, change to famshr.
    2. If set to fmf and no famshr id, leave as fmf.
    '''
    broadcast_info_msg(f"Stage 3 > Tune Tracking Method")

    try:
        # Global data_source specified, nothing to do
        if Gb.primary_data_source_ICLOUD is False:
            return
        elif Gb.Devices_by_devicename == {}:
            return

        cnt_famshr = 0     # famshr is specified as the data_source for the device in config
        cnt_fmf    = 0     # fmf is specified as the data_source for the device in config
        cnt_famshr_to_fmf = 0
        cnt_fmf_to_famshr = 0

        for devicename, Device in Gb.Devices_by_devicename.items():
            broadcast_info_msg(f"Tune Device Tracking Method > {devicename}")

            if Device.is_data_source_FAMSHR:
                cnt_famshr += 1
            elif Device.is_data_source_FMF:
                cnt_fmf += 1

            # Only count those with no data_source config parm
            Devices_famshr_to_fmf = []
            Devices_fmf_to_famshr = []
            if Device.data_source_config == '':
                if Device.is_data_source_FAMSHR and Device.device_id_fmf:
                    Devices_fmf_to_famshr.append(Device)
                    cnt_famshr_to_fmf += 1
                elif Device.is_data_source_FMF and Device.device_id_famshr:
                    Devices_famshr_to_fmf.append(Device)
                    cnt_fmf_to_famshr += 1

        if cnt_famshr == 0 or cnt_fmf == 0:
            pass
        elif cnt_famshr_to_fmf == 0 or cnt_fmf_to_famshr == 0:
            pass
        elif cnt_famshr >= cnt_fmf:
            for Device in Devices_fmf_to_famshr:
                #Device.data_source = FAMSHR
                Device.primary_data_source = FAMSHR
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)
                Gb.Devices_by_icloud_device_id[Device.device_id_famshr] = Device
        else:
            for Device in Devices_famshr_to_fmf:
                #Device.data_source = FMF
                Device.primary_data_source = FMF
                Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
                Gb.Devices_by_icloud_device_id[Device.device_id_fmf] = Device
    except:
        pass

#--------------------------------------------------------------------
def setup_tracked_devices_for_mobapp():
    '''
    Get the MobApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.
    '''
    check_mobile_app_integration()

    devices_desc = mobapp_interface.get_entity_registry_mobile_app_devices()
    mobapp_id_by_mobapp_devicename             = devices_desc[0]
    mobapp_devicename_by_mobapp_id             = devices_desc[1]
    device_info_by_mobapp_devicename           = devices_desc[2]
    device_model_info_by_mobapp_devicename     = devices_desc[3]
    last_updt_trig_by_mobapp_devicename        = devices_desc[4]
    mobile_app_notify_devicenames              = devices_desc[5]
    battery_level_sensors_by_mobapp_devicename = devices_desc[6]
    battery_state_sensors_by_mobapp_devicename = devices_desc[7]

    mobapp_error_mobile_app_msg = ''
    mobapp_error_search_msg     = ''
    mobapp_error_disabled_msg   = ''
    mobapp_error_not_found_msg  = ''
    Gb.mobapp_device_verified_cnt = 0

    unmatched_mobapp_devices = mobapp_id_by_mobapp_devicename.copy()
    verified_mobapp_fnames = []

    tracked_msg = f"Mobile App Devices > {Gb.conf_mobapp_device_cnt} of {len(Gb.conf_devices)} used by iCloud3"

    Gb.devicenames_x_mobapp_devicenames = {}
    for devicename, Device in Gb.Devices_by_devicename.items():
        broadcast_info_msg(f"Set up Mobile App Devices > {devicename}")

        conf_mobapp_device = Device.mobapp[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')
        Gb.devicenames_x_mobapp_devicenames[devicename] = None

        # Set mobapp devicename to icloud devicename if nothing is specified. Set to not monitored
        # if no icloud famshr name
        if conf_mobapp_device in ['', 'None']:
            Device.mobapp[DEVICE_TRACKER] = ''
            continue

        # Check if the specified mobapp device tracker is valid and in the entity registry
        if conf_mobapp_device.startswith('Search: ') is False:
            if conf_mobapp_device in mobapp_id_by_mobapp_devicename:
                mobapp_devicename = conf_mobapp_device
                Gb.devicenames_x_mobapp_devicenames[devicename]        = mobapp_devicename
                Gb.devicenames_x_mobapp_devicenames[mobapp_devicename] = devicename

            else:
                Device.set_fname_alert(YELLOW_ALERT)
                mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_device} > "
                                                f"Assigned to {Device.fname_devicename}")
        else:
            mobapp_devicename = _search_for_mobapp_device( devicename, Device,
                                                            mobapp_id_by_mobapp_devicename,
                                                            conf_mobapp_device)
            if mobapp_devicename:
                Gb.devicenames_x_mobapp_devicenames[devicename]        = mobapp_devicename
                Gb.devicenames_x_mobapp_devicenames[mobapp_devicename] = devicename
            else:
                Device.set_fname_alert(YELLOW_ALERT)
                mobapp_error_search_msg += (f"{CRLF_X}{conf_mobapp_device}_??? > "
                                            f"Assigned to {Device.fname_devicename}")

    for devicename, Device in Gb.Devices_by_devicename.items():
        mobapp_devicename = Gb.devicenames_x_mobapp_devicenames[devicename]
        if mobapp_devicename is None:
            continue

        mobapp_id  = mobapp_id_by_mobapp_devicename[mobapp_devicename]

        try:
            mobapp_fname = Gb.mobapp_fnames_x_mobapp_id[mobapp_id]
        except Exception as err:
            # log_exception(err)
            mobapp_fname = f"{mobapp_devicename.replace('_', ' ').title()}(?)"

        Gb.devicenames_x_mobapp_devicenames[mobapp_fname] = devicename

        # device_tracker entity is disabled
        if mobapp_id in Gb.mobapp_fnames_disabled:
            Device.set_fname_alert(YELLOW_ALERT)
            Device.mobapp_device_unavailable_flag = True
            mobapp_error_disabled_msg += (  f"{CRLF_DOT}{mobapp_devicename} > "
                                            f"Assigned to-{Device.fname_devicename}")
            continue

        # Build errors message, can still use the Mobile App for zone changes but sensors are not monitored
        if (last_updt_trig_by_mobapp_devicename.get(mobapp_devicename, '') == ''
                or instr(last_updt_trig_by_mobapp_devicename.get(mobapp_devicename, ''), 'DISABLED')
                or battery_level_sensors_by_mobapp_devicename.get(mobapp_devicename, '') == ''
                or instr(battery_level_sensors_by_mobapp_devicename.get(mobapp_devicename, ''), 'DISABLED')):
            Device.set_fname_alert(YELLOW_ALERT)
            mobapp_error_mobile_app_msg += (f"{CRLF_DOT}{mobapp_devicename} > "
                                            f"Assigned to {Device.fname_devicename}")

        verified_mobapp_fnames.append(mobapp_fname)
        Device.conf_mobapp_fname = mobapp_fname
        Device.mobapp_monitor_flag = True
        Gb.mobapp_device_verified_cnt += 1
        Device.verified_MOBAPP = True


        # Set raw_model that will get picked up by device_tracker and set in the device registry if it is still
        # at it's default value. Normally, raw_model is set when setting up FamShr if that is available, FmF does not
        # set raw_model since it is only shared via an email addres or phone number. This will also be saved in the
        # iCloud3 configuration file.
        raw_model, model, model_display_name = device_model_info_by_mobapp_devicename[mobapp_devicename]
        if ((raw_model and Device.raw_model != raw_model)
                or (model and Device.model != model)
                or (model_display_name and Device.model_display_name != model_display_name)):

            for conf_device in Gb.conf_devices:
                if conf_device[CONF_MOBILE_APP_DEVICE] == mobapp_devicename:
                    if raw_model:
                        Device.raw_model = conf_device[CONF_RAW_MODEL] = raw_model
                    if model:
                        Device.model = conf_device[CONF_MODEL] = model
                    if model_display_name:
                        Device.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
                    config_file.write_storage_icloud3_configuration_file()
                    break

        Gb.Devices_by_mobapp_devicename[mobapp_devicename] = Device
        Device.mobapp[DEVICE_TRACKER] = f"device_tracker.{mobapp_devicename}"
        Device.mobapp[TRIGGER]        = f"sensor.{last_updt_trig_by_mobapp_devicename.get(mobapp_devicename, '')}"
        Device.mobapp[BATTERY_LEVEL]  = Device.sensors['mobapp_sensor-battery_level'] = \
                                        f"sensor.{battery_level_sensors_by_mobapp_devicename.get(mobapp_devicename, '')}"
        Device.mobapp[BATTERY_STATUS] = Device.sensors['mobapp_sensor-battery_status'] = \
                                        f"sensor.{battery_state_sensors_by_mobapp_devicename.get(mobapp_devicename, '')}"

        tracked_msg += (f"{CRLF_CHK}{mobapp_fname}, {mobapp_devicename} ({Device.raw_model}) >"
                        f"{CRLF_SP8_HDOT}{devicename}, {Device.fname} "
                        f"{Device.tracking_mode_fname}")

        # Remove the mobapp device from the list since we know it is tracked
        if mobapp_devicename in unmatched_mobapp_devices:
            unmatched_mobapp_devices.pop(mobapp_devicename)

    setup_notify_service_name_for_mobapp_devices()

    # Devices in the list were not matched with an iCloud3 device or are disabled
    for mobapp_devicename, mobapp_id in unmatched_mobapp_devices.items():
        devicename = Gb.devicenames_x_mobapp_devicenames.get(mobapp_devicename, 'unknown')
        Device     = Gb.Devices_by_devicename.get(devicename)

        try:
            mobapp_fname = Gb.mobapp_fnames_x_mobapp_id[mobapp_id]
            mobapp_dev_info = device_info_by_mobapp_devicename[mobapp_devicename]
            fname_dev_type  = mobapp_dev_info.rsplit('(')
            mobapp_dev_type = f"({fname_dev_type[1]}"

        except Exception as err:
            # log_exception(err)
            mobapp_info     = f"{mobapp_devicename.replace('_', ' ').title()}(?)"
            mobapp_fname    = mobapp_info
            mobapp_dev_type = ''

        duplicate_msg = ' (DUPLICATE NAME)' if mobapp_fname in verified_mobapp_fnames else ''
        crlf_sym = CRLF_X
        device_msg = "Not Monitored" if Device else "Not Assigned to an iCloud3 Device"

        if mobapp_id in Gb.mobapp_fnames_disabled:
            if Device:
                device_msg  = "DISABLED IN MOBILE APP INTEGRATION"
                crlf_sym    = CRLF_RED_X
            else:
                device_msg += ' (Disabled)'

        tracked_msg += (f"{crlf_sym}{mobapp_fname}, {mobapp_devicename} {mobapp_dev_type} >")
        if Device:
            Device.set_fname_alert(YELLOW_ALERT)
            tracked_msg += (f"{CRLF_SP8_HDOT}{Device.fname}, {Device.devicename}")
        tracked_msg += f"{CRLF_SP8_HDOT}{device_msg}{duplicate_msg}"
    post_event(tracked_msg)

    _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_search_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg)

    return

#--------------------------------------------------------------------
def _search_for_mobapp_device(devicename, Device, mobapp_id_by_mobapp_devicename, conf_mobapp_device):
    '''
    The conf_mobapp_devicename parameter starts with 'Search: '. Scan the list of mobapp
    devices and find the one that starts with the ic3_devicename value

    Return:
        mobapp device_tracker entity name - if it was found
        None - More than one entity or no entities were found
    '''

    conf_mobapp_device = conf_mobapp_device.replace('Search: ', '')

    matched_mobapp_devices = [k for k, v in mobapp_id_by_mobapp_devicename.items()
                    if k.startswith(conf_mobapp_device) and v.startswith('DISABLED') is False]

    Gb.debug_log['_.matched_mobapp_devices'] = matched_mobapp_devices

    if len(matched_mobapp_devices) == 1:
        return matched_mobapp_devices[0]

    elif len(matched_mobapp_devices) == 0:
        return None

    elif len(matched_mobapp_devices) > 1:
        mobapp_devicename = matched_mobapp_devices[-1]
        post_startup_alert( f"Mobile App device_tracker entity scan found several devices: "
                            f"{Device.fname_devicename}")

        alert_msg =(f"{EVLOG_ALERT}DUPLICATE MOBAPP DEVICES FOUND > More than one Device Tracker Entity "
                    f"was found during the scan of the HA Device Registry."
                    f"{CRLF_X}AssignedTo-{Device.fname_devicename}"
                    f"{CRLF}{more_info('mobapp_error_multiple_devices_on_scan')}"
                    f"{CRLF}{'-'*75}"
                    f"{CRLF}Count-{len(matched_mobapp_devices)}, "
                    f"{CRLF}Entities-{', '.join(matched_mobapp_devices)}, "
                    f"{CRLF}Monitored-{mobapp_devicename}")
        post_event(alert_msg)

        log_error_msg(f"iCloud3 Error > Mobile App Config Error > Dev Trkr Entity not found "
                    f"during Search {conf_mobapp_device}_???. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")
        return mobapp_devicename

    return None

#--------------------------------------------------------------------
def _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_search_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg):

    if mobapp_error_mobile_app_msg:
        post_startup_alert( f"Mobile App Integration missing trigger or battery sensors"
                            f"{mobapp_error_mobile_app_msg.replace(CRLF_X, CRLF_DOT)}")

        alert_msg =(f"{EVLOG_ALERT}MOBILE APP INTEGRATION (Mobile App) SET UP PROBLEM > The Mobile App "
                    f"Integration `last_update_trigger` and `battery_level` sensors are disabled or "
                    f"were not found during the scan of the HA Entities Registry for a Device."
                    f"iCloud3 will use the Mobile App for Zone (State) changes but update triggers and/or "
                    f"battery information will not be available for these devices."
                    f"{mobapp_error_mobile_app_msg}"
                    f"{more_info('mobapp_error_mobile_app_msg')}")
        post_event(alert_msg)

        log_error_msg(f"iCloud3 Error > The Mobile App Integration has not been set up or the "
                    f"battery_level or last_update_trigger sensor entities were not found."
                    f"{mobapp_error_mobile_app_msg}")

    if mobapp_error_search_msg:
        post_startup_alert( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_search_msg.replace(CRLF_X, CRLF_DOT)}")

        alert_msg =(f"{EVLOG_ALERT}MOBAPP DEVICE NOT FOUND > An MobApp device_tracker "
                    f"entity was not found in the `Scan for mobile_app devices` in the HA Device Registry."
                    f"{mobapp_error_search_msg}"
                    f"{more_info('mobapp_error_search_msg')}")
        post_event(alert_msg)

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_search_msg}. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_not_found_msg:
        post_startup_alert( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_not_found_msg.replace(CRLF_X, CRLF_DOT)}")

        alert_msg =(f"{EVLOG_ALERT}MOBAPP DEVICE NOT FOUND > The device tracker entity "
                    f"was not found during the scan of the HA Device Registry."
                    f"{mobapp_error_not_found_msg}"
                    f"{more_info('mobapp_error_not_found_msg')}")
        post_event(alert_msg)

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity was not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_not_found_msg}"
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_disabled_msg:
        post_startup_alert( f"Mobile App Config Error > Device Tracker Entity disabled"
                            f"{mobapp_error_disabled_msg.replace(CRLF_X, CRLF_DOT)}")

        alert_msg =(f"{EVLOG_ALERT}MOBILE APP DEVICE DISABLED > The device tracker entity "
                    f"is disabled so the mobile_app last_update_trigger and bettery_level sensors "
                    f"can not be monitored. iCloud3 will not use the Mobile App for these devices."
                    f"{mobapp_error_disabled_msg}"
                    f"{more_info('mobapp_error_disabled_msg')}")
        post_event(alert_msg)

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity is disabled and "
                    f"can not be monitored by iCloud3."
                    f"{mobapp_error_disabled_msg}"
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

#--------------------------------------------------------------------
def setup_notify_service_name_for_mobapp_devices(post_event_msg=False):
    '''
    Get the MobApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.

    Parameters:
        post_event_msg -
                Post an event msg indicating the notify device names were set up. This is done
                when they are set up when this is run after HA has started

    '''
    mobile_app_notify_devicenames = mobapp_interface.get_mobile_app_notify_devicenames()

    setup_msg = ''

    # Cycle thru the ha notify names and match them up with a device. This function runs
    # while iC3 is starting and again when ha has started. HA may run iC3 before
    # 'notify.mobile_app' so running again when ha has started makes sure they are set up.
    for mobile_app_notify_devicename in mobile_app_notify_devicenames:
        mobapp_devicename = mobile_app_notify_devicename.replace('mobile_app_', '')
        for devicename, Device in Gb.Devices_by_devicename.items():
            if instr(mobapp_devicename, devicename) or instr(devicename, mobapp_devicename):
                if Device.mobapp[NOTIFY] == '':
                    Device.mobapp[NOTIFY] = mobile_app_notify_devicename
                    setup_msg += (f"{CRLF_DOT}{Device.devicename_fname}{RARROW}{mobile_app_notify_devicename}")
                break

    if setup_msg and post_event_msg:
        post_event(f"Delayed MobApp Notifications Setup Completed > {setup_msg}")

#--------------------------------------------------------------------
def log_debug_stage_4_results():

    # if Gb.log_debug_flag:
    #     log_debug_msg(f"{Gb.Devices=}")
    #     log_debug_msg(f"{Gb.Devices_by_devicename=}")
    #     log_debug_msg(f"{Gb.conf_devicenames=}")
    #     log_debug_msg(f"{Gb.conf_famshr_devicenames=}")
    #     self.devices_not_set_up          = []
    #     self.device_id_by_famshr_fname   = {}       # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
    #     self.famshr_fname_by_device_id   = {}       # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
    #     self.device_info_by_famshr_fname = {}       # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro (iPhone15,2)'}
    #     self.device_model_info_by_fname  = {}       # {'Gary-iPhone': [raw_model,model,model_display_name]}
    #     self.dup_famshr_fname_cnt
    return

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 5
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# def remove_unverified_untrackable_devices(PyiCloud=None):

#     if PyiCloud is None: PyiCloud = Gb.PyiCloud
#     if PyiCloud is None:
#         return
#     if PyiCloud.FamilySharing is None and PyiCloud.FindMyFriends is None:
#         return

#     _Devices_by_devicename = Gb.Devices_by_devicename.copy()
#     device_removed_flag = False
#     alert_msg =(f"{EVLOG_ALERT}UNTRACKABLE DEVICES ALERT > Devices are not being tracked:")
#     for devicename, Device in _Devices_by_devicename.items():
#         Device.display_info_msg("Verifing Devices")

#         # Device not verified as valid FmF, FamShr or MobApp device. Remove from devices list
#         if Device.data_source is None or Device.verified_flag is False:
#             device_removed_flag = True
#             alert_msg +=(f"{CRLF_DOT}{devicename} ({Device.fname_devtype})")

#             devicename = Device.devicename
#             if Device.device_id_famshr:
#                 Gb.Devices_by_icloud_device_id.pop(Device.device_id_famshr)
#             if Device.device_id_fmf:
#                 Gb.Devices_by_icloud_device_id.pop(Device.device_id_fmf)

#             Gb.Devices_by_devicename.pop(devicename)

#     if device_removed_flag:
#         alert_msg +=f"{more_info('unverified_device')}"
#         post_event(alert_msg)
#         post_startup_alert('Some devices are not being tracked')

#------------------------------------------------------------------------------
def set_devices_verified_status():
    '''
    Cycle thru the Devices and set verified status based on data sources
    '''
    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.verified_flag = (Device.verified_FAMSHR
                            or  Device.verified_FMF
                            or  Device.verified_MOBAPP)

        # If the data source is FamShr and the device is not verified, set the
        # data source to MobApp
        if (Device.verified_flag
                and Device.is_data_source_FAMSHR_FMF
                and Device.verified_FAMSHR is False
                and Device.verified_FMF is False
                and Device.verified_MOBAPP):
            Device.primary_data_source = MOBAPP

#------------------------------------------------------------------------------
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

    Gb.debug_log['Gb.Devices_by_devicename_tracked'] = Gb.Devices_by_devicename_tracked
    Gb.debug_log['Gb.Devices_by_devicename_monitored'] = Gb.Devices_by_devicename_monitored

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

    # Cycle thru any paired devices and associate them with each other
    # Gb.PairedDevices_by_paired_with_id={'NDM0NTU2NzE3': [<Device: lillian_watch>, <Device: lillian_iphone>]}
    for PairedDevices in Gb.PairedDevices_by_paired_with_id.values():
        if len(PairedDevices) != 2 or PairedDevices[0] is PairedDevices[1]:
            continue
        try:
            PairedDevices[0].PairedDevice = PairedDevices[1]
            PairedDevices[1].PairedDevice = PairedDevices[0]
        except:
            pass

    _display_all_devices_config_info()

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

    if Gb.primary_data_source_ICLOUD is False:
        if Gb.conf_data_source_ICLOUD:
            post_event("iCloud Location Tracking is not available")
        else:
            post_event("iCloud Location Tracking is not being used")

    if Gb.conf_data_source_MOBAPP is False:
        post_event("Mobile App Location Tracking is not being used")

#------------------------------------------------------------------------------
def _display_all_devices_config_info():
    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.display_info_msg(f"Set Trackable Devices > {devicename}")
        if Device.verified_flag:
            tracking_mode = ''
        else:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_famshr_device_cnt > 0)
            tracking_mode = f"{RED_X} NOT "
            Device.evlog_fname_alert_char += RED_X

        tracking_mode += 'Monitored' if Device.is_monitored else 'Tracked'
        event_msg =(f"{tracking_mode} Device > {devicename} ({Device.fname_devtype})")

        if Gb.primary_data_source_ICLOUD:
            event_msg += f"{CRLF_DOT}iCloud Tracking Parameters:"
            if Device.is_data_source_FAMSHR:
                Gb.used_data_source_FAMSHR = True
                event_msg += f"{CRLF_HDOT}FamShr Device: {Device.conf_famshr_name}"

            if Device.is_data_source_FMF:
                Gb.used_data_source_FMF = True
                event_msg += f"{CRLF_HDOT}FmF Device: {Device.conf_fmf_email}"

            if Device.PairedDevice is not None:
                event_msg += (f"{CRLF_HDOT}Paired Device: {Device.PairedDevice.fname_devicename}")

        # Set a flag indicating there is a tracked device that does not use the Mobile App
        if Device.mobapp_monitor_flag is False and Device.is_tracked:
            Gb.mobapp_monitor_any_devices_false_flag = True

        if Device.mobapp[DEVICE_TRACKER] == '':
            event_msg += f"{CRLF_DOT}Mobile App Tracking Parameters: Mobile App Not Used"
        else:
            event_msg += CRLF_DOT if Device.mobapp_monitor_flag else CRLF_RED_X
            event_msg += f"Mobile App Tracking Parameters:"

            trigger_entity = Device.mobapp[TRIGGER][7:] or 'UNKNOWN'
            bat_lev_entity = Device.mobapp[BATTERY_LEVEL][7:] or 'UNKNOWN'
            notify_entity  = Device.mobapp[NOTIFY] or 'WAITING FOR NOTIFY SVC TO START"'
            event_msg += (  f"{CRLF_HDOT}Device Tracker: {Device.mobapp[DEVICE_TRACKER]}"
                            f"{CRLF_HDOT}Action Trigger.: {trigger_entity}"
                            f"{CRLF_HDOT}Battery Sensor: {bat_lev_entity}"
                            f"{CRLF_HDOT}Notifications...: {notify_entity}")

        event_msg += f"{CRLF_DOT}Other Parameters:"
        event_msg += f"{CRLF_HDOT}inZone Interval: {format_timer(Device.inzone_interval_secs)}"
        if Device.fixed_interval_secs > 0:
            event_msg += f"{CRLF_HDOT}Fixed Interval: {format_timer(Device.fixed_interval_secs)}"
        if 'none' not in Device.log_zones:
            log_zones_fname = [zone_dname(zone) for zone in Device.log_zones]
            log_zones = list_to_str(log_zones_fname)
            log_zones = f"{log_zones.replace(', Name-', f'{RARROW}(')}.csv)"
            event_msg += f"{CRLF_HDOT}Log Zone Activity: {log_zones}"

        if Device.track_from_base_zone != HOME:
                event_msg += f"{CRLF_HDOT}Primary Track from Zone: {zone_dname(Device.track_from_base_zone)}"
        if Device.track_from_zones != [HOME]:
            tfz_fnames = [zone_dname(zone) for zone in Device.track_from_zones]
            event_msg += (f"{CRLF_HDOT}Track from Zones: {list_to_str(tfz_fnames)}")
        if Device.away_time_zone_offset != 0:
            plus_minus = '+' if Device.away_time_zone_offset > 0 else ''
            event_msg += (f"{CRLF_HDOT}Away Time Zone: HomeZone {plus_minus}{Device.away_time_zone_offset} hours")

        try:
            device_status = Device.PyiCloud_RawData_famshr.device_data[ICLOUD_DEVICE_STATUS]
            timestamp     = Device.PyiCloud_RawData_famshr.device_data[LOCATION][TIMESTAMP]
            if device_status == '201':
                event_msg += (f"{CRLF_RED_X}DEVICE IS OFFLINE > "
                            f"Since-{format_time_age(timestamp)}")
                Device.offline_secs = timestamp

            # if Device.no_location_data:
            #     event_msg += f"{CRLF_RED_X}NO GPS DATA RETURNED FROM ICLOUD LOCATION SERVICE"

        except Exception as err:
            # log_exception(err)
            pass

        post_event(event_msg)

#------------------------------------------------------------------------------
def display_inactive_devices():
    '''
    Display a list of the Inactive devices in the Event Log
    '''

    inactive_devices =[(f"{conf_device[CONF_IC3_DEVICENAME]} ("
                        f"{conf_device[CONF_FNAME]}/{conf_device[CONF_DEVICE_TYPE]})")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

    Gb.debug_log['_.inactive_devices'] = inactive_devices

    if inactive_devices == []:
        return

    event_msg = f"Inactive/Untracked Devices > "
    event_msg+= list_to_str(inactive_devices, separator=CRLF_DOT)
    post_event(event_msg)

    if len(inactive_devices) == len(Gb.conf_devices):
        post_startup_alert('All devices are Inactive and nothing will be tracked')
        event_msg =(f"{EVLOG_ALERT}ALL DEVICES ARE INACTIVE > "
                    f"{more_info('all_devices_inactive')}")
        post_event(event_msg)

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

#------------------------------------------------------------------------------
def display_platform_operating_mode_msg():
    if Gb.ha_config_platform_stmt is False:
        return

    if Gb.conf_profile[CONF_VERSION] == 1:
        alert_msg =("HA tried to start iCloud3 from a configuration.yaml file statement. "
                    "It was ignored.")
    else:
        post_startup_alert('HA configuration.yaml contains a `platform: iCloud3` that can be deleted')
        alert_msg = (f"{EVLOG_ALERT}HA CONFIG CHANGE NEEDED > iCloud3 is an HA Integration. Delete the 'platform: icloud3` "
                "configuration parameters in the HA `configuration.yaml` file.")

    post_event(alert_msg)

#------------------------------------------------------------------------------
def post_restart_icloud3_complete_msg():
    for devicename, Device in Gb.Devices_by_devicename.items():   #
        Device.display_info_msg("Setup Complete, Locating Device")

    event_msg =(f"{EVLOG_IC3_STARTING}Initializing iCloud3 v{Gb.version} > Complete")
    post_event(event_msg)

    Gb.EvLog.update_event_log_display("")