#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles all tracking activities for a device. It contains
#   the following modules:
#       TrackFromZones - iCloud3 creates an object for each device/zone
#           with the tracking data fields.
#
#   The primary methods are:
#       determine_interval - Determines the polling interval, update times,
#           location data, etc for the device based on the distance from
#           the zone.
#       determine_interval_after_error - Determines the interval when the
#           location data is to be discarded due to poor GPS, it is old or
#           some other error occurs.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .global_variables  import GlobalVariables as Gb
from .const             import (HOME, NOT_SET,
                                DATETIME_ZERO, HHMMSS_ZERO, HHMM_ZERO,
                                TOWARDS, AWAY_FROM,
                                INZONE, INZONE_HOME, INZONE_STATZONE, INZONE_CODES,
                                INTERVAL, DISTANCE,
                                ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD,
                                FROM_ZONE, ZONE_INFO,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM,
                                ARRIVAL_TIME, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                LAST_LOCATED, LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
                                LAST_UPDATE, LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
                                NEXT_UPDATE, NEXT_UPDATE_TIME, NEXT_UPDATE_DATETIME,
                                )
from .helpers.dist_util import (gps_distance_km, km_to_um,)
from .helpers.messaging import (log_exception, post_internal_error, _evlog, _log, )

import homeassistant.util.dt as dt_util
import traceback
import copy


#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class iCloud3_DeviceFmZone():

    def __init__(self, Device, from_zone):
        try:
            self.Device               = Device
            self.devicename           = Device.devicename
            self.FromZone             = Gb.Zones_by_zone[from_zone]
            self.from_zone            = from_zone
            self.devicename_zone      = (f"{self.devicename}:{from_zone}")
            self.from_zone_dname      = self.FromZone.dname
            self.from_zone_radius_m   = self.FromZone.radius_m

            self.initialize()
            self.initialize_sensors()

        except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
    def initialize(self):
        try:
            self.interval_secs           = 0
            self.interval_str            = '0'
            self.interval_method         = ''
            self.last_travel_time        = ''
            self.last_distance_str       = ''
            self.last_distance_km        = 0
            self.dir_of_travel           = NOT_SET
            self.dir_of_travel_awayfrom_override = False
            self.dir_of_travel_history   = ''
            self.last_update_time        = HHMMSS_ZERO
            self.last_update_secs        = 0
            self.next_update_time        = HHMMSS_ZERO
            self.next_update_secs        = 0
            self.next_update_devicenames = ''
            self.waze_time               = 0
            self.waze_dist_km            = 0
            self.calc_dist_km            = 0
            self.zone_dist_km            = 0
            self.zone_dist_m             = 0
            self.zone_center_dist        = 0
            self.waze_results            = None
            self.home_dist_km            = gps_distance_km(Gb.HomeZone.gps, self.FromZone.gps)
            self.max_dist_km             = 0

            self.sensor_prefix       = (f"sensor.{self.devicename}_") \
                                            if self.from_zone== HOME \
                                            else (f"sensor.{self.devicename}_{self.from_zone}_")
            self.sensor_prefix_zone  = '' if self.from_zone== HOME else (f"{self.from_zone}_")
            self.info_status_msg     = (f"From-({self.from_zone})")

        except:
            post_internal_error(traceback.format_exc)

#--------------------------------------------------------------------
    def initialize_sensors(self):
        self.sensors_um = {}
        self.sensors    = {}

        self.sensors[FROM_ZONE]            = self.from_zone
        self.sensors[INTERVAL]             = 0
        self.sensors[LAST_LOCATED_DATETIME] = DATETIME_ZERO
        self.sensors[LAST_LOCATED_TIME]     = HHMMSS_ZERO
        self.sensors[LAST_LOCATED]          = HHMMSS_ZERO
        self.sensors[NEXT_UPDATE_DATETIME] = DATETIME_ZERO
        self.sensors[NEXT_UPDATE_TIME]     = HHMMSS_ZERO
        self.sensors[NEXT_UPDATE]          = HHMMSS_ZERO
        self.sensors[LAST_UPDATE_DATETIME] = DATETIME_ZERO
        self.sensors[LAST_UPDATE_TIME]     = HHMMSS_ZERO
        self.sensors[LAST_UPDATE]          = HHMMSS_ZERO
        self.sensors[TRAVEL_TIME]          = 0
        self.sensors[TRAVEL_TIME_MIN]      = 0
        self.sensors[TRAVEL_TIME_HHMM]     = HHMM_ZERO
        self.sensors[ARRIVAL_TIME]         = HHMMSS_ZERO
        self.sensors[DISTANCE]             = 0
        self.sensors[MAX_DISTANCE]         = 0
        self.sensors[ZONE_DISTANCE]        = 0
        self.sensors[ZONE_DISTANCE_M]      = 0
        self.sensors[ZONE_DISTANCE_M_EDGE] = 0
        self.sensors[WAZE_DISTANCE]        = 0
        self.sensors[WAZE_METHOD]          = ''
        self.sensors[CALC_DISTANCE]        = 0
        self.sensors[DIR_OF_TRAVEL]        = NOT_SET
        self.sensors[MOVED_DISTANCE]       = 0
        self.sensors[ZONE_INFO]            = ''

        Sensors_from_zone      = Gb.Sensors_by_devicename_from_zone.get(self.devicename, {})
        from_this_zone_sensors = {k:v   for k, v in Sensors_from_zone.items()
                                        if v.from_zone == self.from_zone}
        for sensor, Sensor in from_this_zone_sensors.items():
            Sensor.FromZone = self

#--------------------------------------------------------------------
    def __repr__(self):
        return (f"<DeviceFmZone: {self.devicename_zone}>")

#--------------------------------------------------------------------
    @property
    def zone_distance_str(self):
        return ('' if self.zone_dist_km == 0 else (f"{km_to_um(self.zone_dist_km)}"))

    @property
    def distance_km(self):
        return gps_distance_km(self.Device.loc_data_gps, self.FromZone.gps)

    @property
    def distance_km_mobapp(self):
        return gps_distance_km(self.Device.mobapp_data_gps, self.FromZone.gps)

    @property
    def is_going_towards(self):
        return self.dir_of_travel == TOWARDS

    @property
    def isnot_going_towards(self):
        return self.dir_of_travel != TOWARDS

    @property
    def is_going_awayfrom(self):
        return self.dir_of_travel == AWAY_FROM

    @property
    def isnot_going_awayfrom(self):
        return self.dir_of_travel != AWAY_FROM

#--------------------------------------------------------------------
    def update_dir_of_travel_history(self, dir_of_travel):
        '''
        Update and Format the dir_of_travel_history.
        Away-A and Towards-T directions are stored with the first-letter code (A, T)
        Other directions (inZone (Home-H, Stationary-S, OtherZone-Z, FarAway-F &
            Unknown-U) are stored with the number of occurances (H09, S04)
        '''

        dir_code = INZONE_CODES.get(dir_of_travel, dir_of_travel[0:1])
        if dir_code not in ['A', 'T']:
            if self.dir_of_travel_history.endswith(dir_code):
                self.dir_of_travel_history += '02'
            elif self.dir_of_travel_history[-3:-2] == dir_code:
                try:
                    cnt = int(self.dir_of_travel_history[-2:]) + 1
                    if cnt > 99: cnt = 99
                except:
                    cnt = 1
                self.dir_of_travel_history = self.dir_of_travel_history[:-2] + f"{cnt:0>2}"
            else:
                self.dir_of_travel_history += dir_code
            return

        if self.dir_of_travel_awayfrom_override:
            dir_code = dir_code.lower()

        self.dir_of_travel_history += dir_code

        if len(self.dir_of_travel_history) > 40:
            self.dir_of_travel_history = self.dir_of_travel_history[-30:]

        return
