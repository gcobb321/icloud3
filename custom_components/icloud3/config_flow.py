import os
import time

from homeassistant                  import config_entries, data_entry_flow
from homeassistant.config_entries   import ConfigEntry as config_entry
from homeassistant.data_entry_flow  import FlowHandler, FlowResult
from homeassistant.core             import callback, HomeAssistant
from homeassistant.util             import slugify
from homeassistant.helpers          import (selector, entity_registry as er, device_registry as dr,
                                            area_registry as ar,)

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol




from .global_variables  import GlobalVariables as Gb
from .const             import (DOMAIN, ICLOUD3, DATETIME_FORMAT,
                                RARROW, RARROW2, CRLF_DOT, DOT, HDOT, CIRCLE_STAR, YELLOW_ALERT, RED_ALERT,
                                EVLOG_NOTICE, EVLOG_ALERT,
                                IPHONE_FNAME, IPHONE, IPAD, WATCH, AIRPODS, ICLOUD, FAMSHR, FMF, OTHER, HOME,
                                DEVICE_TYPES, DEVICE_TYPE_FNAME, DEVICE_TRACKER_DOT,
                                MOBAPP, NO_MOBAPP, APPLE_SPECIAL_ICLOUD_SERVER_COUNTRY_CODE,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE,
                                NAME,  FRIENDLY_NAME, FNAME, TITLE, BATTERY,
                                ZONE, HOME_DISTANCE, WAZE_SERVERS_FNAME,
                                PICTURE_WWW_STANDARD_DIRS, CONF_PICTURE_WWW_DIRS,
                                CONF_VERSION, CONF_EVLOG_CARD_DIRECTORY,
                                CONF_EVLOG_BTNCONFIG_URL,
                                CONF_USERNAME, CONF_PASSWORD, CONF_DEVICES, CONF_SETUP_ICLOUD_SESSION_EARLY,
                                CONF_DATA_SOURCE, CONF_VERIFICATION_CODE,
                                CONF_TRACK_FROM_ZONES,
                                CONF_TRACK_FROM_BASE_ZONE_USED, CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_HOME_ZONE,
                                CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX, CONF_LOG_ZONES,
                                CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVALS,
                                CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME, CONF_FAMSHR_DEVICE_ID,
                                CONF_UNIT_OF_MEASUREMENT, CONF_TIME_FORMAT,
                                CONF_MAX_INTERVAL, CONF_OFFLINE_INTERVAL, CONF_EXIT_ZONE_INTERVAL, CONF_MOBAPP_ALIVE_INTERVAL,
                                CONF_GPS_ACCURACY_THRESHOLD, CONF_OLD_LOCATION_THRESHOLD, CONF_OLD_LOCATION_ADJUSTMENT,
                                CONF_TRAVEL_TIME_FACTOR, CONF_TFZ_TRACKING_MAX_DISTANCE,
                                CONF_PASSTHRU_ZONE_TIME, CONF_LOG_LEVEL, CONF_LOG_LEVEL_DEVICES,
                                CONF_DISPLAY_ZONE_FORMAT, CONF_DEVICE_TRACKER_STATE_SOURCE, CONF_DISPLAY_GPS_LAT_LONG,
                                CONF_CENTER_IN_ZONE, CONF_DISCARD_POOR_GPS_INZONE,
                                CONF_DISTANCE_BETWEEN_DEVICES,
                                CONF_WAZE_USED, CONF_WAZE_SERVER, CONF_WAZE_MAX_DISTANCE, CONF_WAZE_MIN_DISTANCE,
                                CONF_WAZE_REALTIME, CONF_WAZE_HISTORY_DATABASE_USED, CONF_WAZE_HISTORY_MAX_DISTANCE,
                                CONF_WAZE_HISTORY_TRACK_DIRECTION,

                                CONF_STAT_ZONE_FNAME, CONF_STAT_ZONE_STILL_TIME, CONF_STAT_ZONE_INZONE_INTERVAL,
                                CONF_STAT_ZONE_BASE_LATITUDE,
                                CONF_STAT_ZONE_BASE_LONGITUDE, CONF_DISPLAY_TEXT_AS,
                                CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME, CONF_MOBILE_APP_DEVICE, CONF_FMF_EMAIL,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES,
                                CONF_SENSORS_MONITORED_DEVICES,
                                CONF_SENSORS_DEVICE,
                                CONF_SENSORS_TRACKING_UPDATE, CONF_SENSORS_TRACKING_TIME, CONF_SENSORS_TRACKING_DISTANCE,
                                CONF_SENSORS_TRACK_FROM_ZONES, CONF_SENSORS_TRACKING_OTHER, CONF_SENSORS_ZONE,
                                CONF_SENSORS_OTHER, CONF_EXCLUDED_SENSORS,
                                CONF_PARAMETER_TIME_STR, CONF_PARAMETER_FLOAT,
                                CF_PROFILE, CF_DATA_TRACKING, CF_DATA_GENERAL,
                                DEFAULT_DEVICE_CONF, DEFAULT_GENERAL_CONF,
                                DEFAULT_DEVICE_REINITIALIZE_CONF,
                                )
from .const_sensor      import (SENSOR_GROUPS )
from .helpers.common    import (instr, isnumber, obscure_field, list_to_str, str_to_list,
                                is_statzone, zone_dname, isbetween, list_del, list_add,
                                sort_dict_by_values, )
from .helpers.messaging import (log_exception, log_debug_msg, log_info_msg,
                                _traceha, _trace,
                                post_event, post_monitor_msg, )
from .helpers           import entity_io
from .                  import sensor as ic3_sensor
from .                  import device_tracker as ic3_device_tracker
from .support           import start_ic3
from .support           import config_file
from .support           import service_handler
from .support           import pyicloud_ic3_interface
from .support.v2v3_config_migration import iCloud3_v2v3ConfigMigration
from .support.pyicloud_ic3  import (PyiCloudService, PyiCloudException, PyiCloudFailedLoginException,
                                    PyiCloudServiceNotActivatedException, PyiCloudNoDevicesException, )
import logging
_CF_LOGGER = logging.getLogger("icloud3-cf")
DATA_ENTRY_ALERT_CHAR = '⛔'
DATA_ENTRY_ALERT      = f"      {DATA_ENTRY_ALERT_CHAR} "
DEVICE_NON_TRACKING_FIELDS =   [CONF_FNAME, CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                CONF_FIXED_INTERVAL, CONF_LOG_ZONES,
                                CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES]

#-----------------------------------------------------------------------------------------
def dict_value_to_list(key_value_dict):
    """ Make a drop down list from a list  """

    if type(key_value_dict) is dict:
        value_list = [v for v in key_value_dict.values() if v.startswith('.') is False]
    else:
        value_list = list(key_value_dict)

    return value_list

#-----------------------------------------------------------------------------------------
def ensure_six_item_list(list_item):
    for i in range(6 - len(list_item)):
        list_item.append('.')

    return list_item

#-----------------------------------------------------------------------------------------
def ensure_six_item_dict(dict_item):
    dummy_key = ''
    for i in range(6 - len(dict_item)):
        dummy_key += '.'
        dict_item[dummy_key] = '.'

    return dict_item

#-----------------------------------------------------------------------------------------
MENU_PAGE_0_INITIAL_ITEM = 1
MENU_PAGE_TITLE = [
    'Menu > Configure Devices and Sensor Menu',
    'Menu > Configure Parameters Menu'
    ]
MENU_KEY_TEXT = {
        'icloud_account':       'iCLOUD ACCOUNT & MOBILE APP ᐳ •Set iCloud Account Username/Password, •Set Location Data Sources',
        'device_list':          'ICLOUD3 DEVICES  ᐳ •Add, Change and Delete tracked and monitored devices',
        'verification_code':    'ENTER/REQUEST AN APPLE ID VERIFICATION CODE ᐳ •Enter or Request the 6-digit Apple ID Verification Code',
        'away_time_zone':       'AWAY TIME ZONE ᐳ •Select the time zone used to display time based tracking events for a device when in another time zone',
        'change_device_order':  'CHANGE DEVICE ORDER ᐳ •Change the tracking order of the Devices and their display sequence on the Event Log',
        'sensors':              'SENSORS ᐳ •Set Sensors created by iCloud3, •Exclude Specific Sensors from being created',
        'actions':              'ACTION COMMANDS ᐳ •Restart/Pause/Resume Polling, •Debug Logging, •Export Event Log, •Waze Utilities',

        'format_settings':      'FORMAT SETTINGS ᐳ •Log Level, •Zones Display Format, •DeviceTracker State, •Unit of Measure, •Time & Distance, Display GPS Coordinates',
        'display_text_as':      'DISPLAY TEXT AS ᐳ •Event Log Custom Card Text Replacement',
        'waze':                 'WAZE ROUTE DISTANCE, TIME & HISTORY ᐳ •Set Route Server Location, Min/Max Intervals, etc. •Set Waze History Database Parameters and Controls',
        'inzone_intervals':     'INZONE DEFAULT INTERVALS ᐳ •Default inZone intervals for different device types and the Mobile App, •Other inZone Controls ',
        'special_zones':        'SPECIAL ZONES ᐳ •Enter Zone Delay, •Stationary Zone, •Primary Track-from-Home Zone Override',
        'tracking_parameters':  'TRACKING & OTHER PARAMETERS ᐳ •Set Nearby Device Info, Accuracy Thresholds & Other Location Request Intervals, •Picture Image Directories, •Event Log Custom Card Directory, etc.',

        'select':               'SELECT ᐳ Select the parameter update form',
        'next_page_0':          f'{MENU_PAGE_TITLE[0].upper()} ᐳ •iCloud Account & Mobile App, •iCloud3 Devices, •Enter & Request Verification Code, •Change Device Order, •Sensors, •Action Commands',
        'next_page_1':          f'{MENU_PAGE_TITLE[1].upper()} ᐳ •Format Parameters, •Display Text As, •Waze Route Distance, Time & History, •inZone Intervals, •Special Zones, • Other Parameters',
        'exit':                 f'EXIT AND RESTART ICLOUD3 v{Gb.version}'
}

MENU_KEY_TEXT_PAGE_0 = [
    MENU_KEY_TEXT['icloud_account'],
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

ACTION_LIST_ITEMS_KEY_TEXT = {
        'next_page_items':          'NEXT PAGE ITEMS ᐳ ^info_field^',
        'next_page':                'NEXT PAGE ᐳ Save changes. Display the next page',
        'next_page_device':         'NEXT PAGE ᐳ Friendly Name, Track-from-Zones, Other Setup Fields',
        'next_page_waze':           'NEXT PAGE ᐳ Waze History Database parameters',
        'select_form':              'SELECT ᐳ Select the parameter update form',

        'login_icloud_account':     'LOG INTO AN ICLOUD ACCOUNT ᐳ Log into an iCloud Account that will provide FamShr location data',
        'logout_icloud_account':    'LOG OUT OF ICLOUD ACCOUNT ᐳ Log out of the iCloud Account used for FamShr location data (^msg)',
        'verification_code':        'ENTER/REQUEST AN APPLE ID VERIFICATION CODE ᐳ Enter (or Request) the 6-digit Apple ID Verification Code',

        'send_verification_code':   'SEND THE VERIFICATION CODE TO APPLE ᐳ Send the 6-digit Apple ID Verification Code back to Apple to approve access to iCloud account',
        "request_verification_code":'REQUEST A NEW APPLE ID VERIFICATION CODE ᐳ Reset iCloud Interface and request a new Apple ID Verification Code',
        'cancel_verification_entry':'CANCEL ᐳ Cancel the Verification Code Entry and Close this screen',

        'update_device':            'UPDATE DEVICE ᐳ Update the selected device',
        'add_device':               'ADD DEVICE ᐳ Add a device to be tracked by iCloud3',
        'delete_device':            'DELETE DEVICE(S), OTHER DEVICE MAINTENANCE ᐳ Delete the device(s) from the tracked device list, clear the FamShr/FmF/Mobile App selection fields',
        'change_device_order':      'CHANGE DEVICE ORDER ᐳ Change the tracking order of the Devices and their display sequence on the Event Log',

        'delete_this_device':       'DELETE THIS DEVICE ᐳ Delete this device → ',
        'delete_all_devices':       'DELETE ALL DEVICES ᐳ Delete all devices from the iCloud3 tracked devices list',
        'delete_icloud_mobapp_info':'CLEAR FAMSHR/MOBAPP INFO ᐳ Reset the FamShr/Mobile App seletion fields on all devices',
        'delete_device_cancel':     'CANCEL ᐳ Return to the Device List screen',

        'inactive_to_track':        'TRACK ALL OR SELECTED ᐳ Change the `Tracking Mode‘ of all of the devices (or the selected devices) from `Inactive‘ to `Tracked‘',
        'inactive_keep_inactive':   'DO NOT TRACK, KEEP INACTIVE ᐳ None of these devices should be `Tracked‘ and should remain `Inactive‘',

        'restart_ha':               'RESTART HOME ASSISTANT ᐳ Restart HA and reload iCloud3',
        'restart_ic3_now':          'RESTART NOW ᐳ Restart iCloud3 now to load the updated configuration',
        'restart_ic3_later':        'RESTART LATER ᐳ The configuration changes have been saved. Load the updated configuration the next time iCloud3 is started',
        'reload_icloud3':           'RELOAD ICLOUD3 ᐳ Reload & Restart iCloud3 (This does not load a new version)',
        'review_inactive_devices':  'REVIEW INACTIVE DEVICES ᐳ Some Devices are `Inactive` and will not be located or tracked',

        'select_text_as':           'SELECT ᐳ Update selected `Display Text As‘ field',
        'clear_text_as':            'CLEAR ᐳ Remove `Display Text As‘ entry',

        'exclude_sensors':          'EXCLUDE SENSORS ᐳ Select specific Sensors that should not be created',
        'filter_sensors':           'FILTER SENSORS ᐳ Select Sensors that should be displayed',

        'move_up':                  'MOVE UP ᐳ Move the Device up in the list',
        'move_down':                'MOVE DOWN ᐳ Move the Device down in the list',

        'save':                     'SAVE ᐳ Update Configuration File, Return to the Menu',
        'return':                   'RETURN ᐳ Return to the Menu',

        'cancel':                   'RETURN ᐳ Return to the previous screen. Cancel any unsaved changes',
        'exit':                     'EXIT ᐳ Exit the iCloud3 Configurator',

        'confirm_return':           'RETURN WITHOUT SAVING CONFIGURATION CHANGES ᐳ Return to the Main Menu without saving any changes',
        'confirm_save':             'SAVE THE CONFIGURATION CHANGES ᐳ Save any changes, then return to the Main Menu',

        "divider1": "═══════════════════════════════════════",
        "divider2": "═══════════════════════════════════════",
        "divider3": "═══════════════════════════════════════"
        }

ACTION_LIST_ITEMS_KEY_BY_TEXT = {text: key for key, text in ACTION_LIST_ITEMS_KEY_TEXT.items()}

ACTION_LIST_ITEMS_BASE = [
        ACTION_LIST_ITEMS_KEY_TEXT['save'],
        ACTION_LIST_ITEMS_KEY_TEXT['cancel']
        ]

NONE_DICT_KEY_TEXT          = {'None': 'None'}
UNKNOWN_DEVICE_TEXT         = ' >  ⛔ UNKNOWN/NOT FOUND > NEEDS REVIEW'
SERVICE_NOT_AVAILABLE       = ' > This Data Source/Web Location Service is not available'
SERVICE_NOT_STARTED_YET     = ' > This Data Source/Web Location Svc has not finished starting. Exit and Retry.'
LOGGED_INTO_MSG_ACTION_LIST_IDX = 1     # Index number of the Action list item containing the username/password

# Action List Items for all screens
ICLOUD_ACCOUNT_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['login_icloud_account'],
        ACTION_LIST_ITEMS_KEY_TEXT['logout_icloud_account'],
        ACTION_LIST_ITEMS_KEY_TEXT['verification_code']]
REAUTH_CONFIG_FLOW_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['send_verification_code'],
        ACTION_LIST_ITEMS_KEY_TEXT['request_verification_code'],
        ACTION_LIST_ITEMS_KEY_TEXT['cancel_verification_entry']]
REAUTH_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['send_verification_code'],
        ACTION_LIST_ITEMS_KEY_TEXT['request_verification_code'],
        ACTION_LIST_ITEMS_KEY_TEXT['cancel']]
DEVICE_LIST_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['update_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['add_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['delete_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['change_device_order'],
        ACTION_LIST_ITEMS_KEY_TEXT['return']]
DEVICE_LIST_ACTIONS_ADD = [
        ACTION_LIST_ITEMS_KEY_TEXT['add_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['return']]
DEVICE_LIST_ACTIONS_NO_ADD = [
        ACTION_LIST_ITEMS_KEY_TEXT['update_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['delete_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['change_device_order'],
        ACTION_LIST_ITEMS_KEY_TEXT['return']]
DELETE_DEVICE_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['delete_this_device'],
        ACTION_LIST_ITEMS_KEY_TEXT['delete_all_devices'],
        ACTION_LIST_ITEMS_KEY_TEXT['delete_icloud_mobapp_info'],
        ACTION_LIST_ITEMS_KEY_TEXT['delete_device_cancel']]
REVIEW_INACTIVE_DEVICES =  [
        ACTION_LIST_ITEMS_KEY_TEXT['inactive_to_track'],
        ACTION_LIST_ITEMS_KEY_TEXT['inactive_keep_inactive']]
RESTART_NOW_LATER_ACTIONS = [
        ACTION_LIST_ITEMS_KEY_TEXT['restart_ha'],
        ACTION_LIST_ITEMS_KEY_TEXT['reload_icloud3'],
        ACTION_LIST_ITEMS_KEY_TEXT['restart_ic3_now'],
        ACTION_LIST_ITEMS_KEY_TEXT['restart_ic3_later'],
        ACTION_LIST_ITEMS_KEY_TEXT['review_inactive_devices']]


#   Parameter List Selections Items
# DATA_SOURCE_ITEMS_KEY_TEXT = {
#         'icloud,mobapp': 'ICLOUD & MOBAPP - iCloud account and Mobile App are used for location data',
#         'icloud':   'ICLOUD ONLY - Mobile App is not monitored on any tracked device',
#         'mobapp':   'Mobile App ONLY - iCloud account is not used for location data on any tracked device'
#         }
DATA_SOURCE_ICLOUD_ITEMS_KEY_TEXT = {
        'famshr':   'Family Sharing List members from the iCloud Account (FamShr)',
        # 'fmf':      'Friends/Contacts who are sharing their location with you (FmF)'
        }
DATA_SOURCE_MOBAPP_ITEMS_KEY_TEXT = {
        'mobapp':   'HA Mobile App device_tracker and sensor entities are monitored (MobApp)'
        }
ICLOUD_SERVER_ENDPOINT_SUFFIX_ITEMS_KEY_TEXT = {
        'none':     'Use normal Apple iCloud Servers',
        'cn':       'China - Use Apple iCloud Servers located in China'
        }
MOBAPP_DEVICE_SEARCH_TEXT = '⚡ Scan for mobile app device_tracker ᐳ '
MOBAPP_DEVICE_NONE_ITEMS_KEY_TEXT = {
        'None':     'None - The Mobile App is not installed on this device',
        }
LOG_ZONES_KEY_TEXT = {
        # '.fmf':             f"{'-'*10} File Name Formats {'-'*10}",
        'name-zone':        ' → [year]-[zone].csv',
        'name-device':      ' → [year]-[device].csv',
        'name-device-zone': ' → [year]-[device]-[zone].csv',
        'name-zone-device': ' → [year]-[zone]-[device].csv',
        }
TRACKING_MODE_ITEMS_KEY_TEXT = {
        'track':    'Track - Request Location and track the device',
        'monitor':  'Monitor - Report location only when another tracked device is updated',
        'inactive': 'INACTIVE - Device is inactive and will not be tracked'
        }
DATA_SOURCE_ITEMS_KEY_TEXT = {
        'famshr':   'iCloud - Family Sharing List members from the iCloud Account (FamShr)',
        # 'fmf':      'iCloud - Friends/Contacts who are sharing their location with you (FmF)',
        'mobapp':   'Mobile App - HA Mobile App device_tracker and sensor entities are monitored (MobApp)'
        }
UNIT_OF_MEASUREMENT_ITEMS_KEY_TEXT = {
        'mi':       'Imperial (mi, ft)',
        'km':       'Metric (km, m)'
        }
TIME_FORMAT_ITEMS_KEY_TEXT = {
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
DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT = {}
DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT_BASE = {
        'fname':    'HA Zone Friendly Name (Home, Away, TheShores) →→→ PREFERRED',
        'zone':     'HA Zone entity_id (home, not_home, the_shores)',
        'name':     'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
        'title':    'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'
        }
DEVICE_TRACKER_STATE_SOURCE_ITEMS_KEY_TEXT = {
        'ic3_evlog': 'iCloud3 Zone - Use EvLog Zone Display Name (gps & accuracy) →→→ PREFERRED',
        'ic3_fname': 'iCloud3 Zone - Use Zone Friendly Name (gps & accuracy)',
        'ha_gps':    'HA Zone - Use gps coordinates to determine the zone (except Stationary Zones)'
}
LOG_LEVEL_ITEMS_KEY_TEXT = {
        'info':     'Info - Log General Information and Event Log messages',
        'debug':    'Debug - Info + Other Internal Tracking Monitors',
        'debug-ha': 'Debug (HALog) - Also add log records to the `home-assistant.log` file',
        'debug-auto-reset': 'Debug (AutoReset) - Debug logging that resets to Info at midnight',
        'rawdata':  'Rawdata - Debug + Raw Data (filtered) received from iCloud Location Servers',
        'rawdata-auto-reset':  'Rawdata (AutoReset) - RawData logging that resets to Info at midnight',
        'unfiltered':  'Rawdata (Unfiltered) - Raw Data (everything) received from iCloud Location Servers',
        }
DISTANCE_METHOD_ITEMS_KEY_TEXT = {
        'waze':     'Waze - Waze Route Service provides travel time & distance information',
        'calc':     'Calc - Distance is calculated using a `straight line` formula'
        }
WAZE_SERVER_ITEMS_KEY_TEXT = {
        'us':       WAZE_SERVERS_FNAME['us'],
        'il':       WAZE_SERVERS_FNAME['il'],
        'row':      WAZE_SERVERS_FNAME['row']
        }
WAZE_HISTORY_TRACK_DIRECTION_ITEMS_KEY_TEXT = {
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

ACTIONS_SCREEN_ITEMS_KEY_TEXT = {
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
        "restart_ha":       "RESTART HA, RELOAD ICLOUD3 ᐳ Restart HA or Reload iCloud3",
        "return":           "MAIN MENU ᐳ Return to the Main Menu"
        }
ACTIONS_SCREEN_ITEMS_TEXT  = [text for text in ACTIONS_SCREEN_ITEMS_KEY_TEXT.values()]
ACTIONS_SCREEN_ITEMS_KEY_BY_TEXT = {text: key
                                for key, text in ACTIONS_SCREEN_ITEMS_KEY_TEXT.items()
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



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                     ICLOUD3 CONFIG FLOW - INITIAL SETUP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class iCloud3_ConfigFlow(config_entries.ConfigFlow, FlowHandler, domain=DOMAIN):
    '''iCloud3 config flow Handler'''

    VERSION = 1
    def __init__(self):
        self.step_id = ''           # step_id for the window displayed
        self.errors  = {}           # Errors en.json error key
        self.OptFlow = None

    def form_msg(self):
        return f"Form-{self.step_id}, Errors-{self.errors}"

    def _traceui(self, user_input):
        _traceha(f"{user_input=} {self.errors=} ")

#----------------------------------------------------------------------
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        '''
        Create the options flow handler for iCloud3. This is called when the iCloud3 > Configure
        is selected on the Devices & Services screen, not when HA or iCloud3 is loaed
        '''
        Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()

        return Gb.OptionsFlowHandler

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  CONFIG_FLOW FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_user(self, user_input=None):
        '''
        Invoked when a user initiates a '+ Add Integration' on the Integerations screen
        '''
        disabled_by = added_datetime = None

        try:
            # Get the iCloud3 config_entry info. This will fail if it has not been installed.
            config_entries = self.hass.config_entries.async_entries(self.handler)
            config_entry   = config_entries[0]
            disabled_by    = config_entry.disabled_by
            added_datetime = config_entry.data.get('added')

            # for config_entry in config_entries:
            #     _CF_LOGGER.info(f"ic3 config_entry {config_entry.disabled_by=}")
            #     _CF_LOGGER.info(f"ic3 config_entry {config_entry.data=}")
            #     _CF_LOGGER.info(f"ic3 config_entry {config_entry.data.get('added')=}")

        except Exception as err:
            pass

        errors = {}

        await self.async_set_unique_id(DOMAIN)
        # self._abort_if_unique_id_configured()

        if disabled_by:
            _CF_LOGGER.info(f"Aborting iCloud3 Integration, Already set up but Disabled")
            return self.async_abort(reason="disabled")

        if self.hass.data.get(DOMAIN):
            _CF_LOGGER.info(f"Aborting iCloud3 Integration, Already set up")
            return self.async_abort(reason="already_configured")

        # If Gb.hass is None, then the iCloud3 Integration is being added for the first itme and
        # __init__ has not run yet. Do the preliminary initialization and v2-v3 migration check
        # and migrate the data if needed from config_ic3.yaml.
        if Gb.hass is None:
            Gb.hass = self.hass

            start_ic3.initialize_directory_filenames()
            config_file.load_storage_icloud3_configuration_file()
            start_ic3.initialize_icloud_data_source()

        # Convert the .storage/icloud3.configuration file if it is at a default
        # state or has never been updated via config_flow using 'HA Integrations > iCloud3'
        if Gb.conf_profile[CONF_VERSION] == -1:
            self.migrate_v2_config_to_v3()

        _CF_LOGGER.info(f"Config_Flow Added Integration-{Gb.ha_device_id_by_devicename=} {Gb.ha_area_id_by_devicename=}")

        if user_input is not None:
            _CF_LOGGER.info(f"Added iCloud3 Integration")

            if Gb.restart_ha_flag:
                return await self.async_step_restart_ha()

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        schema = vol.Schema({
            vol.Required('continue', default=True): bool})

        return self.async_show_form(step_id="user",
                                    data_schema=schema,
                                    errors=errors)

#----------------------------------------------------------------------
    async def async_step_reauth(self, user_input=None, errors=None):
        '''
        Ask the verification code to the user.

        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the called_from_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - called_from_step_id
                    = the step_id in the config_glow if the icloud3 configuration
                        is being updated
                    = None if the rquest is from another regular function during the normal
                        tracking operation.
        '''

        # Config_flow is only set up on the initial add. This reauth uses some of the OptionsFlowHandler
        # functions so we need to set up that link when a reauth is needed
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()

        self.step_id = 'reauth'
        self.errors = errors or {}
        self.errors_user_input = {}
        action_item = ''

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        user_input, action_item = Gb.OptionsFlowHandler._action_text_to_item(user_input)
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if (action_item == 'cancel_verification_entry'
                or (action_item == 'send_verification_code' and user_input.get(CONF_VERIFICATION_CODE, '') == '')):
            return self.async_abort(reason="verification_code_cancelled")

        if action_item == 'request_verification_code':
            await Gb.hass.async_add_executor_job(
                                        pyicloud_ic3_interface.pyicloud_reset_session,
                                        Gb.PyiCloud)
            self.errors['base'] = 'verification_code_requested2'

        elif (action_item == 'send_verification_code'
                and CONF_VERIFICATION_CODE in user_input
                and user_input[CONF_VERIFICATION_CODE]):

            valid_code = await Gb.hass.async_add_executor_job(
                                    Gb.PyiCloud.validate_2fa_code,
                                    user_input[CONF_VERIFICATION_CODE])

            # Do not restart iC3 right now if the username/password was changed on the
            # iCloud setup screen. If it was changed, another account is being logged into
            # and it will be restarted when exiting the configurator.
            if valid_code:
                post_event( f"{EVLOG_NOTICE}The Verification Code was accepted ({user_input[CONF_VERIFICATION_CODE]})")
                post_event(f"{EVLOG_NOTICE}iCLOUD ALERT > Apple ID Verification complete")

                Gb.EvLog.clear_evlog_greenbar_msg()
                Gb.EvLog.update_event_log_display("")
                start_ic3.set_primary_data_source(FAMSHR)
                Gb.PyiCloud.new_2fa_code_already_requested_flag = False

                Gb.authenticated_time = time.time()
                return self.async_abort(reason="verification_code_accepted")

            else:
                post_event( f"{EVLOG_ALERT}The Apple ID Verification Code is invalid "
                            f"({user_input[CONF_VERIFICATION_CODE]})")
                self.errors[CONF_VERIFICATION_CODE] = 'verification_code_invalid'

        return self.async_show_form(step_id=self.step_id,
                                    data_schema=self.form_schema(self.step_id),
                                    errors=self.errors)
#-------------------------------------------------------------------------------------------
    async def async_step_restart_ha(self, user_input=None, errors=None):
        '''
        A restart is required if there were devicenames in known_devices.yaml
        '''
        if Gb.OptionsFlowHandler is None:
            Gb.OptionsFlowHandler = iCloud3_OptionsFlowHandler()

        self.step_id = 'restart_ha'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = Gb.OptionsFlowHandler._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")

            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            return self.async_create_entry(title="iCloud3", data=data)

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('restart_ha'),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    def migrate_v2_config_to_v3(self):
        '''
        Migrate v2 to v3 if needed

        conf_version goes from:
            -1 --> 0 (default version installed) --> (v2 migrated to v3)
            0 --> 1 (configurator/config_flow opened and configuration file was accessed/updated).
        '''
        # if a platform: icloud3 statement or config_ic3.yaml, migrate the files
        if Gb.ha_config_platform_stmt:
            config_file.load_icloud3_ha_config_yaml(Gb.config)
        elif os.path.exists(Gb.hass.config.path('config_ic3.yaml')):
            pass
        else:
            return

        v2v3_config_migration = iCloud3_v2v3ConfigMigration()
        v2v3_config_migration.convert_v2_config_files_to_v3()
        v2v3_config_migration.remove_ic3_devices_from_known_devices_yaml_file()

        config_file.load_storage_icloud3_configuration_file()
        Gb.v2v3_config_migrated = True

        if Gb.restart_ha_flag:
            pass

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def form_schema(self, step_id):
        if step_id == 'reauth':
            self.actions_list = REAUTH_CONFIG_FLOW_ACTIONS.copy()

            return vol.Schema({
                vol.Optional(CONF_VERIFICATION_CODE):
                            selector.TextSelector(),
                vol.Required('action_items',
                            default=Gb.OptionsFlowHandler.action_default_text('send_verification_code')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

#------------------------------------------------------------------------
        elif step_id == 'restart_ha':

            restart_default = 'restart_ha'
            self.actions_list = []
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ha'])
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ic3_later'])

            actions_list_default = Gb.OptionsFlowHandler.action_default_text(restart_default)

            return  vol.Schema({
                vol.Required('action_items',
                            default=actions_list_default):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                 ICLOUD3 UPDATE CONFIGURATION / OPTIONS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class iCloud3_OptionsFlowHandler(config_entries.OptionsFlow):
    '''Handles options flow for the component.'''

    def __init__(self, settings=False):
        self.initialize_options_required_flag = True
        self.step_id        = ''       # step_id for the window displayed
        self.errors         = {}       # Errors en.json error key
        self.errors_entered_value = {}

        self.initialize_options()
        if settings:
            Gb.hass.async_create_task(self.async_step_menu())

    def initialize_options(self):
        Gb.trace_prefix = 'CONFIG'
        self._set_initial_icloud3_device_tracker_area_id()
        self.initialize_options_required_flag = False
        self.v2v3_migrated_flag               = False  # Set to True when the conf_profile[VERSION] = -1 when first loaded

        self.errors                = {}     # Errors en.json error key
        self.user_input_multi_form = {}     # Saves the user_input from form #1 on a multi-form update
        self.errors_user_input     = {}     # user_input text for a value with an error
        self.step_id               = ''     # step_id for the window displayed
        self.menu_item_selected    = [  MENU_KEY_TEXT_PAGE_0[MENU_PAGE_0_INITIAL_ITEM],
                                        MENU_KEY_TEXT_PAGE_1[MENU_PAGE_1_INITIAL_ITEM]]
        self.menu_page_no          = 0      # Menu currently displayed
        self.header_msg            = None   # Message displayed on menu after update
        self.called_from_step_id_1   = ''     # Form/Fct to return to when verifying the icloud auth code
        self.called_from_step_id_1_2 = ''     # Form/Fct to return to when verifying the icloud auth code

        self.actions_list              = []     # Actions list at the bottom of the screen
        self.actions_list_default      = ''     # Default action_items to reassign on screen redisplay
        self.config_flow_updated_parms = {''}   # Stores the type of parameters that were updated, used to reinitialize parms
        self._description_placeholders = None
        self.code_to_schema_pass_value = None

        # Variables used for icloud_account update forms
        self.logging_into_icloud_flag = False
        self._existing_entry          = None

        # Variables used for device selection and update on the device_list and device_update forms
        self.form_devices_list_all         = []         # List of the devices in the Gb.conf_tracking[DEVICES] parameter
        self.form_devices_list_displayed   = []         # List of the devices displayed on the device_list form
        self.form_devices_list_devicename  = []         # List of the devicenames in the Gb.conf_tracking[DEVICES] parameter
        self.next_page_devices_list        = []
        self.device_list_page_no           = 0          # Devices List form page number, starting with 0
        self.device_list_page_selected_idx = \
                [idx for idx in range(0, len(Gb.conf_devices)+10, 5)] # Device selected on each display page
        self.ic3_devicename_being_updated  = ''         # Devicename currently being updated
        self.conf_device_selected          = {}
        self.conf_device_selected_idx      = 0
        self.sensor_entity_attrs_changed   = {}          # Contains info regarding update_device and needed entity changes
        self.device_list_control_default   = 'select'    # Select the Return to main menu as the default
        self.add_device_flag               = False
        self.add_device_enter_devicename_form_part_flag = False  # Add device started, True = form top part only displayed

        self.all_famshr_devices            = True
        self.devicename_device_info_famshr = {}
        self.devicename_device_id_famshr   = {}
        self.devicename_device_info_fmf    = {}
        self.devicename_device_id_fmf      = {}
        self.device_id_devicename_fmf      = {}
        self.device_trkr_by_entity_id_all  = {}          # other platform device_tracker used to validate the ic3 entity is not used

        # Option selection lists on the Update devices screen
        self.famshr_list_text_by_fname      = {}
        self.famshr_list_text_by_fname_base = NONE_DICT_KEY_TEXT.copy()
        self.fmf_list_text_by_email         = {}
        self.fmf_list_text_by_email_base    = NONE_DICT_KEY_TEXT.copy()
        self.mobapp_list_text_by_entity_id  = {}         # mobile_app device_tracker info used in devices form for mobapp selection
        self.mobapp_list_text_by_entity_id  = MOBAPP_DEVICE_NONE_ITEMS_KEY_TEXT.copy()
        self.picture_by_filename       = {}
        self.picture_by_filename_base  = NONE_DICT_KEY_TEXT.copy()
        self.zone_name_key_text        = {}

        self.opt_picture_file_name_list    = []

        self.devicename_by_famshr_fmf     = {}
        self.mobapp_search_for_devicename = 'None'
        self.inactive_devices_key_text    = {}
        self.log_level_devices_key_text   = {}

        self._verification_code = None

        # Variables used for the display_text_as update
        self.dta_selected_idx      = -1        # Current conf index being updated
        self.dta_selected_idx_page = [0, 5]    # Selected idx to display on each page
        self.dta_page_no           = 0         # Current page being displayed
        self.dta_working_copy      = {0: '', 1: '', 2: '', 3: '', 4: '', 5: '', 6: '', 7: '', 8: '', 9: '',}

        # EvLog Parameter screen, Change Device Order fields
        self.cdo_devicenames   = {}
        self.cdo_new_order_idx = {}
        self.cdo_curr_idx      = 0

        # away_time_zone_adjustment
        self.away_time_zone_hours_key_text   = {}
        self.away_time_zone_devices_key_text = {}

        # Variables used for the system_settings s update
        self.www_directory_list = []

        # List of all sensors created by ic3 during startup by sensor.py that is used
        # in the exclude_sensors screen
        # Format: ('gary_iphone_zone_distance': 'Gary ZoneDistance (gary_iphone_zone_distance)')
        self.sensors_fname_list     = []
        self.excluded_sensors       = ['None']
        self.excluded_sensors_removed = []
        self.sensors_list_filter    = '?'

        self.abort_flag = ('version' not in Gb.conf_profile)
        if self.abort_flag: return

        # PyiCloud object and variables. Using local variables rather than the Gb PyiCloud variables
        # in case the username/password is changed and another account is accessed. These will not
        # intefer with ones already in use by iC3. The Global Gb variables will be set to the local
        # variables if they were changes and a iC3 Restart was selected when finishing the config setup
        self._initialize_self_PyiCloud_fields_from_Gb()

    async def async_step_init(self, user_input=None):
        if self.initialize_options_required_flag:
            self.initialize_options()
        self.errors = {}

        if self.abort_flag:
            return await self.async_step_restart_ha_ic3_load_error()

        return await self.async_step_menu_0()

#-------------------------------------------------------------------------------------------
    def _traceui(self, user_input):
        _traceha(f"{user_input=} {self.errors=} ")

#-------------------------------------------------------------------------------------------
    def _initialize_self_PyiCloud_fields_from_Gb(self):
        self.PyiCloud = Gb.PyiCloud if Gb.PyiCloud else None
        self.username                 = Gb.username or Gb.conf_tracking[CONF_USERNAME]
        self.password                 = Gb.password or Gb.conf_tracking[CONF_PASSWORD]
        self.obscure_username         = obscure_field(self.username) or 'NoUsername'
        self.obscure_password         = obscure_field(self.password) or 'NoPassword'
        self.show_username_password   = False
        self.data_source              = Gb.conf_tracking[CONF_DATA_SOURCE]
        self.endpoint_suffix          = Gb.icloud_server_endpoint_suffix or \
                                        Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX]

#-------------------------------------------------------------------------------------------
    def _set_initial_icloud3_device_tracker_area_id(self):
        '''
        When the integration is first added, there are no devices (conf_devices == [] or all of the
        devices are set to inactive. If this is the case, no Device objects have been created and
        the ICLOUD3 Integration Device Tracker Entity has not been totaly initialized. Do it now.

        - Add the 'Personal Device' area to the iCloud3 device tracker
        '''
        if (ICLOUD3 not in Gb.ha_device_id_by_devicename
                or Gb.area_id_personal_device == None
                or Gb.ha_area_id_by_devicename[ICLOUD3] not in [None, 'unknown', '']):
            return

        inactive_devices_cnt = len([Device for Device in Gb.Devices if Device.is_inactive])
        if Gb.Devices == []:
            pass
        elif inactive_devices_cnt != len(Gb.Devices):
            return

        self.update_area_id_personal_device(ICLOUD3)

#-------------------------------------------------------------------------------------------
    async def async_step_menu_0(self, user_input=None, errors=None):
        self.menu_page_no = 0
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu_1(self, user_input=None, errors=None):
        self.menu_page_no = 1
        return await self.async_step_menu(user_input, errors)

    async def async_step_menu(self, user_input=None, errors=None):
        '''Main Menu displays different screens for parameter entry'''
        Gb.trace_prefix = 'CONFIG'
        Gb.config_flow_flag = True

        if Gb.PyiCloud and self.PyiCloud is None:
            self.PyiCloud = Gb.PyiCloud
        Gb.PyiCloudConfigFlow = self.PyiCloud

        if self.PyiCloud is None and self.username:
            self.header_msg = 'icloud_acct_not_logged_into'

        self.step_id = f"menu_{self.menu_page_no}"
        self.called_from_step_id_1 = self.called_from_step_id_2 =''
        self.errors = {}

        if user_input is None:
            self._set_inactive_devices_header_msg()
            self._set_header_msg()

            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        self.menu_item_selected[self.menu_page_no] = user_input['menu_items']
        user_input, menu_item = self._menu_text_to_item(user_input, 'menu_items')
        user_input, menu_action_item = self._menu_text_to_item(user_input, 'action_items')

        if menu_action_item == 'exit':
            Gb.config_flow_flag = False
            self.initialize_options_required_flag = False

            # conf_version goes from:
            #   -1 --> 0    default version installed --> v2 migrated to v3
            #   -1 --> 1    default version installed --> configurator/config_flow opened and updated, or
            #    0 --> 1    migrated config file  --> configurator/config_flow opened and updated
            # Set to 1 here indicating the config file was reviewed/updated after inital v3 install.
            if Gb.conf_profile[CONF_VERSION] <= 0:
                self.v2v3_migrated_flag = (Gb.conf_profile[CONF_VERSION] == 0)
                Gb.conf_profile[CONF_VERSION] = 1
                config_file.write_storage_icloud3_configuration_file()

            Gb.config_flow_updated_parms = self.config_flow_updated_parms
            if ('restart' in self.config_flow_updated_parms
                    or self._set_inactive_devices_header_msg() in ['all', 'most']):
                return await self.async_step_restart_icloud3()

            else:
                self.config_flow_updated_parms = {''}
                data = {}
                data = {'updated': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
                log_debug_msg(f"Exit Configure Settings, UpdateParms-{Gb.config_flow_updated_parms}")

                return self.async_create_entry(title="iCloud3", data={})

        elif menu_action_item == 'next_page_0':
            self.menu_page_no = 0
            self.step_id = 'menu_0'
        elif menu_action_item == 'next_page_1':
            self.menu_page_no = 1
            self.step_id = 'menu_1'

        elif 'menu_item' == '':
            pass
        elif menu_item == 'icloud_account':
            return await self.async_step_icloud_account()
        elif menu_item == 'verification_code':
            return await self.async_step_reauth()
        elif menu_item == 'device_list':
            return await self.async_step_device_list()
        elif menu_item == 'change_device_order':
            return await self.async_step_change_device_order()
        elif menu_item == 'away_time_zone':
            return await self.async_step_away_time_zone()
        elif menu_item == 'format_settings':
            return await self.async_step_format_settings()
        elif menu_item == 'display_text_as':
            return await self.async_step_display_text_as()
        elif menu_item == 'tracking_parameters':
            return await self.async_step_tracking_parameters()
        elif menu_item == 'inzone_intervals':
            return await self.async_step_inzone_intervals()
        elif menu_item == 'waze':
            return await self.async_step_waze_main()
        elif menu_item == 'special_zones':
            return await self.async_step_special_zones()
        elif menu_item == 'sensors':
            return await self.async_step_sensors()
        elif menu_item == 'actions':
            return await self.async_step_actions()

        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors,
                            last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_restart_icloud3(self, user_input=None, errors=None):
        '''
        A restart is required due to tracking, devices or sensors changes. Ask if this
        should be done now or later.
        '''
        self.step_id = 'restart_icloud3'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item == 'cancel':
                return await self.async_step_menu_0()

            elif action_item == 'restart_ic3_later':
                if 'restart' in self.config_flow_updated_parms:
                    self.config_flow_updated_parms.remove('restart')
                Gb.config_flow_updated_parms = self.config_flow_updated_parms


            # If the polling loop has been set up, set the restart flag to trigger a restart when
            # no devices are being updated. Otherwise, there were probably no devices to track
            # when first loaded and a direct restart must be done.
            elif action_item == 'restart_ic3_now':
                Gb.config_flow_updated_parms = self.config_flow_updated_parms
                #if 'restart' in self.config_flow_updated_parms:
                #    self.config_flow_updated_parms.remove('restart')
                #Gb.restart_icloud3_request_flag = True

            elif action_item.startswith('restart_ha'):
                await Gb.hass.services.async_call("homeassistant", "restart")
                return self.async_abort(reason="ha_restarting")

            elif action_item == 'review_inactive_devices':
                self.called_from_step_id_1 = self.step_id
                return await self.async_step_review_inactive_devices()


            self.config_flow_updated_parms = {''}
            data = {}
            data = {'added': dt_util.now().strftime(DATETIME_FORMAT)[0:19]}
            log_debug_msg(f"Exit Configure Settings, UpdateParms-{Gb.config_flow_updated_parms}")

            return self.async_create_entry(title="iCloud3", data={})

        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('restart_icloud3'),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_review_inactive_devices(self, user_input=None, errors=None):
        '''
        There are inactive devices. Display the list of devices and confirm they should
        remain active.
        ACTION_LIST_ITEMS_KEY_TEXT['inactive_to_track'],
        ACTION_LIST_ITEMS_KEY_TEXT['inactive_keep_inactive']]
        '''
        self.step_id = 'review_inactive_devices'
        self.errors = errors or {}
        self.errors_user_input = {}

        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is not None or action_item is not None:
            if action_item == 'inactive_to_track':
                devicename_list = [self.inactive_devices_key_text.values()] \
                        if user_input['inactive_devices'] == [] \
                        else user_input['inactive_devices']

                for conf_device in Gb.conf_devices:
                    if conf_device[CONF_IC3_DEVICENAME] in devicename_list:
                        conf_device[CONF_TRACKING_MODE] = TRACK_DEVICE

                config_file.write_storage_icloud3_configuration_file()
                self.config_flow_updated_parms.update(['tracking', 'restart'])
                self.header_msg = 'action_completed'

            if self.called_from_step_id_1 == 'restart_icloud3':
                return await self.async_step_restart_icloud3()

            return await self.async_step_menu()

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema('review_inactive_devices'),
                        errors=self.errors,
                        last_step=False)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  DISPLAY AND HANDLE USER INPUT FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def common_form_handler(self, user_input=None, action_item=None, errors=None):
        '''
        Handle the data verification, error handling and confguration update of
        normal parameter feenry forms, excluding those dealing with icloud and
        device updates.
        '''
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return False

        # Validate the user_input, update the config file with valid entries
        if action_item is None:
            user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'cancel':
            return True
        elif self.step_id == 'icloud_account':
            pass
        elif self.step_id == 'device_list':
            user_input = self._get_conf_device_selected(user_input)
        elif self.step_id == 'format_settings':
            user_input = self._validate_format_settings(user_input)
        elif self.step_id == 'away_time_zone':
            user_input = self._validate_away_time_zone(user_input)
        elif self.step_id == "display_text_as":
            pass
        elif self.step_id == 'tracking_parameters':
            user_input = self._validate_tracking_parameters(user_input)
        elif self.step_id == 'inzone_intervals':
            user_input = self._validate_inzone_intervals(user_input)
        elif self.step_id == "waze_main":
            user_input = self._validate_waze_main(user_input)
        elif self.step_id == "special_zones":
            user_input = self._validate_special_zones(user_input)
        elif self.step_id == "sensors":
            self._remove_and_create_sensors(user_input)

        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        post_event(f"Configuration Changed > Type-{self.step_id.replace('_', ' ').title()}")
        self._update_configuration_file(user_input)

        # Redisplay the menu if there were no errors
        if not self.errors:
            return True

        # Display the config data entry form, any errors will be redisplayed and highlighted
        return False

#-------------------------------------------------------------------------------------------
    async def async_step_format_settings(self, user_input=None, errors=None):
        self.step_id = 'format_settings'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self.errors != {} and self.errors.get('base') != 'conf_updated':
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _format_device_info(conf_device):
        device_info = ( f"{conf_device[CONF_FNAME]}{RARROW}"
                        f"{conf_device[CONF_IC3_DEVICENAME]}, "
                        f"{DEVICE_TYPE_FNAME.get(conf_device[CONF_DEVICE_TYPE])}")
        if conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            device_info += ", MONITOR"
        elif conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            device_info += ", INACTIVE"

        return device_info

#-------------------------------------------------------------------------------------------
    async def async_step_change_device_order(self, user_input=None, errors=None, called_from_step_id=None):
        self.step_id = 'change_device_order'
        user_input, action_item = self._action_text_to_item(user_input)
        self.called_from_step_id_1 = called_from_step_id or self.called_from_step_id_1 or 'menu_0'

        if user_input is None:
            log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")
            self.cdo_devicenames = [self._format_device_info(conf_device)
                                        for conf_device in Gb.conf_devices]
            self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
            self.actions_list_default = 'move_down'
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        if action_item == 'save':
            new_conf_devices = []
            for idx in self.cdo_new_order_idx:
                new_conf_devices.append(Gb.conf_devices[idx])

            Gb.conf_devices = new_conf_devices
            config_file.set_conf_devices_index_by_devicename()
            config_file.write_storage_icloud3_configuration_file()
            self.config_flow_updated_parms.update(['restart', 'profile'])
            self.errors['base'] = 'conf_updated'

            action_item = 'cancel'

        if action_item == 'cancel':
            return self.async_show_form(step_id=self.called_from_step_id_1,
                                        data_schema=self.form_schema(self.called_from_step_id_1),
                                        errors=self.errors)

        self.cdo_curr_idx = self.cdo_devicenames.index(user_input['device_desc'])

        new_idx = self.cdo_curr_idx
        if action_item == 'move_up':
            if new_idx > 0:
                new_idx = new_idx - 1
        if action_item == 'move_down':
            if new_idx < len(self.cdo_devicenames) - 1:
                new_idx = new_idx + 1
        self.actions_list_default = action_item

        if new_idx != self.cdo_curr_idx:
            self.cdo_devicenames[self.cdo_curr_idx], self.cdo_devicenames[new_idx] = \
                    self.cdo_devicenames[new_idx], self.cdo_devicenames[self.cdo_curr_idx]
            self.cdo_new_order_idx[self.cdo_curr_idx], self.cdo_new_order_idx[new_idx] = \
                    self.cdo_new_order_idx[new_idx], self.cdo_new_order_idx[self.cdo_curr_idx]

            self.cdo_curr_idx = new_idx

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_away_time_zone(self, user_input=None, errors=None):
        self.step_id = 'away_time_zone'
        user_input, action_item = self._action_text_to_item(user_input)

        self._build_away_time_zone_devices_list()
        self._build_away_time_zone_hours_list()

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _build_away_time_zone_hours_list(self):
        if self.away_time_zone_hours_key_text != {}:
            return

        ha_time = int(Gb.this_update_time[0:2])
        for hh in range(ha_time-12, ha_time+13):
            away_hh = hh + 24 if hh < 0 else hh

            if   away_hh == 0: ap_hh = 12; ap = 'a'
            elif away_hh < 12:  ap_hh = away_hh; ap = 'a'
            elif away_hh == 12: ap_hh = 12; ap = 'p'
            else: ap_hh = away_hh - 12; ap = 'p'

            if away_hh >= 24:
                away_hh -= 24
                if   ap_hh == 12: ap = 'a'
                elif ap_hh >= 13: ap_hh -= 12; ap = 'a'

            if Gb.time_format_12_hour:
                time_str = f"{ap_hh:}{Gb.this_update_time[2:]}{ap}"
            else:
                time_str = f"{away_hh:02}{Gb.this_update_time[2:]}"

            if away_hh == ha_time:
                time_str = f"Home Time Zone"
            elif hh < ha_time:
                time_str += f" (-{abs(hh-ha_time):} hours)"
            else:
                time_str += f" (+{abs(ha_time-hh):} hours)"
            self.away_time_zone_hours_key_text[hh-ha_time] = time_str

#-------------------------------------------------------------------------------------------
    def _build_away_time_zone_devices_list(self):

        #self.away_time_zone_devices_key_text = {'none': 'Home time zone is used for all devices'}
        self.away_time_zone_devices_key_text = {'none': 'None - All devices are at Home'}
        self.away_time_zone_devices_key_text.update(self._devices_selection_list())
        self.away_time_zone_devices_key_text = ensure_six_item_dict(self.away_time_zone_devices_key_text)

#-------------------------------------------------------------------------------------------
    def _build_log_level_devices_list(self):

        self.log_level_devices_key_text = {'all': 'All devices should be logged to the log file'}
        self.log_level_devices_key_text.update(self._devices_selection_list())
        self.log_level_devices_key_text = ensure_six_item_dict(self.log_level_devices_key_text)

#-------------------------------------------------------------------------------------------
    def _devices_selection_list(self):
        return {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                for conf_device in Gb.conf_devices
                                if conf_device[CONF_TRACKING_MODE] != INACTIVE_DEVICE}

#-------------------------------------------------------------------------------------------
    async def async_step_confirm_action(self, user_input=None, action_items=None,
                                            called_from_step_id=None):
        '''
        Confirm an action - This will display a screen containing the action_items.

        Parameters:
            action_items - The action_item keys in the ACTION_LIST_ITEMS_KEY_TEXT dictionary.
                            The last key is the default item on the confirm actions screen.
            called_from_step_id - The name of the step to return to.

        Notes:
            Before calling this function, set the self.user_input_multi_form to the user_input.
                    This will preserve all parameter changes in the calling screen. They are
                    returned to the called from step on exit.
            Action item - The action_item selected on this screen is added to the
                    self.user_input_multi_form variable returned. It is resolved in the calling
                    step in the self._action_text_to_item function in the calling step.
            On Return - Set the function to return to for the called_from_step_id.
        '''
        self.step_id = 'confirm_action'
        self.errors = {}
        self.errors_user_input = {}
        self.called_from_step_id_1 = called_from_step_id or self.called_from_step_id_1 or 'menu_0'

        if action_items is not None:
            actions_list = []
            for action_item in action_items:
                actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT[action_item])

            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id,
                                                                    actions_list=actions_list),
                                                                    errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        self.user_input_multi_form['action_item'] = action_item

        if self.called_from_step_id_1 == 'icloud_account':
            return await self.async_step_icloud_account(user_input=self.user_input_multi_form)

        return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    def _set_example_zone_name(self):
        '''
        'fname': 'HA Zone Friendly Name used by zone automation triggers (TheShores)',
        'zone': 'HA Zone entity_id (the_shores)',
        'name': 'iCloud3 reformated Zone entity_id (zone.the_shores → TheShores)',
        'title': 'iCloud3 reformated Zone entity_id (zone.the_shores → The Shores)'
        '''
        DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT.update(DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT_BASE)

        # Zone = [Zone    for zone, Zone in Gb.Zones_by_zone.items()
        #                 if Zone.radius_m > 1 and instr(Zone.zone, '_')]
        Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                        if instr(Zone.zone, '_')]
        if Zone == []:
            # Zone = [Zone    for zone, Zone in Gb.Zones_by_zone.items()
            #                 if Zone.radius_m > 1 and zone != 'home']
            Zone = [Zone    for zone, Zone in Gb.HAZones_by_zone.items()
                            if  zone != 'home']
        if Zone != []:
            exZone = Zone[0]
            self._dzf_set_example_zone_name_text(ZONE, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(FNAME, 'The Shores', exZone.fname)
            self._dzf_set_example_zone_name_text(FNAME, 'TheShores', exZone.fname)
            self._dzf_set_example_zone_name_text('fname/Home', 'TheShores', exZone.fname)
            self._dzf_set_example_zone_name_text(NAME, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(NAME, 'TheShores', exZone.name)
            self._dzf_set_example_zone_name_text(TITLE, 'the_shores', exZone.zone)
            self._dzf_set_example_zone_name_text(TITLE, 'The Shores', exZone.title)

    def _dzf_set_example_zone_name_text(self, key, example_text, real_text):
        if key in DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT:
            DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT[key] = \
                DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT[key].replace(example_text, real_text)

#-------------------------------------------------------------------------------------------
    async def async_step_tracking_parameters(self, user_input=None, errors=None):
        self.step_id = 'tracking_parameters'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.www_directory_list == []:
            dir_filters      = ['/.', 'deleted', '/x-']
            path_config_base = f"{Gb.ha_config_directory}/"
            back_slash       = '\\'

            for path, dirs, files in os.walk(f"{path_config_base}www"):
                www_sub_directory = path.replace(path_config_base, '')
                in_filter_cnt = len([filter for filter in dir_filters if instr(www_sub_directory, filter)])
                if in_filter_cnt > 0 or www_sub_directory.count('/') > 4 or www_sub_directory.count(back_slash) > 4:
                    continue

                self.www_directory_list.append(www_sub_directory)

        if self.common_form_handler(user_input, action_item, errors):
            if action_item == 'save':
                Gb.picture_www_dirs = Gb.conf_profile[CONF_PICTURE_WWW_DIRS].copy()
                self.picture_by_filename = {}
            return await self.async_step_menu()


        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_inzone_intervals(self, user_input=None, errors=None):
        self.step_id = 'inzone_intervals'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_waze_main(self, user_input=None, errors=None):
        self.step_id = 'waze_main'
        user_input, action_item = self._action_text_to_item(user_input)

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors,
                            last_step=True)

#-------------------------------------------------------------------------------------------
    async def async_step_special_zones(self, user_input=None, errors=None):
        self.step_id = 'special_zones'
        user_input, action_item = self._action_text_to_item(user_input)\

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_sensors(self, user_input=None, errors=None):
        self.step_id = 'sensors'
        user_input, action_item = self._action_text_to_item(user_input)

        if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] == []:
            Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = ['None']

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        if HOME_DISTANCE not in user_input[CONF_SENSORS_TRACKING_DISTANCE]:
            user_input[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

        # TfZ Sensors are not configured via config_flow but built in
        # config_flow from the distance, time & zone sensors
        tfz_sensors_base = ['zone_info']
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_TIME])
        tfz_sensors_base.extend(user_input[CONF_SENSORS_TRACKING_DISTANCE])
        tfz_sensors = []
        for sensor in tfz_sensors_base:
            if sensor in SENSOR_GROUPS['track_from_zone']:
                tfz_sensors.append(f"tfz_{sensor}")
        user_input[CONF_SENSORS_TRACK_FROM_ZONES] = tfz_sensors

        if action_item == 'exclude_sensors':
            self.excluded_sensors = Gb.conf_sensors[CONF_EXCLUDED_SENSORS].copy()
            self.sensors_list_filter = '?'
            return await self.async_step_exclude_sensors()

        if self.common_form_handler(user_input, action_item, errors):
            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_exclude_sensors(self, user_input=None, errors=None):
        self.step_id = 'exclude_sensors'
        self.errors = {}
        user_input, action_item = self._action_text_to_item(user_input)

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']

        if self.sensors_fname_list == []:
                Sensors = []
                for devicename in Gb.Devices_by_devicename.keys():
                    devicename_Sensors = [Sensor for Sensor in Gb.Sensors_by_devicename[devicename].values()]
                    Sensors.extend(devicename_Sensors)

                self.sensors_fname_list = [Sensor.fname_entity_name for Sensor in Sensors]
                self.sensors_fname_list.sort()

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")
        sensors_list_filter = user_input['filter'].lower().replace('?', '').strip()

        if (self.sensors_list_filter == sensors_list_filter
                and len(self.excluded_sensors) == len(user_input[CONF_EXCLUDED_SENSORS])
                and user_input['filtered_sensors'] == []):
            self.sensors_list_filter = '?'
        else:
            self.sensors_list_filter = sensors_list_filter or '?'

        if action_item == 'cancel':
            return await self.async_step_sensors()

        if (action_item == 'save'
                or user_input[CONF_EXCLUDED_SENSORS] != self.excluded_sensors
                or user_input['filtered_sensors'] != []):
            self._update_excluded_sensors(user_input)

            if Gb.conf_sensors[CONF_EXCLUDED_SENSORS] != self.excluded_sensors:
                Gb.conf_sensors[CONF_EXCLUDED_SENSORS] = self.excluded_sensors.copy()
                config_file.write_storage_icloud3_configuration_file()

                self.errors['excluded_sensors'] = 'excluded_sensors_ha_restart'
                self.config_flow_updated_parms.update(['restart_ha', 'restart'])

        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _update_excluded_sensors(self, user_input):

        excluded_sensors = []
        excluded_sensors.extend(user_input[CONF_EXCLUDED_SENSORS])
        excluded_sensors.extend(user_input['filtered_sensors'])
        self.excluded_sensors = list(set(excluded_sensors))
        self.excluded_sensors.sort()

        self.excluded_sensors_removed = [sensor_fname
                                        for sensor_fname in Gb.conf_sensors[CONF_EXCLUDED_SENSORS]
                                        if sensor_fname not in self.excluded_sensors]
        self.sensors_fname_list.extend(self.excluded_sensors)
        self.sensors_fname_list = list(set(self.sensors_fname_list))
        self.sensors_fname_list.sort()

        if self.excluded_sensors == []:
            self.excluded_sensors = ['None']
        elif len(self.excluded_sensors) > 1 and 'None' in self.excluded_sensors:
            self.excluded_sensors.remove('None')

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  DISPLAY_TEXT_AS HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_display_text_as(self, user_input=None, errors=None):
        self.step_id = 'display_text_as'
        user_input, action_item = self._action_text_to_item(user_input)

        # Reinitialize everything
        if self.dta_selected_idx == -1:
            self.dta_selected_idx = 0
            self.dta_selected_idx_page = [0, 5]
            self.dta_page_no = 0
            idx = -1
            for dta_text in Gb.conf_general[CONF_DISPLAY_TEXT_AS]:
                idx += 1
                self.dta_working_copy[idx] = dta_text

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_TEXT_AS, self.dta_working_copy)
        self.dta_selected_idx = int(user_input[CONF_DISPLAY_TEXT_AS])
        self.dta_selected_idx_page[self.dta_page_no] = self.dta_selected_idx
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if action_item == 'next_page_items':
            self.dta_page_no = 1 if self.dta_page_no == 0 else 0

        elif action_item == 'select_text_as':
            return await self.async_step_display_text_as_update(user_input)

        elif action_item == 'cancel':
            self.dta_selected_idx = -1
            return await self.async_step_menu()

        elif action_item == 'save':
            idx = -1
            self.dta_selected_idx = -1
            dta_working_copy_list = DEFAULT_GENERAL_CONF[CONF_DISPLAY_TEXT_AS].copy()
            for temp_dta_text in self.dta_working_copy.values():
                if instr(temp_dta_text,'>'):
                    idx += 1
                    dta_working_copy_list[idx] = temp_dta_text

            user_input[CONF_DISPLAY_TEXT_AS] = dta_working_copy_list

            self._update_configuration_file(user_input)

            return await self.async_step_menu()

        if self._any_errors():
                self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    async def async_step_display_text_as_update(self, user_input=None, errors=None):
        self.step_id = 'display_text_as_update'
        user_input, action_item = self._action_text_to_item(user_input)

        if action_item == 'cancel':
            return await self.async_step_display_text_as()

        if action_item == 'save':
            text_from = user_input['text_from'].strip()
            text_to   = user_input['text_to'].strip()
            if  text_from and text_to:
                self.dta_working_copy[self.dta_selected_idx] = f"{text_from} > {text_to}"
            else:
                self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        if action_item == 'clear_text_as':
            self.dta_working_copy[self.dta_selected_idx] = f"#{self.dta_selected_idx + 1}"

            return await self.async_step_display_text_as()

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  ACTION MENU HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    '''
    "divider1": "━━━━━━━━━━ ICLOUD3 CONTROL ACTIONS ━━━━━━━━━━ ",
    "restart": "RESTART > Restart iCloud3",
    "pause": "PAUSE > Pause polling on all devices",
    "resume": "RESUME > Resume Polling on all devices, Refresh all locations",
    "divider2": "━━━━━━━━━━ ICLOUD ACCOUNT ACTIONS ━━━━━━━━━━ ",
    "debug": "START/STOP DEBUG LOGGING > Start or stop debug logging",
    "rawdata": "START/STOP DEBUG RAWDATA LOGGING > Start or stop debug rawdata logging",
    "commit": "COMMIT DEBUG LOG RECORDS > Verify all debug log file records are written",
    "divider3": "━━━━━━━━━━━━ OTHER COMMANDS ━━━━━━━━━━━━ ",
    "evlog_export": "EXPORT EVENT LOG > Export Event Log data",
    "wazehist_maint": "WAZE HIST DATABASE > Recalc time/distance data at midnight",
    "wazehist_track": "WAZE HIST MAP TRACK > Load route locations for map display",
    "divider4": "═══════════════════════════════════════════════ ",
    "return": "RETURN > Return to the Main Menu"
    '''

    async def async_step_actions(self, user_input=None, errors=None):
        '''
        Handle the Actions request menu
        '''
        self.step_id = 'actions'
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        # Get key for item selected ("RESTART" --> "restart") and then
        # process the requested action
        if user_input['action_items']:
            action_item =user_input['action_items'][0]
        elif user_input['ic3_actions']:
            action_item = user_input['ic3_actions'][0]
        elif user_input['debug_actions']:
            action_item = user_input['debug_actions'][0]
        elif user_input['other_actions']:
            action_item = user_input['other_actions'][0]
        else:
            action_item = 'return'

        if action_item == 'return':
            return await self.async_step_menu()

        elif action_item in [   'restart', 'pause', 'resume',
                                'wazehist_maint', 'wazehist_track',
                                'evlog_export', ]:
            service_handler.update_service_handler(action_item)

        elif action_item.startswith('debug'):
            service_handler.handle_action_log_level('debug', change_conf_log_level=False)

        elif action_item.startswith('rawdata'):
            service_handler.handle_action_log_level('rawdata', change_conf_log_level=False)

        elif action_item == 'restart_ha':
            return await self.async_step_restart_ha_ic3()

        if self.header_msg is None:
            self.header_msg = 'action_completed'

        return await self.async_step_menu()

#--------------------------------------------------------------------------------
    async def _process_action_request(self, action_item):
        #update_service_handler(action=None, action_fname=None, devicename=None):#
        self.header_msg = None

        if action_item == 'return':
            return

        elif action_item in [   'restart', 'pause', 'resume',
                                'wazehist_maint', 'wazehist_track',
                                'evlog_export', ]:
            service_handler.update_service_handler(action_item)

        elif action_item.startswith('debug'):
            service_handler.handle_action_log_level('debug', change_conf_log_level=False)

        elif action_item.startswith('rawdata'):
            service_handler.handle_action_log_level('rawdata', change_conf_log_level=False)

        if self.header_msg is None:
            self.header_msg = 'action_completed'

#-------------------------------------------------------------------------------------------
    async def async_step_restart_ha_ic3_load_error(self, user_input=None, errors=None):
        self.step_id = 'restart_ha_ic3_load_error'
        return await self.async_restart_ha_ic3(user_input, errors)

#-------------------------------------------------------------------------------------------
    async def async_step_restart_ha_ic3(self, user_input=None, errors=None):
        self.step_id = 'restart_ha_ic3'
        return await self.async_restart_ha_ic3(user_input, errors)
        # return await self.async_step_menu()

#-------------------------------------------------------------------------------------------
    async def async_restart_ha_ic3(self, user_input, errors):
        '''
        A restart HA or reload iCloud3
        '''
        # self.step_id = 'restart_ha_ic3'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        if user_input is None or action_item is None:
            return self.async_show_form(step_id=self.step_id,
                                    data_schema=self.form_schema(self.step_id),
                                    errors=self.errors)

        if action_item == 'restart_ha':
            await Gb.hass.services.async_call("homeassistant", "restart")
            return self.async_abort(reason="ha_restarting")

        elif action_item == 'reload_icloud3':
            await Gb.hass.services.async_call(
                    "homeassistant",
                    "reload_config_entry",
                    {'device_id': Gb.ha_device_id_by_devicename[ICLOUD3]},
                    )

            return self.async_abort(reason="ic3_reloading")

        return await self.async_step_menu()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                  VALIDATE DATA AND UPDATE CONFIG FILE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _update_configuration_file(self, user_input):
        '''
        Update the configuration parameters and write to the icloud3.configuration file
        '''
        updated_parms = {''}
        for pname, pvalue in user_input.items():
            if type(pvalue) is str:
                pvalue = pvalue.strip()
                if pvalue == '.':
                    continue

            if (pname not in self.errors
                    and pname in CONF_PARAMETER_FLOAT):
                pvalue = float(pvalue)

            if pname in Gb.conf_tracking:
                if Gb.conf_tracking[pname] != pvalue:
                    Gb.conf_tracking[pname] = pvalue
                    updated_parms.update(['tracking', 'restart'])

            if pname in Gb.conf_general:
                if Gb.conf_general[pname] != pvalue:
                    Gb.conf_general[pname] = pvalue
                    updated_parms.update(['general'])
                    if 'special_zones' in self.step_id:
                        updated_parms.update(['zone_formats'])
                    if 'away_time_zone' in self.step_id:
                        updated_parms.update(['devices'])
                        #updated_parms.update(['restart'])
                    if 'waze' in self.step_id:
                        updated_parms.update(['waze'])

                    if pname == CONF_LOG_LEVEL:
                        Gb.conf_general[CONF_LOG_LEVEL] = pvalue
                        start_ic3.set_log_level(pvalue)

            if pname in Gb.conf_sensors:
                if Gb.conf_sensors[pname] != pvalue:
                    Gb.conf_sensors[pname] = pvalue
                    updated_parms.update(['sensors'])

            if pname in Gb.conf_profile:
                if Gb.conf_profile[pname] != pvalue:
                    Gb.conf_profile[pname] = pvalue
                    updated_parms.update(['profile', 'evlog'])   #, 'restart'])

        if updated_parms != {''}:
            # If default or converted file, update version so the
            # ic3 parameters are now handled by config_flow
            if Gb.conf_profile[CONF_VERSION] <= 0:
                Gb.conf_profile[CONF_VERSION] = 1

            self.config_flow_updated_parms.update(updated_parms)
            config_file.write_storage_icloud3_configuration_file()

            self.header_msg = 'conf_updated'

        return

#-------------------------------------------------------------------------------------------
    def _validate_format_settings(self, user_input):
        '''
        The display_zone_format may contain '(Example: ...). If so, strip it off.
        '''
        user_input = self._option_text_to_parm(user_input, CONF_DISPLAY_ZONE_FORMAT, DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_ITEMS_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_ITEMS_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_TIME_FORMAT, TIME_FORMAT_ITEMS_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_LOG_LEVEL, LOG_LEVEL_ITEMS_KEY_TEXT)

        if (user_input[CONF_LOG_LEVEL_DEVICES] == []
                or len(user_input[CONF_LOG_LEVEL_DEVICES]) >= len(Gb.Devices)):
            user_input[CONF_LOG_LEVEL_DEVICES] = ['all']
        elif len(user_input[CONF_LOG_LEVEL_DEVICES]) > 1:
            list_del(user_input[CONF_LOG_LEVEL_DEVICES], 'all')

        if (Gb.display_zone_format != user_input[CONF_DISPLAY_ZONE_FORMAT]):
            self.config_flow_updated_parms.update(['zone_formats'])

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_away_time_zone(self, user_input):
        '''
        Validate and reinitialize the local zone parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_AWAY_TIME_ZONE_1_OFFSET, self.away_time_zone_hours_key_text)
        user_input = self._option_text_to_parm(user_input, CONF_AWAY_TIME_ZONE_2_OFFSET, self.away_time_zone_hours_key_text)

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0
        elif 'none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and len(user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]) > 1:
            if 'none' in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]:
                user_input[CONF_AWAY_TIME_ZONE_1_DEVICES].remove('none')

        if (('none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and 'none' not in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES])
                or user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] == []
                or user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] == 0):
            user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            user_input[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0
        elif 'none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and len(user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]) > 1:
            if 'none' in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]:
                user_input[CONF_AWAY_TIME_ZONE_2_DEVICES].remove('none')

        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_1_DEVICES] = 'away_time_zone_dup_devices_1'
        dup_devices = [devicename   for devicename in user_input[CONF_AWAY_TIME_ZONE_2_DEVICES]
                                    if devicename in user_input[CONF_AWAY_TIME_ZONE_1_DEVICES] and devicename != 'none']
        if dup_devices != [] : self.errors[CONF_AWAY_TIME_ZONE_2_DEVICES] = 'away_time_zone_dup_devices_2'



        return user_input
#-------------------------------------------------------------------------------------------
    def _validate_tracking_parameters(self, user_input):
        '''
        Update the profile parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)
        user_input[CONF_EVLOG_BTNCONFIG_URL] = user_input[CONF_EVLOG_BTNCONFIG_URL].strip()

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_inzone_intervals(self, user_input):
        '''
        Cycle through the inzone_interval items, validate them and rebuild the inzone_interval
        list in the config file.

        Return = valid inzone_interval diction item as part of the user_input field

        user_input:
            {'iphone': {'hours': 3, 'minutes': 11, 'seconds': 0},
            'ipad': {'hours': 2, 'minutes': 55, 'seconds': 0},
            'watch': {'hours': 0, 'minutes': 44, 'seconds': 0},
            'airpods': {'hours': 0, 'minutes': 33, 'seconds': 0},
            'no_mobapp': {'hours': 0, 'minutes': 22, 'seconds': 0},
            'center_in_zone': True,
            'discard_poor_gps_inzone': True}
        '''

        user_input_copy = user_input.copy()
        config_inzone_interval = Gb.conf_general[CONF_INZONE_INTERVALS].copy()

        for pname, pvalue in user_input_copy.items():
            if (pname not in self.errors and pname in config_inzone_interval):
                config_inzone_interval[pname] = pvalue
                user_input.pop(pname)

        user_input[CONF_INZONE_INTERVALS] = config_inzone_interval

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_waze_main(self, user_input):
        '''
        Validate the Waze numeric fields
        '''
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_SERVER, WAZE_SERVER_ITEMS_KEY_TEXT)
        user_input = self._validate_numeric_field(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_WAZE_HISTORY_TRACK_DIRECTION, WAZE_HISTORY_TRACK_DIRECTION_ITEMS_KEY_TEXT)
        user_input = self._validate_numeric_field(user_input)

        user_input[CONF_WAZE_USED] = False if user_input[CONF_WAZE_USED] == [] else True
        user_input[CONF_WAZE_HISTORY_DATABASE_USED] = False if user_input[CONF_WAZE_HISTORY_DATABASE_USED] == [] else True

        # If Waze Used changes, also change the History DB used
        if user_input[CONF_WAZE_USED] != Gb.conf_general[CONF_WAZE_USED]:
            user_input[CONF_WAZE_HISTORY_DATABASE_USED] = user_input[CONF_WAZE_USED]

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_special_zones(self, user_input):
        """ Validate the stationary one fields

        user_input:
            {'stat_zone_fname': 'Stationary',
            'stat_zone_still_time': {'hours': 0, 'minutes': 10, 'seconds': 0},
            'stat_zone_inzone_interval': {'hours': 0, 'minutes': 30, 'seconds': 0},
            'stat_zone_base_latitude': '1',
            'stat_zone_base_longitude': '0'}
        """

        user_input = self._validate_numeric_field(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)
        user_input[CONF_TRACK_FROM_BASE_ZONE_USED] = (user_input[CONF_TRACK_FROM_BASE_ZONE_USED] != [])

        if 'passthru_zone_header' in user_input:
            if user_input['passthru_zone_header'] == []:
                user_input[CONF_PASSTHRU_ZONE_TIME] = 0
            elif (user_input['passthru_zone_header'] != []
                    and user_input[CONF_PASSTHRU_ZONE_TIME] == 0):
                user_input[CONF_PASSTHRU_ZONE_TIME] = DEFAULT_GENERAL_CONF[CONF_PASSTHRU_ZONE_TIME]

        if (user_input[CONF_TRACK_FROM_BASE_ZONE_USED] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]
                or user_input[CONF_TRACK_FROM_BASE_ZONE] != Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE]
                or user_input[CONF_TRACK_FROM_HOME_ZONE] != Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
            self.config_flow_updated_parms.update(['restart'])

        if 'stat_zone_header' in user_input:
            if user_input['stat_zone_header'] == []:
                user_input[CONF_STAT_ZONE_STILL_TIME] = 0
            elif (user_input['stat_zone_header'] != []
                    and user_input[CONF_STAT_ZONE_STILL_TIME] == 0):
                user_input[CONF_STAT_ZONE_STILL_TIME] = DEFAULT_GENERAL_CONF[CONF_STAT_ZONE_STILL_TIME]

        return user_input

#-------------------------------------------------------------------------------------------
    def _strip_special_text_from_user_input(self, user_input, pname):
        '''
        The user_input options may contain a special message after the actual parameter
        value. If so, strip it off so the field can be updated in the configuration file.

        Special message types:
            - '(Example: exampletext)'
            - '>'

        Returns:
            user_input  - user_input without the example text
        '''
        if user_input is None: return

        if pname not in user_input or type(pname) is not str:
            return user_input

        pvalue = user_input[pname]
        try:
            if instr(pvalue, DATA_ENTRY_ALERT_CHAR):
                pvalue = pvalue.split(DATA_ENTRY_ALERT_CHAR)[0]
            elif instr(pvalue, '(Example:'):
                pvalue = pvalue.split('(Example:')[0]
            # elif instr(pvalue, '>'):
                # pvalue = pvalue.split('>')[0]

        except Exception as err:
            log_exception(err)
            pass

        user_input[pname] = pvalue.strip()

        return user_input

#-------------------------------------------------------------------------------------------
    def _check_inactive_devices(self):

        inactive_list = [conf_device[CONF_IC3_DEVICENAME]
                                        for conf_device in Gb.conf_devices
                                        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]

        return inactive_list != [] or self.inactive_devices_key_text.get('keep_inactive', False)

#-------------------------------------------------------------------------------------------
    def _set_inactive_devices_header_msg(self):
        '''
        Display the All/Most/Some Devices are Inactive message by setting the header message key.

        Return none, few, some, most, all based on the number of inactive devices
        '''
        # if instr(Gb.conf_tracking[CONF_DATA_SOURCE], FAMSHR):
        if instr(self.data_source, FAMSHR):
            if (Gb.conf_tracking[CONF_USERNAME] == ''
                    or Gb.conf_tracking[CONF_PASSWORD] == ''):
                self.header_msg = 'icloud_acct_not_set_up'
                return 'none'

        device_cnt = self._device_cnt()
        if device_cnt == 0:
            self.header_msg = 'inactive_no_devices'
            return 'none'

        inactive_device_cnt = self._inactive_device_cnt()
        if inactive_device_cnt == 0:
            return 'none'

        inactive_pct = inactive_device_cnt / device_cnt

        if device_cnt == inactive_device_cnt:
            inactive_msg = 'all'
        elif  inactive_pct > .66:
            inactive_msg =  'most'
        elif inactive_pct > .34:
            inactive_msg =  'some'
        else:
            inactive_msg = 'few'

        self.header_msg = f'inactive_{inactive_msg}_devices'

        return inactive_msg

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _inactive_device_cnt():
        '''
        Return the number of inactive Devices
        '''

        return len([conf_device[CONF_IC3_DEVICENAME]
                                        for conf_device in Gb.conf_devices
                                        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE])

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _device_cnt():
        '''
        Return the number of Devices
        '''

        return len(Gb.conf_devices)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        ICLOUD ACCOUNT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_icloud_account(self, user_input=None, errors=None, called_from_step_id=None):
        self.step_id = 'icloud_account'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.actions_list_default = ''
        action_item = ''
        self.called_from_step_id_2 = called_from_step_id or self.called_from_step_id_2 or 'menu_0'

        try:
            if user_input is None:
                if self.username == '' or self.password == '':
                    self.actions_list_default = 'login_icloud_account'

                elif (self.username != '' and self.password != ''
                        and instr(self.data_source, FAMSHR) is False):
                    self.actions_list_default = 'login_icloud_account'
                    self.errors['base'] = 'icloud_acct_data_source_warning'

                return self.async_show_form(step_id=self.step_id,
                                            data_schema=self.form_schema(self.step_id),
                                            errors=self.errors)

            user_input, action_item = self._action_text_to_item(user_input)
            user_input = self._strip_spaces(user_input, [CONF_USERNAME, CONF_PASSWORD])
            user_input = self._strip_spaces(user_input)

            user_input[CONF_USERNAME] = user_input[CONF_USERNAME].lower()
            user_input['endpoint_suffix'] = 'cn' if user_input['url_suffix_china'] is True else 'None'
            if user_input[CONF_USERNAME] == '' or user_input[CONF_PASSWORD] == '':
                user_input['data_source_icloud'] = []
            user_input = self._set_data_source(user_input)

            if Gb.log_debug_flag:
                log_user_input = user_input.copy()
                if CONF_USERNAME in log_user_input:
                    log_user_input[CONF_USERNAME] = obscure_field(log_user_input[CONF_USERNAME])
                log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{log_user_input}, Errors-{errors}")

            if action_item == 'cancel':
                self._initialize_self_PyiCloud_fields_from_Gb()
                return await self.async_step_menu()

            if (action_item == 'save'
                    and (self.username != user_input[CONF_USERNAME]
                        or self.password != user_input[CONF_PASSWORD])):
                action_item = 'login_icloud_account'

            # Data Source is Mobile App only, iCloud was not selected
            if user_input[CONF_USERNAME] == '' and user_input[CONF_PASSWORD] == '':
                user_input['data_source_icloud'] = []
                user_input = self._set_data_source(user_input)

                self._update_configuration_file(user_input)
                self.PyiCloud = None
                return await self.async_step_menu()

            if action_item == 'verification_code':
                if self.PyiCloud:
                    return await self.async_step_reauth(called_from_step_id='icloud_account')
                else:
                    action_item = 'login_icloud_account'

            if user_input[CONF_USERNAME] == '':
                self.errors[CONF_USERNAME] = 'required_field'
                self.errors_user_input[CONF_USERNAME] = ''
            if user_input[CONF_PASSWORD] == '':
                self.errors[CONF_PASSWORD] = 'required_field'
                self.errors_user_input[CONF_PASSWORD] = ''

            if user_input[CONF_DATA_SOURCE] == ',':
                self.errors['data_source_icloud'] = 'icloud_acct_no_data_source'
                self.errors['data_source_mobapp'] = 'icloud_acct_no_data_source'

            if self.errors == {}:
                if action_item == 'login_icloud_account':
                    user_input['data_source_icloud'] = [FAMSHR]
                    user_input = self._set_data_source(user_input)

                    # if already logged in and no changes, do not login again
                    if (self.PyiCloud
                            and self.PyiCloud.username == user_input[CONF_USERNAME]
                            and self.PyiCloud.password == user_input[CONF_PASSWORD]):
                        pass
                    else:
                        await self._log_into_icloud_account(user_input, called_from_step_id='icloud_account')

                        if (self.PyiCloud and self.PyiCloud.requires_2fa):
                            errors = {'base': 'verification_code_needed'}
                            return await self.async_step_reauth(user_input=None,
                                                                errors={'base': 'verification_code_needed'},
                                                                called_from_step_id='icloud_account')

                        if self.PyiCloud is None:
                            self.actions_list_default = 'login_icloud_account'
                        if self.errors.get('base', '') == 'icloud_acct_login_error_user_pw':
                            self.actions_list_default = 'login_icloud_account'
                            self.errors[CONF_USERNAME] = 'icloud_acct_username_password_error'

                elif action_item == 'logout_icloud_account':
                    user_input = self._initialize_pyicloud_username_password(user_input)

                elif (action_item == 'save'
                        and (self.errors == {}
                                or self.errors.get('base', '') == 'icloud_acct_logged_into')
                                or self.errors.get('base', '') == 'icloud_acct_not_logged_into'):

                    await self._build_update_device_selection_lists()
                    self._prepare_device_selection_list()

                    user_input[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX] = self.endpoint_suffix
                    user_input[CONF_DATA_SOURCE] = self.data_source

                    self._update_configuration_file(user_input)

                    return self.async_show_form(step_id=self.called_from_step_id_2,
                                            data_schema=self.form_schema(self.called_from_step_id_2),
                                            errors=self.errors)

        except Exception as err:
            log_exception(err)

        self.step_id = 'icloud_account'
        return self.async_show_form(step_id=self.step_id,
                            data_schema=self.form_schema(self.step_id),
                            errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _initialize_pyicloud_username_password(self, user_input):
        '''
        Logging out of the iCloud account - Reset all of the login variables
        '''
        self.PyiCloud = None
        self.username = ''
        self.password = ''
        self.endpoint_suffix = ''

        user_input[CONF_USERNAME] = ''
        user_input[CONF_PASSWORD] = ''
        user_input['data_source_icloud'] = []
        user_input = self._set_data_source(user_input)

        return user_input

#-------------------------------------------------------------------------------------------
    def _set_data_source(self, user_input):
        data_source = ''
        if user_input['data_source_icloud']: data_source += f"{FAMSHR}, "
        if user_input['data_source_mobapp']: data_source += f"{MOBAPP}, "
        data_source = data_source[:-2] if data_source else ','
        user_input[CONF_DATA_SOURCE] = self.data_source = data_source

        return user_input

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD VERIFICATION CODE ENTRY FORM
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_step_reauth(self, user_input=None, errors=None, called_from_step_id=None):
        '''
        Ask the verification code to the user.

        The iCloud account needs to be verified. Show the code entry form, get the
        code from the user, send the code back to Apple ID iCloud via pyicloud and get
        a valid code indicator or invalid code error.

        If the code is valid, either:
            - return to the called_from_step_id (icloud_account form) if in the config_flow configuration routine or,
            - issue a 'create_entry' indicating a successful verification. This will return
            to the function it wass called from. This will be when a validation request was
            needed during the normal tracking.

        If invalid, display an error message and ask for the code again.

        Input:
            - called_from_step_id
                    = the step_id in the config_glow if the icloud3 configuration
                        is being updated
                    = None if the rquest is from another regular function during the normal
                        tracking operation.
        '''
        self.step_id = 'reauth'
        self.errors = errors or {}
        self.errors_user_input = {}
        action_item = ''
        self.called_from_step_id_1 = called_from_step_id or self.called_from_step_id_1 or 'menu_0'

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._strip_spaces(user_input, [CONF_VERIFICATION_CODE])
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if self.PyiCloud is None:
            self.errors = 'icloud_acct_not_logged_into'
            action_item = 'cancel'

        if action_item == 'send_verification_code' and user_input.get(CONF_VERIFICATION_CODE, '') == '':
            action_item = 'cancel'

        if action_item == 'cancel':
            return self.async_show_form(step_id=self.called_from_step_id_1,
                                        data_schema=self.form_schema(self.called_from_step_id_1),
                                        errors=self.errors)

        if action_item == 'request_verification_code':
            await Gb.hass.async_add_executor_job(
                                        pyicloud_ic3_interface.pyicloud_reset_session,
                                        self.PyiCloud)
                                        # PyiCloud)

            self.errors['base'] = 'verification_code_requested2'

        elif (action_item == 'send_verification_code'
                and CONF_VERIFICATION_CODE in user_input
                and user_input[CONF_VERIFICATION_CODE]):
            valid_code = await Gb.hass.async_add_executor_job(
                                        self.PyiCloud.validate_2fa_code,
                                        user_input[CONF_VERIFICATION_CODE])

            # Do not restart iC3 right now if the username/password was changed on the
            # iCloud setup screen. If it was changed, another account is being logged into
            # and it will be restarted when exiting the configurator.
            if valid_code:
                post_event( f"{EVLOG_NOTICE}The Verification Code was accepted ({user_input[CONF_VERIFICATION_CODE]})")
                post_event(f"{EVLOG_NOTICE}iCLOUD ALERT > Apple ID Verification complete")

                Gb.EvLog.clear_evlog_greenbar_msg()
                Gb.icloud_force_update_flag = True
                self.PyiCloud.new_2fa_code_already_requested_flag = False

                self.errors['base'] = self.header_msg = 'verification_code_accepted'

                return self.async_show_form(step_id=self.called_from_step_id_1,
                                            data_schema=self.form_schema(self.called_from_step_id_1),
                                            errors=self.errors)

            else:
                post_event( f"{EVLOG_NOTICE}The Apple ID Verification Code is invalid "
                            f"({user_input[CONF_VERIFICATION_CODE]})")
                self.errors[CONF_VERIFICATION_CODE] = 'verification_code_invalid'

        return self.async_show_form(step_id=self.step_id,
                                    data_schema=self.form_schema(self.step_id),
                                    errors=self.errors)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            ICLOUD UTILITIES - LOG INTO ACCOUNT
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def _log_into_icloud_account(self, user_input, called_from_step_id=None, request_verification_code=False):
        '''
        Log into the icloud account and check to see if a verification code is needed.
        If so, show the verification form, get the code from the user, verify it and
        return to the 'called_from_step_id' (icloud_account).

        Input:
            user_input  = A dictionary with the username and password, or
                            {username: icloudAccountUsername, password: icloudAccountPassword}
                        = {} to use the username/password in the tracking configuration parameters
            called_from_step_id
                        = The step logging into the iCloud account. This step will be returned
                            to when the login is complete.

        Exception:
            The self.PyiCloud.requres_2fa must be checked after a login to see if the account
            access needs to be verified. If so, the verification code entry form must be displayed.

        Returns:
            Gb.Pyicloud object
            self.PyiCloud_FamilySharing object
            self.PyiCloud_FindMyFriends object
            self.opt_famshr_devicename_list & self.device_form_icloud_famf_list =
                    A dictionary with the devicename and identifiers
                    used in the tracking configuration devices icloud_device parameter
        '''
        called_from_step_id = called_from_step_id or 'icloud_account'
        log_debug_msg(  f"Logging into iCloud Acct > UserInput-{user_input}, "
                        f"Errors-{self.errors}, Step-{self.step_id}, CalledFrom-{called_from_step_id}")

        if CONF_USERNAME in user_input:
            self.username = user_input[CONF_USERNAME].lower()
            self.password = user_input[CONF_PASSWORD]
            self.endpoint_suffix = user_input['endpoint_suffix']
            verify_password = (self.username != Gb.conf_tracking[CONF_USERNAME])
        else:
            self.username = Gb.conf_tracking[CONF_USERNAME]
            self.password = Gb.conf_tracking[CONF_PASSWORD]
            self.endpoint_suffix = Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX]
            verify_password = False

        # If using same username/password as primary PyiCloud, we are already logged in
        if (Gb.PyiCloud
                and self.PyiCloud
                and self.PyiCloud == Gb.PyiCloud
                and self.username == Gb.PyiCloud.username
                and self.password == Gb.PyiCloud.password
                and self.endpoint_suffix == Gb.PyiCloud.endpoint_suffix):
            return

        # Already logged in with same username/password
        if (self.PyiCloud
                and request_verification_code is False
                and self.username == self.PyiCloud.username
                and self.password == self.PyiCloud.password
                and self.endpoint_suffix == self.PyiCloud.endpoint_suffix):
            return

        if request_verification_code:
            event_msg = f"{EVLOG_NOTICE}Configure Settings > Requesting Apple ID Verification Code"
        else:
            event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into iCloud Account, "
                        f"{CRLF_DOT}iCloud Account Currently Used > {obscure_field(Gb.username)}"
                        f"{CRLF_DOT}New iCloud Account > {obscure_field(self.username)}")
            if self.endpoint_suffix != 'None':
                event_msg += f", AppleServerURLSuffix-{self.endpoint_suffix}"
        log_info_msg(event_msg)

        try:
            self.PyiCloud = await Gb.hass.async_add_executor_job(
                                        pyicloud_ic3_interface.create_PyiCloudService_secondary,
                                        self.username,
                                        self.password,
                                        self.endpoint_suffix,
                                        'config',
                                        verify_password,
                                        request_verification_code)

        except (PyiCloudFailedLoginException) as err:
            self.PyiCloud = None
            self.endpoint_suffix = Gb.icloud_server_endpoint_suffix = \
                    Gb.conf_tracking[CONF_ICLOUD_SERVER_ENDPOINT_SUFFIX]

            err = str(err)
            _CF_LOGGER.error(f"Error logging into iCloud service: {err}")

            if called_from_step_id == 'icloud_account':
                if err.endswith('302'):
                    error_msg = 'icloud_acct_login_error_connection'
                elif err.endswith('400'):
                    error_msg = 'icloud_acct_login_error_user_pw'
                else:
                    error_msg = 'icloud_acct_login_error_other'
            else:
                error_msg = 'icloud_acct_login_error_other'
            self.errors = {'base': error_msg}

            return self.async_show_form(step_id=called_from_step_id,
                                        data_schema=self.form_schema(called_from_step_id),
                                        errors=self.errors)

        except Exception as err:
            log_exception(err)
            _CF_LOGGER.error(f"Error logging into iCloud service: {err}")

            self.errors = {'base': 'icloud_acct_login_error_other'}

            return self.async_show_form(step_id=called_from_step_id,
                        data_schema=self.form_schema(called_from_step_id),
                        errors=self.errors)

        await self._build_update_device_selection_lists()

        self.obscure_username = obscure_field(self.username) or 'NoUsername'
        self.obscure_password = obscure_field(self.password) or 'NoPassword'

        if self.PyiCloud.requires_2fa or request_verification_code:
            return

        self.errors   = {'base': 'icloud_acct_logged_into'}
        self.header_msg = 'icloud_acct_logged_into'

        return self.async_show_form(step_id=called_from_step_id,
                        data_schema=self.form_schema(called_from_step_id),
                        errors=self.errors)

#-------------------------------------------------------------------------------------------
    def _set_action_list_item_username_password(self):
        '''
        Insert the username/password of the iCloud account currently logged into
        into the Action Item selection list item
        '''

        if (self.username== '' or self.password == ''
                or self.PyiCloud is None ): #or Gb.PyiCloud is None):
            if 'base' not in self.errors:
                self.errors = {'base': 'icloud_acct_not_logged_into'}
            logged_into_msg = 'NOT LOGGED IN'
        else:
            if (self.username == Gb.conf_tracking[CONF_USERNAME]
                    and self.password == Gb.conf_tracking[CONF_PASSWORD]):
                logged_into_msg = f"Logged into: {self.obscure_username}"
            else:
                logged_into_msg = (f"New iCloud Acct: {self.obscure_username} "
                                    f"{RED_ALERT}SAVE CHANGES{RED_ALERT}")

        self.actions_list[LOGGED_INTO_MSG_ACTION_LIST_IDX] = \
                self.actions_list[LOGGED_INTO_MSG_ACTION_LIST_IDX].replace('^msg', logged_into_msg)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            TRACKED DEVICE MENU - DEVICE LIST, DEVICE UPDATE FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_device_list(self, user_input=None, errors=None):
        '''
        Display the list of devices form and the function to be performed
        (add, update, delete) on the selected device.
        '''
        self.step_id = 'device_list'
        self.errors = errors or {}
        self.errors_user_input = {}
        self.add_device_flag = False

        user_input, action_item = self._action_text_to_item(user_input)
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if action_item == 'return':
            self.sensor_entity_attrs_changed = {}
            return await self.async_step_menu()

        if Gb.PyiCloud and self.PyiCloud is None:
            self.PyiCloud = Gb.PyiCloud

        if instr(self.data_source, FAMSHR):
            if (Gb.conf_tracking[CONF_USERNAME] == ''
                    or Gb.conf_tracking[CONF_PASSWORD] == ''):
                self.header_msg = 'icloud_acct_not_set_up'
                errors = {'base': 'icloud_acct_not_set_up'}
                return await self.async_step_icloud_account(user_input=None,
                                                    errors=errors,
                                                    called_from_step_id='device_list')

            elif (self.PyiCloud is None
                    and Gb.conf_tracking[CONF_USERNAME]
                    and Gb.conf_tracking[CONF_PASSWORD]):
                await self._log_into_icloud_account({}, called_from_step_id='device_list')

            if (self.PyiCloud and self.PyiCloud.requires_2fa):
                errors = {'base': 'verification_code_needed'}
                return await self.async_step_reauth(user_input=None,
                                                    errors=errors,
                                                    called_from_step_id='device_list')

        device_cnt = len(Gb.conf_devices)
        if user_input is None:
            await self._build_update_device_selection_lists()

        if user_input is not None:
            if (action_item in ['update_device', 'delete_device']
                    and CONF_DEVICES not in user_input):
                await self._build_update_device_selection_lists()
                action_item = ''

            if action_item == 'return':
                self.sensor_entity_attrs_changed = {}
                return await self.async_step_menu()

            if action_item == 'update_device':
                self.sensor_entity_attrs_changed['update_device'] = True
                if self._get_conf_device_selected(user_input):
                    return await self.async_step_update_device()

            if action_item == 'add_device':
                self.sensor_entity_attrs_changed['add_device'] = True
                self.conf_device_selected = DEFAULT_DEVICE_CONF.copy()
                return await self.async_step_add_device()

            if action_item == 'delete_device':
                self.sensor_entity_attrs_changed['delete_device'] = True
                if self._get_conf_device_selected(user_input):
                    return await self.async_step_delete_device()

            if action_item == 'next_page_items':
                if device_cnt == 0:
                    self.sensor_entity_attrs_changed = {}
                    return await self.async_step_menu()
                elif device_cnt > 5:
                    self.device_list_page_no += 1
                    if self.device_list_page_no > int(device_cnt/5):
                        self.device_list_page_no = 0
                    self.conf_device_selected_idx = self.device_list_page_no * 5

            if action_item == 'change_device_order':
                self.cdo_devicenames = [self._format_device_info(conf_device)
                                            for conf_device in Gb.conf_devices]
                self.cdo_new_order_idx = [x for x in range(0, len(Gb.conf_devices))]
                self.actions_list_default = 'move_down'
                return await self.async_step_change_device_order(called_from_step_id='device_list')

        self._set_inactive_devices_header_msg()
        self._set_header_msg()

        self._prepare_device_selection_list()
        self.sensor_entity_attrs_changed = {}

        self.step_id = 'device_list'

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    def _get_conf_device_selected(self, user_input):
        '''
        Cycle through the devices listed on the device_list screen. If one was selected,
        get it's device name and position in the Gb.config_tracking[DEVICES] parameter.

        If it is deleted, pop it from the config parameter and return.
        If it is being added, add a default entry to the config parameter and return that entry.
        If it is being updated, return that entry.

        Returns:
            - True = The device is being added or updated. Display the device update form.
            - False = The device was deleted. Rebuild the list and redisplay the screen.

        '''
        # Displayed info is devicename > Name, FamShr device info, FmF device info,
        # MobApp device. Get devicename.
        if CONF_DEVICES in user_input:
            devicename_selected = user_input[CONF_DEVICES]
        else:
            self.ic3_devicename_being_updated  = ''
            self.conf_device_selected          = {}
            self.conf_device_selected_idx      = 0
            self.device_list_page_no           = 0
            return False

        first_space_pos = devicename_selected.find(' ')
        if first_space_pos > 0:
            devicename_selected = devicename_selected[:first_space_pos]

        for form_devices_list_index, devicename in enumerate(self.form_devices_list_devicename):
            if devicename_selected == devicename:
                self.conf_device_selected     = Gb.conf_devices[form_devices_list_index]
                self.conf_device_selected_idx = form_devices_list_index
                break

        user_input[CONF_DEVICES] = self.conf_device_selected[CONF_IC3_DEVICENAME]

        self.conf_device_selected_idx = form_devices_list_index


        return True

#-------------------------------------------------------------------------------------------
    async def async_step_delete_device(self, user_input=None, errors=None):
        '''
        1. Delete the device from the tracking devices list and adjust the device index
        2. Delete all devices
        3. Clear the FamShr, FmF, Mobile App and track_from_zone fields from all devices
        '''
        self.step_id = 'delete_device'
        self.errors = errors or {}
        self.errors_user_input = {}
        user_input, action_item = self._action_text_to_item(user_input)

        # The delete_this_device item was modified to add the devicename/fname so it will
        # return a field value without a match, reset it here
        if action_item and action_item.startswith('delete_this_device'):
            action_item = 'delete_this_device'

        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if user_input is None or action_item is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        # if user_input is not None or action_item is not None:
        if action_item == 'delete_device_cancel':
            pass

        elif action_item == 'delete_this_device':
            self._delete_this_device()

        elif action_item == 'delete_all_devices':
            self._delete_all_devices()

        elif action_item == 'delete_icloud_mobapp_info':
            self._clear_icloud_mobapp_selection_parms()

        if action_item != 'delete_device_cancel':
            self.config_flow_updated_parms.update(['tracking', 'restart'])
            self.header_msg = 'action_completed'

        return await self.async_step_device_list()

#-------------------------------------------------------------------------------------------
    def _delete_this_device(self):
        """ Delete the device_tracker entity and associated ic3 configuration """

        devicename = self.conf_device_selected[CONF_IC3_DEVICENAME]
        event_msg = (f"Configuration Changed > DeleteDevice-{devicename}, "
                    f"{self.conf_device_selected[CONF_FNAME]}/"
                    f"{DEVICE_TYPE_FNAME[self.conf_device_selected[CONF_DEVICE_TYPE]]}")
        post_event(event_msg)

        self._remove_device_tracker_entity(devicename)

        Gb.conf_devices.pop(self.conf_device_selected_idx)
        self.form_devices_list_all.pop(self.conf_device_selected_idx)
        devicename = self.form_devices_list_devicename.pop(self.conf_device_selected_idx)

        config_file.write_storage_icloud3_configuration_file()

        device_cnt = len(self.form_devices_list_devicename) - 1
        if self.conf_device_selected_idx > device_cnt:
            self.conf_device_selected_idx = device_cnt
        if self.conf_device_selected_idx < 5:
            self.device_list_page_no = 0

#-------------------------------------------------------------------------------------------
    def _delete_all_devices(self):
        """
        Erase all ic3 devices,
        Delete the device_tracker entity and associated ic3 configuration
        """

        for conf_device in Gb.conf_devices:
            devicename = conf_device[CONF_IC3_DEVICENAME]
            self._remove_device_tracker_entity(devicename)

        Gb.conf_devices = []
        self.form_devices_list_all = []
        self.device_list_page_no = 0
        self.conf_device_selected_idx = 0

        config_file.write_storage_icloud3_configuration_file()

#-------------------------------------------------------------------------------------------
    def _clear_icloud_mobapp_selection_parms(self):
        """
        Reset the FamShr, FmF, Mobile App, track_from_zone fields to their initiial values.
        Keep the devicename, friendly name, picture and other fields
        """

        for conf_device in Gb.conf_devices:
            conf_device.update(DEFAULT_DEVICE_REINITIALIZE_CONF)

        config_file.write_storage_icloud3_configuration_file()


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            TRACKED DEVICE MENU - DEVICE LIST, DEVICE UPDATE FORMS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def async_step_add_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'add_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_FNAME)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_MOBILE_APP_DEVICE)
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, TRACKING_MODE_ITEMS_KEY_TEXT)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAME)
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if (action_item == 'cancel'
                or user_input[CONF_IC3_DEVICENAME].strip() == ''):
            return await self.async_step_device_list()

        self.add_device_flag = True
        self._validate_devicename(user_input)

        if not self.errors:
            self.conf_device_selected.update(user_input)

            if user_input[MOBAPP] is False:
                self.conf_device_selected[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][NO_MOBAPP]
                self.conf_device_selected[CONF_MOBILE_APP_DEVICE] = 'None'
            else:
                device_type = user_input[CONF_DEVICE_TYPE]
                self.conf_device_selected[CONF_INZONE_INTERVAL] = DEFAULT_GENERAL_CONF[CONF_INZONE_INTERVALS][device_type]

            self.conf_device_selected.pop(MOBAPP)

            self.step_id = 'update_device'

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'
            self.conf_device_selected.update(user_input)

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=False)

#-------------------------------------------------------------------------------------------
    async def async_step_update_device(self, user_input=None, errors=None):
        '''
        Display the device form. Validate and update the device parameters
        '''
        self.step_id = 'update_device'
        self.errors = errors or {}
        self.errors_user_input = {}

        if user_input is None:
            return self.async_show_form(step_id=self.step_id,
                                        data_schema=self.form_schema(self.step_id),
                                        errors=self.errors)

        user_input, action_item = self._action_text_to_item(user_input)
        user_input = self._option_text_to_parm(user_input, CONF_FAMSHR_DEVICENAME, self.famshr_list_text_by_fname)
        # user_input = self._option_text_to_parm(user_input, CONF_FMF_EMAIL, self.fmf_list_text_by_email)
        user_input[CONF_FMF_EMAIL] = 'None'
        user_input = self._option_text_to_parm(user_input, CONF_MOBILE_APP_DEVICE, self.mobapp_list_text_by_entity_id)
        user_input = self._option_text_to_parm(user_input, CONF_PICTURE, self.picture_by_filename)
        user_input = self._option_text_to_parm(user_input, CONF_DEVICE_TYPE, DEVICE_TYPE_FNAME)
        user_input = self._option_text_to_parm(user_input, CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)

        user_input = self._strip_special_text_from_user_input(user_input, CONF_IC3_DEVICENAME)
        user_input = self._strip_special_text_from_user_input(user_input, CONF_FAMSHR_DEVICENAME)
        # user_input = self._strip_special_text_from_user_input(user_input, CONF_FMF_EMAIL)
        log_debug_msg(f"{self.step_id} ({action_item}) > UserInput-{user_input}, Errors-{errors}")

        if action_item == 'cancel':
            return await self.async_step_device_list()

        user_input['old_devicename'] = self.conf_device_selected[CONF_IC3_DEVICENAME]
        user_input  = self._validate_devicename(user_input)
        user_input  = self._validate_update_device(user_input)
        change_flag = self._was_device_data_changed(user_input)

        if not self.errors:
            if change_flag:
                ui_devicename = user_input[CONF_IC3_DEVICENAME]

                only_non_tracked_field_updated = self._is_only_non_tracked_field_updated(user_input)
                self.conf_device_selected.update(user_input)

                # Update the configuration file
                if 'add_device' in self.sensor_entity_attrs_changed:
                    Gb.conf_devices.append(self.conf_device_selected)
                    self.conf_device_selected_idx = len(Gb.conf_devices) - 1

                    # Add the new device to the device_list form and and set it's position index
                    self.form_devices_list_all.append(self._format_device_list_item(self.conf_device_selected))
                    self.form_devices_list_devicename.append(ui_devicename)

                    if self.device_list_page_no < int(self.conf_device_selected_idx/5):
                        self.device_list_page_no += 1
                    self.device_list_page_selected_idx[self.device_list_page_no] = \
                        self.conf_device_selected_idx

                    event_msg = (f"Configuration Changed > AddDevice-{ui_devicename}, "
                                    f"{self.conf_device_selected[CONF_FNAME]}/"
                                    f"{DEVICE_TYPE_FNAME[self.conf_device_selected[CONF_DEVICE_TYPE]]}")
                    post_event(event_msg)
                else:
                    event_msg = (f"Configuration Changed > ChangeDevice-{ui_devicename}, "
                                    f"{self.conf_device_selected[CONF_FNAME]}/"
                                    f"{DEVICE_TYPE_FNAME[self.conf_device_selected[CONF_DEVICE_TYPE]]}")
                    post_event(event_msg)
                    Gb.conf_devices[self.conf_device_selected_idx] = self.conf_device_selected

                config_file.write_storage_icloud3_configuration_file()

                # Update the device_tracker & sensor entities now that the configuration has been updated
                if 'add_device' in self.sensor_entity_attrs_changed:
                    if Gb.async_add_entities_device_tracker is None:
                        await Gb.hass.config_entries.async_forward_entry_setups(Gb.config_entry, ['device_tracker'])
                    self._create_device_tracker_and_sensor_entities(ui_devicename, self.conf_device_selected)

                else:
                    self._update_changed_sensor_entities()

                self.header_msg = 'conf_updated'
                if only_non_tracked_field_updated:
                    self.config_flow_updated_parms.update(['devices'])
                else:
                    self.config_flow_updated_parms.update(['tracking', 'restart'])

            return await self.async_step_device_list()

        if self._any_errors():
            self.errors['action_items'] = 'update_aborted'

        return self.async_show_form(step_id=self.step_id,
                        data_schema=self.form_schema(self.step_id),
                        errors=self.errors,
                        last_step=True)

#-------------------------------------------------------------------------------------------
    def _is_only_non_tracked_field_updated(self, user_input):
        '''
        Cycle through the fields in the working fields dictionary for the device and see if
        only non-tracked fields were updated.

        Update the device's fields if only non-tracked fields were updated
        Restart iCloud3 if a tracked field was updated
        '''

        try:
            if Gb.conf_devices == []:
                return False

            for pname, pvalue in user_input.items():
                if (Gb.conf_devices[self.conf_device_selected_idx][pname] != pvalue
                        and pname not in DEVICE_NON_TRACKING_FIELDS):
                    return False
        except:
            return False

        return True

#-------------------------------------------------------------------------------------------
    def _validate_devicename(self, user_input):
        '''
        Validate the add device parameters
        '''
        user_input = self._option_text_to_parm(user_input, CONF_TRACKING_MODE, TRACKING_MODE_ITEMS_KEY_TEXT)

        ui_devicename     = user_input[CONF_IC3_DEVICENAME] = slugify(user_input[CONF_IC3_DEVICENAME]).strip()
        ui_fname          = user_input[CONF_FNAME]          = user_input[CONF_FNAME].strip()
        old_devicename    = user_input.get('old_devicename', ui_fname)
        ui_old_devicename = [ui_devicename, old_devicename]

        if ui_devicename == '':
            self.errors[CONF_IC3_DEVICENAME] = 'required_field'
            return user_input

        if ui_fname == '':
            self.errors[CONF_FNAME] = 'required_field'
            return user_input

        other_ic3_devicename_list = self.form_devices_list_devicename.copy()
        if other_ic3_devicename_list:
            current_ic3_devicename = Gb.conf_devices[self.conf_device_selected_idx][CONF_IC3_DEVICENAME]
            if self.add_device_flag is False and current_ic3_devicename in other_ic3_devicename_list:
                other_ic3_devicename_list.remove(current_ic3_devicename)

        # Already used if the new ic3_devicename is in the devicename list
        if ui_devicename in other_ic3_devicename_list:
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_ic3_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = ui_devicename
            self.errors_user_input[CONF_IC3_DEVICENAME] = f"{ui_devicename}{DATA_ENTRY_ALERT}Assigned to another iCloud3 device"

        # Already used if the new ic3_devicename is in the ha device_tracker entity list
        if (ui_devicename in self.device_trkr_by_entity_id_all
                and self.device_trkr_by_entity_id_all[ui_devicename] != DOMAIN):
            self.errors[CONF_IC3_DEVICENAME] = 'duplicate_other_devicename'
            self.errors_user_input[CONF_IC3_DEVICENAME] = ( f"{ui_devicename}{DATA_ENTRY_ALERT}Used by Integration > "
                                                            f"{self.device_trkr_by_entity_id_all[ui_devicename]}")

        for conf_device in Gb.conf_devices:
            if ui_devicename == conf_device[CONF_IC3_DEVICENAME]:
                continue
            if ui_fname == conf_device[CONF_FNAME]:
                self.errors[CONF_FNAME] = 'duplicate_ic3_devicename'
                self.errors_user_input[CONF_FNAME] = (  f"{ui_fname}{DATA_ENTRY_ALERT}Used by iCloud3 device > "
                                                        f"{conf_device[CONF_IC3_DEVICENAME]}")
                break

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_update_device(self, user_input):
        """ Validate the device parameters

            Sets:
                self.error[] for fields that are in error
            Returns:
                user_input
                change_flag: True if a field was changed
                change_fname_flag: True if the fname was changed and the device_tracker entity needs to be updated
                change_tfz_flag: True if the track_fm_zones zone was changed and the sensors need to be updated
        """
        # self.errors = {}
        ui_devicename  = user_input[CONF_IC3_DEVICENAME]
        old_devicename = user_input.get('old_devicename', ui_devicename)
        ui_old_devicename = [ui_devicename, old_devicename]

        self.ic3_devicename_being_updated = ui_devicename

        user_input[CONF_FNAME] = user_input[CONF_FNAME].strip()
        if user_input[CONF_FNAME] == '':
            self.errors[CONF_FNAME] = 'required_field'

        # Check to make sure either the iCloud Device or MobApp device was entered
        # You must have one of them to enable tracking
        if user_input[CONF_FAMSHR_DEVICENAME].strip() == '':
            user_input[CONF_FAMSHR_DEVICENAME] = 'None'

        # if user_input[CONF_FMF_EMAIL].strip() == '':
        user_input[CONF_FMF_EMAIL] = 'None'

        if user_input[CONF_MOBILE_APP_DEVICE].strip() == '':
            user_input[CONF_MOBILE_APP_DEVICE] = 'None'

        if (user_input[CONF_TRACKING_MODE] != INACTIVE_DEVICE
                and user_input[CONF_FAMSHR_DEVICENAME] == 'None'
                and user_input[CONF_FMF_EMAIL] == 'None'
                and user_input[CONF_MOBILE_APP_DEVICE] == 'None'):
            self.errors['base'] = 'required_field_device'
            self.errors[CONF_FAMSHR_DEVICENAME] = 'no_device_selected'
            self.errors[CONF_FMF_EMAIL]         = 'no_device_selected'
            self.errors[CONF_MOBILE_APP_DEVICE] = 'no_device_selected'

        if (user_input[CONF_FAMSHR_DEVICENAME] in self.devicename_by_famshr_fmf
                and self.devicename_by_famshr_fmf[user_input[CONF_FAMSHR_DEVICENAME]] not in ui_old_devicename):
            self.errors[CONF_FAMSHR_DEVICENAME] = 'already_assigned'

        # if (user_input[CONF_FMF_EMAIL] in self.devicename_by_famshr_fmf
        #         and self.devicename_by_famshr_fmf[user_input[CONF_FMF_EMAIL]] not in ui_old_devicename):
        #     self.errors[CONF_FMF_EMAIL] = 'already_assigned'

        if self.PyiCloud:
            _FamShr = self.PyiCloud.FamilySharing
            conf_famshr_fname = user_input[CONF_FAMSHR_DEVICENAME]
            device_id = self.PyiCloud.device_id_by_famshr_fname.get(conf_famshr_fname, '')
            raw_model, model, model_display_name = self.PyiCloud.device_model_info_by_fname.get(conf_famshr_fname, ['', '', ''])
            user_input[CONF_FAMSHR_DEVICE_ID]   = device_id
            user_input[CONF_RAW_MODEL]          = raw_model
            user_input[CONF_MODEL]              = model
            user_input[CONF_MODEL_DISPLAY_NAME] = model_display_name

        # Build 'log_zones' list
        if ('none' in user_input[CONF_LOG_ZONES]
                and 'none' not in self.conf_device_selected[CONF_LOG_ZONES]):
            log_zones = []
        else:
            log_zones = [zone   for zone in self.zone_name_key_text.keys()
                                if zone in user_input[CONF_LOG_ZONES] and zone != '.' ]
        if log_zones == []:
            log_zones = ['none']
        else:
            user_input[CONF_LOG_ZONES].append('name-zone')
            log_zones.append([item  for item in user_input[CONF_LOG_ZONES]
                                    if item.startswith('name')][0])
        user_input[CONF_LOG_ZONES] = log_zones

        # Build 'track_from_zones' list
        track_from_zones = [zone    for zone in self.zone_name_key_text.keys()
                                    if (zone in user_input[CONF_TRACK_FROM_ZONES]
                                        and zone not in ['.',
                                            self.conf_device_selected[CONF_TRACK_FROM_BASE_ZONE]])]
        track_from_zones.append(self.conf_device_selected[CONF_TRACK_FROM_BASE_ZONE])
        user_input[CONF_TRACK_FROM_ZONES] = track_from_zones

        if isbetween(user_input[CONF_FIXED_INTERVAL], 1, 2):
            user_input[CONF_FIXED_INTERVAL] = 3
            self.errors[CONF_FIXED_INTERVAL] = 'fixed_interval_invalid_range'

        return user_input

#-------------------------------------------------------------------------------------------
    def _was_device_data_changed(self, user_input):
        """ Cycle thru old and new data and identify changed fields

            Returns:
                True if anything was changed
            Updates:
                sensor_entity_attrs_changed based on changes detected
        """

        if self.errors:
            return False

        change_flag = False
        self.sensor_entity_attrs_changed[CONF_IC3_DEVICENAME]  = self.conf_device_selected[CONF_IC3_DEVICENAME]
        self.sensor_entity_attrs_changed['new_ic3_devicename'] = user_input[CONF_IC3_DEVICENAME]
        self.sensor_entity_attrs_changed[CONF_TRACKING_MODE]   = self.conf_device_selected[CONF_TRACKING_MODE]
        self.sensor_entity_attrs_changed['new_tracking_mode']  = user_input[CONF_TRACKING_MODE]

        for pname, pvalue in self.conf_device_selected.items():
            if pname not in user_input or user_input[pname] != pvalue:
                change_flag = True

            if pname == CONF_FNAME and user_input[CONF_FNAME] != pvalue:
                self.sensor_entity_attrs_changed[CONF_FNAME] = user_input[CONF_FNAME]

            if pname == CONF_TRACK_FROM_ZONES and user_input[CONF_TRACK_FROM_ZONES] != pvalue:
                new_tfz_zones_list, remove_tfz_zones_list = \
                            self._devices_form_identify_new_and_removed_tfz_zones(user_input)

                self.sensor_entity_attrs_changed['new_tfz_zones']    = new_tfz_zones_list
                self.sensor_entity_attrs_changed['remove_tfz_zones'] = remove_tfz_zones_list

        return change_flag

#-------------------------------------------------------------------------------------------
    def _update_changed_sensor_entities(self):
        """ Update the track_fm_zone and device_tracker sensors if needed"""

        # Use the current ic3_devicename since that is how the Device & DeviceTracker objects with the
        # device_tracker and sensor entities are stored. If the devicename was also changed, the
        # device_tracker and sensor entity names will be changed later

        devicename        = self.sensor_entity_attrs_changed[CONF_IC3_DEVICENAME]
        new_devicename    = self.sensor_entity_attrs_changed['new_ic3_devicename']
        tracking_mode     = self.sensor_entity_attrs_changed[CONF_TRACKING_MODE]
        new_tracking_mode = self.sensor_entity_attrs_changed['new_tracking_mode']

        # Remove the new track_fm_zone sensors just unchecked
        if 'remove_tfz_zones' in self.sensor_entity_attrs_changed:
            remove_tfz_zones_list = self.sensor_entity_attrs_changed['remove_tfz_zones']
            self.remove_track_fm_zone_sensor_entity(devicename, remove_tfz_zones_list)

        # Create the new track_fm_zone sensors just checked
        if 'new_tfz_zones' in self.sensor_entity_attrs_changed:
            new_tfz_zones_list = self.sensor_entity_attrs_changed['new_tfz_zones']
            self._create_track_fm_zone_sensor_entity(devicename, new_tfz_zones_list)

        # fname was changed - change the fname of device_tracker and all sensors to the new fname
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        if (devicename == new_devicename
                and CONF_FNAME in self.sensor_entity_attrs_changed
                and devicename in Gb.DeviceTrackers_by_devicename):
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])

            try:
                for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                    Sensor.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])
            except:
                pass

            # v3.0.0-beta3-Added check to see if device has tfz sensors
            try:
                for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
                    Sensor.update_entity_attribute(new_fname=self.conf_device_selected[CONF_FNAME])
            except:
                pass

        # devicename was changed - delete device_tracker and all sensors for devicename and add them for new_devicename
        if devicename != new_devicename:
            config_file.write_storage_icloud3_configuration_file()
            self._create_device_tracker_and_sensor_entities(new_devicename, self.conf_device_selected)
            self._remove_device_tracker_entity(devicename)

        # If the device was 'inactive' it's entity may not exist since they are not created for
        # inactive devices. If so, create it now if it is no longer 'inactive'.
        elif (tracking_mode == 'inactive'
                and new_tracking_mode != 'inactive'
                and new_devicename not in Gb.DeviceTrackers_by_devicename):
            self._create_device_tracker_and_sensor_entities(new_devicename, self.conf_device_selected)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#            DEVICES LIST FORM, DEVICE UPDATE FORM SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    async def _build_update_device_selection_lists(self):
        """ Setup the option lists used to select device parameters """

        self._build_picture_filename_list()
        self._build_mobapp_entity_list()
        self._build_zone_list()

        await self._build_famshr_devices_list()
        # self._build_fmf_devices_list()
        self._build_devicename_by_famshr_fmf()

#----------------------------------------------------------------------
    async def _build_famshr_devices_list(self):
        '''
        Create the FamShr object if it does not exist. This will create the famshr_info_by_famshr_fname
        that contains the fname and device info dictionary. Then sort this by the lower case fname values
        so the uppercase items (Watch) are not listed before the lower case ones (iPhone).

        This creates the list of devices used on the update devices screen
        '''
        self.famshr_list_text_by_fname_base = NONE_DICT_KEY_TEXT.copy()

        if self.PyiCloud is None:
            return

        if self.PyiCloud.FamilySharing is None:
            config_flow_login = True
            _FamShr = await Gb.hass.async_add_executor_job(
                                        pyicloud_ic3_interface.create_FamilySharing_secondary,
                                        self.PyiCloud,
                                        config_flow_login)

        if _FamShr := self.PyiCloud.FamilySharing:
            self._check_finish_v2v3conversion_for_famshr_fname()

            sorted_famshr_info_by_famshr_fname = sort_dict_by_values(self.PyiCloud.device_info_by_famshr_fname)
            self.famshr_list_text_by_fname_base.update(sorted_famshr_info_by_famshr_fname)
            self.famshr_list_text_by_fname = self.famshr_list_text_by_fname_base.copy()

#----------------------------------------------------------------------
    def _check_finish_v2v3conversion_for_famshr_fname(self):
        '''
        This will be done if the v2 files were just converted to the v3 configuration.
        Finish setting up the device by determining the actual FamShr devicename and the
        raw_model, model, model_display_name and device_id fields.
        '''

        if self.PyiCloud is None or self.PyiCloud.FamilySharing is None:
            return

        _FamShr = self.PyiCloud.FamilySharing
        famshr_devicenames = [conf_device[CONF_FAMSHR_DEVICENAME]
                                            for conf_device in Gb.conf_devices
                                            if conf_device[CONF_FAMSHR_DEVICENAME] == \
                                                    conf_device[CONF_IC3_DEVICENAME]]

        if famshr_devicenames == []:
            return

        # Build a dictionary of the FamShr fnames to compare to the ic3_devicename {gary_iphone: Gary-iPhone}
        famshr_fname_by_ic3_devicename = {slugify(fname).strip(): fname
                                                for fname in self.PyiCloud.device_model_info_by_fname.keys()}

        # Cycle thru conf_devices and see if there are any ic3_devicename = famshr_fname entries.
        # If so, they were just converted and the real famshr_devicename needs to be reset to the actual
        # value from the PyiCloud RawData fields
        update_conf_file_flag = False
        for conf_device in Gb.conf_devices:
            famshr_devicename = conf_device[CONF_FAMSHR_DEVICENAME]
            ic3_devicename    = conf_device[CONF_IC3_DEVICENAME]

            if (famshr_devicename != ic3_devicename
                    or famshr_devicename not in famshr_fname_by_ic3_devicename):
                continue

            famshr_fname = famshr_fname_by_ic3_devicename[ic3_devicename]
            conf_device[CONF_FAMSHR_DEVICENAME] = famshr_fname

            raw_model, model, model_display_name = \
                                self.PyiCloud.device_model_info_by_fname[famshr_fname]
            device_id = Gb.device_id_by_famshr_fname[famshr_fname]

            conf_device[CONF_FAMSHR_DEVICE_ID] = device_id
            conf_device[CONF_MODEL] = model
            conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
            conf_device[CONF_RAW_MODEL] = raw_model
            update_conf_file_flag = True

        if update_conf_file_flag:
            config_file.write_storage_icloud3_configuration_file()

#----------------------------------------------------------------------
    def _build_fmf_devices_list(self):
        '''
        Cycle through fmf following, followers and contact details data and get
        devices that can be tracked for the icloud device selection list
        '''

        self.fmf_list_text_by_email_base = NONE_DICT_KEY_TEXT.copy()

        if self.PyiCloud is None:
            return

        # devices_desc = start_ic3.get_fmf_devices(self.PyiCloud)
        # self.fmf_list_text_by_email_base.update(devices_desc[2])
        if _FmF := self.PyiCloud.FindMyFriends:
            # if _FmF:
            self.fmf_list_text_by_email_base.update(_FmF.device_info_by_fmf_email)
            self.fmf_list_text_by_email = self.fmf_list_text_by_email_base.copy()

#----------------------------------------------------------------------
    def _build_devicename_by_famshr_fmf(self, current_devicename=None):
        '''
        Cycle thru the configured devices and build a devicename by the
        famshr fname and fmf email values. This is used to validate these
        items are only assigned to one devicename.
        '''
        self.devicename_by_famshr_fmf = {}
        for conf_device in Gb.conf_devices:
            if conf_device[CONF_FAMSHR_DEVICENAME] != 'None':
                self.devicename_by_famshr_fmf[conf_device[CONF_FAMSHR_DEVICENAME]] = \
                        conf_device[CONF_IC3_DEVICENAME]
            if conf_device[CONF_FMF_EMAIL] != 'None':
                self.devicename_by_famshr_fmf[conf_device[CONF_FMF_EMAIL]] = \
                        conf_device[CONF_IC3_DEVICENAME]

        self.famshr_list_text_by_fname = self.famshr_list_text_by_fname_base.copy()
        for famshr_devicename, famshr_text in self.famshr_list_text_by_fname_base.items():
            devicename_msg = ''
            devicename_msg_alert = ''
            try:
                if current_devicename != self.devicename_by_famshr_fmf[famshr_devicename]:
                    devicename_msg_alert = f"{YELLOW_ALERT} "
                    devicename_msg = (  f"{RARROW}ASSIGNED TO-"
                                        f"{self.devicename_by_famshr_fmf[famshr_devicename]}")
            except:
                pass
            self.famshr_list_text_by_fname[famshr_devicename] = \
                        f"{devicename_msg_alert}{famshr_text}{devicename_msg}"

        # self.fmf_list_text_by_email = self.fmf_list_text_by_email_base.copy()
        # for fmf_email, fmf_text in self.fmf_list_text_by_email_base.items():
        #     devicename_msg = ''
        #     try:
        #         if current_devicename != self.devicename_by_famshr_fmf[fmf_email]:
        #             devicename_msg = (  f"{RARROW}ASSIGNED TO-"
        #                                 f"{self.devicename_by_famshr_fmf[fmf_email]}")
        #     except:
        #         pass
        #     self.fmf_list_text_by_email[fmf_email] = f"{fmf_text}{devicename_msg}"

#----------------------------------------------------------------------
    def _build_mobapp_entity_list(self):
        '''
        Cycle through the /config/.storage/core.entity_registry file and return
        the entities for platform ('mobile_app', etc)
        '''

        # Build dict of all HA device_tracker entity devicenames ({devicename: platform})
        mobapp_entities, mobapp_entity_data = entity_io.get_entity_registry_data(domain='device_tracker')
        self.device_trkr_by_entity_id_all = {entity_io._base_entity_id(k): v['platform']
                                            for k, v in mobapp_entity_data.items()}

        # Build dict of Mobile App device_tracker entity devicenames ({devicename: entity_id > fname})
        mobapp_entities, mobapp_entity_data = \
                            entity_io.get_entity_registry_data(platform='mobile_app', domain='device_tracker')
        self.mobapp_list_text_by_entity_id = MOBAPP_DEVICE_NONE_ITEMS_KEY_TEXT.copy()

        # Get `Devices` items
        mobapp_devices =    {f"{entity_io._base_entity_id(dev_trkr_entity)}": (
                                f"{self._mobapp_fname(entity_attrs)} ("
                                f"{DEVICE_TRACKER_DOT}{entity_io._base_entity_id(dev_trkr_entity)} "
                                f"({entity_attrs[CONF_RAW_MODEL]})")
                            for dev_trkr_entity, entity_attrs in mobapp_entity_data.items()}

        # Get `Search` items
        try:
            search_mobapp_devices = \
                            {f"Search: {slugify(self._mobapp_fname(entity_attrs))}": (
                                f"{MOBAPP_DEVICE_SEARCH_TEXT}{self._mobapp_fname(entity_attrs)} "
                                f"({slugify(self._mobapp_fname(entity_attrs))})")
                            for dev_trkr_entity, entity_attrs in mobapp_entity_data.items()}
        except:
            pass

        self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(mobapp_devices))
        self.mobapp_list_text_by_entity_id.update(sort_dict_by_values(search_mobapp_devices))

        return

#-------------------------------------------------------------------------------------------
    @staticmethod
    def _mobapp_fname(entity_attrs):
        return entity_attrs['name'] or entity_attrs['original_name']

#-------------------------------------------------------------------------------------------
    def _prepare_device_selection_list(self):
        '''
        Rebuild the device list for displaying on the devices list form. This is necessary
        since the parameters displayed may have been changed. Update the default values for
        each page for the device selected on each page.
        '''
        self.form_devices_list_all = []
        self.form_devices_list_displayed = []
        self.form_devices_list_devicename = []

        # Format all the device info to be listed on the form
        for conf_device_data in Gb.conf_devices:
            conf_device_data[CONF_IC3_DEVICENAME] = conf_device_data[CONF_IC3_DEVICENAME].replace(' ', '_')
            self.form_devices_list_all.append(self._format_device_list_item(conf_device_data))
            self.form_devices_list_devicename.append(conf_device_data[CONF_IC3_DEVICENAME])

        # No devices in config, reset to initial conditions
        if self.form_devices_list_all == []:
            self.conf_device_selected_idx = 0
            self.device_list_page_no   = 0
            self.device_list_page_selected_idx[0] = 0
            return

        # Build the device-list page items
        device_from_pos = self.device_list_page_no * 5
        self.form_devices_list_displayed = self.form_devices_list_all[device_from_pos:device_from_pos+5]

        # Build list of devices on next page
        device_from_pos = device_from_pos + 5
        if device_from_pos >= len(self.form_devices_list_devicename):
            device_from_pos = 0
        self.next_page_devices_list = ", ".join(self.form_devices_list_devicename[device_from_pos:device_from_pos+5])

        # Save the selected item info just updated to be used in reselecting the same item via the default value
        self.device_list_page_selected_idx[self.device_list_page_no] = self.conf_device_selected_idx

#-------------------------------------------------------------------------------------------
    def _format_device_list_item(self, conf_device_data):
        """ Format the text that is displayed for the device on the device_list form """

        device_info  = (f"{conf_device_data[CONF_IC3_DEVICENAME]}{RARROW}")

        if conf_device_data[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            device_info += "MONITOR, "
        elif conf_device_data[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
            device_info += "INACTIVE, "

        device_info += f"{conf_device_data[CONF_FNAME]}"

        if conf_device_data[CONF_FAMSHR_DEVICENAME] != 'None':
            device_info +=  f", FamShr-({conf_device_data[CONF_FAMSHR_DEVICENAME]})"

        # if conf_device_data[CONF_FMF_EMAIL] != 'None':
        #     device_info +=  f", FmF-({conf_device_data[CONF_FMF_EMAIL]})"

        if conf_device_data[CONF_MOBILE_APP_DEVICE] != 'None':
            device_info +=  f", MobApp-({conf_device_data[CONF_MOBILE_APP_DEVICE]})"

        if conf_device_data[CONF_TRACK_FROM_ZONES] != [HOME]:
            tfz_fnames = [zone_dname(z)
                    for z in conf_device_data[CONF_TRACK_FROM_ZONES]]
            device_info +=  f", TrackFromZones-({', '.join(tfz_fnames)})"
        if conf_device_data[CONF_TRACK_FROM_BASE_ZONE] != HOME:
            z = conf_device_data[CONF_TRACK_FROM_BASE_ZONE]
            device_info +=  f", PrimaryHomeZone-({zone_dname(z)})"


        return device_info

#-------------------------------------------------------------------------------------------
    def _build_picture_filename_list(self):

        try:
            if self.picture_by_filename != {}:
                return

            dir_filters      = ['/.', 'deleted', '/x-']
            image_filenames  = []
            path_config_base = f"{Gb.ha_config_directory}/"
            back_slash       = '\\'
            www_dir_25_items = {}

            for path, dirs, files in os.walk(f"{path_config_base}www"):
                www_sub_directory = path.replace(path_config_base, '')
                in_filter_cnt = len([filter for filter in dir_filters if instr(www_sub_directory, filter)])
                if in_filter_cnt > 0 or www_sub_directory.count('/') > 4 or www_sub_directory.count(back_slash):
                    continue

                # Filter unwanted directories - std dirs are www/icloud3, www/cummunity, www/images
                if Gb.picture_www_dirs:
                    valid_dir = [dir for dir in Gb.picture_www_dirs if www_sub_directory.startswith(dir)]
                    if valid_dir == []:
                        continue

                dir_image_filenames = [f"{www_sub_directory}/{file}"
                                    for file in files
                                    if file.rsplit('.', 1)[-1] in ['png', 'jpg', 'jpeg']]

                image_filenames.extend(dir_image_filenames[:25])
                if len(dir_image_filenames) > 25:
                    www_dir_25_items[f"www_dirs-{www_sub_directory}"] = \
                                (f" ⛔ {www_sub_directory} > The first 25 files out of "
                                f"{len(dir_image_filenames)} are listed")

            sorted_image_filenames = []
            for image_filename in image_filenames:
                sorted_image_filenames.append(f"{image_filename.rsplit('/', 1)[1]}:{image_filename}")
            sorted_image_filenames.sort()

            self.picture_by_filename = {}
            self.picture_by_filename['www_dirs'] = "Source Directories:"
            if Gb.picture_www_dirs:
                www_dir_idx = 0
                while www_dir_idx < len(Gb.picture_www_dirs):
                    self.picture_by_filename[f"www_dirs{www_dir_idx}"] = \
                                f"{DOT}{list_to_str(Gb.picture_www_dirs[www_dir_idx:www_dir_idx+3])}"
                    www_dir_idx += 3
            else:
                self.picture_by_filename["www_dirs0"] = f"{DOT}All `www/*` directories are searched"

            self.picture_by_filename.update(www_dir_25_items)
            self.picture_by_filename['www_dirs998'] = "Set filter on `Tracking and Other Parameters` screen"
            self.picture_by_filename['www_dirs999'] = f"{'-'*85}"
            self.picture_by_filename.update(self.picture_by_filename_base)

            for sorted_image_filename in sorted_image_filenames:
                image_filename, image_filename_path = sorted_image_filename.split(':')
                self.picture_by_filename[image_filename_path] = \
                            f"{image_filename}{RARROW}{image_filename_path.replace(image_filename, '')}"

        except Exception as err:
            log_exception(err)

#-------------------------------------------------------------------------------------------
    def _build_zone_list(self):

        if self.zone_name_key_text != {}:
            return

        fname_zones = []
        for zone, Zone in Gb.HAZones_by_zone.items():
            if is_statzone(zone):
                continue

            passive_msg = ' (Passive)' if Zone.passive else ''
            fname_zones.append(f"{Zone.dname}{passive_msg}|{zone}")

        fname_zones.sort()

        self.zone_name_key_text = {'home': 'Home'}

        for fname_zone in fname_zones:
            fname, zone = fname_zone.split('|')
            self.zone_name_key_text[zone] = fname

        self.zone_name_key_text = ensure_six_item_dict(self.zone_name_key_text)
        dummy_key = ''
        for i in range(6 - len(self.zone_name_key_text)):
            dummy_key += '.'
            self.zone_name_key_text[dummy_key] = '.'

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#      ROUTINES THAT SUPPORT ADD & REMOVE SENSOR AND DEVICE_TRACKER ENTITIES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _any_errors(self):
        return self.errors != {} and self.errors.get('base') != 'conf_updated'

    def _remove_and_create_sensors(self, user_input):
        """ Remove unchecked sensor entities and create newly checked sensor entities """

        new_sensors_list, remove_sensors_list = \
                self._sensor_form_identify_new_and_removed_sensors(user_input)
        self._remove_sensor_entity(remove_sensors_list)

        for conf_device in Gb.conf_devices:
            devicename  = conf_device[CONF_IC3_DEVICENAME]
            self._create_sensor_entity(devicename, conf_device, new_sensors_list)

#-------------------------------------------------------------------------------------------
    def _create_device_tracker_and_sensor_entities(self, devicename, conf_device):
        """ Create a device and all of it's sensors in the ha entity registry

            Create device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.
        """

        if conf_device[CONF_TRACKING_MODE] == 'inactive':
            return

        NewDeviceTrackers = []
        DeviceTracker     = None
        if devicename in Gb.DeviceTrackers_by_devicename:
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
        else:
            DeviceTracker = ic3_device_tracker.iCloud3_DeviceTracker(devicename, conf_device)
            self.update_area_id_personal_device(devicename)

        if DeviceTracker is None:
            return

        Gb.DeviceTrackers_by_devicename[devicename] = DeviceTracker
        NewDeviceTrackers.append(DeviceTracker)

        Gb.async_add_entities_device_tracker(NewDeviceTrackers, True)

        sensors_list = self._get_all_sensors_list()
        self._create_sensor_entity(devicename, conf_device, sensors_list)

#-------------------------------------------------------------------------------------------
    def _remove_device_tracker_entity(self, devicename):
        """ Remove a specific device from the ha entity registry

            Remove device_tracker.[devicename] and all sensor.[devicename]_[sensor_name]
            associated with the device.

            devicename:
                devicename to be removed
        """
        # Inactive devices were not created so they are not in Gb.DeviceTrackers_by_devicename
        if devicename not in Gb.DeviceTrackers_by_devicename:
            return

        try:
            for sensor, Sensor in Gb.Sensors_by_devicename[devicename].items():
                Sensor.remove_entity()
        except:
            pass

        try:
            for sensor, Sensor in Gb.Sensors_by_devicename_from_zone[devicename].items():
                Sensor.remove_entity()
        except:
            pass

        try:
            DeviceTracker = Gb.DeviceTrackers_by_devicename[devicename]
            DeviceTracker.remove_device_tracker()
        except:
            pass

#-------------------------------------------------------------------------------------------
    def _devices_form_identify_new_and_removed_tfz_zones(self, user_input):
        """ Determine checked/unchecked track_fm_zones """

        new_tfz_zones_list    = []
        remove_tfz_zones_list = []     # base device sensors
        old_tfz_zones_list    = self.conf_device_selected[CONF_TRACK_FROM_ZONES]
        ui_tfz_zones_list     = user_input[CONF_TRACK_FROM_ZONES]

        # Cycle thru the devices tfz zones before the update to get a list of new
        # and removed zones
        for zone in Gb.HAZones_by_zone.keys():
            if zone in ui_tfz_zones_list and zone not in old_tfz_zones_list:
                new_tfz_zones_list.append(zone)
            elif zone in old_tfz_zones_list and zone not in ui_tfz_zones_list:
                remove_tfz_zones_list.append(zone)

        return new_tfz_zones_list, remove_tfz_zones_list

#-------------------------------------------------------------------------------------------
    def remove_track_fm_zone_sensor_entity(self, devicename, remove_tfz_zones_list):
        '''
        Remove the all tfz sensors for all of the just unchecked zones
        This is called when a zone is removed from the tfz list on the Update Devices
        screen and when a tfz zone is deleted from HA and being removed from iCloud3
        in start_ic3 module
        '''

        if remove_tfz_zones_list == []:
            return

        device_tfz_sensors = Gb.Sensors_by_devicename_from_zone.get(devicename).copy()

        if device_tfz_sensors is None:
            return

        # Cycle through the zones that are no longer tracked from for the device, then cycle
        # through the Device's sensor list and remove all track_from_zone sensors ending with
        # that zone.
        for zone in remove_tfz_zones_list:
            for sensor, Sensor in device_tfz_sensors.items():
                if (sensor.endswith(f"_{zone}")
                        and Sensor.entity_removed_flag is False):
                    Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_track_fm_zone_sensor_entity(self, devicename, new_tfz_zones_list):
        """ Add tfz sensors for all zones that were just checked

            This must be done after the devices user_input parameters have been updated
        """

        if new_tfz_zones_list == []:
            return

        # Cycle thru each new zone and then cycle thru the track_from_zone sensors
        # Then add that sensor for the zones just checked
        sensors_list = []
        for sensor in Gb.conf_sensors[CONF_TRACK_FROM_ZONES]:
            sensors_list.append(sensor)

        NewZones = ic3_sensor.create_tracked_device_sensors(devicename, self.conf_device_selected, sensors_list)

        if NewZones is not []:
            Gb.async_add_entities_sensor(NewZones, True)

#-------------------------------------------------------------------------------------------
    def _sensor_form_identify_new_and_removed_sensors(self, user_input):
        """ Add newly checked/delete newly unchecked ha sensor entities """

        new_sensors_list    = []
        remove_sensors_list = []     # base device sensors
        if user_input[CONF_EXCLUDED_SENSORS] == []:
            user_input[CONF_EXCLUDED_SENSORS] = ['None']

        for sensor_group, sensor_list in user_input.items():
            if (sensor_group not in Gb.conf_sensors
                    or user_input[sensor_group] == Gb.conf_sensors[sensor_group]
                    or sensor_group == CONF_EXCLUDED_SENSORS):
                if user_input[CONF_EXCLUDED_SENSORS] != Gb.conf_sensors[CONF_EXCLUDED_SENSORS]:
                    self.config_flow_updated_parms.update(['restart_ha', 'restart'])
                continue

            # Cycle thru the sensors now in the user_input sensor_group
            # Get list of sensors to be added
            for sensor in sensor_list:
                if sensor not in Gb.conf_sensors[sensor_group]:
                    if sensor == 'last_zone':
                        if 'zone'       in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone')
                        if 'zone_name'  in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_name')
                        if 'zone_fname' in Gb.conf_sensors[sensor_group]: new_sensors_list.append('last_zone_fname')
                    else:
                        new_sensors_list.append(sensor)

            # Get list of sensors to be removed
            for sensor in Gb.conf_sensors[sensor_group]:
                if sensor not in sensor_list:
                    if sensor == 'last_zone':
                        if 'zone'       in sensor_list: remove_sensors_list.append('last_zone')
                        if 'zone_name'  in sensor_list: remove_sensors_list.append('last_zone_name')
                        if 'zone_fname' in sensor_list: remove_sensors_list.append('last_zone_fname')
                    else:
                        remove_sensors_list.append(sensor)

        return new_sensors_list, remove_sensors_list

#-------------------------------------------------------------------------------------------
    def _remove_sensor_entity(self, remove_sensors_list, select_devicename=None):
        """ Delete sensors from the ha entity registry and ic3 dictionaries

            remove_sensors_list:
                    list of the sensors to be deleted
            selected_devicename:
                    specified       - only delete this devicename's sensors
                    not_specified   - delete the sensors in the remove_sensors_list from all devices
        """

        if remove_sensors_list == []:
            return

        # Remove regular sensors
        device_tracking_mode = {k['ic3_devicename']: k['tracking_mode'] for k in Gb.conf_devices}
        for devicename, devicename_sensors in Gb.Sensors_by_devicename.items():
            if (devicename not in device_tracking_mode
                    or select_devicename and select_devicename != devicename):
                continue

            # Select normal/monitored sensors from the remove_sensors_list for this device
            if device_tracking_mode[devicename] == 'track':      #Device.is_tracked:
                sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is False]
            elif device_tracking_mode[devicename] == 'monitor':      #Device.is_monitored:
                sensors_list = [k for k in remove_sensors_list if k.startswith('md_') is True]
            else:
                sensors_list = []

            # The sensor group is a group of sensors combined under one conf_sensor item
            # Build sensors to be removed from the the sensor or the sensor's group
            device_sensors_list = []
            for sensor in sensors_list:
                if sensor in SENSOR_GROUPS:
                    device_sensors_list.extend(SENSOR_GROUPS[sensor])
                else:
                    device_sensors_list.append(sensor)

            Sensors_list = [v for k, v in devicename_sensors.items() if k in device_sensors_list]
            for Sensor in Sensors_list:
                if Sensor.entity_removed_flag is False:
                    Sensor.remove_entity()

        # Remove track_fm_zone sensors
        device_track_from_zones = {k['ic3_devicename']: k['track_from_zones'] for k in Gb.conf_devices}
        for devicename, devicename_sensors in Gb.Sensors_by_devicename_from_zone.items():
            if (devicename not in device_track_from_zones
                    or select_devicename and select_devicename != devicename):
                continue

            # Create tfz removal list, tfz_sensor --> sensor_zone
            tfz_sensors_list = [f"{k.replace('tfz_', '')}_{z}"
                                            for k in remove_sensors_list if k.startswith('tfz_')
                                            for z in device_track_from_zones[devicename]]

            Sensors_list = [v for k, v in devicename_sensors.items() if k in tfz_sensors_list]
            for Sensor in Sensors_list:
                if Sensor.entity_removed_flag is False:
                    Sensor.remove_entity()

#-------------------------------------------------------------------------------------------
    def _create_sensor_entity(self, devicename, conf_device, new_sensors_list):
        """ Add sensors that were just checked """

        if new_sensors_list == []:
            return

        if conf_device[CONF_TRACKING_MODE] == TRACK_DEVICE:
            sensors_list = [v for v in new_sensors_list if v.startswith('md_') is False]
            NewSensors = ic3_sensor.create_tracked_device_sensors(devicename, conf_device, sensors_list)

        elif conf_device[CONF_TRACKING_MODE] == MONITOR_DEVICE:
            sensors_list = [v for v in new_sensors_list if v.startswith('md_') is True]
            NewSensors = ic3_sensor.create_monitored_device_sensors(devicename, conf_device, sensors_list)
        else:
            return

        Gb.async_add_entities_sensor(NewSensors, True)
        ic3_sensor._setup_recorder_exclude_sensor_filter(NewSensors)

#-------------------------------------------------------------------------------------------
    def _get_all_sensors_list(self):
        """ Get a list of all sensors from the ic3 config file  """

        sensors_list = []
        for sensor_group, sensor_list in Gb.conf_sensors.items():
            if sensor_group == CONF_EXCLUDED_SENSORS:
                continue

            for sensor in Gb.conf_sensors[sensor_group]:
                sensors_list.append(sensor)

        return sensors_list

#-------------------------------------------------------------------------------------------
    def update_area_id_personal_device(self, devicename):
        '''
        Change the device's area to Personal Device
        '''

        try:
            kwargs = {}
            kwargs['area_id'] = Gb.area_id_personal_device
            Gb.ha_area_id_by_devicename[devicename] = Gb.area_id_personal_device

            ha_device_id = Gb.ha_device_id_by_devicename[devicename]
            device_registry = dr.async_get(Gb.hass)
            dr_entry = device_registry.async_update_device(ha_device_id, **kwargs)

            log_debug_msg(  "Device Tracker entity changed: device_tracker.icloud3, "
                        "iCloud3, Personal Device")
        except:
            pass

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                      MISCELLANEOUS SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _menu_text_to_item(self, user_input, selection_list):
        '''
        Convert the text of the menu item selected to it's key name.

        selection_list - Field name in user_input to use:
            ''menu_item' 'menu_action_item'
        '''

        if user_input is None:
            return None, None

        selected_text = None
        if selection_list in user_input:
            selected_text = user_input[selection_list]
            selected_text_len = 35 if len(selected_text) > 35 else len(selected_text)
            menu_item = [k for k, v in MENU_KEY_TEXT.items() if v.startswith(selected_text[:selected_text_len])][0]

            user_input.pop(selection_list)
        else:
            menu_item = self.menu_item_selected

        return user_input, menu_item

#--------------------------------------------------------------------
    def _set_header_msg(self):
        '''
        See if any header messages need to be displayed. If so set the self.errors['base']
        '''
        if self.header_msg:
            if self.errors is None: self.errors = {}
            self.errors['base'] = self.header_msg
            self.header_msg = None

#--------------------------------------------------------------------
    def _strip_spaces(self, user_input, parm_list=[]):
        '''
        Remove leading or trailing spaces from items in the parameter list

        '''
        parm_list = [pname  for pname, pvalue in user_input.items()
                                if type(pvalue) is str and pvalue != '']

        for parm in parm_list:
            user_input[parm] = user_input[parm].strip()

        return user_input

#--------------------------------------------------------------------
    def _action_text_to_item(self, user_input):
        '''
        Convert the text of the item selected to it's key name.
        '''

        if user_input is None:
            return None, None

        action_text = None
        if 'action_item' in user_input:
            action_item = user_input['action_item']
            user_input.pop('action_item')

        elif 'action_items' in user_input:
            action_text = user_input['action_items']

            if action_text.startswith('NEXT PAGE ITEMS'):
                action_item = 'next_page_items'
            else:
                action_text_len = 25 if len(action_text) > 25 else len(action_text)
                action_item = [k    for k, v in ACTION_LIST_ITEMS_KEY_TEXT.items()
                                    if v.startswith(action_text[:action_text_len])][0]
            if 'action_items' in user_input:
                user_input.pop('action_items')

        else:
            action_item = None

        if action_item == 'cancel':
            self.header_msg = None

        return user_input, action_item

#-------------------------------------------------------------------------------------------
    def _parm_or_error_msg(self, pname, conf_group=CF_DATA_GENERAL, conf_dict_variable=None):
        '''
        Determine the value that should be displayed in the config_flow parameter entry screen based
        on whether it was entered incorrectly and has an error message.

        Input:
            conf_group
        Return:
            Value in errors if it is in errors
            Value in Gb.conf_general[CONF_pname] if it is valid
        '''
        # pname is in the 'Profile' data fields
        # Example: [profile][version
        if conf_group == CF_PROFILE:
            return self.errors_user_input.get(pname) or Gb.conf_profile[pname]

        # pname is in the 'Tracking' data fields
        # Example: [data][general][tracking][username]
        # Example: [data][general][tracking][devices]
        elif conf_group == CF_DATA_TRACKING:
            return self.errors_user_input.get(pname) or Gb.conf_tracking[pname]

        # pname is in a dictionary variable in the 'General Data' data fields grupo. It is a dictionary variable.
        # Example: [data][general][inzone_intervals][phone]
        elif conf_dict_variable is not None:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][conf_dict_variable][pname]

        # pname is in a dictionary variable in the 'General Data' data fields group. It is a non-dictionary variable.
        # Example: [data][general][unit_of_measurement]
        else:
            pvalue = self.errors_user_input.get(pname) or Gb.conf_data[conf_group][pname]
            if pname in CONF_PARAMETER_FLOAT:
                pvalue = str(pvalue).replace('.0', '')

        return pvalue

#-------------------------------------------------------------------------------------------
    def _parm_or_device(self, pname, suggested_value=''):
        '''
        Get the default value from the various dictionaries to display on the input form
        '''
        try:
            parm_displayed = self.errors_user_input.get(pname) \
                                or self.user_input_multi_form.get(pname) \
                                or self.conf_device_selected.get(pname) \
                                or suggested_value

            if pname == 'device_type':
                parm_displayed = DEVICE_TYPE_FNAME.get(parm_displayed, IPHONE_FNAME)
            parm_displayed = ' ' if parm_displayed == '' else parm_displayed

        except Exception as err:
            log_exception(err)

        return parm_displayed

#-------------------------------------------------------------------------------------------
    def _option_parm_to_text(self, pname, option_list_key_text, conf_device=False):
        '''
        Returns the full text string displayed in the config_flow options list for the parameter
        value in the configuration parameter file for the parameter name.

        pname - The name of the config parameter
        option_list_key_text - The option list displayed
        conf_device - Resolves device & general with same parameter name

        Example:
            pname = unit_of_measure field in conf record = 'mi'
            um_key_text = {'mi': 'miles', 'km': 'kilometers'}
        Return:
            'miles'
        '''

        try:

            if pname in self.errors_user_input:
                return option_list_key_text[self.errors_user_input[pname]]

            pvalue_key = pname
            if pname in Gb.conf_profile:
                pvalue_key = Gb.conf_profile[pname]

            elif pname in Gb.conf_tracking:
                pvalue_key = Gb.conf_tracking[pname]

            elif pname in Gb.conf_general and pname in self.conf_device_selected:
                if conf_device:
                    pvalue_key = self.conf_device_selected[pname]
                else:
                    pvalue_key = Gb.conf_general[pname]

            elif pname in self.conf_device_selected:
                pvalue_key = self.conf_device_selected[pname]

            else:
                pvalue_key = Gb.conf_general[pname]

            if type(pvalue_key) in [float, int, str]:
                return option_list_key_text[pvalue_key]

            elif type(pvalue_key) is list:
                return [option_list_key_text[pvalue_key_item] for pvalue_key_item in pvalue_key]

            return option_list_key_text.values()[0]


        except Exception as err:
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_key not in option_list_key_text:
                if pname in [CONF_FAMSHR_DEVICENAME, CONF_FMF_EMAIL, CONF_MOBILE_APP_DEVICE]:
                    self.errors[pname] = 'unknown_devicename'
                else:
                    self.errors[pname] = 'unknown_value'

            return f"{pvalue_key} {DATA_ENTRY_ALERT}Unknown Selection"

#-------------------------------------------------------------------------------------------
    def key_text_to_text_list(self, key_text):
        return [text for text in key_text.values()]

#-------------------------------------------------------------------------------------------
    def _option_text_to_parm(self, user_input, pname, option_list_key_text):
        '''
        user_input contains the full text of the option list item selected. Replace it with
        the actual parameter value for the item selected.
        '''
        try:
            pvalue_text = '_'
            if user_input is None:
                return None

            pvalue_text = user_input[pname]

            # Handle special text added to the end of the key_list
            pvalue_text = pvalue_text.replace(UNKNOWN_DEVICE_TEXT, '')

            if pvalue_text in ['', '.']:
                self.errors[pname] = 'required_field'

            pvalue_key = [k for  k, v in option_list_key_text.items() if v == pvalue_text]
            pvalue_key = pvalue_key[0] if pvalue_key else pvalue_text

            user_input[pname] = pvalue_key

        except:
            # If the parameter value is already the key to the items dict, it is ok.
            if pvalue_text not in option_list_key_text:
                self.errors[pname] = 'invalid_value'

        return  user_input

#-------------------------------------------------------------------------------------------
    def _convert_field_str_to_numeric(self, user_input):
        '''
        Config_flow chokes with malformed input errors when a field is numeric. To avoid this,
        the field's default value is always a string. This converts it back to a float.
        '''
        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_FLOAT:
                user_input[pname] = float(pvalue)

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_numeric_field(self, user_input):
        '''
        Cycle through the user_input fields and, if numeric, validate it
        '''
        for pname, pvalue in user_input.items():
            if pname not in CONF_PARAMETER_FLOAT:
                continue

            if isnumber(pvalue) is False:
                pvalue = pvalue.strip()
                if pvalue == '':
                    self.errors[pname] = "required_field"
                else:
                    self.errors[pname] = "not_numeric"

            if pname in self.errors:
                self.errors_user_input[pname] = pvalue

        return user_input

#-------------------------------------------------------------------------------------------
    def _validate_time_str(self, user_input):
        '''
        Cycle through the each of the parameters. If it is a time string, check it's
        value and sec/min/hrs entry
        '''
        new_user_input = {}

        for pname, pvalue in user_input.items():
            if pname in CONF_PARAMETER_TIME_STR:
                time_parts  = (f"{pvalue} mins").split(' ')

                if time_parts[0].strip() == '':
                    self.errors[pname] = "required_field"
                    self.errors_user_input[pname] = ''
                    continue
                elif isnumber(str(time_parts[0])) is False:
                    self.errors[pname] = "not_numeric"
                    self.errors_user_input[pname] = user_input[pname]
                    continue

                if instr(time_parts[1], 'm'):
                    pvalue = f"{time_parts[0]} mins"
                elif instr(time_parts[1], 'h'):
                    pvalue = f"{time_parts[0]} hrs"
                elif instr(time_parts[1], 's'):
                    pvalue = f"{time_parts[0]} secs"
                else:
                    pvalue = f"{time_parts[0]} mins"

                if not self.errors.get(pname):
                    try:
                        if float(time_parts[0]) == 1:
                            pvalue = pvalue.replace('s', '')
                        new_user_input[pname] = pvalue

                    except ValueError:
                        self.errors[pname] = "not_numeric"
                        self.errors_user_input[pname] = user_input[pname]

            else:
                new_user_input[pname] = pvalue

        return new_user_input

#-------------------------------------------------------------------------------------------
    def _parm_with_example_text(self, config_parameter, input_select_list_KEY_TEXT):
        '''
        The input_select_list for the parameter has an example text '(Example: exampletext)'
        as part of list of options display for user selection. The exampletext is not part
        of the configuration parameter. Dydle through the input_select_list and determine which
        one should be the default value.

        Return:
            default - The input_select item to be used for the default value
        '''
        for isli_with_example in input_select_list_KEY_TEXT:
            if isli_with_example.startswith(Gb.conf_general[config_parameter]):
                return isli_with_example

        return input_select_list_KEY_TEXT[0]

#--------------------------------------------------------------------
    def _extract_name_device_type(self, devicename):
        '''
        Extract the name and device type from the devicename
        '''

        try:
            fname       = devicename.lower()
            device_type = ""
            for ic3dev_type in DEVICE_TYPES:
                if devicename == ic3dev_type:
                    return (devicename, devicename)

                elif instr(devicename, ic3dev_type):
                    fnamew = devicename.replace(ic3dev_type, "")
                    fname  = fnamew.replace("_", "").replace("-", "").title().strip()
                    device_type = DEVICE_TYPE_FNAME.get(ic3dev_type, ic3dev_type)
                    break

            if device_type == "":
                fname  = fname.replace("_", "").replace("-", "").title().strip()
                device_type = IPHONE_FNAME

        except Exception as err:
            log_exception(err)

        return (fname, device_type)

#--------------------------------------------------------------------
    def action_default_text(self, action_item, action_items_key_text=None):
        if action_items_key_text:
            return action_items_key_text.get(action_item, 'UNKNOWN ACTION > Unknown Action')
        else:
            return ACTION_LIST_ITEMS_KEY_TEXT.get(action_item, 'UNKNOWN ACTION - Unknown Action')

#--------------------------------------------------------------------
    def _discard_changes(self, user_input):
        '''
        See if user_input 'action_item' item has a 'discard_change' option
        selected. Discard changes is the last item in the list.
        '''
        if user_input:
            return (user_input.get('action_item') == self.action_default_text('cancel'))
        else:
            return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#                        FORM SCHEMA DEFINITIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def form_schema(self, step_id, actions_list=None, actions_list_default=None):
        '''
        Return the step_id form schema for the data entry forms
        '''
        log_debug_msg(f"Show Form-{step_id}, Errors-{self.errors}")
        schema = {}
        self.actions_list = actions_list or ACTION_LIST_ITEMS_BASE.copy()

        if step_id in ['menu', 'menu_0', 'menu_1']:
            menu_title = MENU_PAGE_TITLE[self.menu_page_no]
            menu_action_items = MENU_ACTION_ITEMS.copy()

            if self.menu_page_no == 0:
                menu_key_text  = MENU_KEY_TEXT_PAGE_0
                menu_action_items[1] = MENU_KEY_TEXT['next_page_1']


                if (self.username == '' or self.password == ''):
                    self.menu_item_selected[0] = MENU_KEY_TEXT['icloud_account']
                elif (self.username and self.password
                        and (self._device_cnt() == 0 or self._device_cnt() == self._inactive_device_cnt())):
                    self.menu_item_selected[0] = MENU_KEY_TEXT['device_list']
            else:
                menu_key_text  = MENU_KEY_TEXT_PAGE_1
                menu_action_items[1] = MENU_KEY_TEXT['next_page_0']


            return vol.Schema({
                vol.Required("menu_items",
                            default=self.menu_item_selected[self.menu_page_no]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=menu_key_text, mode='list')),
                vol.Required("action_items",
                            default=menu_action_items[0]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=menu_action_items, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id.startswith('confirm_action'):
            actions_list_default = actions_list_default or self.actions_list[0]

            return vol.Schema({
                vol.Required('action_items',
                            default=actions_list_default):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'restart_icloud3':
            self.actions_list = []
            restart_default='restart_ic3_now'

            if 'restart_ha' in self.config_flow_updated_parms:
                restart_default='restart_ha'
                self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ha'])

            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ic3_now'])
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ic3_later'])

            actions_list_default = self.action_default_text(restart_default)
            if self._inactive_device_cnt() > 0:
                inactive_devices = [conf_device[CONF_IC3_DEVICENAME]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE]
                inactive_devices_list = (
                            f"{ACTION_LIST_ITEMS_KEY_TEXT['review_inactive_devices']} "
                            f"({list_to_str(inactive_devices)})")
                self.actions_list.append(inactive_devices_list)
                if self._set_inactive_devices_header_msg() in ['all', 'most']:
                    actions_list_default = inactive_devices_list

            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['cancel'])

            return  vol.Schema({
                vol.Required('action_items',
                            default=actions_list_default):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'review_inactive_devices':
            self.actions_list = REVIEW_INACTIVE_DEVICES.copy()

            self.inactive_devices_key_text = {conf_device[CONF_IC3_DEVICENAME]: self._format_device_info(conf_device)
                                        for conf_device in Gb.conf_devices
                                        if conf_device[CONF_TRACKING_MODE] == INACTIVE_DEVICE}

            return vol.Schema({
                vol.Required('inactive_devices',
                            default=[]):
                            cv.multi_select(self.inactive_devices_key_text),

                vol.Required('action_items',
                            default=self.action_default_text('inactive_keep_inactive')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'icloud_account':
            self.actions_list = ICLOUD_ACCOUNT_ACTIONS.copy()
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)
            self._set_action_list_item_username_password()

            data_source_icloud_list = []
            data_source_mobapp_list = []
            if instr(self.data_source, FAMSHR): data_source_icloud_list.append(FAMSHR)
            # if instr(self.data_source, FMF):    data_source_icloud_list.append(FMF)
            if instr(self.data_source, MOBAPP): data_source_mobapp_list.append(MOBAPP)

            default_action = self.actions_list_default if self.actions_list_default else 'save'
            self.actions_list_default = ''

            if start_ic3.check_mobile_app_integration() is False:
                self.errors['data_source_mobapp'] = 'mobile_app_error'

            url_suffix_china = (Gb.icloud_server_endpoint_suffix == 'cn')

            return vol.Schema({
                vol.Optional('data_source_icloud',
                            default=data_source_icloud_list):
                            cv.multi_select(DATA_SOURCE_ICLOUD_ITEMS_KEY_TEXT),
                vol.Optional(CONF_USERNAME,
                            default=self.username):
                            selector.TextSelector(selector.TextSelectorConfig(type='password')),
                vol.Optional(CONF_PASSWORD,
                            default=self.password):
                            selector.TextSelector(selector.TextSelectorConfig(type='password')),
                vol.Optional('url_suffix_china',
                            default=url_suffix_china):
                            selector.BooleanSelector(),
                vol.Optional('data_source_mobapp',
                            default=data_source_mobapp_list):
                            cv.multi_select(DATA_SOURCE_MOBAPP_ITEMS_KEY_TEXT),

                vol.Required('action_items',
                            default=self.action_default_text(default_action)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'reauth':
            self.actions_list = REAUTH_ACTIONS.copy()
            # self._set_action_list_item_username_password()
            return vol.Schema({
                vol.Optional(CONF_VERIFICATION_CODE, default=' '):
                            selector.TextSelector(),
                vol.Required('action_items',
                            default=self.action_default_text('send_verification_code')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'device_list':

            action_default = 'add_device' if Gb.conf_devices == [] else 'update_device'

            idx = self.device_list_page_selected_idx[self.device_list_page_no]
            if len(self.form_devices_list_all) > 0:
                device_list_default = self.form_devices_list_all[idx]

            if Gb.conf_devices == []:
                self.actions_list = DEVICE_LIST_ACTIONS_ADD.copy()

            elif len(self.form_devices_list_all) <= 5:
                self.actions_list = DEVICE_LIST_ACTIONS.copy()

            else:
                devices_text = f"iCloud3 Devices: {self.next_page_devices_list}"
                next_page_text = ACTION_LIST_ITEMS_KEY_TEXT['next_page_items']
                next_page_text = next_page_text.replace('^info_field^', devices_text)
                self.actions_list = [next_page_text]
                self.actions_list.extend(DEVICE_LIST_ACTIONS)

            schema = {}
            schema = vol.Schema({})
            if self.form_devices_list_displayed != []:
                schema = schema.extend({
                    vol.Required('devices',
                                default=device_list_default):
                                selector.SelectSelector(selector.SelectSelectorConfig(
                                    options=self.form_devices_list_displayed)),
                })
            schema = schema.extend({
                vol.Required('action_items',
                            default=self.action_default_text(action_default)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })
            return schema

        #------------------------------------------------------------------------
        elif step_id == 'add_device':

            return vol.Schema({
                vol.Required(CONF_IC3_DEVICENAME,
                            default=self._parm_or_device(CONF_IC3_DEVICENAME)):
                            selector.TextSelector(),
                vol.Required(CONF_FNAME,
                            default=self._parm_or_device(CONF_FNAME)):
                            selector.TextSelector(),
                vol.Required(CONF_DEVICE_TYPE,
                            default=self._parm_or_device(CONF_DEVICE_TYPE, suggested_value=IPHONE)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(DEVICE_TYPE_FNAME), mode='dropdown')),
                vol.Required(CONF_TRACKING_MODE,
                            default=self._option_parm_to_text(CONF_TRACKING_MODE, TRACKING_MODE_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(TRACKING_MODE_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required('mobapp',
                            default=True):
                            #cv.boolean,
                            selector.BooleanSelector(),
                })

        #------------------------------------------------------------------------
        elif step_id == 'update_device':
            self._build_picture_filename_list()
            self._build_devicename_by_famshr_fmf(self.conf_device_selected[CONF_IC3_DEVICENAME])
            error_key = ''
            self.errors = self.errors or {}

            # If conf_famshr_devicename is not in available famshr values list, add it
            famshr_devicename = self.conf_device_selected[CONF_FAMSHR_DEVICENAME]
            famshr_list_text_by_fname = self.famshr_list_text_by_fname.copy()
            if famshr_devicename not in self.famshr_list_text_by_fname:
                error_key = '_famshr'
                self.errors[CONF_FAMSHR_DEVICENAME] = 'unknown_famshr'
                famshr_list_text_by_fname[famshr_devicename] = f"{famshr_devicename}{UNKNOWN_DEVICE_TEXT}"

            if self.PyiCloud:
                try:
                    if self.PyiCloud.FamilySharing.is_service_not_available:
                        famshr_list_text_by_fname[famshr_devicename] = f"{famshr_devicename}{DATA_ENTRY_ALERT}{SERVICE_NOT_AVAILABLE}"
                except:
                    famshr_list_text_by_fname[famshr_devicename] = f"{famshr_devicename}{DATA_ENTRY_ALERT}{SERVICE_NOT_STARTED_YET}"
            elif 'base' not in self.errors:
                self.errors['base'] = 'icloud_acct_not_available'

            # If conf_fmf_email is not in available fmf emails list, add it
            # fmf_email = self.conf_device_selected[CONF_FMF_EMAIL]
            # fmf_list_text_by_email = self.fmf_list_text_by_email.copy()
            # if fmf_email not in self.fmf_list_text_by_email:
            #     error_key = f"{error_key}_fmf"
            #     self.errors[CONF_FMF_EMAIL] = 'unknown_fmf'
            #     fmf_list_text_by_email[fmf_email] = f"{fmf_email}{UNKNOWN_DEVICE_TEXT}"

            if self.PyiCloud:
                pass
                # try:
                #     if self.PyiCloud.FindMyFriends.is_service_not_available:
                #         fmf_list_text_by_email[fmf_email] = f"{fmf_email}{DATA_ENTRY_ALERT}{SERVICE_NOT_AVAILABLE}"
                # except:
                #     fmf_list_text_by_email[fmf_email] = f"{fmf_email}{DATA_ENTRY_ALERT}{SERVICE_NOT_STARTED_YET}"
            elif 'base' not in self.errors:
                self.errors['base'] = 'icloud_acct_not_available'

            # If conf_mobapp_device is not in available mobapp devices list, add it
            mobapp_device = self.conf_device_selected[CONF_MOBILE_APP_DEVICE]
            mobapp_list_text_by_entity_id = self.mobapp_list_text_by_entity_id.copy()
            if mobapp_device not in mobapp_list_text_by_entity_id:
                error_key = f"{error_key}_mobapp"
                self.errors[CONF_MOBILE_APP_DEVICE] = 'unknown_mobapp'
                mobapp_list_text_by_entity_id[mobapp_device] = f"{mobapp_device}{UNKNOWN_DEVICE_TEXT}"

            picture_filename = self.conf_device_selected[CONF_PICTURE]
            picture_by_filename = self.picture_by_filename.copy()

            if picture_filename not in picture_by_filename:
                error_key = f"{error_key}_picture"
                self.errors[CONF_PICTURE] = 'unknown_picture'
                picture_by_filename[picture_filename] = f"{picture_filename}{UNKNOWN_DEVICE_TEXT}"
            if error_key and 'base' not in self.errors:
                self.errors['base'] = f'unknown{error_key}'

            if self.conf_device_selected[CONF_TRACKING_MODE] == INACTIVE_DEVICE:
                self.errors[CONF_TRACKING_MODE] = 'inactive_device'

            log_zones_key_text = {'none': 'None'}
            log_zones_key_text.update(self.zone_name_key_text)
            log_zones_key_text.update(LOG_ZONES_KEY_TEXT)

            return vol.Schema({
                vol.Required(CONF_IC3_DEVICENAME,
                            default=self._parm_or_device(CONF_IC3_DEVICENAME)):
                            selector.TextSelector(),
                vol.Required(CONF_FNAME,
                            default=self._parm_or_device(CONF_FNAME)):
                            selector.TextSelector(),
                vol.Required(CONF_DEVICE_TYPE,
                            default=self._option_parm_to_text(CONF_DEVICE_TYPE, DEVICE_TYPE_FNAME)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(DEVICE_TYPE_FNAME), mode='dropdown')),
                vol.Required(CONF_TRACKING_MODE,
                            default=self._option_parm_to_text(CONF_TRACKING_MODE, TRACKING_MODE_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(TRACKING_MODE_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_FAMSHR_DEVICENAME,
                            default=self._option_parm_to_text(CONF_FAMSHR_DEVICENAME, famshr_list_text_by_fname)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(famshr_list_text_by_fname), mode='dropdown')),
                # vol.Required(CONF_FMF_EMAIL,
                #             default=self._option_parm_to_text(CONF_FMF_EMAIL, fmf_list_text_by_email)):
                #             selector.SelectSelector(selector.SelectSelectorConfig(
                #                 options=dict_value_to_list(fmf_list_text_by_email), mode='dropdown')),
                vol.Required(CONF_MOBILE_APP_DEVICE,
                            default=self._option_parm_to_text(CONF_MOBILE_APP_DEVICE, mobapp_list_text_by_entity_id)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(mobapp_list_text_by_entity_id), mode='dropdown')),
                vol.Required(CONF_PICTURE,
                            default=self._option_parm_to_text(CONF_PICTURE, picture_by_filename)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(picture_by_filename), mode='dropdown')),

                vol.Optional(CONF_LOG_ZONES,
                            default=self._parm_or_device(CONF_LOG_ZONES)):
                            cv.multi_select(log_zones_key_text),
                vol.Required(CONF_TRACK_FROM_ZONES,
                            default=self._parm_or_device(CONF_TRACK_FROM_ZONES)):
                            cv.multi_select(self.zone_name_key_text),

                vol.Required(CONF_INZONE_INTERVAL,
                            default=self.conf_device_selected[CONF_INZONE_INTERVAL]):
                            # default=self._parm_or_device(CONF_INZONE_INTERVAL)):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Required(CONF_FIXED_INTERVAL,
                            default=self.conf_device_selected[CONF_FIXED_INTERVAL]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=0, max=480, step=5, unit_of_measurement='minutes')),
                vol.Required(CONF_TRACK_FROM_BASE_ZONE,
                            default=self._option_parm_to_text(CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text, conf_device=True)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'delete_device':
            self.actions_list = DELETE_DEVICE_ACTIONS.copy()
            device_info = ( f"{self.conf_device_selected[CONF_IC3_DEVICENAME]}, "
                            f"{self.conf_device_selected[CONF_FNAME]}")

            # The first item is 'Delete this device, add the selected device's info
            self.actions_list[0] = f"{self.actions_list[0]}{device_info}"

            return vol.Schema({
                vol.Required('action_items',
                            default=self.action_default_text('delete_device_cancel')):
                            selector.SelectSelector(
                                selector.SelectSelectorConfig(options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'actions':
            debug_items_key_text = ACTIONS_DEBUG_ITEMS.copy()
            if Gb.log_debug_flag:
                debug_items_key_text.pop('debug_start')
            else:
                debug_items_key_text.pop('debug_stop')
            if Gb.log_rawdata_flag:
                debug_items_key_text.pop('rawdata_start')
            else:
                debug_items_key_text.pop('rawdata_stop')

            return vol.Schema({
                vol.Optional('ic3_actions', default=[]):
                            cv.multi_select(ACTIONS_IC3_ITEMS),
                            # selector.SelectSelector(selector.SelectSelectorConfig(
                            #     options=dict_value_to_list(ACTIONS_IC3_ITEMS), mode='list')),
                vol.Optional('debug_actions', default=[]):
                            cv.multi_select(debug_items_key_text),
                            # selector.SelectSelector(selector.SelectSelectorConfig(
                            #     options=dict_value_to_list(debug_items_key_text), mode='list')),
                vol.Optional('other_actions', default=[]):
                            cv.multi_select(ACTIONS_OTHER_ITEMS),
                            # selector.SelectSelector(selector.SelectSelectorConfig(
                            #     options=dict_value_to_list(ACTIONS_OTHER_ITEMS), mode='list')),
                vol.Optional('action_items', default=[]):
                            cv.multi_select(ACTIONS_ACTION_ITEMS),
                            # selector.SelectSelector(selector.SelectSelectorConfig(
                            #     options=dict_value_to_list(ACTIONS_ACTION_ITEMS), mode='list')),
                })
        #------------------------------------------------------------------------
        elif step_id == 'format_settings':
            self._set_example_zone_name()
            self._build_log_level_devices_list()

            return vol.Schema({
                vol.Required(CONF_LOG_LEVEL_DEVICES,
                            default=Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                            cv.multi_select(self.log_level_devices_key_text),
                vol.Required(CONF_LOG_LEVEL,
                            default=self._option_parm_to_text(CONF_LOG_LEVEL, LOG_LEVEL_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(LOG_LEVEL_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_DISPLAY_ZONE_FORMAT,
                            default=self._option_parm_to_text(CONF_DISPLAY_ZONE_FORMAT, DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(DISPLAY_ZONE_FORMAT_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_DEVICE_TRACKER_STATE_SOURCE,
                            default=self._option_parm_to_text(CONF_DEVICE_TRACKER_STATE_SOURCE, DEVICE_TRACKER_STATE_SOURCE_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(DEVICE_TRACKER_STATE_SOURCE_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_UNIT_OF_MEASUREMENT,
                            default=self._option_parm_to_text(CONF_UNIT_OF_MEASUREMENT, UNIT_OF_MEASUREMENT_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list( UNIT_OF_MEASUREMENT_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_TIME_FORMAT,
                            default=self._option_parm_to_text(CONF_TIME_FORMAT, TIME_FORMAT_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(TIME_FORMAT_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_DISPLAY_GPS_LAT_LONG,
                            default=Gb.conf_general[CONF_DISPLAY_GPS_LAT_LONG]):
                            # cv.boolean,
                            selector.BooleanSelector(),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'change_device_order':
            self.actions_list = [
                    ACTION_LIST_ITEMS_KEY_TEXT['move_up'],
                    ACTION_LIST_ITEMS_KEY_TEXT['move_down']]
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            return vol.Schema({
                vol.Required('device_desc',
                            default=self.cdo_devicenames[self.cdo_curr_idx]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.cdo_devicenames, mode='list')),
                vol.Required('action_items',
                            default=self.action_default_text(self.actions_list_default)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'away_time_zone':
            self.actions_list = []
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            return vol.Schema({
                vol.Required(CONF_AWAY_TIME_ZONE_1_DEVICES,
                            default=Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
                            cv.multi_select(self.away_time_zone_devices_key_text),
                vol.Required(CONF_AWAY_TIME_ZONE_1_OFFSET,
                            default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET]]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

                vol.Required(CONF_AWAY_TIME_ZONE_2_DEVICES,
                            default=Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
                            cv.multi_select(self.away_time_zone_devices_key_text),
                vol.Required(CONF_AWAY_TIME_ZONE_2_OFFSET,
                            default=self.away_time_zone_hours_key_text[Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET]]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(self.away_time_zone_hours_key_text), mode='dropdown')),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'display_text_as':
            self.dta_selected_idx = self.dta_selected_idx_page[self.dta_page_no]
            if self.dta_selected_idx <= 4:
                dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                                if k <= 4]
                dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                                if k >= 5]
            else:
                dta_page_display_list = [v for k,v in self.dta_working_copy.items()
                                                if k >= 5]
                dta_next_page_display_list = [v.split('>')[0] for k,v in self.dta_working_copy.items()
                                                if k <= 4]

            dta_next_page_display_items = ", ".join(dta_next_page_display_list)
            next_page_text = ACTION_LIST_ITEMS_KEY_TEXT['next_page_items']
            next_page_text = next_page_text.replace('^info_field^', dta_next_page_display_items)
            self.actions_list = [next_page_text]
            self.actions_list.extend([ACTION_LIST_ITEMS_KEY_TEXT['select_text_as']])
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            return vol.Schema({
                vol.Required(CONF_DISPLAY_TEXT_AS,
                            default=self.dta_working_copy[self.dta_selected_idx]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dta_page_display_list)),
                vol.Required('action_items',
                            default=self.action_default_text('select_text_as')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'display_text_as_update':
            self.actions_list = [ACTION_LIST_ITEMS_KEY_TEXT['clear_text_as']]
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            if instr(self.dta_working_copy[self.dta_selected_idx], '>'):
                text_from_to_parts = self.dta_working_copy[self.dta_selected_idx].split('>')
                text_from = text_from_to_parts[0].strip()
                text_to   = text_from_to_parts[1].strip()
            else:
                text_from = ''
                text_to   = ''

            return vol.Schema({
                vol.Optional('text_from',
                            default=text_from):
                            selector.TextSelector(),
                vol.Optional('text_to'  ,
                            default=text_to):
                            selector.TextSelector(),
                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'tracking_parameters':
            self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

            self.picture_by_filename = {}
            if PICTURE_WWW_STANDARD_DIRS in Gb.conf_profile[CONF_PICTURE_WWW_DIRS]:
                Gb.conf_profile[CONF_PICTURE_WWW_DIRS] = []

            return vol.Schema({
                vol.Required(CONF_DISTANCE_BETWEEN_DEVICES,
                            default=Gb.conf_general[CONF_DISTANCE_BETWEEN_DEVICES]):
                            selector.BooleanSelector(),
                vol.Required(CONF_GPS_ACCURACY_THRESHOLD,
                            default=Gb.conf_general[CONF_GPS_ACCURACY_THRESHOLD]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=300, step=5, unit_of_measurement='m')),
                vol.Required(CONF_OLD_LOCATION_THRESHOLD,
                            default=Gb.conf_general[CONF_OLD_LOCATION_THRESHOLD]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=1, max=60, step=1, unit_of_measurement='minutes')),
                vol.Required(CONF_OLD_LOCATION_ADJUSTMENT,
                            default=Gb.conf_general[CONF_OLD_LOCATION_ADJUSTMENT]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=0, max=60, step=1, unit_of_measurement='minutes')),
                vol.Required(CONF_MAX_INTERVAL,
                            default=Gb.conf_general[CONF_MAX_INTERVAL]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=15, max=480, step=5, unit_of_measurement='minutes')),
                vol.Required(CONF_EXIT_ZONE_INTERVAL,
                            default=Gb.conf_general[CONF_EXIT_ZONE_INTERVAL]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=.5, max=10, step=.5, unit_of_measurement='minutes')),
                vol.Required(CONF_MOBAPP_ALIVE_INTERVAL,
                            default=Gb.conf_general[CONF_MOBAPP_ALIVE_INTERVAL]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=15, max=240, step=5, unit_of_measurement='minutes')),
                vol.Required(CONF_OFFLINE_INTERVAL,
                            default=Gb.conf_general[CONF_OFFLINE_INTERVAL]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=240, step=5, unit_of_measurement='minutes')),
                vol.Required(CONF_TFZ_TRACKING_MAX_DISTANCE,
                            default=Gb.conf_general[CONF_TFZ_TRACKING_MAX_DISTANCE]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=1, max=100, unit_of_measurement='Km')),
                vol.Optional(CONF_DISCARD_POOR_GPS_INZONE,
                            default=Gb.conf_general[CONF_DISCARD_POOR_GPS_INZONE]):
                            selector.BooleanSelector(),
                vol.Required(CONF_TRAVEL_TIME_FACTOR,
                            default=self._option_parm_to_text(CONF_TRAVEL_TIME_FACTOR, TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(TRAVEL_TIME_INTERVAL_MULTIPLIER_KEY_TEXT), mode='dropdown')),
                vol.Required(CONF_PICTURE_WWW_DIRS,
                            default=Gb.conf_profile[CONF_PICTURE_WWW_DIRS] or self.www_directory_list):
                            cv.multi_select(self.www_directory_list),
                vol.Required(CONF_EVLOG_CARD_DIRECTORY,
                            default=self._parm_or_error_msg(CONF_EVLOG_CARD_DIRECTORY, conf_group=CF_PROFILE)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(self.www_directory_list), mode='dropdown')),
                vol.Optional(CONF_EVLOG_BTNCONFIG_URL,
                            default=f"{self._parm_or_error_msg(CONF_EVLOG_BTNCONFIG_URL, conf_group=CF_PROFILE)} "):
                            selector.TextSelector(),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'inzone_intervals':
            return vol.Schema({
                vol.Optional(IPHONE,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][IPHONE]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Optional(IPAD,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][IPAD]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Optional(WATCH,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][WATCH]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Optional(AIRPODS,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][AIRPODS]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Optional(NO_MOBAPP,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][NO_MOBAPP]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),
                vol.Optional(OTHER,
                            default=Gb.conf_general[CONF_INZONE_INTERVALS][OTHER]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=5, max=480, step=5, unit_of_measurement='minutes')),

                vol.Optional('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'waze_main':
            self.actions_list = ACTION_LIST_ITEMS_BASE.copy()

            wuh_default  = [WAZE_USED_HEADER] if Gb.conf_general[CONF_WAZE_USED] else []
            whuh_default = [WAZE_HISTORY_USED_HEADER] if Gb.conf_general[CONF_WAZE_HISTORY_DATABASE_USED] else []
            return vol.Schema({
                vol.Optional(CONF_WAZE_USED,
                            default=wuh_default):
                            cv.multi_select([WAZE_USED_HEADER]),
                vol.Optional(CONF_WAZE_SERVER,
                            default=self._option_parm_to_text(CONF_WAZE_SERVER, WAZE_SERVER_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(WAZE_SERVER_ITEMS_KEY_TEXT), mode='dropdown')),
                vol.Optional(CONF_WAZE_MIN_DISTANCE,
                            default=Gb.conf_general[CONF_WAZE_MIN_DISTANCE]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=0, max=100, step=5, unit_of_measurement='km')),
                vol.Optional(CONF_WAZE_MAX_DISTANCE,
                            default=Gb.conf_general[CONF_WAZE_MAX_DISTANCE]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=0, max=1000, step=5, unit_of_measurement='km')),
                vol.Optional(CONF_WAZE_REALTIME,
                            default=Gb.conf_general[CONF_WAZE_REALTIME]):
                            selector.BooleanSelector(),

                vol.Required(CONF_WAZE_HISTORY_DATABASE_USED,
                            default=whuh_default):
                            cv.multi_select([WAZE_HISTORY_USED_HEADER]),
                vol.Required(CONF_WAZE_HISTORY_MAX_DISTANCE,
                            default=Gb.conf_general[CONF_WAZE_HISTORY_MAX_DISTANCE]):
                            selector.NumberSelector(selector.NumberSelectorConfig(
                                min=0, max=1000, step=5, unit_of_measurement='km')),
                vol.Required(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                            default=self._option_parm_to_text(CONF_WAZE_HISTORY_TRACK_DIRECTION,
                                                                WAZE_HISTORY_TRACK_DIRECTION_ITEMS_KEY_TEXT)):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=dict_value_to_list(WAZE_HISTORY_TRACK_DIRECTION_ITEMS_KEY_TEXT), mode='dropdown')),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == 'special_zones':
            try:
                if self.zone_name_key_text == {}:
                    self._build_zone_list()

                pass_thru_zone_used  = (Gb.conf_general[CONF_PASSTHRU_ZONE_TIME] > 0)
                stat_zone_used       = (Gb.conf_general[CONF_STAT_ZONE_STILL_TIME] > 0)
                track_from_base_zone_used = Gb.conf_general[CONF_TRACK_FROM_BASE_ZONE_USED]

                ptzh_default = [PASSTHRU_ZONE_HEADER] if pass_thru_zone_used else []
                szh_default  = [STAT_ZONE_HEADER] if stat_zone_used else []
                tfzh_default = [TRK_FROM_HOME_ZONE_HEADER] if track_from_base_zone_used else []

                return vol.Schema({
                    vol.Required('stat_zone_header',
                                default=szh_default):
                                cv.multi_select([STAT_ZONE_HEADER]),
                    vol.Required(CONF_STAT_ZONE_FNAME,
                                default=self._parm_or_error_msg(CONF_STAT_ZONE_FNAME)):
                                selector.TextSelector(),
                    vol.Required(CONF_STAT_ZONE_STILL_TIME,
                                default=Gb.conf_general[CONF_STAT_ZONE_STILL_TIME]):
                                selector.NumberSelector(selector.NumberSelectorConfig(
                                    min=0, max=60, unit_of_measurement='minutes')),
                    vol.Required(CONF_STAT_ZONE_INZONE_INTERVAL,
                                default=Gb.conf_general[CONF_STAT_ZONE_INZONE_INTERVAL]):
                                selector.NumberSelector(selector.NumberSelectorConfig(
                                    min=5, max=60, step=5, unit_of_measurement='minutes')),

                    vol.Optional('passthru_zone_header',
                                default=ptzh_default):
                                cv.multi_select([PASSTHRU_ZONE_HEADER]),
                    vol.Required(CONF_PASSTHRU_ZONE_TIME,
                                default=Gb.conf_general[CONF_PASSTHRU_ZONE_TIME]):
                                selector.NumberSelector(selector.NumberSelectorConfig(
                                    min=0, max=5, step=.5, unit_of_measurement='minutes')),

                    vol.Optional(CONF_TRACK_FROM_BASE_ZONE_USED,
                                default=tfzh_default):
                                cv.multi_select([TRK_FROM_HOME_ZONE_HEADER]),
                    vol.Required(CONF_TRACK_FROM_BASE_ZONE,
                                default=self._option_parm_to_text(CONF_TRACK_FROM_BASE_ZONE, self.zone_name_key_text)):
                                selector.SelectSelector(selector.SelectSelectorConfig(
                                    options=dict_value_to_list(self.zone_name_key_text), mode='dropdown')),
                    vol.Optional(CONF_TRACK_FROM_HOME_ZONE,
                                default=Gb.conf_general[CONF_TRACK_FROM_HOME_ZONE]):
                                # cv.boolean,
                                selector.BooleanSelector(),

                    vol.Required('action_items',
                                default=self.action_default_text('save')):
                                selector.SelectSelector(selector.SelectSelectorConfig(
                                    options=self.actions_list, mode='list')),
                    })
            except Exception as err:
                log_exception(err)

        #------------------------------------------------------------------------
        elif step_id == 'sensors':
            self.actions_list = [ACTION_LIST_ITEMS_KEY_TEXT['exclude_sensors']]
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            if HOME_DISTANCE not in Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]:
                Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE].append(HOME_DISTANCE)

            return vol.Schema({
                vol.Required(CONF_SENSORS_DEVICE,
                            default=Gb.conf_sensors[CONF_SENSORS_DEVICE]):
                            cv.multi_select(CONF_SENSORS_DEVICE_KEY_TEXT),
                vol.Required(CONF_SENSORS_TRACKING_UPDATE,
                            default=Gb.conf_sensors[CONF_SENSORS_TRACKING_UPDATE]):
                            cv.multi_select(CONF_SENSORS_TRACKING_UPDATE_KEY_TEXT),
                vol.Required(CONF_SENSORS_TRACKING_TIME,
                            default=Gb.conf_sensors[CONF_SENSORS_TRACKING_TIME]):
                            cv.multi_select(CONF_SENSORS_TRACKING_TIME_KEY_TEXT),
                vol.Required(CONF_SENSORS_TRACKING_DISTANCE,
                            default=Gb.conf_sensors[CONF_SENSORS_TRACKING_DISTANCE]):
                            cv.multi_select(CONF_SENSORS_TRACKING_DISTANCE_KEY_TEXT),
                vol.Required(CONF_SENSORS_ZONE,
                            default=Gb.conf_sensors[CONF_SENSORS_ZONE]):
                            cv.multi_select(CONF_SENSORS_ZONE_KEY_TEXT),
                vol.Required(CONF_SENSORS_OTHER,
                            default=Gb.conf_sensors[CONF_SENSORS_OTHER]):
                            cv.multi_select(CONF_SENSORS_OTHER_KEY_TEXT),
                # vol.Required(CONF_SENSORS_TRACK_FROM_ZONES,
                #             default=Gb.conf_sensors[CONF_SENSORS_TRACK_FROM_ZONES]):
                #             cv.multi_select(CONF_SENSORS_TRACK_FROM_ZONES_KEY_TEXT),
                vol.Required(CONF_SENSORS_MONITORED_DEVICES,
                            default=Gb.conf_sensors[CONF_SENSORS_MONITORED_DEVICES]):
                            cv.multi_select(CONF_SENSORS_MONITORED_DEVICES_KEY_TEXT),
                vol.Required(CONF_SENSORS_TRACKING_OTHER,
                            default=Gb.conf_sensors[CONF_SENSORS_TRACKING_OTHER]):
                            cv.multi_select(CONF_SENSORS_TRACKING_OTHER_KEY_TEXT),
                vol.Optional(CONF_EXCLUDED_SENSORS,
                            default=Gb.conf_sensors[CONF_EXCLUDED_SENSORS]):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=Gb.conf_sensors[CONF_EXCLUDED_SENSORS], mode='list', multiple=True)),

                vol.Required('action_items',
                            default=self.action_default_text('save')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })
        #------------------------------------------------------------------------
        elif step_id == 'exclude_sensors':
            self.actions_list = [ACTION_LIST_ITEMS_KEY_TEXT['filter_sensors']]
            self.actions_list.extend(ACTION_LIST_ITEMS_BASE)

            if self.sensors_list_filter == '?':
                filtered_sensors_fname_list = [f"None Displayed - Enter a Filter or `all` \
                                to display all sensors ({len(self.sensors_fname_list)} Sensors)"]
                filtered_sensors_list_default = []
            else:
                self.sensors_list_filter.replace('?', '')
                if self.sensors_list_filter.lower() == 'all':
                    filtered_sensors_fname_list = [sensor_fname
                                    for sensor_fname in self.sensors_fname_list
                                    if sensor_fname not in self.excluded_sensors]
                else:
                    filtered_sensors_fname_list = list(set([sensor_fname
                                    for sensor_fname in self.sensors_fname_list
                                    if ((instr(sensor_fname.lower(), self.sensors_list_filter)
                                        and sensor_fname not in self.excluded_sensors))]))

                filtered_sensors_list_default = list(set([sensor_fname
                                    for sensor_fname in filtered_sensors_fname_list
                                    if sensor_fname in self.excluded_sensors]))

                filtered_sensors_fname_list.sort()
                if filtered_sensors_fname_list == []:
                    filtered_sensors_fname_list = [f"No Sensors found containing \
                                                        '{self.sensors_list_filter}'"]

            return vol.Schema({
                vol.Optional(CONF_EXCLUDED_SENSORS,
                            default=self.excluded_sensors):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.excluded_sensors, mode='list', multiple=True)),
                vol.Optional('filter',
                            default=self.sensors_list_filter):
                            selector.TextSelector(),
                vol.Optional('filtered_sensors',
                            default=filtered_sensors_list_default):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=filtered_sensors_fname_list, mode='list', multiple=True)),

                vol.Required('action_items',
                            default=self.action_default_text('filter_sensors')):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id.startswith('restart_ha_ic3'):
            restart_default = 'restart_ha'
            self.actions_list = []
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['restart_ha'])
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['reload_icloud3'])
            self.actions_list.append(ACTION_LIST_ITEMS_KEY_TEXT['cancel'])

            actions_list_default = self.action_default_text(restart_default)

            return vol.Schema({
                vol.Required('action_items',
                            default=actions_list_default):
                            selector.SelectSelector(selector.SelectSelectorConfig(
                                options=self.actions_list, mode='list')),
                })

        #------------------------------------------------------------------------
        elif step_id == '':
            pass

        return schema
