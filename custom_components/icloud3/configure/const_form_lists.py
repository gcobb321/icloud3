
from ..global_variables     import GlobalVariables as Gb
from ..const                import (NAME, )
from ..const_config         import (ARRIVAL_TIME, HOME_DISTANCE, NEXT_UPDATE, TRAVEL_TIME, BATTERY, )

#----------------------------------------------------------------------------------------
# Dashboard constants
RESULT_SUMMARY = 'result-summary'
TRACK_DETAILS  = 'track-details'
ALL_DEVICES    = 'all-devices'
IPHONE_FIRST_2 = 'iphone-first-2'
ALL_IPH2_DEVICES = [ALL_DEVICES, IPHONE_FIRST_2]

DATA           = 'data'
CONFIG         = 'config'
ITEMS          = 'items'
VIEWS          = 'views'
TITLE          = 'title'
PATH           = 'path'
ADD            = 'add'
IC3DB          = 'ic3db-'

# Form field of the Submit/Back choice displayed at the end of the forms (utils_cf.submit_back_field).
# The labels are the strings.json selector.cf_text.options submit_[action], back_[action],
# back_discard and back texts, {dest} is a dest_[key] text.
FORM_ACTION = 'form_action'
# Forms whose Submit action saves the entered data. Back discards it.
FORM_ACTION_SAVES_DATA = ['save', 'save_menu', 'save_log_into_apple_acct', 'update_text_as',
                            'update_sensor_list', 'update_tracking_mode']

# The Tools that display the Confirm Action screen. The question and the Yes/No rows are the
# strings.json selector.cf_text.options confirm_[tool], confirm_yes_[tool] and
# confirm_no_[tool] texts
TOOL_CONFIRM_ITEMS = [  'restart_icloud3', 'reset_data_source', 'reset_tracking', 'reset_general',
                        'del_apple_acct_cookies', 'del_icloud3_config_files', ]

DATA_ENTRY_ALERT_CHAR = '⚠︎'
DATA_ENTRY_ALERT      = f"      {DATA_ENTRY_ALERT_CHAR} "

#----------------------------------------------------------------------------------------
#   Configure Menus - HA native menus (async_show_menu)
#
#   MENU_TREE - The menu step_id and the menu options displayed on it. A menu option is:
#       - menu_xxx  - Another menu, displayed by async_step_menu_xxx
#       - open_xxx  - A configure screen, opened by async_step_open_xxx --> open_menu_item(xxx)
#       - main_menu - Return to the main menu
#   The option labels are in strings.json options.step.[menu step_id].menu_options
MAIN_MENU = 'menu'
MENU_TREE = {
        'menu':             ['open_apple_accounts', 'open_device_list', 'menu_tracking',
                                'menu_display', 'menu_sensors', 'menu_system', ],
        'menu_tracking':    ['open_tracking_parameters', 'open_special_zones', 'open_waze',
                                'open_inzone_intervals', 'main_menu', ],
        'menu_display':     ['open_format_settings', 'open_display_text_as', 'open_away_time_zone',
                                'main_menu', ],
        'menu_sensors':     ['open_sensors', 'open_exclude_sensors',
                                'open_dashboard_builder', 'main_menu', ],
        'menu_system':      ['open_tools', 'open_analytics', 'open_analytics_reports',
                                'main_menu', ],
}

# Menu items (configure screens) on the menus and the Needs attention items displayed
# at the top of the main menu (form_config_flow.build_needs_attention)
MENU_ITEMS = [  'apple_accounts', 'device_list', 'inzone_intervals',
                'tracking_parameters', 'special_zones', 'waze',
                'format_settings', 'display_text_as', 'away_time_zone',
                'sensors', 'exclude_sensors', 'dashboard_builder',
                'tools', 'analytics', 'analytics_reports', ]
MENU_ACTION_NEEDED_ITEMS = [
                'action_terms_of_use', 'action_reauth', 'action_login_failed',
                'action_add_apple_acct', 'action_no_data_source', 'action_add_devices',
                'action_review_inactive', 'action_review_inactive_some', 'action_analytics', ]

# The keys of the form sections (data_entry_flow.section, utils_cf.sectioned_schema) end
# with SECTION_SUFFIX
SECTION_SUFFIX   = '_section'
ADVANCED_SECTION = 'advanced_section'

# Warning symbol displayed in the Configure screen text (text presentation, not the emoji)
CF_ALERT = '⚠︎ '

PICTURE_DIR_FILTER = 'setup_picture_dir_filter'

#----------------------------------------------------------------------------------------


NONE_DICT_KEY_TEXT          = {'None': 'None'}
SERVICE_NOT_AVAILABLE       = ' → This Data Source/Web Location Service is not available'
SERVICE_NOT_STARTED_YET     = ' → This Data Source/Web Location Svc has not finished starting. Exit and Retry.'
LOGGED_INTO_MSG_ACTION_LIST_IDX = 1     # Index number of the Action list item containing the apple_id/password
APPLE_ACCOUNT_USERNAME_ACTION_LIST_IDX = 0     # Index number of the Action list item containing the apple_id/password
UNSELECTED_IDX = -1

#------------------------–--------------------------------------------------------------
# Tools menu (step_id tools) options. The labels are in strings.json options.step.tools.menu_options
TOOL_ITEMS = [  'log_level', 'beta_version', 'cleanup_entity_registry', 'restart_icloud3',
                'reset_data_source', 'reset_tracking', 'reset_general', 'del_apple_acct_cookies',
                'del_icloud3_config_files', ]


        # ACTION_LIST_OPTIONS['rtn_device_list']]
        # ACTION_LIST_OPTIONS['menu']]
        # ACTION_LIST_OPTIONS['exit'],


# marketplace.async_set_icloud3_prerelease_switch return value --> options error key
PRERELEASE_SWITCH_ERRORS = {
        'repo_not_installed': 'prerelease_repo_not_installed',
        'switch_not_found':   'prerelease_switch_not_found',
        'fix_action_failed':  'prerelease_switch_failed'}

# The Devices, Change Device Order, Apple Accounts and Display Text As menus display a menu
# row for each device, Apple Account and text replacement item. The rows are opened by the
# async_step_device_list_device_[slot], async_step_change_device_order_device_[idx],
# async_step_apple_accounts_acct_[slot] and async_step_display_text_as_item_[idx] functions
DEVICE_LIST_PAGE_SIZE     = 6
DEVICE_ORDER_MAX_CNT      = 100
DISPLAY_TEXT_AS_ITEM_CNT  = 10
APPLE_ACCT_LIST_PAGE_SIZE = 5

#------------------------–--------------------------------------------------------------

#------------------------–--------------------------------------------------------------
#   Parameter List Selections Items
DATA_SOURCE_OPTIONS = {
        'iCloud':   'APPLE ACCOUNT - Location data is provided for devices in the Family Sharing List',
        'MobApp':   'HA MOBILE APP - Location data and zone enter/exit triggers from devices with the Mobile App'
        }

# Apple Server Endpoint value - Add onto the Server URL in AppleAcct_ic3 if this starts with a period ('.')
APPLE_SERVER_LOCATION_OPTIONS = ['usa', '.cn', '.cn,GCJ02', '.cn,BD09']
DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS = ['reassign_devices', 'delete_devices', 'set_devices_inactive']
DASHBOARD_MAIN_VIEW_STYLE_OPTIONS = [RESULT_SUMMARY, TRACK_DETAILS]
# The selector.cf_text.options log_zones_[key] texts
LOG_ZONES_FILE_NAMES = ['name-zone', 'name-device', 'name-device-zone', 'name-zone-device']
DATA_SOURCE_OPTIONS = ['iCloud,MobApp', 'iCloud', 'MobApp']
TRACKING_MODE_OPTIONS = ['track', 'monitor', 'inactive']
UNIT_OF_MEASUREMENT_OPTIONS = ['mi', 'km']
TIME_FORMAT_OPTIONS = ['12-hour', '24-hour']
TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT = [.25, .33, .50, .66, .75]
DISPLAY_ZONE_FORMAT_OPTIONS_BASE = ['fname', 'zone', 'name', 'title']
DEVICE_TRACKER_STATE_SOURCE_OPTIONS = ['ic3_evlog', 'ic3_fname', 'ha_gps']
LOG_LEVEL_OPTIONS = ['info', 'debug', 'debug-ha', 'debug-auto-reset', 'rawdata', 'rawdata-auto-reset',
        'unfiltered']
DISTANCE_METHOD_OPTIONS = {
        'waze':     'Waze - Waze Route Service provides travel time & distance information',
        'calc':     'Calc - Distance is calculated using a `straight line` formula'
        }
WAZE_SERVER_OPTIONS = ['us', 'il', 'row']
WAZE_HISTORY_TRACK_DIRECTION_OPTIONS = ['north_south', 'east_west']
USER_AUTH_RAW_YAML_DISPLAY_MODES = ['always', 'when_auth_needed']
# The sensors that are always created. They are not on the Sensors screen, the section
# descriptions name them.
ALWAYS_CREATED_SENSORS = {
        'device':               ['badge', BATTERY],
        'tracking_update':      [NEXT_UPDATE],
        'tracking_time':        [TRAVEL_TIME, ARRIVAL_TIME],
        'tracking_distance':    [HOME_DISTANCE],
        'monitored_devices':    ['md_badge', 'md_battery'],
        }
CONF_SENSORS_DEFAULT = {
        BATTERY:            '_battery, _battery_status → Create Battery Level (65%) and Battery Status (Charging, Low, etc) (ALWAYS CREATED)',
        'arrival_time':     '_arrival_time → Home Zone arrival time based on Waze Travel time (ALWAYS CREATED)',
        'travel_time':      '_travel_time → Waze Travel time to Home or closest Track-from-Zone zone (ALWAYS CREATED)',
        'home_distance':    '_home_distance → Distance to the Home zone (ALWAYS CREATED)',
        'next_update':      '_next_update → Next time the location will be updated (ALWAYS CREATED)',
        }
CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT = ['md_badge', 'md_battery', 'md_location_sensors']
CONF_SENSORS_DEVICE_KEY_TEXT = [NAME, 'badge', BATTERY, 'info']
CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT = ['interval', 'last_update', 'next_update', 'last_located']
CONF_SENSORS_TRACKING_TIME_KEY_TEXT = ['travel_time', 'travel_time_min', 'travel_time_hhmm', 'arrival_time']
CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT = ['home_distance', 'zone_distance', 'dir_of_travel', 'moved_distance']
CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT = {
        'general_sensors':  'Include General Sensors (_zone_info)',
        'time_sensors':     'Include Travel Time Sensors (_travel_time, _travel_time_mins, _travel_time_hhmm, _arrival_time',
        'distance_sensors': 'Include Zone Distance Sensors (_zone_distance, _distance, _dir_of_travel)',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEYS = ['general_sensors', 'time_sensors', 'distance_sensors']
CONF_SENSORS_TRACKING_OTHER_KEY_TEXT = ['trigger', 'waze_distance', 'calc_distance']
CONF_SENSORS_ZONE_KEY_TEXT = ['zone_fname', 'zone', 'zone_name', 'zone_datetime', 'last_zone']
CONF_SENSORS_OTHER_KEY_TEXT = ['gps_accuracy', 'vertical_accuracy', 'altitude']

ACTIONS_SCREEN_OPTIONS = {
        "divider1":         "═════════════ ICLOUD3 CONTROL ACTIONS ══════════════",
        "restart":          "RESTART → Restart iCloud3",
        "pause":            "PAUSE → Pause polling on all devices",
        "resume":           "RESUME → Resume Polling on all devices, Refresh all locations",
        "divider2":         "════════════════ DEBUG LOG ACTIONS ══════════════",
        "debug_start":      "START DEBUG LOGGING → Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING → Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING → Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING → Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS → Verify all debug log file records are written",
        "divider3":         "════════════════ OTHER COMMANDS ═══════════════",
        "evlog_export":     "EXPORT EVENT LOG → Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE → Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK → Load route locations for map display",
        "divider4":         "═══════════════════════════════════════════════",
        "restart_ha":       "RESTART HA, RESTART ICLOUD3 → Restart HA, Restart iCloud3",
        "return":           "MAIN MENU → Return to the Main Menu"
        }
ACTIONS_SCREEN_ITEMS_TEXT  = [text for text in ACTIONS_SCREEN_OPTIONS.values()]
ACTIONS_SCREEN_ITEMS_KEY_BY_TEXT = {text: key
                                for key, text in ACTIONS_SCREEN_OPTIONS.items()
                                if key.startswith('divider') is False}

ACTIONS_IC3_ITEMS = {
        "restart":          "RESTART → Restart iCloud3",
        "pause":            "PAUSE → Pause polling on all devices",
        "resume":           "RESUME → Resume Polling on all devices, Refresh all locations",
        }
ACTIONS_DEBUG_ITEMS = {
        "debug_start":      "START DEBUG LOGGING → Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING → Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING → Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING → Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS → Verify all debug log file records are written",
        }
ACTIONS_OTHER_ITEMS = {
        "evlog_export":     "EXPORT EVENT LOG → Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE → Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK → Load route locations for map display",
        }
ACTIONS_ACTION_ITEMS = {
        "restart_ha":       "RESTART HA AND ICLOUD3 → Restart HA and iCloud3",
        "return":           "MAIN MENU → Return to the Main Menu"
        }

# Section Headers used on various forms
MOBILE_APP_USED_HEADER = (
        'MOBILE APP INTEGRATION - Monitor the Mobile App Integration devices location data and zone enter/exit triggers')
RARELY_UPDATED_PARMS        = 'rarely_updated_parms'
RARELY_UPDATED_PARMS_HEADER = (
        "➤ RARELY USED PARAMETERS - Display inZone & Fixed Interval, Track-from-Zone and Track-from-Home Zone Override parameters the parameters")
WAZE_USED_HEADER = (
        "The Waze Route Service provides the travel time and distance information from your "
        "current location to the Home or another tracked from zone. This information is used to determine "
        "when the next location request should be made")
WAZE_HISTORY_USED_HEADER = (
        "The Waze History Data base stores 'close to zone' travel time and distance information "
        "for a GPS location (100m radius). It reduces the number of internet requests to the Waze Servers "
        "after it has been in use for a while and speed up response time when in a poor cell area")
PASSTHRU_ZONE_HEADER = (
        "You may be driving through a non-tracked zone but not stopping at the zone. The Mobile "
        "App issues an Enter Zone trigger when the device enters the zone and changes the "
        "device_tracker entity state to the Zone. iCloud3 does not process the Enter Zone "
        "trigger until the delay time has passed. This prevents processing a Zone Enter "
        "trigger that is immediately followed by an Exit Zone trigger.")
STAT_ZONE_HEADER = (
        "A Stationary Zone is automatically created if the device remains in the same location "
        "(store, friends house, doctor’s office, etc.) for an extended period of time")
TRK_FROM_HOME_ZONE_HEADER =(
        "Normally, the Home zone is used as the primary track-from-zone for the tracking results "
        "(travel time, distance, etc).  However, a different zone can be used as the base location "
        "if you are away from Home for an extended period or the device is normally at another "
        "location (vacation house, second home, parent's house, etc.). This is a global setting "
        "that overrides the Primary Track-from-Home Zone assigned to an individual Device on the Update "
        "Devices screen.")
IC3_DIRECTORY_HEADER = (
        "Change the directory containing the Event Log Custom Card File (event-log-card.js). Set the `Gear` URL for the `HA Devices & Svcs → iCloud3 Config screen`")
DATA_SOURCE_ICLOUD_HDR = (
        "APPLE ACCOUNT → Location data is provided by devices in the Family Sharing list")
DATA_SOURCE_MOBAPP_HDR = (
        "HA MOBILE APP → Location data and zone Enter/Exit triggers are provided by the Mobile App")
ANALYTICS_ENABLED_HDR = (
        "SEND ICLOUD3 ANALYTICS DATA > Send iCloud3 Usage, Location and Analytics Data to the iCloud3 Analytics Database on a regular basis. `What is Sent` below shows the actual data you will be sending")



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→
