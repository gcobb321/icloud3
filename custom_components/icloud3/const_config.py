
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           CONFIG_FLOW CONSTANTS - CONFIGURATION PARAMETERS IN
#                                       .storage/icloud.configuration FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from .const import (DOMAIN, VERSION, DATETIME_ZERO, HOME, ICLOUD, MOBAPP, NO_MOBAPP, TRACK, MONITOR,
                     IPHONE, IPAD, WATCH, AIRPODS, MAC, OTHER, NONE_FNAME, BATTERY_SOURCE,
                     DEVICE_TYPE_INZONE_INTERVALS, EVLOG_CARD_WWW_DIRECTORY, EVLOG_CARD_WWW_JS_PROG, )

# STORAGE_KEY = DOMAIN
# STORAGE_VERSION = 1

DISTANCE           = 'distance'
CONF_SENSORS_ZONE  = 'zone'
ZONE_INFO          = 'zone_info'
ZONE               = "zone"
ZONE_DNAME         = "zone_dname"
ZONE_FNAME         = "zone_fname"
ZONE_NAME          = "zone_name"
ZONE_DATETIME      = "zone_changed"
ZONE_ENTER_SECS    = "zone_enter_secs"
ZONE_EXIT_SECS     = "zone_exit_secs"
LAST_ZONE          = "last_zone"
LAST_ZONE_DNAME    = "last_zone_dname"
LAST_ZONE_FNAME    = "last_zone_fname"
LAST_ZONE_NAME     = "last_zone_name"
LAST_ZONE_DATETIME = "last_zone_changed"

CF_PROFILE         = 'profile'
CF_DATA            = 'data'
CF_TRACKING        = 'tracking'
CF_APPLE_ACCOUNTS  = 'apple_accounts'
CF_DEVICES         = 'devices'
CF_GENERAL         = 'general'
CF_SENSORS         = 'sensors'
CF_DEVICE_SENSORS  = 'device_sensors'

#--------------------------------------------------------------------
#       CONFIG_PROFILE
#--------------------------------------------------------------------
CONF_VERSION                    = 'version'
CONF_IC3_VERSION                = 'ic3_version'
CONF_VERSION_INSTALL_DATE       = 'version_install_date'
CONF_UPDATE_DATE                = 'config_update_date'
CONF_EVLOG_BTNCONFIG_URL        = 'event_log_btnconfig_url'
CONF_EVLOG_CARD_DIRECTORY       = 'event_log_card_directory'
CONF_EVLOG_CARD_PROGRAM         = 'event_log_card_program'
CONF_EVLOG_VERSION              = 'event_log_version'
CONF_EVLOG_VERSION_RUNNING      = 'event_log_version_running'
CONF_PICTURE_WWW_DIRS           = 'picture_www_dirs'
CONF_SENSORS_HASH               = 'sensors_hash'
CONF_FIRST_SEEN                 = 'first_seen'

CONF_EXTERNAL_IP_ADDRESS        = 'external_ip_address'

DEFAULT_PROFILE_CONF = {
        CONF_VERSION: 0,
        CONF_IC3_VERSION: VERSION,
        CONF_VERSION_INSTALL_DATE: DATETIME_ZERO,
        CONF_UPDATE_DATE: DATETIME_ZERO,
        CONF_FIRST_SEEN: '',
        CONF_EVLOG_VERSION: '',
        CONF_EVLOG_VERSION_RUNNING: '',
        CONF_EVLOG_CARD_DIRECTORY: EVLOG_CARD_WWW_DIRECTORY,
        CONF_EVLOG_CARD_PROGRAM: EVLOG_CARD_WWW_JS_PROG,
        CONF_EVLOG_BTNCONFIG_URL: '',
        CONF_PICTURE_WWW_DIRS: [],
        CONF_SENSORS_HASH: '',
}

#--------------------------------------------------------------------
#       CONF_TRACKING
#--------------------------------------------------------------------
CONF_ENCODE_PASSWORD            = 'encode_password'
CONF_SERVER_LOCATION_NEEDED     = 'apple_server_location_needed'
CONF_PASSWORD_SRP_ENABLED       = 'password_srp_enabled'
CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX = 'icloud_server_endpoint_suffix'
CONF_SETUP_ICLOUD_SESSION_EARLY = 'setup_icloud_session_early'
CONF_DATA_SOURCE                = 'data_source'
CONF_APPLE_ACCOUNTS             = 'apple_accounts'
CONF_DEVICES                    = 'devices'
CONF_DEVICENAME                 = 'device_name'

DEFAULT_TRACKING_CONF = {
        CONF_ENCODE_PASSWORD: True,
        CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX: '',
        CONF_SERVER_LOCATION_NEEDED: False,
        CONF_SETUP_ICLOUD_SESSION_EARLY: True,
        CONF_PASSWORD_SRP_ENABLED: True,
        CONF_DATA_SOURCE: f'{ICLOUD},{MOBAPP}',
        CONF_APPLE_ACCOUNTS: [],
        CONF_DEVICES: [],
}

#--------------------------------------------------------------------

#-------------------------------------------------------------------
#     CONF_APPLE_ACCTS
#--------------------------------------------------------------------
CONF_USERNAME           = 'username'
# CONF_APPLE_ID           = 'apple_id'
CONF_APPLE_ACCOUNT      = 'apple_account'
CONF_APPLE_ACCT         = 'apple_account'
CONF_PASSWORD           = 'password'
CONF_LOCATE_ALL         = 'locate_all'
CONF_SERVER_LOCATION    = 'server_location'

CONF_AUTH_METHODS       = 'auth_methods'
CURRENT                 = 'current'
PUSH                    = 'push'
TEXT                    = 'text'
TEXT_1                  = 'text_1'
TEXT_2                  = 'text_2'
HWKEY                   = 'hwkey'
AUTH_METHOD_FNAME       = {
        PUSH: 'Push',
        TEXT_1: 'Text-1',
        TEXT_2: 'Text-2',
        'text_3': 'Text-3',
        'text_4': 'Text-4',
        HWKEY: 'SecurityKey'
}

DEFAULT_AUTH_METHODS = {
        CURRENT: PUSH,
        TEXT_1: '',
        TEXT_2: '',
        HWKEY: '',
}

DEFAULT_APPLE_ACCOUNT_CONF = {
        CONF_USERNAME: '',
        CONF_APPLE_ACCOUNT: '',
        CONF_PASSWORD: '',
        CONF_AUTH_METHODS: DEFAULT_AUTH_METHODS,
        CONF_LOCATE_ALL: True,
        CONF_SERVER_LOCATION: 'usa',
}

#--------------------------------------------------------------------
#       CONF_DEVICES
#--------------------------------------------------------------------
# Devices Parameters
CONF_IC3_DEVICENAME             = 'ic3_devicename'
CONF_FNAME                      = 'fname'
CONF_AADEV_NAME                 = 'apple_device_name'
CONF_AADEV_DEVICE_ID            = 'apple_device_id'
CONF_FAMSHR_NAME                = 'famshr_devicename'
CONF_FAMSHR_DEVICE_ID           = 'famshr_device_id'
CONF_RAW_MODEL                  = 'raw_model'
CONF_MODEL                      = 'model'
CONF_MODEL_DISPLAY_NAME         = 'model_display_name'
CONF_FMF_EMAIL                  = 'fmf_email'
CONF_FMF_DEVICE_ID              = 'fmf_device_id'
CONF_IOSAPP_DEVICE              = 'iosapp_device'
CONF_MOBILE_APP_DEVICE          = 'mobile_app_device'
CONF_PICTURE                    = 'picture'
CONF_ICON                       = 'icon'
CONF_TRACKING_MODE              = 'tracking_mode'
CONF_TRACK_FROM_BASE_ZONE       = 'track_from_base_zone'        # Primary Zone a device is tracking from, normally Home
CONF_TRACK_FROM_ZONES           = 'track_from_zones'            # All zones the device is tracking from
CONF_LOG_ZONES                  = 'log_zones'                   # Log zone activity to 'icloud3-zone-log_[year]_[device]_[zone].csv' file
CONF_DEVICE_TYPE                = 'device_type'
CONF_INZONE_INTERVAL            = 'inzone_interval'
CONF_FIXED_INTERVAL             = 'fixed_interval'
CONF_UNIQUE_ID                  = 'unique_id'
CONF_EVLOG_DISPLAY_ORDER        = 'evlog_display_order'
# CONF_STAT_ZONE_FNAME            = 'stat_zone_fname'

CONF_ZONE                       = 'zone'
CONF_COMMAND                    = 'command'
CONF_NAME                       = 'name'
CONF_MOBAPP_REQUEST_LOC_MAX_CNT = 'mobapp_request_loc_max_cnt'
CONF_INTERVAL                   = 'interval'


DEFAULT_DEVICE_CONF = {
        CONF_IC3_DEVICENAME: ' ',
        CONF_FNAME: '',
        CONF_PICTURE: 'None',
        CONF_ICON: 'mdi:account',
        CONF_DEVICE_TYPE: 'iPhone',
        CONF_INZONE_INTERVAL: 120,
        CONF_FIXED_INTERVAL: 0,
        CONF_TRACKING_MODE: TRACK,
        CONF_APPLE_ACCOUNT: '',
        CONF_AADEV_NAME: 'None',
        CONF_AADEV_DEVICE_ID: '',
        CONF_FAMSHR_NAME: 'None',
        CONF_FAMSHR_DEVICE_ID: '',
        CONF_RAW_MODEL : '',
        CONF_MODEL: '',
        CONF_MODEL_DISPLAY_NAME: '',
        CONF_MOBILE_APP_DEVICE: 'None',
        CONF_TRACK_FROM_BASE_ZONE: HOME,
        CONF_TRACK_FROM_ZONES: [HOME],
        CONF_LOG_ZONES: ['none'],
}
# Used in conf_flow to reinialize the Configuration Devices
DEFAULT_DEVICE_APPLE_ACCT_DATA_SOURCE = {
        CONF_APPLE_ACCOUNT: '',
        CONF_AADEV_NAME: 'None',
        CONF_AADEV_DEVICE_ID: '',
        CONF_RAW_MODEL : '',
        CONF_MODEL: '',
        CONF_MODEL_DISPLAY_NAME: '',
}
DEFAULT_DEVICE_MOBAPP_DATA_SOURCE = {
        CONF_MOBILE_APP_DEVICE: 'None',
}
RANGE_DEVICE_CONF = {
        CONF_INZONE_INTERVAL: [5, 480],
        CONF_FIXED_INTERVAL: [0, 480],
}

#--------------------------------------------------------------------
#       CONFIG_GENERAL
#--------------------------------------------------------------------
CONF_UNIT_OF_MEASUREMENT        = 'unit_of_measurement'
CONF_TIME_FORMAT                = 'time_format'
CONF_MAX_INTERVAL               = 'max_interval'
CONF_OFFLINE_INTERVAL           = 'offline_interval'
CONF_EXIT_ZONE_INTERVAL         = 'exit_zone_interval'
CONF_MOBAPP_ALIVE_INTERVAL      = 'mobapp_alive_interval'
CONF_IOSAPP_ALIVE_INTERVAL      = 'iosapp_alive_interval'
CONF_GPS_ACCURACY_THRESHOLD     = 'gps_accuracy_threshold'
CONF_OLD_LOCATION_THRESHOLD     = 'old_location_threshold'
CONF_OLD_LOCATION_ADJUSTMENT    = 'old_location_adjustment'
CONF_TRAVEL_TIME_FACTOR         = 'travel_time_factor'
CONF_TFZ_TRACKING_MAX_DISTANCE  = 'tfz_tracking_max_distance'
CONF_PASSTHRU_ZONE_TIME         = 'passthru_zone_time'
CONF_LOG_LEVEL                  = 'log_level'
CONF_LOG_LEVEL_DEVICES          = 'log_level_devices'
CONF_DISPLAY_GPS_LAT_LONG       = 'display_gps_lat_long'

# Zone Parameters
CONF_DEVICE_TRACKER_STATE_SOURCE= 'device_tracker_state_source'
CONF_DISPLAY_ZONE_FORMAT        = 'display_zone_format'
CONF_CENTER_IN_ZONE             = 'center_in_zone'
CONF_DISCARD_POOR_GPS_INZONE    = 'discard_poor_gps_inzone'
CONF_DISTANCE_BETWEEN_DEVICES   = 'distance_between_devices'
CONF_INZONE_INTERVALS           = 'inzone_intervals'

# Waze Parameters
CONF_DISTANCE_METHOD            = 'distance_method'
CONF_WAZE_USED                  = 'waze_used'
CONF_WAZE_REGION                = 'waze_region'
CONF_WAZE_SERVER                = 'waze_region'
CONF_WAZE_MAX_DISTANCE          = 'waze_max_distance'
CONF_WAZE_MIN_DISTANCE          = 'waze_min_distance'
CONF_WAZE_REALTIME              = 'waze_realtime'
CONF_WAZE_HISTORY_DATABASE_USED = 'waze_history_database_used'
CONF_WAZE_HISTORY_MAX_DISTANCE  = 'waze_history_max_distance'
CONF_WAZE_HISTORY_TRACK_DIRECTION= 'waze_history_track_direction'

# Stationary Zone Parameters
CONF_STAT_ZONE_FNAME            = 'stat_zone_fname'
CONF_STAT_ZONE_STILL_TIME       = 'stat_zone_still_time'
CONF_STAT_ZONE_INZONE_INTERVAL  = 'stat_zone_inzone_interval'
CONF_STAT_ZONE_BASE_LATITUDE    = 'stat_zone_base_latitude'
CONF_STAT_ZONE_BASE_LONGITUDE   = 'stat_zone_base_longitude'

CONF_TRACK_FROM_BASE_ZONE_USED  = 'track_from_base_zone_used'   # Primary Zone a device is tracking from, normally Home
CONF_TRACK_FROM_HOME_ZONE       = 'track_from_home_zone'

# Local Time Zone
CONF_AWAY_TIME_ZONE_1_OFFSET    = 'away_time_zone_1_offset'
CONF_AWAY_TIME_ZONE_1_DEVICES   = 'away_time_zone_1_devices'
CONF_AWAY_TIME_ZONE_2_OFFSET    = 'away_time_zone_2_offset'
CONF_AWAY_TIME_ZONE_2_DEVICES   = 'away_time_zone_2_devices'

# Display Text As Parameter
CONF_DISPLAY_TEXT_AS            = 'display_text_as'

# Analytics
CONF_ANALYTICS_ENABLED          = 'analytics_enabled'
CONF_ANALYTICS_SENT_DATE        = 'analytics_sent_date'
CONF_ANALYTICS_COMMENT          = 'analytics_comment'

DEFAULT_GENERAL_CONF = {
        CONF_LOG_LEVEL: 'debug-auto-reset',
        CONF_LOG_LEVEL_DEVICES: ['all'],

        # General Configuration Parameters
        CONF_UNIT_OF_MEASUREMENT: 'mi',
        CONF_TIME_FORMAT: '12-hour',
        CONF_DISPLAY_ZONE_FORMAT: 'fname',
        CONF_DEVICE_TRACKER_STATE_SOURCE: 'ic3_fname',
        CONF_MAX_INTERVAL: 240,
        CONF_OFFLINE_INTERVAL: 20,
        CONF_EXIT_ZONE_INTERVAL: 3,
        CONF_MOBAPP_ALIVE_INTERVAL: 60,
        CONF_OLD_LOCATION_THRESHOLD: 3,
        CONF_OLD_LOCATION_ADJUSTMENT: 0,
        CONF_GPS_ACCURACY_THRESHOLD: 100,
        CONF_DISPLAY_GPS_LAT_LONG: True,
        CONF_TRAVEL_TIME_FACTOR: .5,
        CONF_TFZ_TRACKING_MAX_DISTANCE: 8,
        CONF_PASSTHRU_ZONE_TIME: .5,
        CONF_TRACK_FROM_BASE_ZONE_USED: True,
        CONF_TRACK_FROM_BASE_ZONE: HOME,
        CONF_TRACK_FROM_HOME_ZONE: True,

        # inZone Configuration Parameters
        CONF_CENTER_IN_ZONE: False,
        CONF_DISCARD_POOR_GPS_INZONE: False,
        CONF_DISTANCE_BETWEEN_DEVICES: True,
        CONF_INZONE_INTERVALS: DEVICE_TYPE_INZONE_INTERVALS.copy(),

        # Waze Configuration Parameters
        CONF_WAZE_USED: True,
        CONF_WAZE_REGION: 'us',
        CONF_WAZE_MIN_DISTANCE: 1,
        CONF_WAZE_MAX_DISTANCE: 1000,
        CONF_WAZE_REALTIME: False,
        CONF_WAZE_HISTORY_DATABASE_USED: True,
        CONF_WAZE_HISTORY_MAX_DISTANCE: 20,
        CONF_WAZE_HISTORY_TRACK_DIRECTION: 'north_south',

        # Stationary Zone Configuration Parameters
        CONF_STAT_ZONE_FNAME: 'StatZon#',
        CONF_STAT_ZONE_STILL_TIME: 8,
        CONF_STAT_ZONE_INZONE_INTERVAL: 30,
        CONF_STAT_ZONE_BASE_LATITUDE: 1,
        CONF_STAT_ZONE_BASE_LONGITUDE: 0,

        # Analytics
        CONF_ANALYTICS_ENABLED: None,
        CONF_ANALYTICS_SENT_DATE: '',
        CONF_ANALYTICS_COMMENT: '',

        # DisplayText_as and AwayTimeZone lists
        CONF_DISPLAY_TEXT_AS: ['#1', '#2', '#3', '#4', '#5', '#6', '#7', '#8', '#9', '#10'],

        CONF_AWAY_TIME_ZONE_1_OFFSET: 0,
        CONF_AWAY_TIME_ZONE_1_DEVICES: ['none'],
        CONF_AWAY_TIME_ZONE_2_OFFSET: 0,
        CONF_AWAY_TIME_ZONE_2_DEVICES: ['none'],

}

RANGE_GENERAL_CONF = {
        # General Configuration Parameters
        CONF_GPS_ACCURACY_THRESHOLD: [5, 250, 5, 'm'],
        CONF_OLD_LOCATION_THRESHOLD: [1, 60],
        CONF_OLD_LOCATION_ADJUSTMENT: [0, 60],
        CONF_MAX_INTERVAL: [15, 480],
        CONF_EXIT_ZONE_INTERVAL: [.5, 10, .5],
        CONF_MOBAPP_ALIVE_INTERVAL: [15, 480],
        CONF_OFFLINE_INTERVAL: [5, 480],
        CONF_TFZ_TRACKING_MAX_DISTANCE: [1, 100, 1, 'km'],
        CONF_TRAVEL_TIME_FACTOR: [.1, 1, .1, ''],
        CONF_PASSTHRU_ZONE_TIME: [0, 5],

        # Waze Configuration Parameters
        CONF_WAZE_MIN_DISTANCE: [0, 20, 1, 'km'],
        CONF_WAZE_MAX_DISTANCE: [0, 1000, 5, 'km'],
        CONF_WAZE_HISTORY_MAX_DISTANCE: [0, 1000, 5, 'km'],

        # Stationary Zone Configuration Parameters
        CONF_STAT_ZONE_STILL_TIME: [0, 60],
        CONF_STAT_ZONE_INZONE_INTERVAL: [5, 60],
        CONF_STAT_ZONE_BASE_LATITUDE:  [-90, 90, 1, ''],
        CONF_STAT_ZONE_BASE_LONGITUDE: [-180, 180, 1, ''],
}

#--------------------------------------------------------------------
#       CONF_SENSORS
#--------------------------------------------------------------------
CONF_SENSORS_MONITORED_DEVICES = 'monitored_devices'

CONF_SENSORS = SENSORS         = 'sensors'
CONF_SENSORS_DEVICE            = 'device'
NAME                           = "name"
BADGE                          = "badge"
BATTERY                        = "battery"
BATTERY_STATUS                 = "battery_status"
INFO                           = "info"

CONF_SENSORS_TRACKING_UPDATE   = 'tracking_update'
INTERVAL                       = "interval"
INTERVAL_METHOD                = "interval_method"
LOCATED                        = "located"
LAST_LOCATED                   = "last_located"
LAST_UPDATE                    = "last_update"
NEXT_UPDATE                    = "next_update"

CONF_SENSORS_TRACKING_TIME     = 'tracking_time'
TRAVEL_TIME                    = "travel_time"
TRAVEL_TIME_MIN                = "travel_time_min"
TRAVEL_TIME_HHMM               = "travel_time_hhmm"
ARRIVAL_TIME                   = "arrival_time"


CONF_SENSORS_TRACKING_DISTANCE = 'tracking_distance'
ZONE_DISTANCE_M                = 'distance (meters)'
ZONE_DISTANCE_M_EDGE           = 'distance_to_zone_edge (meters)'
ZONE_DISTANCE                  = "zone_distance"
HOME_DISTANCE                  = "home_distance"
DISTANCE_HOME                  = "distance_home"
DIR_OF_TRAVEL                  = "dir_of_travel"
MOVED_DISTANCE                 = "moved_distance"
MOVED_TIME_FROM                = 'moved_from'
MOVED_TIME_TO                  = 'moved_to'

# TfZ Sensors are not configured via config_flow but built in
# config_flow from the distance, time & zone sensors
CONF_SENSORS_TRACK_FROM_ZONES = 'track_from_zones'
TFZ_ZONE_INFO                 = 'tfz_zone_info'
TFZ_DISTANCE                  = 'tfz_distance'
TFZ_ZONE_DISTANCE             = 'tfz_zone_distance'
TFZ_TRAVEL_TIME               = 'tfz_travel_time'
TFZ_TRAVEL_TIME_MIN           = 'tfz_travel_time_min'
TFZ_TRAVEL_TIME_HHMM          = "tfz_travel_time_hhmm"
TFZ_ARRIVAL_TIME              = "tfz_arrival_time"
TFZ_DIR_OF_TRAVEL             = 'tfz_dir_of_travel'

CONF_SENSORS_TRACKING_OTHER   = 'tracking_other'
TRIGGER                       = "trigger"
WAZE_DISTANCE_ATTR            = "waze_route_distance"
CALC_DISTANCE_ATTR            = "calculated_distance"
WAZE_DISTANCE                 = "waze_distance"
CALC_DISTANCE                 = "calc_distance"

CONF_SENSORS_OTHER            = 'other'
GPS_ACCURACY                  = "gps_accuracy"
ALTITUDE                      = "altitude"
VERTICAL_ACCURACY             = "vertical_accuracy"

CONF_EXCLUDED_SENSORS         = "excluded_sensors"

# Default Create Sensor Field Parameter
DEFAULT_SENSORS_CONF = {
        CONF_SENSORS_MONITORED_DEVICES: [
                'md_badge',
                'md_battery', ],
        CONF_SENSORS_DEVICE: [
                NAME,
                BADGE,
                BATTERY,
                INFO, ],
        CONF_SENSORS_TRACKING_UPDATE: [
                INTERVAL,
                LAST_LOCATED,
                LAST_UPDATE,
                NEXT_UPDATE, ],
        CONF_SENSORS_TRACKING_TIME: [
                TRAVEL_TIME,
                TRAVEL_TIME_MIN,
                ARRIVAL_TIME, ],
        CONF_SENSORS_TRACKING_DISTANCE: [
                HOME_DISTANCE,
                ZONE_DISTANCE,
                MOVED_DISTANCE,
                DIR_OF_TRAVEL, ],
        CONF_SENSORS_TRACK_FROM_ZONES: [
                TFZ_ZONE_INFO,
                TFZ_TRAVEL_TIME,
                TFZ_TRAVEL_TIME_MIN,
                TFZ_ARRIVAL_TIME,
                TFZ_ZONE_DISTANCE,
                TFZ_DIR_OF_TRAVEL,],
        CONF_SENSORS_TRACKING_OTHER: [],
        CONF_SENSORS_ZONE: [
                ZONE_NAME],
        CONF_SENSORS_OTHER: [],
        CONF_EXCLUDED_SENSORS: [
                NONE_FNAME],
}
DEFAULT_DEVICE_SENSORS_CONF = {
        TRACK: [],
        MONITOR: [],
        CONF_TRACK_FROM_ZONES: [],
        CONF_EXCLUDED_SENSORS: []
}

CF_DEFAULT_IC3_CONF_FILE = {
        CF_PROFILE: DEFAULT_PROFILE_CONF,
        CF_DATA: {
                CF_TRACKING: DEFAULT_TRACKING_CONF,
                CF_GENERAL: DEFAULT_GENERAL_CONF,
                CF_SENSORS: DEFAULT_SENSORS_CONF,
                CF_DEVICE_SENSORS: DEFAULT_DEVICE_SENSORS_CONF,
        }
}

#--------------------------------------------------------------------
CONF_PARAMETER_TIME_STR = [
        CONF_INZONE_INTERVAL,
        CONF_FIXED_INTERVAL,
        CONF_MAX_INTERVAL,
        CONF_OFFLINE_INTERVAL,
        CONF_EXIT_ZONE_INTERVAL,
        CONF_MOBAPP_ALIVE_INTERVAL,
        CONF_PASSTHRU_ZONE_TIME,
        CONF_STAT_ZONE_STILL_TIME,
        CONF_STAT_ZONE_INZONE_INTERVAL,
        CONF_OLD_LOCATION_THRESHOLD,
        CONF_OLD_LOCATION_ADJUSTMENT,
        IPHONE,
        IPAD,
        MAC,
        WATCH,
        AIRPODS,
        NO_MOBAPP,
        OTHER,
]

CONF_PARAMETER_FLOAT = [
        CONF_TRAVEL_TIME_FACTOR,
        CONF_STAT_ZONE_BASE_LATITUDE,
        CONF_STAT_ZONE_BASE_LONGITUDE,
]

CONF_ALL_FAMSHR_DEVICES = "all_find_devices"
DEFAULT_ALL_FAMSHR_DEVICES = True

# .storage/icloud3.restore_state file used to resore the device_trackers
# and sensors state during start up
RESTORE_STATE_FILE = {
        CF_PROFILE : {
                CONF_VERSION: 0,
                LAST_UPDATE: DATETIME_ZERO, },
        CF_DEVICES: {},
}

# Initialize the Device sensors[xxx] value from the restore_state file if
# the sensor is in the file. Otherwise, initialize to this value
USE_RESTORE_STATE_VALUE_ON_STARTUP = {
        BATTERY: 0,
        BATTERY_STATUS: '',
        BATTERY_SOURCE: '',
}
