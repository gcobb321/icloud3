#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Define the iCloud3 General Constants
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#       Contributors:
#       @DuncanIdahoCT - iCloud Display Message Alert service call
#                        This service will send a message to the selected device
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
VERSION                         = '3.8.0'
VERSION_BETA                    = '2'
#-----------------------------------------
DOMAIN                          = 'icloud3'
PLATFORMS                       = ['sensor', 'device_tracker', 'button', 'text']
PLATFORM_DEVICE_TRACKER         = 'device_tracker'
PLATFORM_SENSOR                 = 'sensor'
PLATFORM_BUTTON                 = 'button'      # User auth code Request Auth Code entities
PLATFORM_TEXT                   = 'text'        # User auth code Enter Auth Code entities

#-----------------------------------------

ICLOUD3                         = 'iCloud3'
ICLOUD3LC                       = 'icloud3'
STORAGE_KEY                     = DOMAIN
STORAGE_VERSION                 = 1
MODE_PLATFORM                   = -1
MODE_INTEGRATION                = 1
DEBUG_TRACE_CONTROL_FLAG        = False

HA_ENTITY_REGISTRY_FILE_NAME    = 'config/.storage/core.entity_registry'
ENTITY_REGISTRY_FILE_KEY        = 'core.entity_registry'
DEFAULT_CONFIG_IC3_FILE_NAME    = 'config/config_ic3.yaml'

STORAGE_DIR                     = ".storage"
STORAGE_KEY_ENTITY_REGISTRY     = 'core.entity_registry'
SENSOR_EVENT_LOG_NAME           = f'{DOMAIN}_event_log'
EVLOG_CARD_WWW_DIRECTORY        = f'www/{DOMAIN}'
EVLOG_CARD_WWW_JS_PROG          = 'icloud3-event-log-card.js'
EVLOG_BTNCONFIG_DEFAULT_URL     = f'/config/integrations/integration/{DOMAIN}'
HA_CONFIG_IC3_URL               = f'/config/integrations/integration/{DOMAIN}'
WAZE_LOCATION_HISTORY_DATABASE  = 'icloud3.waze_location_history.db'
SENSOR_WAZEHIST_TRACK_NAME      = 'icloud3_wazehist_track'
IC3LOG_FILENAME                 = f'{DOMAIN}.log'
PICTURE_WWW_STANDARD_DIRS       = 'www/icloud3, www/community, www/images, www/custom_cards'

DEVICE_TRACKER                  = PLATFORM_DEVICE_TRACKER
DEVICE_TRACKER_DOT              = 'device_tracker.'
SENSOR                          = PLATFORM_SENSOR
ATTRIBUTES                      = 'attributes'
ENTITY_ID                       = 'entity_id'
HA_DEVICE_TRACKER_LEGACY_MODE   = False
MOBILE_APP                      = 'mobile_app_'
NOTIFY                          = 'notify'
DISTANCE_TO_DEVICES             = 'distance_to'
DISTANCE_TO_OTHER_DEVICES       = 'distance_to_other_devices'
DISTANCE_TO_OTHER_DEVICES_DATETIME = 'distance_to_other_devices_datetime'
TRUST_COOKIE_NAME               = 'X-APPLE-WEBAUTH-HSA-TRUST'


# General constants
BASE                            = 'base'
TRACKED                         = 'tracked'
MONITORED                       = 'monitored'
EXCLUDED                        = 'excluded'
HOME                            = 'home'
HOME_FNAME                      = 'Home'
NOT_HOME                        = 'not_home'
NOT_HOME_FNAME                  = 'NotHome'
AWAY                            = 'Away'
NEAR_HOME                       = 'NearHome'
NOT_SET                         = 'not_set'
NOT_SET_FNAME                   = 'NotSet'
UNKNOWN                         = 'Unknown'
STATIONARY                      = 'stationary'
STATIONARY_FNAME                = 'Stationary'
NOT_HOME_ZONES                  = [NOT_HOME, AWAY, NOT_SET]

AWAY_FROM                       = 'AwayFrom'
AWAY_FROM_HOME                  = 'AwayFromHome'
NEAR                            = 'Near'
TOWARDS                         = 'Towards'
TOWARDS_HOME                    = 'TowardsHome'
FAR_AWAY                        = 'FarAway'
INZONE                          = 'inZone'
INZONE_HOME                     = 'inHomeZone'
INZONE_STATZONE                 = 'inStatZone'
INZONE_CODES                    = {INZONE: 'Z', INZONE_HOME: 'H', INZONE_STATZONE: 'S'}
STATZONE                        = 'StatZone'
PAUSED                          = 'PAUSED'
PAUSED_CAPS                     = 'PAUSED'
RESUMING                        = 'RESUMING'
RESUMING_CAPS                   = 'RESUMING'
NEVER                           = 'Never'
ERROR                           = 0
NONE                            = 'none'
NONE_FNAME                      = 'None'
SEARCH                          = 'search'
SEARCH_FNAME                    = 'Search'
VALID_DATA                      = 1
UTC_TIME                        = True
LOCAL_TIME                      = False
NUMERIC                         = True
WAZE                            = 'waze'
CALC                            = 'calc'
DIST                            = 'dist'

# Tracking Method
ICLOUD                          = 'iCloud'    #iCloud Location Services
FAMSHR                          = 'iCloud'    #Family Sharing
MOBAPP                          = 'MobApp'    #HA Mobile App v1.5x or v2.x
NO_MOBAPP                       = 'no_mobapp'
IOSAPP                          = 'iosapp'
NO_IOSAPP                       = 'no_iosapp'

# Apple Device Types
IPHONE_DN                       = 'iPhone'
WATCH_DN                        = 'Watch'
WATCH_DN_WIFI_CELL              = 'Watch-WiFi+Cell'
WATCH_DN_WIFI                   = 'Watch-WiFi'
IPAD_DN                         = 'iPad'
IPAD_DN_WIFI                    = 'iPad-WiFi'
IPAD_DN_WIFI_CELL               = 'iPad-WiFi+Cell'
MAC_DN                          = 'Mac'
IPOD_DN                         = 'iPod'
AIRPODS_DN                      = 'AirPods'
OTHER_DN                        = 'Other'

IPHONE                          = 'iphone'
WATCH                           = 'watch'
APPLE_WATCH                     = 'apple watch'
WATCH_WIFI                      = 'watch_wifi'
IPAD                            = 'ipad'
IPAD_CELL                       = 'ipad_cell'
MAC                             = 'mac'
IPOD                            = 'ipod'
AIRPODS                         = 'airpods'
OTHER                           = 'other'

# Device tracking modes
TRACK               = 'track'
MONITOR             = 'monitor'
INACTIVE            = 'inactive'
TRACKING_MODES      = [TRACK, MONITOR, INACTIVE]
TRACKING_MODE_DN    = {TRACK: 'Tracked', MONITOR: 'Monitored', INACTIVE: 'INACTIVE',}

DEVICE_TYPES = [
        IPHONE, IPAD, IPAD_CELL, WATCH, WATCH_WIFI,
        IPHONE_DN, IPAD_DN, IPAD_DN_WIFI, IPAD_DN_WIFI_CELL,
        WATCH_DN, WATCH_DN_WIFI_CELL, WATCH_DN_WIFI, APPLE_WATCH,
        MAC, IPOD, AIRPODS,
        MAC_DN, IPOD_DN, AIRPODS_DN,
        ICLOUD,
]
DEVICE_TYPES_TRACK_MONITOR = [
        IPHONE, IPAD, IPAD_CELL, WATCH, WATCH_WIFI, MAC,
]
DEVICE_TYPE_DEFAULT_TRACKING_MODE = {
        IPHONE: TRACK,
        WATCH: TRACK,
        IPAD: MONITOR,
        MAC: MONITOR,
}
def DEVICE_TYPE_TRACKING_MODE(device_type):
        device_type_base = device_type.split('_')[0]
        return DEVICE_TYPE_DEFAULT_TRACKING_MODE.get(device_type_base, INACTIVE)

DEVICE_TYPE_DNS = {
        IPHONE: IPHONE_DN,
        WATCH: WATCH_DN_WIFI_CELL,
        WATCH_WIFI: WATCH_DN_WIFI,
        IPAD: IPAD_DN_WIFI,
        IPAD_CELL: IPAD_DN_WIFI_CELL,
        AIRPODS: AIRPODS_DN,
        MAC: MAC_DN,
        IPOD: IPOD_DN,
        OTHER: OTHER_DN,
}
DEVICE_TYPES_CELL_SVC = {
        IPHONE, WATCH, IPAD_CELL,
}
def DEVICE_TYPE_DN(device_type):
        return DEVICE_TYPE_DNS.get(device_type, device_type)

DEVICE_TYPE_PICTURE_FILENAMES = {
        IPHONE: "iphone.png",
        IPAD: "ipad-landscape.png",
        IPAD_CELL: "ipad-landscape.png",
        WATCH: "watch-light.png",
        WATCH_WIFI: "watch-light.png",
        AIRPODS: "airpods.png",
        MAC : "",
        IPOD: "",
        OTHER: ""
}

DEVICE_TYPE_ICONS = {
        IPHONE: "mdi:cellphone",
        IPAD: "mdi:tablet",
        IPAD_CELL: "mdi:tablet",
        WATCH: "mdi:watch-variant",
        WATCH_WIFI: "mdi:watch-variant",
        AIRPODS: "mdi:earbuds-outline",
        MAC : "mdi:laptop",
        IPOD: "mdi:ipod",
        OTHER: 'mdi:laptop'
}

DEVICE_TYPE_INZONE_INTERVALS = {
        IPHONE: 120,
        IPAD: 120,
        IPAD_CELL: 120,
        WATCH: 15,
        WATCH_WIFI: 15,
        MAC: 120,
        AIRPODS: 120,
        NO_MOBAPP: 15,
        OTHER: 120,
}
DEVICE_DISPLAY_NAMES_FILTERS = {
        'generation': 'gen',
        'nd gen': '',
        'th gen': '',
        'Series ': 'S',
        'Pro Max': 'ProMax',
        'Apple ': '',
        'mini': 'Mini',
        '(': '',
        ')': '',
}

# Apple is using a country specific iCloud server based on the country code in pyicloud_ic3.
# Add to the HOME_ENDPOINT & SETUP_ENDPOINT urls if the HA country code is one of these values.
ICLOUD_SERVER_COUNTRY_CODE = ['cn', 'CN']
APPLE_SERVER_ENDPOINT = {
        'home':     'https://www.icloud.com',
        'setup':    'https://setup.icloud.com/setup/ws/1',
        'auth':     'https://idmsa.apple.com/appleauth/auth',
        'auth_url': 'https://setup.icloud.com/setup/authenticate'
}
APPLE_SERVER_ENDPOINT_IPv4 = {
        'idmsa':    'https://idmsa.apple.com',
        'appleid':  'https://appleid.apple.com',
        'auth':     'https://auth.apple.com'
}

INTERNET_STATUS_PING_IPS = {
        'Google/P': '8.8.8.8',
        'Google/S': '8.8.4.4',
        'CloudFlare/P': '1.1.1.1',
        'CloudFlare/S': '1.0.0.1',
        'OpenDNS/P': '208.67.222.222',
        'OpenDNS/S': '208.67.220.220',
        'ChinaAlibaba/P1': '116.251.64.1',
        'ChinaAlibaba/P2': '43.33.76.1',
        'ChinaAlibaba/S': '65.22.132.9',
        'ChinaOpen114/S': '114.114.115.115',
}

UM_FNAME        = {'mi': 'Miles', 'km': 'Kilometers'}
DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
DATETIME_ZERO   = '0000-00-00 00:00:00'
HHMMSS_ZERO     = '00:00:00'
HHMM_ZERO       = '00:00'
HIGH_INTEGER    = 9999999999

# iCloud3 Alerts Sensor (icloud3_alerts)
SENSOR_ALERTS_NAME = f'{DOMAIN}_alerts'
ALERT_CRITICAL   = 'critical'
ALERT_APPLE_ACCT = 'apple_acct'
ALERT_DEVICE     = 'device'
ALERT_STARTUP    = 'startup'
ALERT_OTHER      = 'other'
# alerts_by_alert_key = {}

# Device Tracking Status
TRACKING_NORMAL  = 0
TRACKING_PAUSED  = 1
TRACKING_RESUMED = 2

# Config Parameter Range Index (used in RANGE_DEVICE_CONF, RANGE_GENERAL_CONF lists)
MIN      = 0
MAX      = 1
STEP     = 2
RANGE_UM = 3

#Other constants
MOBAPP_DT_ENTITY = True
ICLOUD_DT_ENTITY = False
ICLOUD_LOCATION_DATA_ERROR   = False
TRUST_TOKEN_EXPIRE_WARNING_DAYS = 88    #   Start warning user trust cookie will expire in x days
CMD_RESET_PYICLOUD_SESSION   = 'reset_session'
NEAR_DEVICE_DISTANCE         = 25       # Distance between nearby devices  (det_interval)
PASS_THRU_ZONE_INTERVAL_SECS = 60       # Delay time before moving into a non-tracked zone to see if if just passing thru
STATZONE_RADIUS_1M           = 1
ICLOUD3_ERROR_MSG            = "ICLOUD3 ERROR-SEE EVENT LOG"

# A tracked device that is offline this long can be replaced by a newer device
# with the same Apple default name
REPLACED_DEVICE_OFFLINE_SECS = 3600

# A tracked device that is not in the Apple acct's device list this long was removed
# (wiped, removed from the Apple acct, Find My turned off). It is checked every
# 15-mins (4 refreshes) before iCloud3 is restarted to reassign or report it.
MISSING_DEVICE_RESTART_IN_SECS          = 3600
MISSING_DEVICE_INTERVAL_SECS = 900

# Event Log variables
EVENT_RECDS_MAX_CNT_BASE = 1500         # Used to calculate the max recds to store
EVENT_RECDS_MAX_CNT_ZONE = 2000         # Used to calculate the max recds to store
EVENT_LOG_CLEAR_SECS     = 900          # Clear event log data interval
EVENT_LOG_CLEAR_CNT      = 50           # Number of recds to display when clearing event log

EVLOG_URL_LIST           =     {'urlConfig': '',
                                'urlBuyMeACoffee': '',
                                'urlIssues': '',
                                'urlHelp': ''}

#Devicename config parameter file extraction
DI_DEVICENAME           = 0
DI_DEVICE_TYPE          = 1
DI_NAME                 = 2
DI_EMAIL                = 3
DI_BADGE_PICTURE        = 4
DI_MOBAPP_ENTITY        = 5
DI_MOBAPP_SUFFIX        = 6
DI_ZONES                = 7

# Waze status codes
# WAZE_REGIONS      = ['US', 'NA', 'EU', 'IL', 'AU']
WAZE_SERVERS_BY_COUNTRY_CODE = {'us': 'us', 'ca': 'us', 'il': 'il', 'row': 'row'}
WAZE_SERVERS_FNAME =           {'us': 'United States, Canada',
                                'US': 'United States, Canada',
                                'il': 'Israel',
                                'IL': 'Israel',
                                'row': 'Rest of the World',
                                'ROW': 'Rest of the World'}
WAZE_USED         = 0
WAZE_NOT_USED     = 1
WAZE_PAUSED       = 2
WAZE_OUT_OF_RANGE = 3
WAZE_NO_DATA      = 4

# Interval range table used for setting the interval based on a retry count
# The key is starting retry count range, the value is the interval (in minutes)
# poor_location_gps cnt, icloud_authentication cnt (default)
OLD_LOCATION_CNT       = 1.1
AUTH_ERROR_CNT         = 1.2
# RETRY_INTERVAL_RANGE_1 = 15s*4=1m, 4*1m=4m=5m, 4*5m=20m=25m, 4*30m=2h=2.5h, 4*1h=4h=6.5h

# RETRY_INTERVAL_RANGE_1 = 30s*4=2m, 4*1.5m=6m=8m, 4*15m=1h=1h8m, 4*30m=2h=3h8m, 4*1h=4h=6.5h
# RETRY_INTERVAL_RANGE_1 = {0:.25, 4:1, 8:5, 12:30, 16:60, 20:60}
# RETRY_INTERVAL_RANGE_1 = 15s*5=1.25m, 5*1m=5m=6m, 5*5m=25m=30m, 5*30m=2.5h=3, 4*1h=4h=6h25h
RETRY_INTERVAL_RANGE_1 = {0:.25, 4:.5, 8:1, 12:5, 16:15, 20:30, 24:60}
MOBAPP_REQUEST_LOC_CNT = 2.1
RETRY_INTERVAL_RANGE_2 = {0:.5, 4:2, 8:30, 12:60, 16:60}
# RETRY_INTERVAL_RANGE_2 = {0:.5, 4:2, 8:30, 12:60, 14:120, 16:180, 18:240, 20:240}

# Used by the 'update_method' in the polling_5_sec loop
MOBAPP_UPDATE     = "MOBAPP"
ICLOUD_UPDATE     = "ICLOUD"

# The event_log lovelace card will display the event in a special color if
# the text starts with a special character:
# ^1^ - LightSeaGreen
# ^2^ - BlueViolet
# ^3^ - OrangeRed
# ^4^ - DeepPink
# ^5^ - MediumVioletRed
# ^6^ - --dark-primary-color
# EVLOG_GREEN, EVLOG_VIOLET, EVLOG_ORANGE, EVLOG_PINK, EVLOG_RED, EVLOG_BLUE
EVLOG_GREEN       = '^1^'
EVLOG_VIOLET      = '^2^'
EVLOG_ORANGE      = '^3^'
EVLOG_PINK        = '^4^'
EVLOG_RED         = '^5^'
EVLOG_BLUE        = '^6^'       # DO NOT USE - EventLog uses ^6^

EVLOG_UPDATE_HDR  = '^u^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_START= '^s^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_END  = '^c^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_BARS = [EVLOG_UPDATE_HDR, EVLOG_UPDATE_START, EVLOG_UPDATE_END]
EVLOG_ERROR       = '^e^'
EVLOG_ALERT       = '^a^'       # Red letters on yellow background
EVLOG_WARNING     = '^w^'
EVLOG_ATTENTION   = '^i^'       # White Letters on orchid bar
EVLOG_HIGHLIGHT   = '^h^'       # Green highlight bar
EVLOG_IC3_STAGE_HDR = '^g^'

EVLOG_NOTICE      = '^6^'
EVLOG_TRACE       = '^3^'
EVLOG_DEBUG       = '^6^'
EVLOG_MONITOR     = '^m^'

# Device error code EvLog text
ERR_UNKNOWN         = " ⛔ UNKNOWN"
ERR_UNKNOWN_AA      = " ⛔ UNKNOWN APPLE ACCT"
ERR_UNKNOWN_MOBAPP  = " ⛔ UNKNOWN MOBAPP"
ERR_ICLOUD_DISABLED = " 🔸 ICLOUD DISABLED"
ERR_USERNAME_PW     = " ⛔ INVALID USERNAME/PW"
ERR_INACTIVE        = " 🔸 INACTIVE"
ERR_DISABLED_HA     = " 🔸 DISABLED IN HA"
ERR_NOT_AVAIL       = " 🔸 NOT AVAILABLE"
ERR_NOT_IN_AA       = " ⛔ NOT IN APPLE ACCT"
ERR_NOT_IN_MOBAPP   = " ⛔ NOT IN MOBAPP"
ERR_NOT_USED        = " ⛔ NOT USED"
ERR_OFFLINE         = " ⛔ OFFLINE"
ERR_NOT_DATA_SOURCE = " 🔸 NOT USED AS A DATA SOURCE"
ERR_NOT_CONFIG      = " ⛔ NOT CONFIGURED"
ERR_UNKNOWN,
# ERR_UNKNOWN_AA, ERR_UNKNOWN_MOBAPP, ERR_UNKNOWN, ERR_INACTIVE
# ERR_DISABLED_HA, ERR_ICLOUD_DISABLED, ERR_NOT_AVAIL,
# ERR_NOT_IN_AA, ERR_NOT_IN_MOBAPP,
# ERR_NOT_USED, ERR_OFFLINE, ERR_NOT_DATA_SOURCE, ERR_NOT_CONFIG,


# SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
SETTINGS_INTEGRATIONS_MSG   = '`Settings > Devices & Services > Integrations`'
INTEGRATIONS_IC3_CONFIG_MSG = '`iCloud3 > Configuration`'

# Greenbar message items
from .const_char import (CRLF, NBSP, )
GB_ALERT          = f'{CRLF}⚙️{NBSP}'
GB_ITEM           = f'{CRLF}💠{NBSP}'
OPT_NONE          = 0

# Zone field names
NAME              = 'name'
FNAME             = 'fname'
FNAME_HOME        = 'fname/Home'
TITLE             = 'title'
RADIUS            = 'radius'
NON_ZONE_ITEM_LIST = {
        'not_home': 'Away',
        'Not_Home': 'Away',
        'not_set': 'NotSet',   #'──',
        'Not_Set': 'NotSet',   #'──',
        '──': 'NotSet',
        'NotSet': 'NotSet',   #'──',
        STATIONARY: STATIONARY_FNAME,
        STATIONARY_FNAME: STATIONARY_FNAME,
        'unknown': 'Unknown'}

#Convert state non-fname value to internal zone/state value
from homeassistant.const import (STATE_HOME, STATE_NOT_HOME, )
STATE_TO_ZONE_BASE = {
        'NotSet': 'not_set',
        'Away': STATE_NOT_HOME,
        "away": STATE_NOT_HOME,
        'NotHome': STATE_NOT_HOME,
        "nothome": STATE_NOT_HOME,
        'not_home': STATE_NOT_HOME,
        'home': STATE_HOME,
        'Home': STATE_HOME,
        STATIONARY: STATIONARY_FNAME,
        STATIONARY_FNAME: STATIONARY_FNAME,
        }

# Standardize the battery status text between the Mobile App and icloud icloud
BATTERY_LEVEL_LOW     = 20
BATTERY_CHARGING      = 'battery_charging'
BATTERY_CHARGING_DESC = ['Unknown', 'Low', 'NotCharging', 'Charging', 'Charged']
CHARGING_UNKNOWN      = 0
CHARGING_LOW          = 1
CHARGING_NOTCHARGING  = 2
CHARGING_CHARGING     = 3
CHARGING_CHARGED      = 4
BATTERY_STATUS_CODES  = {
        'full': 'not charging',
        'charged': 'not charging',
        'charging': 'charging',
        'notcharging': 'not charging',
        'not charging': 'not charging',
        'not_charging': 'not charging',
        'unknown': '',
        }
BATTERY_STATUS_FNAME = {
        # 'full, full': 'Full, Not Charging',
        'full, charging': 'Full, Charging',
        'full, not charging': 'Full, Not Charging',
        # 'charged': 'Full',
        # 'full': 'Full',
        'charging': 'Charging',
        'not charging': 'Not Charging',
        'unknown': 'Charging Unknown',
        }

# Device Tracker State Source
DEVICE_TRACKER_STATE_SOURCE_DESC = {
        'ic3_fname': 'iCloud3 Zone Friendly Name',
        'ic3_evlog': 'iCloud3 EvLog Zone Display Name',
        'ha_gps':    'HA GPS Coordinates'
        }

#Mobile App Triggers defined in /iOS/Shared/Location/LocatioTrigger.swift
BACKGROUND_FETCH          = 'Background Fetch'
BKGND_FETCH               = 'Bkgnd Fetch'
GEOGRAPHIC_REGION_ENTERED = 'Geographic Region Entered'
GEOGRAPHIC_REGION_EXITED  = 'Geographic Region Exited'
IBEACON_REGION_ENTERED    = 'iBeacon Region Entered'
IBEACON_REGION_EXITED     = 'iBeacon Region Exited'
REGION_ENTERED            = 'Region Entered'
REGION_EXITED             = 'Region Exited'
ENTER_ZONE                = 'Enter Zone'
EXIT_ZONE                 = 'Exit Zone'
INITIAL                   = 'Initial'
MANUAL                    = 'Manual'
LAUNCH                    = "Launch",
PERIODIC                  = "Periodic"
SIGNIFICANT_LOC_CHANGE    = 'Significant Location Change'
SIGNIFICANT_LOC_UPDATE    = 'Significant Location Update'
SIG_LOC_CHANGE            = 'Sig Loc Change'
PUSH_NOTIFICATION         = 'Push Notification'
REQUEST_MOBAPP_LOC        = 'Request MobApp Loc'
MOBAPP_LOC_CHANGE         = 'MobApp Loc Change'
SIGNALED                  = 'Signaled'

#Trigger is converted to abbreviation after getting last_update_trigger
MOBAPP_TRIGGER_ABBREVIATIONS = {
        GEOGRAPHIC_REGION_ENTERED: ENTER_ZONE,
        GEOGRAPHIC_REGION_EXITED: EXIT_ZONE,
        IBEACON_REGION_ENTERED: ENTER_ZONE,
        IBEACON_REGION_EXITED: EXIT_ZONE,
        SIGNIFICANT_LOC_CHANGE: SIG_LOC_CHANGE,
        SIGNIFICANT_LOC_UPDATE: SIG_LOC_CHANGE,
        PUSH_NOTIFICATION: REQUEST_MOBAPP_LOC,
        BACKGROUND_FETCH: BKGND_FETCH,
        }
MOBAPP_TRIGGERS_VERIFY_LOCATION = [
        INITIAL,
        LAUNCH,
        SIGNALED,
        MANUAL,
        MOBAPP_LOC_CHANGE,
        BKGND_FETCH,
        SIG_LOC_CHANGE,
        REQUEST_MOBAPP_LOC,
        ]
MOBAPP_TRIGGERS_ENTER      = [ENTER_ZONE, ]
MOBAPP_TRIGGERS_EXIT       = [EXIT_ZONE, ]
MOBAPP_TRIGGERS_ENTER_EXIT = [ENTER_ZONE, EXIT_ZONE, ]

#Lists to hold the group names, group objects and iCloud device configuration
#The ICLOUD3_GROUPS is filled in on each platform load, the GROUP_OBJS is
#filled in after the polling timer is setup.
ICLOUD3_GROUPS     = []
ICLOUD3_GROUP_OBJS = {}
ICLOUD3_TRACKED_DEVICES = {}

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#       OTHER WORKING VARIABLES
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

# v2 to v3 migration items
CONF_ENTITY_REGISTRY_FILE  = 'entity_registry_file_name'
CONFIG_IC3                 = 'config_ic3'
CONF_CREATE_SENSORS        = 'create_sensors'
CONF_EXCLUDE_SENSORS       = 'exclude_sensors'
CONF_CONFIG_IC3_FILE_NAME  = 'config_ic3_file_name'

# entity attributes (iCloud FmF & iCloud)
ICLOUD_TIMESTAMP           = 'timeStamp'
ICLOUD_HORIZONTAL_ACCURACY = 'horizontalAccuracy'
ICLOUD_VERTICAL_ACCURACY   = 'verticalAccuracy'
ICLOUD_POSITION_TYPE       = 'positionType'
ICLOUD_BATTERY_STATUS      = 'batteryStatus'
ICLOUD_BATTERY_LEVEL       = 'batteryLevel'
ICLOUD_DEVICE_CLASS        = 'deviceClass'
ICLOUD_DEVICE_STATUS       = 'deviceStatus'
ICLOUD_LOW_POWER_MODE      = 'lowPowerMode'
ICLOUD_LOST_MODE_CAPABLE   = 'lostModeCapable'
ID                         = 'id'
LAST_CHANGED_SECS          = 'last_changed_secs'
LAST_CHANGED_TIME          = 'last_changed_time'
LAST_UPDATED_SECS          = 'last_updated_secs'
LAST_UPDATED_TIME          = 'last_updated_time'
STATE                      = 'state'

# device tracker attributes
LOCATION                   = 'location'
ATTRIBUTES                 = 'attributes'
RADIUS                     = 'radius'
NAME                       = 'name'
FRIENDLY_NAME              = 'friendly_name'
LATITUDE                   = 'latitude'
LONGITUDE                  = 'longitude'
POSITION_TYPE              = 'position_type'
DEVICE_CLASS               = 'device_class'
DEVICE_ID                  = 'device_id'
PASSIVE                    = 'passive'

# entity attributes
DEVICE_TRACKER_STATE       = 'device_tracker_state'
LOCATION_SOURCE            = 'location_source'
NEAR_DEVICE_USED           = 'nearby_device_used'
INTO_ZONE_DATETIME         = 'into_zone'
FROM_ZONE                  = 'from_zone'
TIMESTAMP                  = 'timestamp'
TIMESTAMP_SECS             = 'timestamp_secs'
TIMESTAMP_TIME             = 'timestamp_time'
LOCATION_TIME              = 'location_time'
DATA_SOURCE                = 'data_source'
DATETIME                   = 'date_time'
AGE                        = 'age'
BATTERY_SOURCE             = 'battery_data_source'
BATTERY_LEVEL              = 'battery_level'
BATTERY_UPDATE_TIME        = 'battery_level_updated'
BATTERY_ICLOUD             = 'icloud_battery_info'
BATTERY_MOBAPP             = 'mobapp_battery_info'
BATTERY_LATEST             = 'battery_info'
WAZE_METHOD                = 'waze_method'
MAX_DISTANCE               = 'max_distance'
WENT_3KM                   = 'went_3km'

DEVICE_STATUS              = 'device_status'
LOW_POWER_MODE             = 'low_power_mode'
TRACKING                   = 'tracking'
DEVICENAME_MOBAPP          = 'mobapp_device'
AUTHENTICATED              = 'authenticated'
ALERT                      = 'alert'
AUTH_CODE                  = 'auth_code'

LAST_UPDATE_TIME           = 'last_update_time'
LAST_UPDATE_DATETIME       = 'last_updated_date/time'
NEXT_UPDATE_TIME           = 'next_update_time'
NEXT_UPDATE_DATETIME       = 'next_update_date/time'
LAST_LOCATED_SECS          = 'last_located_secs'
LAST_LOCATED_TIME          = 'last_located_time'
LAST_LOCATED_DATETIME      = 'last_located_date/time'

GPS                        = 'gps'
POLL_COUNT                 = 'poll_count'
ICLOUD3_VERSION            = 'icloud3_version'
VERT_ACCURACY              = 'vertical_accuracy'
EVENT_LOG                  = 'event_log'
PICTURE                    = 'entity_picture'
ICON                       = 'icon'
RAW_MODEL                  = 'raw_model'
MODEL                      = 'model'
MODEL_DISPLAY_NAME         = 'model_display_name'
RAW_MODEL2                 = 'raw_model2'
MODEL2                     = 'model2'
MODEL_DISPLAY_NAME2        = 'model_display_name2'

DEVICE_STATUS_SET = [
        ICLOUD_DEVICE_CLASS,
        ICLOUD_BATTERY_STATUS,
        ICLOUD_LOW_POWER_MODE,
        LOCATION
        ]
DEVICE_STATUS_CODES = {
        200:   'Online',
        201:   'Offline',
        203:   'Pending',
        204:   'Unregistered',
        0:     'Unknown',
        '200': 'Online',
        '201': 'Offline',
        '203': 'Pending',
        '204': 'Unregistered',
        '0': 'Unknown',
        }

DEVICE_STATUS_ONLINE  = [200, 203, 204, 0]
DEVICE_STATUS_OFFLINE = 201
DEVICE_STATUS_PENDING = 203

ICLOUD3_EVENT_LOG    = 'icloud3_event_log'
DEVTRKR_ONLY_MONITOR = 'devtrkr_only_monitored_devices'

#