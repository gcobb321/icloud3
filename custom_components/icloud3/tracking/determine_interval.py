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
#
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from ..global_variables     import GlobalVariables as Gb
from ..const                import (HOME, NOT_HOME, AWAY, NOT_SET, NOT_HOME_ZONES, HIGH_INTEGER,
                                    CRLF, CHECK_MARK, CIRCLE_X, LTE, LT, PLUS_MINUS, RED_X, CIRCLE_STAR2, CRLF_DOT,
                                    RARROW,
                                    STATIONARY, STATIONARY_FNAME, STATZONE, WATCH, MOBAPP, YELLOW_ALERT,
                                    ICLOUD,
                                    AWAY_FROM, FAR_AWAY, TOWARDS, PAUSED, INZONE, INZONE_STATZONE, INZONE_HOME,
                                    ERROR, UNKNOWN, VALID_DATA, NEAR_DEVICE_DISTANCE,
                                    WAZE,
                                    WAZE_USED, WAZE_NOT_USED, WAZE_PAUSED, WAZE_OUT_OF_RANGE, WAZE_NO_DATA,
                                    EVLOG_TIME_RECD, EVLOG_ALERT,
                                    NEAR_DEVICE_USEABLE_SYM, EXIT_ZONE,
                                    ZONE, ZONE_INFO, INTERVAL,
                                    DISTANCE, ZONE_DISTANCE, ZONE_DISTANCE_M, ZONE_DISTANCE_M_EDGE,
                                    MAX_DISTANCE, CALC_DISTANCE, WAZE_DISTANCE, WAZE_METHOD,
                                    TRAVEL_TIME, TRAVEL_TIME_MIN, TRAVEL_TIME_HHMM, ARRIVAL_TIME, DIR_OF_TRAVEL, MOVED_DISTANCE,
                                    LAST_LOCATED, LAST_LOCATED_TIME, LAST_LOCATED_DATETIME,
                                    LAST_UPDATE, LAST_UPDATE_TIME, LAST_UPDATE_DATETIME,
                                    NEXT_UPDATE, NEXT_UPDATE_TIME, NEXT_UPDATE_DATETIME,
                                    LAST_LOCATED,
                                    )

from ..utils.utils        import (instr, isbetween, round_to_zero, is_zone, is_statzone, isnot_zone,
                                    zone_dname, )
from ..utils.messaging    import (post_event, post_error_msg,
                                    post_evlog_greenbar_msg, clear_evlog_greenbar_msg,
                                    post_internal_error, post_monitor_msg, log_debug_msg, log_data,
                                    log_info_msg, log_info_msg_HA, log_exception, _evlog, _log, )
from ..utils.time_util    import (secs_to_time, format_timer, format_time_age, format_secs_since,
                                    secs_since, mins_since, time_to_12hrtime, secs_to_datetime, secs_to, format_age,
                                    datetime_now, time_now, time_now_secs, secs_to_hhmm, secs_to_hhmm, )
from ..utils.dist_util    import (km_to_mi, km_to_um, format_dist_km,  format_dist_m,
                                    km_to_um, m_to_um, m_to_um_ft, )


import homeassistant.util.dt as dt_util
import traceback

# location_data fields
LD_STATUS      = 0
LD_ZONE_DIST   = 1
LD_ZONE_DIST_M = 2
LD_WAZE_DIST   = 3
LD_CALC_DIST   = 4
LD_WAZE_TIME   = 5
LD_MOVED       = 6
LD_DIRECTION   = 7
LD_AWAYFROM_OVERRIDE = 8

#waze_from_zone fields
WAZ_STATUS   = 0
WAZ_TIME     = 1
WAZ_DISTANCE = 2
WAZ_MOVED    = 3

# Interval range table used for setting the interval based on a retry count
# The key is starting retry count range, the value is the interval (in minutes)
# poor_location_gps cnt, icloud_authentication cnt (default)
OLD_LOCATION_CNT       = 1.1
AUTH_ERROR_CNT         = 1.2
# RETRY_INTERVAL_RANGE_1 = 15s*4=1m, 4*1m=4m=5m, 4*5m=20m=25m, 4*30m=2h=2.5h, 4*1h=4h=6.5h

# RETRY_INTERVAL_RANGE_1 = 30s*4=2m, 4*1.5m=6m=8m, 4*15m=1h=1h8m, 4*30m=2h=3h8m, 4*1h=4h=6.5h
# RETRY_INTERVAL_RANGE_1 = {0:.25, 4:1, 8:5, 12:30, 16:60, 20:60}
# RETRY_INTERVAL_RANGE_1 = 15s*5=1.25m, 5*1m=5m=6m, 5*5m=25m=30m, 5*30m=2.5h=3, 4*1h=4h=6h25h
RETRY_INTERVAL_RANGE_1 = {0:.25, 4:.5, 8:1, 12:5, 16:15, 20:30, 24:60}
MOBAPP_REQUEST_LOC_CNT = 2.1
RETRY_INTERVAL_RANGE_2 = {0:.5, 4:2, 8:30, 12:60, 16:60}
# RETRY_INTERVAL_RANGE_2 = {0:.5, 4:2, 8:30, 12:60, 14:120, 16:180, 18:240, 20:240}

#<><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><><>
def determine_interval(Device, FromZone):
    '''
    Calculate new interval. Return location based attributes.
    The durrent location:   Device.loc_data_latitude/longitude.
    The last location:      Device.sensors[LATITUDE]/[LONGITUDE]
    '''

    battery10_flag  = (0 > Device.dev_data_battery_level >= 10)
    battery5_flag   = (0 > Device.dev_data_battery_level >= 5)

    isin_zone       = (Device.loc_data_zone not in NOT_HOME_ZONES)
    isnotin_zone    = (Device.loc_data_zone in NOT_HOME_ZONES)
    wasin_zone      = (Device.sensors[ZONE] not in NOT_HOME_ZONES)

    isin_zone_home  = (Device.loc_data_zone == HOME)
    wasin_zone_home = (Device.sensor_zone == HOME)

    devicename = Device.devicename
    Device.FromZone_BeingUpdated = FromZone

    if FromZone.from_zone == Device.loc_data_zone:
        Device.FromZone_LastIn = FromZone

    if Device.offline_secs > 0 and Device.is_online:
        post_event(devicename,
                    f"{EVLOG_ALERT}Device back Online > "
                    f"WentOfflineAt-{format_time_age(Device.offline_secs)}, "
                    f"DeviceStatus-{Device.device_status}")
        Device.offline_secs = 0
        Device.display_info_msg(Device.format_info_msg, new_base_msg=True)

    #--------------------------------------------------------------------------------
    #Device.write_ha_sensor_state(LAST_LOCATED, Device.loc_data_time)
    Device.write_ha_sensors_state([LAST_LOCATED, NEXT_UPDATE, LAST_UPDATE])

    if used_near_device_results(Device, FromZone):
        return FromZone.sensors

    Device.NearDeviceUsed = None

    #--------------------------------------------------------------------------------
    location_data = _get_distance_data(Device, FromZone)

    # If an error occurred, the [1] entry contains an attribute that can be passed to
    # display_info_code to display an error message
    if (location_data[LD_STATUS] == ERROR):
        return location_data[LD_ZONE_DIST]

    dist_from_zone_km       = location_data[LD_ZONE_DIST]
    dist_from_zone_m        = location_data[LD_ZONE_DIST_M]
    waze_dist_from_zone_km  = location_data[LD_WAZE_DIST]
    calc_dist_from_zone_km  = location_data[LD_CALC_DIST]
    waze_time_from_zone     = location_data[LD_WAZE_TIME]
    dist_moved_km           = location_data[LD_MOVED]
    dir_of_travel           = location_data[LD_DIRECTION]
    dir_of_travel_awayfrom_override = location_data[LD_AWAYFROM_OVERRIDE]

    awayfrom_override_star = '*' if dir_of_travel_awayfrom_override else ''
    log_msg = ( f"DistFmZome-{dist_from_zone_km}, "
                f"Moved-{dist_moved_km}, "
                f"Waze-{waze_dist_from_zone_km}, "
                f"Calc-{calc_dist_from_zone_km}, "
                f"TravTime-{waze_time_from_zone}, "
                f"Dir-{dir_of_travel}{awayfrom_override_star}, "
                f"DirHist-{FromZone.dir_of_travel_history[-40:]}")
    log_debug_msg(devicename, log_msg)


    #--------------------------------------------------------------------------------
    # The following checks the distance from home and assigns a
    # polling interval in minutes.  It assumes a varying speed and
    # is generally set so it will poll one or twice for each distance
    # group. When it gets real close to home, it switches to once
    # each 15 seconds so the distance from home will be calculated
    # more often and can then be used for triggering automations
    # when you are real close to home. When home is reached,
    # the distance will be 0.

    Device.display_info_msg( f"Determine Interval-{FromZone.info_status_msg}")

    # Reset got zone exit trigger since now in a zone for next
    # exit distance check. Also reset Stat Zone timer and dist moved.
    if isin_zone:
        Device.got_exit_trigger_flag = False
        Device.statzone_clear_timer

    waze_time_msg = 'NotUsed'
    calc_interval_secs = round(km_to_mi(dist_from_zone_km) * Gb.travel_time_factor) * 60
    if Gb.Waze.is_status_USED:
        waze_interval_secs = round(waze_time_from_zone * 60 * Gb.travel_time_factor , 0)
    else:
        waze_interval_secs = 0

    #--------------------------------------------------------------------------------
    #if more than 3km(1.8mi) then assume driving
    if FromZone is Device.FromZone_Home:
        # if dist_from_zone_km >= .0030:   # Force True when testing and at Home
        if dist_from_zone_km >= 3:
            Device.went_3km = True

    #--------------------------------------------------------------------------------
    interval_secs   = 15
    interval_str    = ''
    interval_method = ''
    interval_multiplier = 1

    if Device.state_change_flag:
        if isin_zone:
            #inzone & old location
            if Device.is_location_old_or_gps_poor and battery10_flag is False:
                interval_method = '1.OldLoc/GPS'
                interval_secs   = _get_interval_for_error_retry_cnt(Device, OLD_LOCATION_CNT)

            elif Device.isnotin_statzone:
                interval_method = "1.EnterZone"
                interval_secs   = Device.inzone_interval_secs

        #battery < 5% and near zone
        elif battery5_flag and dist_from_zone_km <= 1:
            interval_method = "2.Battery5%"
            interval_secs   = 15

        #battery < 10%
        elif battery10_flag:
            interval_method = "2.Battery10%"
            interval_secs   = Device.statzone_inzone_interval_secs

        #exited zone, set to short interval if other devices are in same zone
        elif isnotin_zone and wasin_zone:
            interval_method = "2.ExitZone"
            interval_secs   = Gb.exit_zone_interval_secs

            if Device.loc_data_zone == HOME:
                FromZone.max_dist_km = 0.0
                Device.went_3km = False

        else:
            interval_method = "2.ZoneChng"
            interval_secs   = 240

    # Exit_Zone trigger & away & exited less than 1 min ago
    elif (instr(Device.trigger, EXIT_ZONE)
            and isnotin_zone
            and secs_since(Device.mobapp_zone_exit_secs) < 60):
        interval_method = '3.ExitTrig'
        interval_secs   = Gb.exit_zone_interval_secs

    #inzone & poor gps & check gps accuracy when inzone
    elif (Device.is_gps_poor
            and isin_zone
            and Gb.discard_poor_gps_inzone_flag is False):
        interval_method = '3.PoorGPSinZone'
        interval_secs   = _get_interval_for_error_retry_cnt(Device, OLD_LOCATION_CNT)

    elif Device.is_gps_poor:
        interval_method = '3.PoorGPS'
        interval_secs   = _get_interval_for_error_retry_cnt(Device, OLD_LOCATION_CNT)

    elif Device.is_location_old_or_gps_poor:
        interval_method = '3.OldLoc/GPS'
        interval_secs   = _get_interval_for_error_retry_cnt(Device, OLD_LOCATION_CNT)

    elif battery10_flag and dist_from_zone_km > 1:
        interval_method = "3.Battery10%"
        interval_secs   = Device.statzone_inzone_interval_secs

    elif isin_zone_home or (dist_from_zone_km < .05 and dir_of_travel == TOWARDS):
        interval_method = '3.AtHome'
        interval_secs   = Device.inzone_interval_secs

    #in another zone and inzone time > travel time
    elif isin_zone and Device.inzone_interval_secs > waze_interval_secs:
        interval_method = '3.InZone'
        interval_secs   = Device.inzone_interval_secs

    elif dir_of_travel ==  NOT_SET:
        interval_method = '3.NeedInfo'
        interval_secs   = 150

    elif dist_from_zone_km < 2 and dir_of_travel == AWAY_FROM and waze_interval_secs > 0:
        interval_method = '3.<2km+AwayFm'
        interval_secs   = Device.old_loc_threshold_secs  #1.5 mi & going Away

    elif dist_from_zone_km < 2 and Device.went_3km:
        interval_method = '3.<2km'
        interval_secs   = 15          #1.5 mi = real close and driving

    elif dist_from_zone_km < 2:       #1.5 mi=1 min
        interval_method = '3.<3km'
        interval_secs   = 60

    elif dist_from_zone_km < 3.5:      #2 mi=1.5 min
        interval_method = '3.<3.5km'
        interval_secs   = 90

    elif waze_time_from_zone > 5 and waze_interval_secs > 0:
        interval_method = '3.WazeTime'
        interval_secs   = waze_interval_secs

    elif dist_from_zone_km < 5:        #3 mi=2 min
        interval_method = '3.<5km'
        interval_secs   = 120

    elif dist_from_zone_km < 8:        #5 mi=3 min
        interval_method = '3.<8km'
        interval_secs   = 180

    elif dist_from_zone_km < 12:       #7.5 mi=5 min
        interval_method = '3.<12km'
        interval_secs   = 300

    elif dist_from_zone_km < 20:       #12 mi=10 min
        interval_method = '3.<20km'
        interval_secs   = 600

    elif dist_from_zone_km < 40:       #25 mi=15 min
        interval_method = '3.<40km'
        interval_secs   = 900

    elif dist_from_zone_km > 150:      #90 mi=1 hr
        interval_method = '3.>150km'
        interval_secs   = 3600

    else:
        interval_method = '3.Calc'
        interval_secs   = calc_interval_secs

    # if (dir_of_travel in ('', ' ', '___', AWAY_FROM)
    #         and isbetween(interval_secs, 30, 180)):
    #     interval_method += '+6.AwayFm+<3min'
    #     interval_secs = 180

    if (dir_of_travel == AWAY_FROM
            and calc_dist_from_zone_km >= 3
            and Device.state_change_flag is False
            and Device.is_gps_good
            and not Gb.Waze.distance_method_waze_flag
            and Device.fixed_interval_secs == 0):
        interval_method += '+6.AwayFm+Calc'
        interval_multiplier = 2    #calc-increase timer

    elif dir_of_travel == NOT_SET and interval_secs > 180:
        interval_method += '+6.>180s'
        interval_secs    = 180

    #Turn off waze close to zone flag to use waze after leaving zone or getting more than 1km from it
    if Gb.Waze.waze_close_to_zone_pause_flag:
        if isin_zone or calc_dist_from_zone_km >= 1:
            Gb.Waze.waze_close_to_zone_pause_flag = False

    #if triggered by Mobile App (Zone Enter/Exit, Manual, Fetch, etc.)
    if (Device.mobapp_update_flag
            and interval_secs < 180
            and interval_secs > 30):
        interval_method += '+8.MobAppTrig'
        interval_secs    = 180

    #if changed zones on this poll reset multiplier
    # if Device.state_change_flag:
    #     interval_multiplier = 1

    #Check accuracy again to make sure nothing changed, update counter
    # if Device.is_gps_poor:
    #     interval_multiplier = 1

    try:
        #Real close, final check to make sure interval_secs is not adjusted
        if (interval_secs <= 60
                or ((0 > Device.dev_data_battery_level >= 33) and interval_secs >= 120)):
            interval_multiplier = 1

        interval_secs     = interval_secs * interval_multiplier
        interval_secs, x  = divmod(interval_secs, 5)
        interval_secs     = interval_secs * 5

        # Use interval_secs if > StatZone interval unless the StatZone interval is the device's
        # inzone interval
        if Device.isin_statzone:
            interval_method = "9.StatZone"
            interval_secs = 300 if Device.StatZone.is_small_statzone else \
                            Device.statzone_inzone_interval_secs

        # Use fixed_interval_secs if > 5m, not in a zone etc.
        elif (Device.fixed_interval_secs >= 300
                and interval_secs > 300
                and Device.isnotin_zone_or_statzone
                and Device.is_location_good
                and Device.is_offline is False
                and Device.is_passthru_timer_set is False):
            interval_secs = Device.fixed_interval_secs
            interval_method = "9.Fixed"

        #check for max interval_secs, override in zone times
        elif interval_secs > Gb.max_interval_secs:
            if Device.isin_statzone:
                interval_method = "9.inZoneMax"
                interval_secs   = Device.statzone_inzone_interval_secs
            elif isin_zone:
                pass

            elif (Device.is_location_good
                    and Device.is_offline is False
                    and Device.is_passthru_timer_set is False):
                interval_method = "9.Max"
                interval_secs   = Gb.max_interval_secs

        # if moving, make sure interval is not larger than the travtime*factor
        if (dir_of_travel in [AWAY_FROM, TOWARDS]
                and waze_interval_secs > 0
                and interval_secs > (waze_interval_secs * (Gb.travel_time_factor * 1.5))):
            interval_secs = waze_interval_secs * Gb.travel_time_factor

        interval_str = format_timer(interval_secs)

        if interval_multiplier > 1:
            interval_method += (f"x{interval_multiplier}")

        #check if next update is past midnight (next day), if so, adjust it
        next_update_secs = round((Gb.this_update_secs + interval_secs)/5, 0) * 5

        # If the device is monitored, the get the smallest next_update_secs for the tracked devices.
        # Override the results of this device with the next one to be updated.
        try:
            if Device.is_monitored:
                for _Device in Gb.Devices_by_devicename_tracked.values():
                    if (_Device.FromZone_TrackFrom
                            and _Device.near_device_distance <= NEAR_DEVICE_DISTANCE
                            and next_update_secs < _Device.FromZone_TrackFrom.next_update_secs):

                        next_update_secs = _Device.FromZone_TrackFrom.next_update_secs
                        interval_secs    = _Device.FromZone_TrackFrom.interval_secs
                        interval_str     = _Device.FromZone_TrackFrom.interval_str
                        interval_method  = _Device.fname

        except:
            pass

        # Update all dates and other fields
        Device.loc_data_dist_moved_km = dist_moved_km
        FromZone.interval_secs    = interval_secs
        FromZone.interval_str     = interval_str
        FromZone.next_update_secs = next_update_secs
        FromZone.next_update_time = secs_to_time(next_update_secs)
        FromZone.last_update_secs = Gb.this_update_secs
        FromZone.last_update_time = time_to_12hrtime(Gb.this_update_time)
        FromZone.interval_method  = interval_method

        FromZone.dir_of_travel    = dir_of_travel
        FromZone.dir_of_travel_awayfrom_override = dir_of_travel_awayfrom_override
        FromZone.update_dir_of_travel_history(dir_of_travel)

        monitor_msg = f"DirHist-{FromZone.dir_of_travel_history[-40:]}"
        post_monitor_msg(devicename, monitor_msg)

    except Exception as err:
        sensor_msg = post_internal_error('Update FromZone Times', traceback.format_exc)

    #--------------------------------------------------------------------------------
    # if poor gps and moved less than 1km, redisplay last distances
    if (Device.state_change_flag is False
            and Device.is_gps_poor
            and dist_moved_km < 1):
        dist_from_zone_km      = FromZone.zone_dist_km
        dist_from_zone_m       = FromZone.zone_dist_m
        waze_dist_from_zone_km = FromZone.waze_dist_km
        calc_dist_from_zone_km = FromZone.calc_dist_km
        waze_time_from_zone    = FromZone.waze_time

    else:
        #save for next poll if poor gps
        FromZone.zone_dist_km = dist_from_zone_km
        FromZone.zone_dist_m  = dist_from_zone_m
        FromZone.waze_dist_km = waze_dist_from_zone_km
        FromZone.waze_time    = waze_time_from_zone
        FromZone.calc_dist_km = calc_dist_from_zone_km

    waze_time_msg = format_timer(waze_time_from_zone * 60)

    if (Device.is_location_gps_good
            and interval_secs > 60
            and waze_dist_from_zone_km > FromZone.max_dist_km):
        FromZone.max_dist_km = waze_dist_from_zone_km

    if Device.mobapp_monitor_flag:
        # If monitored and the mobapp state is before the last update, reset it since
        # the mobapp is not really used for monitored devices
        if (Device.is_monitored
                and Device.mobapp_data_state != Device.loc_data_zone
                and Device.last_update_loc_secs > (Device.mobapp_data_state_secs + Device.old_loc_threshold_secs)):
            Device.mobapp_data_state = NOT_SET

    #--------------------------------------------------------------------------------
    #Make sure the new 'last state' value is the internal value for
    #the state (e.g., Away-->not_home) to reduce state change triggers later.
    sensors                       = {}
    sensors[LAST_LOCATED_DATETIME]= Device.loc_data_datetime
    sensors[LAST_LOCATED_TIME]    = Device.loc_data_time
    sensors[LAST_LOCATED]         = Device.loc_data_time

    sensors.update(_update_next_update_fields_and_sensors(None, interval_secs))

    sensors[TRAVEL_TIME]          = format_timer(waze_time_from_zone * 60)
    sensors[TRAVEL_TIME_MIN]      = f"{waze_time_from_zone:.0f} min"
    sensors[TRAVEL_TIME_HHMM]     = secs_to_hhmm(waze_time_from_zone * 60)
    sensors[ARRIVAL_TIME]         = _sensor_arrival_time(Device, FromZone)
    sensors[DIR_OF_TRAVEL]        = dir_of_travel
    sensors[MAX_DISTANCE]         = km_to_mi(FromZone.max_dist_km)
    sensors[DISTANCE]             = km_to_mi(dist_from_zone_km)
    sensors[ZONE_DISTANCE]        = km_to_mi(dist_from_zone_km)
    sensors[ZONE_DISTANCE_M]      = dist_from_zone_m
    sensors[ZONE_DISTANCE_M_EDGE] = abs(dist_from_zone_m - FromZone.from_zone_radius_m)
    sensors[WAZE_DISTANCE]        = km_to_mi(waze_dist_from_zone_km)
    sensors[WAZE_METHOD]          = Gb.Waze.waze_status_fname
    sensors[CALC_DISTANCE]        = km_to_mi(calc_dist_from_zone_km)
    sensors[MOVED_DISTANCE]       = km_to_mi(dist_moved_km)
    sensors[ZONE_INFO]            = _sensor_zone_info(Device, FromZone)

    #save for event log
    if type(waze_time_msg) != str: waze_time_msg = ''
    FromZone.last_travel_time  = waze_time_msg
    FromZone.last_distance_km  = dist_from_zone_km
    FromZone.last_distance_str = km_to_um(dist_from_zone_km)
    FromZone.sensors.update(sensors)

    Device.loc_time_updates_icloud = [Device.loc_data_time]
    if Device.is_location_gps_good: Device.old_loc_cnt = 0
    Device.display_info_msg(Device.format_info_msg, new_base_msg=True)

    post_results_message_to_event_log(Device, FromZone)
    post_zone_time_dist_event_msg(Device, FromZone)

    return sensors

#...............................................................................abs
def _sensor_arrival_time(Device, FromZone):

    if (Device.isin_zone
            and is_statzone(Device.loc_data_zone) is False
            and Device.loc_data_zone == FromZone.from_zone):
        days = secs_since(Device.zone_change_secs)/86400
        day_adj = f"-{days:.0f}d" if days >= 1 else ''
        return f"@{secs_to_hhmm(Device.zone_change_secs)}{day_adj}"

    if Gb.waze_status != WAZE_USED:
        return ''

    # Display the last arrival time since device is under min waze dist
    if Gb.Waze.is_status_USED is False:
        if FromZone.zone_dist_km < Gb.Waze.waze_min_distance:
            #return f"~{Device.sensors[ARRIVAL_TIME].replace('~', '')}"
            return '±5 min'

    # Display arrival time
    if FromZone.waze_time > 0:
        return secs_to_hhmm(FromZone.waze_time * 60 + time_now_secs())

    return ''

#...............................................................................abs
def _sensor_zone_info(Device, FromZone):
    if Device.isin_zone:
        if Device.wasnotin_zone:
            log_info_msg_HA(f"{Device.fname} Entered Zone: {zone_dname(Device.loc_data_zone)}")
        return f"@{Device.loc_data_zone_fname}"

    if Device.wasin_zone:
        log_info_msg_HA(f"{Device.fname} Exited Zone: {zone_dname(Device.sensors[ZONE])}")
        return km_to_um(FromZone.zone_dist_km)

    return ''

#--------------------------------------------------------------------------------
def post_results_message_to_event_log(Device, FromZone):
    '''
    Post the final tracking results to the Event Log and HA log file
    '''
    Device.last_update_msg_secs = time_now_secs()

    if Device.only_track_from_home:
        event_msg = f"Results > "
    else:
        event_msg = f"Results: From-{FromZone.from_zone_dname} > "

    if (FromZone.sensors[ARRIVAL_TIME]
            and (Device.isnotin_zone
                or (Device.isin_zone and FromZone.from_zone != Device.loc_data_zone))):
        event_msg += f"Arrive-{FromZone.sensors[ARRIVAL_TIME]}, "

    event_msg += f"NextUpdate-{FromZone.next_update_time}, "
    event_msg += f"Moved-{km_to_um(Device.loc_data_dist_moved_km)} "

    if Device.isin_zone:
        event_msg += ', '
    else:
        awayfrom_override_star = '*' if FromZone.dir_of_travel_awayfrom_override else ''
        event_msg += f"({FromZone.dir_of_travel}{awayfrom_override_star}), "

    if Device.is_statzone_timer_set and Device.is_tracked and Gb.is_statzone_used:
        event_msg += f"IntoStatZone-{secs_to_time(Device.statzone_timer)}, "

    if Device.dev_data_battery_level > 0 and FromZone is Device.FromZone_Home:
        event_msg += f"Battery-{Device.dev_data_battery_level}%, "

    event_msg += f"{'✓' if Device.went_3km else '×'}Went3km, "

    if Gb.log_debug_flag and FromZone.interval_method and Device.is_tracked:
        event_msg += f"Method-{FromZone.interval_method}, "

    if Gb.Waze.waze_status == WAZE_OUT_OF_RANGE:
        event_msg += f"WazeMsg-{Gb.Waze.range_msg(FromZone.zone_dist_km)}, "

    if (Device.mobapp_monitor_flag
            and secs_since(Device.mobapp_data_secs) > 3600):
        event_msg += f"MobAppLocated-{format_age(Device.mobapp_data_secs)}, "

    # event_msg += f"AppleAcct-{Device.PyiCloud.account_name}, "

    post_event(Device, event_msg[:-2])

    log_msg = ( f"RESULTS: From-{FromZone.from_zone_dname} > "
                f"MobApp-{Device.mobapp_data_state}, "
                f"iC3-{Device.loc_data_zone}, "
                f"Intrvl-{FromZone.interval_str}, "
                f"TravTime-{FromZone.last_travel_time}, "
                f"Dist-{format_dist_km(FromZone.zone_dist_km)}, "
                f"Arrival-{Device.sensors[ARRIVAL_TIME]}, "
                f"MaxDist-{format_dist_km(FromZone.max_dist_km)}, "
                f"Moved-{format_dist_km(Device.statzone_dist_moved_km)}, "
                f"Calc/WazeDist={FromZone.sensors[CALC_DISTANCE]}/{FromZone.sensors[WAZE_DISTANCE]}, "
                f"Dir-{FromZone.dir_of_travel}, "
                f"Batt-{Device.dev_data_battery_level}%, "
                f"NextUpdt-{FromZone.next_update_time}, "
                f"LastUpdt-{secs_to_time(Device.last_data_update_secs)}, "
                f"GPSAccur-{Device.loc_data_gps_accuracy}m, "
                f"LocAge-{format_age(Device.loc_data_secs)}, "
                f"OldThresh-{format_timer(Device.old_loc_threshold_secs)}, "
                f"LastEvLogMsg-{secs_to_time(Device.last_evlog_msg_secs)}, "
                f"Method-{FromZone.interval_method}")
    #log_info_msg(Device, log_msg)
    post_monitor_msg(Device, log_msg)

#--------------------------------------------------------------------------------
def post_zone_time_dist_event_msg(Device, FromZone):
    '''
    Post the mobapp state, ic3 zone, interval, travel time, distance msg to the
    Event Log
    '''

    if Device.mobapp_device_unavailable_flag:
        mobapp_state = 'Unavail...'
    elif Device.mobapp_monitor_flag is False:
        mobapp_state = 'NotUsed'
    else:
        mobapp_state = zone_dname(Device.mobapp_data_state)
    ic3_zone = zone_dname(Device.loc_data_zone)

    if Device.loc_data_zone == NOT_SET:
        interval_str = travel_time = 0
        distance = 0.0
    else:
        interval_str = FromZone.interval_str.split("(")[0]
        travel_time  = '' if FromZone.last_travel_time == '0 min' else FromZone.last_travel_time
        distance     = FromZone.zone_distance_str

    post_event(Device,
                f"{EVLOG_TIME_RECD}{mobapp_state},{ic3_zone},{interval_str},{travel_time},{distance}")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   iCloud FmF or iCloud authentication returned an error or no location
#   data is available. Update counter and device attributes and set
#   retry intervals based on current retry count.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def determine_interval_monitored_device_offline(Device):
    '''
    Handle errors where the device can not be or should not be updated with
    the current data. The update will be retried 4 times on a 15 sec interval.
    If the error continues, the interval will increased based on the retry
    count using the following cycles:
    '''
    if Device.is_online:
        Device.offline_secs = 0
        return False

    if (Device.is_offline and Device.offline_secs == 0):
        Device.offline_secs = Gb.this_update_secs

    age = secs_since(Device.loc_data_secs)
    if age > 3600:
        interval_secs = 3600        # 1-hr
    elif age > 1800:
        interval_secs = 1800        # 30-min
    elif age > 3600:
        interval_secs = 900         # 15-min
    elif age > 180:
        interval_secs = 300         # 5-min
    else:
        interval_secs = 180         # 3-min

    update_all_device_fm_zone_sensors_interval(Device, interval_secs)

    post_event(Device,
                f"{RED_X}Offline > "
                f"Since-{format_time_age(Device.loc_data_secs)}, "
                f"CheckNext-{Device.sensors[NEXT_UPDATE_TIME]}")

    return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   iCloud iCloud authentication returned an error or no location
#   data is available. Update counter and device attributes and set
#   retry intervals based on current retry count.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def determine_interval_after_error(Device, counter=OLD_LOCATION_CNT):
    '''
    Handle errors where the device can not be or should not be updated with
    the current data. The update will be retried 4 times on a 15 sec interval.
    If the error continues, the interval will increased based on the retry
    count using the following cycles:
        1-4   - 15 sec
        5-8   - 1 min
        9-12  - 5min
        13-16 - 15min
        >16   - 30min

    The following errors use this routine:
        - iCloud Authentication errors
        - FmF location data not available
        - Old location
        - Poor GPS Acuracy
    '''
    devicename = Device.devicename

    try:
        interval_secs, error_cnt, max_error_cnt = get_error_retry_interval(Device, counter)

        # Reset interval and counter if the max count was reached
        if counter == OLD_LOCATION_CNT and error_cnt > max_error_cnt:
            if (secs_since(Device.loc_data_secs) > 7200
                    or Device.no_location_data
                    or Device.is_offline):
                Device.reset_tracking_fields(interval_secs=5, max_error_cnt_reached=True)
                Device.max_error_cycle_cnt += 1
                interval_secs, error_cnt, max_error_cnt = get_error_retry_interval(Device, counter)

                post_event(Device,
                            f"iCloud Loc > Old > Tracking Reinitialized, "
                            f"Retry Cycle #{Device.max_error_cycle_cnt}, "
                            f"LastLocated-{format_time_age(Device.loc_data_secs)}, "
                            f"RetryAt-{Device.FromZone_Home.next_update_time}")
                return

        if (Device.is_offline and Device.offline_secs == 0):
            Device.offline_secs = Gb.this_update_secs

        # Adjust the interval based on the number of times the error retry table
        # has been cycled thru and started at the beginning again. Pause tracking
        # if cycled more than 8 times or 4 times and last location is over 2-days ago
        if Device.max_error_cycle_cnt > 8:
            Device.pause_tracking
        elif (Device.max_error_cycle_cnt > 4
                and mins_since(Device.last_update_loc_secs) > 2880):
            Device.pause_tracking
        elif Device.max_error_cycle_cnt > 2:
            interval_secs = interval_secs * int(Device.max_error_cycle_cnt/2)
            if interval_secs > Gb.max_interval_secs:
                interval_secs = Gb.max_interval_secs

        # Often, iCloud does not actually locate the device but just returns the last
        # location it has. A second call is needed after a 5-sec delay. This also
        # happens after a reauthentication. If so, do not display an error on the
        # first retry.
        last_interval_secs = Device.interval_secs
        interval_str       = format_timer(interval_secs)
        next_update_secs   = Gb.this_update_secs + interval_secs
        next_update_time   = secs_to_time(next_update_secs)
        Device.update_sensors_error_msg = Device.update_sensors_error_msg or Device.old_loc_msg

        update_all_device_fm_zone_sensors_interval(Device, interval_secs)

        Device.display_info_msg(Device.update_sensors_error_msg)

        event_msg = ''
        if counter == AUTH_ERROR_CNT:
            event_msg =(f"Results > RetryCounter-{Gb.icloud_acct_error_cnt}, "
                        f"RetryAt {next_update_time} ({interval_str})")

        elif Device.update_sensors_error_msg != '':
            event_msg =(f"{Device.update_sensors_error_msg}, "
                        f"RetryAt-{next_update_time} ({interval_str})")

            if interval_secs != last_interval_secs:
                event_msg = f"{EVLOG_ALERT}{event_msg}"
                if Device.no_location_data is False:
                    event_msg += f", Over-{format_timer(Device.old_loc_threshold_secs)}"

            Device.icloud_update_reason = "Newer Data is Available"

        if event_msg and Device.old_loc_cnt > 2:
            post_event(devicename, event_msg)
            log_info_msg(Device.devicename, f"Old Location/Other Error-{event_msg}")
            Device.display_info_msg()

    except Exception as err:
        log_exception(err)

#----------------------------------------------------------------------------
def get_error_retry_interval(Device, counter=OLD_LOCATION_CNT):
    '''
    Determine the interval value based on the error counter and current retry_count

    Return:
        interval value

    Called from:
        determine interval after error
        Device.post_location_data_accepted_rejected_msg

    '''
    try:
        interval_secs = 0

        if counter == OLD_LOCATION_CNT:
            error_cnt = Device.old_loc_cnt
            range_tbl = RETRY_INTERVAL_RANGE_1

        elif counter == AUTH_ERROR_CNT:
            error_cnt = Gb.icloud_acct_error_cnt
            range_tbl = RETRY_INTERVAL_RANGE_1

        elif counter == MOBAPP_REQUEST_LOC_CNT:
            error_cnt = Device.mobapp_request_loc_retry_cnt
            range_tbl = RETRY_INTERVAL_RANGE_2
        else:
            error_cnt = Device.old_loc_cnt
            range_tbl = RETRY_INTERVAL_RANGE_1
            interval_secs = 60

        max_error_cnt = int(list(range_tbl.keys())[-1])
        #if max_error_cnt < 25: max_error_cnt = 25

        # Retry in 5-secs if this is the first time retried
        if error_cnt <= 1:
            interval_secs = 5

        else:
            interval_list = [cnt_time for cnt, cnt_time in range_tbl.items() if cnt <= error_cnt]
            interval_secs = interval_list[-1]
            interval_secs = interval_secs * 60

            # Increase threshold when interval was updated (rc9) to try to get an acceptable location
            if Device.old_loc_threshold_secs < 300:
                Device.old_loc_threshold_secs += 60

    except Exception as err:
        log_exception(err)

    return interval_secs, error_cnt, max_error_cnt

#----------------------------------------------------------------------------
def update_all_device_fm_zone_sensors_interval(Device, interval_secs, FromZone=None):
    '''
    Update the Device and FromZone sensors with a new interval

    Parameters:
        Device - Device to be updated
        interval_secs - New polling interval_secs that determins the next_update_time
        FromZone - Update all FromZones or only this FromZone
    '''

    # if next_update_secs < Device.next_update_secs:
    if FromZone:
        Device.FromZone_NextToUpdate = FromZone

    _update_next_update_fields_and_sensors(Device, interval_secs)

    # Set all track from zone intervals. This prevents one zone from triggering an update
    # when the location data was poor.
    for _FromZone in Device.FromZones_by_zone.values():
        _update_next_update_fields_and_sensors(_FromZone, interval_secs)

        # Move Stationary Zone timer if it is set and expired so it does not trigger an update
        if Device.is_statzone_timer_reached and Gb.is_statzone_used:
            Device.statzone_timer = Device.next_update_secs

#----------------------------------------------------------------------------
def _update_next_update_fields_and_sensors(Device_or_FromZone, interval_secs):
    '''
    Update all of the internal and sensor fields for an interval value.

    Parameters:
        Device   - The Device or FromZone to update
                   None: Update a sensors dictionary to be merged with Device.sensors later
        interval - The new interval (secs)

    Return:
        sensors  - Dictionary of updated sensors that can be merged with the Device's
                    sensors.
    '''
    next_update_secs = Gb.this_update_secs + interval_secs
    next_update_time = secs_to_time(next_update_secs)

    sensors = {}

    if Device_or_FromZone:
        Device = Device_or_FromZone if Device_or_FromZone in Gb.Devices else Device_or_FromZone.Device
        data_source_ICLOUD = Device.is_data_source_ICLOUD
    else:
        data_source_ICLOUD = Gb.use_data_source_ICLOUD

    sensors[INTERVAL]             = format_timer(interval_secs)
    sensors[NEXT_UPDATE_DATETIME] = secs_to_datetime(next_update_secs)
    sensors[NEXT_UPDATE_TIME]     = next_update_time
    sensors[NEXT_UPDATE]          = next_update_time

    sensors[LAST_UPDATE_DATETIME] = datetime_now()
    sensors[LAST_UPDATE_TIME]     = time_now()
    sensors[LAST_UPDATE]          = time_now()

    if Device_or_FromZone is None:
        return sensors

    Device_or_FromZone.interval_secs    = interval_secs
    Device_or_FromZone.interval_str     = format_timer(interval_secs)
    Device_or_FromZone.next_update_secs = next_update_secs
    Device_or_FromZone.next_update_time = next_update_time
    Device_or_FromZone.last_update_secs = Gb.this_update_secs
    Device_or_FromZone.last_update_time = time_to_12hrtime(Gb.this_update_time)

    Device_or_FromZone.sensors.update(sensors)

    return sensors

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   TRACK FROM ZONE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def determine_TrackFrom_zone(Device):
    '''
    The FromZone tracking sensors have the results i.e., zone distance, interval, next update time
    and direction calculations, etc. The TrackFmZone sensor data that is closest to the Device's
    location are copied to the Device sensors if the Device is < 100km from home and 8km of the TrackFmZone
    or > 100km from Home
    '''
    if Device.only_track_from_home: return

    # track_fm_zone_radius is the distance from the trackFm zone before it's results are displayed
    # track_fm_zone_home_radius is the max home zone distance before the closest trackFm results are dsplayed

    Device.FromZone_TrackFrom = Device.TrackFromBaseZone
    for from_zone, FromZone in Device.FromZones_by_zone.items():
        if FromZone.next_update_secs <= Device.FromZone_TrackFrom.next_update_secs:
            # If within tfz tracking dist, display this tfz results
            # Then see if another trackFmZone is closer to the device
            if (FromZone.zone_dist_km <= Gb.tfz_tracking_max_distance
                    and FromZone.zone_dist_km < Device.FromZone_TrackFrom.zone_dist_km):
                Device.FromZone_TrackFrom = FromZone

    # If this is the last zone exited and going away from it, use Home instead
    if Device.FromZone_TrackFrom is not Device.TrackFromBaseZone:
        if Device.FromZone_TrackFrom.dir_of_travel == AWAY_FROM:
            Device.FromZone_TrackFrom = Device.TrackFromBaseZone

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   UPDATE DEVICE LOCATION & INFORMATION ATTRIBUTE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def _get_distance_data(Device, FromZone):
    """
    Determine the location of the device.
        Returns:
            - zone (current zone from lat & long)
                set to HOME if distance < home zone radius
            - dist_from_zone_km (mi or km)
            - dist_traveled (since last poll)
            - dir_of_travel (towards, away_from, stationary, in_zone,
                left_zone, near_home)
    """

    Device.display_info_msg(f"GetDistancesFrom-{FromZone.from_zone_dname}")

    if Device.no_location_data:
        post_event(Device, "No location data available, will retry")
        return (ERROR, {})


    calc_dist_from_zone_km = dist_from_zone_km   = FromZone.distance_km
    dist_from_zone_m       = dist_from_zone_km * 1000
    waze_dist_moved_km     = dist_moved_km       = Device.loc_data_dist_moved_km
    waze_dist_from_zone_km = calc_dist_from_zone_km
    waze_time_from_zone    = 0
    from_zone              = FromZone.from_zone

    # Device is in the from_zone so nothing to do
    if Device.loc_data_zone == from_zone:
        dir_of_travel = INZONE_HOME if Device.loc_data_zone == HOME else \
                        INZONE_STATZONE if Device.isin_statzone else \
                        INZONE
        Device.statzone_reset_timer
        Gb.Waze.waze_status = WAZE_PAUSED
        Gb.Waze.waze_close_to_zone_pause_flag = True
        distance_data = [VALID_DATA,
                        0.0,                        # dist_from_zone_km,
                        dist_from_zone_m,           # dist_from_zone_m,
                        0.0,                        # waze_dist_from_zone_km,
                        calc_dist_from_zone_km,     # calc_dist_from_zone_km,
                        0,                          # waze_time_from_zone,
                        dist_moved_km,              # dist moved
                        dir_of_travel,              # direction
                        False]                      # direction away_from override

        return distance_data

    #--------------------------------------------------------------------------------
    Gb.Waze.waze_status = WAZE_USED if Gb.Waze.distance_method_waze_flag else WAZE_NOT_USED
    waze_source_msg = ''
    if Gb.Waze.is_status_USED:
        # See if this location hasn't changed or is in the history db
        if Gb.WazeHist.is_historydb_USED and calc_dist_from_zone_km < Gb.WazeHist.max_distance:
            waze_status, waze_time_from_zone, waze_dist_from_zone_km, dist_moved_km, \
                hist_db_location_id, waze_source_msg = \
                Gb.Waze.get_history_time_distance(Device, FromZone, check_hist_db=True)
        else:
            hist_db_location_id = 0

        # Not in history db or history db is not used
        if hist_db_location_id == 0:
            waze_dist_from_zone_km = calc_dist_from_zone_km
            waze_time_from_zone    = 0

        if hist_db_location_id > 0:
            pass

        # Pause waze and set close to zone pause flag if nearing a track from zone
        elif (calc_dist_from_zone_km < 1
                and Device.loc_data_zone == from_zone
                and FromZone.is_going_towards):
            Gb.Waze.waze_status = WAZE_PAUSED
            Gb.Waze.waze_close_to_zone_pause_flag = True
            dist_from_zone_km = calc_dist_from_zone_km

        #Determine if Waze should be used based on calculated distance
        elif (calc_dist_from_zone_km > Gb.Waze.waze_max_distance
                or calc_dist_from_zone_km < Gb.Waze.waze_min_distance):
            Gb.Waze.waze_status = WAZE_OUT_OF_RANGE
            dist_from_zone_km = calc_dist_from_zone_km

    dist_from_zone_m = dist_from_zone_km * 1000

    # Get Waze travel_time & distance
    if Gb.Waze.is_status_USED:
        if hist_db_location_id == 0:
            waze_status, waze_time_from_zone, waze_dist_from_zone_km, waze_dist_moved_km \
                    = Gb.Waze.get_route_time_distance(Device, FromZone, check_hist_db=False)

            Gb.Waze.waze_status = waze_status

        # Don't reset data if poor gps, use the best we have
        dist_from_zone_m = dist_from_zone_km * 1000
        Device.display_info_msg( f"Finalizing-{FromZone.info_status_msg}")
        if Device.loc_data_zone == from_zone:
            dist_from_zone_km = 0.0
            dist_moved_km     = 0.0

        elif Gb.Waze.is_status_USED:
            dist_from_zone_km = waze_dist_from_zone_km
            dist_from_zone_m  = waze_dist_from_zone_km * 1000
            dist_moved_km     = waze_dist_moved_km
    else:
        waze_dist_from_zone_km = 0.0

    if waze_source_msg:
        post_event(Device, f"Waze Route Info > {waze_source_msg}")

    #--------------------------------------------------------------------------------
    # Get direction of travel

    dir_of_travel = UNKNOWN
    time_change_secs = 0    if waze_time_from_zone == 0 \
                            else int(waze_time_from_zone * 60) - int(FromZone.waze_time * 60)
    dist_from_zone_moved_m = int(dist_from_zone_m - FromZone.zone_dist_m)

    if Device.isin_zone:
        dir_of_travel = INZONE_HOME if Device.loc_data_zone == HOME else \
                        INZONE_STATZONE if Device.isin_statzone else \
                        INZONE

    elif Device.sensors[ZONE] == NOT_SET or FromZone.dir_of_travel == NOT_SET:
        dir_of_travel = UNKNOWN

    # Use last direction if did not move
    elif time_change_secs == 0 and dist_from_zone_moved_m == 0:
        dir_of_travel = Device.sensors[DIR_OF_TRAVEL]

    # Far Away if dist > 150km/100mi
    elif (calc_dist_from_zone_km > 150):
        dir_of_travel = FAR_AWAY

    # Towards if the last zone distance > than this zone distance
    elif time_change_secs < 0 or dist_from_zone_moved_m < 0:
        dir_of_travel = TOWARDS

    elif time_change_secs > 0 or dist_from_zone_moved_m > 0:
        dir_of_travel = AWAY_FROM

    else:
        #didn't move far enough to tell current direction
        dir_of_travel = Device.sensors[DIR_OF_TRAVEL]

    # Override AWAY_FROM if last 3 directions were TOWARDS and close to the zone
    if (dir_of_travel == AWAY_FROM
            and Device.went_3km
            and dist_from_zone_km < 2
            and FromZone.dir_of_travel_history[-3:] in \
                    ['TTT', 'TTt', 'TtT', 'tTT', 'Ttt', 'ttT']):
        dir_of_travel = TOWARDS
        dir_of_travel_awayfrom_override = True

    else:
        dir_of_travel_awayfrom_override = False


    if Device.loc_data_zone == NOT_HOME:
        if Gb.is_statzone_used is False:
            pass

        elif Device.statzone_timer == 0:
            Device.statzone_reset_timer

        # If moved more than stationary zone limit (~.06km(200ft)),
        # reset StatZone still timer
        # Use calc distance rather than waze for better accuracy
        elif (calc_dist_from_zone_km > Gb.statzone_min_dist_from_zone_km
                and Device.loc_data_dist_moved_km > Gb.statzone_dist_move_limit_km
                and Device.is_tracked):
            Device.statzone_reset_timer

            post_event(Device,
                        f"StatZone Timer Reset > "
                        f"NewTime-{secs_to_time(Device.statzone_timer)}, "
                        f"Moved-{km_to_um(Device.loc_data_dist_moved_km)}")

    distance_data = [VALID_DATA,
                    dist_from_zone_km,
                    dist_from_zone_m,
                    waze_dist_from_zone_km,
                    calc_dist_from_zone_km,
                    waze_time_from_zone,
                    dist_moved_km,
                    dir_of_travel,
                    dir_of_travel_awayfrom_override]

    return  distance_data

#--------------------------------------------------------------------------------
def _get_interval_for_error_retry_cnt(Device, counter=OLD_LOCATION_CNT, pause_control_flag=False):
    '''
    Get the interval time based on the retry_cnt.
    retry_cnt   =   poor_location_gps count (default)
                =   mobapp_request_loc_sent_retry_cnt
                =   retry pyicloud authorization count
    pause_control_flag = True if device will be paused (interval is negative)
                = False if just getting interfal and device will not be paused

    Returns     interval in minutes
                (interval is negative if device should be paused)

    Interval range table - key = retry_cnt, value = time in minutes
    - poor_location_gps cnt, icloud_authentication cnt (default):
        interval_range_1 = {0:.25, 4:1, 8:5,  12:30, 16:60, 20:120, 24:240}
    - request mobapp location retry cnt:
        interval_range_2 = {0:.5,  4:2, 8:30, 12:60, 16:120}

    '''
    if counter == OLD_LOCATION_CNT:
        retry_cnt = Device.old_loc_cnt
        range_tbl = RETRY_INTERVAL_RANGE_1

    elif counter == AUTH_ERROR_CNT:
        retry_cnt = Gb.icloud_acct_auth_error_cnt
        range_tbl = RETRY_INTERVAL_RANGE_1

    elif counter == MOBAPP_REQUEST_LOC_CNT:
        retry_cnt = Device.mobapp_request_loc_retry_cnt
        range_tbl = RETRY_INTERVAL_RANGE_2
    else:
        return 60

    interval_secs = .25
    for k, v in range_tbl.items():
        if k <= retry_cnt:
            interval_secs = v

    if pause_control_flag is False: interval_secs = abs(interval_secs)
    if Device.isin_statzone:
        interval_secs = min(interval_secs, Device.statzone_inzone_interval_secs)
    elif Device.isin_zone:
        interval_secs = min(interval_secs, Device.inzone_interval_secs)
    interval_secs = interval_secs * 60

    return interval_secs


# #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   MISCELLANEOUS SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def device_will_update_in_15secs(Device=None, update_in_secs=None, only_icloud_devices=False):
    '''
    Get the time (secs) until the next update for any device. This is used to determine
    when icloud data should be prefetched before it is needed.

    Parameter:
        = update_in_secs - Secs to be used in update test (default=15)
        = only_icloud_devices - True=Only check iCloud devices, False=All devices
    Return:
        = Device - The device that will be updated  within the update_in_secs time
        = None - No device will be updated in the update_in_secs time
    '''

    _Devices_not_to_check = [_Device
                    for _Device in Gb.Devices_by_devicename_tracked.values()
                    if (_Device is Device
                        or _Device.PyiCloud is None
                        or (only_icloud_devices and _Device.family_share_device is False)
                        or _Device.is_offline
                        or _Device.is_data_source_ICLOUD is False
                        or _Device.is_tracking_paused
                        or secs_since(_Device.loc_data_secs) > Gb.max_interval_secs
                        or secs_since(_Device.PyiCloud.last_refresh_secs) < 10)]

    _Devices_to_check = [_Device        for _Device in Gb.Devices_by_devicename_tracked.values()
                                        if _Device not in _Devices_not_to_check]

    update_in_secs = 15 if update_in_secs is None else update_in_secs
    for _Device in _Devices_to_check:    #Gb.Devices_by_devicename_tracked.values():

        if _Device.icloud_initial_locate_done is False:
            return _Device

        secs_to_next_update = secs_to(_Device.next_update_secs)

        if (secs_to_next_update < -15
                or secs_to_next_update > update_in_secs):
            continue

        # Corrected inzone_interval to next_update_secs (v3.1)
        # If going towards a TrackFmZone and the next update is in 15-secs or less and distance < 1km
        # and current location is older than 15-secs, prefetch data now
        # Changed to is_approaching_tracked_zone and added error_cnt check (rc9)
        if (_Device.is_approaching_tracked_zone
                and _Device.old_loc_cnt <= 4):
            _Device.old_loc_threshold_secs = 15
            return _Device

        if _Device.is_location_gps_good or _Device.old_loc_cnt > 6:
            continue

        # Updating the device in the next 10-secs
        _Device.display_info_msg(f"Requesting iCloud Location, Next Update in {format_timer(secs_to_next_update)} secs")
        return _Device

    return None

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   If a NearDevice is available, Make sure that it is not a circular reference by checking
#   the NearDevice's NearDevice. It should not point back to this Device. If so, don't use it.
#   If OK, use the results of another device that is nearby. It must be
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def used_near_device_results(Device, FromZone):
    if (Device.NearDevice is None
            or Device.isin_nonstatzone
            or Device.NearDevice.NearDevice is Device
            or FromZone.from_zone not in Device.NearDevice.FromZones_by_zone
            or Device.fixed_interval_secs != Device.NearDevice.fixed_interval_secs):
        Device.near_device_used = ''
        return False

    neardevice_fname      = Device.NearDevice.fname_devtype
    neardevice_fname_chk  = f"{NEAR_DEVICE_USEABLE_SYM}{neardevice_fname}"
    Device.dist_apart_msg = Device.dist_apart_msg.replace(NEAR_DEVICE_USEABLE_SYM, '')
    Device.dist_apart_msg = Device.dist_apart_msg.replace(neardevice_fname, neardevice_fname_chk)
    Device.near_device_used = ( f"{Device.NearDevice.fname_devtype} "
                                f"({m_to_um_ft(Device.near_device_distance)})")
    post_event(Device,
                f"Using Nearby Device Results > {Device.NearDevice.fname}, "
                f"Distance-{m_to_um_ft(Device.near_device_distance)}")

    copy_near_device_results(Device, FromZone)

    post_results_message_to_event_log(Device, FromZone,)
    post_zone_time_dist_event_msg(Device, FromZone)
    Device.display_info_msg(Device.format_info_msg, new_base_msg=True)

    return True

#--------------------------------------------------------------------------------
def copy_near_device_results(Device, FromZone):
    '''
    The Device is near the NearDevice for the FromZone zone results. Copy the NearDevice
    variables to Device since everything is the same.
    '''
    NearDevice   = Device.NearDevice
    from_zone    = FromZone.from_zone
    NearFromZone = Device.NearDevice.FromZones_by_zone[from_zone]

    Device.loc_data_zone       = NearDevice.loc_data_zone
    Device.zone_change_secs    = NearDevice.zone_change_secs

    FromZone.zone_dist_km      = NearFromZone.zone_dist_km
    FromZone.waze_dist_km      = NearFromZone.waze_dist_km
    FromZone.waze_time         = NearFromZone.waze_time
    FromZone.calc_dist_km      = NearFromZone.calc_dist_km
    FromZone.interval_method   = NearFromZone.interval_method
    FromZone.last_update_secs  = NearFromZone.last_update_secs
    FromZone.last_update_time  = NearFromZone.last_update_time
    FromZone.last_travel_time  = NearFromZone.last_travel_time
    FromZone.last_distance_km  = NearFromZone.last_distance_km
    FromZone.last_distance_str = NearFromZone.last_distance_str

    FromZone.dir_of_travel     = NearFromZone.dir_of_travel
    FromZone.dir_of_travel_awayfrom_override = \
            NearFromZone.dir_of_travel_awayfrom_override
    FromZone.update_dir_of_travel_history(NearFromZone.dir_of_travel)
    monitor_msg = (f"DirHist-{FromZone.dir_of_travel_history[-40:]}")
    post_monitor_msg(Device.devicename, monitor_msg)

    FromZone.sensors.update(NearFromZone.sensors)

    if Device.isin_statzone:
        interval_secs = 300 if Device.StatZone.is_small_statzone else \
                        Device.statzone_inzone_interval_secs
    elif Device.isin_zone:
        interval_secs = Device.inzone_interval_secs
    else:
        interval_secs = NearFromZone.interval_secs

    _update_next_update_fields_and_sensors(FromZone, interval_secs)

    Device.StatZone                = NearDevice.StatZone
    Device.statzone_timer          = NearDevice.statzone_timer
    Device.statzone_dist_moved_km  = NearDevice.statzone_dist_moved_km
    Device.mobapp_request_loc_sent_secs = Gb.this_update_secs

    log_data(f"{Device.data_source} - <{Device.devicename}> - {from_zone}", FromZone.sensors)

    return FromZone.sensors

#--------------------------------------------------------------------------------
def update_near_device_info(Device):
    '''
    Cycle through the devices and see if this device is in the same location as
    another device updated earlier in this 5-sec polling loop.

    Return: The closest device

    {devicename: [dist_m, gps_accuracy_factor, display_text]}
    dist_to_other_devices is updated in  Device.update_distance_to_other_devices
    '''
    if (len(Gb.Devices) == 1
            or len(Device.dist_to_other_devices) == 0
            or Gb.distance_between_device_flag is False):
        return

    Device.NearDevice           = None
    Device.near_device_distance = 0.0
    Device.near_device_checked_secs = time_now_secs()
    device_time = secs_to_hhmm(Device.dist_to_other_devices_secs)

    Device.dist_apart_msg = _build_dist_apart_msg(Device, Device.dist_to_other_devices)
    Device.dist_apart_msg2 = _build_dist_apart_msg(Device ,Device.dist_to_other_devices2)

    monitor_msg = ( f"Nearby Devices "
                    f"({LT}{m_to_um_ft(NEAR_DEVICE_DISTANCE, as_integer=True)}) > "
                    f"@{device_time}, "
                    f"{Device.dist_apart_msg.replace(f' ({device_time})', '')}")
    post_monitor_msg(Device.devicename, monitor_msg)

    # post_nearby_devices_msg()

    return

#--------------------------------------------------------------------------------
def set_dist_to_devices(post_event_msg=False):

        for devicename_from, Device_from in Gb.Devices_by_devicename.items():
            dist_to_devices_data = []

            try:
                for devicename_to, Device_to in Gb.Devices_by_devicename.items():
                    if (devicename_from == devicename_to
                            or Device_from.loc_data_secs == 0
                            or Device_to.loc_data_secs == 0):
                        continue

                    dist_to_m = Device_from.distance_m(Device_to.loc_data_latitude, Device_to.loc_data_longitude)
                    if dist_to_m == 0:
                        continue
                    loc_time_secs = min(Device_from.loc_data_secs, Device_to.loc_data_secs)

                    dist_to_device_data = [dist_to_m, Device_to, loc_time_secs]
                    dist_to_devices_data.append(dist_to_device_data)

            except Exception as err:
                # log_exception(err)
                pass

            try:
                # dist_to_devices_data.sort()
                Device_from.dist_to_devices_data = dist_to_devices_data
                Device_from.dist_to_devices_secs = Device_from.loc_data_secs

                if post_event_msg and dist_to_devices_data != []:
                    event_msg =(f"DistTo Devices > "
                                f"{format_dist_to_devices_msg(Device_from)}")

                    post_event(devicename_from, event_msg)

            except Exception as err:
                # log_exception(err)
                pass

#...............................................................................
def format_dist_to_devices_msg(Device, max_dist_to_m=HIGH_INTEGER, time=False, age=True):

    dist_msg = ''
    for dist_to_device_data in Device.dist_to_devices_data:
        dist_to_m, Device_to, loc_time_secs = dist_to_device_data
        if dist_to_m > max_dist_to_m:
            continue

        dist_msg += f", {Device_to.fname}--{m_to_um(dist_to_m)}"

        if abs(Device.dist_to_devices_secs - loc_time_secs) >= 5:
            if time and age:
                time_msg = format_time_age(loc_time_secs)
            elif time:
                time_msg = secs_to_hhmm(loc_time_secs)
            elif age:
                time_msg = format_secs_since(loc_time_secs)
            else:
                time_msg = None
            if time_msg:
                dist_msg += f" ({time_msg})"

    return dist_msg[1:]

#--------------------------------------------------------------------------------
def _build_dist_apart_msg(Device, dist_to_other_devices):

    dist_apart_msg = ''
    closest_device_distance = HIGH_INTEGER

    for devicename, dist_apart_data in dist_to_other_devices.items():
        _Device = Gb.Devices_by_devicename[devicename]
        if _Device is Device: continue

        dist_apart_m, min_gps_accuracy, loc_data_secs, display_text = dist_apart_data

        if (Device.device_type == WATCH or _Device.device_type == WATCH):
            useable_symbol = '×'

        elif dist_apart_m > NEAR_DEVICE_DISTANCE:
            useable_symbol = '×'
        elif min_gps_accuracy > NEAR_DEVICE_DISTANCE:
            useable_symbol = '±'
        elif instr(display_text, '+') or instr(display_text, '±'):      # old or gps accuracy issue
            useable_symbol = '×'
        elif _Device.NearDevice is Device:
            useable_symbol = '⌘'
        elif _check_near_device_circular_loop(_Device, Device) is False:
            useable_symbol = '⌘'
        elif Device.loc_data_zone != _Device.loc_data_zone:
            useable_symbol = '×'
        else:
            useable_symbol = NEAR_DEVICE_USEABLE_SYM

        #dist_apart_msg += f"{useable_symbol}{_Device.fname_devtype}-{display_text}, "
        dist_apart_msg += f"{useable_symbol}{_Device.fname}-{display_text}, "

        # The nearby devices can not point to each other and other criteria
        if (dist_apart_m < closest_device_distance
                and Device.is_tracked
                and _Device.is_tracked
                and useable_symbol == NEAR_DEVICE_USEABLE_SYM
                and _Device.FromZone_Home.interval_secs > 0
                and _Device.old_loc_cnt == 0
                and _Device.is_online):

            closest_device_distance = dist_apart_m
            Device.NearDevice = _Device
            Device.near_device_distance = dist_apart_m

    return dist_apart_msg

#--------------------------------------------------------------------------------
def _check_near_device_circular_loop(_Device, Device):
    '''
    Make sure the eligible nearbe device is not used by another device(s) that ends
    up referencing the Device being updated, creating a circular loop back to itself
    '''
    if _Device.NearDevice is None:
        return True

    next_Device_to_check = _Device.NearDevice
    checked_Devices = []
    near_devices_msg = f"{_Device.devicename}{RARROW}{next_Device_to_check.devicename}"
    log_debug_base_msg = f"Check Nearby Device-{_Device.devicename}"
    reason_msg = ''

    check_start_time_secs = time_now_secs()
    cnt = 0
    can_use_device = False

    while can_use_device is False:     #next_Device_to_check is not Device:
        # Make sure the loop will not hang
        cnt += 1
        if cnt > len(Gb.Devices):
            reason_msg = f"DeviceCnt-{cnt} > {len(Gb.Devices)}"
            break

        # Make sure the loop does not hang by only running 5-secs
        if secs_since(check_start_time_secs) > 5:
            reason_msg = 'Running more than 10-secs'
            break

        # If the next_NearDevice will loop back to a device that has already been checked,
        # do not use the _Device.NearDevice
        if next_Device_to_check.NearDevice in checked_Devices:
            near_devices_msg += f"{RARROW}{_Device.devicename}"
            reason_msg = 'Looped back to itself'
            break

        # If the next_NearDevice circles back to the _Device originally being checked,
        # do not use the _Device.NearDevice
        if next_Device_to_check.NearDevice is _Device:
            near_devices_msg += f"{RARROW}{_Device.devicename}"
            reason_msg = 'Looped back to start'
            break

        # If the NearDevice cycle ends, it's OK to use the current _Device
        if (next_Device_to_check is None
                or next_Device_to_check.NearDevice is None):
            near_devices_msg += f"{RARROW}None"
            can_use_device = True
            break

        near_devices_msg += f"{RARROW}{next_Device_to_check.NearDevice.devicename}"
        next_Device_to_check = next_Device_to_check.NearDevice
        checked_Devices.append(next_Device_to_check.NearDevice)
        log_msg = ( f"{log_debug_base_msg}, Checking, "
                    f"Cnt-{cnt}, "
                    f"Timer-{secs_since(check_start_time_secs)} secs, "
                    f"{near_devices_msg}")
        log_debug_msg(Device.devicename, log_msg)

    # The loop was broken out of
    can_cannot_msg = 'CanUse' if can_use_device else f"CanNotUse, {reason_msg}"
    log_msg = ( f"{log_debug_base_msg}, "
                f"{can_cannot_msg}, "
                f"Cnt-{cnt}, "
                f"Timer-{secs_since(check_start_time_secs)} secs, "
                f"{near_devices_msg}")
    log_debug_msg(Device.devicename, log_msg)
    return can_use_device
