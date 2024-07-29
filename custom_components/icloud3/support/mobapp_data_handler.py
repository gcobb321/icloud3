

from ..global_variables     import GlobalVariables as Gb
from ..const                import (DEVICE_TRACKER, NOTIFY,
                                    CRLF_DOT, EVLOG_ALERT, RARROW, LT,
                                    NOT_SET, NOT_HOME, RARROW,
                                    NUMERIC, HIGH_INTEGER, HHMMSS_ZERO,
                                    ENTER_ZONE, EXIT_ZONE, MOBAPP_TRIGGERS_EXIT,
                                    LATITUDE, LONGITUDE, TIMESTAMP_SECS, TIMESTAMP_TIME,
                                    TRIGGER, LAST_ZONE, ZONE,
                                    GPS_ACCURACY, VERT_ACCURACY, ALTITUDE,
                                    CONF_IC3_DEVICENAME,
                                    )

from ..helpers.common       import (instr, is_statzone, is_zone, zone_dname, )
from ..helpers.messaging    import (post_event, post_monitor_msg, more_info,
                                    log_debug_msg, log_exception, log_error_msg, log_rawdata,
                                    _trace, _traceha, )
from ..helpers.time_util    import (secs_to_time, secs_since, format_time_age, format_age,  )
from ..helpers.dist_util    import (format_dist_km, format_dist_m, )
from ..helpers              import entity_io
from ..support              import mobapp_interface
from ..support              import stationary_zone as statzone
from ..support              import zone_handler



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Check the mobapp device_tracker entity and last_update_trigger entity to
#   see if anything has changed and the icloud3 device_tracker entity should be
#   updated with the new location information.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def check_mobapp_state_trigger_change(Device):
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
        Device.mobapp_data_updated_flag = False
        Device.mobapp_data_change_reason = ''
        Device.mobapp_data_reject_reason = ''

        mobapp_data_state_not_set_flag = (Device.mobapp_data_state == NOT_SET)

        # Get the state data
        device_trkr_attrs = get_mobapp_device_trkr_entity_attrs(Device)
        if device_trkr_attrs is None:
            return

        mobapp_data_state      = device_trkr_attrs[DEVICE_TRACKER]
        mobapp_data_state_secs = device_trkr_attrs[f"state_{TIMESTAMP_SECS}"]
        mobapp_data_state_time = device_trkr_attrs[f"state_{TIMESTAMP_TIME}"]
        mobapp_data_state_time = device_trkr_attrs[f"state_{TIMESTAMP_TIME}"]

        # State change will create enter/exit Zone trigger
        if Device.mobapp_data_state != mobapp_data_state:
            mobapp_data_trigger      = device_trkr_attrs["trigger"] = EXIT_ZONE \
                            if mobapp_data_state == NOT_HOME else     ENTER_ZONE
            mobapp_data_trigger_secs = device_trkr_attrs[f"trigger_{TIMESTAMP_SECS}"] = mobapp_data_state_secs
            mobapp_data_trigger_time = device_trkr_attrs[f"trigger_{TIMESTAMP_TIME}"] = mobapp_data_state_time

            event_msg =(f"MobApp State Changed > "
                        f"{zone_dname(Device.mobapp_data_state)}{RARROW}{zone_dname(mobapp_data_state)}")
            post_event(Device, event_msg)

        # Get the trigger data
        elif Device.mobapp[TRIGGER]:
            entity_id = Device.mobapp[TRIGGER]
            mobapp_data_trigger      = device_trkr_attrs["trigger"]                   = entity_io.get_state(entity_id)
            mobapp_data_trigger_secs = device_trkr_attrs[f"trigger_{TIMESTAMP_SECS}"] = entity_io.get_last_changed_time(entity_id)
            mobapp_data_trigger_time = device_trkr_attrs[f"trigger_{TIMESTAMP_TIME}"] = secs_to_time(mobapp_data_trigger_secs)
        else:
            mobapp_data_trigger      = device_trkr_attrs["trigger"]                   = 'None'
            mobapp_data_trigger_secs = device_trkr_attrs[f"trigger_{TIMESTAMP_SECS}"] = 0
            mobapp_data_trigger_time = device_trkr_attrs[f"trigger_{TIMESTAMP_TIME}"] = HHMMSS_ZERO

        # Get the latest of the state time or trigger time for the new data (rc9)
        if (mobapp_data_state_not_set_flag
                and mobapp_data_state_secs == 0
                and mobapp_data_trigger_secs == 0):
            Device.mobapp_data_trigger_secs = mobapp_data_secs = mobapp_data_trigger_secs = Gb.this_update_secs
            Device.mobapp_data_trigger_time = mobapp_data_time = mobapp_data_trigger_time = Gb.this_update_time
            mobapp_data_change_flag = True

        if mobapp_data_state_secs >= mobapp_data_trigger_secs:
            mobapp_data_from = f" (State), Trig-{mobapp_data_trigger_time}"
            mobapp_data_secs = device_trkr_attrs[TIMESTAMP_SECS] = mobapp_data_state_secs
            mobapp_data_time = device_trkr_attrs[TIMESTAMP_TIME] = mobapp_data_state_time
        else:
            mobapp_data_from = f" (Trig), State-{mobapp_data_state_time}"
            mobapp_data_secs = device_trkr_attrs[TIMESTAMP_SECS] = mobapp_data_trigger_secs
            mobapp_data_time = device_trkr_attrs[TIMESTAMP_TIME] = mobapp_data_trigger_time

        # Build message if data has changed (rc9)
        change_msg = ''
        if Device.mobapp_data_trigger != mobapp_data_trigger:
            change_msg += f'Trigger ({Device.mobapp_data_trigger}{RARROW}{mobapp_data_trigger}, '

        if abs(Device.mobapp_data_secs - mobapp_data_secs) >= 5:
            change_msg += f'Time ({Device.mobapp_data_time}{RARROW}{mobapp_data_time}), '
        if mobapp_data_state == NOT_SET:
            change_msg += 'NotSet, '

        if  Gb.log_rawdata_flag and change_msg:
            log_rawdata(f"MobApp Data - <{Device.devicename}> {change_msg}", device_trkr_attrs, log_rawdata_flag=True)

        mobapp_data_change_flag = (Device.mobapp_data_trigger != mobapp_data_trigger
                                or Device.mobapp_data_secs != mobapp_data_secs
                                or Device.mobapp_data_state == NOT_SET)

        # Force a reject if periodic and has not moved
        if mobapp_data_trigger == 'periodic':
            if (Device.is_dev_data_source_SET
                    and device_trkr_attrs[LATITUDE] == Device.mobapp_data_latitude
                    and device_trkr_attrs[LONGITUDE] == Device.mobapp_data_longitude):
                mobapp_data_change_flag = False

        # Update Device mobapp_data with the state & trigger location data
        # rc3 - Always try update, will check time in update_data fct
        update_mobapp_data_from_entity_attrs(Device, device_trkr_attrs)

        Device.mobapp_data_trigger = mobapp_data_trigger

        # Get the new trigger data if the last_changed_time has changed
        if ((mobapp_data_change_flag and mobapp_data_trigger_secs > Device.mobapp_data_trigger_secs)
                or mobapp_data_state_not_set_flag):
            Device.mobapp_data_trigger_secs = mobapp_data_trigger_secs
            Device.mobapp_data_trigger_time = mobapp_data_trigger_time

        # ---------------------------------------------
        # Entering a zone and this state time > last zone enter time
        # We are entering a new zone from not_home or going from one zone to another
        if (Device.mobapp_data_trigger == ENTER_ZONE
                and Device.isin_zone_mobapp_state
                and mobapp_data_secs >= Device.mobapp_zone_enter_secs):
            Device.mobapp_zone_enter_secs = mobapp_data_secs
            Device.mobapp_zone_enter_time = mobapp_data_state_time
            Device.mobapp_zone_enter_zone = mobapp_data_state
            if mobapp_data_state in Gb.HAZones_by_zone:
                Device.mobapp_zone_enter_dist_m = \
                        Gb.Zones_by_zone[mobapp_data_state].distance_m(
                                Device.mobapp_data_latitude, Device.mobapp_data_longitude)
            else:
                Device.mobapp_zone_enter_dist_m = 0

        # ---------------------------------------------
        # Exiting a zone when we are in a zone
        elif (Device.mobapp_data_trigger == EXIT_ZONE
                and Device.isin_zone):
                # and Device.isnotin_zone):
            Device.got_exit_trigger_flag = True
            Device.mobapp_zone_exit_secs = mobapp_data_secs
            Device.mobapp_zone_exit_time = mobapp_data_state_time

            if Device.is_passthru_timer_set:
                Device.mobapp_zone_exit_zone = Device.passthru_zone

            elif (Device.mobapp_zone_enter_secs >= Device.loc_data_secs
                    or Device.isin_statzone):
                Device.mobapp_zone_exit_zone = Device.loc_data_zone

            elif is_zone(Device.sensors[ZONE]):
                Device.mobapp_zone_exit_zone = Device.sensors[ZONE]

            elif is_zone(Device.mobapp_zone_enter_zone):
                Device.mobapp_zone_exit_zone = Device.mobapp_zone_enter_zone
            else:
                Device.mobapp_zone_exit_zone = Device.sensors[LAST_ZONE]

            if Device.mobapp_zone_exit_zone in Gb.HAZones_by_zone:
                Device.mobapp_zone_exit_dist_m = \
                        Gb.Zones_by_zone[Device.mobapp_zone_exit_zone].distance_m(
                                Device.mobapp_data_latitude, Device.mobapp_data_longitude)
            else:
                Device.mobapp_zone_exit_zone   = 'unknown'
                Device.mobapp_zone_exit_dist_m = 0

        # ---------------------------------------------
        mobapp_msg =(f"MobApp Monitor > "
                    f"State-{Device.mobapp_data_state}@{Device.mobapp_data_state_time} (^state_age), "
                    f"Trigger-{mobapp_data_trigger}@{mobapp_data_trigger_time} (^trig_age), ")

        # ---------------------------------------------
        if mobapp_data_state_not_set_flag:
            Device.mobapp_data_change_reason = \
                Device.mobapp_data_trigger = f"Initial Locate@{mobapp_data_time}"

        # Reject State and trigger changes older than the current data
        elif (Device.mobapp_data_secs <= Device.last_update_loc_secs):
            Device.mobapp_data_reject_reason = (f"Before Last Update "
                                                f"({secs_to_time(Device.mobapp_data_secs)} <= "
                                                f"{secs_to_time(Device.last_update_loc_secs)})")

        elif mobapp_data_change_flag is False:
            Device.mobapp_data_reject_reason = "Data has not changed"

        # Exit a zone and not in a zone, nothing to do
        elif (Device.mobapp_data_trigger == EXIT_ZONE
                and Device.isnotin_zone
                # and Device.isin_zone
                and Device.got_exit_trigger_flag is False):
            if mobapp_data_secs > Device.located_secs_plus_5:
                Device.got_exit_trigger_flag = True
                Device.mobapp_zone_exit_secs = mobapp_data_secs
                Device.mobapp_zone_exit_time = mobapp_data_state_time
                exit_zone_name = Device.StatZone.dname if Device.StatZone else 'Unknown'
                Device.mobapp_data_trigger = (  f"Verify Exit {exit_zone_name}@"
                                                f"{mobapp_data_state_time}")
                Device.mobapp_data_change_reason = Device.mobapp_data_trigger

            else:
                Device.mobapp_data_reject_reason = "Exit when not in zone"

        # Exit trigger and the trigger changed from last poll overrules trigger change time
        elif Device.mobapp_data_trigger == EXIT_ZONE:
            if Device.mobapp_data_secs > Device.located_secs_plus_5:
                Device.mobapp_data_change_reason = (f"{EXIT_ZONE}@{Device.mobapp_data_time} "
                                                    f"({zone_dname(Device.mobapp_zone_exit_zone)}"
                                                    f"/{format_dist_m(Device.mobapp_zone_exit_dist_m)})")

            Device.mobapp_zone_exit_trigger_info = Device.mobapp_data_change_reason

        # Enter trigger and the trigger changed from last poll overrules trigger change time
        elif (Device.mobapp_data_trigger == ENTER_ZONE):
            Device.mobapp_data_change_reason = f"{ENTER_ZONE}@{Device.mobapp_data_time} "
            if Device.isin_zone_mobapp_state:
                Device.mobapp_data_change_reason +=(f"({zone_dname(Device.mobapp_zone_enter_zone)}/"
                                                    f"{format_dist_m(Device.mobapp_zone_enter_dist_m)})")

            Device.mobapp_zone_enter_trigger_info = Device.mobapp_data_change_reason

        elif (Device.mobapp_data_trigger not in [ENTER_ZONE, EXIT_ZONE]
                and Device.mobapp_data_secs > Device.located_secs_plus_5
                and Device.mobapp_data_gps_accuracy > Gb.gps_accuracy_threshold):
            Device.mobapp_data_reject_reason = (f"Poor GPS Accuracy-{Device.mobapp_data_gps_accuracy}m "
                                                f"#{Device.old_loc_cnt}")

        # ---------------------------------------------
        # Discard StatZone entered if StatZone was created in the last 15-secs
        if (Device.mobapp_data_trigger == ENTER_ZONE
                and is_statzone(Device.mobapp_data_state)
                and Device.isin_statzone
                and secs_since(Device.loc_data_secs <= 15)):
            Device.mobapp_data_reject_reason = "Enter into StatZone just created"

        # Discard if already in the zone
        elif (Device.mobapp_data_trigger == ENTER_ZONE
                and Device.mobapp_data_state == Device.loc_data_zone):
            Device.mobapp_data_reject_reason = "Enter Zone and already in zone"

        # ---------------------------------------------
        if Device.is_passthru_zone_delay_active:
            Device.mobapp_data_reject_reason = f"Passing thru zone, {Device.mobapp_data_trigger} discarded"

        # ---------------------------------------------
        # If Enter or Exit, reasons already set, continue
        if (Device.mobapp_data_change_reason
                or Device.mobapp_data_reject_reason):
            pass

        elif (Device.is_still_at_last_location
                and Device.is_next_update_time_reached is False):
            Device.mobapp_data_reject_reason = f"Still and Next Update not Reached"

        # trigger time is after last locate
        elif Device.mobapp_data_secs > Device.located_secs_plus_5:
            Device.mobapp_data_change_reason = (f"{Device.mobapp_data_trigger}@"
                                                f"{Device.mobapp_data_time}")

        # No update needed if no location changes
        elif (Device.mobapp_data_state == Device.loc_data_zone      #Device.last_update_loc_zone
                and f'{Device.mobapp_data_latitude:.5f}'  == f'{Device.loc_data_latitude:.5f}'
                and f'{Device.mobapp_data_longitude:.5f}' == f'{Device.loc_data_longitude:.5f})'):
            Device.mobapp_data_reject_reason = "No Location Change"

        # MobApp location changed and State changed more than 5-secs after last locate
        elif Device.mobapp_data_secs > Device.located_secs_plus_5:
            Device.mobapp_data_change_reason = (f"Location Change")
            Device.mobapp_data_trigger = (f"Location Change, "
                    f"GPS-{Device.mobapp_data_fgps}")

        # Prevent duplicate update if State & Trigger changed at the same time
        # and state change was handled on last cycle
        # elif (Device.mobapp_data_secs == Device.mobapp_data_secs
        elif (Device.mobapp_data_state_secs == Device.mobapp_data_trigger_secs
                or Device.mobapp_data_secs <= Device.located_secs_plus_5):
            Device.mobapp_data_reject_reason = "Already Processed"

        # Bypass if trigger contains ic3 date stamp suffix (@hhmmss)
        elif instr(Device.mobapp_data_trigger, '@'):
            Device.mobapp_data_reject_reason = "Trigger Already Processed"

        elif Device.mobapp_data_secs <= Device.located_secs_plus_5:
            Device.mobapp_data_reject_reason = "Trigger Before Last Locate"

        else:
            Device.mobapp_data_reject_reason = "Failed Update Tests"

        # ---------------------------------------------
        # Display MobApp Monitor info message if the state or trigger changed
        if (Gb.this_update_time.endswith('00:00')
                or mobapp_msg != Device.last_mobapp_msg):
            _display_mobapp_msg(Device, mobapp_msg)

    except Exception as err:
            log_exception(err)

#--------------------------------------------------------------------
def _display_mobapp_msg(Device, mobapp_msg):
    try:
        Device.last_mobapp_msg = mobapp_msg
        mobapp_msg += (f"LastTrigger-{Device.sensors[TRIGGER]}, "
                        f"MobAppData-{Device.mobapp_data_time}")

        if Device.mobapp_zone_enter_zone:
            mobapp_msg +=(f", LastZoneEnter-{Device.mobapp_zone_enter_zone}@"
                            f"{Device.mobapp_zone_enter_time}")
        if Device.mobapp_zone_exit_zone:
            mobapp_msg +=(f", LastZoneExit-{Device.mobapp_zone_exit_zone}@"
                            f"{Device.mobapp_zone_exit_time}")

        Device.mobapp_data_updated_flag = (Device.mobapp_data_reject_reason == "")
        mobapp_msg += (f", WillUpdate-{Device.mobapp_data_updated_flag}")

        if Device.mobapp_data_change_reason:
            mobapp_msg += (f"-{Device.mobapp_data_change_reason}")
        if Device.mobapp_data_reject_reason:
            mobapp_msg += (f"-{Device.mobapp_data_reject_reason}")
        mobapp_msg += (f", Located-{Device.loc_data_time} ({Device.dev_data_source}), "
                        f"GPS-{Device.mobapp_data_fgps}")

        mobapp_msg = mobapp_msg.replace("^trig_age", format_age(Device.mobapp_data_trigger_secs))
        mobapp_msg = mobapp_msg.replace("^state_age", format_age(Device.mobapp_data_state_secs))
        mobapp_msg += f", {Device.mobapp_zone_enter_trigger_info}"
        mobapp_msg += f", {Device.mobapp_zone_exit_trigger_info}"
        post_monitor_msg(Device.devicename, mobapp_msg)

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Update the device on a state or trigger change was recieved from the Mobile App
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''
If this Device is entering a zone also assigned to another device. The Mobile App
will move issue a Region Entered trigger and the state is the other devicename's
stat zone name. Create this device's stat zone at the current location to get the
zone tables in sync. Must do this before processing the state/trigger change or
this devicename will use this trigger to start a timer rather than moving it ineo
the stat zone.
'''
def reset_statzone_on_enter_exit_trigger(Device):
    try:
        if Device.mobapp_data_trigger in MOBAPP_TRIGGERS_EXIT:
            if Device.isin_statzone:
                statzone.exit_statzone(Device)

    except Exception as err:
        log_exception(err)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#  Check the state of the mobapp to see if it is alive on regular intervals by
#  sending a location request at regular intervals. It will be considered dead/inactive
#  if there is no response with it's location.
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def check_if_mobapp_is_alive(Device):
    try:
        if (Device.mobapp_monitor_flag is False
                or Device.is_offline
                or Device.mobapp[NOTIFY] == ''):
            return

        # Send a location request if the mobapp data is more than 'alive Interval'
        # and the check for request sent > 1 hr ago. Only send once an hour.
        if (secs_since(Device.mobapp_request_loc_first_secs) % Gb.mobapp_alive_interval_secs == 0
                and secs_since(Device.mobapp_data_secs) > Gb.mobapp_alive_interval_secs
                and secs_since(Device.mobapp_data_trigger_secs) > Gb.mobapp_alive_interval_secs):
            mobapp_interface.request_location(Device, is_alive_check=True)

            return

        # No activity, display Alert msg in Event Log
        if (Gb.this_update_time in ['00:00:00', '06:00:00', '12:00:00', '18:00:00']
                and secs_since(Device.mobapp_data_secs) > 21600):
            event_msg =(f"Last Mobile App update from {Device.mobapp_device_trkr_entity_id_fname}"
                        f"—{format_time_age(Device.mobapp_data_secs)}")
            Device.display_info_msg( event_msg)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def get_mobapp_device_trkr_entity_attrs(Device):
    '''
    Return the state and attributes of the Mobile App device tracker.
    The ic3 device tracker state and attributes are returned if
    the Mobile App data is not available or an error occurs.

    Return:
        device_trkr_attrs - MobApp device tracker attrinutes if available
        None -  error or no data is available
    '''
    try:
        if (Device.mobapp_monitor_flag is False
                or Gb.conf_data_source_MOBAPP is False):
            return None

        entity_id = Device.mobapp[DEVICE_TRACKER]
        device_trkr_attrs = {}
        device_trkr_attrs[DEVICE_TRACKER] =  entity_io.get_state(entity_id)

        if device_trkr_attrs[DEVICE_TRACKER] == 'unavailable':
            Device.mobapp_monitor_flag            = False
            Device.mobapp_device_unavailable_flag = True
            Device.mobapp_data_invalid_error_cnt += 1
            post_event( f"{EVLOG_ALERT}The Mobile App has returned a `not available` status "
                        f"and will not be used for tracking or zone enter/exit events"
                        f"{CRLF_DOT}{Device.fname_devicename}{RARROW}{entity_id}"
                        f"{more_info('mobapp_device_unavailable')}")
            log_error_msg(f"iCloud3 Error ({Device.fname_devtype}) > "
                f"The Mobile App is not available and this device will not be monitored")
            return None

        device_trkr_attrs.update(entity_io.get_attributes(entity_id))

        if LATITUDE not in device_trkr_attrs or device_trkr_attrs[LATITUDE] == 0:
            Device.mobapp_data_invalid_error_cnt += 1
            if Device.mobapp_data_invalid_error_cnt == 4:
                post_event( f"{EVLOG_ALERT}The Mobile App has not reported the gps "
                            f"location after 4 requests. It may be asleep, offline "
                            f"or not available and should be reviewed."
                            f"{CRLF_DOT}{Device.fname_devicename}{RARROW}{entity_id}"
                            f"{more_info('mobapp_device_no_location')}")
                log_error_msg(f"iCloud3 Alert ({Device.fname_devtype}) > "
                    f"The Mobile App has not reported the gps location after 4 requests. "
                    f"It may be asleep, offline or not available.")
            return None

        device_trkr_attrs[CONF_IC3_DEVICENAME] = Device.devicename
        device_trkr_attrs[f"state_{TIMESTAMP_SECS}"] = entity_io.get_last_changed_time(entity_id)
        device_trkr_attrs[f"state_{TIMESTAMP_TIME}"] = secs_to_time(device_trkr_attrs[f"state_{TIMESTAMP_SECS}"])

        if GPS_ACCURACY in device_trkr_attrs:
            device_trkr_attrs[GPS_ACCURACY] = round(device_trkr_attrs[GPS_ACCURACY])
        if ALTITUDE in device_trkr_attrs:
            device_trkr_attrs[ALTITUDE] = round(device_trkr_attrs[ALTITUDE])
        if VERT_ACCURACY in device_trkr_attrs:
            device_trkr_attrs[VERT_ACCURACY] = round(device_trkr_attrs[VERT_ACCURACY])

        #log_rawdata(f"MobApp Data - {entity_id}", device_trkr_attrs)

        return device_trkr_attrs

    except Exception as err:
        log_exception(err)
        return None

# -----------------------------------------------------------------
def update_mobapp_data_from_entity_attrs(Device, device_trkr_attrs):
    '''
    Update the mobapp data fields from the raw device_tracker entity attribute fields
    '''

    if (device_trkr_attrs is None
            or LATITUDE not in device_trkr_attrs):
        log_error_msg(Device.devicename,
                f"iCloud3 Alert ({Device.fname_devtype}) > No data was returned from "
                f"the Mobile App")
        return

    mobapp_data_secs = device_trkr_attrs.get(TIMESTAMP_SECS, Device.mobapp_data_state_secs)
    mobapp_data_time = device_trkr_attrs.get(TIMESTAMP_TIME, Device.mobapp_data_state_time)
    gps_accuracy     = device_trkr_attrs.get(GPS_ACCURACY, 99999)

    if Device.mobapp_data_secs >= mobapp_data_secs or gps_accuracy > Gb.gps_accuracy_threshold:
        return

    log_rawdata(f"MobApp Attrs - <{Device.devicename}>", device_trkr_attrs)

    Device.mobapp_data_state             = device_trkr_attrs.get(DEVICE_TRACKER, NOT_SET)
    Device.mobapp_data_state_secs        = device_trkr_attrs.get(f"state_{TIMESTAMP_SECS}", 0)
    Device.mobapp_data_state_time        = device_trkr_attrs.get(f"state_{TIMESTAMP_TIME}", HHMMSS_ZERO)

    Device.mobapp_data_trigger           = device_trkr_attrs.get("trigger", NOT_SET)
    Device.mobapp_data_secs              = mobapp_data_secs
    Device.mobapp_data_time              = mobapp_data_time
    Device.mobapp_data_invalid_error_cnt = 0
    Device.mobapp_data_latitude          = device_trkr_attrs.get(LATITUDE, 0)
    Device.mobapp_data_longitude         = device_trkr_attrs.get(LONGITUDE, 0)
    Device.mobapp_data_gps_accuracy      = gps_accuracy
    Device.mobapp_data_vertical_accuracy = device_trkr_attrs.get(VERT_ACCURACY, 99999)
    Device.mobapp_data_altitude          = device_trkr_attrs.get(ALTITUDE, 0)

    if Device.FromZone_Home:
        home_dist = format_dist_km(Device.FromZone_Home.distance_km_mobapp)
    else:
        home_dist = ''

    monitor_msg = (f"UPDATED MobApp > {Device.devicename}, {Device.mobapp_data_trigger}, "
                    f"{CRLF_DOT}Loc-{Device.mobapp_data_time}, "
                    f"Home-{home_dist}, "
                    f"{Device.mobapp_data_fgps}")
    if monitor_msg != Device.update_mobapp_data_monitor_msg:
        Device.update_mobapp_data_monitor_msg = monitor_msg
        post_monitor_msg(Device.devicename, monitor_msg)


#--------------------------------------------------------------------
def sync_mobapp_data_state_statzone(Device):
    '''
    Update the Device's mobapp_data_state value to sync it with the statzone
    the device is in. If the mobapp state is a statzone but ic3 has it set to
    not_home and the device is in a statzone, the mobapp state value may be
    out of sync because the state value changed byt the actual location did not
    change.

    This is done at the befinning of the process_update function in icloud3_main
    sot the mobapp state value will be correct when the Event Log is displayed

    Return:
        True - The mobapp_data_state was updated
        False - The mobapp_data_state was not updated

    '''
    if (Device.mobapp_monitor_flag is False
            or Gb.conf_data_source_MOBAPP is False
            or Device.mobapp.get(DEVICE_TRACKER) is None):
        return False

    mobapp_data_state = entity_io.get_state(Device.mobapp[DEVICE_TRACKER])

    if (is_statzone(mobapp_data_state)
            and is_statzone(Device.loc_data_zone)
            and Device.isnotin_zone_mobapp_state):
            #and Device.mobapp_data_state == NOT_HOME):
        Device.mobapp_data_state      = mobapp_data_state
        Device.mobapp_data_state_secs = Gb.this_update_secs
        Device.mobapp_data_state_time = Gb.this_update_time

        return True

    return False
