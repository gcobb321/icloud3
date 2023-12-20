

from ..global_variables     import GlobalVariables as Gb
from ..const                import (DEVICE_TRACKER, NOTIFY,
                                    CRLF_DOT,
                                    NOT_SET, NOT_HOME, RARROW,
                                    NUMERIC, HIGH_INTEGER, HHMMSS_ZERO,
                                    ENTER_ZONE, EXIT_ZONE, IOS_TRIGGERS_EXIT,
                                    LATITUDE, LONGITUDE, TIMESTAMP_SECS, TIMESTAMP_TIME,
                                    TRIGGER, LAST_ZONE, ZONE,
                                    GPS_ACCURACY, VERT_ACCURACY, ALTITUDE,
                                    )

from ..helpers.common       import (instr, is_statzone, is_zone, zone_display_as, )
from ..helpers.messaging    import (post_event, post_monitor_msg,
                                    log_debug_msg, log_exception, log_error_msg, log_rawdata,
                                    _trace, _traceha, )
from ..helpers.time_util    import (secs_to_time, secs_since, format_time_age, format_age, format_age_hrs, )
from ..helpers.dist_util    import (format_dist_km, format_dist_m, )
from ..helpers              import entity_io
from ..support              import iosapp_interface
from ..support              import stationary_zone as statzone



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Check the iosapp device_tracker entity and last_update_trigger entity to
#   see if anything has changed and the icloud3 device_tracker entity should be
#   updated with the new location information.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def check_iosapp_state_trigger_change(Device):
    '''
    Example of device_trkr_attrs:
    {'device_tracker': 'home', 'source_type': <SourceType.GPS: 'gps'>, 'battery_level': 97, 'latitude': 27.726821899414062,
    'longitude': -80.39051823335237, 'gps_accuracy': 5, 'altitude': 3, 'speed': 0, 'vertical_accuracy': 3,
    'friendly_name': 'Lillian-iPhone-app', 'state': 'home', 'last_changed_secs': 1680103760,
    'last_changed_time': '11:29:20a', 'state_timestamp_secs': 1680103760.0, 'state_timestamp_time': '11:29:20a',
    'trigger': 'periodic', 'trigger_timestamp_secs': 1680103956.0, 'trigger_timestamp_time': '11:32:36a',
    'timestamp_secs': 1680103760.0, 'timestamp_time': '11:29:20a'}
    '''
    try:
        Device.iosapp_data_updated_flag = False
        Device.iosapp_data_change_reason = ''
        Device.iosapp_data_reject_reason = ''

        iosapp_data_state_not_set_flag = (Device.iosapp_data_state == NOT_SET)

        # Get the state data
        device_trkr_attrs = get_iosapp_device_trkr_entity_attrs(Device)
        if device_trkr_attrs is None:
            return

        iosapp_data_state      = device_trkr_attrs[DEVICE_TRACKER]
        iosapp_data_state_secs = device_trkr_attrs[f"state_{TIMESTAMP_SECS}"]
        iosapp_data_state_time = device_trkr_attrs[f"state_{TIMESTAMP_TIME}"]

        # Get the trigger data
        entity_id = Device.iosapp[TRIGGER]
        if entity_id:
            iosapp_data_trigger      = device_trkr_attrs["trigger"]                   = entity_io.get_state(entity_id)
            iosapp_data_trigger_secs = device_trkr_attrs[f"trigger_{TIMESTAMP_SECS}"] = entity_io.get_last_changed_time(entity_id)
            iosapp_data_trigger_time = device_trkr_attrs[f"trigger_{TIMESTAMP_TIME}"] = secs_to_time(iosapp_data_trigger_secs)
        else:
            iosapp_data_trigger      = device_trkr_attrs["trigger"]                   = 'None'
            iosapp_data_trigger_secs = device_trkr_attrs[f"trigger_{TIMESTAMP_SECS}"] = 0
            iosapp_data_trigger_time = device_trkr_attrs[f"trigger_{TIMESTAMP_TIME}"] = HHMMSS_ZERO


        # Get the latest of the state time or trigger time for the new data (rc9)
        if (iosapp_data_state_not_set_flag
                and iosapp_data_state_secs == 0
                and iosapp_data_trigger_secs == 0):
            Device.iosapp_data_trigger_secs = iosapp_data_secs = iosapp_data_trigger_secs = Gb.this_update_secs
            Device.iosapp_data_trigger_time = iosapp_data_time = iosapp_data_trigger_time = Gb.this_update_time
            iosapp_data_change_flag = True

        if iosapp_data_state_secs > iosapp_data_trigger_secs:
            iosapp_data_from = f" (State), Trig-{iosapp_data_trigger_time}"
            iosapp_data_secs = device_trkr_attrs[TIMESTAMP_SECS] = iosapp_data_state_secs
            iosapp_data_time = device_trkr_attrs[TIMESTAMP_TIME] = iosapp_data_state_time
        else:
            iosapp_data_from = f" (Trig), State-{iosapp_data_state_time}"
            iosapp_data_secs = device_trkr_attrs[TIMESTAMP_SECS] = iosapp_data_trigger_secs
            iosapp_data_time = device_trkr_attrs[TIMESTAMP_TIME] = iosapp_data_trigger_time

        # Build message if data has changed (rc9)
        change_msg = ''
        if Device.iosapp_data_trigger != iosapp_data_trigger:
            change_msg += f'Trigger ({Device.iosapp_data_trigger}{RARROW}{iosapp_data_trigger}, '

        if abs(Device.iosapp_data_secs - iosapp_data_secs) >= 5:
            change_msg += f'Time ({Device.iosapp_data_time}{RARROW}{iosapp_data_time}), '
        if iosapp_data_state == NOT_SET:
            change_msg += 'NotSet, '

        if  Gb.log_rawdata_flag and change_msg:
            log_rawdata(f"iOSApp Data - <{Device.devicename}> {change_msg}", device_trkr_attrs, log_rawdata_flag=True)

        iosapp_data_change_flag = (Device.iosapp_data_trigger != iosapp_data_trigger
                                or Device.iosapp_data_secs != iosapp_data_secs
                                or Device.iosapp_data_state == NOT_SET)

        # Force a reject if periodic and has not moved
        if iosapp_data_trigger == 'periodic':
            if (Device.is_dev_data_source_SET
                    and device_trkr_attrs[LATITUDE] == Device.iosapp_data_latitude
                    and device_trkr_attrs[LONGITUDE] == Device.iosapp_data_longitude):
                iosapp_data_change_flag = False

        # Update Device iosapp_data with the state & trigger location data
        # rc3 - Always try update, will check time in update_data fct
        # if iosapp_data_change_flag:
        update_iosapp_data_from_entity_attrs(Device, device_trkr_attrs)

        Device.iosapp_data_trigger = iosapp_data_trigger

        # Get the new trigger data if the last_changed_time has changed
        if ((iosapp_data_change_flag and iosapp_data_trigger_secs > Device.iosapp_data_trigger_secs)
                or iosapp_data_state_not_set_flag):
            Device.iosapp_data_trigger_secs = iosapp_data_trigger_secs
            Device.iosapp_data_trigger_time = iosapp_data_trigger_time

        # If enter/exit zone, save zone and enter/exit time
        if (Device.iosapp_data_trigger == EXIT_ZONE and Device.is_inzone):
            Device.iosapp_zone_exit_secs = iosapp_data_secs
            Device.iosapp_zone_exit_time = iosapp_data_state_time

            if Device.is_passthru_timer_set:
                Device.iosapp_zone_exit_zone = Device.passthru_zone

            elif (Device.iosapp_zone_enter_secs >= Device.loc_data_secs
                    or Device.is_in_statzone):
                Device.iosapp_zone_exit_zone = Device.loc_data_zone

            elif is_zone(Device.sensors[ZONE]):
                Device.iosapp_zone_exit_zone = Device.sensors[ZONE]

            elif is_zone(Device.iosapp_zone_enter_zone):
                Device.iosapp_zone_exit_zone = Device.iosapp_zone_enter_zone
            else:
                Device.iosapp_zone_exit_zone = Device.sensors[LAST_ZONE]

            if Device.iosapp_zone_exit_zone in Gb.Zones_by_zone:
                Device.iosapp_zone_exit_dist_m = \
                        Gb.Zones_by_zone[Device.iosapp_zone_exit_zone].distance_m(
                                Device.iosapp_data_latitude, Device.iosapp_data_longitude)
            else:
                Device.iosapp_zone_exit_zone = ''
                Device.iosapp_zone_exit_dist_m = -1

        if (Device.iosapp_data_trigger == ENTER_ZONE
                and Device.is_inzone_iosapp_state
                and iosapp_data_secs >= Device.iosapp_zone_enter_secs):
            Device.iosapp_zone_enter_secs = iosapp_data_secs
            Device.iosapp_zone_enter_time = iosapp_data_state_time
            Device.iosapp_zone_enter_zone = iosapp_data_state
            if iosapp_data_state in Gb.Zones_by_zone:
                Device.iosapp_zone_enter_dist_m = \
                        Gb.Zones_by_zone[iosapp_data_state].distance_m(
                                Device.iosapp_data_latitude, Device.iosapp_data_longitude)
            else:
                Device.iosapp_zone_enter_dist_m = -1

        iosapp_msg =(f"iOSApp Monitor > "
                    f"State-{Device.iosapp_data_state}@{Device.iosapp_data_state_time} (^state_age), "
                    f"Trigger-{iosapp_data_trigger}@{iosapp_data_trigger_time} (^trig_age), ")

        if iosapp_data_state_not_set_flag:
            Device.iosapp_data_change_reason = \
                Device.iosapp_data_trigger = f"Initial iOSApp Locate@{iosapp_data_time}"

        # Reject State and trigger changes older than the current data
        elif (Device.iosapp_data_secs <= Device.last_update_loc_secs):
            Device.iosapp_data_reject_reason = (f"Before Last Update "
                                                f"({secs_to_time(Device.iosapp_data_secs)} <= "
                                                f"{secs_to_time(Device.last_update_loc_secs)})")

        elif iosapp_data_change_flag is False:
            Device.iosapp_data_reject_reason = "Data has not changed"

        # Exit trigger and the trigger changed from last poll overrules trigger change time
        elif Device.iosapp_data_trigger == EXIT_ZONE:
            if Device.iosapp_data_secs > Device.located_secs_plus_5:
                Device.iosapp_data_change_reason = (f"{EXIT_ZONE}@{Device.iosapp_data_time} "
                                                    f"({zone_display_as(Device.iosapp_zone_exit_zone)}"
                                                    f"/{format_dist_m(Device.iosapp_zone_exit_dist_m)})")

            Device.iosapp_zone_exit_trigger_info = Device.iosapp_data_change_reason

        # Enter trigger and the trigger changed from last poll overrules trigger change time
        elif (Device.iosapp_data_trigger == ENTER_ZONE):
            Device.iosapp_data_change_reason = f"{ENTER_ZONE}@{Device.iosapp_data_time} "
            if Device.is_inzone_iosapp_state:
                Device.iosapp_data_change_reason +=(f"({zone_display_as(Device.iosapp_zone_enter_zone)}/"
                                                    f"{format_dist_m(Device.iosapp_zone_enter_dist_m)})")

            Device.iosapp_zone_enter_trigger_info = Device.iosapp_data_change_reason

        elif (Device.iosapp_data_trigger not in [ENTER_ZONE, EXIT_ZONE]
                and Device.iosapp_data_secs > Device.located_secs_plus_5
                and Device.iosapp_data_gps_accuracy > Gb.gps_accuracy_threshold):
            Device.iosapp_data_reject_reason = (f"Poor GPS Accuracy-{Device.iosapp_data_gps_accuracy}m "
                                                f"#{Device.old_loc_cnt}")

        # Discard StatZone entered if StatZone was created in the last 15-secs
        if (Device.iosapp_data_trigger == ENTER_ZONE
                and is_statzone(Device.iosapp_data_state)
                and Device.is_in_statzone
                and secs_since(Device.loc_data_secs <= 15)):
            Device.iosapp_data_reject_reason = "Enter into StatZone just created"

        # Discard if already in the zone
        elif (Device.iosapp_data_trigger == ENTER_ZONE
                and Device.iosapp_data_state == Device.loc_data_zone):
            Device.iosapp_data_reject_reason = "Enter Zone and already in zone"

        if Device.is_passthru_zone_delay_active:
            Device.iosapp_data_reject_reason = f"Passing thru zone, {Device.iosapp_data_trigger} discarded"

        # If Enter or Exit, reasons already set, continue
        if (Device.iosapp_data_change_reason
                or Device.iosapp_data_reject_reason):
            pass

        elif (Device.is_still_at_last_location
                and Device.is_next_update_time_reached is False):
            Device.iosapp_data_reject_reason = f"Still and Next Update not Reached"

        # trigger time is after last locate
        elif Device.iosapp_data_secs > Device.located_secs_plus_5:
            Device.iosapp_data_change_reason = (f"{Device.iosapp_data_trigger}@"
                                                f"{Device.iosapp_data_time}")
                                                # f"{Device.iosapp_data_trigger_time}")

        # No update needed if no location changes
        elif (Device.iosapp_data_state == Device.loc_data_zone      #Device.last_update_loc_zone
                and f'{Device.iosapp_data_latitude:.5f}'  == f'{Device.loc_data_latitude:.5f}'
                and f'{Device.iosapp_data_longitude:.5f}' == f'{Device.loc_data_longitude:.5f})'):
            Device.iosapp_data_reject_reason = "No Location Change"

        # iOSAPP location changed and State changed more than 5-secs after last locate
        elif Device.iosapp_data_secs > Device.located_secs_plus_5:
            Device.iosapp_data_change_reason = (f"Location Change")
            Device.iosapp_data_trigger = (f"Location Change, "
                    f"GPS-{Device.iosapp_data_fgps}")

        # Prevent duplicate update if State & Trigger changed at the same time
        # and state change was handled on last cycle
        elif (Device.iosapp_data_secs == Device.iosapp_data_secs
                or Device.iosapp_data_secs <= Device.located_secs_plus_5):
            Device.iosapp_data_reject_reason = "Already Processed"

        # Bypass if trigger contains ic3 date stamp suffix (@hhmmss)
        elif instr(Device.iosapp_data_trigger, '@'):
            Device.iosapp_data_reject_reason = "Trigger Already Processed"

        elif Device.iosapp_data_secs <= Device.located_secs_plus_5:
            Device.iosapp_data_reject_reason = "Trigger Before Last Locate"

        else:
            Device.iosapp_data_reject_reason = "Failed Update Tests"

        # If data time is very old, change it to it's age
        if secs_since(Device.iosapp_data_secs) >= 10800:
            Device.iosapp_data_time = device_trkr_attrs[TIMESTAMP_TIME] = \
                    format_age_hrs(Device.iosapp_data_secs)

        # Display iOSApp Monitor info message if the state or trigger changed
        if (Gb.this_update_time.endswith('00:00')
                or iosapp_msg != Device.last_iosapp_msg):
            _display_iosapp_msg(Device, iosapp_msg)

    except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
def _display_iosapp_msg(Device, iosapp_msg):
    try:
        Device.last_iosapp_msg = iosapp_msg
        iosapp_msg += (f"LastTrigger-{Device.sensors[TRIGGER]}, "
                        f"iOSAppData-{Device.iosapp_data_time}")

        if Device.iosapp_zone_enter_zone:
            iosapp_msg +=(f", LastZoneEnter-{Device.iosapp_zone_enter_zone}@"
                            f"{Device.iosapp_zone_enter_time}")
        if Device.iosapp_zone_exit_zone:
            iosapp_msg +=(f", LastZoneExit-{Device.iosapp_zone_exit_zone}@"
                            f"{Device.iosapp_zone_exit_time}")

        Device.iosapp_data_updated_flag = (Device.iosapp_data_reject_reason == "")
        iosapp_msg += (f", WillUpdate-{Device.iosapp_data_updated_flag}")

        if Device.iosapp_data_change_reason:
            iosapp_msg += (f"-{Device.iosapp_data_change_reason}")
        if Device.iosapp_data_reject_reason:
            iosapp_msg += (f"-{Device.iosapp_data_reject_reason}")
        iosapp_msg += (f", Located-{Device.loc_data_time} ({Device.dev_data_source}), "
                        f"GPS-{Device.iosapp_data_fgps}")

        iosapp_msg = iosapp_msg.replace("^trig_age", format_age(secs_since(Device.iosapp_data_trigger_secs)))
        iosapp_msg = iosapp_msg.replace("^state_age", format_age(secs_since(Device.iosapp_data_state_secs)))
        iosapp_msg += f", {Device.iosapp_zone_enter_trigger_info}"
        iosapp_msg += f", {Device.iosapp_zone_exit_trigger_info}"
        post_monitor_msg(Device.devicename, iosapp_msg)

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Update the device on a state or trigger change was recieved from the ios app
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''
If this Device is entering a zone also assigned to another device. The ios app
will move issue a Region Entered trigger and the state is the other devicename's
stat zone name. Create this device's stat zone at the current location to get the
zone tables in sync. Must do this before processing the state/trigger change or
this devicename will use this trigger to start a timer rather than moving it ineo
the stat zone.
'''
def reset_statzone_on_enter_exit_trigger(Device):
    try:
        if Device.iosapp_data_trigger in IOS_TRIGGERS_EXIT:
            if Device.is_in_statzone:
                statzone.exit_statzone(Device)

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#  Check the state of the iosapp to see if it is alive on regular intervals by
#  sending a location request at regular intervals. It will be considered dead/inactive
#  if there is no response with it's location.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def check_if_iosapp_is_alive(Device):
    try:
        if (Device.iosapp_monitor_flag is False
                or Device.is_offline
                or Device.iosapp[NOTIFY] == ''):
            return

        # Send a location request if the iosapp data is more than 'alive Interval'
        # and the check for request sent > 1 hr ago. Only send once an hour.
        if (secs_since(Device.iosapp_request_loc_first_secs) % Gb.iosapp_alive_interval_secs == 0
                and secs_since(Device.iosapp_data_secs) > Gb.iosapp_alive_interval_secs
                and secs_since(Device.iosapp_data_trigger_secs) > Gb.iosapp_alive_interval_secs):
            iosapp_interface.request_location(Device, is_alive_check=True)

            return

        # No activity, display Alert msg in Event Log
        if (Gb.this_update_time in ['00:00:00', '06:00:00', '12:00:00', '18:00:00']
                and secs_since(Device.iosapp_data_secs) > 21600):
            event_msg =(f"Last iOS App update from {Device.iosapp_device_trkr_entity_id_fname}"
                        f"—{format_time_age(Device.iosapp_data_secs)}")
            Device.display_info_msg( event_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def get_iosapp_device_trkr_entity_attrs(Device):
    '''
    Return the state and attributes of the ios app device tracker.
    The ic3 device tracker state and attributes are returned if
    the ios app data is not available or an error occurs.

    Return:
        device_trkr_attrs - iOSApp device tracker attrinutes if available
        None -  error or no data is available
    '''
    try:
        entity_id = Device.iosapp[DEVICE_TRACKER]
        device_trkr_attrs = {}
        device_trkr_attrs[DEVICE_TRACKER] =  entity_io.get_state(entity_id)

        device_trkr_attrs.update(entity_io.get_attributes(entity_id))
        device_trkr_attrs[f"state_{TIMESTAMP_SECS}"] = entity_io.get_last_changed_time(entity_id)
        device_trkr_attrs[f"state_{TIMESTAMP_TIME}"] = secs_to_time(device_trkr_attrs[f"state_{TIMESTAMP_SECS}"])

        if (device_trkr_attrs == {}
                or LATITUDE not in device_trkr_attrs):
            Device.iosapp_data_invalid_error_cnt += 1
            return None

        if GPS_ACCURACY in device_trkr_attrs:
            device_trkr_attrs[GPS_ACCURACY] = round(device_trkr_attrs[GPS_ACCURACY])
        if ALTITUDE in device_trkr_attrs:
            device_trkr_attrs[ALTITUDE] = round(device_trkr_attrs[ALTITUDE])
        if VERT_ACCURACY in device_trkr_attrs:
            device_trkr_attrs[VERT_ACCURACY] = round(device_trkr_attrs[VERT_ACCURACY])

        #log_rawdata(f"iOSApp Data - {entity_id}", device_trkr_attrs)

        return device_trkr_attrs

    except Exception as err:
        log_exception(err)
        return None

# -----------------------------------------------------------------
def update_iosapp_data_from_entity_attrs(Device, device_trkr_attrs):
    '''
    Update the iosapp data fields from the raw device_tracker entity attribute fields
    '''

    if (device_trkr_attrs is None
            or LATITUDE not in device_trkr_attrs):
        log_error_msg(Device.devicename, 'iOSApp Data Error > No data available')
        return

    iosapp_data_secs = device_trkr_attrs.get(TIMESTAMP_SECS, Device.iosapp_data_state_secs)
    iosapp_data_time = device_trkr_attrs.get(TIMESTAMP_TIME, Device.iosapp_data_state_time)
    gps_accuracy     = device_trkr_attrs.get(GPS_ACCURACY, 99999)

    if Device.iosapp_data_secs >= iosapp_data_secs or gps_accuracy > Gb.gps_accuracy_threshold:
        return

    log_rawdata(f"iOS App - {Device.devicename}", device_trkr_attrs)

    Device.iosapp_data_state             = device_trkr_attrs.get(DEVICE_TRACKER, NOT_SET)
    Device.iosapp_data_state_secs        = device_trkr_attrs.get(f"state_{TIMESTAMP_SECS}", 0)
    Device.iosapp_data_state_time        = device_trkr_attrs.get(f"state_{TIMESTAMP_TIME}", HHMMSS_ZERO)

    Device.iosapp_data_trigger           = device_trkr_attrs.get("trigger", NOT_SET)
    Device.iosapp_data_secs              = iosapp_data_secs
    Device.iosapp_data_time              = iosapp_data_time
    Device.iosapp_data_invalid_error_cnt = 0
    Device.iosapp_data_latitude          = device_trkr_attrs.get(LATITUDE, 0)
    Device.iosapp_data_longitude         = device_trkr_attrs.get(LONGITUDE, 0)
    Device.iosapp_data_gps_accuracy      = gps_accuracy
    Device.iosapp_data_vertical_accuracy = device_trkr_attrs.get(VERT_ACCURACY, 99999)
    Device.iosapp_data_altitude          = device_trkr_attrs.get(ALTITUDE, 0)

    if Device.FromZone_Home:
        home_dist = format_dist_km(Device.FromZone_Home.distance_km_iosapp)
    else:
        home_dist = ''

    monitor_msg = (f"UPDATED iOSApp > {Device.devicename}, {Device.iosapp_data_trigger}, "
                    f"{CRLF_DOT}Loc-{Device.iosapp_data_time}, "
                    f"Home-{home_dist}, "
                    f"{Device.iosapp_data_fgps}")
    if monitor_msg != Device.update_iosapp_data_monitor_msg:
        Device.update_iosapp_data_monitor_msg = monitor_msg
        post_monitor_msg(Device.devicename, monitor_msg)


#--------------------------------------------------------------------
def sync_iosapp_data_state_statzone(Device):
    '''
    Update the Device's iosapp_data_state value to sync it with the statzone
    the device is in. If the iosapp state is a statzone but ic3 has it set to
    not_home and the device is in a statzone, the iosapp state value may be
    out of sync because the state value changed byt the actual location did not
    change.

    This is done at the befinning of the process_update function in icloud3_main
    sot the iosapp state value will be correct when the Event Log is displayed

    Return:
        True - The iosapp_data_state was updated
        False - The iosapp_data_state was not updated

    '''
    if (Device.iosapp_monitor_flag is False
            or Gb.conf_data_source_IOSAPP is False
            or Device.iosapp.get(DEVICE_TRACKER) is None):
        return False

    iosapp_data_state = entity_io.get_state(Device.iosapp[DEVICE_TRACKER])

    if (is_statzone(iosapp_data_state)
            and is_statzone(Device.loc_data_zone)
            and Device.iosapp_data_state == NOT_HOME):
        Device.iosapp_data_state      = iosapp_data_state
        Device.iosapp_data_state_secs = Gb.this_update_secs
        Device.iosapp_data_state_time = Gb.this_update_time

        return True

    return False
