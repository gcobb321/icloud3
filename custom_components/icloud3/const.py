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

# from homeassistant.const import (Platform)

VERSION                         = '3.3.4'
VERSION_BETA                    = ''
#-----------------------------------------
DOMAIN                          = 'icloud3'
PLATFORMS                       = ['sensor', 'device_tracker']
PLATFORM_DEVICE_TRACKER         = 'device_tracker'
PLATFORM_SENSOR                 = 'sensor'

#-----------------------------------------

ICLOUD3                         = 'iCloud3'
ICLOUD3_VERSION_MSG             = f"{ICLOUD3} v{VERSION}{VERSION_BETA}"
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

# General constants
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
IPHONE_FNAME                    = 'iPhone'
WATCH_FNAME                     = 'Watch-WiFi+Cell'
WATCH_WIFI_FNAME                = 'Watch-WiFi'
IPAD_FNAME                      = 'iPad-WiFi'
IPAD_CELL_FNAME                 = 'iPad-WiFi+Cell'
MAC_FNAME                       = 'Mac'
IPOD_FNAME                      = 'iPod'
AIRPODS_FNAME                   = 'AirPods'
OTHER_FNAME                     = 'Other'

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

DEVICE_TYPES = [
        IPHONE, IPAD, IPAD_CELL, WATCH, WATCH_WIFI,
        IPHONE_FNAME, IPAD_FNAME, IPAD_CELL_FNAME,
        WATCH_FNAME, WATCH_WIFI_FNAME, APPLE_WATCH,
        MAC, IPOD, AIRPODS,
        MAC_FNAME, IPOD_FNAME, AIRPODS_FNAME,
        ICLOUD,
]
DEVICE_TYPE_FNAMES = {
        IPHONE: IPHONE_FNAME,
        WATCH: WATCH_FNAME,
        APPLE_WATCH: WATCH_FNAME,
        WATCH_WIFI: WATCH_WIFI_FNAME,
        IPAD: IPAD_FNAME,
        IPAD_CELL: IPAD_CELL_FNAME,
        AIRPODS: AIRPODS_FNAME,
        MAC: MAC_FNAME,
        IPOD: IPOD_FNAME,
        OTHER: OTHER_FNAME,
}
DEVICE_TYPES_CELL_SVC = {
        IPHONE, WATCH, IPAD_CELL,
}
def DEVICE_TYPE_FNAME(device_type):
        return DEVICE_TYPE_FNAMES.get(device_type, device_type)

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
        AIRPODS: 15,
        NO_MOBAPP: 15,
        OTHER: 120,
}
DEVICE_DISPLAY_NAMES_FILTERS = {
        'generation': 'gen',
        'nd gen': '',
        'th gen': '',
        'Series ': '',
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
ALERTS_SENSOR_ATTRS = {}

'''
data_template:
  title: iCloud3 Alert Summary
  message: "{{ state_attr('sensor.icloud3_alerts', 'apple_account') }}"
   message: >-
iCloud3 Error: {{ states('sensor.icloud3_alerts') }}
{% if is_state_attr("sensor.icloud3_alerts", "apple_account", "") %}{% else %}
 • AppleAcct: {{ state_attr('sensor.icloud3_alerts', 'apple_account') }},  {% endif -%}
{% if is_state_attr("sensor.icloud3_alerts", "device", "") %}{% else %}
 • Device: {{ state_attr('sensor.icloud3_alerts', 'device') }},  {% endif -%}
{% if is_state_attr("sensor.icloud3_alerts", "startup", "") %}{% else %}
 • StartUp: {{ state_attr('sensor.icloud3_alerts', 'startup') }},  {% endif -%}
{% if is_state_attr("sensor.icloud3_alerts", "critical", "") %}{% else %}
 • Critical: {{ state_attr('sensor.icloud3_alerts', 'critical') }},  {% endif -%}
---
Distance: {{ states('sensor.gary_iphone_zone_distance') }}
'''

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
CMD_RESET_PYICLOUD_SESSION   = 'reset_session'
NEAR_DEVICE_DISTANCE         = 25       # Distance between nearby devices  (det_interval)
PASS_THRU_ZONE_INTERVAL_SECS = 60       # Delay time before moving into a non-tracked zone to see if if just passing thru
STATZONE_RADIUS_1M       = 1
ICLOUD3_ERROR_MSG        = "ICLOUD3 ERROR-SEE EVENT LOG"

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
RETRY_INTERVAL_RANGE_1 = {0:.25, 5:1, 10:5, 15:15, 20:30, 25:60}
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

EVLOG_TIME_RECD   = '^t^'       # MobileApp State, ic3 Zone, interval, travel time, distance event
EVLOG_UPDATE_HDR  = '^u^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_START= '^s^'       # update start-to-complete highlight and edge bar block
EVLOG_UPDATE_END  = '^c^'       # update start-to-complete highlight and edge bar block
EVLOG_ERROR       = '^e^'
EVLOG_ALERT       = '^a^'
EVLOG_WARNING     = '^w^'
EVLOG_INIT_HDR    = '^i^'       # iC3 initialization start/complete event
EVLOG_HIGHLIGHT   = '^h^'       # Display item in green highlight bar
EVLOG_IC3_STARTING  = '^i^'
EVLOG_IC3_STAGE_HDR = '^g^'
EVLOG_BROWN_BAR     = '^i^'


EVLOG_NOTICE      = '^6^'
EVLOG_TRACE       = '^3^'
EVLOG_DEBUG       = '^6^'
EVLOG_MONITOR     = '^m^'

# SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
SETTINGS_INTEGRATIONS_MSG   = '`Settings > Devices & Services > Integrations`'
INTEGRATIONS_IC3_CONFIG_MSG = '`iCloud3 > Configuration`'

CIRCLE_LETTERS_DARK =  {'a':'🅐', 'b':'🅑', 'c':'🅒', 'd':'🅓', 'e':'🅔', 'f':'🅕', 'g':'🅖',
                        'h':'🅗', 'i':'🅘', 'j':'🅙', 'k':'🅚', 'l':'🅛', 'm':'🅜', 'n':'🅝',
                        'q':'🅞', 'p':'🅟', 'q':'🅠', 'r':'🅡', 's':'🅢', 't':'🅣', 'u':'🅤',
                        'v':'🅥', 'w':'🅦', 'x':'🅧', 'y':'🅨', 'z':'🅩', 'other': '✪'}
CIRCLE_LETTERS_LITE =  {'a':'Ⓐ', 'b':'Ⓑ', 'c':'Ⓒ', 'd':'Ⓓ', 'e':'Ⓔ', 'f':'Ⓕ', 'g':'Ⓖ',
                        'h':'Ⓗ', 'i':'Ⓘ', 'j':'Ⓙ', 'k':'Ⓚ', 'l':'Ⓛ', 'm':'Ⓜ', 'n':'Ⓝ',
                        'q':'Ⓞ', 'p':'Ⓟ', 'q':'Ⓠ', 'r':'Ⓡ', 's':'Ⓢ', 't':'Ⓣ', 'u':'Ⓤ',
                        'v':'Ⓥ', 'w':'Ⓦ', 'x':'Ⓧ', 'y':'Ⓨ', 'z':'Ⓩ', 'other': '✪'}
'''
lite_circled_letters = "Ⓐ Ⓑ Ⓒ Ⓓ Ⓔ Ⓕ Ⓖ Ⓗ Ⓘ Ⓙ Ⓚ Ⓛ Ⓜ Ⓝ Ⓞ Ⓟ Ⓠ Ⓡ Ⓢ Ⓣ Ⓤ Ⓥ Ⓦ Ⓧ Ⓨ Ⓩ"
dark_circled_letters = "🅐 🅑 🅒 🅓 🅔 🅕 🅖 🅗 🅘 🅙 🅚 🅛 🅜 🅝 🅞 🅟 🅠 🅡 🅢 🅣 🅤 🅥 🅦 🅧 🅨 🅩 ✪"
Symbols = ±▪•●▬⮾ ⊗ ⊘✓×ø¦ ▶◀ ►◄▲▼ ∙▪ »« oPhone=►▶→⟾➤➟➜➔➤🡆🡪🡺⟹🡆➔ᐅ◈🝱☒☢⦻⛒⊘Ɵ⊗ⓧⓍ⛒z🜔
Important =✔️❗❌✨➰⚠️☢❓⚽⛔🛑⚡⭐◌\⭕🔶🔸ⓘ• ⍰ ‶″“”‘’‶″ 🕓 🔻🔺✔☁️🍎🔻⮽➕⚙️
🔵🔴🟠🟡🟢🟣🟤🟦🟥🟧🟨🟩🟪🟫🔶🔷🔸🔹🔺🔻
✅❎☑️⏭️⏮️🍏🅰️
↺↻⟲⟳⭯⭮↺↻⥀⥁↶↷⮌⮍⮎⮏⤻⤸⤾⤿⤺⤼⤽⤹🗘⮔⤶⤷⃕⟳↻🔄🔁➡️🔃⬇️🔗
●•✶✹✽♦✱✥❄✪⬥⨳✫✡  ﹡✱*⨯⧫♦⚙⚹⚙️✳🞺🞴🞸🞳
═ ⎯ — –ᗒ ⁃ » ━▶ ━➤🡺 —> > ❯↦ 🡪ᗕᗒ ᐳ ─🡢 ⎯ ━ ──ᗒ 🡢 ─ᐅ ↣ ➙ →《》◆aak◈◉● ⟷
•⟛⚯⧟⫗' '᚛᚜ 〉〈 ⦒⦑  ⟩⟨ ⓧ≻≺ ⸩⸨
▐‖  ▹▻◁─▷◅◃‖╠ᐅ🡆▶▐🡆▐▶‖➤▐➤➜➔❰❰❱❱ ⠤ … ² ⚯⟗⟐⥄⥵⧴⧕⫘⧉⯏≷≶≳≲≪≫⋘⋙ ∮∯ ❪❫❴❵❮❯❰❱
.…⋯⋮ ⋱⋰ ⠁⠂⠐⠄⠠⠈⣇⠈⠉⠋⠛⠟⠿⡿⣿ ⠗⠺ ⠿  ⸩⸨⯎⟡⯌✦⯌⯏⯍aak✧ 🙾 🙿 (ⲶⲼ+≈⟣⟢aak.
🀫█ (▊Ⲷ (▉Ⲷ ▆ (■ ▦ ◼ ▉ (🀫Ⲷ▩▤
≽≼≽ ⋞⋟≺≻ ≪≫≾≿⋘⋙ ⋖⋗
https://www.fileformat.info/info/unicode/block/braille_patterns/utf8test.htm
https://www.htmlsymbols.xyz/unit-symbols
'''
NBSP              = '⠈' #'&nbsp;'
NBSP2             = '⠉' #'&nbsp;&nbsp;'
NBSP3             = '⠋' #'&nbsp;&nbsp;&nbsp;'
NBSP4             = '⠛' #'&nbsp;&nbsp;&nbsp;&nbsp;'
NBSP5             = '⠟' #'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
NBSP6             = '⠿' #'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'
CRLF              = '⣇' #'<br>'
NL                = '\n'
NLSP4             = '\n⠂   '
NL3               = '\n⠂ '
NL4               = '\n⠂  '
NL3U              = '\n⠂ 🔺 '
NL3D              = '\n⠂ 🔻 '
NL3_DATA          = '\n⠂  ❗ '
NL4_DATA          = '\n⠂   ❗ '
BSP4              = '⠀⠀⠀⠀'  # Braille spaces
LLINK             = ''
RLINK             = ''
LINK              = '⟢'
CLOCK_FACE        = '🕓'
INFO              = '🛈'
CHECK_MARK        = '✓ '
RED_X             = '❌'
YELLOW_ALERT      = '❎ '      #'⚠️'
RED_ALERT         = '⛔ '
RED_STOP          = '🛑'
RED_CIRCLE        = '⭕'
SMALL_X           = '⊗ '
CIRCLE_STAR       = '✪ '
CIRCLE_STAR2      = '✪'
CIRCLE_BIG_X      = '⊗'
CIRCLE_SLASH      = '⊘'
CIRCLE_X          = '⊗'
DOT               = '• '
PDOT              = '•'
SQUARE_DOT        = '▪'
HDOT              = '◦ '
PHDOT             = '◦'
LT                = '&lt;'
GT                = '&gt;'
LTE               = '≤'
GTE               = '≥'
DOTS              = '…'
PLUS_MINUS        = '±'

CRLF_DOT          = f'{CRLF}{NBSP2}•{NBSP2}'
CRLF_HDOT         = f'{CRLF}{NBSP6}◦{NBSP2}'
CRLF_HDOT2        = f'{CRLF}{NBSP2}◦{NBSP2}'
NL_DOT            = f'{NL} • '
CRLF_X            = f'{CRLF}{NBSP2}×{NBSP}'
CRLF_XD           = f'{CRLF}{NBSP}×{NBSP2}'
CRLF_CIRCLE_X     = f'{CRLF}{NBSP2}⊗{NBSP}'

LDOT2             = f'•{NBSP2}'
CRLF_LDOT         = f'{CRLF}•{NBSP}'
CRLF_LHDOT        = f'{CRLF}◦{NBSP}'
CRLF_LBDOT        = f'{CRLF}●{NBSP2}'
CRLF_LASTERISK    = f'{CRLF}🞳{NBSP}'
CRLF_LCIRCLE_X    = f'{CRLF}⊗{NBSP}'
CRLF_LX           = f'{CRLF}×{NBSP}'
CRLF_LCHK         = f'{CRLF}✓{NBSP}'
CRLF_LDIAMOND     = f'{CRLF}✦{NBSP}'

CRLF_RED_X        = f'{CRLF}❌{NBSP}'
CRLF_RED_ALERT    = f'{CRLF}⛔{NBSP2}'
CRLF_LRED_ALERT    = f'{CRLF}⛔{NBSP}'
CRLF_CHK          = f'{CRLF}{NBSP2}✓{NBSP}'
CRLF_STAR         = f'{CRLF}{NBSP}✪{NBSP}'
CRLF_YELLOW_ALERT = f'{CRLF}⚠️{NBSP}'
CRLF_RED_MARK     = f'{CRLF}{NBSP}❗{NBSP}'
CRLF_RED_STOP     = f'{CRLF}{NBSP}{RED_STOP}'
CRLF_RED_ALERT    = f'{CRLF}{NBSP}{RED_ALERT}'

CRLF_SP3_DOT      = f'{CRLF}{NBSP3}•{NBSP}'
CRLF_SP5_DOT      = f'{CRLF}{NBSP5}•{NBSP}'
CRLF_SP8_DOT      = f'{CRLF}{NBSP4}{NBSP4}•{NBSP}'
CRLF_SP8_HDOT     = f'{CRLF}{NBSP4}{NBSP4}◦{NBSP}'
CRLF_SP3_HDOT     = f'{CRLF}{NBSP3}◦{NBSP2}'
CRLF_SP3_STAR     = f'{CRLF}{NBSP3}✪{NBSP}'
CRLF_TAB          = f'{CRLF}{NBSP4}{NBSP4}{NBSP4}'
CRLF_INDENT       = f'{CRLF}{NBSP6}{NBSP6}'
CRLF_DASH_75      = f'{CRLF}{"-"*75}'

NEAR_DEVICE_USEABLE_SYM = '✓'
BLANK_SENSOR_FIELD = '———'
RARROW            = ' → '       #U+27F6 (Long Arrow Right)  ⟹ ⟾
RARROW2           = '→'         #U+27F6 (Long Arrow Right)  ⟹ ⟾
LARROW            = ' <-- '     #U+27F5 (Long Arrow Left) ⟸ ⟽
LARROW2           = '<--'       #U+27F5 (Long Arrow Left) ⟸ ⟽
INFO_SEPARATOR    = '/' #'∻'
DASH_20           = '—'*20
DASH_50           = '—'*50
DASH_DOTTED_50    = '- '*25
TAB_11            = '\t'*11
DATA_ENTRY_ALERT_CHAR = '⛔'
DATA_ENTRY_ALERT      = f"      {DATA_ENTRY_ALERT_CHAR} "

OPT_NONE          = 0

# Device tracking modes
TRACK_DEVICE      = 'track'
MONITOR_DEVICE    = 'monitor'
INACTIVE_DEVICE   = 'inactive'
TRACKING_MODE_FNAME = {
        TRACK_DEVICE: 'Tracked',
        MONITOR_DEVICE: 'Monitored',
        INACTIVE_DEVICE: 'INACTIVE',
}

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

# TRK_METHOD_SHORT_NAME = {
#         ICLOUD: ICLOUD,
#         MOBAPP: MOBAPP, }

# Standardize the battery status text between the Mobile App and icloud icloud
BATTERY_STATUS_CODES = {
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
TRACKING_METHOD            = 'data_source'
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
        '200': 'Online',
        '201': 'Offline',
        '203': 'Pending',
        '204': 'Unregistered',
        '0': 'Unknown',
        }
BATTERY_LEVEL_LOW     = 20
DEVICE_STATUS_ONLINE  = [200, 203, 204, 0]
DEVICE_STATUS_OFFLINE = 201
DEVICE_STATUS_PENDING = 203
# DEVICE_STATUS_ONLINE  = ['Online', 'Pending', 'Unknown', 'unknown', '']
# DEVICE_STATUS_OFFLINE = ['Offline']
# DEVICE_STATUS_PENDING = ['Pending']
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>

ICLOUD3_EVENT_LOG    = 'icloud3_event_log'
DEVTRKR_ONLY_MONITOR = 'devtrkr_only_monitored_devices'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           CONFIG_FLOW CONSTANTS - CONFIGURATION PARAMETERS IN
#                                       .storage/icloud.configuration FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

# Platform
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
CONF_EXTERNAL_IP_ADDRESS        = 'external_ip_address'

# Account, Devices, Tracking Parameters
CONF_USERNAME                   = 'username'
CONF_PASSWORD                   = 'password'
CONF_TOTP_KEY                   = 'totp_key'
CONF_LOCATE_ALL                 = 'locate_all'
CONF_APPLE_ACCOUNTS             = 'apple_accounts'
CONF_DEVICES                    = 'devices'
CONF_DATA_SOURCE                = 'data_source'
CONF_VERIFICATION_CODE          = 'verification_code'
CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX = 'icloud_server_endpoint_suffix'
CONF_SERVER_LOCATION            = 'server_location'
CONF_SERVER_LOCATION_NEEDED     = 'apple_server_location_needed'
CONF_ENCODE_PASSWORD            = 'encode_password'
CONF_SETUP_ICLOUD_SESSION_EARLY = 'setup_icloud_session_early'
CONF_DEVICENAME                 = 'device_name'

#devices_schema parameters used for v2->v3 migration
# CONF_IOSAPP_SUFFIX              = 'iosapp_suffix'
# CONF_IOSAPP_ENTITY              = 'iosapp_entity'
# CONF_NOIOSAPP                   = 'noiosapp'
# CONF_NO_IOSAPP                  = 'no_iosapp'
# CONF_IOSAPP_INSTALLED           = 'iosapp_installed'
# CONF_EMAIL                      = 'email'
# CONF_CONFIG                     = 'config'
# CONF_SOURCE                     = 'source'

# General Parameters
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
CONF_PASSWORD_SRP_ENABLED       = 'password_srp_enabled'

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

# Display Text As Parameter
CONF_DISPLAY_TEXT_AS            = 'display_text_as'

# Devices Parameters
CONF_IC3_DEVICENAME             = 'ic3_devicename'
CONF_FNAME                      = 'fname'
CONF_APPLE_ACCOUNT              = 'apple_account'
CONF_APPLE_ACCT                 = 'apple_account'
CONF_ICLOUD_DEVICENAME          = 'famshr_devicename'
CONF_ICLOUD_DEVICE_ID           = 'famshr_device_id'
CONF_FAMSHR_DEVICENAME          = 'famshr_devicename'
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
CONF_TRACK_FROM_BASE_ZONE_USED  = 'track_from_base_zone_used'   # Primary Zone a device is tracking from, normally Home
CONF_TRACK_FROM_BASE_ZONE       = 'track_from_base_zone'        # Primary Zone a device is tracking from, normally Home
CONF_TRACK_FROM_HOME_ZONE       = 'track_from_home_zone'
CONF_TRACK_FROM_ZONES           = 'track_from_zones'            # All zones the device is tracking from
CONF_LOG_ZONES                  = 'log_zones'                   # Log zone activity to 'icloud3-zone-log_[year]_[device]_[zone].csv' file
CONF_DEVICE_TYPE                = 'device_type'
CONF_INZONE_INTERVAL            = 'inzone_interval'
CONF_FIXED_INTERVAL             = 'fixed_interval'
CONF_UNIQUE_ID                  = 'unique_id'
CONF_EVLOG_DISPLAY_ORDER        = 'evlog_display_order'
CONF_STAT_ZONE_FNAME            = 'stat_zone_fname'

CONF_ZONE                       = 'zone'
CONF_COMMAND                    = 'command'
CONF_NAME                       = 'name'
CONF_MOBAPP_REQUEST_LOC_MAX_CNT = 'mobapp_request_loc_max_cnt'
CONF_INTERVAL                   = 'interval'

# Local Time Zone
CONF_AWAY_TIME_ZONE_1_OFFSET    = 'away_time_zone_1_offset'
CONF_AWAY_TIME_ZONE_1_DEVICES   = 'away_time_zone_1_devices'
CONF_AWAY_TIME_ZONE_2_OFFSET    = 'away_time_zone_2_offset'
CONF_AWAY_TIME_ZONE_2_DEVICES   = 'away_time_zone_2_devices'

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

CONF_EXCLUDED_SENSORS         = "excluded_sensors"


DISTANCE           = 'distance'
CONF_SENSORS_ZONE  = 'zone'
ZONE_INFO          = 'zone_info'
ZONE               = "zone"
ZONE_DNAME         = "zone_dname"
ZONE_FNAME         = "zone_fname"
ZONE_NAME          = "zone_name"
ZONE_DATETIME      = "zone_changed"
LAST_ZONE          = "last_zone"
LAST_ZONE_DNAME    = "last_zone_dname"
LAST_ZONE_FNAME    = "last_zone_fname"
LAST_ZONE_NAME     = "last_zone_name"
LAST_ZONE_DATETIME = "last_zone_changed"

CONF_SENSORS_OTHER = 'other'
GPS_ACCURACY       = "gps_accuracy"
ALTITUDE           = "altitude"
VERTICAL_ACCURACY  = "vertical_accuracy"

CF_PROFILE         = 'profile'
CF_DATA            = 'data'
CF_TRACKING        = 'tracking'
CF_DATA_DEVICES    = 'devices'
CF_DATA_APPLE_ACCOUNTS = 'apple_accounts'
CF_GENERAL         = 'general'
CF_SENSORS         = 'sensors'
CF_DEVICE_SENSORS  = 'device_sensors'

#--------------------------------------------------------
DEFAULT_PROFILE_CONF = {
        CONF_VERSION: 0,
        CONF_IC3_VERSION: VERSION,
        CONF_VERSION_INSTALL_DATE: DATETIME_ZERO,
        CONF_UPDATE_DATE: DATETIME_ZERO,
        CONF_EVLOG_VERSION: '',
        CONF_EVLOG_VERSION_RUNNING: '',
        CONF_EVLOG_CARD_DIRECTORY: EVLOG_CARD_WWW_DIRECTORY,
        CONF_EVLOG_CARD_PROGRAM: EVLOG_CARD_WWW_JS_PROG,
        CONF_EVLOG_BTNCONFIG_URL: '',
        CONF_PICTURE_WWW_DIRS: []
}

DEFAULT_TRACKING_CONF = {
        CONF_USERNAME: '',
        CONF_PASSWORD: '',
        CONF_ENCODE_PASSWORD: True,
        CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX: '',
        CONF_SERVER_LOCATION_NEEDED: False,
        CONF_SETUP_ICLOUD_SESSION_EARLY: True,
        CONF_PASSWORD_SRP_ENABLED: True,
        CONF_DATA_SOURCE: f'{ICLOUD},{MOBAPP}',
        CONF_APPLE_ACCOUNTS: [],
        CONF_DEVICES: [],
}

DEFAULT_APPLE_ACCOUNT_CONF = {
        CONF_USERNAME: '',
        CONF_PASSWORD: '',
        CONF_TOTP_KEY: '',
        CONF_LOCATE_ALL: True,
        CONF_SERVER_LOCATION: 'usa',
}

DEFAULT_DEVICE_CONF = {
        CONF_IC3_DEVICENAME: ' ',
        CONF_FNAME: '',
        CONF_PICTURE: 'None',
        CONF_ICON: 'mdi:account',
        CONF_UNIQUE_ID: '',
        CONF_DEVICE_TYPE: 'iPhone',
        CONF_INZONE_INTERVAL: 120,
        CONF_FIXED_INTERVAL: 0,
        CONF_TRACKING_MODE: TRACK_DEVICE,
        CONF_APPLE_ACCOUNT: '',
        CONF_FAMSHR_DEVICENAME: 'None',
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
        CONF_FAMSHR_DEVICENAME: 'None',
        CONF_FAMSHR_DEVICE_ID: '',
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
        CONF_WAZE_MIN_DISTANCE: [0, 1000, 5, 'km'],
        CONF_WAZE_MAX_DISTANCE: [0, 1000, 5, 'km'],
        CONF_WAZE_HISTORY_MAX_DISTANCE: [0, 1000, 5, 'km'],

        # Stationary Zone Configuration Parameters
        CONF_STAT_ZONE_STILL_TIME: [0, 60],
        CONF_STAT_ZONE_INZONE_INTERVAL: [5, 60],
        CONF_STAT_ZONE_BASE_LATITUDE:  [-90, 90, 1, ''],
        CONF_STAT_ZONE_BASE_LONGITUDE: [-180, 180, 1, ''],
}

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

DEFAULT_DATA_CONF =  {
        CF_TRACKING: DEFAULT_TRACKING_CONF,
        CF_GENERAL: DEFAULT_GENERAL_CONF,
        CF_SENSORS: DEFAULT_SENSORS_CONF,
        CF_DEVICE_SENSORS: [],
}

CF_DEFAULT_IC3_CONF_FILE = {
        CF_PROFILE: DEFAULT_PROFILE_CONF,
        CF_DATA: {
                CF_TRACKING: DEFAULT_TRACKING_CONF,
                CF_GENERAL: DEFAULT_GENERAL_CONF,
                CF_SENSORS: DEFAULT_SENSORS_CONF,
                CF_DEVICE_SENSORS: [],
        }
}

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
        'profile': {
                CONF_VERSION: 0,
                LAST_UPDATE: DATETIME_ZERO, },
        'devices': {},
}

# Initialize the Device sensors[xxx] value from the restore_state file if
# the sensor is in the file. Otherwise, initialize to this value
USE_RESTORE_STATE_VALUE_ON_STARTUP = {
        BATTERY: 0,
        BATTERY_STATUS: '',
        BATTERY_SOURCE: '',
}

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
#
#       TRACE AND RAWDATA VARIABLES
#
#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
TRACE_ATTRS_BASE = {
        NAME: '',
        ZONE: '',
        LAST_ZONE: '',
        INTO_ZONE_DATETIME: '',
        LATITUDE: 0,
        LONGITUDE: 0,
        POSITION_TYPE: '',
        TRIGGER: '',
        TIMESTAMP: DATETIME_ZERO,
        ZONE_DISTANCE: 0,
        HOME_DISTANCE: 0,
        INTERVAL: 0,
        DIR_OF_TRAVEL: '',
        MOVED_DISTANCE: 0,
        WAZE_DISTANCE: '',
        CALC_DISTANCE: 0,
        LAST_LOCATED_DATETIME: '',
        LAST_UPDATE_TIME: '',
        NEXT_UPDATE_TIME: '',
        POLL_COUNT: '',
        INFO: '',
        BATTERY: 0,
        BATTERY_LEVEL: 0,
        GPS: 0,
        GPS_ACCURACY: 0,
        VERT_ACCURACY: 0,
        }

TRACE_ICLOUD_ATTRS_BASE = {
        'name': '',
        ICLOUD_DEVICE_STATUS: '',
        LATITUDE: 0,
        LONGITUDE: 0,
        ICLOUD_POSITION_TYPE: '',
        ICLOUD_TIMESTAMP: 0,
        ICLOUD_HORIZONTAL_ACCURACY: 0,
        ICLOUD_VERTICAL_ACCURACY: 0,
        }
FAMSHR_LOCATION_FIELDS = [
        ALTITUDE,
        LATITUDE,
        LONGITUDE,
        ICLOUD_POSITION_TYPE,
        TIMESTAMP,
        ICLOUD_HORIZONTAL_ACCURACY,
        ICLOUD_VERTICAL_ACCURACY,
        ICLOUD_BATTERY_STATUS, ]

X_LOG_RAWDATA_FIELDS = [
        LATITUDE,  LONGITUDE, LOCATION_SOURCE, TRACKING_METHOD, DATA_SOURCE, NEAR_DEVICE_USED,
        ZONE, ZONE_DATETIME, INTO_ZONE_DATETIME, LAST_ZONE,
        TIMESTAMP, TIMESTAMP_SECS, TIMESTAMP_TIME, LOCATION_TIME, DATETIME, AGE,
        TRIGGER, BATTERY, BATTERY_LEVEL, BATTERY_STATUS,
        INTERVAL, ZONE_DISTANCE, HOME_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE,
        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME, DIR_OF_TRAVEL, MOVED_DISTANCE,
        DEVICE_STATUS, LOW_POWER_MODE,
        TRACKING, DEVICENAME_MOBAPP,
        AUTHENTICATED,
        LAST_UPDATE_TIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_TIME, LAST_LOCATED_DATETIME,
        INFO, GPS_ACCURACY, GPS, POLL_COUNT, VERT_ACCURACY, ALTITUDE,
        ICLOUD3_VERSION,
        BADGE,
        DEVICE_ID, ID,
        ICLOUD_HORIZONTAL_ACCURACY, ICLOUD_VERTICAL_ACCURACY, ICLOUD_POSITION_TYPE,
        ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS,
        ICLOUD_DEVICE_CLASS, ICLOUD_DEVICE_STATUS, ICLOUD_LOW_POWER_MODE, ICLOUD_TIMESTAMP,
        NAME, 'emails', 'firstName', 'laststName',
        'prsId', 'batteryLevel', 'isOld', 'isInaccurate', 'phones',
        'invitationAcceptedByEmail', 'invitationFromEmail', 'invitationSentToEmail', 'data',
        'original_name', 'name_by_user',
        ]
