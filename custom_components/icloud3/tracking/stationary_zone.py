#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Methods to move the Stationary Zone to it's new location or back
#   to the base location based on the Update Control value.
#   Function that support Stationary Zones
#       Moving devices into a stationary zone
#       Exiting a stationary zone
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
from ..global_variables import GlobalVariables as Gb
from ..const            import (HIGH_INTEGER, NOT_SET, RARROW,
                                ZONE, LATITUDE, LONGITUDE, GPS, RADIUS,
                                STATZONE_RADIUS_1M,
                                ENTER_ZONE, EXIT_ZONE, NEXT_UPDATE, INTERVAL, )

from ..utils.utils      import (isbetween, is_statzone, format_gps, zone_dname,
                                is_empty, isnot_empty, )
from ..utils.messaging  import (post_event, post_alert, post_error_msg, post_monitor_msg,
                                log_debug_msg, log_exception, log_data, _evlog, _log, )
from ..utils.time_util  import (datetime_now, )
from ..utils.dist_util  import (format_dist_m, gps_distance_km, )

from ..mobile_app       import mobapp_interface
from ..tracking         import determine_interval as det_interval
from ..zone             import iCloud3_StationaryZone

#--------------------------------------------------------------------
def move_into_statzone_if_timer_reached(Device):
    '''
    Check the Device's Stationary Zone expired timer and distance moved:
        Update the Device's Stat Zone distance moved
        Reset the timer if the Device has moved further than the distance limit
        Move Device into the Stat Zone if it has not moved further than the limit
    '''
    if Gb.is_statzone_used is False:
        return False

    calc_dist_last_poll_moved_km = gps_distance_km(Device.sensors[GPS], Device.loc_data_gps)
    Device.update_distance_moved(calc_dist_last_poll_moved_km)

    # See if moved less than the stationary zone movement limit
    # If updating via the Mobile App and the current state is stationary,
    # make sure it is kept in the stationary zone
    if Device.is_statzone_timer_reached is False or Device.is_location_old_or_gps_poor:
        return False

    if Device.is_statzone_move_limit_exceeded:
        Device.statzone_reset_timer

    # Monitored devices can move into a tracked zone but can not create on for itself
    elif Device.is_monitored: #beta 4/13b16
        pass

    elif (Device.isnotin_statzone
            or (is_statzone(Device.mobapp_data_state) and Device.loc_data_zone == NOT_SET)):
        move_device_into_statzone(Device)

    return True

#--------------------------------------------------------------------
def move_device_into_statzone(Device):
    '''
    The timer has expired, move the statzone to the device's location and move the device
    into it

    Return:
        True  - StatZone was set up and Device moved into it
        False - A new StatZone was not set up. The Device was close to another zone
                or another error occurred.
    '''
    if Device.old_loc_cnt > 0 or Gb.is_statzone_used is False:
        return False

    latitude  = Device.loc_data_latitude
    longitude = Device.loc_data_longitude

    # ''' Start of commented out code to test of moving device into a statzone while home

    # See if there is an existing zone this device can move into (real & statzones) when
    # the zone is selected. Real zones use radius, StatZones use radius*1.5
    available_zones = [Zone
                        for Zone in Gb.HAZones
                        if (Zone.passive is False
                            and Zone.distance_m(latitude, longitude) <= Zone.radius_m)]

    if available_zones != []:
        clear_statzone_timer_distance(Device)
        return False

    # ''' End of commented out code to test of moving device into a statzone while home

    # Cycle thru existing ic3 StatZones looking for one that can be recreated at a
    # new location.
    _ha_statzones = ha_statzones()
    for StatZone in Gb.StatZones:
        if StatZone.passive and StatZone.zone not in _ha_statzones:
            StatZone.__init__(StatZone.statzone_id)
            event_msg = f"Reusing Stationary Zone > {StatZone.fname_id}"
            break

    else:
        StatZone = create_StationaryZones_object()

        event_msg = f"Created Stationary Zone > {StatZone.fname_id}, SetupBy-{Device.fname}"
    post_event(event_msg)

    clear_statzone_timer_distance(Device, create_statzone_flag=True)

    StatZone.attrs[LATITUDE]  = latitude
    StatZone.attrs[LONGITUDE] = longitude
    StatZone.attrs[RADIUS]    = _get_statzone_radius(Device)

    StatZone.write_ha_zone_state(StatZone.attrs)

    # Set Stationary Zone at new location
    Device.StatZone           = StatZone
    Device.loc_data_zone      = StatZone.zone
    Device.into_zone_datetime = datetime_now()
    Device.selected_zone_results = []

    mobapp_interface.request_location(Device)

    # Move monitored devices into the new StatZone if they should be in it
    _trigger_monitored_device_update(StatZone, Device, ENTER_ZONE)

    return True

#....................................................................
def _within_radius(Zone):
    if Zone.isnot_statzone:
        return Zone.radius_m
    else:
        return Zone.radius_m * 1.5

#--------------------------------------------------------------------
def create_StationaryZones_object():
    '''
    Create a new Stationary Zone
    '''

    statzone_id = str(len(Gb.StatZones) + 1)

    StatZone = iCloud3_StationaryZone(statzone_id)

    event_msg = (f"ADDED StatZone > {StatZone.fname} ({StatZone.zone})")
    post_monitor_msg(event_msg)

    Gb.StatZones.append(StatZone)
    Gb.StatZones_by_zone[StatZone.zone] = StatZone

    Gb.Zones.append(StatZone)
    Gb.Zones_by_zone[StatZone.zone] = StatZone
    Gb.HAZones.append(StatZone)
    Gb.HAZones_by_zone[StatZone.zone] = StatZone
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
        if StatZone and StatZone.passive is False:
            remove_statzone(StatZone, Device)

#--------------------------------------------------------------------
def exit_statzone(Device):
    '''
    Move a device out of this stat zone. Delete the stat zone  if there are no
    other devces still in it.

    Parameter:
        Device - The Device exiting the stat zone
    '''

    StatZone = Device.StatZone
    Device.StatZone = None

    # If only  monitored devices left in the StatZone, take them out of the StatZone
    # so the zone will be removed
    if tracked_devices_in_statzone_count(StatZone) == 0:
        if monitored_devices_in_statzone_count(StatZone) > 0:
            _trigger_monitored_device_update(StatZone, Device, EXIT_ZONE)

        remove_statzone(StatZone, Device)

        post_event(Device,
                    f"Will Remove Stationary Zone > {StatZone.dname}, "
                    f"LastUsedBy-{Device.fname}")

#--------------------------------------------------------------------
def kill_and_recreate_unuseable_statzone(Device):
    '''
    There are times when the MobApp will exit a StatZone when it is still in it.
    It exits and the Devices distance is less than 100m, the MobApp will not
    put the device back in it and seems to stop monitoring it. When this happens,
    create a new StatZone, move any devices in this one to the new one and delete
    the old one.
    '''

    StatZone = Device.StatZone
    if StatZone is None: return

    exit_statzone(Device)
    move_device_into_statzone(Device)

    _StatZone = Device.StatZone
    if _StatZone is None: return

    Devices_in_statzone = [_Device  for _Device in Gb.Devices
                                    if _Device.StatZone is StatZone]

    for _Device in Devices_in_statzone:
        _Device.StatZone = _StatZone
        post_event(_Device,
                    f"Reassigned Stationary Zone > {StatZone.dname}{RARROW}"
                    f"{_StatZone.dname}")

    remove_statzone(StatZone)

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

    clear_statzone_timer_distance(Device)

    StatZone.attrs[LATITUDE]  = latitude
    StatZone.attrs[LONGITUDE] = longitude
    StatZone.attrs[RADIUS]    = _get_statzone_radius(Device)
    StatZone.write_ha_zone_state(StatZone.attrs)

    Device.StatZone      = StatZone
    Device.loc_data_zone = StatZone.zone

#--------------------------------------------------------------------
def remove_statzone(StatZone, Device=None):
    '''
    Delete the stationary zone.  It will be removed from HA but the StatZone
    object still exists in iCloud3 and will be recreated when a new one is
    needed. It is set to passive so it will not be selected.  It's remove
    time is set so it will not reuse the same StatZone in the next 5-minutes.
    This gives the MobApp time to remove it from its monitored zones.
    '''

    if StatZone is None or StatZone.passive:
        return

    StatZone.write_ha_zone_state(StatZone.passive_attrs)

    if StatZone not in Gb.StatZones_to_delete:
        Gb.StatZones_to_delete.append(StatZone)

    if Device:
        clear_statzone_timer_distance(Device)
        post_event(Device,
                    f"Exited Stationary Zone > {StatZone.dname}, "
                    f"DevicesRemaining-{devices_in_statzone_count(StatZone)}")

#--------------------------------------------------------------------
def ha_statzones():
    '''
    Return a list of StatZones in the yaml zone collection updated when
    iCloud3 Add our remove a StatZone
    '''
    Gb.hass.services.call(ZONE, "reload")
    return [zone.replace('zone.', '')   for zone in Gb.hass.data['zone_entity_ids']
                                        if zone.startswith('zone.ic3_stationary_')]

#--------------------------------------------------------------------
def _trigger_monitored_device_update(StatZone, Device, action):
    '''
    When a StatZone is being created, see if any monitored devices are close enough to
    the device creating it and, if so, trigger a locate update so they will move into
    it.

    When the last device in a StatZone exited from it and there are monitored devices in
    it, move all monitored devices in that StatZone out of it. Then trigger an update
    to reset the monitored device as Away
    '''
    for _Device in Gb.Devices_by_devicename_monitored.values():
        event_msg = ""
        if action == ENTER_ZONE and _Device.StatZone is None:
            dist_apart_m = _Device.distance_m(Device.loc_data_latitude, Device.loc_data_longitude)
            if dist_apart_m <= Gb.statzone_radius_m:
                post_event(_Device, f"Trigger > Enter New Stationary Zone > {StatZone.dname}")

        elif action == EXIT_ZONE and _Device.StatZone is StatZone:
            _Device.StatZone = None
            post_event(_Device, f"Trigger > Exit Removed Stationary Zone > {StatZone.dname}")

        else:
            continue

        if event_msg:
            _Device.icloud_force_update_flag = True
            det_interval.update_all_device_fm_zone_sensors_interval(_Device, 5)
            _Device.icloud_update_reason = event_msg
            _Device.write_ha_sensors_state([NEXT_UPDATE, INTERVAL])

#--------------------------------------------------------------------
def devices_in_statzone_count(StatZone):

    return len([_Device for _Device in Gb.Devices
                        if _Device.StatZone is StatZone])

#--------------------------------------------------------------------
def tracked_devices_in_statzone_count(StatZone):

    return len([_Device for _Device in Gb.Devices_by_devicename_tracked.values()
                        if _Device.StatZone is StatZone])

#--------------------------------------------------------------------
def monitored_devices_in_statzone_count(StatZone):

    return len([_Device for _Device in Gb.Devices_by_devicename_monitored.values()
                        if _Device.StatZone is StatZone])

#--------------------------------------------------------------------
def _get_statzone_radius(Device):
    '''
    If a Device's location is very close to another zone when it is going into a StatZone,
    create a small StatZone instead of one with a 100m radius. It is close if the
    distance to the zone's edge is less than the 1/2 of the CloseZoneRadius + gps accuracy.
    The StatZone small radius  is CloseZoneRadius/4
    '''

    CloseZones = [Zone
                for Zone in Gb.HAZones
                if (Zone.passive is False
                    and Zone.distance_m(Device.loc_data_latitude, Device.loc_data_longitude) <= \
                        (Zone.radius_m*1.5 + Device.loc_data_gps_accuracy))]

    if is_empty(CloseZones):
        return Gb.statzone_radius_m

    CloseZone = CloseZones[0]

    statzone_radius = int(CloseZone.radius_m/2)
    edge_dist_m = (CloseZone.distance_m(Device.loc_data_latitude, Device.loc_data_longitude) -
                        CloseZone.radius_m)

    post_event(Device, (f"Close to {CloseZone.dname} ({format_dist_m(edge_dist_m)}), "
                        f"Small StatZone created ({format_dist_m(statzone_radius)})"))

    return statzone_radius

#--------------------------------------------------------------------
def clear_statzone_timer_distance(Device, create_statzone_flag=False):

    Device.statzone_timer      = 0
    Device.statzone_moved_dist = 0.0
    Device.statzone_setup_secs = Gb.this_update_secs if create_statzone_flag else 0