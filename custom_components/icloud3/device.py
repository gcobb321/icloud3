#------------------------------------------------------------------------------
#
#   This module handles all device data
#
#------------------------------------------------------------------------------
from .global_variables  import GlobalVariables as Gb
from .const             import (DEVICE_TRACKER, DEVICE_TRACKER_DOT, CIRCLE_STAR2, LTE, GTE,
                                NOTIFY, DISTANCE_TO_DEVICES, NEAR_DEVICE_DISTANCE,
                                DISTANCE_TO_OTHER_DEVICES, DISTANCE_TO_OTHER_DEVICES_DATETIME,
                                HOME, HOME_FNAME, NOT_HOME, NOT_SET, UNKNOWN, NOT_HOME_ZONES,
                                DOT, RED_X, RARROW, RED_STOP, RED_ALERT, CRLF_DOT, CRLF_HDOT,
                                EVLOG_ALERT, BLANK_SENSOR_FIELD,
                                TOWARDS, AWAY, AWAY_FROM, INZONE, STATIONARY, STATIONARY_FNAME,
                                TOWARDS_HOME, AWAY_FROM_HOME, INZONE_HOME, INZONE_STATZONE,
                                STATE_TO_ZONE_BASE, DEVICE_TRACKER_STATE,
                                PAUSED, PAUSED_CAPS, RESUMING,
                                DATETIME_ZERO, HHMMSS_ZERO,HHMM_ZERO, HIGH_INTEGER,
                                TRACKING_NORMAL, TRACKING_PAUSED, TRACKING_RESUMED,
                                LAST_CHANGED_SECS, LAST_CHANGED_TIME, LAST_UPDATED_SECS, LAST_UPDATED_TIME,
                                STATE,
                                ICLOUD, MOBAPP, DEVICE_TYPE_ICONS,
                                TRACK_DEVICE, MONITOR_DEVICE, INACTIVE_DEVICE, TRACKING_MODE_FNAME,
                                NAME, DEVICE_TYPE_FNAME,
                                ICLOUD_HORIZONTAL_ACCURACY, ICLOUD_VERTICAL_ACCURACY, ICLOUD_POSITION_TYPE,
                                ICLOUD_BATTERY_LEVEL, ICLOUD_DEVICE_CLASS, ICLOUD_DEVICE_STATUS, ICLOUD_LOW_POWER_MODE, ID,
                                FRIENDLY_NAME, PICTURE, ICON, BADGE, ALERT,
                                LATITUDE, LONGITUDE, POSITION_TYPE,
                                LOCATION, LOCATION_SOURCE, TRIGGER, TRACKING, NEAR_DEVICE_USED,
                                FROM_ZONE, INTERVAL,
                                ZONE, ZONE_DNAME, ZONE_NAME, ZONE_FNAME, ZONE_DATETIME,
                                LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME, LAST_ZONE_DATETIME,
                                BATTERY_SOURCE, BATTERY, BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW,
                                BATTERY_ICLOUD, BATTERY_MOBAPP, BATTERY_LATEST,
                                BATTERY_STATUS_CODES, BATTERY_STATUS_FNAME, BATTERY_UPDATE_TIME,
                                ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE, HOME_DISTANCE, MAX_DISTANCE,
                                CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME, DIR_OF_TRAVEL,
                                MOVED_DISTANCE, MOVED_TIME_FROM, MOVED_TIME_TO, WENT_3KM,
                                DEVICE_STATUS, LOW_POWER_MODE, RAW_MODEL, MODEL, MODEL_DISPLAY_NAME,
                                LAST_UPDATE, LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
                                NEXT_UPDATE, NEXT_UPDATE_TIME, NEXT_UPDATE_DATETIME,
                                LAST_LOCATED, LAST_LOCATED_SECS, LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
                                INFO, GPS_ACCURACY, GPS, VERT_ACCURACY, ALTITUDE,
                                DEVICE_STATUS_CODES, DEVICE_STATUS_OFFLINE, DEVICE_STATUS_PENDING,
                                CONF_TRACK_FROM_BASE_ZONE, CONF_TRACK_FROM_ZONES, CONF_LOG_ZONES,
                                CONF_FNAME, FRIENDLY_NAME, PICTURE, ICON, BADGE,
                                CONF_PICTURE, CONF_ICON,  CONF_STAT_ZONE_FNAME,
                                CONF_DEVICE_TYPE, CONF_RAW_MODEL, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_APPLE_ACCOUNTS, CONF_APPLE_ACCOUNT, CONF_FAMSHR_DEVICENAME, CONF_USERNAME,
                                CONF_MOBILE_APP_DEVICE,
                                CONF_TRACKING_MODE, CONF_INZONE_INTERVAL, CONF_FIXED_INTERVAL, )

from .const_sensor      import (SENSOR_LIST_ZONE_NAME, SENSOR_ICONS, )
from .                  import device_fm_zone
from .tracking          import determine_interval as det_interval
from .startup           import restore_state
from .startup           import config_file
from .utils             import entity_io

from .utils.utils       import (instr, is_zone, isnot_zone, is_statzone, list_add, list_del,
                                circle_letter, format_gps, zone_dname, username_id, )
from .utils.messaging   import (post_event, post_alert, post_error_msg, post_monitor_msg,
                                post_greenbar_msg, clear_greenbar_msg,
                                log_exception, log_debug_msg, log_error_msg, log_data,
                                post_internal_error, _evlog, _log, )
from .utils.time_util   import (time_now_secs, secs_to_time, s2t, time_now, datetime_now,
                                secs_since, mins_since, secs_to, mins_to, secs_to_hhmm,
                                format_timer, format_secs_since, time_to_12hrtime,
                                secs_to_datetime,
                                format_age, format_time_age, format_age_hrs, )
from .utils.dist_util   import (gps_distance_m, gps_distance_km,
                                km_to_um, m_to_um, m_to_um_ft, )
from .utils.format      import (icon_circle, icon_box, )

#--------------------------------------------------------------------
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.util import slugify
from collections        import OrderedDict
import traceback
import copy

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3_Device(TrackerEntity):

    def __init__(self, devicename, conf_device):
        self.setup_time            = time_now()
        self.conf_device           = conf_device
        self.devicename            = devicename
        self.ha_device_id          = ''      # ha device_registry device_id
        self.fname                 = devicename.title()

        self.StatZone              = None    # The StatZone this Device is in or None if not in a StatZone
        self.AppleAcct             = None    # AppleAcct object for the Apple Account for this iCloud device

        self.FromZones_by_zone     = {}      # DeviceFmZones objects for the track_from_zones parameter for this Device
        self.FromZone_Home         = None    # DeviceFmZone object for the Home zone
        self.from_zone_names       = []      # List of the from_zones in the FromZones_by_zone dictionary
        self.only_track_from_home  = True    # Track from only Home  (True) or also track from other zones (False)
        self.FromZone_BeingUpdated = None    # DeviceFmZone object being updated in determine_interval for EvLog TfZ info
        self.FromZone_NextToUpdate = None    # Set to the DeviceFmZone when it's next_update_time is reached
        self.FromZone_TrackFrom    = None    # DeviceFmZone object for the Closest tfz - used to set the Device's sensors
        self.FromZone_LastIn       = None    # DeviceFmZone object the device was last in
        self.TrackFromBaseZone     = None    # DeviceFmZone of Home or secondary tracked from zone
        self.track_from_base_zone  = HOME    # Name of secondary tracked from base zone (normally Home)
        self.NearDevice            = None    # Device in the same location as this Device
        self.NearDeviceUsed        = None
        self.DeviceTracker         = None    # Device's device_tracker entity object
        self.Sensors               = Gb.Sensors_by_devicename.get(devicename, {})
        self.Sensors_from_zone     = Gb.Sensors_by_devicename_from_zone.get(devicename, {})


        self.initialize()
        self.initialize_on_initial_load()
        self.initialize_sensors()

        self.configure_device(conf_device)
        self.initialize_track_from_zones()
        det_interval.determine_TrackFrom_zone(self)
        self._link_device_entities_sensor_device_tracker()

    def initialize(self):
        self.devicename_verified          = False
        self.verified_flag                = False    # Indicates this is a valid and trackable Device

        # Operational variables
        self.device_type                  = 'iPhone'
        self.raw_model                    = DEVICE_TYPE_FNAME(self.device_type)      # iPhone15,2
        self.model                        = DEVICE_TYPE_FNAME(self.device_type)      # iPhone
        self.model_display_name           = Gb.model_display_name_by_raw_model.get(self.raw_model, self.raw_model)  # iPhone 14 Pro
        self.data_source                  = None
        self.tracking_status              = TRACKING_NORMAL
        self.tracking_mode                = TRACK_DEVICE      #normal, monitor, inactive
        self.alert                        = ''
        self.last_data_update_secs        = time_now_secs()
        self.last_evlog_msg_secs          = time_now_secs()
        self.last_update_msg_secs         = time_now_secs()
        self.dist_from_zone_km_small_move_total = 0.0
        self.device_tracker_entity_ic3    = (f"{DEVICE_TRACKER}.{self.devicename}")
        self.last_zone                    = ''
        self.last_track_from_zone         = ''
        self.log_zones_filenames          = []              # Log Zone activity to a .csv file
        self.info_msg                     = ''              # results of last format_info_msg
        self.went_3km                     = False
        self.near_device_group            = 0               # Devices witin 50m are in the same  tracking sync group
        self.near_device_distance         = 0.0             # Distance to the NearDevice device
        self.near_device_checked_secs     = 0               # When the nearby devices were last updated
        self.near_device_used             = ''
        self.dist_apart_msg               = ''              # Distance to all other devices msg set in icloud3_main
        self.dist_apart_msg_by_devicename = {}              # Distance to all other devices msg set in icloud3_main
        self.dist_apart_msg2              = ''              # Distance to all other devices msg set in icloud3_main
        self.dist_apart_msg_by_devicename2= {}              # Distance to all other devices msg set in icloud3_main
        self.dist_to_devices_data         = []              # Near devices msg displayed in the det_interval.post_neary_devices_msg
        self.dist_to_devices_secs         = 0               # Near devices msg displayed in the det_interval.post_neary_devices_msg
        self.last_update_loc_secs         = 0               # Located secs from the device tracker entity update
        self.last_update_loc_time         = DATETIME_ZERO   # Located time from the device tracker entity update
        self.last_update_gps_accuracy     = 0
        self.passthru_zone                = ''
        self.passthru_zone_timer          = 0               # Timer (secs) when the passthru zone delay expires
        self.selected_zone_results        = []              # ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list

        # Trigger & Update variables
        self.trigger                      = 'iCloud3'
        self.interval_secs                = 0
        self.interval_str                 = ''
        self.next_update_secs             = 0
        self.seen_this_device_flag        = False
        self.mobapp_zone_enter_secs       = 0
        self.mobapp_zone_enter_time       = HHMMSS_ZERO
        self.mobapp_zone_enter_zone       = ''
        self.mobapp_zone_enter_dist_m     = -1
        self.mobapp_zone_enter_trigger_info= ''
        self.mobapp_zone_exit_secs        = 0
        self.mobapp_zone_exit_time        = HHMMSS_ZERO
        self.mobapp_zone_exit_zone        = ''
        self.mobapp_zone_exit_dist_m      = -1
        self.mobapp_zone_exit_trigger_info= ''
        self.update_in_process_flag       = False
        self.device_being_updated_retry_cnt = 0
        self.got_exit_trigger_flag        = False
        self.outside_no_exit_trigger_flag = False
        self.moved_since_last_update_km   = 0

        # Fields used in iCloud initialization
        self.icloud_device_id        = ''     #       "
        self.icloud_person_id        = ''     # icloud person id that's a key into the Gb.Devices_by_person_id

        # StatZone fields
        self.statzone_latitude       = 0.0
        self.statzone_longitude      = 0.0
        self.statzone_timer          = 0
        self.statzone_dist_moved_km  = 0.0
        self.statzone_setup_secs     = 0     # Time the statzone was set up

        # iCloud3 configration fields
        self.conf_apple_acct_username= ''
        self.conf_icloud_dname       = ''     # The iCloud famshr devicename parameter used to select the device's iCloud data
        self.conf_icloud_devicename  = ''     # slugified version of the dname value
        self.conf_icloud_device_id   = ''
        self.family_share_device     = False        # False=One of Apple acct owners devices, True=Family Share device
        self.conf_mobapp_fname       = ''

        # Device source
        self.primary_data_source     = ICLOUD
        self.is_data_source_ICLOUD   = True
        self.is_data_source_MOBAPP   = True
        self.verified_ICLOUD         = False
        self.verified_MOBAPP         = False

        # Device location & gps fields
        self.old_loc_cnt             = 0   # Number of old locations received from Apple in a row
        self.max_error_cycle_cnt     = 0   # Number of times the old loc interval retry  time has cycled
        self.old_loc_msg             = ''
        self.old_loc_threshold_secs  = 120
        self.poor_gps_flag           = False
        self.inzone_interval_secs    = 600
        self.fixed_interval_secs     = 0
        self.statzone_inzone_interval_secs = min(self.inzone_interval_secs, Gb.statzone_inzone_interval_secs)
        self.check_zone_exit_secs    = 0        # Time when a MobApp exited a zone and a non-MobApp was exit check was issued
        self.offline_secs            = 0        # Time the device went offline
        self.pending_secs            = 0        # Time the device went into a pending status (checked after authentication)
        self.dist_to_other_devices_secs = 0
        self.dist_to_other_devices   = {}       # A dict of other devices distances
        self.dist_to_other_devices2  = {}       # A dict of other devices distances
                                                # {devicename: [distance_m, gps_accuracy_factor, location_old_flag]}
        self.loc_time_updates_icloud = [HHMMSS_ZERO]       # History of update times from one results to the next
        self.loc_time_updates_mobapp = [HHMMSS_ZERO]       # History of update times from one results to the next
        self.loc_msg_icloud_mobapp_time = ''    # Time string the locate msg was displayed to prevent dup msgs (icl_data_handlr)
        self.dev_data_useable_chk_secs = 0      # The device data is checked several times during an update
        self.dev_data_useable_chk_results = []  # If this check is the same as the last one, return the previous results

        self.last_mobapp_msg         = ''
        self.last_device_monitor_msg = ''
        self.mobapp_statzone_action_msg_cnt = 0

        self.time_waze_calls         = 0.0

        # Device MobApp message fields
        self.mobapp_request_loc_first_secs = 0    # Used for checking if alive and user request
        self.mobapp_request_loc_last_secs  = 0    # Used for checking if alive and user request
        self.mobapp_request_loc_cnt        = 0
        self.mobapp_request_loc_sent_secs  = 0    # Used for tracking in 5-sec loop when the data source is mobapp
        self.mobapp_request_sensor_update_secs = 0

        # MobApp state variables
        self.mobapp_data_gps_accuracy      = 0
        self.mobapp_data_vertical_accuracy = 0
        self.mobapp_data_altitude          = 0.0

        # Mobile App data update control variables
        self.mobapp_monitor_flag           = False
        self.mobapp_device_unavailable_flag= False
        self.invalid_error_cnt             = 0
        self.mobapp_data_invalid_error_cnt = 0
        self.mobapp_data_updated_flag      = False
        self.mobapp_data_change_reason     = ''         # Why a state/trigger is causing an update
        self.mobapp_data_reject_reason     = ''         # Why a state/trigger was not updated
        self.mobapp_update_flag            = False
        self.last_mobapp_trigger           = ''

        # iCloud data update control variables
        self.icloud_force_update_flag      = False      # Bypass all update needed checks and force an iCloud update
        self.icloud_devdata_useable_flag   = False
        self.icloud_acct_error_flag        = False      # An error occured from the iCloud account update request
        self.icloud_update_reason          = 'Trigger > Initial Locate'
        self.icloud_no_update_reason       = ''
        self.icloud_update_retry_flag      = False       # Set to True for initial locate
        self.icloud_initial_locate_done    = False

        # Final update control variables -
        self.update_sensors_flag           = False       # The data is good and tracking can be updated
        self.update_sensors_error_msg      = ''          # Reason an error message will be displayed

        # Log zone activity variables
        self.log_zone                      = ''          # Zone entered that is being logged
        self.log_zone_enter_secs           = 0

        # Location Data from iCloud or the Mobile App
        self.dev_data_source             = NOT_SET          #icloud or mobapp data
        self.dev_data_fname              = ''
        self.dev_data_device_class       = 'iPhone'
        self.dev_data_device_status      = "Online"
        self.dev_data_device_status_code = 200
        self.dev_data_low_power_mode     = False

        self.loc_data_zone           = NOT_SET
        self.loc_data_latitude       = 0.0
        self.loc_data_longitude      = 0.0
        self.loc_data_position_type  = ''
        self.loc_data_gps_accuracy   = 0
        self.loc_data_secs           = 0
        self.loc_data_time           = HHMMSS_ZERO
        self.loc_data_datetime       = DATETIME_ZERO
        self.loc_data_altitude       = 0.0
        self.loc_data_vert_accuracy  = 0
        self.loc_data_isold          = False
        self.loc_data_ispoorgps      = False
        self.loc_data_dist_moved_km  = 0.0
        self.loc_data_time_moved_from = DATETIME_ZERO
        self.loc_data_time_moved_to   = DATETIME_ZERO
        self.last_loc_data_time_gps   = "Initial Locate"

        self.sensor_prefix            = (f"sensor.{self.devicename}_")

        # Test variables used for saving the last value of a variable during debugging
        self.debug_save_number            = 0
        self.debug_save_string            = ''
        self.debug_save_list              = []
        self.debug_save_dict              = {}

    def __repr__(self):
        return (f"<{self.devicename}>")

#------------------------------------------------------------------------------
    def initialize_on_initial_load(self):
        # Initialize these variables only when starting up
        # Do not initialize them on a restart

        # If self.sensors exists, this device has been initialized during the initial
        # load or when iC3 is restarted and it is not a new device.
        try:
            if self.sensors != {}:
                return
        except:
            pass

        self.initialize_mobapp_device_tracker_entity_name()

        # MobApp state variables
        self.update_mobapp_data_monitor_msg= ''
        self.mobapp_data_state             = NOT_SET
        self.mobapp_data_latitude          = 0.0
        self.mobapp_data_longitude         = 0.0
        self.mobapp_data_source_type       = ''
        self.mobapp_data_state_secs        = 0
        self.mobapp_data_state_time        = HHMMSS_ZERO
        self.mobapp_data_trigger_secs      = 0
        self.mobapp_data_trigger_time      = HHMMSS_ZERO
        self.mobapp_data_secs              = 0
        self.mobapp_data_time              = HHMMSS_ZERO
        self.mobapp_data_trigger           = NOT_SET
        self.mobapp_data_battery_level     = 0
        self.mobapp_data_battery_status    = UNKNOWN
        self.mobapp_data_battery_update_secs = 0
        self._restore_state_reset_mobapp_items()

        self.zone_change_datetime         = DATETIME_ZERO
        self.zone_change_secs             = 0
        self._restore_state_reset_other_items()

        self.dev_data_battery_source      = ''
        self.dev_data_battery_level       = 0
        self.dev_data_battery_status      = UNKNOWN
        self.dev_data_battery_update_secs = 0
        self.dev_data_battery_level_last  = 0
        self.dev_data_battery_status_last = UNKNOWN
        self.last_battery_msg             = '0%, not_set'
        self.last_battery_msg_secs        = 0

        # rc9 Added battery_info sensors to display last battery data for icloud
        # & mobapp sensor.battery attributes
        self.battery_info                 = {ICLOUD: '', MOBAPP: ''}

    def initialize_mobapp_device_tracker_entity_name(self):
        self.mobapp = { DEVICE_TRACKER: '',
                        TRIGGER: '',
                        BATTERY_LEVEL: '',
                        BATTERY_STATUS: '',
                        NOTIFY: ''}

#------------------------------------------------------------------------------
    def initialize_sensors(self):
        # device_tracker.[devicename] attributes for the Device

        self.attrs              = {}
        self.kwargs             = {}
        self.sensors            = {}
        self.sensors_icon       = {}
        self.sensor_badge_attrs = {}

        # Device related sensors
        self.sensors[DEVICE_TRACKER_STATE] = None
        self.sensors[NAME]               = ''
        self.sensors[PICTURE]            = ''
        self.sensors[ICON]               = 'mdi:account'
        self.sensors[BADGE]              = ''
        self.sensors[LOW_POWER_MODE]     = ''
        self.sensors[INFO]               = ''
        self.sensors[ALERT]              = ''

        self.sensors[BATTERY]            = 0
        self.sensors[BATTERY_STATUS]     = UNKNOWN
        self.sensors[BATTERY_SOURCE]     = ''
        self.sensors[BATTERY_UPDATE_TIME] = HHMMSS_ZERO
        self.sensors['mobapp_sensor-battery_level']  = ''
        self.sensors['mobapp_sensor-battery_status'] = ''

        # rc9 Added battery_icloud & battery_mobapp to display battery_info data
        self.sensors[BATTERY_ICLOUD]     = ''
        self.sensors[BATTERY_MOBAPP]     = ''
        self.sensors[BATTERY_LATEST]     = ''

        # Location related items
        self.sensors[GPS]                = (0, 0)
        self.sensors['last_gps']         = (0, 0)
        self.sensors[LATITUDE]           = 0.0
        self.sensors[LONGITUDE]          = 0.0
        self.sensors[GPS_ACCURACY]       = 0
        self.sensors[ALTITUDE]           = 0
        self.sensors[VERT_ACCURACY]      = 0
        self.sensors[LOCATION_SOURCE]    = ''             #icloud: icloud or mobapp
        self.sensors[NEAR_DEVICE_USED]   = ''
        self.sensors[TRIGGER]            = ''
        self.sensors[LAST_LOCATED_DATETIME] = DATETIME_ZERO
        self.sensors[LAST_LOCATED_TIME]     = HHMMSS_ZERO
        self.sensors[LAST_LOCATED]          = HHMMSS_ZERO

        self.sensors['dev_id']           = ''
        self.sensors[RAW_MODEL]          = ''
        self.sensors[MODEL]              = ''
        self.sensors[MODEL_DISPLAY_NAME] = ''
        self.sensors['host_name']        = ''
        self.sensors[POSITION_TYPE]      = ''
        self.sensors[DEVICE_STATUS]      = UNKNOWN
        self.sensors[TRACKING]           = ''
        self.sensors[DISTANCE_TO_DEVICES]= ''
        self.sensors[DISTANCE_TO_OTHER_DEVICES] = {}
        self.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO

        # Sensors overlaid with DeviceFmZone sensors for nearest zone
        self.sensors[FROM_ZONE]             = ''
        self.sensors[INTERVAL]              = ''
        self.sensors[NEXT_UPDATE_DATETIME]  = DATETIME_ZERO
        self.sensors[NEXT_UPDATE_TIME]      = HHMMSS_ZERO
        self.sensors[NEXT_UPDATE]           = HHMMSS_ZERO
        self.sensors[LAST_UPDATE_DATETIME]  = DATETIME_ZERO
        self.sensors[LAST_UPDATE_TIME]      = HHMMSS_ZERO
        self.sensors[LAST_UPDATE]           = HHMMSS_ZERO
        self.sensors[TRAVEL_TIME]           = 0
        self.sensors[TRAVEL_TIME_MIN]       = 0
        self.sensors[TRAVEL_TIME_HHMM]      = HHMM_ZERO
        self.sensors[ARRIVAL_TIME]          = HHMM_ZERO
        self.sensors[ZONE_DISTANCE]         = 0.0
        self.sensors[ZONE_DISTANCE_M]       = 0.0
        self.sensors[ZONE_DISTANCE_M_EDGE]  = 0.0
        self.sensors[HOME_DISTANCE]         = 0.0
        self.sensors[MAX_DISTANCE]          = 0.0
        self.sensors[WENT_3KM]              = False
        self.sensors[WAZE_DISTANCE]         = 0.0
        self.sensors[WAZE_METHOD]           = ''
        self.sensors[CALC_DISTANCE]         = 0.0
        self.sensors[DIR_OF_TRAVEL]         = NOT_SET
        self.sensors[MOVED_DISTANCE]        = 0.0
        self.sensors[MOVED_TIME_FROM]       = DATETIME_ZERO
        self.sensors[MOVED_TIME_TO]         = DATETIME_ZERO

        # Zone related items
        self.sensors[ZONE]               = NOT_SET
        self.sensors[ZONE_DNAME]         = NOT_SET
        self.sensors[ZONE_FNAME]         = NOT_SET
        self.sensors[ZONE_NAME]          = NOT_SET
        self.sensors[ZONE_DATETIME]      = DATETIME_ZERO
        self.sensors[LAST_ZONE]          = NOT_SET
        self.sensors[LAST_ZONE_DNAME]    = NOT_SET
        self.sensors[LAST_ZONE_FNAME]    = NOT_SET
        self.sensors[LAST_ZONE_NAME]     = NOT_SET
        self.sensors[LAST_ZONE_DATETIME] = DATETIME_ZERO

        # Initialize the Device sensors[xxx] value from the restore_state file if
        # the sensor is in the file. Otherwise, initialize to this value. This will preserve
        # non-tracking sensors across restarts
        self._restore_sensors_from_restore_state_file()

        self.sensors[DISTANCE_TO_OTHER_DEVICES] = {}
        self.sensors[DISTANCE_TO_OTHER_DEVICES_DATETIME] = HHMMSS_ZERO
        self.sensors[ALERT] = ''

#------------------------------------------------------------------------------
    def _link_device_entities_sensor_device_tracker(self):
        # The DeviceTracker & Sensors entities are created before the Device object
        # using the configuration parameters. Cycle thru them now to set there
        # self.Device, device_id and area_id variables to this Device object.
        # This permits access to the sensors & attrs values.

        # Link the DeviceTracker-Device objects
        if self.devicename in Gb.DeviceTrackers_by_devicename:
            self.DeviceTracker = Gb.DeviceTrackers_by_devicename[self.devicename]
            self.DeviceTracker.Device = self
            try:
                self.DeviceTracker.device_id = Gb.ha_device_id_by_devicename[self.devicename]
                self.DeviceTracker.area_id   = Gb.ha_area_id_by_devicename[self.devicename]
            except:
                pass

        # Cycle through all sensors for this device.
        # Link the Sensor-Device objects to provide access the sensors dictionary
        # when they are updated.
        for Sensor in self.Sensors.values():
            Sensor.Device = self

        for sensor, Sensor in self.Sensors_from_zone.items():
            Sensor.Device = self

#------------------------------------------------------------------------------
    def configure_device(self, conf_device):

        # Configuration parameters
        # Change Monitored to tracked if primary data source is MOBAPP since
        # a monitored device only monitors the iCloud data and MobApp Data may be available
        self.tracking_mode        = conf_device.get(CONF_TRACKING_MODE, TRACK_DEVICE)
        self.sensors['dev_id']    = self.devicename
        self.evlog_fname_alert_char = ''          # Character added to the fname in the EvLog (❗❌⚠️)

        self._initialize_data_source_fields(conf_device)
        self.initialize_non_tracking_config_fields(conf_device)
        self._validate_zone_parameters()

        self.raw_model            = conf_device.get(CONF_RAW_MODEL, self.device_type)  # iPhone15,2
        self.model                = conf_device.get(CONF_MODEL, self.device_type)      # iPhone
        self.model_display_name   = conf_device.get(CONF_MODEL_DISPLAY_NAME, self.device_type) # iPhone 14 Pro
        self.track_from_zones     = conf_device.get(CONF_TRACK_FROM_ZONES, [HOME]).copy()
        self.track_from_base_zone = conf_device.get(CONF_TRACK_FROM_BASE_ZONE, HOME)

        try:
            # Update tfz with master base zone, also remove Home zone if necessaryself.track_from_base_zone
            if (Gb.is_track_from_base_zone_used
                    and Gb.track_from_base_zone != HOME):
                self.track_from_base_zone = Gb.track_from_base_zone
                list_add(self.track_from_zones, self.track_from_base_zone)
                if Gb.track_from_home_zone is False:
                    list_del(self.track_from_zones, HOME)
            else:
                self.track_from_base_zone = conf_device[CONF_TRACK_FROM_BASE_ZONE]
                if self.track_from_base_zone == HOME:
                    list_add(self.track_from_zones, HOME)

            # Put it at the end of the track-from list
            if self.track_from_base_zone != self.track_from_zones[-1]:
                list_del(self.track_from_zones, self.track_from_base_zone)
                list_add(self.track_from_zones, self.track_from_base_zone)

        except Exception as err:
            log_exception(err)

    def _extract_devicename(self, device_field):
        # The xxx_device field will contain a '>' if it is a valid devicename that will be used
        if instr(device_field, '>'):
            device_name = device_field.split(' >')[0].strip()
        elif device_field.startswith('Select'):
            device_name = ''
        else:
            device_name = device_field

        return device_name

#------------------------------------------------------------------------------
    def initialize_non_tracking_config_fields(self, conf_device):
        '''
        Set the device's fields to the configuration for fields not related to device
        selection, data source, track_from zones or tracking related fields that require
        an iCloud3 restart

        DEVICE_NON_TRACKING_FIELDS =   [CONF_FNAME, CONF_PICTURE, CONF_DEVICE_TYPE, CONF_INZONE_INTERVAL,
                                        CONF_FIXED_INTERVAL, CONF_LOG_ZONES,
                                        CONF_AWAY_TIME_ZONE_1_OFFSET, CONF_AWAY_TIME_ZONE_1_DEVICES,
                                        CONF_AWAY_TIME_ZONE_2_OFFSET, CONF_AWAY_TIME_ZONE_2_DEVICES]
        '''

        self.fname                = conf_device.get(CONF_FNAME, self.devicename.title())
        self.sensors[NAME]        = self.fname_devicename
        self.sensors['host_name'] = self.fname

        self.sensor_badge_attrs[FRIENDLY_NAME] = self.fname
        # self.sensor_badge_attrs[ICON]          = conf_device.get(CONF_ICON, 'mdi:account-circle-outline')
        self.sensor_badge_attrs[ICON]          = conf_device.get(CONF_ICON, 'mdi:account')

        picture = conf_device.get(CONF_PICTURE, 'None')
        if picture == 'None':
            self.sensors[PICTURE] = ''

        else:
            picture = picture.replace('www/', '/local/')
            if picture.startswith('/local') is False:
                picture = f"/local/{picture}"
            self.sensors[PICTURE] = picture
            self.sensor_badge_attrs[PICTURE] = picture

        self.sensors[ICON]        = conf_device.get(CONF_ICON, 'mdi:account')
        self.inzone_interval_secs = conf_device.get(CONF_INZONE_INTERVAL, 30) * 60
        self.statzone_inzone_interval_secs = min(self.inzone_interval_secs, Gb.statzone_inzone_interval_secs)
        self.fixed_interval_secs  = conf_device.get(CONF_FIXED_INTERVAL, 0) * 60
        self.device_type          = conf_device.get(CONF_DEVICE_TYPE, 'iphone')
        self.log_zones            = conf_device.get(CONF_LOG_ZONES, ['none'])

        if (self.devicename in Gb.away_time_zone_1_devices
                or 'all' in Gb.away_time_zone_1_devices):
            self.away_time_zone_offset = Gb.away_time_zone_1_offset
        elif (self.devicename in Gb.away_time_zone_2_devices
                or 'all' in Gb.away_time_zone_2_devices):
            self.away_time_zone_offset = Gb.away_time_zone_2_offset
        else:
            self.away_time_zone_offset = 0

#--------------------------------------------------------------------
    def _initialize_data_source_fields(self, conf_device):

        if conf_device.get(CONF_FAMSHR_DEVICENAME, 'None') != 'None':
            self.conf_apple_acct_username = conf_device.get(CONF_APPLE_ACCOUNT, '')
            self.conf_icloud_dname        = conf_device.get(CONF_FAMSHR_DEVICENAME, '')
            self.conf_icloud_devicename   = slugify(self.conf_icloud_dname)

        if self.conf_apple_acct_username:
            username_devices = Gb.Devices_by_username.get(self.conf_apple_acct_username, [])
            Gb.Devices_by_username[self.conf_apple_acct_username] = list_add(username_devices, self)

        self. initialize_mobapp_device_tracker_entity_name()
        self.mobapp[DEVICE_TRACKER] = conf_device[CONF_MOBILE_APP_DEVICE]

        self.is_data_source_ICLOUD = Gb.conf_data_source_ICLOUD and self.conf_icloud_dname != ''
        self.is_data_source_MOBAPP = Gb.conf_data_source_MOBAPP and self.mobapp[DEVICE_TRACKER] != ''

        # Set primary data source
        if self.is_data_source_ICLOUD:
            self.primary_data_source = ICLOUD
        elif self.is_data_source_MOBAPP:
            self.primary_data_source = MOBAPP
            if self.is_monitored:
                self.tracking_mode = TRACK_DEVICE
        else:
            self.primary_data_source = None

#--------------------------------------------------------------------
    def initialize_track_from_zones(self):
        '''
        Cycle through each track_from_zones zone.
            - Validate the zone name
            - Create the DeviceFmZones object
            - Set up the global variables with the DeviceFmZone objects
        '''
        try:
            try:
                old_FromZones_by_zone = self.FromZones_by_zone.copy()
            except Exception as err:
                log_exception(err)
                old_FromZones_by_zone = {}

            self.FromZones_by_zone = {}

            # Validate the zone in the config parameter. If valid, get the Zone object
            # and add to the device's FromZones_by_zone object list
            if self.track_from_zones == [] or self.track_from_zones == '':
                self.track_from_zones = [HOME]

            # Reuse current DeviceFmZones if it exists.
            #track_from_zones = self.track_from_zones.copy()
            for zone in self.track_from_zones.copy():
                Zone = Gb.Zones_by_zone[zone]
                if Zone.passive:
                    idx = self.track_from_zones.index(zone)
                    self.track_from_zones[idx] = f"{LTE}{zone}-Passive{GTE}"
                    continue

                if zone in old_FromZones_by_zone:
                    FromZone = old_FromZones_by_zone[zone]
                    FromZone.__init__(self, zone)
                    post_monitor_msg(f"INITIALIZED DeviceFmZone > {self.devicename}:{zone}")

                else:
                    FromZone = device_fm_zone.iCloud3_DeviceFmZone(self, zone)
                    post_monitor_msg(f"ADDED DeviceFmZone > {self.devicename}:{zone}")

                self.FromZones_by_zone[zone] = FromZone

                self._restore_sensors_from_restore_state_file(zone, FromZone)

                if zone not in Gb.TrackedZones_by_zone:
                    Gb.TrackedZones_by_zone[zone] = Gb.Zones_by_zone[zone]

                if zone == self.track_from_base_zone:
                    self.FromZone_Home         = FromZone
                    self.FromZone_LastIn       = FromZone
                    self.FromZone_BeingUpdated = FromZone
                    self.FromZone_NextToUpdate = FromZone
                    self.FromZone_TrackFrom    = FromZone
                    self.TrackFromBaseZone     = FromZone
                    self.last_track_from_zone  = FromZone.from_zone

                FromZone.zone_dist_km = FromZone.sensors[ZONE_DISTANCE]

            # Set a list of tracked from zone names to make it easier to get them later
            self.from_zone_names = [k for k in self.FromZones_by_zone.keys()]
            self.only_track_from_home = (len(self.FromZones_by_zone) == 1)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def _validate_zone_parameters(self):
        '''
        See if there is an unknown zone in track from zones or log zone activity
        parameters. If one is found, remove it and update the Device's configuration
        '''
        invalid_zone_msg = ''
        tfz_zones = lza_zones = tfbz_zone = ''

        # Check track-from-zones
        if self.conf_device[CONF_TRACK_FROM_ZONES] in ['', []]:
            self.conf_device[CONF_TRACK_FROM_ZONES] = [HOME]
            tfz_zones += "Initialized"
        for zone in self.conf_device[CONF_TRACK_FROM_ZONES].copy():
            if zone not in Gb.HAZones_by_zone:
                tfz_zones += f"{zone}, "
                self.conf_device[CONF_TRACK_FROM_ZONES] = list_del(self.conf_device[CONF_TRACK_FROM_ZONES], zone)

        # Check log-zone-activity
        if (self.conf_device[CONF_LOG_ZONES] in ['', []]
                or (len(self.conf_device[CONF_LOG_ZONES]) == 1
                    and self.conf_device[CONF_LOG_ZONES][0].startswith('name-'))):
            self.conf_device[CONF_LOG_ZONES] = self.log_zones = ['none']

        for zone in self.conf_device[CONF_LOG_ZONES].copy():
            if zone.startswith('name-') or zone == 'none':
                continue
            if zone not in Gb.HAZones_by_zone:
                lza_zones += f"{zone}, "
                self.conf_device[CONF_LOG_ZONES] = list_del(self.conf_device[CONF_LOG_ZONES], zone)

        #Check Track from base zone
        if self.conf_device[CONF_TRACK_FROM_BASE_ZONE] not in Gb.Zones_by_zone:
            tfbz_zone += f"{zone}"
            invalid_zone_msg += f"{CRLF_HDOT}Track-from-base-Home zone setting"
            self.conf_device[CONF_TRACK_FROM_BASE_ZONE] = HOME

        if lza_zones or tfz_zones or tfbz_zone:
            config_file.write_icloud3_configuration_file()

            self.set_fname_alert(RED_ALERT)

            alert_msg = (f"{EVLOG_ALERT}CONFIGURATION PARAMETER ERROR > "
                        f"Unknown zones have been removed from the Device's "
                        f"configuration parameters. Verify these parameters "
                        f"on the Configure Settings > Update Device screen."
                        f"{CRLF_DOT}{self.fname_devicename}")
            zone_msg = ""
            if lza_zones:
                zone_msg = f"{CRLF_HDOT}Log Zone Activity ({lza_zones}), "
            if tfz_zones:
                zone_msg = f"{CRLF_HDOT}Track From Zone ({tfz_zones}), "
            if tfbz_zone:
                zone_msg = f"{CRLF_HDOT}Track From Base Home Zone ({tfbz_zone})"
            alert_msg += zone_msg
            post_event(alert_msg)
            log_error_msg(  f"ICLOUD3 ERROR > Unknown Zone removed from device parameter. "
                            f"Device-{self.fname_devicename}, {zone_msg}")

#--------------------------------------------------------------------
    def remove_zone_from_settings(self, zone):
        '''
        Remove a zone from the device's zone parameters"
            - track from zone
            - log zone activity
            - primary home zone
        '''
        try:
            if (zone == HOME
                    or Gb.start_icloud3_inprocess_flag):
                return

            conf_file_updated_flag = False
            if zone in self.track_from_zones:
                conf_file_updated_flag = True
                self.track_from_zones = list_del(self.track_from_zones, zone)
                self.from_zone_names = self.track_from_zones
                self.conf_device[CONF_TRACK_FROM_ZONES] = self.track_from_zones
                if zone in self.FromZones_by_zone:
                    del self.FromZones_by_zone[zone]

                if (self.conf_device[CONF_TRACK_FROM_ZONES] == []
                        or HOME not in self.conf_device[CONF_TRACK_FROM_ZONES]):
                    conf_file_updated_flag = True
                    self.track_from_base_zone = HOME
                    self.conf_device[CONF_TRACK_FROM_ZONES] = [HOME]

                # Cycle through the zones that are no longer tracked from for the device, then cycle
                # through the Device's sensor list and remove all track_from_zone sensors ending with
                # that zone.
                device_tfz_sensors = Gb.Sensors_by_devicename_from_zone.get(self.devicename, [])
                for sensor, Sensor in device_tfz_sensors.items():
                    if sensor.endswith(f"_{zone}") and Sensor.entity_removed_flag is False:
                        entity_io.remove_entity(Sensor.entity_id)

            # Update log_zone_activity zone
            if zone in self.log_zones:
                conf_file_updated_flag = True
                self.log_zones = list_del(self.log_zones, zone)
                self.conf_device[CONF_LOG_ZONES] = list_del(self.conf_device[CONF_LOG_ZONES], zone)
                if len(self.conf_device[CONF_LOG_ZONES]) <= 1:
                    self.conf_device[CONF_LOG_ZONES] = ['none']

            # Update track_from_base_home_zone, set back to Home
            if (self.track_from_base_zone == zone
                    or self.conf_device[CONF_TRACK_FROM_BASE_ZONE] not in Gb.Zones_by_zone):
                conf_file_updated_flag = True
                self.track_from_base_zone = HOME
                self.conf_device[CONF_TRACK_FROM_BASE_ZONE] = HOME

            if conf_file_updated_flag:
                config_file.write_icloud3_configuration_file()

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def _restore_sensors_from_restore_state_file(self, zone=None, FromZone=None):
        '''
        Restore the Device's sensor values and the Device's DeviceFmZone track from zone sensors
        from the restore_state configuration file
        '''
        try:
            if FromZone:
                FromZone.sensors.update(Gb.restore_state_devices[self.devicename]['from_zone'][zone])
            else:
                self.sensors.update(Gb.restore_state_devices[self.devicename]['sensors'])

        except:
            pass

#--------------------------------------------------------------------
    @property
    def fname_devicename(self):
        return (f"{self.fname} ({self.devicename})")

    @property
    def devicename_fname(self):
        return (f"{self.devicename} ({self.fname})")

    @property
    def devtype_fname(self):
        return DEVICE_TYPE_FNAME(self.device_type)

    @property
    def fname_devtype(self):
        if instr(self.fname, DEVICE_TYPE_FNAME(self.device_type)):
            return self.fname

        return (f"{self.fname} "
                f"({DEVICE_TYPE_FNAME(self.device_type)})")

    @property
    def conf_apple_acct_username_id(self):
        try:
            return username_id(self.conf_apple_acct_username)
        except:
            return ''

    @property
    def device_id8_icloud(self):
        if self.icloud_device_id:
            return f"#{self.icloud_device_id[:8]}"
        return 'None'

    @property
    def tracking_mode_fname(self, track_fname=False):
        if self.tracking_mode == TRACK_DEVICE and track_fname is False:
            return ''
        else:
            return f", {TRACKING_MODE_FNAME[self.tracking_mode]}"

    def is_statzone_name(self, zone_name):
        return zone_name in Gb.StatZones_by_zone

    def set_fname_alert(self, alert_char):
        return

    @property
    def AADevData_icloud(self):
        if self.AppleAcct:
            return self.AppleAcct.AADevData_by_device_id.get(self.icloud_device_id)

        return None

    def device_model(self):
        return f"{self.device_type}"

    @property
    def mobapp_device_trkr_entity_id_fname(self):
        return (f"{self.mobapp[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')}")

    @property
    def FromZone(self, Zone):
        return (f"{self.devicename}:{Zone.zone}")

    @property
    def state_change_flag(self):
        return (self.sensors[ZONE] != self.loc_data_zone)

    @property
    def sensor_zone(self):
        return self.sensors[ZONE]

    @property
    def loc_data_zone_fname(self):
        return zone_dname(self.loc_data_zone)

    @property
    def loc_data_time_gps(self):
        time_msg = self.loc_data_time
        if self.loc_data_gps_accuracy > Gb.gps_accuracy_threshold*.75:
            time_msg += (f"/±{self.loc_data_gps_accuracy:.0f}m")
        return time_msg

    @property
    def mobapp_data_time_gps(self):
        if secs_since(self.mobapp_data_secs) >= 10800:
            return f"{format_age_hrs(self.mobapp_data_secs)}"

        time_msg = time_to_12hrtime(self.mobapp_data_time)
        if self.mobapp_data_gps_accuracy > Gb.gps_accuracy_threshold*.75:
            time_msg += f"/±{self.mobapp_data_gps_accuracy:.0f}m"
        return time_msg

    @property
    def device_status(self):
        return f"{self.dev_data_device_status}/{self.dev_data_device_status_code}"

    @property
    def device_status_msg(self):
        return ( f"{DEVICE_STATUS_CODES.get(self.dev_data_device_status_code, 'Unknown')}/"
                f"{self.dev_data_device_status_code}")

    @property
    def loc_data_fgps(self):
        gps_msg = format_gps(self.loc_data_latitude, self.loc_data_longitude, self.loc_data_gps_accuracy)
        position_type = f" ({self.loc_data_position_type})" if self.loc_data_position_type else ''
        return f"{gps_msg}{position_type}"

    @property
    def mobapp_data_fgps(self):
        return format_gps(self.mobapp_data_latitude, self.mobapp_data_longitude, self.mobapp_data_gps_accuracy)

    @property
    def loc_data_gps(self):
        return (self.loc_data_latitude, self.loc_data_longitude)

    @property
    def mobapp_data_gps(self):
        return (self.mobapp_data_latitude, self.mobapp_data_longitude)

    @property
    def log_zones_filename(self):
        ''' Return the  Log zone activity filename zone/device part '''
        if 'name-zone' in self.log_zones:
            return f"{self.log_zone}"
        elif 'name-device' in self.log_zones:
            return f"{self.devicename}"
        elif 'name-device-zone' in self.log_zones:
            return f"{self.devicename}-{self.log_zone}"
        elif 'name-zone-device' in self.log_zones:
            return f"{self.log_zone}-{self.devicename}"
        else:
            return f"{self.log_zone}"

    @property
    def log_zones_filename_fname(self):
        ''' Return the  Log zone activity  display as filename zone/device part '''
        if 'name-zone' in self.log_zones:
            return f"[{self.log_zone}]"
        elif 'name-device' in self.log_zones:
            return f"[{self.devicename}]"
        elif 'name-device-zone' in self.log_zones:
            return f"[{self.devicename}]-[{self.log_zone}]"
        elif 'name-zone-device' in self.log_zones:
            return f"[{self.log_zone}]-[{self.devicename}]"
        else:
            return f"[{self.log_zone}]"

    #--------------------------------------------------------------------
    @property
    def format_battery_level(self):
        return f"{self.dev_data_battery_level}%"

    @property
    def format_battery_status(self):
        return self.dev_data_battery_status
        return f"{BATTERY_STATUS_FNAME.get(self.dev_data_battery_status, self.dev_data_battery_status.title())}"

    @property
    def format_battery_status_source(self):
        return (f"{self.format_battery_status} ({self.dev_data_battery_source})")

    @property
    def format_battery_level_status_source(self):
        return f"{self.format_battery_level}, {self.format_battery_status_source}"

    @property
    def format_battery_time(self):
        return secs_to_datetime(self.dev_data_battery_update_secs)

#--------------------------------------------------------------------
    @property
    def data_source_fname(self):
        return self.data_source

    # is_dev_data_source properties
    @property
    def is_dev_data_source_NOT_SET(self):
        return self.dev_data_source == NOT_SET

    @property
    def is_dev_data_source_SET(self):
        return self.dev_data_source != NOT_SET

    @property
    def is_dev_data_source_ICLOUD(self):
        return self.is_dev_data_source_ICLOUD

    @property
    def is_dev_data_source_MOBAPP(self):
        return self.dev_data_source in [MOBAPP]

    @property
    def no_location_data(self):
        return self.loc_data_latitude == 0.0 or self.loc_data_longitude == 0.0

    # is_xxx other properties
    @property
    def is_tracked(self):
        return self.tracking_mode == TRACK_DEVICE

    @property
    def is_monitored(self):
        return self.tracking_mode == MONITOR_DEVICE

    @property
    def is_inactive(self):
        return self.tracking_mode == INACTIVE_DEVICE

    @property
    def isnot_inactive(self):
        return (not self.is_inactive)

    @property
    def is_online(self):
        return not self.is_offline

    @property
    def is_offline(self):
        '''
        Returns True/False if the device is offline based on the device_status
        Return False if there is no GPS location so the old location will be processed,
            it was located in the last 5-mins or it is not a 201/offline code
        '''
        if (self.no_location_data
                or (self.dev_data_device_status_code == DEVICE_STATUS_OFFLINE
                    and mins_since(self.loc_data_secs) > 5)):
            return True
        return False

    @property
    def is_pending(self):
        ''' Returns True/False if the device is pending based on the device_status '''
        return (self.dev_data_device_status in DEVICE_STATUS_PENDING)

    @property
    def is_using_mobapp_data(self):
        ''' Return True/False if using MobApp data '''
        return self.dev_data_source == MOBAPP

    @property
    def track_from_other_zone_flag(self):
        ''' Returns True if tracking from multiple zones '''
        return (len(self.FromZones_by_zone) > 1)

    @property
    def located_secs_plus_5(self):
        ''' timestamp (secs) plus 5 secs for next cycle '''
        return (self.loc_data_secs)     # + 5)

    @property
    def is_approaching_tracked_zone(self):
        '''
        Determine if the Device is going towards a tracked zone, is within 1km of
        the zone, on a 15-sec inerval and the location is older than 15-secs.
        When this occurs, we want to refresh the location or set the old
        location threshold to 15-secs.
        '''
        if self.FromZone_TrackFrom:
            if (secs_to(self.next_update_secs) <= 15
                    and secs_since(self.loc_data_secs) > 15
                    and self.FromZone_TrackFrom.is_going_towards
                    and self.went_3km):
                return True
        return False

    @property
    def is_tracking_from_home(self):
        return self.FromZone_TrackFrom.from_zone == HOME

#--------------------------------------------------------------------
    def update_location_gps_accuracy_status(self):
        if self.no_location_data or self.is_offline:
            self.loc_data_isold     = True
            self.loc_data_ispoorgps = False
            self.icloud_devdata_useable_flag = False
        elif self.icloud_devdata_useable_flag or self.loc_data_secs == 0:
            self.loc_data_isold     = False
            self.loc_data_ispoorgps = False
        else:
            self.loc_data_isold     = (secs_since(self.loc_data_secs) > self.old_loc_threshold_secs + 5
                                            or self.is_offline)
            self.loc_data_ispoorgps = (self.loc_data_gps_accuracy > Gb.gps_accuracy_threshold)
            self.icloud_devdata_useable_flag = (self.loc_data_isold is False
                                                    and self.loc_data_ispoorgps is False)

    @property
    def is_mobapp_data_good(self):
        return not self.is_mobapp_data_old

    @property
    def is_mobapp_data_old(self):
        return secs_since(self.mobapp_data_secs) > self.old_loc_threshold_secs

    @property
    def is_location_old_or_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold or self.loc_data_ispoorgps)

    @property
    def is_location_old_and_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold and self.loc_data_ispoorgps)

    @property
    def is_location_gps_good(self):
        self.update_location_gps_accuracy_status()
        return (self.loc_data_isold is False and self.loc_data_ispoorgps is False)

    @property
    def is_location_old(self):
        self.update_location_gps_accuracy_status()
        return self.loc_data_isold

    @property
    def is_location_good(self):
        return not self.is_location_old

    @property
    def is_gps_poor(self):
        self.update_location_gps_accuracy_status()
        return self.loc_data_ispoorgps

    @property
    def is_gps_good(self):
        return not self.is_gps_poor

    @property
    def is_next_update_overdue(self):
        return (secs_since(self.next_update_secs) > 60)

#--------------------------------------------------------------------
    @property
    def is_still_at_last_location(self):
        return False
        #return (self.loc_data_latitude == self.sensors[LATITUDE]
        #            and self.loc_data_longitude == self.sensors[LONGITUDE])

    # @property
    # def sensor_secs(self):
    #     return (datetime_to_secs(self.sensors[LAST_UPDATE_DATETIME]))

    @property
    def loc_data_age(self):
        ''' timestamp(secs) --> age (secs ago)'''
        return (secs_since(self.loc_data_secs))

    @property
    def loc_data_time_age(self):
        ''' timestamp (secs) --> hh:mm:ss (secs ago)'''
        return self.loc_data_12hrtime_age

    @property
    def loc_data_time_utc(self):
        ''' timestamp (secs) --> hh:mm:ss'''
        return (secs_to_time(self.loc_data_secs))

    @property
    def loc_data_12hrtime_age(self):
        ''' location time --> 12:mm:ss (secs ago)'''
        return (f"{time_to_12hrtime(self.loc_data_time)} "
                f"({format_timer(self.loc_data_age)} ago)")

#--------------------------------------------------------------------
    @property
    def isnot_set(self):
        return (self.sensors[ZONE] == NOT_SET)

    @property
    def isin_zone(self):
        return (self.loc_data_zone not in NOT_HOME_ZONES)

    @property
    def isnotin_zone(self):
        return (self.loc_data_zone in NOT_HOME_ZONES)

    @property
    def isnotin_zone_or_statzone(self):
        return (self.loc_data_zone in NOT_HOME_ZONES and self.StatZone is None)

    @property
    def isin_zone_mobapp_state(self):
        return (self.mobapp_data_state not in NOT_HOME_ZONES)

    @property
    def isnotin_zone_mobapp_state(self):
        return (self.mobapp_data_state in NOT_HOME_ZONES)

    @property
    def is_tracking_from_another_zone(self):
        return (self.sensors[FROM_ZONE] and self.sensors[FROM_ZONE] not in [NOT_SET, HOME])

    @property
    def wasin_zone(self):
        return (self.sensors[ZONE] not in NOT_HOME_ZONES)

    @property
    def wasnotin_zone(self):
        return (self.sensors[ZONE] in NOT_HOME_ZONES)

    @property
    def is_statzone_trigger_reached(self):
        return self.icloud_update_reason.startswith('Stationary')

#--------------------------------------------------------------------
    @property
    def isin_nonstatzone(self):
        return (self.isin_zone and self.isnotin_statzone)

    @property
    def isin_statzone(self):
        return self.StatZone is not None

    @property
    def isnotin_statzone(self):
        return self.StatZone is None

    @property
    def wasin_statzone(self):
        return (is_statzone(self.sensors[ZONE]))

    @property
    def wasnotin_statzone(self):
        return (is_statzone(self.sensors[ZONE]) is False)

    @property
    def is_statzone_timer_reached(self):
        ''' Return True if the timer has expired, False if not expired or not using Stat Zone '''
        return (self.is_statzone_timer_set and Gb.this_update_secs >= self.statzone_timer)

    @property
    def is_statzone_move_limit_exceeded(self):
        return (self.statzone_dist_moved_km > Gb.statzone_dist_move_limit_km)

    @property
    def is_statzone_timer_set(self):
        return self.statzone_timer > 0

    @property
    def in_statzone_interval_secs(self):
        if self.FromZone_Home.calc_dist_km < 180 or self.mobapp_monitor_flag is False:
            return self.statzone_inzone_interval_secs
        return Gb.max_interval_secs / 2

    @property
    def statzone_timer_left(self):
        ''' Return the seconds left before the phone should be moved into a Stationary Zone '''
        if self.is_statzone_timer_set:
            return (self.statzone_timer - time_now_secs())
        else:
            return HIGH_INTEGER

    @property
    def statzone_reset_timer(self):
        ''' Set the Stationary Zone timer expiration time '''
        self.statzone_dist_moved_km = 0.0
        self.statzone_timer     = Gb.this_update_secs + Gb.statzone_still_time_secs
        self.statzone_latitude  = self.loc_data_latitude
        self.statzone_longitude = self.loc_data_longitude

    @property
    def statzone_clear_timer(self):
        ''' Clear the Stationary Zone timer '''
        self.statzone_reset_timer
        self.statzone_timer = 0

    def update_distance_moved(self, distance):
        self.statzone_dist_moved_km = self.distance_km(self.statzone_latitude, self.statzone_longitude)

        if Gb.evlog_trk_monitors_flag:
            log_msg =  (f"StatZone Movement > "
                        f"TotalMoved-{km_to_um(self.statzone_dist_moved_km)}")
            if self.is_statzone_timer_set:
                log_msg += (f", Timer-{secs_to_time(self.statzone_timer)}, "
                            f"UnderMoveLimit-"
                            f"{self.statzone_dist_moved_km <= Gb.statzone_dist_move_limit_km}, "
                            f"TimerLeft-{self.statzone_timer_left/60:1f} mins, "
                            f"TimerExpired-{self.is_statzone_timer_reached}")
            post_monitor_msg(self.devicename, log_msg)

        return self.statzone_dist_moved_km

#--------------------------------------------------------------------
    def pause_tracking(self):
        ''' Pause tracking the device '''
        try:
            self.tracking_status = TRACKING_PAUSED
            # self.xx = RED_STOP
            # Device.set_fname_alert('')

            msg = f'{RED_ALERT}OFFLINE' if Gb.internet_error else PAUSED

            self.write_ha_sensor_state(NEXT_UPDATE, msg)
            self.display_info_msg(msg)

        except Exception as err:
            log_exception(err)
            pass

#--------------------------------------------------------------------
    @property
    def is_tracking_paused(self):
        '''
        Return:
            True    Device is paused
            False   Device not pause
        '''
        return (self.tracking_status == TRACKING_PAUSED)

#--------------------------------------------------------------------
    def resume_tracking(self, interval_secs=0):
        ''' Resume tracking '''
        try:
            self.write_ha_sensor_state(NEXT_UPDATE, RESUMING)
            self.display_info_msg(RESUMING)

            self.tracking_status             = TRACKING_RESUMED
            Gb.all_tracking_paused_flag      = False
            Gb.any_device_was_updated_reason = ''

            Gb.iCloud3.initialize_5_sec_loop_control_flags()

            if Gb.use_data_source_ICLOUD is False or self.is_data_source_ICLOUD is False:
                self.write_ha_sensor_state(NEXT_UPDATE, '___')
                return

            self.reset_tracking_fields(interval_secs)

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def reset_tracking_fields(self, interval_secs=0, max_error_cnt_reached=False):
        '''
        Reset all tracking fields

        Parameters:
            interval_secs - Next Update interval value
        '''
        for FromZone in self.FromZones_by_zone.values():
            # FromZone.next_update_secs = interval_secs
            FromZone.next_update_secs = Gb.this_update_secs + interval_secs
            FromZone.next_update_time = HHMMSS_ZERO if interval_secs == 0 \
                                                    else secs_to_time(Gb.this_update_secs + interval_secs)

        self.FromZone_NextToUpdate        = self.FromZone_Home
        self.next_update_secs             = self.FromZone_Home.next_update_secs
        self.next_update_time             = self.FromZone_Home.next_update_time
        self.icloud_force_update_flag     = True

        self.old_loc_cnt                  = 0
        if max_error_cnt_reached is False:
            self.max_error_cycle_cnt      = 0
        self.old_loc_msg                  = ''
        self.poor_gps_flag                = False
        self.outside_no_exit_trigger_flag = False
        self.dev_data_device_status       = "Online"
        self.dev_data_device_status_code  = 200
        self.icloud_update_reason         = 'Trigger > Resume/Relocate'
        self.icloud_no_update_reason      = ''

        self.mobapp_request_loc_first_secs = 0
        self.mobapp_request_loc_last_secs  = 0
        self.passthru_zone_timer           = 0

#--------------------------------------------------------------------
    @property
    def is_tracking_resumed(self):
        '''
        Return
            True    Device is resuming tracking
            False   Device tracking is normal
        '''
        try:
            return (self.tracking_status == TRACKING_RESUMED)

        except Exception as err:
            log_exception(err)
            return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PASSTHRU (ENTER ZONE) DELAY FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @property
    def is_passthru_timer_set(self):
        return (self.passthru_zone_timer > 0)

    @property
    def is_passthru_zone_delay_active(self):
        '''
        See if the device has just entered a non-tracked zone. If it is and
        it's timer has expired, reset the timer

        Return:
            True - Device is still waiting to see if it is ina zone
            False - It is not or the timerhas expired
        '''
        # Not used, not Active
        if Gb.is_passthru_zone_used is False or self.is_passthru_timer_set is False:
            return False

        # Active and has not expired
        if Gb.this_update_secs < self.passthru_zone_timer:
            return True

        # Expired
        self.passthru_zone_timer = 0

        return False

#--------------------------------------------------------------------
    def set_passthru_zone_delay(self, data_source, zone_entered=None, zone_entered_secs=0):
        '''
        The Mobile App may have entered a non-tracked zone. If so, it might be just passing thru the zone and
        not staying in it. Check the passthru_zone_timer to see if the 1-min enter zone delay is still
        in effect or if has expired.

        Return:
            True - Set up passthru delay or it is already set up
            False - Zone was reset and should proceed with an update
        '''
        # Passthru zone is not used or already set up
        passthru_not_used_reason = ''
        if (zone_entered == self.passthru_zone
                or zone_entered == self.loc_data_zone):
            return True

        # Entering a zone not subject to a delay
        if zone_entered in self.FromZones_by_zone:
            passthru_not_used_reason = 'TrackedFrom Zone'
        elif is_statzone(zone_entered):
            passthru_not_used_reason = 'Stat Zone'
        elif zone_entered is None:
            passthru_not_used_reason = 'Unknown Zone'
        elif (data_source == ICLOUD and self.is_location_old_or_gps_poor):
            passthru_not_used_reason = 'Old Location'

        # Not set and next update not reached, set it below
        elif (self.is_passthru_timer_set is False
                and self.is_next_update_time_reached is False):
            pass

        # Time for an update, reset it
        elif self.is_next_update_time_reached:
            self.reset_passthru_zone_delay()
            passthru_not_used_reason = 'Next Update Time Reached'

        # Passthru expire is set, if before enter zone time or this update time, reset it
        elif (self.is_passthru_timer_set
                and (zone_entered_secs > self.passthru_zone_timer
                        or Gb.this_update_secs >= self.passthru_zone_timer)):
            self.reset_passthru_zone_delay()
            passthru_not_used_reason = 'Timer Expired'

        if passthru_not_used_reason:
            post_event(self.devicename,
                        f"Zone Enter Not Delayed > {passthru_not_used_reason}")
            return False

        # Activate Passthru zone
        det_interval.update_all_device_fm_zone_sensors_interval(self, Gb.passthru_zone_interval_secs)

        self.passthru_zone_timer = Gb.this_update_secs + Gb.passthru_zone_interval_secs
        self.passthru_zone = zone_entered

        post_event(self.devicename,
                    f"Enter Zone Delayed > {zone_dname(self.passthru_zone)}, "
                    f"DelayFor-{format_timer(Gb.passthru_zone_interval_secs)}")

        self.display_info_msg(
                    f"Enter Zone Delayed - {zone_dname(self.passthru_zone)}, "
                    f"Expires-{secs_to_time(self.passthru_zone_timer)} "
                    f"({format_timer(secs_to(self.passthru_zone_timer))})")

        return True

#--------------------------------------------------------------------
    def reset_passthru_zone_delay(self):

        if Gb.is_passthru_zone_used is False or self.is_passthru_timer_set is False:
            return

        # event_msg =(f"Enter Zone Delay Ended > {zone_dname(self.passthru_zone)}")
        # post_event(self.devicename, event_msg)

        self.passthru_zone_timer = 0
        self.passthru_zone = ''

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   NEXT UPDATE TIME AND DISTANCE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @property
    def is_next_update_time_reached(self):
        '''
        Check to see if any of this Device's DeviceFmZone items will
        need to be updated within the next 5-secs

        Return:
            True    Next update time reached
            False   Next update time not reached
        '''

        if self.FromZone_NextToUpdate is None:
            self.FromZone_LastIn       = self.FromZone_Home
            self.FromZone_BeingUpdated = self.FromZone_Home
            self.FromZone_NextToUpdate = self.FromZone_Home
            self.FromZone_TrackFrom    = self.FromZone_Home
            self.TrackFromBaseZone     = self.FromZone_Home
            self.last_track_from_zone  = self.FromZone_Home.from_zone

        if self.icloud_initial_locate_done is False:    # or self.is_tracking_resumed:
            return True

        return Gb.this_update_secs >= self.FromZone_NextToUpdate.next_update_secs

#
#--------------------------------------------------------------------
    def _set_next_FromZone_to_update(self):
        '''
        Cycle thru the DeviceFmZones and get the lowest (next) updated secs

        Return:
            next_update_secs for the DeviceFmZone that will be updaed next
        Sets:
            FromZone_NextToUpdate to the object
        '''
        if self.only_track_from_home:
            return self.next_update_secs

        self.next_update_secs = HIGH_INTEGER
        self.FromZone_NextToUpdate = None
        for FromZone in self.FromZones_by_zone.values():
            if FromZone.next_update_secs <= self.next_update_secs:
                self.next_update_secs = FromZone.next_update_secs
                self.FromZone_NextToUpdate = FromZone

        if self.FromZone_NextToUpdate is None:
            self.FromZone_NextToUpdate = self.FromZone_Home
            self.next_update_secs = self.FromZone_Home.next_update_secs

        return self.next_update_secs

#--------------------------------------------------------------------
    def calculate_distance_moved(self):
        '''
        Calculate the distance (km) from the last updated location to
        the current location
        '''
        if self.sensor_zone == NOT_SET:
            self.loc_data_dist_moved_km < 0.0001
        else:
            self.loc_data_dist_moved_km = gps_distance_km(self.sensors[GPS], self.loc_data_gps)
        self.loc_data_time_moved_from = self.sensors[LAST_LOCATED_DATETIME]
        self.loc_data_time_moved_to   = self.loc_data_datetime

#--------------------------------------------------------------------
    def distance_m(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = gps_distance_m(self.loc_data_gps, to_gps)
        distance = 0.0 if distance < .002 else distance
        return distance

    def distance_km(self, to_latitude, to_longitude):
        to_gps = (to_latitude, to_longitude)
        distance = gps_distance_km(self.loc_data_gps, to_gps)
        distance = 0.0 if distance < .00002 else distance
        return distance

    def Distance_m(self, Device_or_Zone):
        return self.distance_m(Device_or_Zone.latitude, Device_or_Zone.longitude)

    def Distance_km(self, Device_or_Zone):
        return self.distance_km(Device_or_Zone.latitude, Device_or_Zone.longitude)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE DEVICE_TRACKER AND SENSORS FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def write_ha_device_tracker_state(self):
        ''' Update the device_tracker entity for this device '''

        if self.DeviceTracker:
            self.DeviceTracker.write_ha_device_tracker_state()

        self._update_restore_state_values()

#--------------------------------------------------------------------
    def write_ha_sensor_state(self, sensor_name, sensor_value):
        '''
        Display a value in a ic3 sensor field

        Input:
            sensor_name     Attribute field name (LOCATED_DATETIME)
            sensor_value    Value that should be displayed (self.loc_data_datetime)
        '''
        if instr(sensor_name, BATTERY) and self.sensors[BATTERY] < 1:
            return

        self.sensors[sensor_name] = sensor_value

        self.write_ha_sensors_state([sensor_name])

#--------------------------------------------------------------------
    def write_ha_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        try:
            if sensors:
                update_sensors_list = {k:v  for sensor in sensors
                                            for k, v in self.Sensors.items()
                                            if k == sensor}
            else:
                update_sensors_list = self.Sensors.copy()

            update_sensors_list = self._update_battery_sensors(update_sensors_list)

            for sensor, Sensor in update_sensors_list.items():
                Sensor.write_ha_sensor_state()

            self._update_restore_state_values()
        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def write_ha_device_from_zone_sensors_state(self, sensors=None):
        ''' Update the sensors for the Device that are in the sensor_list '''

        if sensors:
            update_sensors_list = {k:v  for sensor in sensors
                                        for k, v in self.Sensors_from_zone.items()
                                        if k.startswith(sensor)}
        else:
            update_sensors_list = self.Sensors_from_zone

        for sensor, Sensor in update_sensors_list.items():
            Sensor.write_ha_sensor_state()

        # rc9 Added update restore state
        self._update_restore_state_values()

#--------------------------------------------------------------------
    def _update_restore_state_values(self):
        """ Save the Device's updated sensors in the icloud3.restore_state file """

        if self.update_sensors_flag is False:
            return

        Gb.restore_state_devices[self.devicename] = {}
        Gb.restore_state_devices[self.devicename]['last_update'] = datetime_now()
        Gb.restore_state_devices[self.devicename]['sensors']     = copy.deepcopy(self.sensors)
        Gb.restore_state_devices[self.devicename]['mobapp']      = self._restore_state_save_mobapp_items()
        Gb.restore_state_devices[self.devicename]['other']       = self._restore_state_save_other_items()

        Gb.restore_state_devices[self.devicename]['from_zone'] = {}
        for from_zone, FromZone in self.FromZones_by_zone.items():
            Gb.restore_state_devices[self.devicename]['from_zone'][from_zone] = copy.deepcopy(FromZone.sensors)

        restore_state.write_icloud3_restore_state_file()

#--------------------------------------------------------------------
    def _restore_state_save_mobapp_items(self):
        '''
        Build dictionary of Mobile App items to be saved in restore_state file
        '''
        mobapp_items = {}
        mobapp_items['state']          = self.mobapp_data_state
        mobapp_items['latitude']       = self.mobapp_data_latitude
        mobapp_items['longitude']      = self.mobapp_data_longitude
        mobapp_items['source_type']    = self.mobapp_data_source_type
        mobapp_items['state_secs']     = self.mobapp_data_state_secs
        mobapp_items['state_time']     = self.mobapp_data_state_time
        mobapp_items['trigger_secs']   = self.mobapp_data_trigger_secs
        mobapp_items['trigger_time']   = self.mobapp_data_trigger_time
        mobapp_items['secs']           = self.mobapp_data_secs
        mobapp_items['time']           = self.mobapp_data_time
        mobapp_items['trigger']        = self.mobapp_data_trigger
        mobapp_items['battery_level']  = self.mobapp_data_battery_level
        mobapp_items['battery_status'] = self.mobapp_data_battery_status
        mobapp_items['battery_update_secs'] = self.mobapp_data_battery_update_secs
        return mobapp_items


#--------------------------------------------------------------------
    def _restore_state_reset_mobapp_items(self):

        try:
            mobapp_items = Gb.restore_state_devices[self.devicename]['mobapp']

            self.mobapp_data_state          = mobapp_items['state']
            self.mobapp_data_latitude       = mobapp_items['latitude']
            self.mobapp_data_longitude      = mobapp_items['longitude']
            self.mobapp_data_source_type    = mobapp_items['source_type']
            self.mobapp_data_state_secs     = mobapp_items['state_secs']
            self.mobapp_data_state_time     = mobapp_items['state_time']
            self.mobapp_data_trigger_secs   = mobapp_items['trigger_secs']
            self.mobapp_data_trigger_time   = mobapp_items['trigger_time']
            self.mobapp_data_secs           = mobapp_items['secs']
            self.mobapp_data_time           = mobapp_items['time']
            self.mobapp_data_trigger        = mobapp_items['trigger']
            self.mobapp_data_battery_level  = mobapp_items['battery_level']
            self.mobapp_data_battery_status = mobapp_items['battery_status']
            self.mobapp_data_battery_update_secs =  mobapp_items['battery_update_secs']

        except Exception as err:
            #log_exception(err)
            pass

#--------------------------------------------------------------------
    def _restore_state_save_other_items(self):
        '''
        Build dictionary of Otheritems to be saved in restore_state file
        '''
        other_items = {}
        other_items['zone_change_secs']     = self.zone_change_secs
        other_items['zone_change_datetime'] = self.zone_change_datetime

        return other_items

#--------------------------------------------------------------------
    def _restore_state_reset_other_items(self):

        try:
            other_items = Gb.restore_state_devices[self.devicename]['other']

            self.zone_change_secs     = other_items['zone_change_secs']
            self.zone_change_datetime = other_items['zone_change_datetime']

        except Exception as err:
            #log_exception(err)
            pass

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE SENSORS FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @property
    def badge_sensor_value(self):
        """ Determine the badge sensor state value """

        try:
            # Tracking Paused
            if self.is_tracking_paused:
                sensor_value = PAUSED_CAPS

            # Display zone name if in a zone
            elif self.isin_zone and self.isnotin_statzone:
                sensor_value = self.loc_data_zone_fname

            # Display the distance to Home
            elif self.FromZone_Home:
                sensor_value = (km_to_um(self.FromZone_Home.zone_dist_km))

            else:
                sensor_value = BLANK_SENSOR_FIELD

        except Exception as err:
            log_exception(err)
            sensor_value = BLANK_SENSOR_FIELD

        return sensor_value
#--------------------------------------------------------------------
    def _update_battery_sensors(self, update_sensors_list):

        if BATTERY not in update_sensors_list:
            return update_sensors_list

        if (self.dev_data_battery_level < 1
                or (self.dev_data_battery_level == self.sensors[BATTERY]
                    and self.format_battery_status == self.sensors[BATTERY_STATUS])
                    and Gb.start_icloud3_inprocess_flag is False):
            update_sensors_list.pop(BATTERY, None)
            update_sensors_list.pop(BATTERY_STATUS, None)
            update_sensors_list.pop(BATTERY_SOURCE, None)
            return update_sensors_list

        self._set_battery_sensor_values()

        # Battery info in in the Badge sensor. Make sure it is updated too
        # if BADGE not in update_sensors_list:
        #     list_add(update_sensors_list, BADGE)

        return update_sensors_list

    def _set_battery_sensor_values(self):
        self.sensors[BATTERY]          = self.dev_data_battery_level
        self.sensors[BATTERY_STATUS]   = self.format_battery_status
        self.sensors[BATTERY_SOURCE]   = self.dev_data_battery_source
        self.sensors[BATTERY_UPDATE_TIME] = self.format_battery_time
        self.sensors[BATTERY_ICLOUD]   = self.battery_info[ICLOUD]
        self.sensors[BATTERY_MOBAPP]   = self.battery_info[MOBAPP]
        if self.dev_data_battery_source == ICLOUD:
            self.sensors[BATTERY_LATEST] = f"(iCloud) {self.sensors[BATTERY_ICLOUD]}"
            self.sensors[BATTERY_ICLOUD] = f"(Latest) {self.sensors[BATTERY_ICLOUD]}"
        elif self.dev_data_battery_source == MOBAPP:
            self.sensors[BATTERY_LATEST] = f"(MobApp) {self.sensors[BATTERY_MOBAPP]}"
            self.sensors[BATTERY_MOBAPP] = f"(Latest) {self.sensors[BATTERY_MOBAPP]}"


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CALCULATE THE OLD LOCATION THRESHOLD FOR THE DEVICE
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def calculate_old_location_threshold(self):
        """
        The old_loc_threshold_secs is used to determine if the Device's location is too
        old to be used. If it is too old, the Device's location will be requested again
        using an interval calculated in the determine_interval_after_error routine. The
        old_loc_threshold_secs is recalculated each time the Device's location is
        updated.
        """
        try:
            # Device is approaching a TrackFmZone (distance less than 1-km, on a 15-secs
            # interval). Set threshold to 15-secs so the location will be updated
            # immediately. Only use small interval if already retries 4 times (rc9)
            if (self.is_approaching_tracked_zone
                    and self.old_loc_cnt <= 4):
                self.old_loc_threshold_secs = 30 + Gb.old_location_adjustment
                return

            # Get smallest interval of all zones being tracked from
            interval_secs = HIGH_INTEGER
            for from_zone, FromZone in self.FromZones_by_zone.items():
                if FromZone.interval_secs < interval_secs:
                    interval_secs = FromZone.interval_secs

            threshold_secs = 60
            if self.isin_zone:
                threshold_secs = interval_secs * .025        # 2.5% of interval_secs time
                if threshold_secs < 120: threshold_secs = 120

            elif self.FromZone_BeingUpdated.zone_dist_km > 5:
                threshold_secs = 180

            elif interval_secs < 90:
                threshold_secs = 60
            else:
                threshold_secs = interval_secs * .125

            if self.is_passthru_timer_set:
                threshold_secs = 15
            elif threshold_secs < 60:
                threshold_secs = 60
            elif threshold_secs > 600:
                threshold_secs = 600

            if (Gb.old_location_threshold > 0
                    and threshold_secs > Gb.old_location_threshold):
                threshold_secs = Gb.old_location_threshold

            self.old_loc_threshold_secs = threshold_secs + Gb.old_location_adjustment

        except Exception as err:
            log_exception(err)
            post_internal_error('Calc Old Threshold', traceback.format_exc)
            self.old_loc_threshold_secs = 120

#--------------------------------------------------------------------
    def is_location_data_rejected(self):
        '''
        Post an event message describing the location/gps status of the data being used
        '''
        if (self.is_location_gps_good
                or self.is_dev_data_source_NOT_SET
                or self.loc_data_secs > self.last_update_loc_secs
                or self.is_offline is False):
            return False

        try:
            interval, error_cnt, max_error_cnt = det_interval.get_error_retry_interval(self)
            det_interval.update_all_device_fm_zone_sensors_interval(self, interval)

            if self.old_loc_cnt < 2:
                return False

            reason_msg = ''

            if self.is_tracked:
                if self.loc_data_isold:
                    reason_msg = (f"Old>{format_timer(self.old_loc_threshold_secs)}")
                elif self.loc_data_ispoorgps:
                    reason_msg = (f"PoorGPS>{Gb.gps_accuracy_threshold}m")

            post_event(self.devicename,
                        f"Rejected #{self.old_loc_cnt} > "
                        f"{self.dev_data_source}-{self.loc_data_time_gps}, "
                        f"{format_age(self.loc_data_secs)}, "
                        f"{reason_msg}, "
                        f"NextUpdate-{secs_to_time(self.next_update_secs)} "
                        f"({format_timer(interval)}), "
                        f"LastUpdate-{format_age(self.last_update_loc_secs)}")

        except Exception as err:
            log_exception(err)

        return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE DISTANCE TO OTHER DEVICES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    # Used in sensor._format_devices_distance_extra_attrs to build device dust sttrs
    def other_device_distance(self, other_devicename):
        return self.dist_to_other_devices[other_devicename][0]

    def update_distance_to_other_devices(self):
        '''
        Cycle through all devices and update this device's and the other device's
        dist_to_other_device_info field

        This is run when the self device's location is updated.

        {devicename: [distance_m, gps_accuracy_factor, loc_time (newer), display_text]}
        '''
        update_at_time = secs_to_hhmm(self.loc_data_secs)
        self.dist_to_other_devices_secs = self.loc_data_secs

        for _devicename, _Device in Gb.Devices_by_devicename.items():
            if _Device is self:
                continue

            dist_apart_m     = _Device.distance_m(self.loc_data_latitude, self.loc_data_longitude)
            min_gps_accuracy = (min(self.loc_data_gps_accuracy, _Device.loc_data_gps_accuracy))
            gps_msg          = f"±{min_gps_accuracy}" if min_gps_accuracy > Gb.gps_accuracy_threshold else ''
            loc_data_time    = secs_to_hhmm(_Device.loc_data_secs)
            time_msg         = f" ({loc_data_time})"
            display_text     = f"{m_to_um(dist_apart_m)}{gps_msg}{time_msg}"
            dist_apart_data = [dist_apart_m, min_gps_accuracy, _Device.loc_data_secs, display_text]

            time_msg2        = f" (^SECS={_Device.loc_data_secs}^)"
            display_text2    = f"{m_to_um(dist_apart_m)}{gps_msg}{time_msg2}"
            dist_apart_data2 = [dist_apart_m, min_gps_accuracy, _Device.loc_data_secs, display_text2]

            # if (_devicename not in self.dist_to_other_devices
            #         or self.devicename not in _Device.dist_to_other_devices
            #         or _Device.dist_to_other_devices[self.devicename] != dist_apart_data
            #         or self.dist_to_other_devices[_devicename] != dist_apart_data):
            try:
                self.dist_to_other_devices[_devicename] = dist_apart_data
                _Device.dist_to_other_devices[self.devicename] = dist_apart_data

                self.dist_to_other_devices2[_devicename] = \
                _Device.dist_to_other_devices2[self.devicename] = dist_apart_data2

                Gb.dist_to_other_devices_update_sensor_list.add(self.devicename)
                Gb.dist_to_other_devices_update_sensor_list.add(_devicename)

            except Exception as err:
                log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE BATTERY INFORMATION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_battery_data_from_mobapp(self):
        '''
        Update the battery info from the Mobile App if the Mobile App data is newer than the iCloud
        battery info. Then update the sensors if it has changed.

        sensor.gary_iphone_app_battery_level entity_attrs={'unit_of_measurement': '%', 'device_class':
            'battery', 'icon': 'mdi:battery-charging-80', 'friendly_name': 'Gary-iPhone-app Battery Level',
            'state': '82', 'last_changed_secs': 1680080444, 'last_changed_time': '5:00:44a'},
        sensor.gary_iphone_app_battery_state entity_attrs={'Low Power Mode': False,
            'icon': 'mdi:battery-charging-80', 'friendly_name': 'Gary-iPhone-app Battery State',
            'state': 'charging', 'last_changed_secs': 1680080444, 'last_changed_time': '5:00:44a'}

        Return:
            True - Data has changed
            False - Data has not changed
        '''
        if (self.mobapp_monitor_flag is False
                or Gb.conf_data_source_MOBAPP is False
                or self.mobapp.get(BATTERY_LEVEL) is None
                or self.is_dev_data_source_NOT_SET
                or Gb.start_icloud3_inprocess_flag):
            return False

        try:
            battery_level_attrs = entity_io.get_attributes(self.mobapp[BATTERY_LEVEL])
            battery_level = int(battery_level_attrs[STATE])
            battery_update_secs = \
                max(battery_level_attrs[LAST_UPDATED_SECS],
                    battery_level_attrs[LAST_CHANGED_SECS])

        except Exception as err:
            #log_exception(err)
            return False

        if Gb.this_update_time.endswith('00:00'):
                # or battery_update_secs != self.mobapp_data_battery_update_secs):
            log_data(f"MobApp Battery Level - <{self.devicename}> {s2t(battery_update_secs)=} {s2t(self.mobapp_data_battery_update_secs)=} {format_age(battery_update_secs - self.mobapp_data_battery_update_secs)}", battery_level_attrs)

        if battery_level > 99:
            battery_status = 'Charged'
        elif instr(battery_level_attrs['icon'], 'charging'):
            battery_status = 'Charging'
        elif battery_level > 0 and battery_level < BATTERY_LEVEL_LOW:
            battery_status = 'Low'
        else:
            battery_status = 'NotCharging'

        if (battery_level == self.mobapp_data_battery_level
                and battery_status == self.mobapp_data_battery_status):
            return False

        self.mobapp_data_battery_update_secs = battery_update_secs
        self.mobapp_data_battery_level  = battery_level
        self.mobapp_data_battery_status = battery_status

        self._update_battery_data_and_sensors(
                MOBAPP, battery_update_secs, battery_level, battery_status)

        # self.write_ha_sensors_state([BATTERY, BATTERY_STATUS])
        return True

#-------------------------------------------------------------------
    def _update_battery_data_and_sensors(self, data_source, battery_update_secs,
                                                battery_level, battery_status):
        '''
        Update the dev_data_battery and mobapp_battery fields with the battery data if this
        data is newer
        '''

        if battery_level < 1 or battery_status == '':
            return

        self.battery_info[data_source] = f"{battery_level}@{secs_to_time(battery_update_secs)}, {battery_status}"

        if battery_update_secs > self.dev_data_battery_update_secs:
            self.dev_data_battery_update_secs = battery_update_secs
            self.dev_data_battery_source = data_source
            self.dev_data_battery_level  = battery_level
            self.dev_data_battery_status = battery_status

            self.write_ha_sensors_state([BATTERY, BATTERY_STATUS, BADGE])

#-------------------------------------------------------------------
    def display_battery_info_msg(self, force_display=False):
        '''
        Display the Battery info msg if the status (Charging, Not Charging) has changed or the
        battery level is divisible by 5 (80, 85, etc.)
        '''

        if self.dev_data_battery_level < 1:
            return False

        last_battery_level, last_battery_status = self.last_battery_msg.split('%, ')

        if last_battery_status != self.format_battery_status or force_display:
            pass
        elif (last_battery_level == self.dev_data_battery_level
                or secs_since(self.last_battery_msg_secs) < 5
                or (self.dev_data_battery_level % 5) != 0):
            return False

        battery_msg = f"{self.dev_data_battery_level}%, {self.format_battery_status}"
        if battery_msg == self.last_battery_msg and force_display is False:
            return False

        self.last_battery_msg = battery_msg
        self.last_battery_msg_secs = time_now_secs()

        post_event(self.devicename,
                    f"Battery Info > Level-{battery_msg} ({self.dev_data_battery_source})")

        if Gb.EvLog.evlog_attrs["devicename"] == self.devicename:
            Gb.EvLog.update_event_log_display(self.devicename)

        return True


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Update the Device data from the Mobile App raw data or from the AADevData
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_dev_loc_data_from_raw_data_MOBAPP(self, AADevData=None):
        if (self.loc_data_secs >= self.mobapp_data_secs
                or self.mobapp_data_secs == 0):
            return

        self.last_data_update_secs = time_now_secs()

        self.dev_data_source            = MOBAPP
        self.dev_data_fname             = self.fname
        self.dev_data_device_class      = self.device_type
        self.dev_data_device_status     = "Online"
        self.dev_data_device_status_code = 200

        self._update_battery_data_and_sensors(
                MOBAPP, self.mobapp_data_battery_update_secs,
                self.mobapp_data_battery_level, self.mobapp_data_battery_status)

        self.loc_data_latitude          = self.mobapp_data_latitude
        self.loc_data_longitude         = self.mobapp_data_longitude
        self.loc_data_position_type     = self.mobapp_data_source_type
        self.loc_data_gps_accuracy      = self.mobapp_data_gps_accuracy
        self.loc_data_vertical_accuracy = self.mobapp_data_vertical_accuracy
        self.loc_data_altitude          = self.mobapp_data_altitude
        self.loc_data_secs              = self.mobapp_data_secs
        self.loc_data_time              = secs_to_time(self.mobapp_data_secs)
        self.loc_data_datetime          = secs_to_datetime(self.mobapp_data_secs)

        # rc3 Check old location when data is set
        if self.is_location_gps_good: self.old_loc_cnt = 0
        self.calculate_distance_moved()
        self.update_distance_to_other_devices()
        #self.write_ha_sensor_state(LAST_LOCATED, self.loc_data_time)
        self.write_ha_sensors_state([LAST_LOCATED, NEXT_UPDATE, LAST_UPDATE])
        self.display_update_location_msg()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_dev_loc_data_from_raw_data_ICLOUD(self, AADevData, requesting_device_flag=True):
        '''
        Update the Device's location data with the AADevData (iCloud) from the iCloud Account.

        Parameters:
            AADevData - iCloud object to be used to update this Device
            requesting_device_flag - Multiple devices can be updated since all device info is returned
                    from iCloud on a location request.
                        True-   This is the Device that requested the update and the Update Location
                                info should be displayed in the Event Log
                        False - This is another device and do not display the Update Location msg
        '''

        if (AADevData is None
                or AADevData.device_data is None
                or LOCATION not in AADevData.device_data
                or AADevData.device_data[LOCATION] is None
                or (AADevData.location_secs <= self.loc_data_secs and self.loc_data_secs > 0)):
            return

        self.last_data_update_secs = time_now_secs()

        location                       = AADevData.device_data[LOCATION]
        location_secs                  = AADevData.location_secs
        AADevData.last_used_location_secs = AADevData.location_secs
        AADevData.last_used_location_time = AADevData.location_time

        self.dev_data_source           = AADevData.data_source
        self.dev_data_fname            = AADevData.device_data.get(NAME, "")
        self.dev_data_device_class     = AADevData.device_data.get(ICLOUD_DEVICE_CLASS, "")
        self.dev_data_low_power_mode   = AADevData.device_data.get(ICLOUD_LOW_POWER_MODE, "")

        if AADevData.device_data.get(ICLOUD_BATTERY_LEVEL):
            aadevdata_battery_level  = AADevData.battery_level
            aadevdata_battery_status = AADevData.battery_status
        else:
            aadevdata_battery_level  = 0
            aadevdata_battery_status = UNKNOWN

        if AADevData.is_data_source_ICLOUD:
            self._update_battery_data_and_sensors(
                    ICLOUD, location_secs,
                    aadevdata_battery_level, aadevdata_battery_status)

        self.dev_data_device_status_code = AADevData.device_data.get(ICLOUD_DEVICE_STATUS, 0)
        self.dev_data_device_status      = DEVICE_STATUS_CODES.get(self.dev_data_device_status_code, UNKNOWN)

        self.loc_data_latitude       = location.get(LATITUDE, 0)
        self.loc_data_longitude      = location.get(LONGITUDE, 0)
        self.loc_data_position_type  = location.get(ICLOUD_POSITION_TYPE, '')
        self.loc_data_gps_accuracy   = round(location.get(ICLOUD_HORIZONTAL_ACCURACY, 0))
        self.loc_data_secs           = location_secs
        self.loc_data_time           = secs_to_time(location_secs)
        self.loc_data_datetime       = secs_to_datetime(location_secs)
        self.loc_data_altitude       = float(f"{location.get(ALTITUDE, 0):.1f}")
        self.loc_data_vert_accuracy  = round(location.get(ICLOUD_VERTICAL_ACCURACY, 0))
        self.loc_data_isold          = location.get('isOld', False)
        self.loc_data_ispoorgps      = location.get('isInaccurate', False)

        if self.loc_data_position_type == 'Wifi': self.loc_data_position_type = 'WiFi'
        if self.is_location_gps_good: self.old_loc_cnt = 0
        self.calculate_distance_moved()
        self.update_distance_to_other_devices()
        #self.write_ha_sensor_state(LAST_LOCATED, self.loc_data_time)
        self.write_ha_sensors_state([LAST_LOCATED, NEXT_UPDATE, LAST_UPDATE])
        if requesting_device_flag or self.is_monitored:
            self.display_update_location_msg()

#-------------------------------------------------------------------
    def display_update_location_msg(self):

        return
        if self.loc_data_time_gps == self.last_loc_data_time_gps:
            return

        if self.isnotin_zone or self.loc_data_dist_moved_km > .015:
            post_event(self.devicename,
                        f"Selected > "
                        f"{self.last_loc_data_time_gps}"
                        f"{RARROW}{self.dev_data_source}-{self.loc_data_time_gps}")

        #self.last_loc_data_time_gps = f"{self.dev_data_source}-{self.loc_data_time_gps} "

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def update_sensor_values_from_data_fields(self):
        #Note: Final prep and update device attributes via
        #device_tracker.see. The gps location, battery, and
        #gps accuracy are not part of the attrs variable and are
        #reformatted into device attributes by 'See'. The gps
        #location goes to 'See' as a "(latitude, longitude)" pair.
        #'See' converts them to LATITUDE and LONGITUDE
        #and discards the 'gps' item.

        # Determine the soonest DeviceFmZone to update, then get the sensor
        # values to be displayed with the Device sensors

        try:
            self._set_next_FromZone_to_update()
            det_interval.set_dist_to_devices(post_event_msg=False)
            det_interval.format_dist_to_devices_msg(self, time=True, age=False)

            # Initialize Batttery if not set up. Then Update in _update_battery_sensors
            if self.sensors[BATTERY] < 1 and self.dev_data_battery_level >= 1:
                self._set_battery_sensor_values()


            # Device related sensors
            self.sensors[DEVICE_STATUS]        = self.device_status
            self.sensors[LOW_POWER_MODE]       = self.dev_data_low_power_mode
            self.sensors[BADGE]                = self.badge_sensor_value
            self.sensors[INFO]                 = self.format_info_msg

            # Location related items
            self.sensors['last_gps']           = self.sensors[GPS]
            self.sensors[GPS]                  = (self.loc_data_latitude, self.loc_data_longitude)
            self.sensors[LATITUDE]             = self.loc_data_latitude
            self.sensors[LONGITUDE]            = self.loc_data_longitude
            self.sensors[GPS_ACCURACY]         = self.loc_data_gps_accuracy
            self.sensors[ALTITUDE]             = self.loc_data_altitude
            self.sensors[VERT_ACCURACY]        = self.loc_data_vert_accuracy
            self.sensors[LOCATION_SOURCE]      = self.dev_data_source
            self.sensors[NEAR_DEVICE_USED]     = self.near_device_used
            self.sensors[TRIGGER]              = self.trigger
            self.sensors[LAST_LOCATED_DATETIME]= self.loc_data_datetime
            self.sensors[LAST_LOCATED_TIME]    = self.loc_data_time
            self.sensors[LAST_LOCATED]         = self.loc_data_time
            self.sensors[LAST_LOCATED_SECS]    = self.loc_data_secs
            # self.sensors[DISTANCE_TO_DEVICES]  = self.dist_apart_msg.rstrip(', ')
            self.sensors[DISTANCE_TO_DEVICES]  = det_interval.format_dist_to_devices_msg(self, time=True, age=False)
            self.sensors[MOVED_DISTANCE]       = self.loc_data_dist_moved_km
            self.sensors[MOVED_TIME_FROM]      = self.loc_data_time_moved_from
            self.sensors[MOVED_TIME_TO]        = self.loc_data_time_moved_to
            self.sensors[ZONE_DATETIME]        = secs_to_datetime(self.zone_change_secs)

            if self.FromZone_NextToUpdate is None:
                self.FromZone_NextToUpdate = self.FromZone_Home
            self.interval_secs                 = self.FromZone_NextToUpdate.interval_secs
            self.interval_str                  = self.FromZone_NextToUpdate.interval_str
            self.next_update_secs              = self.FromZone_NextToUpdate.next_update_secs
            self.sensors[INTERVAL]             = self.FromZone_NextToUpdate.sensors[INTERVAL]
            self.sensors[NEXT_UPDATE_DATETIME] = self.FromZone_NextToUpdate.sensors[NEXT_UPDATE_DATETIME]
            self.sensors[NEXT_UPDATE_TIME]     = self.FromZone_NextToUpdate.sensors[NEXT_UPDATE_TIME]
            self.sensors[NEXT_UPDATE]          = self.FromZone_NextToUpdate.sensors[NEXT_UPDATE]

            if self.FromZone_TrackFrom is None: self.FromZone_TrackFrom = self.FromZone_Home
            self.sensors[FROM_ZONE]            = self.FromZone_TrackFrom.from_zone
            self.sensors[LAST_UPDATE_DATETIME] = self.FromZone_TrackFrom.sensors[LAST_UPDATE_DATETIME]
            self.sensors[LAST_UPDATE_TIME]     = self.FromZone_TrackFrom.sensors[LAST_UPDATE_TIME]
            self.sensors[LAST_UPDATE]          = self.FromZone_TrackFrom.sensors[LAST_UPDATE]
            self.sensors[TRAVEL_TIME]          = self.FromZone_TrackFrom.sensors[TRAVEL_TIME]
            self.sensors[TRAVEL_TIME_MIN]      = self.FromZone_TrackFrom.sensors[TRAVEL_TIME_MIN]
            self.sensors[TRAVEL_TIME_HHMM]     = self.FromZone_TrackFrom.sensors[TRAVEL_TIME_HHMM]
            self.sensors[ARRIVAL_TIME]         = self.FromZone_TrackFrom.sensors[ARRIVAL_TIME]
            self.sensors[ZONE_DISTANCE]        = self.FromZone_TrackFrom.sensors[ZONE_DISTANCE]
            self.sensors[ZONE_DISTANCE_M]      = self.FromZone_TrackFrom.sensors[ZONE_DISTANCE_M]
            self.sensors[ZONE_DISTANCE_M_EDGE] = self.FromZone_TrackFrom.sensors[ZONE_DISTANCE_M_EDGE]
            self.sensors[MAX_DISTANCE]         = self.FromZone_TrackFrom.sensors[MAX_DISTANCE]
            self.sensors[WENT_3KM]             = 'true' if self.went_3km else 'false'
            self.sensors[WAZE_DISTANCE]        = self.FromZone_TrackFrom.sensors[WAZE_DISTANCE]
            self.sensors[WAZE_METHOD]          = self.FromZone_TrackFrom.sensors[WAZE_METHOD]
            self.sensors[CALC_DISTANCE]        = self.FromZone_TrackFrom.sensors[CALC_DISTANCE]

            self.sensors[HOME_DISTANCE]        = self.FromZone_Home.sensors[ZONE_DISTANCE]
            self.FromZone_TrackFrom.dir_of_travel = dir_of_travel = \
                    self.FromZone_TrackFrom.sensors[DIR_OF_TRAVEL]

            self.sensors[DIR_OF_TRAVEL] = dir_of_travel

            # Update the last zone info if the device was in a zone and now not in a zone or went immediatelly from
            # one zone to another (it was in a zone and still is in a zone and the old zone is differenent than the new zone)
            if (self.wasnotin_statzone
                    and (self.wasin_zone and self.isnotin_zone)
                    or  (self.wasin_zone and self.isin_zone and self.sensors[ZONE] != self.loc_data_zone)):
                self.last_zone                   = self.sensors[ZONE]
                if self.last_zone in self.from_zone_names:
                    self.last_tracked_from_zone = self.last_zone
                self.sensors[LAST_ZONE]          = self.sensors[ZONE]
                self.sensors[LAST_ZONE_DNAME]    = self.sensors[ZONE_DNAME]
                self.sensors[LAST_ZONE_NAME]     = self.sensors[ZONE_NAME]
                self.sensors[LAST_ZONE_FNAME]    = self.sensors[ZONE_FNAME]
                self.sensors[LAST_ZONE_DATETIME] = secs_to_datetime(time_now_secs())

            if Zone := Gb.Zones_by_zone.get(self.loc_data_zone):
                self.sensors[ZONE] = self.loc_data_zone
            else:
                Zone = Gb.HomeZone
                self.sensors[ZONE] = self.loc_data_zone = HOME

            self.sensors[ZONE_DNAME] = Zone.dname
            self.sensors[ZONE_NAME]  = Zone.name
            self.sensors[ZONE_FNAME] = Zone.fname
            self.sensors[DEVICE_TRACKER_STATE] = self.format_device_tracker_state(Zone)

            self.last_update_loc_secs = self.loc_data_secs
            self.last_update_loc_time = self.loc_data_time
            self.last_update_gps_accuracy = self.loc_data_gps_accuracy

            self._set_sensors_special_icon()

        except Exception as err:
            post_internal_error('Set Attributes', traceback.format_exc)

#----------------------------------------------------------------------------
    def _set_sensors_special_icon(self):
        '''
        Determine if the sensor icon should be customized for the sensor's value. If so,
        set it.

        The values are:
            - zone sensosr: icons are home or for a generic zone
            - direction-of-travel sensor:  based on towards, away from or inzone
            - next_update sensor: icon when the time is for a track-from-zone
        '''

        self.sensors_icon = {}
        for sensor_name in SENSOR_LIST_ZONE_NAME:
            zone = self.sensors[sensor_name]
            if is_statzone(zone):
                self.sensors_icon[sensor_name] = SENSOR_ICONS[INZONE_STATZONE]
            if zone in [HOME, HOME_FNAME]:
                self.sensors_icon[sensor_name] = SENSOR_ICONS[INZONE_HOME]

        dir_of_travel = self.sensors[DIR_OF_TRAVEL]
        if dir_of_travel == TOWARDS:
            icon = TOWARDS_HOME if self.is_tracking_from_home else TOWARDS
            self.sensors_icon[DIR_OF_TRAVEL] = SENSOR_ICONS[icon]

        elif dir_of_travel == AWAY_FROM:
            icon = AWAY_FROM_HOME if self.is_tracking_from_home else AWAY_FROM
            self.sensors_icon[DIR_OF_TRAVEL] = SENSOR_ICONS[icon]

        #elif dir_of_travel.startswith('@') or dir_of_travel in [INZONE, STATIONARY_FNAME]:
        elif dir_of_travel in [INZONE, INZONE_STATZONE]:
            if self.loc_data_zone == HOME:
                self.sensors_icon[DIR_OF_TRAVEL] = self.sensors_icon[ARRIVAL_TIME]  = \
                    SENSOR_ICONS[INZONE_HOME]    #['arrival_time_in_home']

            elif self.isin_statzone:
                self.sensors_icon[DIR_OF_TRAVEL] = SENSOR_ICONS[INZONE_STATZONE]

            else:
                self.sensors_icon[DIR_OF_TRAVEL] = SENSOR_ICONS[INZONE]

        # Tracking from a non-home zone, get the icon from the first letter of the tfz
        if is_statzone(self.loc_data_zone):
            pass

        elif self.is_tracking_from_another_zone:
            self.sensors_icon[NEXT_UPDATE] = icon_box(self.sensors[FROM_ZONE])

            self.sensors_icon[ZONE_DISTANCE] = self.sensors_icon[HOME_DISTANCE] = \
                    SENSOR_ICONS[TOWARDS]

            icon = INZONE
            if self.isin_zone:# else TOWARDS
                self.sensors_icon[ARRIVAL_TIME] = SENSOR_ICONS[icon]
            else:
                self.sensors_icon[ARRIVAL_TIME] = icon_box(self.sensors[FROM_ZONE])



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   INFO MESSAGES AND OTHER SUPPORT FUNCTIONSS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def format_device_tracker_state(self, Zone):
        '''
        Set Device's device_tracker_state_value
        '''
        if is_statzone(self.loc_data_zone):
            if Gb.device_tracker_state_source == 'ic3_fname': return Zone.fname
            if Gb.display_zone_format == 'fname': return Zone.fname
            if Gb.display_zone_format == 'ic3_evlog': return  Zone.dname
            if Gb.display_zone_format == 'zone': return 'stationary'
            return Zone.dname

        elif Gb.device_tracker_state_source == 'ha_gps':
            return None

        else:
            if self.loc_data_zone in STATE_TO_ZONE_BASE: return STATE_TO_ZONE_BASE[self.loc_data_zone]
            if Gb.device_tracker_state_source == 'ic3_evlog': return Zone.dname
            return Zone.fname

        return None

#----------------------------------------------------------------------------
    @property
    def format_info_msg(self):
        """
        Analyze the Device's fields.

        Return: Info text to be displayed in the info field
        """
        try:
            if self.is_passthru_zone_delay_active:
                info_msg = (f"Enter Zone Delayed - {zone_dname(self.passthru_zone)}, "
                    f"Expires-{secs_to_time(self.passthru_zone_timer)} "
                    f"({format_timer(secs_to(self.passthru_zone_timer))})")
                return info_msg

            if Gb.info_notification != '':
                Gb.info_notification = ''
                return f"** {Gb.info_notification} **"

            info_msg = ''
            if self.offline_secs > 0:
                info_msg +=(f"{RED_X}Offline@{format_time_age(self.offline_secs)} "
                            f"({self.device_status}), ")

            if (self.is_statzone_timer_set
                    and secs_to(self.statzone_timer) < 90
                    and self.sensors[MOVED_DISTANCE] < 0.00001):
                info_msg += (f"IntoStatZone-{secs_to_time(self.statzone_timer)}, ")

            elif self.zone_change_secs > 0:
                if self.isin_zone:
                    info_msg +=f"At {zone_dname(self.loc_data_zone)}-"
                    if self.sensors[ARRIVAL_TIME].startswith('@'):
                        info_msg += f"(Since-{self.sensors[ARRIVAL_TIME][1:]}), "
                    elif self.sensors[ARRIVAL_TIME].startswith('~'):
                        info_msg += f"(About-{self.sensors[ARRIVAL_TIME][1:]}), "
                    else:
                        info_msg += f"(Before-{secs_to_hhmm(Gb.started_secs)}), "

                elif self.mobapp_zone_exit_zone != '':
                    info_msg +=(f"Left-{zone_dname(self.mobapp_zone_exit_zone)}-"
                                f"{format_time_age(self.mobapp_zone_exit_secs)}, ")

            if self.is_tracking_from_another_zone:
                from_zone = self.sensors[FROM_ZONE]
                Zone = Gb.Zones_by_zone[from_zone]
                info_msg += f"FromZone-{Zone.dname}, "

            # if self.FromZone_NextToUpdate is not self.FromZone_Home:
            #     info_msg += f"NextUpdateFor-{self.FromZone_NextToUpdate.from_zone_dname[:8]}, "

            if self.NearDeviceUsed:
                info_msg +=(f"UsedNearbyDevice-{self.NearDeviceUsed.fname}, "
                            f"({m_to_um_ft(self.near_device_distance, as_integer=True)}, ")

            # if self.data_source != self.dev_data_source.lower():
            #info_msg += f"LocationData-{self.dev_data_source}, "

            # if self.dev_data_battery_level > 0:
            #     info_msg += f"Battery-{self.format_battery_level}, "

            if (self.mobapp_monitor_flag
                    and secs_since(self.mobapp_data_secs) > 3600):
                info_msg += (f"MobApp LastUpdate-{format_age(self.mobapp_data_secs)}, ")

            if self.mobapp_request_loc_last_secs > 0:
                info_msg +=  f"MobApp LocRequest-{format_age(self.mobapp_request_loc_last_secs)}, "

            if self.is_gps_poor:
                info_msg += (f"PoorGPS-±{self.loc_data_gps_accuracy}m #{self.old_loc_cnt}, ")
                if is_zone(self.loc_data_zone) and Gb.discard_poor_gps_inzone_flag:
                    info_msg = f"{info_msg[:-2]} (Ignored), "

            if self.old_loc_cnt > 3:
                info_msg += f"LocationOld-{format_age(self.loc_data_secs)} (#{self.old_loc_cnt}), "

            if self.old_loc_cnt > 20:
                info_msg += f"May Be Offline, "

        except Exception as err:
            log_exception(err)

        if info_msg.endswith(', '): info_msg = info_msg[:-2]
        if info_msg.endswith(','): info_msg = info_msg[:-1]
        self.info_msg = info_msg if info_msg else \
                                f'iCloud3 v{Gb.version}, Running for {format_secs_since(Gb.started_secs)}'

        return self.info_msg

#-------------------------------------------------------------------
    def display_info_msg(self, info_msg=None, new_base_msg=False):
        '''
        Display the info msg in the Device's sensor.[devicename]_info entity.

        Parameters:
            info_msg    - message to display
            append_msg  - True = Append the info_msg to the existing info_msg
                        - False = Only display the info_msg
        Return:
            Message text
        '''
        Gb.broadcast_info_msg = None

        if info_msg is None:
            info_msg = self.format_info_msg

        # PassThru zone msg has priority over all other messages
        if self.is_passthru_zone_delay_active and instr(info_msg, 'PassThru') is False:
            return

        try:
            self.write_ha_sensor_state(INFO, info_msg)
        except:
            pass

        return info_msg


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def log_data_fields(self):

        if self.NearDevice:
            near_devicename = self.NearDevice.devicename
        else:
            near_devicename = 'None'

        log_msg = ( f"Device Status > {self.devicename} > "
                    f"NearbyDevice-{near_devicename}, "
                    f"MobAppZone-{self.mobapp_data_state}, "
                    f"iC3Zone-{self.loc_data_zone}, ")
        if self.FromZone_Home:
            log_msg += (f"Interval-{self.sensors[INTERVAL]}, "
                        f"TravTime-{self.sensors[TRAVEL_TIME]}, "
                        f"Dist-{self.sensors[HOME_DISTANCE]} {Gb.um}, "
                        f"NextUpdt-{self.sensors[NEXT_UPDATE]}, "
                        f"Dir-{self.sensors[DIR_OF_TRAVEL]}, ")
        log_msg += (f"Moved-{self.sensors[MOVED_DISTANCE]}, "
                    f"LastUpdate-{self.sensors[LAST_UPDATE_TIME]}, "
                    f"IntoStatZone@{secs_to_time(self.statzone_timer)}, "
                    f"GPS-{self.loc_data_fgps}, "
                    f"LocAge-{format_age(self.loc_data_secs)}, "
                    f"OldThreshold-{format_timer(self.old_loc_threshold_secs)}, "
                    f"LastEvLogMsg-{secs_to_time(self.last_evlog_msg_secs)}, "
                    f"Battery-{self.format_battery_level_status_source}@"
                    f"{self.format_battery_time}")

        log_debug_msg(log_msg)
