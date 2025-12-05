
from ..global_variables  import GlobalVariables as Gb
from ..const             import (NAME, BATTERY, WAZE_SERVERS_FNAME, )

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
MENU_PAGE_0_INITIAL_ITEM = 1
MENU_PAGE_TITLE = [
        'Devices & Sensors Menu',
        'Parameters Menu'
        ]
MENU_KEY_TEXT = {
        'data_source':          'APPLE ACCOUNTS & MOBILE APP > Add, Change and Delete Apple Accounts, Enable Monitoring the Mobile App ',
        'device_list':          'ICLOUD3 DEVICES  > Add, Change and Delete Tracked and Monitored Devices',
        'verification_code':    'AUTHENTICATE APPLE ACCT SIGN-IN > Send the 6-digit Verification Code to Apple for account access verification',
        'SK-verification_code':    'AUTHENTICATE APPLE ACCT SIGN-IN > Send the 6-digit Verification Code/Security Key Name to Apple for verification. Refresh expired codes/Security Key approval requests',
        'change_device_order':  'CHANGE DEVICE ORDER > Change the Event Log Device display and tracking update sequence',
        'sensors':              'SENSORS > Set Sensors created by iCloud3, Exclude Specific Sensors from being created',
        'dashboard_builder':    'DASHBOARD BUILDER > Build a Lovelace Dashboard to display device tracking information',
        'tools':                'TOOLS > Log Level, Delete Apple Acct & Device Assignment, Delete Apple Acct Cookie & iCloud3 Config files, Repair sensor ‘_2’ entity name errors, Restart HA & iCloud3',

        'away_time_zone':       'AWAY TIME ZONE > Select the displayed time zone for devices away from Home',
        'tracking_parameters':  'TRACKING PARAMETERS > Nearby Device Info, Accuracy Thresholds & Other Location Request Intervals',
        'format_settings':      'FIELD FORMATS & OTHER PARAMETERS > Zone Display & Device Tracker State formats, Unit of Measure/Time & Distance formats, Picture Dir Filters, Event Log Overrides, etc',
        'display_text_as':      'DISPLAY TEXT AS > Event Log Text Replacement',
        'waze':                 'WAZE ROUTE DISTANCE, TIME & HISTORY > Route Server and Parameters, Waze History Database Parameters and Controls',
        'special_zones':        'SPECIAL ZONES > Enter Zone Delay Time. Stationary Zone. Primary Track-from-Home Zone Override',
        'inzone_intervals':     'DEFAULT INZONE INTERVALS > inZone Interval assigned to new devices',

        'select':               'SELECT > Select the parameter update form',
        'next_page_0':          f'{MENU_PAGE_TITLE[0].upper()} > iCloud Account & Mobile App, iCloud3 Devices, Enter & Request Verification Code; Change Device Order; Sensors; Action Commands',
        'next_page_1':          f'{MENU_PAGE_TITLE[1].upper()} > Tracking Parameters, Field Formats & Directories, Display Text As, Waze Route Distance/Time & History, Special Zones, Default inZone Intervals',
        'exit':                 'EXIT AND RESTART ICLOUD3',
        'exit_update_dashboards': 'EXIT AND RESTART ICLOUD3 - UPDATE DASHBOARDS WITH DEVICE CHANGES'
}

MENU_KEY_TEXT_PAGE_0 = [
        MENU_KEY_TEXT['data_source'],
        MENU_KEY_TEXT['device_list'],
        MENU_KEY_TEXT['verification_code'],
        MENU_KEY_TEXT['sensors'],
        MENU_KEY_TEXT['dashboard_builder'],
        MENU_KEY_TEXT['tools'],
        ]
MENU_PAGE_1_INITIAL_ITEM = 0
MENU_KEY_TEXT_PAGE_1 = [
        MENU_KEY_TEXT['away_time_zone'],
        MENU_KEY_TEXT['tracking_parameters'],
        MENU_KEY_TEXT['format_settings'],
        MENU_KEY_TEXT['display_text_as'],
        MENU_KEY_TEXT['waze'],
        MENU_KEY_TEXT['special_zones'],
        # MENU_KEY_TEXT['inzone_intervals'],
        ]
MENU_ACTION_ITEMS = [
        MENU_KEY_TEXT['select'],
        MENU_KEY_TEXT['next_page_1'],
        MENU_KEY_TEXT['exit']
        ]

ACTION_LIST_OPTIONS = {
        'next_page_items':          'NEXT PAGE ITEMS > ^add-text^',
        'next_page':                'NEXT PAGE > Save changes. Display the next page',
        'next_page_devices':        'NEXT PAGE > Display devices ^add-text^',
        'next_page_waze':           'NEXT PAGE > Waze History Database parameters',
        'select_form':              'SELECT > Select the parameter update form',

        'update_apple_acct':        'SELECT APPLE ACCOUNT > Update the Username/Password of the selected Apple Account, Add a new Apple Account, Remove the Apple Account',
        'save_log_into_apple_acct': 'SAVE & LOG INTO APPLE ACCT > Save any configuration changes, Log into the Apple Account',
        'log_into_apple_acct':      'LOG INTO APPLE ACCT > Log into the Apple Account, Save any configuration changes',
        'stop_using_apple_acct':    'STOP USING AN APPLE ACCOUNT > Stop using an Apple Account, Remove it from the Apple Accounts list and all devices using it',
        'verification_code':        'AUTHENTICATE APPLE ACCT SIGN-IN > Send/Request the 6-digit Verification Code',
        'delete_apple_acct':        'DELETE APPLE ACCOUNT > Delete the selected Apple Account. Delete or reassign iCloud3 devices using it',
        'stop_login_retry':         'STOP RETRYING LOGIN > Stop retrying to log into the Apple Account',
        'data_source_parameters':   'OTHER APPLE ACCOUNT PARAMETERS > Set run time or other config parameters (China Apple Server Location)',

        'send_verification_code':   'SEND CODE TO APPLE TO AUTHENTICATE SIGN-IN > Send the Verification Code back to Apple to confirm access to the Apple Account',
        'SK-send_verification_code':   'SEND CODE/KEY TO APPLE TO AUTHENTICATE SIGN-IN > Send the Verification Code or Security Key being used back to Apple to confirm access to the Apple Account',
        'request_verification_code':'REQUEST NEW CODE > Display `Apple Acct Sign-in is Requested` window on a Trusted Device to get a new Code',
        'SK-request_verification_code':'REQUEST NEW CODE/REFRESH SECURITY KEY LIST > Display `Apple Acct Sign-in is Requested` window on a Trusted Device to get a new Code or to confirm using a Security Key',

        'X-send_verification_code':   'SEND VERIFICATION CODE > Send the Verification Code back to Apple to approve access to Apple Account',
        'X-request_verification_code':'REQUEST A VERIFICATION CODE > Reset Apple Account Interface and request a new Verification Code on a Trusted Device',
        'cancel_verification_entry':'CANCEL > Cancel the Verification Code Entry and Close this screen',
        'accept_terms_of_use':      'ACCEPT `TERMS OF USE` > Send `I Agree` to Apple updates to the `Terms of Use`',

        'update_device':            'SELECT THE DEVICE > Update the selected device, Add a new device to be tracked by iCloud3, Display more Devices on the next page',
        'add_device':               'ADD DEVICE > Continue to the `‘Update Devices`’ screen to finish setting up the new device',
        'delete_device':            'DELETE DEVICE > Delete the selected device',
        'change_device_order':      'CHANGE DEVICE ORDER > Change the tracking order of the Devices and their display sequence on the Event Log',
        'update_other_device_parameters': 'UPDATE OTHER DEVICE PARAMETERS > (^otp_msg)',

        'inactive_to_track':        'TRACK ALL OR SELECTED > Change the `Tracking Mode‘ of all of the devices (or the selected devices) from `Inactive‘ to `Tracked‘',
        'inactive_keep_inactive':   'DO NOT TRACK, KEEP INACTIVE > None of these devices should be `Tracked‘ and should remain `Inactive‘',

        'restart_ha':               'RESTART HOME ASSISTANT > Restart HA & iCloud3',
        'restart_icloud3':          'RESTART ICLOUD3 > Restart iCloud3 (Does not restart Home Assistant)',
        'restart_ic3_now':          'RESTART NOW > Restart iCloud3 now to load the updated configuration',
        'reload_icloud3':           'RELOAD ICLOUD3 ᐳ Reload & Restart iCloud3 (This does not load a new version)',
        'restart_ic3_later':        'RESTART LATER > The configuration changes have been saved. Load the updated configuration the next time iCloud3 is started',
        'review_inactive_devices':  'REVIEW INACTIVE DEVICES > Some Devices are `Inactive` and will not be located or tracked ^add-text^',

        'create_dashboard':         'CREATE/UPDATE A DASHBOARD > Erase and recreate an existing Dashboard, Create a new Dashboard',

        'select_text_as':           'SELECT > Update selected `Display Text As‘ field',
        'clear_text_as':            'CLEAR > Remove `Display Text As‘ entry',

        'exclude_sensors':          'EXCLUDE SENSORS > Select specific Sensors that should not be created',
        'filter_sensors':           'FILTER SENSORS > Select Sensors that should be displayed',
        'set_to_default_sensors':   'SET TO DEFAULT > Reset sensors to the default selection',

        'move_up':                  'MOVE UP > Move the Device up in the list',
        'move_down':                'MOVE DOWN > Move the Device down in the list',

        'cancel_goto_previous':     'RETURN > Return to the previous screen. Cancel any unsaved changes',
        'goto_previous':            'RETURN > Return to the previous screen',
        'cancel_goto_menu':         'MENU > Return to the Menu screen. Cancel any unsaved changes',
        'goto_menu':                'MENU > Return to the Menu screen',
        'cancel_goto_select_device': 'BACK TO DEVICE SELECTION > Return to the Device Selection screen. Cancel any unsaved changes',

        'exit':                     'EXIT > Exit the iCloud3 Configure Parameters Settings, Return to HA',
        'save':                     'SAVE > Update Configuration File, Return to the Previous screen',
        'save_stay':                'SAVE > Update Configuration File',

        'confirm_action_yes':       'YES > Complete the requested action',
        'confirm_return_no':        'NO  > Cancel the request',
        'confirm_save':             'SAVE THE CONFIGURATION CHANGES > Save any changes, then return to the Main Menu',

        "divider1": "═══════════════════════════════════════",
        "divider2": "═══════════════════════════════════════",
        "divider3": "═══════════════════════════════════════"
        }

ACTION_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in ACTION_LIST_OPTIONS.items()}

ACTION_LIST_ITEMS_BASE = [
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['cancel_goto_menu']
        ]

NONE_DICT_KEY_TEXT          = {'None': 'None'}
NONE_FAMSHR_DICT_KEY_TEXT   = {'None': 'None - Not using the Apple Acct iCloud Location Service'}
UNKNOWN_DEVICE_TEXT         = ' → UNKNOWN/NOT FOUND > NEEDS REVIEW'
SERVICE_NOT_AVAILABLE       = ' → This Data Source/Web Location Service is not available'
SERVICE_NOT_STARTED_YET     = ' → This Data Source/Web Location Svc has not finished starting. Exit and Retry.'
LOGGED_INTO_MSG_ACTION_LIST_IDX = 1     # Index number of the Action list item containing the username/password
APPLE_ACCOUNT_USERNAME_ACTION_LIST_IDX = 0     # Index number of the Action list item containing the username/password
APPLE_ACCOUNTS_MULTI_HDR = {'apple_acct_hdr': '═════════ Additional Apple Accounts ═════════'}
ADD = UNSELECTED = -1

# Action List Items for all screens
APPLE_ACCOUNT_ACTIONS = [
        ACTION_LIST_OPTIONS['update_apple_acct'],
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['data_source_parameters']]
APPLE_ACCOUNT_DELETE_ACTIONS = [
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['cancel_goto_previous']]
USERNAME_PASSWORD_ACTIONS = [
        ACTION_LIST_OPTIONS['save_log_into_apple_acct'],
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['verification_code'],
        ACTION_LIST_OPTIONS['cancel_goto_previous']]
REAUTH_CONFIG_FLOW_ACTIONS = [
        ACTION_LIST_OPTIONS['send_verification_code'],
        ACTION_LIST_OPTIONS['request_verification_code'],
        ACTION_LIST_OPTIONS['cancel_verification_entry']]
REAUTH_ACTIONS = [
        ACTION_LIST_OPTIONS['send_verification_code'],
        ACTION_LIST_OPTIONS['request_verification_code'],
        ACTION_LIST_OPTIONS['log_into_apple_acct'],
        ACTION_LIST_OPTIONS['goto_previous']]
DEVICE_LIST_ACTIONS = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['goto_menu']]
DEVICE_ADD_ACTIONS = [
        ACTION_LIST_OPTIONS['add_device'],
        ACTION_LIST_OPTIONS['cancel_goto_menu']]
DEVICE_LIST_ACTIONS_NO_ADD = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['goto_menu']]

REVIEW_INACTIVE_DEVICES =  [
        ACTION_LIST_OPTIONS['inactive_to_track'],
        ACTION_LIST_OPTIONS['goto_previous'],
        ACTION_LIST_OPTIONS['goto_menu']]
RESTART_NOW_LATER_ACTIONS = [
        ACTION_LIST_OPTIONS['restart_ha'],
        ACTION_LIST_OPTIONS['restart_icloud3'],
        ACTION_LIST_OPTIONS['restart_ic3_now'],
        ACTION_LIST_OPTIONS['restart_ic3_later'],
        ACTION_LIST_OPTIONS['review_inactive_devices']]
CONFIRM_ACTIONS =  [
        ACTION_LIST_OPTIONS['confirm_action_yes'],
        ACTION_LIST_OPTIONS['confirm_return_no']]
DASHBOARD_BUILDER_ACTIONS = [
        ACTION_LIST_OPTIONS['create_dashboard'],
        ACTION_LIST_OPTIONS['cancel_goto_menu']]
TOOL_LIST = {
        'reset_data_source':      'CLEAR DEVICE`S DATA SOURCE SELECTIONS > Erase the `Apple Acct Device` and `Mobile App Device` selection fields for all iCloud3 devices (Update iCloud3 Device screen)',
        'reset_tracking':         'REMOVE ALL APPLE ACCTS & DEVICES > Erase all Apple Accts (Apple Acct and Mobile App screen) and Erase all Devices (iCloud3 Devices screen)',
        'reset_general':          'RESET GENERAL CONFIGURATION PARAMETERS > Set the `General Parameters` to their default value (Other Parameter Menu screens). Sensors are reset on the Sensors screen.',
        'del_apple_acct_cookies': 'DELETE ALL APPLE/ICLOUD COOKIE FILES > Delete Apple Acct Cookie & Session files in the ‘.storage/icloud3.apple_acct’ directory, Restart HA',
        'del_icloud3_config_files': 'DELETE ALL ICLOUD3 CONFIGURATION FILES > Delete the iCloud3  Configuration files in the ‘.storage/icloud3’ directory. Apple Accts will be reverified.',
        'restart_ha_reload_icloud3': 'RESTART HA > Restart Home Assistant and iCloud3',
        'X-restart_ha_reload_icloud3': 'RESTART HA OR RELOAD ICLOUD3 > Restart Home Assistant, Reload current version of iCloud3',
        'fix_entity_name_error':  'REPAIR ‘_2’ SENSOR ENTITY NAME ERRORS > Rename ‘_2’ sensor entities back to the correct name without the ‘_2’ extension',
        'goto_menu':                 'MENU > Return to the Menu screen',
}
TOOL_LIST_ITEMS = [
        TOOL_LIST['reset_data_source'],
        TOOL_LIST['reset_tracking'],
        TOOL_LIST['reset_general'],
        TOOL_LIST['del_apple_acct_cookies'],
        TOOL_LIST['del_icloud3_config_files'],
        TOOL_LIST['restart_ha_reload_icloud3'],
        TOOL_LIST['fix_entity_name_error'],
        TOOL_LIST['goto_menu'],
]
TOOL_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in TOOL_LIST.items()}

#   Parameter List Selections Items
DATA_SOURCE_OPTIONS = {
        'iCloud':   'APPLE ACCOUNT - Location data is provided for devices in the Family Sharing List',
        'MobApp':   'HA MOBILE APP - Location data and zone enter/exit triggers from devices with the Mobile App'
        }

# Apple Server Endpoint value - Add onto the Server URL in AppleAcct_ic3 if this starts with a period ('.')
APPLE_SERVER_LOCATION_OPTIONS = {
        'usa':       'USA/OTHER - The Apple Server is not located in China',
        '.cn':       'CHINA - The Apple Server is located in China (GCJ02)',
        '.cn,GCJ02': 'CHINA - The Apple Server is located in China (GCJ02 → WGS84)',
        '.cn,BD09':  'CHINA - The Apple Server is located in China (BD09 → WGS84)'
        }
DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS = {
        'reassign_devices': 'REASSIGN DEVICES > Search for another Apple Account with this device device and reassign it to that Apple Account. Set it to  Inactive if one is not found',
        'delete_devices':   'DELETE DEVICES > Delete all devices that are using this Apple Account',
        'set_devices_inactive': 'SET DEVICES TO INACTIVE >  Set the devices using this Apple Account to Inactive. They will be assigned to another Apple Account later'
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
        'name-zone':        ' → [year]-[zone].csv',
        'name-device':      ' → [year]-[device].csv',
        'name-device-zone': ' → [year]-[device]-[zone].csv',
        'name-zone-device': ' → [year]-[zone]-[device].csv',
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

SENSORS_EXCLUDE_ACTIONS_= [
        ACTION_LIST_OPTIONS['filter_sensors'],
        ACTION_LIST_OPTIONS['save_stay'],
        ACTION_LIST_OPTIONS['cancel_goto_previous']]

CONF_SENSORS_DEFAULT = {
        BATTERY:            '_battery, _battery_status > Create Battery Level (65%) and Battery Status (Charging, Low, etc) (ALWAYS CREATED)',
        'arrival_time':     '_arrival_time > Home Zone arrival time based on Waze Travel time (ALWAYS CREATED)',
        'travel_time':      '_travel_time > Waze Travel time to Home or closest Track-from-Zone zone (ALWAYS CREATED)',
        'home_distance':    '_home_distance > Distance to the Home zone (ALWAYS CREATED)',
        'next_update':      '_next_update > Next time the location will be updated (ALWAYS CREATED)',
        }
CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT = {
        'md_badge':         '_badge > Badge sensor - A badge showing the Zone Name or distance from the Home zone. Attributes include location related information',
        'md_battery':       '_battery, battery_status > Create Battery (65%) and Battery Status (Charging, Low, etc) sensors (ALWAYS CREATED)',
        'md_location_sensors': 'Location related sensors > Name, zone, distance, travel_time, etc. (_name, _zone, _zone_fname, _zone_name, _zone_datetime, _home_distance, _travel_time, _travel_time_min, _last_located, _last_update)',
        }
CONF_SENSORS_DEVICE_KEY_TEXT = {
        NAME:               '_name > iCloud3 Device Name',
        'badge':            '_badge > A badge showing the Zone Name or distance from the Home zone',
        BATTERY:            '_battery, _battery_status > Create Battery Level (65%) and Battery Status (Charging, Low, etc) sensors (ALWAYS CREATED)',
        'info':             '_info > An information message containing status, alerts and errors related to device location updates, data accuracy, etc',
        }
CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT = {
        'interval':         '_interval > Time between location requests',
        'last_update':      '_last_update > Last time the location was updated',
        'next_update':      '_next_update > Next time the location will be updated (ALWAYS CREATED)',
        'last_located':     '_last_located > Last time the was located using iCloud or Mobile App location',
        }
CONF_SENSORS_TRACKING_TIME_KEY_TEXT = {
        'travel_time':      '_travel_time > Waze Travel time to Home or closest Track-from-Zone zone (ALWAYS CREATED)',
        'travel_time_min':  '_travel_time_min > Waze Travel time to Home or closest Track-from-Zone zone in minutes',
        'travel_time_hhmm': '_travel_time_hhmm > Waze Travel time to a Zone in hours:minutes',
        'arrival_time':     '_arrival_time > Home Zone arrival time based on Waze Travel time (ALWAYS CREATED)',
        }
CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT = {
        'home_distance':    '_home_distance > Distance to the Home zone (ALWAYS CREATED)',
        'zone_distance':    '_zone_distance > Distance to the Home or closest Track-from-Zone zone',
        'dir_of_travel':    '_dir_of_travel > Direction of Travel for the Home zone or closest Track-from-Zone zone (Towards, AwayFrom, inZone, etc)',
        'moved_distance':   '_moved_distance > Distance moved from the last location',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT = {
        'general_sensors':  'Include General Sensors (_zone_info)',
        'time_sensors':     'Include Travel Time Sensors (_travel_time, _travel_time_mins, _travel_time_hhmm, _arrival_time',
        'distance_sensors': 'Include Zone Distance Sensors (_zone_distance, _distance, _dir_of_travel)',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEYS = ['general_sensors', 'time_sensors', 'distance_sensors']
CONF_SENSORS_TRACKING_OTHER_KEY_TEXT = {
        'trigger':          '_trigger > Last action that triggered a location update',
        'waze_distance':    '_waze_distance > Waze distance from a TrackFrom zone',
        'calc_distance':    '_calc_distance > Calculated straight line distance from a TrackFrom zone',
        }
CONF_SENSORS_ZONE_KEY_TEXT = {
        'zone_fname':       '_zone_fname > HA Zone entity Friendly Name (HA Config > Areas & Zones > Zones > Name)',
        'zone':             '_zone > HA Zone entity_id (`the_shores`)',
        'zone_name':        '_zone_name > Reformat the Zone entity_id, capitalize and remove `_`s (`the_shores` → `TheShores`)',
        'zone_datetime':    '_zone_datetime > The time the Device entered the Zone',
        'last_zone':        '_last_zone_[...] > Create the same sensors for the device`s last HA Zone',
        }
CONF_SENSORS_OTHER_KEY_TEXT = {
        'gps_accuracy':     '_gps_accuracy > GPS acuracy of the last location coordinates',
        'vertical_accuracy':'_vertical_accuracy > Vertical (Elevation) Accuracy',
        'altitude':         '_altitude > Altitude/Elevation',
        }

ACTIONS_SCREEN_OPTIONS = {
        "divider1":         "═════════════ ICLOUD3 CONTROL ACTIONS ══════════════",
        "restart":          "RESTART > Restart iCloud3",
        "pause":            "PAUSE > Pause polling on all devices",
        "resume":           "RESUME > Resume Polling on all devices, Refresh all locations",
        "divider2":         "════════════════ DEBUG LOG ACTIONS ══════════════",
        "debug_start":      "START DEBUG LOGGING > Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING > Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING > Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING > Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS > Verify all debug log file records are written",
        "divider3":         "════════════════ OTHER COMMANDS ═══════════════",
        "evlog_export":     "EXPORT EVENT LOG > Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE > Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK > Load route locations for map display",
        "divider4":         "═══════════════════════════════════════════════",
        "restart_ha":       "RESTART HA, RESTART ICLOUD3 > Restart HA, Restart iCloud3",
        "return":           "MAIN MENU > Return to the Main Menu"
        }
ACTIONS_SCREEN_ITEMS_TEXT  = [text for text in ACTIONS_SCREEN_OPTIONS.values()]
ACTIONS_SCREEN_ITEMS_KEY_BY_TEXT = {text: key
                                for key, text in ACTIONS_SCREEN_OPTIONS.items()
                                if key.startswith('divider') is False}

ACTIONS_IC3_ITEMS = {
        "restart":          "RESTART > Restart iCloud3",
        "pause":            "PAUSE > Pause polling on all devices",
        "resume":           "RESUME > Resume Polling on all devices, Refresh all locations",
        }
ACTIONS_DEBUG_ITEMS = {
        "debug_start":      "START DEBUG LOGGING > Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING > Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING > Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING > Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS > Verify all debug log file records are written",
        }
ACTIONS_OTHER_ITEMS = {
        "evlog_export":     "EXPORT EVENT LOG > Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE > Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK > Load route locations for map display",
        }
ACTIONS_ACTION_ITEMS = {
        "restart_ha":       "RESTART HA AND ICLOUD3 > Restart HA and iCloud3",
        "return":           "MAIN MENU > Return to the Main Menu"
        }

# Section Headers used on various forms
MOBILE_APP_USED_HEADER = (
        'Monitor the Mobile App Integration devices location data and zone enter/exit triggers')
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
        "You may be driving through a non-tracked zone but not stopping at tne zone. The Mobile "
        "App issues an Enter Zone trigger when the device enters the zone and changes the "
        "device_tracker entity state to the Zone. iCloud3 does not process the Enter Zone "
        "trigger until the delay time has passed. This prevents processing a Zone Enter "
        "trig[er that is immediately followed by an Exit Zone trigger.")
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
        "Change the directory containing the Event Log Custom Card File (event-log-card.js). Set the `Gear` URL for the `HA Devices & Svcs > iCloud3 Config screen`")
DATA_SOURCE_ICLOUD_HDR = (
        "APPLE ACCOUNT > Location data is provided by devices in the Family Sharing list")
DATA_SOURCE_MOBAPP_HDR = (
        "HA MOBILE APP > Location data and zone Enter/Exit triggers are provided by the Mobile App")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
