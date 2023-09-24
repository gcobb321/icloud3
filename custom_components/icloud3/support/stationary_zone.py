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
from ..const             import (ZONE, LATITUDE, LONGITUDE, STATZONE_RADIUS_1M, HIGH_INTEGER, 
                                ENTER_ZONE, EXIT_ZONE, NEXT_UPDATE, INTERVAL, RARROW, )
from ..zone              import iCloud3_StationaryZone
from ..support           import determine_interval as det_interval
from ..support           import iosapp_interface
from ..helpers.common    import (isbetween, is_statzone, format_gps, )
from ..helpers.messaging import (post_event, post_error_msg, post_monitor_msg,
                                log_debug_msg, log_exception, log_rawdata, _trace, _traceha, )
from ..helpers.time_util import (secs_to_time, datetime_now, format_time_age, secs_since, )
from ..helpers           import entity_io


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

    # ''' Start of commented out code to test of moving device into a statzone while home
    # See if there is an existing zone this device can move into (real & statzones) when
    # the zone is selected
    available_zones = [Zone for Zone in Gb.Zones
                        if (Zone.passive is False
                            and Zone.distance_m(latitude, longitude) <= Zone.radius_m)]

    if available_zones != []:
        _clear_statzone_timer_distance(Device)
        return

    if _is_too_close_to_another_zone(Device): return
    # ''' End of commented out code to test of moving device into a statzone while home

    _ha_statzones = ha_statzones()

    # Cycle thru existing ic3 StatZones looking for one that can be recreated at a
    # new location. 
    for StatZone in Gb.StatZones:
        if StatZone.passive and StatZone.zone not in _ha_statzones:
            break

    else:
        StatZone = create_StationaryZones_object()

        event_msg = (f"Created StatZone > {StatZone.fname}, SetupBy-{Device.fname}")
        post_event(event_msg)

    # Set location, it will be updated when Device's attributes are updated in main routine
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

    iosapp_interface.request_location(Device)
    _trigger_monitored_device_update(StatZone, Device, ENTER_ZONE)

    return True

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

    removed_msg = "Exited"
    # If only  monitored devices left in the StatZone, take them out of the StatZone
    # so the zone will be removed
    if tracked_devices_in_statzone_count(StatZone) == 0:
        if monitored_devices_in_statzone_count(StatZone) > 0:
            _trigger_monitored_device_update(StatZone, Device, EXIT_ZONE)

        removed_msg += " & Removed"
        remove_statzone(StatZone, Device)

    event_msg =(f"StatZone {removed_msg} ({StatZone.display_as}) > "
                f"DevicesInStatZone-{devices_in_statzone_count(StatZone)}")

    post_event(Device.devicename, event_msg)

#--------------------------------------------------------------------
def kill_and_recreate_unuseable_statzone(Device):
    '''
    There are times when the iOSapp will exit a StatZone when it is still in it. 
    It exits and  the Devices distance is less than 100m, the iOSapp will not
    put the device back in it and seems to stop monitoring it. When this happens,
    create a new StatZone, move any devices in this one to the new one and delete
    it. 
    '''

    StatZone = Device.StatZone
    exit_statzone(Device)
    Devices_in_statzone = [_Device  for _Device in Gb.Devices
                                    if _Device.StatZone is StatZone]

    _StatZone = move_device_into_statzone(Device)
    for _Device in Devices_in_statzone:
        _Device.StatZone = _StatZone
        event_msg =(f"Reassign StatZone > {StatZone.display_as}{RARROW}"
                    f"{_StatZone.display_as}")
        post_event(_Device.devicename, event_msg)

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
def remove_statzone(StatZone, Device=None):
    ''' 
    Delete the stationary zone.  It will be removed from HA but the StatZone 
    object still exists in iCloud3 and will be recreated when a new one is
    needed. It is set to passive so it will not be selected.  It's remove
    time is set so it will not reuse the same StatZone in the next 5-minutes. 
    This gives the iOSapp time to remove it from its monitored zones. 
    '''

    if StatZone is None: return

    StatZone.radius_m = STATZONE_RADIUS_1M
    StatZone.passive  = True

    StatZone.remove_ha_zone()

    if Device:
        _clear_statzone_timer_distance(Device)
        event_msg = f"Exited Stationary Zone ({StatZone.display_as})"
        post_event(Device.devicename, event_msg)

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
    for _Device in Gb.Devices_by_devicename_monitored.values():
        if action == ENTER_ZONE:
            dist_m = _Device.distance_m(Device.loc_data_latitude, Device.loc_data_longitude)
            event_msg = f"Trigger > StatZone Created ({StatZone.display_as}) {dist_m=}"
            post_event(_Device.devicename, event_msg)

        elif action == EXIT_ZONE and _Device.StatZone is StatZone:
            # _Device.StatZone = None
            event_msg = f"Trigger > StatZone Removed ({StatZone.display_as})"
            post_event(_Device.devicename, event_msg)

        else:
            continue 

        Gb.force_icloud_update_flag = True
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
def _is_too_close_to_another_zone(Device):
    ''' Too close if inside zone_radius + statzone_radius_gps_accuracy +25 '''

    CloseZones = [Zone for Zone in Gb.Zones
                        if (Zone.passive is False
                                and Zone.distance_m(Device.loc_data_latitude, Device.loc_data_longitude) <= \
                                    (Zone.radius_m + Gb.statzone_radius_m + 25 + \
                                    Device.loc_data_gps_accuracy))]

    if CloseZones == []: return

    if is_statzone(CloseZones[0].zone):
        log_msg = f"{Device.devicename} > StatZone not created, too close to {CloseZones[0].display_as}"
        log_debug_msg(log_msg)

        return True
#--------------------------------------------------------------------
def _clear_statzone_timer_distance(Device, create_statzone_flag=False):
    Device.statzone_timer      = 0
    Device.statzone_moved_dist = 0
    Device.statzone_setup_secs = Gb.this_update_secs if create_statzone_flag else 0