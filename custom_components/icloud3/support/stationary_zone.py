#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Methods to move the Stationary Zone to it's new location or back
#   to the base location based on the Update Control value.
#   Function that support Stationary Zones
#       Moving devices into a stationary zone
#       Exiting a stationary zone
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from ..global_variables  import GlobalVariables as Gb
from ..const             import (LATITUDE, LONGITUDE, STATZONE_BASE_RADIUS_M, )
from ..zone              import iCloud3_StationaryZone
from ..helpers.common    import (isbetween, is_statzone, format_gps, )
from ..helpers.messaging import (post_event, post_error_msg, post_monitor_msg,
                                log_debug_msg, log_exception, log_rawdata, _trace, _traceha, )
from ..helpers.time_util import (secs_to_time, datetime_now, format_time_age, )


#--------------------------------------------------------------------
def move_device_into_statzone(Device):
    '''
    The timer has expired, move the statzone to the device's location and move the device
    into it
    '''
    if Device.old_loc_poor_gps_cnt > 0 or Gb.is_statzone_used is False:
        return

    latitude  = Device.loc_data_latitude
    longitude = Device.loc_data_longitude

    # See if there is an existing zone this device can move into (real & statzones) when
    # the zone is selected
    available_zones = [Zone for Zone in Gb.Zones
                        if (Zone.passive is False
                                and Zone.distance_m(latitude, longitude) <= Zone.radius_m)]

    if available_zones != []:
        _clear_statzone_timer_distance(Device)
        return

    if _is_too_close_to_another_zone(Device): return

    # Get next available StatZone
    for StatZone in Gb.StatZones:
        if StatZone.is_at_base:
            break

    else:
        StatZone = create_StationaryZones_object()

    # Set new location, it will be updated when Device's attributes are updated in main routine
    StatZone.latitude  = latitude
    StatZone.longitude = longitude
    StatZone.radius_m  = Gb.statzone_radius_m
    StatZone.passive   = False

    still_since_secs = Device.statzone_timer - Gb.statzone_still_time_secs
    _clear_statzone_timer_distance(Device, create_statzone_flag=True)

    StatZone.away_attrs[LATITUDE]  = latitude
    StatZone.away_attrs[LONGITUDE] = longitude

    StatZone.write_ha_zone_state(StatZone.away_attrs)

    # Set Stationary Zone at new location
    Device.StatZone           = StatZone
    Device.loc_data_zone      = StatZone.zone
    Device.into_zone_datetime = datetime_now()
    Device.selected_zone_results = []

    event_msg =(f"Setting Up Stationary Zone ({StatZone.display_as}) > "
                f"StationarySince-{format_time_age(still_since_secs)}, "
                f"GPS-{format_gps(latitude, longitude, 0)}")
    post_event(Device.devicename, event_msg)

    return True

#--------------------------------------------------------------------
def create_StationaryZones_object():
    '''
    Create a new Stationary Zone
    '''

    statzone_id = str(len(Gb.StatZones) + 1)
    StatZone = iCloud3_StationaryZone(statzone_id)
    post_monitor_msg(f"ADDED StationaryZone > {StatZone.fname} ({StatZone.zone})")

    Gb.StatZones.append(StatZone)
    Gb.StatZones_by_zone[StatZone.zone] = StatZone

    Gb.Zones.append(StatZone)
    Gb.Zones_by_zone[StatZone.zone] = StatZone
    Gb.state_to_zone[StatZone.zone] = StatZone.zone

    return StatZone

#--------------------------------------------------------------------
def exit_all_statzones():
    '''
    Move all devices out of there stat zones. Move stat zone back to base and set the
    Devices loc_data_zone to not_home

    Parameter:
        Device - The Device (this device or another device) being moved out of this device's stat zone
    '''
    for Device in Gb.Devices:
        StatZone = Device.StatZone
        if StatZone and StatZone.isnot_at_base:
            move_statzone_to_base_location(StatZone, Device)

#--------------------------------------------------------------------
def exit_statzone(Device):
    '''
    Move a device out of this stat zone. Move stat zone back to base when there are no
    devces still in it. If there are other devices using it, reassign them to another
    statzone.

    Parameter:
        Device - The Device (this device or another device) being moved out of this device's stat zone
    '''
    StatZone = Device.StatZone
    Device.StatZone = None

    # Get all the devices still using this statzone
    Devices_in_statzone = [_Device  for _Device in Gb.Devices
                                    if _Device.StatZone is StatZone]

    # Move to base is no one else is using it
    if Devices_in_statzone == []:
        move_statzone_to_base_location(StatZone, Device)


#--------------------------------------------------------------------
def move_statzone_to_device_location(Device, latitude=None, longitude=None):
    '''
    The Device is currently in a stat zone but the Device's location may
    have been updated on the next locate. This might make it's stat zone
    further away than another device's stat zone. HA will then put this
    device (and Person) into the other device's stat zone.

    Move the Device's stat zone to the same location as the device to try
    to prevent this.
    '''
    StatZone = Device.StatZone
    if StatZone is None: return

    # Set new location, it will be updated when Device's attributes are updated in main routine
    latitude  = Device.loc_data_latitude  if latitude  is None else latitude
    longitude = Device.loc_data_longitude if longitude is None else longitude

    if _is_too_close_to_another_zone(Device): return

    StatZone.away_attrs[LATITUDE]  = StatZone.latitude  = latitude
    StatZone.away_attrs[LONGITUDE] = StatZone.longitude = longitude

    StatZone.radius_m = Gb.statzone_radius_m
    StatZone.passive  = False

    _clear_statzone_timer_distance(Device)

    StatZone.write_ha_zone_state(StatZone.away_attrs)

    Device.StatZone = StatZone
    Device.loc_data_zone = StatZone.zone

#--------------------------------------------------------------------
def move_statzone_to_base_location(StatZone, Device=None):
    ''' Move stationary zone back to base location '''
    # Set new location, it will be updated when Device's attributes are updated in main routine

    if StatZone.is_at_base: return

    StatZone.radius_m = STATZONE_BASE_RADIUS_M
    StatZone.passive  = True

    StatZone.write_ha_zone_state(StatZone.base_attrs)

    if Device:
        _clear_statzone_timer_distance(Device)
        event_msg = f"Exited Stationary Zone ({StatZone.display_as})"
        post_event(Device.devicename, event_msg)

#--------------------------------------------------------------------
def _is_too_close_to_another_zone(Device):
    # Too close if inside zone_radius + statzone_radius_gps_accuracy +25

    CloseZones = [Zone for Zone in Gb.Zones
                        if (Zone.passive is False
                                and Zone.distance_m(Device.loc_data_latitude, Device.loc_data_longitude) <= \
                                    (Zone.radius_m + Gb.statzone_radius_m + 25 + \
                                    Device.loc_data_gps_accuracy))]

    if CloseZones == []: return

    if is_statzone(CloseZones[0].zone):
        log_msg = f"{Device.devicename} > StatZone not created, too close to {CloseZones[0].display_as}"
        log_debug_msg(log_msg)
        # _clear_statzone_timer_distance(Device)

        return True
#--------------------------------------------------------------------
def _clear_statzone_timer_distance(Device, create_statzone_flag=False):
    Device.statzone_timer      = 0
    Device.statzone_moved_dist = 0
    Device.statzone_setup_secs = Gb.this_update_secs if create_statzone_flag else 0