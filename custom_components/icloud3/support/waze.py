#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   WAZE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables     import GlobalVariables as Gb
from ..const                import (WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED, WAZE_OUT_OF_RANGE, WAZE_NO_DATA,
                                    EVLOG_ALERT,
                                    WAZE_SERVERS_FNAME,
                                    LATITUDE, LONGITUDE, ZONE, )
from ..support.waze_history         import WazeRouteHistory as WazeHist
from ..support.waze_route_calc_ic3  import WazeRouteCalculator, WRCError

from ..helpers.common       import (instr, format_gps, )
from ..helpers.messaging    import (post_event, post_internal_error, log_info_msg, _evlog, _log, )
from ..helpers.time_util    import (time_now_secs, secs_to_time, format_timer,  )
from ..helpers.dist_util    import (km_to_um, )

import traceback
import time

Waze_UNDER_MIN = 'under_min'
Waze_OVER_MAX  = 'over_max'
WAZE_STATUS_FNAME ={WAZE_USED: 'Used',
                    WAZE_NOT_USED: '×NotUsed',
                    WAZE_PAUSED: '×Paused',
                    WAZE_OUT_OF_RANGE: '×OutOfRange',
                    WAZE_NO_DATA: '×NoData',
                    Waze_UNDER_MIN: '×Under1km',
                    Waze_OVER_MAX: '×Over100km'}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Waze(object):
    def __init__(self, distance_method_waze_flag, waze_min_distance, waze_max_distance,
                    waze_realtime, waze_region):

        self.waze_status                = WAZE_USED
        self.distance_method_waze_flag  = distance_method_waze_flag
        self.waze_realtime              = waze_realtime
        self.waze_region                = waze_region.upper()
        self.waze_min_distance          = waze_min_distance
        self.waze_max_distance          = waze_max_distance
        WAZE_STATUS_FNAME[Waze_UNDER_MIN] = f"×Under{waze_min_distance}km"
        WAZE_STATUS_FNAME[Waze_OVER_MAX] = f"×Over{waze_max_distance}km"

        self.connection_error_displayed = False

        self.waze_manual_pause_flag        = False  #If Paused via iCloud command
        self.waze_close_to_zone_pause_flag = False  #pause if dist from zone < 1 flag
        self.WazeRouteCalc                 = None
        self.error_server_unavailable_secs = 0       # Time (secs) of first  Server unavailable error
        self.error_server_unavailable_cnt  = 0       # Count of  things error occurred

        try:
            if self.WazeRouteCalc is None:
                self.WazeRouteCalc = WazeRouteCalculator(self.waze_region, self.waze_realtime)

        except Exception as err:
            post_internal_error('Waze Route Info', traceback.format_exc)
            self.distance_method_waze_flag = False

        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED
            config_server_fname = WAZE_SERVERS_FNAME.get(self.waze_region.lower(), self.waze_region.lower())
            event_msg = (f"Set Up Waze > Server-{config_server_fname} ({self.waze_region.upper()}), "
                        f"CountryCode-{Gb.country_code.upper()}, "
                        f"MinDist-{self.waze_min_distance}km, "
                        f"MaxDist-{self.waze_max_distance}km, "
                        f"Realtime-{self.waze_realtime}, "
                        f"HistoryDatabaseUsed-{Gb.waze_history_database_used}")
        else:
            self.waze_status = WAZE_NOT_USED
            event_msg = ("Waze Route Service is not being used")
        post_event(event_msg)

    @property
    def is_status_USED(self):
        return (self.waze_status == WAZE_USED
                and Gb.Waze.distance_method_waze_flag)

    @property
    def is_historydb_USED(self):
        return Gb.WazeHist.use_wazehist_flag

    @property
    def is_status_NOT_USED(self):
        return self.waze_status == WAZE_NOT_USED

    @property
    def is_status_PAUSED(self):
        return self.waze_status == WAZE_PAUSED

    @property
    def is_status_NO_DATA(self):
        return self.waze_status == WAZE_NO_DATA

    @property
    def is_status_OUT_OF_RANGE(self):
        return self.waze_status == WAZE_OUT_OF_RANGE

    def range_msg(self, dist_km):
        if dist_km > self.waze_max_distance:
            return WAZE_STATUS_FNAME[Waze_OVER_MAX]
        elif dist_km < self.waze_min_distance:
            return WAZE_STATUS_FNAME[Waze_UNDER_MIN]
        else:
            return 'inRange'


    @property
    def waze_status_fname(self):
        return WAZE_STATUS_FNAME.get(self.waze_status, 'Waze-Unknown')


########################################################
#
#   WAZE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def get_route_time_distance(self, Device, FromZone, check_hist_db=True):
        '''
        Get the travel time and distance for the Device's current location from the
        track from zone (FromZone) using the Waze History Database, the Waze Route
        Service or the direct calculation. Also determine the distance moved from the
        last location.

        Returns:
            Waze Status - Used, Paused, Not Used, Error, etc.
            Travel Time from the zone to the device
            Distance from the zone to the device
            Distance moved from the last device's location
        '''

        try:
            if not self.distance_method_waze_flag:
                return (WAZE_NOT_USED, 0, 0, 0)
            elif self.is_status_PAUSED:
                return (WAZE_PAUSED, 0, 0, 0)
            elif Device.loc_data_zone == FromZone.from_zone:
                return (WAZE_NOT_USED, 0, 0, 0)

            if self.error_server_unavailable_secs > 0:
                if time_now_secs() < self.error_server_unavailable_secs:
                    return (WAZE_NO_DATA, 0, 0, 0)

                # Reset error and retry Waze after 10/30/60-mins
                self.error_server_unavailable_secs = 0
                post_event("Waze Route Service > Resuming")

            try:
                from_zone         = FromZone.from_zone
                waze_status       = WAZE_USED
                route_time        = 0
                route_dist_km     = 0
                dist_moved_km     = 0
                wazehist_save_msg = ''
                waze_source_msg   = ""
                location_id       = 0

                if self.is_historydb_USED:
                    waze_status, route_time, route_dist_km, dist_moved_km, \
                            location_id, waze_source_msg = \
                            self.get_history_time_distance(Device, FromZone, check_hist_db=True)

                # Get data from Waze if not in history and not being reused or if history is not used
                if location_id == 0:
                    waze_status, route_time, route_dist_km = \
                                    self.get_waze_distance(
                                                Device,
                                                FromZone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                FromZone.FromZone.latitude,
                                                FromZone.FromZone.longitude,
                                                ZONE)

                    self._determine_next_waze_retry()

                    if waze_status == WAZE_NO_DATA:
                        self._determine_next_waze_retry()
                        return (WAZE_NO_DATA, 0, 0, 0)

                    elif self.error_server_unavailable_cnt > 0:
                        self.error_server_unavailable_cnt = 0
                        self.error_server_unavailable_secs = 0

                    # Add a time/distance record to the waze history database
                    try:
                        if (self.is_historydb_USED
                                and Gb.wazehist_zone_id
                                and FromZone.distance_km < Gb.WazeHist.max_distance
                                and route_time > .25
                                and Gb.wazehist_zone_id.get(from_zone, 0) > 0):
                            location_id = Gb.WazeHist.add_location_record(
                                                        Gb.wazehist_zone_id[from_zone],
                                                        Device.loc_data_latitude,
                                                        Device.loc_data_longitude,
                                                        route_time,
                                                        route_dist_km)
                            wazehist_save_msg =f" (Saved)"
                    except:
                        pass

                if route_dist_km == 0:
                    route_time = 0

                # Get distance moved since last update
                if Device.loc_data_dist_moved_km < .5:
                    dist_moved_km = Device.loc_data_dist_moved_km
                else:
                    last_status, last_time, dist_moved_km = \
                                    self.get_waze_distance(
                                                    Device, FromZone,
                                                    Device.sensors[LATITUDE],
                                                    Device.sensors[LONGITUDE],
                                                    Device.loc_data_latitude,
                                                    Device.loc_data_longitude,
                                                    "moved")

            except Exception as err:
                post_internal_error('Waze Route Info', traceback.format_exc)
                if err == "Name 'WazeRouteCalculator' is not defined":
                    self.distance_method_waze_flag = False
                    return (WAZE_NOT_USED, 0, 0, 0)

                return (WAZE_NO_DATA, 0, 0, 0)

            try:
                if (route_dist_km > self.waze_max_distance
                        or route_dist_km < self.waze_min_distance):
                    waze_status = WAZE_OUT_OF_RANGE

            except Exception as err:
                post_internal_error('Waze Route Info', traceback.format_exc)
                route_dist_km = 0
                dist_moved_km     = 0
                route_time        = 0
                waze_source_msg   = 'Error'

            event_msg =(f"Waze Route Info > {waze_source_msg}")
            if waze_source_msg == "":
                event_msg += (  f"TravTime-{format_timer(route_time * 60)}, "
                                f"Dist-{km_to_um(route_dist_km)}, "
                                f"Moved-{km_to_um(dist_moved_km)}"
                                f"{wazehist_save_msg}")
            post_event(Device, event_msg)

            FromZone.waze_results = (WAZE_USED, route_time, route_dist_km, dist_moved_km)

            return FromZone.waze_results

        except Exception as err:
            self._set_waze_not_available_error(err)

            return (WAZE_NO_DATA, 0, 0, 0)

#--------------------------------------------------------------------
    def get_history_time_distance(self, Device, FromZone, check_hist_db=True):
        '''
        Get the time & distance from the history database or the previous results

        Return: [route_time, route_dist_km, location_id]
        '''

        from_zone       = FromZone.from_zone
        waze_status     = WAZE_USED
        route_time      = 0
        route_dist_km   = 0
        dist_moved_km   = 0
        waze_source_msg = ''

        if (Device.is_location_gps_good
                and Device.loc_data_dist_moved_km <= .020        # 20m
                and FromZone.waze_results):

            # If haven't move and accuracte location, use waze data
            # from last time
            waze_status, route_time, route_dist_km, dist_moved_km = \
                            FromZone.waze_results

            location_id = -2
            #waze_source_msg = "Using Previous Waze Location Info "
            waze_source_msg = ( f"Moved-{km_to_um(Device.loc_data_dist_moved_km)}, "
                                f"Using previous results")

        elif check_hist_db is False or self.is_historydb_USED is False:
            location_id = 0

        else:
            # Get waze data from Waze History and update usage counter
            # for that location. (location id is 0 if not in history)
            route_time, route_dist_km, location_id  = \
                    Gb.WazeHist.get_location_time_dist(
                                            from_zone,
                                            Device.loc_data_latitude,
                                            Device.loc_data_longitude)

            if (location_id > 0
                    and route_time > 0
                    and route_dist_km > 0):
                Gb.WazeHist.update_usage_cnt(location_id)
                waze_source_msg = f"Using Route History Database (#{location_id})"

            else:
                # Zone's location changed in WazeHist or invalid data. Get from Waze later
                location_id = 0

        return waze_status, route_time, route_dist_km, dist_moved_km, location_id, waze_source_msg

#--------------------------------------------------------------------
    def get_waze_distance(self, Device, FromZone, from_lat, from_long,
                    to_lat, to_long, route_from):
        """
        Example output:
            Time 72.42 minutes, distance 121.33 km.
            (72.41666666666667, 121.325)

        See https://github.com/home-assistant/home-assistant/blob
        /master/homeassistant/components/sensor/waze_travel_time.py
        See https://github.com/kovacsbalu/WazeRouteCalculator
        """

        try:
            if from_lat == 0 or from_long == 0 or to_lat == 0 or to_long == 0:
                log_msg = (f"Waze request error > No location coordinates provided, "
                            f"GPS-{format_gps(from_lat, from_long, 0, to_lat, to_long)}")
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            elif self.WazeRouteCalc is None:
                log_msg = "Waze Route Calculator module is not set up"
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            retry_cnt = 0
            while retry_cnt < 3:
                try:
                    retry_msg = '' if retry_cnt == 0 else (f" (#{retry_cnt})")

                    route_time, route_dist_km = \
                            self.WazeRouteCalc.calc_route_info(from_lat, from_long, to_lat, to_long)
                    retry_cnt += 1
                    if route_time < 0:
                        continue

                    route_time    = round(route_time, 2)
                    route_dist_km = route_dist_km

                    self.connection_error_displayed = False
                    return (WAZE_USED, route_time, route_dist_km)

                except Exception as err:
                    if retry_cnt > 3:
                        log_msg = (f"Waze Server Error #{retry_cnt}, Retrying, Type-{err}")
                        log_info_msg(log_msg)

        except Exception as err:
            # log_exception(err)
            self._set_waze_not_available_error(err)

        self._set_waze_not_available_error(f"No data returned")

        return (WAZE_NO_DATA, 0, 0)

#--------------------------------------------------------------------
    def _determine_next_waze_retry(self):
        self.error_server_unavailable_cnt += 1
        retry_interval = {10: 600, 20: 1800, 30: 3600}.get(self.error_server_unavailable_cnt, 0)
        if retry_interval > 0:
            self.error_server_unavailable_secs = time_now_secs() + retry_interval
            post_event( f"Waze Route Service Error #{self.error_server_unavailable_cnt} > "
                        f"An error occurred connecting to Waze Servers, "
                        f"distance will be calculated, Travel Time not available. "
                        f"Waze will be paused for {retry_interval/60}-mins and will "
                        f"retry at {secs_to_time(self.error_server_unavailable_secs)}")

        if self.error_server_unavailable_cnt > 40:
            self.error_server_unavailable_cnt = 0
            self.error_server_unavailable_secs = 0
            self.waze_status = WAZE_PAUSED
            post_event( f"Waze Route Service > "
                        f"Waze has been paused after excessive errors")

#--------------------------------------------------------------------
    def _set_waze_not_available_error(self, err):
        ''' Turn Waze off if connection error '''

        if self.connection_error_displayed:
            return
        self.connection_error_displayed = True

        error_msg = f"Waze Server Connection Error-{err}"
        # log_error_msg(error_msg)

        if (instr(err, "www.waze.com")
                and instr(err, "HTTPSConnectionPool")
                and instr(err, "Max retries exceeded")
                and instr(err, "TIMEOUT")):
            self.waze_status = WAZE_NOT_USED
            err = "A problem occurred connecting to `www.waze.com`. Waze is not available at this time"

        post_event(f"{EVLOG_ALERT}Alert > Waze Connection Error, Region-{self.waze_region} > {err}. "
                    "The route distance will be calculated, Travel Time is not available.")

#--------------------------------------------------------------------
    def __repr__(self):
        return (f"<Waze>")