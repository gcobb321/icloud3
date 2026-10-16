#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   WAZE ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

from ..global_variables import GlobalVariables as Gb
from ..const            import (WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED, WAZE_OUT_OF_RANGE, WAZE_NO_DATA,
                                EVLOG_ALERT, EVLOG_RED,
                                WAZE_SERVERS_FNAME,
                                LATITUDE, LONGITUDE, ZONE, )

from ..utils.utils      import (instr, format_gps, )
from ..utils.messaging  import (post_event, post_alert, post_internal_error, log_info_msg, _evlog, _log, )
from ..utils.time_util  import (time_now_secs, secs_to_time, format_timer,  )
from ..utils.dist_util  import (km_to_um, )

from ..tracking.waze_history        import WazeRouteHistory as WazeHist
from ..tracking.waze_route_calc_ic3 import WazeRouteCalculator, WRCError

#--------------------------------------------------------------------
import time
import traceback

#--------------------------------------------------------------------
WAZE_UNDER_MIN = 'under_min'
WAZE_OVER_MAX  = 'over_max'
WAZE_NO_ROUTE  = 'no_route'     # Waze answered but could not calculate the route (internal use)
WAZE_RATE_LIMITED = 'rate_limited'  # Waze rejected the request, HTTP 429 (internal use)
RATE_LIMIT_PAUSE_SECS = [600, 1200, 1800, 3600]   # Pause for each consecutive 429, last one repeats

# Waze route cache shared by all devices (devices traveling together, distance moved
# requested for each from zone). A cached route is used if the from & to gps are
# within 0.0001° (≈11m, the 4th decimal place, same as the Waze History Database) of
# the request. A longitude degree is shorter (×cos(lat)) so it is within 11m too.
WAZE_CACHE_GPS_TOLERANCE = 0.0001
WAZE_CACHE_SECS          = 300      # Cached route expires after 5-mins (traffic changes)
WAZE_STATUS_FNAME ={WAZE_USED: 'Used',
                    WAZE_NOT_USED: 'NotUsed',
                    WAZE_PAUSED: 'Paused',
                    WAZE_OUT_OF_RANGE: 'OutOfRange',
                    WAZE_NO_DATA: 'NoData',
                    WAZE_UNDER_MIN: '<1km',
                    WAZE_OVER_MAX: '>100km'}

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class Waze(object):
    def __init__(self, is_waze_dist_method_used, waze_min_distance, waze_max_distance,
                    waze_realtime, waze_region):

        self.waze_status                  = WAZE_USED
        self.method                  = 'Waze'
        self.is_waze_dist_method_used     = is_waze_dist_method_used
        self.waze_realtime                = waze_realtime
        self.waze_region                  = waze_region.upper()
        self.waze_min_distance            = waze_min_distance
        self.waze_max_distance            = waze_max_distance
        WAZE_STATUS_FNAME[WAZE_UNDER_MIN] = f"<{waze_min_distance:.0f}km"
        WAZE_STATUS_FNAME[WAZE_OVER_MAX]  = f">{waze_max_distance:.0f}km"

        self.Device   = None
        self.FromZone = None

        self.internet_error_displayed = False
        self.no_route_msg_by_zone     = {}  # Zones Waze could not route to, msg displayed once

        self.waze_manual_pause_flag        = False  #If Paused via iCloud command
        self.is_waze_paused_close_to_zone  = False  #pause if dist from zone < 1 flag
        self.WazeRouteCalc                 = None
        self.error_server_unavailable_secs = 0       # Time (secs) of first  Server unavailable error
        self.error_server_unavailable_cnt  = 0       # Count of  things error occurred
        self.rate_limited_cnt              = 0       # Consecutive HTTP 429 pauses

        # Waze route cache [(expire secs, (from_lat, from_long, to_lat, to_long),
        #                                                   route_time, route_dist_km)]
        self.waze_cache = []

        try:
            if self.WazeRouteCalc is None:
                self.WazeRouteCalc = WazeRouteCalculator(self.waze_region, self.waze_realtime)

        except Exception as err:
            post_internal_error('Waze Route Info', traceback.format_exc)
            self.is_waze_dist_method_used = False

        if self.is_waze_dist_method_used:
            self.waze_status = WAZE_USED
            config_server_fname = WAZE_SERVERS_FNAME.get(self.waze_region.lower(), self.waze_region.lower())
            event_msg = (f"Setting Up Waze > Server-{config_server_fname} ({self.waze_region.upper()}), "
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
                and Gb.Waze.is_waze_dist_method_used)

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
            return WAZE_STATUS_FNAME[WAZE_OVER_MAX]
        elif dist_km < self.waze_min_distance:
            return WAZE_STATUS_FNAME[WAZE_UNDER_MIN]
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
        self.Device   = Device
        self.FromZone = FromZone

        try:
            self.method = 'Calc'
            if not self.is_waze_dist_method_used:
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
                results_msg       = ""
                location_id       = 0

                if (self.is_historydb_USED
                        and FromZone.distance_km <= Gb.WazeHist.max_distance):
                    self.method = 'Waze Hist'
                    waze_status, route_time, route_dist_km, dist_moved_km, \
                            location_id, results_msg = \
                            self.get_history_time_distance(Device, FromZone, check_hist_db=True)

                # Get data from Waze if not in history and not being reused or if history is not used
                if location_id == 0:
                    self.method = 'Waze'
                    waze_status, route_time, route_dist_km = \
                                    self.get_waze_distance(
                                                Device,
                                                FromZone,
                                                Device.loc_data_latitude,
                                                Device.loc_data_longitude,
                                                FromZone.FromZone.latitude,
                                                FromZone.FromZone.longitude,
                                                ZONE)

                    # Waze is working but can not route to this zone. Do not count it as
                    # a Waze server error or Waze would be paused for all zones.
                    if waze_status == WAZE_NO_ROUTE:
                        return (WAZE_NO_DATA, 0, 0, 0)

                    # Waze has already been paused by _pause_waze_rate_limited
                    if waze_status == WAZE_RATE_LIMITED:
                        return (WAZE_NO_DATA, 0, 0, 0)

                    if waze_status == WAZE_NO_DATA:
                        self._determine_next_waze_retry()
                        return (WAZE_NO_DATA, 0, 0, 0)

                    elif self.error_server_unavailable_cnt > 0:
                        self.error_server_unavailable_cnt = 0
                        self.error_server_unavailable_secs = 0

                    self.rate_limited_cnt = 0

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
                            wazehist_save_msg = f"Saved"
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
                    self.is_waze_dist_method_used = False
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
                results_msg   = 'Error'

            # event_msg =(f"Waze Info > {FromZone.from_zone_dname}, {results_msg}")
            # if results_msg == "":
            #     event_msg += (  f"TravTime-{format_timer(route_time * 60)}, "
            #                     f"Dist-{km_to_um(route_dist_km)}"
            #                     f"{wazehist_save_msg}")
            # post_event(Device, event_msg)

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
        results_msg     = ''

        if (Device.is_location_gps_good
                and Device.loc_data_dist_moved_km <= .020        # 20m
                and FromZone.waze_results):

            # If haven't move and accuracte location, use waze data
            # from last time
            waze_status, route_time, route_dist_km, dist_moved_km = \
                            FromZone.waze_results

            location_id = -2
            results_msg = "Previous"

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
                results_msg = f"#{location_id}"

            else:
                # Zone's location changed in WazeHist or invalid data. Get from Waze later
                location_id = 0

        return waze_status, route_time, route_dist_km, dist_moved_km, location_id, results_msg

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
                log_msg = (f"Waze Alert > No Location Coordinates Provided, "
                            f"GPS-{format_gps(from_lat, from_long, 0, to_lat, to_long)}")
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            elif self.WazeRouteCalc is None:
                log_msg = "Waze Route Calculator module is not set up"
                log_info_msg(log_msg)
                return (WAZE_NO_DATA, 0, 0)

            # Use the cached route if this or another device requested it recently
            route_gps = (float(from_lat), float(from_long), float(to_lat), float(to_long))
            cached_route = self._get_waze_cache(route_gps)
            if cached_route:
                route_time, route_dist_km = cached_route
                log_info_msg(f"Waze Results > Cached, "
                                f"GPS-({float(from_lat):0.5f}, {float(from_long):0.5f}) --> "
                                f"({float(to_lat):0.5f}, {float(to_long):0.5f}), "
                                f"Time-{route_time:0.2f}min, "
                                f"Distance-{route_dist_km:0.2f}km")
                if route_from == ZONE:
                    self.no_route_msg_by_zone.pop(FromZone.from_zone, None)
                return (WAZE_USED, route_time, route_dist_km)

            retry_cnt = 0
            while retry_cnt < 3:
                try:
                    retry_msg = '' if retry_cnt == 0 else (f" (#{retry_cnt})")

                    route_time, route_dist_km = \
                            self.WazeRouteCalc.calc_route_info(from_lat, from_long, to_lat, to_long)
                    retry_cnt += 1

                    # Waze is limiting requests (HTTP 429). Retrying only extends the
                    # block so pause Waze now instead of after 10 failed updates.
                    if route_time < 0 and self.WazeRouteCalc.is_rate_limited:
                        self._pause_waze_rate_limited()
                        return (WAZE_RATE_LIMITED, 0, 0)

                    # Waze answered but could not calculate the route. Retrying will
                    # not help and it is not a connection error.
                    if route_time < 0 and self.WazeRouteCalc.waze_error_msg:
                        self._display_no_route_msg(FromZone, route_from)
                        return (WAZE_NO_ROUTE, 0, 0)

                    if route_time < 0:
                        continue

                    route_time    = round(route_time, 2)
                    route_dist_km = route_dist_km
                    self._set_waze_cache(route_gps, route_time, route_dist_km)

                    self.internet_error_displayed = False
                    if route_from == ZONE:
                        self.no_route_msg_by_zone.pop(FromZone.from_zone, None)
                    return (WAZE_USED, route_time, route_dist_km)

                except Exception as err:
                    if retry_cnt > 3:
                        log_msg = (f"Waze Alert #{retry_cnt}, Retrying, Type-{err}")
                        log_info_msg(log_msg)

        except Exception as err:
            # log_exception(err)
            self._set_waze_not_available_error(err)

        self._set_waze_not_available_error(f"No data returned")

        return (WAZE_NO_DATA, 0, 0)

#--------------------------------------------------------------------
    def _get_waze_cache(self, route_gps):
        '''
        Return the cached (route_time, route_dist_km) of a route whose from & to gps
        are within 11m of route_gps (this or another device traveling with it), or
        None if there is not one or it has expired
        '''
        secs_now = time_now_secs()
        for expire_secs, cached_gps, route_time, route_dist_km in self.waze_cache:
            if (expire_secs > secs_now
                    and all(abs(gps - cached) <= WAZE_CACHE_GPS_TOLERANCE
                                for gps, cached in zip(route_gps, cached_gps))):
                return route_time, route_dist_km

        return None

    def _set_waze_cache(self, route_gps, route_time, route_dist_km):
        ''' Add the route to the cache and remove expired routes '''
        secs_now = time_now_secs()
        self.waze_cache = [cache_entry for cache_entry in self.waze_cache
                                if cache_entry[0] > secs_now]
        self.waze_cache.append((secs_now + WAZE_CACHE_SECS, route_gps, route_time, route_dist_km))

#--------------------------------------------------------------------
    def _pause_waze_rate_limited(self):
        '''
        Waze rejected the request with HTTP 429 (Too Many Requests). Pause Waze for
        10/20/30/60-mins (or the Retry-After time if longer) for each consecutive 429.
        Waze limits requests by the internet address so other iCloud3 installs on the
        same network count against the limit too.
        '''
        pause_secs = RATE_LIMIT_PAUSE_SECS[min(self.rate_limited_cnt, len(RATE_LIMIT_PAUSE_SECS)-1)]
        pause_secs = max(pause_secs, self.WazeRouteCalc.retry_after_secs)
        self.rate_limited_cnt += 1

        self.error_server_unavailable_secs = time_now_secs() + pause_secs
        post_event( f"{EVLOG_RED}Waze Alert #{self.rate_limited_cnt} > "
                    f"Waze is limiting requests (HTTP 429-Too Many Requests). "
                    f"Pausing Waze for {format_timer(pause_secs)}, "
                    f"Retry at {secs_to_time(self.error_server_unavailable_secs)}")

        # The Waze History Database reuses the travel time/distance from previous
        # requests for nearby locations which reduces the requests sent to Waze
        if self.is_historydb_USED is False:
            post_event( f"{EVLOG_ALERT}Waze Alert > The Waze History Database is not being "
                        f"used. Enabling it will reduce the requests sent to Waze and "
                        f"help prevent Waze from limiting them. "
                        f"(Configure Settings > Waze Route Distance, Time & History > Waze History Database)")

#--------------------------------------------------------------------
    def _display_no_route_msg(self, FromZone, route_from):
        '''
        Waze answered the request with an error (e.g., 'Internal Error') instead of a route.
        This happens when a location is not near a road (the zone is in a lake or the Gulf).
        Display it once for each zone until a route to the zone is found again.
        '''
        waze_error_msg = self.WazeRouteCalc.waze_error_msg

        if route_from != ZONE:
            log_info_msg(f"Waze Alert > No route for distance moved, Waze Error-{waze_error_msg}")
            return

        from_zone = FromZone.from_zone
        if from_zone in self.no_route_msg_by_zone:
            return
        self.no_route_msg_by_zone[from_zone] = waze_error_msg

        post_event( f"{EVLOG_RED}Waze Route > No route available to "
                    f"{FromZone.from_zone_dname}, Waze Dist/Time is not available")

#--------------------------------------------------------------------
    def _determine_next_waze_retry(self):
        self.error_server_unavailable_cnt += 1
        retry_interval = {10: 600, 20: 1800, 30: 3600}.get(self.error_server_unavailable_cnt, 0)
        if retry_interval > 0:
            self.error_server_unavailable_secs = time_now_secs() + retry_interval
            post_event( f"{EVLOG_RED}Waze Alert #{self.error_server_unavailable_cnt} > "
                        f"Waze Servers are not available. "
                        f"Pausing Waze for {retry_interval/60}-mins, "
                        f"Retry at {secs_to_time(self.error_server_unavailable_secs)}")

        if self.error_server_unavailable_cnt > 40:
            self.error_server_unavailable_cnt = 0
            self.error_server_unavailable_secs = 0
            self.waze_status = WAZE_PAUSED
            post_event( f"Waze Alert > "
                        f"Waze has been paused after excessive errors")

#--------------------------------------------------------------------
    def _set_waze_not_available_error(self, err):
        ''' Turn Waze off if connection error '''

        if self.internet_error_displayed:
            return
        self.internet_error_displayed = True

        error_msg = f"Waze Server Connection Error-{err}"
        # log_error_msg(error_msg)

        if (instr(err, "www.waze.com")
                and instr(err, "HTTPSConnectionPool")
                and instr(err, "Max retries exceeded")
                and instr(err, "TIMEOUT")):
            self.waze_status = WAZE_NOT_USED
            err = "A problem occurred connecting to `www.waze.com`. Waze is not available at this time"

        if err == 'No data returned':
            from_zone = self.FromZone.from_zone_dname if self.FromZone else 'Away Location'
            post_event( f"{EVLOG_RED}Waze Alert > Waze did not return route data for "
                                f"{from_zone} (server error or timeout), "
                                f"Waze Dist/Time is not available")
        else:
            post_alert( f"Waze Alert > Waze Connection Error, Region-{self.waze_region} ({err}). "
                        f"The route dist/time is not available.")

#--------------------------------------------------------------------
    def __repr__(self):
        return (f"<Waze>")