#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Global Variables Class Object
#
#   Global Variables is a general class to allow access to iCloud3 shared variables from
#   multiple classes. The variable to be referenced is defined in the __init__
#   function with it's default value.
#
#   Usage:
#       The following code is added to the module.py file containing another class
#       that needs access to the shared global variables.
#
#       Add the following code before the class statement:
#           from .globals import GlobalVariables as GbObj
#
#       Add the following code in the __init__ function:
#           def __init(self, var1, var2, ...):
#               global Gb
#               Gb = GbObj.MasterGbObject
#
#       The shared variables can then be shared using the Gb object:
#           Gb.time_format
#           Gb.Zones_by_zone
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from .const          import (DEVICENAME_MOBAPP, VERSION, VERSION_BETA,
                            NOT_SET, HOME_FNAME, HOME, STORAGE_DIR, WAZE_USED,
                            APPLE_SERVER_ENDPOINT,
                            DEFAULT_GENERAL_CONF, DEFAULT_TRACKING_CONF,
                            CONF_UNIT_OF_MEASUREMENT,
                            CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE,
                            CONF_CENTER_IN_ZONE, CONF_DISPLAY_GPS_LAT_LONG,
                            CONF_TRAVEL_TIME_FACTOR, CONF_GPS_ACCURACY_THRESHOLD,
                            CONF_DISCARD_POOR_GPS_INZONE, CONF_OLD_LOCATION_THRESHOLD, CONF_OLD_LOCATION_ADJUSTMENT,
                            CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL, CONF_MOBAPP_ALIVE_INTERVAL,
                            CONF_WAZE_REGION, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                            CONF_WAZE_REALTIME, CONF_PASSWORD_SRP_ENABLED,
                            CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE ,
                            CONF_WAZE_HISTORY_TRACK_DIRECTION,
                            CONF_STAT_ZONE_FNAME,
                            CONF_STAT_ZONE_BASE_LATITUDE, CONF_STAT_ZONE_BASE_LONGITUDE,
                            CONF_STAT_ZONE_INZONE_INTERVAL, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                            CONF_MOBAPP_REQUEST_LOC_MAX_CNT, CONF_DISTANCE_BETWEEN_DEVICES,
                            CONF_PASSTHRU_ZONE_TIME,
                            CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                            CONF_TFZ_TRACKING_MAX_DISTANCE,
                            CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                            CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,

                            CONF_STAT_ZONE_STILL_TIME,
                            CONF_STAT_ZONE_INZONE_INTERVAL,
                            ALERTS_SENSOR_ATTRS,
                            )


#import logging
#_LOGGER = logging.getLogger("icloud3_cf")

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class GlobalVariables(object):
    '''
    Define global variables used to enable testing iCloud3 functions
    '''
    disable_upw_filter = False # Disable filtering passwords in the icloud3.log file
    fido2_security_keys_enabled = False

    # This variable provides a mechanism of testing Internet Connection Errors when iCloud3 is
    # starting without an actual error.
    # Setting to True will raise an ConnectionError error in 'icloud_requests'
    # that sets Gb.internet_error to True. Then in the 'icloud3_main' 5-sec loop, the Gb.internet_error
    # flag is tested and then calls the start_internet_error_handler function
    # below that handles internet errors.
    test_internet_error = False
    test_internet_error_counter = 2

    # This variable provides a mechanism of testing Internet Connection Errors after iCloud3 has
    # starting without an actual error.
    # Set this to True, then select 'EvLog > Actions > Locate with iCloud'. This will set the
    # 'internet_error_test' to True and set this variable to False. A Locate will then be issued
    # and caught as described above.
    test_internet_error_after_startup = False

    '''
    Define global variables used in the various iCloud3 modules
    '''

    # Fixed variables set during iCloud3 loading that will not change
    version         = f"{VERSION}{VERSION_BETA}"
    version_beta    = VERSION_BETA
    version_evlog   = ''
    version_hacs    = ''

    hass            = None      # hass: HomeAssistant set in __init__
    config_entry    = None      # hass.config_entry set in __init__ (integration)
    config          = None      # has config parmaeter set in __init__ (platform)
    entry_id        = None      # Has entry_id for iCloud3
    local_ip        = None      # from component/local_ip/async_get_source_ip in __init__
    network_url     = None      # from helpers/network/get_url in __init__
    evlog_btnconfig_url = ''
    sensor_async_add_entities = None            # Initial add_entities link passed to sensor during ha startup
    async_add_entities_device_tracker = None    # Initial add_entities link passed to device_tracker during ha startup
    async_executor_call_parameters = None

    ha_location_info    = {'country_code': 'us', 'use_metric': False}
    country_code        = 'us'
    use_metric          = False

    iCloud3             = None   # iCloud3 Platform object
    MobileApp_data      = {}     # mobile_app Integration data dict from hass.data['mobile_app']
    MobileApp_devices   = {}     # mobile_app Integration devices dict from hass.data['mobile_app']['devices]

    config_entry_id     = None
    OptionsFlowHandler  = None  # OptionsFlowHandler (config_flow)

    EvLog               = None   # Event Log
    EvLogSensor         = None   # Event Log Sensor
    IntConnTest         = None   # Internet Connection Test Availabile Handler
    InternetError          = None   # Internet Connection Error Handler
    Waze                = None   # Waze Route ttime & distance handler
    WazeHist            = None   # Waze History Database handler
    WazeHistTrackSensor = None   # Sensor for updating the lat/long values for the WazeHist Map display

    HARootLogger        = None   # HA Root Logger (used in messaging.py during initialization)
    HALogger            = None   # HA Log
    iC3Logger           = None   # iCloud3 Log
    iC3Logger_last_check_exist_secs = 0
    prestartup_log      = ''     # _log calls made before the IC3Logger is set up will be stored here

    iC3EntityPlatform   = None   # iCloud3 Entity Platform (homeassistant.helpers.entity_component)
    AppleAcct           = None   # iCloud Account service
    AppleAcctLoggingInto = None   # AppleAcct being set up  that can be used if the login fails
    AppleAcct_needing_reauth_via_ha = {} # Reauth needed sent to ha for notify msg display
    ValidateAppleAcctUPW = None    # A session that can be used to verify the username/password

    # AppleAcct objects by various categories
    AppleAcct_by_username             = {}  # AppleAcct object for each Apple acct username
    AppleAcct_password_by_username    = {}  # Password for each Apple acct username
    AppleAcct_logging_in_usernames    = []  # usernames that are currently logging in. Used to prevent another login
    AppleAcct_error_by_username       = {}  # An error was encountered during verification, login or authentication
    iCloudSession_by_username         = {}  # Session object for a username, set in Session so exists on an error

    valid_upw_by_username             = {}  # The username/password validation status
    valid_upw_results_msg             = ''  # valid upw results from Stage 3 to redisplay in Stage 4

    conf_usernames                    = []  # List of Apple Acct usernames in config
    AppleAcct_by_devicename           = {}  # AppleAcct object for each ic3 devicename
    Devices_by_username               = {}  # List of Devices for each username ('gary@email.com': [gary_iphone, lillian_iphone])
    owner_device_ids_by_username      = {}  # List of owner info for Devices in Apple Acct
    owner_Devices_by_username         = {}  # List of Devices in the owner Apple Acct (excludes those in the iCloud list)

    upw_filter_items                  = {}    # username/pws to be filtered from the EvLog and log file
    upw_unfilter_items                = {}    # username/pws that are filtered that need to be unfiltered (icloud3_alerts items)
    upw_hide_items                    = []    # username/passwords that should be hidded instead of filtered

    usernames_setup_error_retry_list  = []  # usernames that failed to set up in Stage 4 and need to be retried
    devicenames_setup_error_retry_list= []  # devices that failed to set up in Stage 4 and need to be retried
    startup_alerts_by_source          = {}  # alerts during startup by devicename/apple_acct/mobapp device

    #polling_5_sec_loop_running = False
    operating_mode              = 0         # Platform (Legacy using configuration.yaml) or Integration
    ha_config_platform_stmt     = False     # a platform: icloud3 stmt is in the configurationyaml file that needs to be removed
    add_entities                = None
    ha_started                  = False     # Set to True in start_ic3.ha_startup_completed from listener in __init__

    # iCloud3 Directory & File Names
    ha_config_directory         = ''      # '/config', '/home/homeassistant/.homeassistant'
    ha_storage_directory        = ''      # 'config/.storage' directory
    ha_storage_icloud3          = ''      # 'config/.storage/icloud3'
    icloud3_config_filename     = ''      # 'config/.storage/icloud3/configuration' - iC3 Configuration File
    icloud3_restore_state_filename = ''   # 'config/.storage/icloud3/restore_state'
    config_ic3_yaml_filename    = ''      # 'config/config_ic3.yaml' (v2 config file name)
    icloud3_directory           = ''
    ha_config_www_directory     = ''
    www_evlog_js_directory      = ''
    www_evlog_js_filename       = ''
    wazehist_database_filename  = ''      # Waze Location History sql database (.storage/icloud3.waze_route_history.db)
    picture_www_dirs            = []

    # Platform and iCloud account parameters
    username                     = ''
    username_base                = ''
    password                     = ''
    encode_password_flag         = True
    all_find_devices             = True
    entity_registry_file         = ''
    devices                      = ''

    # icloud.com url suffix for china HOME_ENDPOINT & SETUP_ENDPOINT .com --> .com.cn for China
    icloud_server_suffix         = ''
    HOME_ENDPOINT                = APPLE_SERVER_ENDPOINT['home']
    SETUP_ENDPOINT               = APPLE_SERVER_ENDPOINT['setup']
    AUTH_ENDPOINT                = APPLE_SERVER_ENDPOINT['auth']


    # Global Object Dictionaries
    Devices                           = []  # Devices objects list
    Devices_by_devicename             = {}  # All Devices by devicename
    Devices_by_devicename_monitored   = {}  # All monitored Devices by devicename
    Devices_by_devicename_tracked     = {}  # All monitored Devices by devicename
    Devices_by_icloud_device_id       = {}  # Devices by the icloud device_id receive from Apple
    Devices_by_ha_device_id           = {}  # Device by the device_id in the entity/device registry
    Devices_by_mobapp_dname           = {}  # All verified Devices by the  conf_mobapp_dname
    Devices_by_nearby_group           = {}  # Devvic by group within  50mm of each other
    inactive_fname_by_devicename      = {}  # Devices with tracking_mode=inactive

    InternetPingIP                    = None    # Internet Connection Test Availabile Handler
    InternetError                     = None    # Internet Connection Error Handler
    internet_error                    = False   # Internet Connection Error Flag (set in AppleAcct_Session)
    icloud_io_request_secs            = 0       # Last time a request was sent in PyIcloud, > 1-min ago = internet is down
    icloud_io_1_min_timer_fct         = None    # 1-min timer set when an icloud_io call is made

    external_ip_name                  = None   # External IP name and address of the users newtowrk (internet_error)
    external_ip_address               = None
    apple_com_ip_address              = None
    pingable_ip_name                  = None   # Pingable  P name and address to use to test the internet status (internet_error)
    pingable_ip_address               = None
    pingable_ip_Ping                  = None   # Ping object from the Ping helpers routined (internet_error)
    httpx                             = None   # HTTPX Client from the HA httpx.client (setup & used in file_io.py)

    # iCloud Device information - These is used verify the device, display on the EvLog and in the Config Flow
    # device selection list on the iCloud3 Devices screen
    devices_not_set_up                = []
    device_id_by_icloud_dname         = {}  # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
    icloud_dname_by_device_id         = {}  # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
    device_info_by_icloud_dname       = {}  # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro (iPhone15,2)'}
    device_model_info_by_fname        = {}  # {'Gary-iPhone': [raw_model,model,model_display_name]}
    dup_icloud_dname_cnt              = {}  # Used to create a suffix for duplicate devicenames
    devices_without_location_data     = []

    devicenames_by_icloud_dname       = {}  # All ic3_devicenames by conf_find_devices
    icloud_dnames_by_devicename       = {}  # All ic3_devicenames by conf_find_devices
    devicenames_by_mobapp_dname  = {}  # All ic3_devicenames by conf_mobapp_dname
    mobapp_dnames_by_devicename  = {}  # All ic3_devicenames by conf_mobapp_dname

    mobapp_fnames_by_mobapp_id      = {}  # All mobapp_fnames by mobapp_deviceid from HA hass.data MobApp entry
    mobapp_ids_by_mobapp_fname      = {}  # All mobapp_fnames by mobapp_deviceid from HA hass.data MobApp entry
    mobapp_fnames_disabled          = []
    mobile_app_device_fnames        = []  # fname = name_by_user or name in mobile_app device entry
    model_display_name_by_raw_model = {}

    # From HA Entity Reg file - mobapp_interface.get_entity_registry_mobile_app_devices
    mobapp_id_by_mobapp_dname         = {}
    mobapp_dname_by_mobapp_id         = {}

    device_info_by_mobapp_dname       = {}  # [mobapp_fname, raw_model, model, model_display_name]
                                            # ['Gary-iPhome (MobApp)','iPhone15,2', 'iPhone', 'iPhone 14 Pro']
    last_updt_trig_by_mobapp_dname        = {}
    mobile_app_notify_devicename          = []
    battery_level_sensors_by_mobapp_dname = {}
    battery_state_sensors_by_mobapp_dname = {}

    devicenames_x_famshr_devices    = {}  # All ic3_devicenames by conf_famshr_devices (both ways)
    devicenames_x_mobapp_dnames     = {}  # All ic3_devicenames by conf_mobapp_dname (both ways)

    # Mobile App Integration info from hass_data['mobile_app'], Updated in start_ic3.check_mobile_app_integration
    MobileApp_data                  = {}  # data dict from hass.data['mobile_app']
    MobileApp_device_fnames         = []  # fname = name_by_user or name in mobile_app device entry
    MobileApp_fnames_x_mobapp_id    = {}  # All mobapp_fnames by mobapp_deviceid (both ways)
    MobileApp_fnames_disabled       = []

    Zones                           = []  # Zones object list
    Zones_by_zone                   = {}  # Zone object by zone name for HA Zones and iC3 Pseudo Zones
    HAZones                         = []  # Zones object list for only valid HA Zones
    HAZones_by_zone                 = {}  # Zone object by zone name for only valid HA Zones
    HAZones_by_zone_deleted         = {}  # Zone object by zone name for Zones deleted from HA
    ha_zone_settings_check_secs     = 0   # Last time the ha.states Zone config was checked for changes
    zones_dname                     = {}   # Zone display_as by zone distionary to ease displaying zone fname
    TrackedZones_by_zone            = {HOME, None}  # Tracked zones object by zone name set up with Devices.DeviceFmZones object
    StatZones                       = []  # Stationary Zone objects
    StatZones_to_delete             = []  # Stationary Zone  to delete after the devices that we're in it have  been updated
    StatZones_by_zone               = {}  # Stationary Zone objects by their id number (1-10 --> ic3_#_stationary)
    HomeZone                        = None # Home Zone object

    # HA device_tracker and sensor entity info
    DeviceTrackers_by_devicename    = {}  # HA device_tracker.[devicename] entity objects
    Sensors_by_devicename           = {}  # HA sensor.[devicename]_[sensor_name]_[from_zone] objects
    Sensors_by_devicename_from_zone = {}  # HA sensor.[devicename]_[sensor_name]_[from_zone] objects
    Sensor_EventLog                 = None    # Event Log sensor object
    ha_device_id_by_devicename      = {}  # HA device_registry device_id
    ha_area_id_by_devicename        = {}  # HA device_registry area_id
    sensors_added_by_devicename     = {}  # Updated when a sensor is added in sensor.added_to-hass
    sensors_removed_by_devicename   = {}  # Updated when a sensor is removed in sensor.after_removal_cleanup

    # Event Log operational fields
    evlog_card_directory            = ''
    evlog_card_program              = ''
    evlog_disable_refresh_flag      = False
    evlog_action_request            = ''
    evlog_version                   = ''  # EvLog version reported back from the EvLog via the event_log_version svc call

    # iCloud3 Alerts Sensor
    AlertsSensor                    = None   # icloud3_alerts Sensor
    alerts_sensor                   = 'none' # Alerts sensor State value (last alert encountered)
    alerts_sensor_attrs             = {}     # Alerts Attributes by alert type

    # System Wide variables control iCloud3 start/restart procedures
    ic3_timer_events_are_setup      = False     # Indicates the 5-sec polling loop is set up
    initial_icloud3_loading_flag    = True
    start_icloud3_inprocess_flag    = True
    restart_icloud3_request_flag    = False     # iC3 needs to be restarted
    restart_ha_flag                 = False     # HA needs to be restarted
    restart_requested_by            = ''        # Requested by 'service_handler', 'config_flow'
    any_device_was_updated_reason   = ''
    startup_stage_status_controls   = []        # A general list used by various modules for noting startup progress
    startup_lists                   = {}        # Log variable and dictionsry field/values to icloud3-0.log file

    get_ICLOUD_devices_retry_cnt    = 0         # Retry count to connect to iCloud and retrieve iCloud devices
    reinitialize_icloud_devices_flag= False     # Set when no devices are tracked and iC3 needs to automatically restart
    reinitialize_icloud_devices_cnt = 0

    # Debug and trace flags
    log_debug_flag               = True
    log_rawdata_flag                = False
    log_rawdata_flag_unfiltered     = False
    log_debug_flag_restart       = None
    log_rawdata_flag_restart        = None
    evlog_trk_monitors_flag      = False
    evlog_startup_log_flag       = False
    info_notification            = ''
    ha_notification              = {}
    trace_prefix                 = '_INIT_'
    trace_prefix_pyicloud        = ''
    trace_group                  = False
    trace_text_change_1          = ''
    trace_text_change_2          = ''
    debug_flag                   = False
    debug_integer                = 0

    # Startup variables
    startup_log_msgs          = ''
    startup_log_msgs_prefix   = ''
    mobapp_entities           = ''
    mobapp_notify_devicenames = ''
    started_secs              = 0

    # Configuration parameters that can be changed in config_ic3.yaml
    um                     = DEFAULT_GENERAL_CONF[CONF_UNIT_OF_MEASUREMENT]
    um_MI                  = True
    um_KM                  = False
    time_format_12_hour    = True
    time_format_24_hour    = not time_format_12_hour
    um_km_mi_factor        = .62137
    um_m_ft_factor         = 3.28084
    um_m_ft                = 'ft'
    um_kph_mph             = 'mph'
    um_time_strfmt         = '%I:%M:%S'
    um_time_strfmt_ampm    = '%I:%M:%S%P'
    um_date_time_strfmt    = '%Y-%m-%d %H:%M:%S'
    um_day_date_time_strfmt = '%a, %b %-d, %l:%M:%S %p'   #Tue, Feb 20, 3:23:45 AM

    # Time conversion variables used in global_utilities
    time_zone_offset_secs = 0
    time_zone_offset_str  = '+00:00'
    time_zone_offset_secs_PST = -8 * 60 * 60

    # timestamp_local_offset_secs = 0

    # Away time zone offset used for displaying a devices time tracking sensors in the local time zone
    away_time_zone_1_offset         = 0
    away_time_zone_1_devices        = ['none']
    away_time_zone_2_offset         = 0
    away_time_zone_2_devices        = ['none']

    # Configuration parameters
    config_parm                     = {}        # Config parms from HA config.yaml and config_ic3.yaml
    config_parm_initial_load        = {}        # Config parms from HA config.yaml used to reset eveerything on restart
    ha_config_yaml_icloud3_platform = {}        # Config parms from HA config.yaml used during initial conversion to config_flow

    conf_file_data          = {}
    conf_profile            = {}
    conf_data               = {}
    conf_tracking           = {}
    conf_devices            = []
    conf_apple_accounts     = []
    conf_general            = {}
    conf_sensors            = {}
    conf_devicenames        = []
    conf_icloud_dnames      = []
    conf_devices_idx_by_devicename = {}           # Index of  each device names preposition in the conf_devices parameter
    conf_icloud_device_cnt  = 0                   # Number of devices with iCloud tracking set up
    conf_fmf_device_cnt     = 0                   # Number of devices with FmF tracking set up
    conf_mobapp_device_cnt  = 0                   # Number of devices with Mobile App  tracking set up

    sensors_cnt                 = 0               # Number of sensors that will be creted (__init__.py)
    sensors_created_cnt         = 0               # Number of sensors that have been set up (incremented in sensor.py)
    device_trackers_cnt         = 0               # Number of device_trackers that will be creted (__init__.py)
    device_trackers_created_cnt = 0               # Number of device_trackers that have been set up (incremented in device_tracker.py)
    area_id_personal_device     = None

    # restore_state file
    restore_state_commit_time = 0               # Set a callback timmer to commit te changes to the restore_state file
    restore_state_commit_cnt  = 0               # Set a callback timmer to commit te changes to the restore_state file
    restore_state_file_data   = {}
    restore_state_profile     = {}
    restore_state_devices     = {}

    # This stores the type of configuration parameter change done in the config_flow module
    # It indicates the type of change and if a restart is required to load device or sensor changes.
    # Items in the set are 'tracking', 'devices', 'profile', 'sensors', 'general', 'restart'
    config_parms_update_control     = []

    distance_method_waze_flag       = True
    icloud_force_update_flag        = False
    max_interval_secs               = DEFAULT_GENERAL_CONF[CONF_MAX_INTERVAL] * 60
    offline_interval_secs           = DEFAULT_GENERAL_CONF[CONF_OFFLINE_INTERVAL] * 60
    exit_zone_interval_secs         = DEFAULT_GENERAL_CONF[CONF_EXIT_ZONE_INTERVAL] * 60
    mobapp_alive_interval_secs      = DEFAULT_GENERAL_CONF[CONF_MOBAPP_ALIVE_INTERVAL] * 3600
    old_location_threshold          = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_THRESHOLD] * 60
    old_location_adjustment         = DEFAULT_GENERAL_CONF[CONF_OLD_LOCATION_ADJUSTMENT] * 60
    passthru_zone_interval_secs     = DEFAULT_GENERAL_CONF[CONF_PASSTHRU_ZONE_TIME] * 60
    is_passthru_zone_used           = (14400 > passthru_zone_interval_secs > 0)  # time > 0 and < 4 hrs
    is_track_from_base_zone_used    = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE_USED]
    track_from_base_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_BASE_ZONE]
    track_from_home_zone            = DEFAULT_GENERAL_CONF[CONF_TRACK_FROM_HOME_ZONE]
    gps_accuracy_threshold          = DEFAULT_GENERAL_CONF[CONF_GPS_ACCURACY_THRESHOLD]
    travel_time_factor              = DEFAULT_GENERAL_CONF[CONF_TRAVEL_TIME_FACTOR]
    log_level                       = DEFAULT_GENERAL_CONF[CONF_LOG_LEVEL]
    log_level_devices               = DEFAULT_GENERAL_CONF[CONF_LOG_LEVEL_DEVICES]
    # password_srp_enabled            = DEFAULT_TRACKING_CONF[CONF_PASSWORD_SRP_ENABLED]

    device_tracker_state_source     = DEFAULT_GENERAL_CONF[CONF_DEVICE_TRACKER_STATE_SOURCE]
    display_gps_lat_long_flag       = DEFAULT_GENERAL_CONF[CONF_DISPLAY_GPS_LAT_LONG]
    center_in_zone_flag             = DEFAULT_GENERAL_CONF[CONF_CENTER_IN_ZONE]
    display_zone_format             = DEFAULT_GENERAL_CONF[CONF_DISPLAY_ZONE_FORMAT]
    # device_tracker_state_format     = DEFAULT_GENERAL_CONF[CONF_DEVICE_TRACKER_STATE_FORMAT]
    # if device_tracker_state_format == 'display_as': device_tracker_state_format = display_zone_format

    # device_tracker_state_evlog_format_flag = (device_tracker_state_format == FNAME)
    discard_poor_gps_inzone_flag    = DEFAULT_GENERAL_CONF[CONF_DISCARD_POOR_GPS_INZONE]
    distance_between_device_flag    = DEFAULT_GENERAL_CONF[CONF_DISTANCE_BETWEEN_DEVICES]

    tfz_tracking_max_distance       = DEFAULT_GENERAL_CONF[CONF_TFZ_TRACKING_MAX_DISTANCE]

    waze_region                     = DEFAULT_GENERAL_CONF[CONF_WAZE_REGION]
    waze_max_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MAX_DISTANCE]
    waze_min_distance               = DEFAULT_GENERAL_CONF[CONF_WAZE_MIN_DISTANCE]
    waze_realtime                   = DEFAULT_GENERAL_CONF[CONF_WAZE_REALTIME]
    waze_history_database_used      = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_DATABASE_USED]
    waze_history_max_distance       = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_MAX_DISTANCE]
    waze_history_track_direction    = DEFAULT_GENERAL_CONF[CONF_WAZE_HISTORY_TRACK_DIRECTION]

    statzone_fname                  = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_FNAME]
    statzone_base_latitude          = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_BASE_LATITUDE]
    statzone_base_longitude         = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_BASE_LONGITUDE]
    statzone_inzone_interval_secs   = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_INZONE_INTERVAL] * 60
    statzone_still_time_secs        = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_STILL_TIME] * 60
    is_statzone_used                = (14400 > statzone_still_time_secs > 0)   # time > 0 and < 4 hrs
    monitored_devices_location_sensors_flag = False

    # Initialize Stat Zone size based on Home zone size
    statzone_min_dist_from_zone_km = .05         # Changed from .2km v3.2.0, .05km=165ft
    statzone_dist_move_limit_km    = .125
    statzone_radius_m              = 100

    # Variables used to config the device variables when setting up
    # intervals and determining the tracking method
    inzone_interval_secs = {}

    # Data source control variables
    # Used to reset Gb.is_data_source after pyicloud/icloud account successful reset

    # Specifed in configuration file (set in config_flow icloud credentials screen)
    conf_data_source_ICLOUD   = False
    conf_data_source_MOBAPP   = False
    conf_data_source_ICLOUD   = False

    # A trackable device uses this data source (set in start_ic3.set trackable_devices)
    used_data_source_ICLOUD  = False
    used_data_source_MOBAPP  = False
    device_not_monitoring_mobapp = True             # At least one device does not monitor the mobapp
    device_mobapp_verify_retry_cnt = 0
    device_mobapp_verify_retry_needed = False   # A device that monitors the mobapp has not been verfied as
                                                    # being set up in tme mobapp integration (mobapp_data_handler)

    # Primary data source being used that can be turned off if errors
    use_data_source_ICLOUD     = False
    use_data_source_MOBAPP     = False
    primary_data_source        = None

    # iCloud account authorization variables
    force_icloud_update_flag     = False
    trusted_device               = None
    verification_code            = None
    icloud_cookie_directory      = ''
    icloud_session_directory     = ''
    icloud_cookie_file           = ''
    icloud_device_verified_cnt   = 0
    mobapp_device_verified_cnt   = 0
    authentication_alert_displayed_flag = False

    unverified_Devices           = []               # Devices that have not been verified in start_ic3.check_unverified_devices
    unverified_devices_cnt       = 0                #
    unverified_devices_retry_cnt = 0                # Decreased in icloud_data_handler. Retry verify until cnt=0

    # Waze History for DeviceFmZone
    wazehist_zone_id            = {}
    waze_status                 = WAZE_USED
    waze_manual_pause_flag      = False             # Paused using service call
    waze_close_to_zone_pause_flag = False           # Close to home pauses Waze
    wazehist_recalculate_time_dist_flag = False     # Set in config_flow > Actions to schedule a db rebuild at midnight

    # Variables to be moved to Device object when available
    # mobapp entity data
    last_mobapp_state                = {}
    last_mobapp_state_changed_time   = {}
    last_mobapp_state_changed_secs   = {}
    last_mobapp_trigger              = {}
    last_mobapp_trigger_changed_time = {}
    last_mobapp_trigger_changed_secs = {}
    mobapp_monitor_error_cnt         = {}

    # Device state, zone data from icloud and mobapp
    state_to_zone     = {}
    this_update_secs  = 0
    this_update_time  = ''
    state_this_poll   = {}
    state_last_poll   = {}
    zone_last         = {}
    zone_current      = {}
    zone_timestamp    = {}
    state_change_flag = {}

    # Device status and tracking fields
    devicename                     = ''             # Current devicename being updated
    config_track_devices_change_flag = True         # Set in config_handler when parms are loaded. Do Stave 1 only if no device changes
    device_tracker_entity_ic3      = {}
    trigger                        = {}
    got_exit_trigger_flag          = {}
    device_being_updated_flag      = {}
    device_being_updated_retry_cnt = {}
    mobapp_update_flag             = {}
    attr_tracking_msg              = '' # tracking msg on attributes
    all_tracking_paused_flag       = False
    all_tracking_paused_secs       = 0
    dist_to_other_devices_update_sensor_list = set()    # Contains a list of devicenames that need their distance sensors updated
                                                        # at the end of polling loop after all devices have been processed

    # Miscellenous variables
    broadcast_msg        = ''
    broadcast_info_msg   = None

    # Test variables
    test_true_1         = True
    test_true_2         = True
    test_false_1        = False
    test_false_2        = False
    test_str_1          = ''
    test_str_2          = ''
    test_list_1         = []
    test_list_2         = []
    test_dict_1         = {}
    test_dict_2         = {}

    #<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

    config_flow_flag = False
