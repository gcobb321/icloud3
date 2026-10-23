#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles the Device stationary zone, passthru zone delay,
#   next update time and distance methods used by iCloud3_Device.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from .global_variables  import GlobalVariables as Gb
from .const             import (HIGH_INTEGER, NOT_SET, GPS, ZONE, LAST_LOCATED_DATETIME, ICLOUD, )
from .tracking          import determine_interval as det_interval

from .utils.utils       import (is_statzone, zone_dname, )
from .utils.messaging   import (post_event, post_monitor_msg, )
from .utils.time_util   import (time_now_secs, secs_to_time, format_timer, )
from .utils.dist_util   import (gps_distance_m, gps_distance_km, km_to_um, )

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
class DeviceZoneMixin:

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
        if self.FromZone_Home.calc_dist_km < 180 or self.is_mobapp_monitored is False:
            return self.statzone_inzone_interval_secs
        return Gb.max_interval_secs / 2

    @property
    def statzone_timer_left(self):
        ''' Return the seconds left before the phone should be moved into a Stationary Zone '''
        if self.is_statzone_timer_set:
            return (self.statzone_timer - time_now_secs())
        else:
            return HIGH_INTEGER

    def statzone_reset_timer(self):
        ''' Set the Stationary Zone timer expiration time '''
        self.statzone_dist_moved_km = 0.0
        self.statzone_timer     = Gb.this_update_secs + Gb.statzone_still_time_secs
        self.statzone_latitude  = self.loc_data_latitude
        self.statzone_longitude = self.loc_data_longitude

    def statzone_clear_timer(self):
        ''' Clear the Stationary Zone timer '''
        self.statzone_reset_timer()
        self.statzone_timer = 0

#--------------------------------------------------------------------
    def update_distance_moved(self):
        self.statzone_dist_moved_km = self.distance_km(self.statzone_latitude, self.statzone_longitude)

        if Gb.is_evlog_trk_monitors_displayed:
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

        if self.was_icloud_initial_locate_done is False:    # or self.is_tracking_resumed:
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
            self.loc_data_dist_moved_km = 0.00001
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
