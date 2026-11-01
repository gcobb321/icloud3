
from ..global_variables     import GlobalVariables as Gb
from ..const                import (NAME, )
from ..const_config         import (BATTERY, NEXT_UPDATE, TRAVEL_TIME, ARRIVAL_TIME, HOME_DISTANCE, )

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
UNSELECTED_IDX = -1

#------------------------–--------------------------------------------------------------
# Tools menu (step_id tools) options. The labels are in strings.json options.step.tools.menu_options
TOOL_ITEMS = [  'log_level', 'beta_version', 'cleanup_entity_registry', 'restart_icloud3',
                'reset_data_source', 'reset_tracking', 'reset_general', 'del_apple_acct_cookies',
                'del_icloud3_config_files', ]

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
#   Parameter List Selections Items. The option labels are the strings.json
#   selector.[translation_key].options texts (utils_cf.select)

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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→
