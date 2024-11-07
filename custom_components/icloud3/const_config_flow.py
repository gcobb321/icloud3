
from .global_variables  import GlobalVariables as Gb
from .const             import (NAME, BATTERY, WAZE_SERVERS_FNAME, )

#----------------------------------------------------------------------------------------
MENU_PAGE_0_INITIAL_ITEM = 1
MENU_PAGE_TITLE = [
        'Menu > Configure Devices and Sensor Menu',
        'Menu > Configure Parameters Menu'
        ]
MENU_KEY_TEXT = {
        'data_source':          'DATA SOURCES > APPLE ACCOUNT & MOBILE APP ᐳ Select Location Data Sources; Apple Account Username/Password',
        'device_list':          'ICLOUD3 DEVICES  ᐳ Add, Change and Delete  Tracked and Monitored Devices',
        'verification_code':    'ENTER/REQUEST AN APPLE ACCOUNT VERIFICATION CODE ᐳ Enter or Request the 6-digit Apple Account Verification Code',
        'away_time_zone':       'AWAY TIME ZONE ᐳ Select the displayed time zone for devices away from Home',
        'change_device_order':  'CHANGE DEVICE ORDER ᐳ Change the Event Log Device display and tracking update sequence',
        'sensors':              'SENSORS ᐳ Set Sensors created by iCloud3; Exclude Specific Sensors from being created',
        'actions':              'ACTION COMMANDS ᐳ Restart/Pause/Resume Polling; Debug Logging; Export Event Log; Waze Utilities',

        'format_settings':      'FORMAT SETTINGS ᐳ Log Level; Zone Display Format; Device Tracker State; Unit of Measure; Time & Distance, Display GPS Coordinates',
        'display_text_as':      'DISPLAY TEXT AS ᐳ Event Log Text Replacement, etc',
        'waze':                 'WAZE ROUTE DISTANCE, TIME & HISTORY ᐳ Route Server and Parameters; Waze History Database Parameters and Controls',
        'inzone_intervals':     'INZONE INTERVALS ᐳ inZone Interval assigned to new devices',
        'special_zones':        'SPECIAL ZONES ᐳ Enter Zone Delay Time; Stationary Zone; Primary Track-from-Home Zone Override',
        'tracking_parameters':  'TRACKING & OTHER PARAMETERS ᐳ Set Nearby Device Info, Accuracy Thresholds & Other Location Request Intervals; Picture Image Directories; Event Log Custom Card Directory',

        'select':               'SELECT ᐳ Select the parameter update form',
        'next_page_0':          f'{MENU_PAGE_TITLE[0].upper()} ᐳ iCloud Account & Mobile App; iCloud3 Devices; Enter & Request Verification Code; Change Device Order; Sensors; Action Commands',
        'next_page_1':          f'{MENU_PAGE_TITLE[1].upper()} ᐳ Format Parameters; Display Text As; Waze Route Distance, Time & History; inZone Intervals; Special Zones;  Other Parameters',
        'exit':                 f'EXIT AND RESTART/RELOAD ICLOUD3 (Current version is v{Gb.version})'
}

MENU_KEY_TEXT_PAGE_0 = [
        MENU_KEY_TEXT['data_source'],
        MENU_KEY_TEXT['device_list'],
        MENU_KEY_TEXT['verification_code'],
        MENU_KEY_TEXT['away_time_zone'],
        MENU_KEY_TEXT['sensors'],
        MENU_KEY_TEXT['actions'],
        ]
MENU_PAGE_1_INITIAL_ITEM = 0
MENU_KEY_TEXT_PAGE_1 = [
        MENU_KEY_TEXT['format_settings'],
        MENU_KEY_TEXT['display_text_as'],
        MENU_KEY_TEXT['waze'],
        MENU_KEY_TEXT['special_zones'],
        MENU_KEY_TEXT['tracking_parameters'],
        MENU_KEY_TEXT['inzone_intervals'],
        ]
MENU_ACTION_ITEMS = [
        MENU_KEY_TEXT['select'],
        MENU_KEY_TEXT['next_page_1'],
        MENU_KEY_TEXT['exit']
        ]

ACTION_LIST_OPTIONS = {
        'next_page_items':          'NEXT PAGE ITEMS ᐳ ^info_field^',
        'next_page':                'NEXT PAGE ᐳ Save changes. Display the next page',
        'next_page_device':         'NEXT PAGE ᐳ Friendly Name, Track-from-Zones, Other Setup Fields',
        'next_page_waze':           'NEXT PAGE ᐳ Waze History Database parameters',
        'select_form':              'SELECT ᐳ Select the parameter update form',

        'update_apple_acct':        'SELECT APPLE ACCOUNT ᐳ Update the Username/Password of the selected Apple Account, Add a new Apple Account, Remove the Apple Account',
        'log_into_apple_acct':      'SAVE CHANGES & LOG INTO APPLE ACCT ᐳ Log into the Apple Account, Save any configuration changes',
        'stop_using_apple_acct':    'STOP USING AN APPLE ACCOUNT ᐳ Stop using an Apple Account, Remove it from the Apple Accounts list and all devices using it',
        'verification_code':        'ENTER/REQUEST AN APPLE ACCOUNT VERIFICATION CODE ᐳ Enter (or Request) the 6-digit Apple Account Verification Code',

        'delete_apple_acct':        'DELETE APPLE ACCOUNT ᐳ Delete the Apple Account. It will no longer be used as a data source',

        'send_verification_code':   'SEND THE VERIFICATION CODE TO APPLE ᐳ Send the 6-digit Apple Account Verification Code back to Apple to approve access to Apple Account',
        "request_verification_code":'REQUEST A NEW APPLE ACCOUNT VERIFICATION CODE ᐳ Reset Apple Account Interface and request a new Apple Account Verification Code',
        'cancel_verification_entry':'CANCEL ᐳ Cancel the Verification Code Entry and Close this screen',

        'update_device':            'SELECT THE DEVICE ᐳ Update the selected device, Add a new device to be tracked by iCloud3, Display more Devices on the next page',
        'add_device':               'ADD DEVICE ᐳ Add a device to be tracked by iCloud3',
        'delete_device':            'TOOLS - RESET DATA SOURCE(S), DELETE DEVICE(S) ᐳ Reset Apple Acct & Mobile App to `None`, Delete the device(s)',
        'change_device_order':      'CHANGE DEVICE ORDER ᐳ Change the tracking order of the Devices and their display sequence on the Event Log',

        'reset_this_device_data_source': 'RESET THIS DEVICE`S DATA SOURCE ᐳ Set Apple Acct & Mobile App to `None`',
        'delete_this_device':       'DELETE THIS DEVICE ᐳ Delete this device from the iCloud3 tracked devices list',
        'reset_all_devices_data_source': '⚠️ RESET ALL DEVICE`S DATA SOURCE ᐳ Set Apple Acct & Mobile App to `None`',
        'delete_all_devices':       '⚠️ DELETE ALL DEVICES ᐳ Delete all devices from the iCloud3 tracked devices list',
        'delete_device_cancel':     'CANCEL ᐳ Return to the Device List screen',

        'inactive_to_track':        'TRACK ALL OR SELECTED ᐳ Change the `Tracking Mode‘ of all of the devices (or the selected devices) from `Inactive‘ to `Tracked‘',
        'inactive_keep_inactive':   'DO NOT TRACK, KEEP INACTIVE ᐳ None of these devices should be `Tracked‘ and should remain `Inactive‘',

        'restart_ha':               'RESTART HOME ASSISTANT ᐳ Restart HA, Restart iCloud3',
        'restart_icloud3':          'RESTART ICLOUD3 ᐳ Restart iCloud3 (Does not restart Home Assistant)',
        'restart_ic3_now':          'RESTART NOW ᐳ Restart iCloud3 now to load the updated configuration',
        'restart_ic3_later':        'RESTART LATER ᐳ The configuration changes have been saved. Load the updated configuration the next time iCloud3 is started',
        'review_inactive_devices':  'REVIEW INACTIVE DEVICES ᐳ Some Devices are `Inactive` and will not be located or tracked',

        'select_text_as':           'SELECT ᐳ Update selected `Display Text As‘ field',
        'clear_text_as':            'CLEAR ᐳ Remove `Display Text As‘ entry',

        'exclude_sensors':          'EXCLUDE SENSORS ᐳ Select specific Sensors that should not be created',
        'filter_sensors':           'FILTER SENSORS ᐳ Select Sensors that should be displayed',

        'move_up':                  'MOVE UP ᐳ Move the Device up in the list',
        'move_down':                'MOVE DOWN ᐳ Move the Device down in the list',

        'save':                     'SAVE ᐳ Update Configuration File, Return to the Menu screen',
        'save_stay':                'SAVE ᐳ Update Configuration File',
        'return':                   'MENU ᐳ Return to the Menu screen',

        'cancel_return':            'RETURN ᐳ Return to the previous screen. Cancel any unsaved changes',
        'cancel':                   'MENU ᐳ Return to the Menu screen. Cancel any unsaved changes',
        'cancel_device_selection':  'BACK TO DEVICE SELECTION ᐳ Return to the Device Selection screen. Cancel any unsaved changes',
        'exit':                     'EXIT ᐳ Exit the iCloud3 Configurator',

        'confirm_return':           'NO, RETURN WITHOUT DOING ANYTHING ᐳ Cancel the request and return to the previous screen',
        'confirm_save':             'SAVE THE CONFIGURATION CHANGES ᐳ Save any changes, then return to the Main Menu',
        'confirm_action':           'YES, PERFORM THE REQUESTED ACTION ᐳ Complete the requested action and return to the previous screen',

        "divider1": "═══════════════════════════════════════",
        "divider2": "═══════════════════════════════════════",
        "divider3": "═══════════════════════════════════════"
        }

ACTION_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in ACTION_LIST_OPTIONS.items()}

ACTION_LIST_ITEMS_BASE = [
        ACTION_LIST_OPTIONS['save'],
        ACTION_LIST_OPTIONS['cancel']
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
ICLOUD_ACCOUNT_ACTIONS = [
        ACTION_LIST_OPTIONS['update_apple_acct']]
DELETE_APPLE_ACCT_ACTIONS = [
        ACTION_LIST_OPTIONS['delete_apple_acct'],
        ACTION_LIST_OPTIONS['cancel_return']]
USERNAME_PASSWORD_ACTIONS = [
        ACTION_LIST_OPTIONS['log_into_apple_acct'],
        ACTION_LIST_OPTIONS['stop_using_apple_acct'],
        ACTION_LIST_OPTIONS['verification_code'],
        ACTION_LIST_OPTIONS['cancel_return']]
REAUTH_CONFIG_FLOW_ACTIONS = [
        ACTION_LIST_OPTIONS['send_verification_code'],
        ACTION_LIST_OPTIONS['request_verification_code'],
        ACTION_LIST_OPTIONS['cancel_verification_entry']]
REAUTH_ACTIONS = [
        ACTION_LIST_OPTIONS['send_verification_code'],
        ACTION_LIST_OPTIONS['request_verification_code'],
        ACTION_LIST_OPTIONS['cancel_return']]
DEVICE_LIST_ACTIONS = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['return']]
DEVICE_LIST_ACTIONS_ADD = [
        ACTION_LIST_OPTIONS['add_device'],
        ACTION_LIST_OPTIONS['return']]
DEVICE_LIST_ACTIONS_EXCLUDE_SENSORS = [
        ACTION_LIST_OPTIONS['filter_sensors'],
        ACTION_LIST_OPTIONS['save_stay'],
        ACTION_LIST_OPTIONS['cancel_return']]
DEVICE_LIST_ACTIONS_NO_ADD = [
        ACTION_LIST_OPTIONS['update_device'],
        ACTION_LIST_OPTIONS['delete_device'],
        ACTION_LIST_OPTIONS['change_device_order'],
        ACTION_LIST_OPTIONS['return']]
DELETE_DEVICE_ACTIONS = [
        ACTION_LIST_OPTIONS['reset_this_device_data_source'],
        ACTION_LIST_OPTIONS['delete_this_device'],
        ACTION_LIST_OPTIONS['reset_all_devices_data_source'],
        ACTION_LIST_OPTIONS['delete_all_devices'],
        ACTION_LIST_OPTIONS['delete_device_cancel']]
REVIEW_INACTIVE_DEVICES =  [
        ACTION_LIST_OPTIONS['inactive_to_track'],
        ACTION_LIST_OPTIONS['inactive_keep_inactive']]
RESTART_NOW_LATER_ACTIONS = [
        ACTION_LIST_OPTIONS['restart_ha'],
        ACTION_LIST_OPTIONS['restart_icloud3'],
        ACTION_LIST_OPTIONS['restart_ic3_now'],
        ACTION_LIST_OPTIONS['restart_ic3_later'],
        ACTION_LIST_OPTIONS['review_inactive_devices']]
CONFIRM_ACTIONS =  [
        ACTION_LIST_OPTIONS['confirm_action'],
        ACTION_LIST_OPTIONS['confirm_return']]


#   Parameter List Selections Items
DATA_SOURCE_OPTIONS = {
        'iCloud':   'APPLE ACCOUNT - Location data is provided for devices in the Family Sharing List',
        'MobApp':   'HA MOBILE APP - Location data and zone enter/exit triggers from devices with the Mobile App'
        }
DELETE_APPLE_ACCT_DEVICE_ACTION_OPTIONS = {
        'reassign_devices': 'REASSIGN DEVICES ᐳ Search for another Apple Account with this device device and reassign it to that Apple Account. Set it to  Inactive if one is not found',
        'delete_devices':   'DELETE DEVICES ᐳ Delete all devices that are using this Apple Account',
        'set_devices_inactive': 'SET DEVICES TO INACTIVE ᐳ  Set the devices using this Apple Account to Inactive. They will be assigned to another Apple Account later'
        }
ICLOUD_SERVER_ENDPOINT_SUFFIX_OPTIONS = {
        'none':     'Use normal Apple iCloud Servers',
        'cn':       'China - Use Apple iCloud Servers located in China'
        }
MOBAPP_DEVICE_NONE_OPTIONS = {'None': 'None - The Mobile App is not installed on this device'}
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
        'fname':    'HA Zone Friendly Name (Home, Away, TheShores) →→→ PREFERRED',
        'zone':     'HA Zone entity_id (home, not_home, the_shores)',
        'name':     'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
        'title':    'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'
        }
DEVICE_TRACKER_STATE_SOURCE_OPTIONS = {
        'ic3_evlog': 'iCloud3 Zone - Use EvLog Zone Display Name (gps & accuracy) →→→ PREFERRED',
        'ic3_fname': 'iCloud3 Zone - Use Zone Friendly Name (gps & accuracy)',
        'ha_gps':    'HA Zone - Use gps coordinates to determine the zone (except Stationary Zones)'
}
LOG_LEVEL_OPTIONS = {
        'info':     'Info - Log General Information and Event Log messages',
        'debug':    'Debug - Info + Other Internal Tracking Monitors',
        'debug-ha': 'Debug (HALog) - Also add log records to the `home-assistant.log` file',
        'debug-auto-reset': 'Debug (AutoReset) - Debug logging that resets to Info at midnight',
        'rawdata':  'Rawdata - Debug + Raw Data (filtered) received from iCloud Location Servers',
        'rawdata-auto-reset':  'Rawdata (AutoReset) - RawData logging that resets to Info at midnight',
        'unfiltered':  'Rawdata (Unfiltered) - Raw Data (everything) received from iCloud Location Servers',
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

CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT = {
        'md_badge':         '_badge ᐳ Badge sensor - A badge showing the Zone Name or distance from the Home zone. Attributes include location related information',
        'md_battery':       '_battery, battery_status ᐳ Create Battery (65%) and Battery Status (Charging, Low, etc) sensors',
        'md_location_sensors': 'Location related sensors ᐳ Name, zone, distance, travel_time, etc. (_name, _zone, _zone_fname, _zone_name, _zone_datetime, _home_distance, _travel_time, _travel_time_min, _last_located, _last_update)',
        }
CONF_SENSORS_DEVICE_KEY_TEXT = {
        NAME:               '_name ᐳ iCloud3 Device Name',
        'badge':            '_badge ᐳ A badge showing the Zone Name or distance from the Home zone',
        BATTERY:            '_battery, _battery_status ᐳ Create Battery Level (65%) and Battery Status (Charging, Low, etc) sensors',
        'info':             '_info ᐳ An information message containing status, alerts and errors related to device location updates, data accuracy, etc',
        }
CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT = {
        'interval':         '_interval ᐳ Time between location requests',
        'last_update':      '_last_update ᐳ Last time the location was updated',
        'next_update':      '_next_update ᐳ Next time the location will be updated',
        'last_located':     '_last_located ᐳ Last time the was located using iCloud or Mobile App location',
        }
CONF_SENSORS_TRACKING_TIME_KEY_TEXT = {
        'travel_time':      '_travel_time ᐳ Waze Travel time to Home or closest Track-from-Zone zone',
        'travel_time_min':  '_travel_time_min ᐳ Waze Travel time to Home or closest Track-from-Zone zone in minutes',
        'travel_time_hhmm': '_travel_time_hhmm ᐳ Waze Travel time to a Zone in hours:minutes',
        'arrival_time':     '_arrival_time ᐳ Home Zone arrival time based on Waze Travel time',
        }
CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT = {
        'home_distance':    '_home_distance ᐳ Distance to the Home zone',
        'zone_distance':    '_zone_distance ᐳ Distance to the Home or closest Track-from-Zone zone',
        'dir_of_travel':    '_dir_of_travel ᐳ Direction of Travel for the Home zone or closest Track-from-Zone zone (Towards, AwayFrom, inZone, etc)',
        'moved_distance':   '_moved_distance ᐳ Distance moved from the last location',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT = {
        'general_sensors':  'Include General Sensors (_zone_info)',
        'time_sensors':     'Include Travel Time Sensors (_travel_time, _travel_time_mins, _travel_time_hhmm, _arrival_time',
        'distance_sensors': 'Include Zone Distance Sensors (_zone_distance, _distance, _dir_of_travel)',
        }
CONF_SENSORS_TRACK_FROM_ZONES_KEYS = ['general_sensors', 'time_sensors', 'distance_sensors']
CONF_SENSORS_TRACKING_OTHER_KEY_TEXT = {
        'trigger':          '_trigger ᐳ Last action that triggered a location update',
        'waze_distance':    '_waze_distance ᐳ Waze distance from a TrackFrom zone',
        'calc_distance':    '_calc_distance ᐳ Calculated straight line distance from a TrackFrom zone',
        }
CONF_SENSORS_ZONE_KEY_TEXT = {
        'zone_fname':       '_zone_fname ᐳ HA Zone entity Friendly Name (HA Config > Areas & Zones > Zones > Name)',
        'zone':             '_zone ᐳ HA Zone entity_id (`the_shores`)',
        'zone_name':        '_zone_name ᐳ Reformat the Zone entity_id, capitalize and remove `_`s (`the_shores` → `TheShores`)',
        'zone_datetime':    '_zone_datetime ᐳ The time the Device entered the Zone',
        'last_zone':        '_last_zone_[...] ᐳ Create the same sensors for the device`s last HA Zone',
        }
CONF_SENSORS_OTHER_KEY_TEXT = {
        'gps_accuracy':     '_gps_accuracy ᐳ GPS acuracy of the last location coordinates',
        'vertical_accuracy':'_vertical_accuracy ᐳ Vertical (Elevation) Accuracy',
        'altitude':         '_altitude ᐳ Altitude/Elevation',
        }

ACTIONS_SCREEN_OPTIONS = {
        "divider1":         "═════════════ ICLOUD3 CONTROL ACTIONS ══════════════",
        "restart":          "RESTART ᐳ Restart iCloud3",
        "pause":            "PAUSE ᐳ Pause polling on all devices",
        "resume":           "RESUME ᐳ Resume Polling on all devices, Refresh all locations",
        "divider2":         "════════════════ DEBUG LOG ACTIONS ══════════════",
        "debug_start":      "START DEBUG LOGGING ᐳ Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING ᐳ Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING ᐳ Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING ᐳ Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS ᐳ Verify all debug log file records are written",
        "divider3":         "════════════════ OTHER COMMANDS ═══════════════",
        "evlog_export":     "EXPORT EVENT LOG ᐳ Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE ᐳ Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK ᐳ Load route locations for map display",
        "divider4":         "═══════════════════════════════════════════════",
        "restart_ha":       "RESTART HA, RESTART ICLOUD3 ᐳ Restart HA, Restart iCloud3",
        "return":           "MAIN MENU ᐳ Return to the Main Menu"
        }
ACTIONS_SCREEN_ITEMS_TEXT  = [text for text in ACTIONS_SCREEN_OPTIONS.values()]
ACTIONS_SCREEN_ITEMS_KEY_BY_TEXT = {text: key
                                for key, text in ACTIONS_SCREEN_OPTIONS.items()
                                if key.startswith('divider') is False}

ACTIONS_IC3_ITEMS = {
        "restart":          "RESTART ᐳ Restart iCloud3",
        "pause":            "PAUSE ᐳ Pause polling on all devices",
        "resume":           "RESUME ᐳ Resume Polling on all devices, Refresh all locations",
}
ACTIONS_DEBUG_ITEMS = {
        "debug_start":      "START DEBUG LOGGING ᐳ Start or stop debug logging",
        "debug_stop":       "STOP DEBUG LOGGING ᐳ Start or stop debug logging",
        "rawdata_start":    "START RAWDATA LOGGING ᐳ Start or stop debug rawdata logging",
        "rawdata_stop":     "STOP RAWDATA LOGGING ᐳ Start or stop debug rawdata logging",
        "commit":           "COMMIT DEBUG LOG RECORDS ᐳ Verify all debug log file records are written",
}
ACTIONS_OTHER_ITEMS = {
        "evlog_export":     "EXPORT EVENT LOG ᐳ Export Event Log data",
        "wazehist_maint":   "WAZE HIST DATABASE ᐳ Recalc time/distance data at midnight",
        "wazehist_track":   "WAZE HIST MAP TRACK ᐳ Load route locations for map display",
}
ACTIONS_ACTION_ITEMS = {
        "restart_ha":       "RESTART HA, RELOAD ICLOUD3 ᐳ Restart HA or Reload iCloud3",
        "return":           "MAIN MENU ᐳ Return to the Main Menu"
}
RARELY_UPDATED_PARMS        = 'rarely_updated_parms'
RARELY_UPDATED_PARMS_HEADER = ("➤ RARELY USED PARAMETERS - Display inZone & Fixed Interval, Track-from-Zone and Track-from-Home Zone Override parameters the parameters")
WAZE_USED_HEADER =         ("The Waze Route Service provides the travel time and distance information from your "
                            "current location to the Home or another tracked from zone. This information is used to determine "
                            "when the next location request should be made")
WAZE_HISTORY_USED_HEADER = ("The Waze History Data base stores 'close to zone' travel time and distance information "
                            "for a GPS location (100m radius). It reduces the number of internet requests to the Waze Servers "
                            "after it has been in use for a while and speed up response time when in a poor cell area")
PASSTHRU_ZONE_HEADER =     ("You may be driving through a non-tracked zone but not stopping at tne zone. The Mobile "
                            "App issues an Enter Zone trigger when the device enters the zone and changes the "
                            "device_tracker entity state to the Zone. iCloud3 does not process the Enter Zone "
                            "trigger until the delay time has passed. This prevents processing a Zone Enter "
                            "trig[er that is immediately followed by an Exit Zone trigger.")
STAT_ZONE_HEADER =         ("A Stationary Zone is automatically created if the device remains in the same location "
                            "(store, friends house, doctor`s office, etc.) for an extended period of time")
TRK_FROM_HOME_ZONE_HEADER =("Normally, the Home zone is used as the primary track-from-zone for the tracking results "
                            "(travel time, distance, etc).  However, a different zone can be used as the base location "
                            "if you are away from Home for an extended period or the device is normally at another "
                            "location (vacation house, second home, parent's house, etc.). This is a global setting "
                            "that overrides the Primary Track-from-Home Zone assigned to an individual Device on the Update "
                            "Devices screen.")
DATA_SOURCE_ICLOUD_HDR =   ("APPLE ACCOUNT ᐳ Location data is provided by devices in the Family Sharing list")
DATA_SOURCE_MOBAPP_HDR =   ("HA MOBILE APP ᐳ Location data and zone Enter/Exit triggers are provided by the Mobile App")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
