
#   Constant file for device_tracker and sensors


from .const     import (DISTANCE_TO_DEVICES,
                        BLANK_SENSOR_FIELD,
                        NAME,
                        BADGE,
                        TRIGGER,
                        FROM_ZONE, ZONE_INFO, NEAR_DEVICE_USED,
                        ZONE, ZONE_DNAME, ZONE_NAME, ZONE_FNAME, ZONE_DATETIME,
                        LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME, LAST_ZONE_DATETIME,
                        INTERVAL,
                        BATTERY_SOURCE, BATTERY, BATTERY_STATUS, BATTERY_UPDATE_TIME,
                        BATTERY_FAMSHR, BATTERY_MOBAPP,
                        DISTANCE, ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, HOME_DISTANCE,
                        MAX_DISTANCE,CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME, DIR_OF_TRAVEL,
                        MOVED_DISTANCE, MOVED_TIME_FROM, MOVED_TIME_TO, WENT_3KM,
                        DEVICE_STATUS,
                        LAST_UPDATE, LAST_UPDATE_DATETIME,
                        NEXT_UPDATE, NEXT_UPDATE_DATETIME,
                        LAST_LOCATED, LAST_LOCATED_DATETIME,
                        INFO, GPS, GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY,
                        TFZ_ZONE_INFO, TFZ_DISTANCE, TFZ_ZONE_DISTANCE,  TFZ_DIR_OF_TRAVEL,
                        TFZ_TRAVEL_TIME,TFZ_TRAVEL_TIME_MIN, TFZ_TRAVEL_TIME_HHMM, TFZ_ARRIVAL_TIME,
                        TOWARDS, AWAY_FROM, TOWARDS_HOME, AWAY_FROM_HOME, INZONE, INZONE_HOME, INZONE_STATZONE,
                        SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME,
                        )

HA_EXCLUDE_SENSORS =    [SENSOR_EVENT_LOG_NAME, SENSOR_WAZEHIST_TRACK_NAME, ]
                        # '*_zone_datetime', '*_trigger', '*_info',
                        # '*_next_update', '*_last_update', '*_last_located', '*_interval',
                        # ]

SENSOR_LIST_DEVICE =    [NAME, BADGE, BATTERY, BATTERY_STATUS,
                        TRIGGER, INTERVAL, LAST_LOCATED,
                        INFO,
                        GPS_ACCURACY, ALTITUDE, VERTICAL_ACCURACY,
                        ]
SENSOR_LIST_TRACKING =  [NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        MOVED_DISTANCE, DIR_OF_TRAVEL,
                        WAZE_DISTANCE, CALC_DISTANCE,
                        ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, HOME_DISTANCE,
                        ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
                        LAST_ZONE, LAST_ZONE_FNAME, LAST_ZONE_NAME,
                        ]
SENSOR_LIST_TRACK_FROM_ZONE = [INFO, LAST_UPDATE, NEXT_UPDATE,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME, DIR_OF_TRAVEL,
                        ]
SENSOR_LIST_LOC_UPDATE =[TRIGGER, INTERVAL,
                        NEXT_UPDATE, LAST_UPDATE, LAST_LOCATED,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        ]
SENSOR_LIST_ZONE_NAME =[ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_NAME, ZONE_FNAME,
                        LAST_ZONE_NAME, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE,
                        LAST_ZONE_FNAME, LAST_ZONE_NAME,
                        ]
SENSOR_LIST_DISTANCE =  [DISTANCE, ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, HOME_DISTANCE,
                        ]

SENSOR_GROUPS = {
        'battery':      [BATTERY, BATTERY_STATUS],
        'md_badge':     [BADGE],
        'md_battery':   [BATTERY, BATTERY_STATUS],
        'md_location_sensors': [
                        NAME,
                        ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME,
                        HOME_DISTANCE,
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        LAST_LOCATED,
                        LAST_UPDATE,],
        'track_from_zone': [
                        TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        ZONE_DISTANCE, DISTANCE, DIR_OF_TRAVEL, 'zone_info', ]
}
SENSOR_ICONS = {
        TOWARDS_HOME: 'mdi:home-import-outline',
        AWAY_FROM_HOME: 'mdi:home-export-outline',
        TOWARDS: 'mdi:location-enter',
        AWAY_FROM: 'mdi:location-exit',
        INZONE: 'mdi:crosshairs-gps',
        INZONE_HOME: 'mdi:home-circle-outline',
        INZONE_STATZONE: 'mdi:target-account',
        'arrival_time_to_home': 'mdi:home-clock-outline',
        'arrival_time_in_home': 'mdi:home-clock',
        'arrival_time_to_tfz': 'mdi:map-clock-outline',
        'arrival_time_in_tfz': 'mdi:map-clock',
        'other': 'mdi:compass-outline',
        # INZONE_STATZONE: 'mdi:account-reactivate-outline',
}
'''
The Sensor Definition dictionary defines all sensors created by iCloud3.
        Key:
                Sensor id used in config_flow and in the en.json file (Ex: 'name', 'tfz_zone_distance')
        Item definition:
                Field 0:
                HA base sensor entity_id name.
                        Prefix: [devicename]
                        Suffix: [Track_from_zone name]
                        Examples:   'sensor.gary_iphone_battery', 'sensor.gary_iphone_zone_HOME_DISTANCE',
                                'sensor.bary_iphone_travel_time_home'
        Index 1:
                Sensor Friendly Name.
                        Prefix: [device fridndly name]/[device type]
                        Examples:   'Gary/iPhone Name', 'Gary/iPhone Distance Warehouse'
        Index 2:
                Sensor type used to determine the format of sensor and the Class object that should be used
        Index 3:
                mdi Icon for the sensor
        Index 4:
                List of attributes that should be added to the sensor

        Sesors excluded from the recorder:
                - icloud3_event_log
                - icloud3_wazehist_track
                - *_info
                - *_last_located
                - *_last_update
                - *_next_update
                - *_last_zone
                - *_last_zone_dname
                - *_last_zone_name
                - *_last_zone_fname
                - *_last_zone_datetime
                - *_zone_daetime
'''

SENSOR_SUFFIX = ''
SENSOR_FNAME  = 0
SENSOR_TYPE   = 1
SENSOR_ICON   = 2
SENSOR_ATTRS  = 3
SENSOR_DEFAULT= 4

SENSOR_DEFINITION = {
        # SENSOR_FIELD_ITEMS: [
        #         'Sensor Friendly Name',
        #         'Sensor Type-battery, text, info, distance, time, timer, timestamp, zone',
        #         'icon-mdi:xxx,
        #         [attributes from sensors[sensorname1, sensorname2, ...]],
        #         default value to display at startup,
        #       ]
        NAME: [
                'Name',
                'text',
                'mdi:account',
                [],
                BLANK_SENSOR_FIELD],
        BADGE: [
                'Badge',
                'badge',
                'mdi:shield-account',
                [NAME, BATTERY, ZONE, ZONE_FNAME,
                        HOME_DISTANCE,
                        MAX_DISTANCE, TRAVEL_TIME, DIR_OF_TRAVEL, INTERVAL,
                        DISTANCE_TO_DEVICES,
                        ZONE_DATETIME, LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME,
                        DEVICE_STATUS, ],
                BLANK_SENSOR_FIELD],
        BATTERY: [
                'Battery',
                'battery',
                'mdi:battery-outline',
                [BATTERY_STATUS, BATTERY_SOURCE, BATTERY_UPDATE_TIME,
                        BATTERY_FAMSHR, BATTERY_MOBAPP,
                        'mobapp_sensor-battery_level', ],
                0],
        BATTERY_STATUS: [
                'BatteryStatus',
                'text, title',
                'mdi:battery-outline',
                [BATTERY, BATTERY_SOURCE],
                ''],
        INFO: [
                'Info',
                'info, ha_history_exclude',
                'mdi:information-outline',
                [],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_UPDATE
        INTERVAL: [
                'Interval',
                'timer, secs',
                'mdi:clock-start',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                0],
        LAST_LOCATED: [
                'LastLocated',
                'timestamp, ha_history_exclude',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_UPDATE: [
                'LastUpdate',
                'timestamp, ha_history_exclude',
                'mdi:history',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],
        NEXT_UPDATE: [
                'NextUpdate',
                'timestamp, ha_history_exclude',
                'mdi:update',
                [LAST_LOCATED_DATETIME, LAST_UPDATE_DATETIME, NEXT_UPDATE_DATETIME],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_TIME
        TRAVEL_TIME: [
                'TravelTime',
                'timer, min',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                0],
        TRAVEL_TIME_MIN: [
                'TravelTime (min)',
                'timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                0],
        TRAVEL_TIME_HHMM: [
                'TravelTime (hh:mm)',
                'text',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                BLANK_SENSOR_FIELD],
        ARRIVAL_TIME: [
                'ArrivalTime',
                'text',
                SENSOR_ICONS[TOWARDS_HOME],     #'mdi:home-clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_DISTANCE
        ZONE_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, CALC_DISTANCE, WAZE_DISTANCE,
                        MAX_DISTANCE, NEAR_DEVICE_USED, WENT_3KM],
                0],
        HOME_DISTANCE: [
                'HomeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, CALC_DISTANCE, WAZE_DISTANCE,
                        MAX_DISTANCE, NEAR_DEVICE_USED, WENT_3KM, ],
                0],
        DISTANCE: [
                'Distance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, CALC_DISTANCE, WAZE_DISTANCE,
                        MAX_DISTANCE, NEAR_DEVICE_USED],
                0],
        DIR_OF_TRAVEL: [
                'Direction',
                'text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        ARRIVAL_TIME],
                BLANK_SENSOR_FIELD],
        MOVED_DISTANCE: [
                'MovedDistance',
                'distance, km-mi, m-ft',
                'mdi:map-marker-distance',
                [MOVED_TIME_FROM, MOVED_TIME_TO, DIR_OF_TRAVEL, GPS, 'last_gps'],
                0],
        ZONE_INFO: [
                'ZoneInfo',
                'zone_info',
                'mdi:map-marker-radius-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, DIR_OF_TRAVEL,
                        NEAR_DEVICE_USED],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACK_FROM_ZONES
        TFZ_ZONE_INFO: [
                'ZoneInfo',
                'zone_info',
                'mdi:map-marker-radius-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                        DISTANCE, MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, DIR_OF_TRAVEL],
                BLANK_SENSOR_FIELD],
        TFZ_TRAVEL_TIME: [
                'TravelTime',
                'timer, mins',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                0],
        TFZ_TRAVEL_TIME_MIN: [
                'TravelTimeMin',
                'timer',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                0],
        TFZ_TRAVEL_TIME_HHMM: [
                'TravelTime (hh:mm)',
                'text',
                'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                BLANK_SENSOR_FIELD],
        TFZ_ARRIVAL_TIME: [
                'ArrivalTime',
                'text',
                SENSOR_ICONS[TOWARDS],     #'mdi:clock-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        DIR_OF_TRAVEL, ARRIVAL_TIME, NEAR_DEVICE_USED],
                BLANK_SENSOR_FIELD],
        TFZ_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                        MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, NEAR_DEVICE_USED],
                0],
        TFZ_ZONE_DISTANCE: [
                'ZoneDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                        MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, NEAR_DEVICE_USED],
                0],
        TFZ_DIR_OF_TRAVEL: [
                'Direction',
                'text, title',
                'mdi:compass-outline',
                [FROM_ZONE, TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                        ARRIVAL_TIME, DISTANCE, MAX_DISTANCE],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_TRACKING_OTHER
        TRIGGER: [
                'Trigger',
                'text, ha_history_exclude',
                'mdi:flash-outline',
                [],
                BLANK_SENSOR_FIELD],
        WAZE_DISTANCE: [
                'WazeDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [WAZE_METHOD, FROM_ZONE, MAX_DISTANCE, DISTANCE, CALC_DISTANCE, WAZE_DISTANCE],
                0],
        CALC_DISTANCE: [
                'CalcDistance',
                'distance, km-mi',
                'mdi:map-marker-distance',
                [FROM_ZONE, MAX_DISTANCE, DISTANCE, CALC_DISTANCE, WAZE_DISTANCE],
                0],

        # CONF_SENSORS_ZONE
        ZONE: [
                'Zone',
                'zone',
                'mdi:crosshairs-gps',
                [ZONE, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        ZONE_DNAME: [
                'Zone',
                'zone',
                'mdi:crosshairs-gps',
                [ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        ZONE_FNAME: [
                'ZoneFname',
                'zone',
                'mdi:crosshairs-gps',
                [ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        ZONE_NAME: [
                'ZoneName',
                'zone',
                'mdi:crosshairs-gps',
                [ZONE, ZONE_DNAME, ZONE_FNAME, ZONE_NAME, ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        ZONE_DATETIME: [
                'ZoneChanged',
                'timestamp, ha_history_exclude',
                'mdi:clock-in',
                [],
                BLANK_SENSOR_FIELD],
        LAST_ZONE: [
                'LastZone',
                'zone',    #, ha_history_exclude',
                'mdi:crosshairs-gps',
                [LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_DNAME: [
                'LastZone',
                'zone',    #, ha_history_exclude',
                'mdi:crosshairs-gps',
                [LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_FNAME: [
                'LastZone',
                'zone',    #, ha_history_exclude',
                'mdi:crosshairs-gps',
                [LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_NAME: [
                'LastZone',
                'zone',    #, ha_history_exclude',
                'mdi:crosshairs-gps',
                [LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_FNAME, LAST_ZONE_NAME, LAST_ZONE_DATETIME],
                BLANK_SENSOR_FIELD],
        LAST_ZONE_DATETIME: [
                'ZoneChanged',
                'timestamp, ha_history_exclude',
                'mdi:clock-in',
                [],
                BLANK_SENSOR_FIELD],

        # CONF_SENSORS_OTHER
        GPS_ACCURACY: [
                'GPSAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
        ALTITUDE: [
                'Altitude',
                'distance, m-ft',
                'mdi:arrow-compress-up',
                [VERTICAL_ACCURACY],
                0],
        VERTICAL_ACCURACY: [
                'VerticalAccuracy',
                'distance, m',
                'mdi:map-marker-radius',
                [],
                0],
}
