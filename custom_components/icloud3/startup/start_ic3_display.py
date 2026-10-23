"""Startup display and diagnostic messages.

Event Log and monitor messages posted while iCloud3 initializes. Kept apart
from start_ic3.py so the startup flow and its screen output can be read
independently. Nothing here changes device state.
"""

from ..global_variables import GlobalVariables as Gb
from ..const            import (BATTERY_LEVEL, CONF_DEVICE_TYPE, CONF_FNAME,
                                CONF_IC3_DEVICENAME, CONF_TRACKING_MODE, CONF_VERSION,
                                CRLF_DOT, CRLF_HDOT, CRLF_RED_ALERT,
                                DEVICE_TRACKER, DEVICE_TYPE_DN,
                                EVLOG_ALERT, EVLOG_ATTENTION, HOME,
                                ICLOUD_DEVICE_STATUS, INACTIVE, INACTIVE_SYMB,
                                LOCATION, NOTIFY, RARROW, RED_ALERT, TIMESTAMP,
                                TRIGGER, YELLOW_ALERT, )
from ..utils.utils      import (dict_reverse_sort, instr, is_empty, list_to_str,
                                username_id, zone_dname, )
from ..utils.messaging  import (broadcast_info_msg, post_event, post_alert, post_greenbar_msg,
                                post_monitor_msg, update_alert_sensor,
                                log_debug_msg, log_error_msg, log_exception,
                                more_info, format_header_box, )
from ..utils.time_util  import (mins_since, format_timer, format_time_age, )

#------------------------------------------------------------------------------
def display_all_devices_config_info(selected_devicenames=None):
    '''
    Display the devices configuration in the Event Log.

    selected_devicenames:
        - A list of devices to display in the Event Log
        - If updating devices in config_flow, the updated devicename is in config_parms_update_control field that is
            controlling the iCloud3 update/restart. Only display the updated device
        - 'all' or None - Display all devices
    '''

    for devicename, Device in dict_reverse_sort(Gb.Devices_by_devicename).items():
        if (selected_devicenames is None
                or 'all' in selected_devicenames
                or devicename in selected_devicenames):
            pass
        else:
            continue

        if Device.fname in Gb.alerts_sensor_attrs:
            if Device.was_verified is False:
                Device.evlog_fname_alert_char = RED_ALERT
            else:
                Device.evlog_fname_alert_char = YELLOW_ALERT

        if Device.was_verified:
            tracking_mode = ''
        else:
            Gb.reinitialize_icloud_devices_flag = (Gb.conf_icloud_device_cnt > 0)
            tracking_mode = f"{RED_ALERT}NOT "

        tracking_mode += 'Monitored' if Device.is_monitored else 'Tracked'
        if instr(tracking_mode, 'NOT'):
            tracking_mode = tracking_mode.upper()
        evlog_msg =(f"{Device.fname_devicename} > {Device.model_display_name}, {tracking_mode}")

        # Device is not in configured Apple acct if it was not matched
        username     = Device.conf_apple_acct_username
        apple_acct   = Device.AppleAcct.username_account_owner if Device.AppleAcct else username_id(username)
        icloud_dname = Device.conf_icloud_dname
        apple_acct_err_msg = icloud_dname_err_msg = ''

        # Get Apple acct owner from AppleAcct
        if username == '' or username in Gb.AppleAcct_error_by_username:
            pass
        elif (Device.conf_apple_acct_username in Gb.AppleAcct_by_username
                and Device.verified_ICLOUD is False):
            icloud_dname_err_msg = f", {RED_ALERT}Not in Apple Acct"
            log_error_msg(f"iCloud3 Device Configuration Error > "
                    f"{Device.fname_devicename}, "
                    f"{icloud_dname} Not in Apple Acct ({apple_acct})")
        # Not using Apple as a data source
        elif apple_acct == '' or apple_acct.startswith('Not used'):
            apple_acct = 'None (NOT SPECIFIED)'

        elif Gb.internet_error:
            pass

        # Apple acct is not found in AppleAcct
        elif Device.conf_apple_acct_username in Gb.AppleAcct_by_username:
            pass

        elif Gb.use_data_source_ICLOUD is False:
            apple_acct_err_msg = f", {INACTIVE_SYMB}ICLOUD DISABLED"

        else:
            apple_acct_err_msg = f", {RED_ALERT}APPLE ACCT ERROR"
            update_alert_sensor(Device.fname, f"Unknown Apple Acct ({apple_acct})")
            log_error_msg(  f"iCloud3 Device Configuration Error > "
                            f"{Device.fname_devicename}, "
                            f"Unknown Apple Acct ({apple_acct})")

        if Gb.internet_error:
            apple_acct_err_msg = f", {RED_ALERT}Not Available"

        # Build the Apple acct evlog msg
        evlog_msg += f"{CRLF_DOT}Apple Account Configuration:"

        if apple_acct == '' and icloud_dname == '':
            evlog_msg += f"{CRLF_HDOT}Not used as a location data source"

        else:
            evlog_msg+=(f"{CRLF_HDOT}Acct Owner...: {apple_acct}{apple_acct_err_msg}"
                        f"{CRLF_HDOT}Device Name: {icloud_dname}{icloud_dname_err_msg}")

        # Build MobApp evlog config msg
        if Device.mobapp[DEVICE_TRACKER] == '':
            if Device.conf_mobapp_fname:
                evlog_msg += f"{CRLF_RED_ALERT}Mobile App Device > {Device.conf_mobapp_fname}, Not Found"
            else:
                evlog_msg += (  f"{CRLF_DOT}Mobile App Configuration:"
                                f"{CRLF_HDOT}Not used as a location data source")

        else:
            evlog_msg += CRLF_DOT if Device.is_mobapp_monitored else CRLF_RED_ALERT
            evlog_msg += f"Mobile App Configuration:"

            trigger_entity = Device.mobapp[TRIGGER][7:] or 'UNKNOWN'
            bat_lev_entity = Device.mobapp[BATTERY_LEVEL][7:] or 'UNKNOWN'
            notify_entity  = Device.mobapp[NOTIFY] or 'WAITING FOR NOTIFY SVC TO START"'
            evlog_msg += (  f"{CRLF_HDOT}MobApp Device: {Device.conf_mobapp_fname}"
                            f"{CRLF_HDOT}Device Tracker..: {Device.mobapp[DEVICE_TRACKER]}"
                            f"{CRLF_HDOT}Action Trigger...: {trigger_entity}"
                            f"{CRLF_HDOT}Battery Sensor..: {bat_lev_entity}"
                            f"{CRLF_HDOT}Notifications.....: {notify_entity}")

        # Build evlog m sg for the tracking parameters
        evlog_msg += f"{CRLF_DOT}Other Parameters:"
        evlog_msg += f"{CRLF_HDOT}inZone Interval: {format_timer(Device.inzone_interval_secs)}"
        if Device.fixed_interval_secs > 0:
            evlog_msg += f"{CRLF_HDOT}Fixed Interval: {format_timer(Device.fixed_interval_secs)}"
        if 'none' not in Device.log_zones:
            log_zones_fname = [zone_dname(zone) for zone in Device.log_zones]
            log_zones = list_to_str(log_zones_fname)
            log_zones = f"{log_zones.replace(', Name-', f'{RARROW}(')}.csv)"
            evlog_msg += f"{CRLF_HDOT}Log Zone Activity: {log_zones}"

        if Device.track_from_base_zone != HOME:
                evlog_msg += f"{CRLF_HDOT}Primary Track from Zone: {zone_dname(Device.track_from_base_zone)}"
        if Device.track_from_zones != [HOME]:
            tfz_fnames = [zone_dname(zone) for zone in Device.track_from_zones]
            evlog_msg += (f"{CRLF_HDOT}Track from Zones: {list_to_str(tfz_fnames)}")
        if Device.away_time_zone_offset != 0:
            plus_minus = '+' if Device.away_time_zone_offset > 0 else ''
            evlog_msg += (f"{CRLF_HDOT}Away Time Zone: HomeZone {plus_minus}{Device.away_time_zone_offset} hours")

        try:
            if Gb.use_data_source_ICLOUD:
                if Device.AADevData_icloud is None:
                    evlog_msg += (f"{CRLF_RED_ALERT}DEVICE IS NOT CONFIGURED")
                else:
                    device_status = Device.AADevData_icloud.device_data[ICLOUD_DEVICE_STATUS]
                    timestamp     = Device.AADevData_icloud.device_data[LOCATION][TIMESTAMP]
                    if device_status == '201' and mins_since(timestamp) > 5:
                        evlog_msg += (f"{CRLF_RED_ALERT}DEVICE IS OFFLINE > "
                                    f"Since-{format_time_age(timestamp)}")
                        Device.offline_secs = timestamp

        except Exception as err:
            log_exception(err)
            pass

        post_event(evlog_msg)

#------------------------------------------------------------------------------
def display_inactive_devices():
    '''
    Display a list of the Inactive devices in the Event Log
    '''

    Gb.inactive_fname_by_devicename = {conf_device[CONF_IC3_DEVICENAME]: conf_device[CONF_FNAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE}

    inactive_devices_msg =[( f"{conf_device[CONF_FNAME]} ({conf_device[CONF_IC3_DEVICENAME]}), "
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}")
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_TRACKING_MODE] == INACTIVE]

    Gb.startup_lists['Gb.inactive_fname_by_devicename'] = Gb.inactive_fname_by_devicename

    if is_empty(Gb.inactive_fname_by_devicename):
        return

    evlog_msg = f"Inactive/Untracked Devices > "
    evlog_msg+= list_to_str(inactive_devices_msg, separator=CRLF_DOT)
    post_event(evlog_msg)

    if len(Gb.inactive_fname_by_devicename) == len(Gb.conf_devices):
        post_greenbar_msg('All devices are Inactive and nothing will be tracked')
        post_alert( f"ALL DEVICES ARE INACTIVE > "
                    f"{more_info('all_devices_inactive')}")

#------------------------------------------------------------------------------
def display_object_lists():
    '''
    Display the object list values
    '''
    broadcast_info_msg(f"Logging Initial Monitor Info")
    monitor_msg = (f"StatZones-{list_to_str(Gb.StatZones_by_zone.keys())}")
    post_monitor_msg(monitor_msg)

    monitor_msg = (f"Devices-{list_to_str(Gb.Devices_by_devicename.keys())}")
    post_monitor_msg(monitor_msg)

    for Device in Gb.Devices:
        monitor_msg = (f"Device-{Device.devicename}, "
                        f"FromZones-{list_to_str(Device.FromZones_by_zone.keys())}")
        post_monitor_msg(monitor_msg)

    monitor_msg = (f"Zones-{list_to_str(Gb.Zones_by_zone.keys())}")
    post_monitor_msg(monitor_msg)

#--------------------------------------------------------------------
def dump_startup_lists_to_log(debug_log_title=None):
    '''
    Cycle thru the Gb.startup_lists dictionary that contains internal lists and
    dictionaries. Write all items to the icloud3-0.log file
    '''
    if Gb.startup_lists == {}:  return

    if debug_log_title:
        log_debug_msg(f"{format_header_box(debug_log_title)}")

    _startup_lists = Gb.startup_lists.copy()
    for field, values in _startup_lists.items():
        log_debug_msg(f"{field}={values}")

    # Check to see if any items were added by another task while writing the list to the
    # log. That can generate a 'RuntimeError: dictionary changed size during iteration'
    items_start = len(_startup_lists)
    items_end   = len(Gb.startup_lists)
    if items_end > items_start:
        cnt = -1
        for field, values in _startup_lists.items():
            cnt += 1
            if cnt >= items_start:
                log_debug_msg(f"{field}={values}")


    if debug_log_title:
        log_debug_msg(f"{format_header_box(debug_log_title)}")

    Gb.startup_lists = {}

#------------------------------------------------------------------------------
def display_platform_operating_mode_msg():
    if Gb.ha_config_platform_stmt is False:
        return

    if Gb.conf_profile[CONF_VERSION] == 1:
        alert_msg =("HA tried to start iCloud3 from a configuration.yaml file statement. "
                    "It was ignored.")
    else:
        post_greenbar_msg('HA configuration.yaml contains a `platform: iCloud3` that can be deleted')
        alert_msg = (f"{EVLOG_ALERT}HA CONFIG CHANGE NEEDED > iCloud3 is an HA Integration. Delete the 'platform: icloud3` "
                "configuration parameters in the HA `configuration.yaml` file.")

    post_event(alert_msg)

#------------------------------------------------------------------------------
def post_restart_icloud3_complete_msg():
    post_event(f"{EVLOG_ATTENTION}Initializing {Gb.icloud3_version_msg} > Complete")

    Gb.EvLog.update_event_log_display("")
