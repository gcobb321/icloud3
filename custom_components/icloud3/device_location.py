#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles the Device location data methods (raw-data update,
#   sensor value update and sensor icon selection) used by iCloud3_Device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .global_variables  import GlobalVariables as Gb
from .const             import (LOCATION, MOBAPP, ICLOUD, UNKNOWN, NAME,
                                LATITUDE, LONGITUDE, ALTITUDE, RARROW,
                                HOME, HOME_FNAME,
                                ICLOUD_HORIZONTAL_ACCURACY, ICLOUD_VERTICAL_ACCURACY,
                                ICLOUD_POSITION_TYPE, ICLOUD_BATTERY_LEVEL,
                                ICLOUD_DEVICE_CLASS, ICLOUD_DEVICE_STATUS, ICLOUD_LOW_POWER_MODE,
                                DEVICE_STATUS_CODES, DEVICE_TRACKER_STATE,
                                LAST_LOCATED, NEXT_UPDATE, LAST_UPDATE,
                                LAST_LOCATED_DATETIME, LAST_LOCATED_TIME, LAST_LOCATED_SECS,
                                NEXT_UPDATE_DATETIME, NEXT_UPDATE_TIME,
                                DEVICE_STATUS, LOW_POWER_MODE, BADGE, INFO, BATTERY,
                                GPS, GPS_ACCURACY, VERT_ACCURACY, LOCATION_SOURCE,
                                NEAR_DEVICE_USED, TRIGGER, DISTANCE_TO_DEVICES,
                                MOVED_DISTANCE, MOVED_TIME_FROM, MOVED_TIME_TO,
                                ZONE, ZONE_DNAME, ZONE_NAME, ZONE_FNAME, ZONE_DATETIME,
                                ZONE_ENTER_SECS, ZONE_EXIT_SECS,
                                LAST_ZONE, LAST_ZONE_DNAME, LAST_ZONE_NAME, LAST_ZONE_FNAME,
                                LAST_ZONE_DATETIME,
                                INTERVAL, INTERVAL_METHOD, FROM_ZONE,
                                LAST_UPDATE_DATETIME, LAST_UPDATE_TIME,
                                TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME,
                                ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                HOME_DISTANCE, MAX_DISTANCE,
                                WENT_3KM, WAZE_DISTANCE, WAZE_METHOD, CALC_DISTANCE, DIR_OF_TRAVEL,
                                TOWARDS, AWAY_FROM, INZONE, INZONE_STATZONE, INZONE_HOME,
                                TOWARDS_HOME, AWAY_FROM_HOME, )

from .const_sensor      import (SENSOR_LIST_ZONE_NAME, SENSOR_ICONS, )
from .tracking          import determine_interval as det_interval

from .utils.utils       import (is_statzone, )
from .utils.messaging   import (post_event, post_internal_error, )
from .utils.time_util   import (time_now_secs, secs_to_time, secs_to_datetime, )
from .utils.format      import (icon_box, )

import traceback

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceLocationMixin:

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
            self.sensors[INFO]                 = self.display_info_msg()

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
            self.sensors[INTERVAL_METHOD]      = self.FromZone_NextToUpdate.sensors[INTERVAL_METHOD]
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

            self.sensors[ZONE_ENTER_SECS] = self.zone_enter_secs
            self.sensors[ZONE_EXIT_SECS]  = self.zone_exit_secs

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

