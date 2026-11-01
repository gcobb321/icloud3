
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
NOT_LOGGED_IN  = 'NOT LOGGED IN'

DATA_ENTRY_ALERT_CHAR = '⛔'
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



ACTION_LIST_OPTIONS = {
        'rtn_device_list':          '➤ RETURN → ICLOUD3 DEVICES → Return to the screen showing the Tracked and Monitored devices',
        'rtn_update_device':        '➤ RETURN → UPDATE ICLOUD3 DEVICE → Return to Update iCloud3 Device screen',
        'rtn_apple_accounts':       '➤ RETURN → APPLE ACCOUNTS → Return to the screen showing the Apple Accounts',
        'rtn_update_apple_acct':    '➤ RETURN → UPDATE APPLE ACCOUNT → Return to the Update Apple Account screen',
        'rtn_reauth':               '➤ RETURN → AUTHENTICATE APPLE ACCT SIGN-IN → Return to the screen that authenticates signing into the Apple Accounts',
        'exit_ha_reconfigure_reauth':'➤ RETURN → HA ICLOUD3 CONFIGURE SCREEN → Close Authentication screen and return to HA',

        'goto_previous':            '➤ RETURN → Return to the previous screen',
        'cancel_goto_previous':     '➤ RETURN → Return to the previous screen. Cancel any unsaved changes',
        'menu':                     '➤ MENU → Display the Menu screen',
        'cancel_goto_menu':         '➤ MENU → Display the Menu screen. Cancel any unsaved changes',
        'exit':                     '➤ EXIT → End the iCloud3 Configure Session, Return to HA',
        'exit_repair':              '➤ EXIT → Return to the Repair Item. Cancel any unsaved changes',
        'save':                     '➤ SAVE & RETURN → Update Configuration File, Return to the Previous screen',
        'save_stay':                '➤ SAVE → Update Configuration File',
        'save_menu':                '➤ SAVE & RETURN → Update Configuration File, Display the Menu screen',

        'next_page_items':          'NEXT PAGE ITEMS → ^add-text^',
        'next_page':                'NEXT PAGE → Save changes. Display the next page',
        'next_page_devices':        'NEXT PAGE → Display devices ^add-text^',
        'next_page_waze':           'NEXT PAGE → Waze History Database parameters',
        'select_form':              'SELECT → Select the parameter update form',

        'update_apple_acct':        'UPDATE APPLE ACCOUNT → Update the Username/Password of the selected Apple Account, Add a new Apple Account, Remove the Apple Account',
        'save_log_into_apple_acct': 'SAVE, LOG IN & IMPORT APPLE DEVICES → Save any configuration changes, Log into the Apple Account, Import Apple devices',
        'log_into_apple_acct':      'LOG INTO APPLE ACCT → Log into the Apple Account, Save any configuration changes',
        'stop_using_apple_acct':    'STOP USING AN APPLE ACCOUNT → Stop using an Apple Account, Remove it from the Apple Accounts list and all devices using it',
        'authenticate_apple_acct':  'AUTHENTICATE APPLE ACCT SIGN-IN → Send/Request the 6-digit Authentication Code',
        'delete_apple_acct':        'DELETE APPLE ACCOUNT → Delete the selected Apple Account. Delete or reassign iCloud3 devices using it',
        'stop_login_retry':         'STOP RETRYING LOGIN → Stop retrying to log into the Apple Account',
        'other_apple_acct_parameters': 'OTHER APPLE ACCOUNT PARAMETERS → Set other config parameters (China Apple Server Location)',

        'send_auth_code':           'AUTHENTICATE → Send the Authentication Code back to Apple or Confirm the Security Key security code',
        'request_auth_code':        'REQUEST AUTHENTICATION CODE or SECURITY KEY KEYPRESS → Untrust the Apple Acct. Get a new Authentication code or Start the Hardware Key keypress Process',
        'change_auth_method':       'CHANGE AUTHENTICATION METHOD → Select a new method (Pop-up Window, Text Message, Security Key), Refresh Trusted Phone Numbers & Security Key names',
        'user_auth_dashboard':     'BUILD USER AUTH DASHBOARD CARD → Show the Text/Button raw_yaml code needed to send an authentication code to Apple from a Dashboard',
        'reset_trust_token_return': 'RESET TRUST TOKEN, RETURN TO ENTER & SEND THE CODE TO APPLE → Resets the Trust Token. Return to the Authenticate Apple Sign-in screen',
        'auth_code_from_applecom_login': 'APPLE DID NOT SEND A CODE (PUSH/TEXT), GET ONE FROM APPLE.COM → Sign into your Apple Acct, get a code, enter it here and send to Apple',
        'refresh_hwkey_names':      'REFRESH TRUSTED PHONE NUMBERS/SECURITY KEY NAMES → Get the Trusted Phone Numbers or the registered Security Key names from Apple',

        'accept_terms_of_use':      'ACCEPT `TERMS OF USE` → Send `I Agree` to Apple updates to the `Terms of Use`',

        'update_device':            'UPDATE THE DEVICE → Update the selected device, Display more Devices on the next page',
        'add_device':               'ADD A NEW DEVICE → Add a new device to be tracked by iCloud3',
        'delete_device':            'DELETE DEVICE → Delete the selected device',
        'change_device_order':      'CHANGE DEVICE ORDER → Change the tracking order of the Devices and their display sequence on the Event Log',
        'update_other_device_parameters': 'UPDATE OTHER DEVICE PARAMETERS → (^otp_msg)',

        'import_apple_devices':     'IMPORT APPLE DEVICES → Create iCloud3 devices from the devices in the Apple Accounts',
        'add_imported_apple_devices': 'ADD IMPORTED APPLE DEVICES → Create iCloud3 device_tracker entities from imported Apple devices',

        'update_tracking_mode':     '➤ SAVE → Update the  Tracking Mode of the selected devices, Tracked-iPhone/Watch devices, Monitorted-iPad/Mac devices‘',

        'restart_ha':               'RESTART HOME ASSISTANT → Restart HA & iCloud3',
        'restart_icloud3':          'RESTART ICLOUD3 → Restart iCloud3 Now',
        'restart_ic3_now':          'RESTART NOW → Restart iCloud3 now to load the updated configuration',
        'reload_icloud3':           'RELOAD ICLOUD3 → Reload & Restart iCloud3 (This does not load a new version)',
        'restart_ic3_later':        'RESTART LATER → The configuration changes have been saved. Load the updated configuration the next time iCloud3 is started',
        'review_inactive_devices':  'REVIEW INACTIVE DEVICES → Some Devices are `Inactive‘ and will not be located or tracked ^add-text^',

        'update_sensor_list':       'UPDATE LIST, SELECT MORE SENSORS → Update the Excluded Sensors List, Select more Sensors to Exclude',
        'return_to_sensor_screen':  'UPDATE LIST, RETURN TO SENSOR SCREEN → Return to the Sensor screen with the updated Excluded Sensors list',
        'show_all_sensors':         'DISPLAY SENSOR NAMES (ALL) → Display all of the device‘s sensors',
        'show_some_sensors':        'DISPLAY SENSOR NAMES (2-LINES) → Display the device‘s sensors that will fit on 2-lines',
        'check_all':                'CHECK ALL ITEMS → Select all items',
        'check_none':               'UNCHECK ALL ITEMS → Unselect all items',
        'delete_device_sensors':    'DELETE SELECTED DEVICE SENSORS → Remove the selected device sensors from the HA Entity and Device Registry',

        'create_dashboard':         'CREATE/UPDATE A DASHBOARD → Erase and recreate an existing Dashboard, Create a new Dashboard',

        'select_text_as':           'SELECT → Update selected `Display Text As‘ field',
        'clear_text_as':            'CLEAR → Remove this `Display Text As‘ entry',
        'update_text_as':           'UPDATE → Finished setting this `Display Text As‘ entry',

        'exclude_sensors':          'EXCLUDE SENSORS → Select specific Sensors that should not be created',
        'filter_sensors':           'FILTER SENSORS → Select Sensors that should be displayed',
        'set_to_default_sensors':   'SET TO DEFAULT → Reset sensors to the default selection',

        'move_up':                  'MOVE UP → Move the Device up in the list',
        'move_down':                'MOVE DOWN → Move the Device down in the list',
        'refresh':                  'REFRESH → Refresh the screen',

        'send_analytics_data':      'SEND ANALYTICS DATA NOW → Send the Analytics data to the iCloud3 Analytics Database Now',
        'analytics':                'ICLOUD3 ANALYTICS → Enable Sending Analytics Data to the iCloud3 Analytics Database',
        'analytics_reports':        'REPORTS → Run a Report using data in Analytics Database',
        'run_report':               'RUN REPORT → Run the selected Report and Display the Results',

        'confirm_action_yes_enable_beta':  'ENABLE BETA VERSION → Start downloading Beta Versions from the HA Marketplace',
        'confirm_action_no_disable_beta':  'DISABLE BETA VERSION → Stop downloading Beta Versions from the HA Marketplace',
        'confirm_action_yes':       'YES → Complete the requested action',
        'confirm_action_no':        'NO  → Cancel the request',
        'confirm_save':             '➤ SAVE THE CONFIGURATION CHANGES → Save any changes, Return to the Main Menu',

        "divider1": "═══════════════════════════════════════",
        "divider2": "═══════════════════════════════════════",
        "divider3": "═══════════════════════════════════════",

        }

ACTION_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in ACTION_LIST_OPTIONS.items()}
ACTION_LIST_ITEM_KEYS         = list(ACTION_LIST_OPTIONS.keys())

NONE_DICT_KEY_TEXT          = {'None': 'None'}
NONE_FAMSHR_DICT_KEY_TEXT   = {'None': 'ⓧ Apple iCloud Location Service is not used on this device'}
UNKNOWN_DEVICE_TEXT         = ' → UNKNOWN/NOT FOUND → NEEDS REVIEW'
SERVICE_NOT_AVAILABLE       = ' → This Data Source/Web Location Service is not available'
SERVICE_NOT_STARTED_YET     = ' → This Data Source/Web Location Svc has not finished starting. Exit and Retry.'
LOGGED_INTO_MSG_ACTION_LIST_IDX = 1     # Index number of the Action list item containing the apple_id/password
APPLE_ACCOUNT_USERNAME_ACTION_LIST_IDX = 0     # Index number of the Action list item containing the apple_id/password
APPLE_ACCOUNTS_MULTI_HDR = {'apple_acct_hdr': '═════════ Additional Apple Accounts ═════════'}
UNSELECTED_IDX = -1

#------------------------–--------------------------------------------------------------
# Tools menu (step_id tools) options. The labels are in strings.json options.step.tools.menu_options
TOOL_ITEMS = [  'log_level', 'beta_version', 'cleanup_entity_registry', 'restart_icloud3',
                'reset_data_source', 'reset_tracking', 'reset_general', 'del_apple_acct_cookies',
                'del_icloud3_config_files', ]

APPLE_ACCOUNT_ACTIONS = [
        ACTION_LIST_OPTIONS['update_apple_acct'],
        ACTION_LIST_OPTIONS['authenticate_apple_acct'],
        ACTION_LIST_OPTIONS['import_apple_devices'],
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['menu']]
APPLE_ACCOUNT_DELETE_ACTIONS = [
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['cancel_goto_previous']]
APPLE_ACCOUNT_OTHER_PARMS_ACTIONS = [
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['rtn_update_apple_acct']]
APPLE_ACCOUNT_UPDATE_ACTIONS = [
        ACTION_LIST_OPTIONS['save_log_into_apple_acct'],
        ACTION_LIST_OPTIONS['authenticate_apple_acct'],
        ACTION_LIST_OPTIONS['other_apple_acct_parameters'],
        ACTION_LIST_OPTIONS['rtn_apple_accounts']]
APPLE_ACCOUNT_UPDATE_REPAIR_ACTIONS = [     # Update Apple Account screen opened from HA Repairs
        ACTION_LIST_OPTIONS['save_log_into_apple_acct'],
        ACTION_LIST_OPTIONS['authenticate_apple_acct'],
        ACTION_LIST_OPTIONS['other_apple_acct_parameters'],
        ACTION_LIST_OPTIONS['exit_repair']]
REAUTH_ACTIONS = [
        ACTION_LIST_OPTIONS['request_auth_code'],
        ACTION_LIST_OPTIONS['send_auth_code'],
        ACTION_LIST_OPTIONS['change_auth_method'],
        ACTION_LIST_OPTIONS['user_auth_dashboard']]
REAUTH_CODE_FROM_APPLECOM_LOGIN = [
        ACTION_LIST_OPTIONS['send_auth_code'],
        ACTION_LIST_OPTIONS['goto_previous']]
CHANGE_AUTH_METHOD = [
        ACTION_LIST_OPTIONS['refresh_hwkey_names'],
        ACTION_LIST_OPTIONS['save']]
USER_AUTH_DASHBOARD = [
        ACTION_LIST_OPTIONS['refresh'],
        ACTION_LIST_OPTIONS['goto_previous']]

IMPORT_APPLE_DEVICES = [
        ACTION_LIST_OPTIONS['add_imported_apple_devices'],
        ACTION_LIST_OPTIONS['rtn_device_list'],
        ACTION_LIST_OPTIONS['rtn_apple_accounts'],
        ACTION_LIST_OPTIONS['menu']]

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

#------------------------–--------------------------------------------------------------

#------------------------–--------------------------------------------------------------
#   Parameter List Selections Items
DATA_SOURCE_OPTIONS = {
        'iCloud':   'APPLE ACCOUNT - Location data is provided for devices in the Family Sharing List',
        'MobApp':   'HA MOBILE APP - Location data and zone enter/exit triggers from devices with the Mobile App'
        }
REAUTH_AUTH_METHODS = {
        'push':     'Authentication Code popup window',
        'text':     'Text Message to `……{method_info}`',
        'hwkey':    'Security Key ({method_info})'
        }

# Apple Server Endpoint value - Add onto the Server URL in AppleAcct_ic3 if this starts with a period ('.')
APPLE_SERVER_LOCATION_OPTIONS = {
        'usa':       'USA/OTHER - The Apple Server is not located in China',
        '.cn':       'CHINA - The Apple Server is located in China (GCJ02)',
        '.cn,GCJ02': 'CHINA - The Apple Server is located in China (GCJ02 → WGS84)',
        '.cn,BD09':  'CHINA - The Apple Server is located in China (BD09 → WGS84)'
        }
DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS = {
        'reassign_devices': 'REASSIGN DEVICES → Search for another Apple Account with this device device and reassign it to that Apple Account. Set it to  Inactive if one is not found',
        'delete_devices':   'DELETE DEVICES → Delete all devices that are using this Apple Account',
        'set_devices_inactive': 'SET DEVICES TO INACTIVE →  Set the devices using this Apple Account to Inactive. They will be assigned to another Apple Account later'
        }
MOBAPP_DEVICE_NONE_OPTIONS = {
        'None': 'ⓧ The Mobile App is not installed on this device'
        }
PICTURE_NONE_KEY_TEXT = {
        'None': '📱 Icon - Display the Device’s Icon instead of a picture'
        }
DASHBOARD_MAIN_VIEW_STYLE_OPTIONS = [RESULT_SUMMARY, TRACK_DETAILS]
# The selector.cf_text.options log_zones_[key] texts
LOG_ZONES_FILE_NAMES = ['name-zone', 'name-device', 'name-device-zone', 'name-zone-device']
DASHBOARD_MAIN_VIEW_STYLES = {
        'result-summary': 'Result Summary',
        'track-details':  'Tracking Details',
        }
DASHBOARD_MAIN_VIEW_DEVICES_BASE = {
        'all-devices':    'All Devices',
        'iphone-first-2': 'First 2 iPhones',
        }
LOG_ZONES_KEY_TEXT = {
        '.hdr':             '⎯⎯⎯⎯⎯⎯ ACTIVITY FILE NAME ⎯⎯⎯⎯⎯⎯',
        'name-zone':        '⋙ Zone ([year]-[zone].csv) ',
        'name-device':      '⋙ Device ([year]-[device].csv)',
        'name-device-zone': '⋙ Device+Zone ([year]-[device]-[zone].csv)',
        'name-zone-device': '⋙ Zone+Device ([year]-[zone]-[device].csv)',
        }
AWAY_FROM_ZONE_OPTIONS = {
        'none': 'Not used',
        'all': 'All are Away and in the same Time Zone',
}
DATA_SOURCE_OPTIONS = ['iCloud,MobApp', 'iCloud', 'MobApp']
TRACKING_MODE_OPTIONS = ['track', 'monitor', 'inactive']
UNIT_OF_MEASUREMENT_OPTIONS = ['mi', 'km']
TIME_FORMAT_OPTIONS = ['12-hour', '24-hour']
TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT = [.25, .33, .50, .66, .75]
DISPLAY_ZONE_FORMAT_OPTIONS = {}
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
# The sensors that are always created. They are not on the Sensors screen, the section
# descriptions name them.
ALWAYS_CREATED_SENSORS = {
        'device':               ['badge', BATTERY],
        'tracking_update':      [NEXT_UPDATE],
        'tracking_time':        [TRAVEL_TIME, ARRIVAL_TIME],
        'tracking_distance':    [HOME_DISTANCE],
        'monitored_devices':    ['md_badge', 'md_battery'],
        }
USER_AUTH_RAW_YAML_DISPLAY_MODE = {
        'always':           'Always display the text/button entities on the Dashboard',
        'when_auth_needed': 'Only display text/button entities when an Authentication is needed'
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
APPLE_ACCT_USED_HEADER = (
        'Request location data from the devices in the Apple Account’s Family Sharing List')
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
