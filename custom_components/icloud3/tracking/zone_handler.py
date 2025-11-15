#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   This module handles zone processing for the the icloud3_main module that
#   is used to:
#       - determine if a device is in a zone
#       - select the zone and assigning it to a device
#       - display all zone information in the Event Log
#       - utilities for determining if a device can use a zone
#       - requesting icloud updates for devices not using the mobile app
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


from ..global_variables import GlobalVariables as Gb
from ..const            import (HOME, NOT_HOME, NOT_SET, HIGH_INTEGER, RARROW,
                                GPS, HOME_DISTANCE, ENTER_ZONE, EXIT_ZONE, ZONE, LATITUDE,
                                EVLOG_ALERT, )

from ..utils.file_io    import (file_size, file_exists, set_write_permission, )
from ..utils.utils      import (instr, is_zone, is_statzone, isnot_statzone, isnot_zone, zone_dname,
                                list_to_str, list_add, list_del, )
from ..utils.messaging  import (post_event, post_alert, post_error_msg, post_monitor_msg,
                                log_info_msg, log_exception,
                                _evlog, _log, )
from ..utils.time_util import (time_now_secs, secs_to_time,  secs_to, secs_since, mins_since, time_now,
                                datetime_now, secs_to_datetime, )
from ..utils.dist_util  import (gps_distance_km, format_dist_km, format_dist_m,
                                km_to_um, m_to_um, )

from ..tracking         import stationary_zone as statzone
from ..tracking         import determine_interval as det_interval
from ..utils            import entity_io
from ..zone             import iCloud3_Zone

#--------------------------------------------------------------------
import homeassistant.util.dt as dt_util
from homeassistant.core     import callback

#--------------------------------------------------------------------
# zone_data constants - Used in the select_zone function
ZD_DIST_M = 0
ZD_ZONE   = 1
ZD_NAME   = 2
ZD_RADIUS = 3
ZD_DNAME  = 4
ZD_CNT    = 5



#------------------------------------------------------------------------------
#
#   DETERMINE THE ZONE THE DEVICE IS CURRENTLY IN
#
#------------------------------------------------------------------------------
def update_current_zone(Device, display_zone_msg=True):

    '''
    Get current zone of the device based on the location

    Parameters:
        selected_zone_results - The zone may have already been selected. If so, this list
                        is the results from a previous _select_zone
        display_zone_msg - True if the msg should be posted to the Event Log

    Returns:
        Zone    Zone object
        zone    zone name or not_home if not in a zone

    NOTE: This is the same code as (active_zone/async_active_zone) in zone.py
    but inserted here to use zone table loaded at startup rather than
    calling hass on all polls
    '''

    # Zone selected may have been done when determing if the device just entered a zone
    # during the passthru check. If so, use it and then reset it
    if Device.selected_zone_results == []:
        ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list = \
            select_zone(Device)
    else:
        ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list = \
            Device.selected_zone_results
        Device.selected_zone_results = []

    if zone_selected == 'unknown':
        return ZoneSelected, zone_selected

    if ZoneSelected is None:
        ZoneSelected         = Gb.Zones_by_zone[NOT_HOME]
        zone_selected        = NOT_HOME
        zone_selected_dist_m = 0

    # In a zone but if not in a track from zone and was in a Stationary Zone,
    # reset the stationary zone
    elif Device.isin_statzone and isnot_statzone(zone_selected):
        statzone.exit_statzone(Device)


    # Get distance between zone selected and current zone to see if they overlap.
    # If so, keep the current zone
    if (is_zone(zone_selected)
            and is_same_or_overlapping_zone(Device.loc_data_zone, zone_selected)):
        zone_selected = Device.loc_data_zone
        ZoneSelected  = Gb.Zones_by_zone[Device.loc_data_zone]

    # The zone changed
    elif Device.loc_data_zone != zone_selected:
        # See if any device without the mobapp was in this zone. If so, request a
        # location update since it was running on the inzone timer instead of
        # exit triggers from the Mobile App
        if (Gb.device_not_monitoring_mobapp
                and zone_selected == NOT_HOME
                and Device.loc_data_zone != NOT_HOME):
            request_update_devices_no_mobapp_same_zone_on_exit(Device)

        Device.loc_data_zone        = zone_selected
        Device.zone_change_secs     = time_now_secs()
        Device.zone_change_datetime = datetime_now()

        # The zone changed, update the enter/exit zone times if the
        # Device does not use the Mobile App
        if zone_selected == NOT_HOME:
            if (Device.mobapp_monitor_flag is False
                    or Device.mobapp_zone_exit_secs == 0):
                Device.mobapp_zone_exit_secs = time_now_secs()
                Device.mobapp_zone_exit_time = time_now()

        else:
            if (Device.mobapp_monitor_flag is False
                    or Device.mobapp_zone_enter_secs == 0):
                Device.mobapp_zone_enter_secs = time_now_secs()
                Device.mobapp_zone_enter_time = time_now()

    if display_zone_msg:
        post_zone_selected_msg(Device, ZoneSelected, zone_selected,
                                        zone_selected_dist_m, zones_distance_list)

    return ZoneSelected, zone_selected

#--------------------------------------------------------------------
def select_zone(Device, latitude=None, longitude=None):
    '''
    Cycle thru the zones and see if the Device is in a zone (or it's stationary zone).

    Parameters:
        latitude, longitude - Override the normally used Device.loc_data_lat/long when
                        calculating the zone distance from the current location
    Return:
        ZoneSelected - Zone selected object or None
        zone_selected - zone entity name
        zone_selected_distance_m - distance to the zone (meters)
        zones_distance_list - list of zone info [distance_m|zoneName-distance]
    '''

    if latitude is None:
        latitude  = Device.loc_data_latitude
        longitude = Device.loc_data_longitude
        gps_accuracy_adj = int(Device.loc_data_gps_accuracy / 2)

    # [distance from zone, Zone, zone_name, redius, display_as]
    zone_data_selected = [HIGH_INTEGER, None, '', HIGH_INTEGER, '', 1]

    # Exit if no location data is available
    if Device.no_location_data:
        ZoneSelected         = Gb.Zones_by_zone['unknown']
        zone_selected        = 'unknown'
        zone_selected_dist_m = 0
        zones_msg            = f"Zone > Unknown, GPS-{Device.loc_data_fgps}"
        post_event(Device, zones_msg)
        return ZoneSelected, zone_selected, 0, []

    # Verify that the statzone was not left without an exit trigger. If so, move this device out of it.
    if (Device.isin_statzone
            and Device.StatZone.distance_m(latitude, longitude) > Device.StatZone.radius_m):
        statzone.exit_statzone(Device)

    zones = [Zone.zone for Zone in Gb.HAZones if (Zone.passive is False)]
    Zones = [Gb.Zones_by_zone[zone] for zone in set(zones)]
    zones_data = [[Zone.distance_m(latitude, longitude), Zone, Zone.zone,
                    Zone.radius_m, Zone.dname]
                            for Zone in Zones
                            if (Zone.passive is False)]

    # Select all the zones the device is in
    inzone_zones = [zone_data   for zone_data in zones_data
                                if zone_data[ZD_DIST_M] <= zone_data[ZD_RADIUS] + gps_accuracy_adj]

    for zone_data in inzone_zones:
        if zone_data[ZD_RADIUS] <= zone_data_selected[ZD_RADIUS]:
            zone_data_selected = zone_data

    ZoneSelected  = zone_data_selected[ZD_ZONE]
    zone_selected = zone_data_selected[ZD_NAME]
    zone_selected_dist_m = zone_data_selected[ZD_DIST_M]

    # Selected a statzone
    if zone_selected in Gb.StatZones_by_zone:
        Device.StatZone = Gb.StatZones_by_zone[zone_selected]

    # In a zone and the mobapp enter zone info was not set, set it now
    if (zone_selected != Device.mobapp_zone_enter_zone
            and is_zone(zone_selected) and isnot_zone(Device.mobapp_zone_enter_zone)):
        Device.mobapp_zone_enter_secs = Gb.this_update_secs
        Device.mobapp_zone_enter_time = Gb.this_update_time
        Device.mobapp_zone_enter_zone = zone_selected

    # Build an item for each zone (dist-from-zone|zone_name|display_name-##km)
    zones_distance_list = \
        [(f"{int(zone_data[ZD_DIST_M]):08}|{zone_data[ZD_NAME]}|{zone_data[ZD_DIST_M]}")
                for zone_data in zones_data if zone_data[ZD_NAME] != zone_selected]
    zones_distance_list.sort()

    return ZoneSelected, zone_selected, zone_selected_dist_m, zones_distance_list

#--------------------------------------------------------------------
def post_zone_selected_msg(Device, ZoneSelected, zone_selected,
                                zone_selected_dist_m, zones_distance_list):

    device_zones      = [_Device.loc_data_zone for _Device in Gb.Devices]
    zones_cnt_by_zone = {_zone:device_zones.count(_zone) for _zone in set(device_zones)}

    # Format the Zone Selected Msg (ZoneName (#))
    zone_selected_msg = zone_dname(zone_selected)
    if zone_selected in zones_cnt_by_zone:
        zone_selected_msg += f"({zones_cnt_by_zone[zone_selected]})"
    if ZoneSelected.radius_m > 0:
        zone_selected_msg += f"-{m_to_um(zone_selected_dist_m)}"

    # Format distance msg
    zones_dist_msg = ''
    for zone_distance_list in zones_distance_list:
        zdl_items  = zone_distance_list.split('|')
        _zone      = zdl_items[1]
        _zone_dist_m = float(zdl_items[2])

        zones_dist_msg += ( f"{zone_dname(_zone)}"
                            f"-{m_to_um(_zone_dist_m)}")
        zones_dist_msg += ", "

    gps_accuracy_msg = ''
    if zone_selected_dist_m > ZoneSelected.radius_m:
        gps_accuracy_msg = (f"AccuracyAdjustment-"
                            f"{int(Device.loc_data_gps_accuracy / 2)}m, ")

    # Format distance and count msg
    zones_cnt_msg = ''
    for _zone, cnt in zones_cnt_by_zone.items():
        if zone_dname(_zone) in zones_dist_msg:
            zones_dist_msg = zones_dist_msg.replace(
                    zone_dname(_zone), f"{zone_dname(_zone)}({cnt})")
        elif _zone != zone_selected:
            zones_dist_msg += f"{zone_dname(_zone)}({cnt}), "
            zones_cnt_msg  += f"{zone_dname(_zone)}({cnt}), "

    zones_dist_msg = zones_dist_msg.replace('──', 'NotSet')
    zones_cnt_msg  = zones_cnt_msg.replace('──', 'NotSet')

    if is_zone(zone_selected) and isnot_statzone(zone_selected):
        post_monitor_msg(Device.devicename, f"Zone Distance > {zones_dist_msg}")
        zones_dist_msg = ''
    else:
        zones_cnt_msg = ''

    zones_msg =(f"Zone > "
                f"{zone_selected_msg} > "
                f"{zones_dist_msg}"
                f"{zones_cnt_msg}"
                f"{gps_accuracy_msg}"
                f"GPS-{Device.loc_data_fgps}")

    if zone_selected == Device.log_zone:
        zones_msg += ' (Logged)'

    post_event(Device, zones_msg)

    if (zones_cnt_msg
        and Device.loc_data_zone != Device.sensors[ZONE]
        and NOT_SET not in zones_cnt_by_zone):
            for _Device in Gb.Devices:
                if Device is not _Device:
                    post_event(_Device, f"Zone-Device Counts > {zones_cnt_msg}")

#--------------------------------------------------------------------
def closest_zone(latitude, longitude):
    '''
    Get the  closest zone to this location

    Return:
        - Zone, Zone entity, Zone display name, distance (m)
    '''
    try:
        zones_data = [[Zone.distance_m(latitude, longitude), Zone.zone]
                            for Zone in Gb.HAZones
                            if Zone.radius_m > 1]
        zones_data.sort()
        zone_dist_m, zone = zones_data[0]
        Zone = Gb.Zones_by_zone.get(zone)

        return Zone, zone, Zone.dname, zone_dist_m

    except Exception as err:
        log_exception(err)
        return None, 'unknown', 'Unknown', 0

#--------------------------------------------------------------------
def is_same_or_overlapping_zone(zone1, zone2):
    '''
    zone1 and zone2 overlap if their distance between centers is less than 2m
    '''
    try:
        if zone1 == zone2:
            return True

        if (isnot_zone(zone1)
                or zone1 not in Gb.Zones_by_zone or zone2 not in Gb.Zones_by_zone
                or zone1 == 'not_set' or zone2 == 'not_set'
                or zone1 == "" or zone2 == ""):
            return False

        Zone1 = Gb.Zones_by_zone[zone1]
        Zone2 = Gb.Zones_by_zone[zone2]

        zone_dist_m = Zone1.distance_m(Zone2.latitude, Zone2.longitude)

        return (zone_dist_m <= 2)

    except Exception as err:
        #log_exception(err)
        return False

#--------------------------------------------------------------------
def is_outside_zone_no_exit(Device, zone, trigger, latitude, longitude):
    '''
    If the device is outside of the zone and less than the zone radius + gps_acuracy_threshold
    and no Exit Trigger was received, it has probably wandered due to
    GPS errors. If so, discard the poll and try again later

    Updates:    Set the Device.outside_no_exit_trigger_flag
                Increase the old_location_poor_gps count when this innitially occurs
    Return:     Reason message
    '''
    if Device.mobapp_monitor_flag is False:
        return ''

    trigger = Device.trigger if trigger == '' else trigger
    if (instr(trigger, ENTER_ZONE)
            or Device.sensor_zone == NOT_SET
            or zone not in Gb.HAZones_by_zone
            or Device.icloud_initial_locate_done is False):
        Device.outside_no_exit_trigger_flag = False
        return ''

    Zone           = Gb.Zones_by_zone[zone]
    dist_fm_zone_m = Zone.distance_m(latitude, longitude)
    zone_radius_m  = Zone.radius_m
    zone_radius_accuracy_m = zone_radius_m + Gb.gps_accuracy_threshold

    info_msg = ''
    if (dist_fm_zone_m > zone_radius_m
            and Device.got_exit_trigger_flag is False
            and Zone.is_statzone is False):
        if (dist_fm_zone_m < zone_radius_accuracy_m
                and Device.outside_no_exit_trigger_flag == False):
            Device.outside_no_exit_trigger_flag = True
            Device.old_loc_cnt += 1

            info_msg = ("Outside of Zone without MobApp `Exit Zone` Trigger, "
                        f"Keeping in Zone-{Zone.dname} > ")
        else:
            Device.got_exit_trigger_flag = True
            info_msg = ("Outside of Zone without MobApp `Exit Zone` Trigger "
                        f"but outside threshold, Exiting Zone-{Zone.dname} > ")

        info_msg += (f"Distance-{format_dist_m(dist_fm_zone_m)}, "
                    f"KeepInZoneThreshold-{format_dist_m(zone_radius_m)} "
                    f"to {format_dist_m(zone_radius_accuracy_m)}, "
                    f"Located-{Device.loc_data_time_age}")

    if Device.got_exit_trigger_flag:
        Device.outside_no_exit_trigger_flag = False

    return info_msg

#------------------------------------------------------------------------------
def log_zone_enter_exit_activity(Device):
    '''
    An entry can be written to the 'zone-log-[year]-[device-[zone].csv' file.
    This file shows when a device entered & exited a zone, the time the device was in
    the zone, the distance to Home, etc. It can be imported into a spreadsheet and used
    at year end for expense calculations.
    '''
    # Start - Uncomment the following for testing
    # Also Uncomment icloud3_main UPDATE TRACKED DEVICES routine ~line 280 to run this
    # if Gb.this_update_time.endswith('0:00') or Gb.this_update_time.endswith('5:00'):
    #     Device.mobapp_zone_exit_secs = time_now_secs()
    #     Device.mobapp_zone_exit_time = time_now()
    #     Device.last_zone = HOME
    #     pass
    # elif 'none' in Device.log_zones:
    #     return
    # End - Uncomment the following for testing

    # Start - Comment the following for testing
    if ('none' in Device.log_zones
            or Device.log_zone == Device.loc_data_zone
            or (Device.log_zone == '' and Device.loc_data_zone not in Device.log_zones)):
        return
    # End - Comment the following for testing

    if Device.log_zone == '':
        Device.log_zone = Device.loc_data_zone
        Device.log_zone_enter_secs = Gb.this_update_secs
        post_event(Device, f"Log Zone Activity > Logging Started, {zone_dname(Device.log_zone)}")
        return

    # Must be in the zone for at least 4-minutes
    if mins_since(Device.log_zone_enter_secs) < 4:
        return

    # try:
    #     Gb.hass.async_add_executor_job(write_log_zone_recd, Device)

    # except Exception as err:
    #     # log_exception(err)

    write_log_zone_recd(Device)

    if Device.loc_data_zone in Device.log_zones:
        Device.log_zone = Device.loc_data_zone
        Device.log_zone_enter_secs = Gb.this_update_secs
    else:
        Device.log_zone = ''
        Device.log_zone_enter_secs = 0

#------------------------------------------------------------------------------
def write_log_zone_recd(Device):
    '''
    Write the record to the .csv file. Add a header record if the file is new
    '''

    if Device.log_zone == NOT_SET:
        return

    csv_filename = (f"zone-log-{dt_util.now().strftime('%Y')}-"
                f"{Device.log_zones_filename}.csv")
    csv_filename = Gb.hass.config.path(csv_filename)
    new_file_flag = not file_exists(csv_filename)

    with open(csv_filename, 'a', encoding='utf8') as f:
        if new_file_flag:
            set_write_permission(csv_filename)
            header = "Date,Zone Enter Time,Zone Exit Time,Time (Mins),Time (Hrs),Distance (Home),Zone,Device"
            f.write(header)

        recd = (f"\n"
                f"{datetime_now()[:10]},"
                f"{secs_to_datetime(Device.log_zone_enter_secs)},"
                f"{secs_to_datetime(Gb.this_update_secs)},"
                f"{mins_since(Device.log_zone_enter_secs):.0f},"
                f"{mins_since(Device.log_zone_enter_secs)/60:.2f},"
                f"{Device.sensors[HOME_DISTANCE]:.2f},"
                f"{Device.log_zone},"
                f"{Device.devicename}")
        f.write(recd)
        recd=f"{Device.devicename} CLEARED"

        post_event(Device,  f"Log Zone Activity > Logging Ended, "
                            f"{zone_dname(Device.log_zone)}, "
                            f"Time-{mins_since(Device.log_zone_enter_secs)/60:.2f}h")

#------------------------------------------------------------------------------
def request_update_devices_no_mobapp_same_zone_on_exit(Device):
    '''
    The Device is exiting a zone. Check all other Devices that were in the same
    zone that do not have the mobapp installed and set the next update time to
    5-seconds to see if that device also exited instead of waiting for the other
    devices inZone interval time to be reached.

    Check the next update time to make sure it has not already been updated when
    the device without the Mobile App is with several devices that left the zone.
    '''
    devices_to_update = [_Device
                    for _Device in Gb.Devices_by_devicename_tracked.values()
                    if (Device is not _Device
                        and _Device.is_data_source_MOBAPP is False
                        and _Device.loc_data_zone == Device.loc_data_zone
                        and secs_to(_Device.FromZone_Home.next_update_secs) > 60)]

    if devices_to_update == []:
        return

    for _Device in devices_to_update:
        _Device.icloud_force_update_flag = True
        _Device.trigger = 'Check Zone Exit'
        _Device.check_zone_exit_secs = time_now_secs()
        det_interval.update_all_device_fm_zone_sensors_interval(_Device, 15)
        post_event(_Device, f"Trigger > Check Zone Exit, GeneratedBy-{Device.fname}")


#------------------------------------------------------------------------------
@callback
def ha_added_zone_entity_id(event):
    """Add zone entity ID."""

    zone_entity_id = event.data['entity_id']
    zone           = zone_entity_id.replace('zone.', '')
    ha_zone_attrs  = entity_io.ha_zone_attrs(zone_entity_id)

    try:
        if ha_zone_attrs and LATITUDE in ha_zone_attrs:
            Zone = iCloud3_Zone(zone)

            if isnot_statzone(zone):
                post_event( f"HA Zone Added > Zone-{Zone.dname}/{Zone.zone} "
                            f"(r{Zone.radius_m}m)")

    except Exception as err:
        log_exception(err)
        pass

#------------------------------------------------------------------------------
@callback
def ha_removed_zone_entity_id(event):
    """Remove zone entity ID."""
    try:
        zone_entity_id = event.data['entity_id']
        zone = zone_entity_id.replace('zone.', '')

        if (zone == HOME
                or zone not in Gb.HAZones_by_zone
                or Gb.start_icloud3_inprocess_flag):
            return

        Zone = Gb.HAZones_by_zone[zone]

        Zone.status = -1
        Gb.HAZones_by_zone_deleted[zone] = Zone
        Gb.Zones   = list_del(Gb.Zones, Zone)
        Gb.HAZones = list_del(Gb.HAZones, Zone)
        if zone in Gb.Zones_by_zone:   del Gb.Zones_by_zone[zone]
        if zone in Gb.HAZones_by_zone: del Gb.HAZones_by_zone[zone]

        # if isnot_statzone(zone):
        #     if zone       in Gb.zones_dname: del Gb.zones_dname[zone]
        #     if Zone.fname in Gb.zones_dname: del Gb.zones_dname[Zone.fname]
        #     if Zone.name  in Gb.zones_dname: del Gb.zones_dname[Zone.name]
        #     if Zone.title in Gb.zones_dname: del Gb.zones_dname[Zone.title]

        for Device in Gb. Devices:
            Device.remove_zone_from_settings(zone)

        post_event( f"HA Zone Deleted > Zone-{Zone.dname}/{zone}")

    except Exception as err:
        log_exception(err)
        Gb.restart_icloud3_request_flag = True
        post_event( f"Zone Deleted Error > Zone-{Zone.dname},"
                    f"An error was encountered deleting the zone, "
                    f"iCloud3 will be restarted")
        return
