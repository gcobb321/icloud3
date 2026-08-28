
from ..global_variables     import GlobalVariables as Gb
from ..const                import (NAME, BATTERY, WAZE_SERVERS_FNAME, )

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
NOT_LOGGED_IN  = 'NOT LOGGED IN'

DATA_ENTRY_ALERT_CHAR = '⛔'
DATA_ENTRY_ALERT      = f"      {DATA_ENTRY_ALERT_CHAR} "

#----------------------------------------------------------------------------------------
MENU_KEY_TEXT_PAGE_0 = {
        'apple_accounts':       'APPLE ACCOUNTS → Add, Change Delete and List Apple Accounts, Import Apple Devices into iCloud3',
        'reauth':               'AUTHENTICATE APPLE ACCT SIGN-IN → Authenticate Apple Account access, Request a new Auth Code, Change Authentication Method',
        'device_list':          'ICLOUD3 DEVICES → Add, Change, Delete and List Tracked and Monitored Devices, Import Apple Devices into iCloud3',
        'sensors':              'SENSORS → Select Sensors created by iCloud3 for all devices, Exclude Specific Sensors',
        'dashboard_builder':    'DASHBOARD BUILDER → Create a Dashboard that displays iCloud3 device sensor information from prebuilt templates',
        'tools':                'TOOLS → Log Level, Cleanup HA Registry Files, Cleanup/Reset iCloud3 Device Parameters, Apple Acct Cookies & iCloud3 Config File',
        'menu':                 '➤ MENU #2 (PARAMETERS) → Tracking, Sensor Display Parameters, Display Text As, Waze Route Service, Special Zones',
        'exit':                 '➤ EXIT → End the iCloud3 Configure Session',
}
MENU_KEY_TEXT_PAGE_1 = {
        'away_time_zone':       'AWAY TIME ZONE → Change the time displayed in the Event Log to the local time when away from Home',
        'tracking_parameters':  'TRACKING PARAMETERS →  Enable/disable the Mobile App data source, Configure how device location data is verified and displayed',
        'format_settings':      'DISPLAY SETTINGS & OTHER PARAMETERS → Specify how tracking results are displayed in the Event Log, sensors and device_tracker entities',
        'display_text_as':      'DISPLAY TEXT AS → Event Log Text Replacement',
        'waze':                 'WAZE ROUTE DISTANCE, TIME & HISTORY → Specify how the Waze Route Server is used and enable the Waze Tracking History Database',
        'special_zones':        'SPECIAL ZONES → Configure special zone handling - Delay zone enter triggers, Set up Stationary Zones for non-moving devices, Override the Home zone',
        'menu':                 '➤ MENU #1 (DEVICES & SENSORS) → Apple Account, iCloud3 Devices, Apple Acct Authentication, Sensors, Dashboard Builder, Maintenance Tools',
        'exit':                 '➤ EXIT → End the iCloud3 Configure Session',
}
MENU_EXIT_ITEMS = {
        'exit':                       '➤ EXIT → End the iCloud3 Configure Session',
        'exit_update_dashboards':     '➤ EXIT → End the iCloud3 Configure Session. Update the Dashboards and Restart',
        'exit_add_dev_trkrs_sensors': '➤ EXIT → End the iCloud3 Configure Session. Add new devices and sensors, Update the Dashboards and Restart'
}
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
        'clear_text_as':            'CLEAR → Remove `Display Text As‘ entry',

        'exclude_sensors':          'EXCLUDE SENSORS → Select specific Sensors that should not be created',
        'filter_sensors':           'FILTER SENSORS → Select Sensors that should be displayed',
        'set_to_default_sensors':   'SET TO DEFAULT → Reset sensors to the default selection',

        'move_up':                  'MOVE UP → Move the Device up in the list',
        'move_down':                'MOVE DOWN → Move the Device down in the list',

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
NONE_FAMSHR_DICT_KEY_TEXT   = {'None': 'Apple iCloud Location Service is not used'}
UNKNOWN_DEVICE_TEXT         = ' → UNKNOWN/NOT FOUND → NEEDS REVIEW'
SERVICE_NOT_AVAILABLE       = ' → This Data Source/Web Location Service is not available'
SERVICE_NOT_STARTED_YET     = ' → This Data Source/Web Location Svc has not finished starting. Exit and Retry.'
LOGGED_INTO_MSG_ACTION_LIST_IDX = 1     # Index number of the Action list item containing the username/password
APPLE_ACCOUNT_USERNAME_ACTION_LIST_IDX = 0     # Index number of the Action list item containing the username/password
APPLE_ACCOUNTS_MULTI_HDR = {'apple_acct_hdr': '═════════ Additional Apple Accounts ═════════'}
ADD = UNSELECTED = -1

# Action List Items for all screens
ACTION_LIST_ITEMS_BASE = [
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['menu']]

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
REAUTH_ACTIONS = [
        ACTION_LIST_OPTIONS['request_auth_code'],
        ACTION_LIST_OPTIONS['send_auth_code'],
        ACTION_LIST_OPTIONS['change_auth_method']]
        # ACTION_LIST_OPTIONS['auth_code_from_applecom_login']]
REAUTH_CODE_FROM_APPLECOM_LOGIN = [
        ACTION_LIST_OPTIONS['send_auth_code'],
        ACTION_LIST_OPTIONS['goto_previous']]
CHANGE_AUTH_METHOD = [
        ACTION_LIST_OPTIONS['refresh_hwkey_names'],
        ACTION_LIST_OPTIONS['save']]

DEVICE_LIST_ACTIONS = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['import_apple_devices'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['menu']]
DEVICE_UPDATE_ACTIONS = [
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['rtn_device_list'],
        ACTION_LIST_OPTIONS['menu']]
DEVICE_ADD_ACTIONS = [
        ACTION_LIST_OPTIONS['add_device'],
        ACTION_LIST_OPTIONS['rtn_device_list']]
IMPORT_APPLE_DEVICES = [
        ACTION_LIST_OPTIONS['add_imported_apple_devices'],
        ACTION_LIST_OPTIONS['rtn_device_list'],
        ACTION_LIST_OPTIONS['rtn_apple_accounts'],
        ACTION_LIST_OPTIONS['menu']]
DEVICE_LIST_ACTIONS_NO_ADD = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['menu']]
CHANGE_DEVICE_ORDER = [
        ACTION_LIST_OPTIONS['move_up'],
        ACTION_LIST_OPTIONS['move_down'],
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['rtn_device_list']
]
SENSORS_ACTIONS = [
        ACTION_LIST_OPTIONS['exclude_sensors'],
        ACTION_LIST_OPTIONS['set_to_default_sensors'],
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['menu']]
SENSORS_EXCLUDE_ACTIONS_= [
        ACTION_LIST_OPTIONS['filter_sensors'],
        ACTION_LIST_OPTIONS['update_sensor_list'],
        ACTION_LIST_OPTIONS['return_to_sensor_screen']]

REVIEW_INACTIVE_DEVICES = [
        ACTION_LIST_OPTIONS['update_tracking_mode']]
        # ACTION_LIST_OPTIONS['rtn_device_list']]
        # ACTION_LIST_OPTIONS['menu']]
        # ACTION_LIST_OPTIONS['exit'],

EXIT_ICLOUD3_CONFIGURE_SETTINGS = [
        ACTION_LIST_OPTIONS['review_inactive_devices'],
        ACTION_LIST_OPTIONS['menu'],
        ACTION_LIST_OPTIONS['exit']]

CONFIRM_ACTIONS = [
        ACTION_LIST_OPTIONS['confirm_action_yes'],
        ACTION_LIST_OPTIONS['confirm_action_no']]
DASHBOARD_BUILDER_ACTIONS = [
        ACTION_LIST_OPTIONS['create_dashboard'],
        ACTION_LIST_OPTIONS['cancel_goto_menu']]
CLEANUP_ENTITY_REGISTRY = [
        # ACTION_LIST_OPTIONS['check_all'],
        # ACTION_LIST_OPTIONS['check_none'],
        # ACTION_LIST_OPTIONS['show_all_sensors'],
        # ACTION_LIST_OPTIONS['show_some_sensors'],
        ACTION_LIST_OPTIONS['delete_device_sensors'],
        ACTION_LIST_OPTIONS['goto_previous']]

TOOL_LIST = {
        'log_level':                 ' CHANGE THE LOG LEVEL → Change the current log level (info, debug, rawdata)',
        'cleanup_entity_registry':   'CLEANUP HA ENTITY REGISTRY → Extract and Delete iCloud3  Entity Registry Devices and Sensors',
        'restart_icloud3':           'RESTART ICLOUD3 → Restart iCloud3 Now (Reloads the current version of iCloud3)',
        'reset_data_source':         'CLEAR DEVICE`S DATA SOURCE SELECTIONS → Erase the `Apple Acct Device` and `Mobile App Device` selection fields for all iCloud3 devices (Update iCloud3 Device screen)',
        'reset_tracking':            'REMOVE ALL APPLE ACCTS & DEVICES → Erase all Apple Accts (Apple Acct and Mobile App screen) and Erase all Devices (iCloud3 Devices screen)',
        'reset_general':             'RESET GENERAL CONFIGURATION PARAMETERS → Set the `General Parameters` to their default value (Other Parameter Menu screens). Sensors are reset on the Sensors screen.',
        'del_apple_acct_cookies':    'DELETE ALL APPLE/ICLOUD COOKIE FILES → Delete Apple Acct Cookie & Session files in the ‘.storage/icloud3.apple_acct’ directory, Restart HA',
        'del_icloud3_config_files':  'DELETE ALL ICLOUD3 CONFIGURATION FILES → Delete the iCloud3  Configuration files in the ‘.storage/icloud3’ directory. Apple Accts will be reverified.',
        'menu':                      ACTION_LIST_OPTIONS['menu']
}
TOOL_LIST_ITEMS = [
        TOOL_LIST['log_level'],
        TOOL_LIST['cleanup_entity_registry'],
        TOOL_LIST['restart_icloud3'],
        TOOL_LIST['reset_data_source'],
        TOOL_LIST['reset_tracking'],
        TOOL_LIST['reset_general'],
        TOOL_LIST['del_apple_acct_cookies'],
        TOOL_LIST['del_icloud3_config_files'],
        ACTION_LIST_OPTIONS['menu'],
]
LOG_LEVEL = [
        ACTION_LIST_OPTIONS['save_menu'],
        ACTION_LIST_OPTIONS['menu'],
]
TOOL_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in TOOL_LIST.items()}


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
        'None': 'None - The Mobile App is not installed on this device'
        }
PICTURE_NONE_KEY_TEXT = {
        'None': 'None - Display the Device’s Icon instead of a picture'
        }
DASHBOARD_MAIN_VIEW_STYLE_OPTIONS = {
        'result-summary': 'Result Summary - Show Arrival Time, Distance Travel Time, Battery Info',
        'track-details':  'Tracking Details - Show all results of a location update',
        }
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
        'all': 'All are Away and in the same Time Zone'}
DATA_SOURCE_OPTIONS = {
        'iCloud,MobApp': 'ICLOUD & MOBILE APP → Request data from iCloud and the Mobile App',
        'iCloud':        'ICLOUD ONLY → Mobile App is not used',
        'MobApp':        'MOBILE APP ONLY → iCloud Location Services is not used'
}
TRACKING_MODE_OPTIONS = {
        'track':    'Track - Request Location and track the device',
        'monitor':  'Monitor - Report location only when another tracked device is updated',
        'inactive': 'INACTIVE - Device is inactive and will not be tracked'
        }
UNIT_OF_MEASUREMENT_OPTIONS = {
        'mi':       'Imperial (mi, ft)',
        'km':       'Metric (km, m)'
        }
TIME_FORMAT_OPTIONS = {
        '12-hour':  '12-hour Time Format (9:05:30a, 4:40:15p)',
        '24-hour':  '24-hour Time Format (09:05:30, 16:40:15)'
        }
TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT = {
        .25:  'Shortest Interval Time - 1/4 TravelTime (¼ × 8 mins = Next Locate in 2m)',
        .33:  'Shorter Interval Time - 1/3 TravelTime (⅓ × 8 mins = Next Locate in 2m40s)',
        .50:  'Half Way (Default) - 1/2 TravelTime (½ × 8 mins = Next Locate in 4m)',
        .66:  'Longer Interval Time - 2/3 TravelTime (⅔ × 8 mins = Next Locate in 5m20s',
        .75:  'Longest Interval Time - 3/4 TravelTime (¾ × 8 mins = Next Locate in 6m)'
        }
DISPLAY_ZONE_FORMAT_OPTIONS = {}
DISPLAY_ZONE_FORMAT_OPTIONS_BASE = {
        'fname':    'HA Zone Friendly Name (Home, Away, TheShores) → PREFERRED',
        'zone':     'HA Zone entity_id (home, not_home, the_shores)',
        'name':     'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
        'title':    'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'
        }
DEVICE_TRACKER_STATE_SOURCE_OPTIONS = {
        'ic3_evlog': 'iCloud3 Zone - EventLog Zone Display Name (GPS+accuracy) → PREFERRED',
        'ic3_fname': 'iCloud3 Zone - Zone Friendly Name (GPS+accuracy)',
        'ha_gps':    'HA Zone - GPS coordinates will determine the zone (except Stationary Zones)'
        }
LOG_LEVEL_OPTIONS = {
        'info':     'Info - Log General Information and Event Log messages',
        'debug':    'Debug - Info + Other Internal Tracking Monitors',
        'debug-ha': 'Debug (HALog) - Also add log records to the `home-assistant.log` file',
        'debug-auto-reset': 'Debug (AutoReset) - Debug logging that resets to Info at midnight',
        'rawdata':  'Rawdata - Debug + Device Data (filtered) received from iCloud Location Servers',
        'rawdata-auto-reset':  'Rawdata (AutoReset) - RawData logging that resets to Info at midnight',
        'unfiltered':  'Rawdata (Unfiltered) - Device Data fields (everything) received from iCloud Location Servers',
        }
DISTANCE_METHOD_OPTIONS = {
        'waze':     'Waze - Waze Route Service provides travel time & distance information',
        'calc':     'Calc - Distance is calculated using a `straight line` formula'
        }
WAZE_SERVER_OPTIONS = {
        'us':       WAZE_SERVERS_FNAME['us'],
        'il':       WAZE_SERVERS_FNAME['il'],
        'row':      WAZE_SERVERS_FNAME['row']
        }
WAZE_HISTORY_TRACK_DIRECTION_OPTIONS = {
        'north_south':      'North-South - You generally travel in North-to-South direction',
        'east_west':        'East-West - You generally travel in East-West direction'
        }
CONF_SENSORS_DEFAULT = {
        BATTERY:            '_battery, _battery_status → Create Battery Level (65%) and Battery Status (Charging, Low, etc) (ALWAYS CREATED)',
        'arrival_time':     '_arrival_time → Home Zone arrival time based on Waze Travel time (ALWAYS CREATED)',
        'travel_time':      '_travel_time → Waze Travel time to Home or closest Track-from-Zone zone (ALWAYS CREATED)',
        'home_distance':    '_home_distance → Distance to the Home zone (ALWAYS CREATED)',
        'next_update':      '_next_update → Next time the location will be updated (ALWAYS CREATED)',
        }
CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT = {
        'md_badge':         '_badge → Badge sensor - A badge showing the Zone Name or distance from the Home zone. Attributes include location related information',
        'md_battery':       '_battery, battery_status → Create Battery (65%) and Battery Status (Charging, Low, etc) sensors (ALWAYS CREATED)',
        'md_location_sensors': 'Location related sensors → Name, zone, distance, travel_time, etc. (_name, _zone, _zone_fname, _zone_name, _zone_datetime, _home_distance, _travel_time, _travel_time_min, _last_located, _last_update)',
        }
CONF_SENSORS_DEVICE_KEY_TEXT = {
        NAME:               '_name → iCloud3 Device Name',
        'badge':            '_badge → A badge showing the Zone Name or distance from the Home zone',
        BATTERY:            '_battery, _battery_status → Create Battery Level (65%) and Battery Status (Charging, Low, etc) sensors (ALWAYS CREATED)',
        'info':             '_info → An information message containing status, alerts and errors related to device location updates, data accuracy, etc',
        }
CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT = {
        'interval':         '_interval → Time between location requests',
        'last_update':      '_last_update → Last time the location was updated',
        'next_update':      '_next_update → Next time the location will be updated (ALWAYS CREATED)',
        'last_located':     '_last_located → Last time the was located using iCloud or Mobile App location',
        }
CONF_SENSORS_TRACKING_TIME_KEY_TEXT = {
        'travel_time':      '_travel_time → Waze Travel time to Home or closest Track-from-Zone zone (ALWAYS CREATED)',
        'travel_time_min':  '_travel_time_min → Waze Travel time to Home or closest Track-from-Zone zone in minutes',
        'travel_time_hhmm': '_travel_time_hhmm → Waze Travel time to a Zone in hours:minutes',
        'arrival_time':     '_arrival_time → Home Zone arrival time based on Waze Travel time (ALWAYS CREATED)',
        }
CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT = {
        'home_distance':    '_home_distance → Distance to the Home zone (ALWAYS CREATED)',
        'zone_distance':    '_zone_distance → Distance to the Home or closest Track-from-Zone zone',
        'dir_of_travel':    '_dir_of_travel → Direction of Travel for the Home zone or closest Track-from-Zone zone (Towards, AwayFrom, inZone, etc)',
        'moved_distance':   '_moved_distance → Distance moved from the last location',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT = {
        'general_sensors':  'Include General Sensors (_zone_info)',
        'time_sensors':     'Include Travel Time Sensors (_travel_time, _travel_time_mins, _travel_time_hhmm, _arrival_time',
        'distance_sensors': 'Include Zone Distance Sensors (_zone_distance, _distance, _dir_of_travel)',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEYS = ['general_sensors', 'time_sensors', 'distance_sensors']
CONF_SENSORS_TRACKING_OTHER_KEY_TEXT = {
        'trigger':          '_trigger → Last action that triggered a location update',
        'waze_distance':    '_waze_distance → Waze distance from a TrackFrom zone',
        'calc_distance':    '_calc_distance → Calculated straight line distance from a TrackFrom zone',
        }
CONF_SENSORS_ZONE_KEY_TEXT = {
        'zone_fname':       '_zone_fname → HA Zone Name (`Home`, `The Shores`) → From: HA Config → Areas & Zones → Zones → Name field',
        'zone':             '_zone → HA Zone entity_id (`home`, `the_shores`)',
        'zone_name':        '_zone_name → Reformat the Zone entity_id, capitalize and remove `_`s (`Home`, `TheShores`)',
        'zone_datetime':    '_zone_datetime → The time the Device entered the Zone',
        'last_zone':        '_last_zone_[...] → Create the same sensors for the device`s last HA Zone',
        }
CONF_SENSORS_OTHER_KEY_TEXT = {
        'gps_accuracy':     '_gps_accuracy → GPS acuracy of the last location coordinates',
        'vertical_accuracy':'_vertical_accuracy → Vertical (Elevation) Accuracy',
        'altitude':         '_altitude → Altitude/Elevation',
        }

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
        'Request location data from the devices in the Apple Account`s Family Sharing List')
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
        "(store, friends house, doctor`s office, etc.) for an extended period of time")
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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→→
