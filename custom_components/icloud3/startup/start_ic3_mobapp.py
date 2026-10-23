"""Mobile App device setup for startup Stage 4.

Matches the Mobile App (mobile_app integration) device_tracker entities found in
the entity registry to the iCloud3 devices and sets the tracking and monitoring
flags the rest of the startup flow reads. Split out of start_ic3.py, which
re-exports the public names so existing call sites stay unchanged.
"""

from ..global_variables import GlobalVariables as Gb
from ..const            import (BATTERY_LEVEL, BATTERY_STATUS, CONF_MODEL, CONF_MODEL_DISPLAY_NAME,
                                CONF_MOBILE_APP_DEVICE, CONF_RAW_MODEL,
                                CRLF, CRLF_CHK, CRLF_DOT, CRLF_HDOT, CRLF_RED_ALERT,
                                CRLF_TAB, CRLF_X, DEVICE_TRACKER, DEVICE_TRACKER_DOT,
                                DEVICE_TYPE_DNS, EVLOG_ALERT, MOBAPP, RARROW, RED_ALERT, TRIGGER, )
from ..utils.utils      import (instr, username_id, )
from ..utils.messaging  import (broadcast_info_msg, post_dotted_line, post_event,
                                post_alert, post_greenbar_msg, update_alert_sensor,
                                log_error_msg, log_warning_msg, log_exception, more_info, )
from .mobapp_resolver   import (AMBIGUOUS, DISABLED, RENAMED, RESERVED,
                                resolve_mobapp_dname, )


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SETUP MOBAPP DEVICE -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def setup_tracked_devices_for_mobapp():
    '''
    Get the MobApp device_tracker entities from the entity registry. Then cycle through the
    Devices being tracked and match them up. Anything left over at the end is not matched and not monitored.
    '''

    from ..mobile_app import mobapp_interface
    from ..startup    import config_file

    mobapp_error_mobile_app_msg = ''
    mobapp_error_search_msg     = ''
    mobapp_error_disabled_msg   = ''
    mobapp_error_not_found_msg  = ''
    Gb.mobapp_device_verified_cnt = 0
    devices_monitored_cnt = 0
    devices_monitored_msg = devices_not_monitored_msg = devices_not_assigned_msg = ''
    unmatched_mobapp_devices = Gb.mobapp_id_by_mobapp_dname.copy()
    verified_mobapp_fnames = []

    post_dotted_line()
    tracked_msg = ( f"Mobile App Devices > "
                    f"{Gb.conf_mobapp_device_cnt} of "
                    f"{len(Gb.conf_devices)} used by iCloud3")

    # An explicit Mobile App tracker can only belong to one iCloud3 device. Names
    # selected by another device are reserved so a rename repair can never steal
    # them. ScanFor entries are not concrete names and are not reserved.
    reserved_mobapp_dnames = {
        conf_device.get(CONF_MOBILE_APP_DEVICE, '')
        for conf_device in Gb.conf_devices
        if conf_device.get(CONF_MOBILE_APP_DEVICE, '') not in ('', 'None')
        and not conf_device.get(CONF_MOBILE_APP_DEVICE, '').startswith('ScanFor: ')}

    Gb.devicenames_x_mobapp_dnames = {}
    assigned_mobapp_dnames = set()
    for devicename, Device in Gb.Devices_by_devicename.items():
        broadcast_info_msg(f"Set up Mobile App Devices > {devicename}")

        conf_mobapp_dname = Device.mobapp[DEVICE_TRACKER].replace(DEVICE_TRACKER_DOT, '')
        Gb.devicenames_x_mobapp_dnames[devicename] = None

        if conf_mobapp_dname in ['', 'None']:
            Device.initialize_mobapp_device_tracker_entity_name()
            continue

        # Check if the specified mobapp device tracker is valid and in the entity registry
        if conf_mobapp_dname.startswith('ScanFor: ') is False:
            mobapp_dname, status = resolve_mobapp_dname(
                    conf_mobapp_dname,
                    Gb.mobapp_id_by_mobapp_dname.keys(),
                    reserved_dnames=reserved_mobapp_dnames - {conf_mobapp_dname},
                    disabled_dnames=Gb.mobapp_disabled_dnames)

            if status == RENAMED and mobapp_dname:
                if mobapp_dname in assigned_mobapp_dnames:
                    update_alert_sensor(Device.fname,
                                        f"MobApp Device Already Assigned ({mobapp_dname})")
                    mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                    f"Assigned to {Device.fname_devicename} "
                                                    f"(rename candidate already used)")
                    continue

                # HA renames an entity id when it collides with another entity
                # (foo -> foo_2). A name match alone cannot prove that the new
                # entity belongs to this device, so never rewrite the user's
                # configuration automatically. Report the likely rename and
                # leave tracking disabled until the user confirms it in the
                # iCloud3 configuration.
                update_alert_sensor(Device.fname,
                                    f"Mobile App Device renamed? ({conf_mobapp_dname}{RARROW}{mobapp_dname})")
                Device.set_fname_alert(RED_ALERT)
                post_event(f"{EVLOG_ALERT}Mobile App Device Tracker Not Found > "
                           f"{conf_mobapp_dname} is not in the entity registry. "
                           f"The similarly named {mobapp_dname} was found. "
                           f"Update the Mobile App Device for {Device.fname_devicename} "
                           f"in the iCloud3 configuration.")
                log_warning_msg(f"iCloud3 > Mobile App Device Tracker not found > "
                                f"{conf_mobapp_dname}, possible rename to {mobapp_dname}, "
                                f"Assigned to {Device.fname_devicename}. "
                                f"Update the Mobile App Device in the iCloud3 configuration.")
                continue

            if mobapp_dname is None:
                if status == DISABLED:
                    update_alert_sensor(Device.fname,
                                        f"MobApp Device Disabled ({conf_mobapp_dname})")
                    Device.set_fname_alert(RED_ALERT)
                    Device.is_mobapp_device_unavailable = True
                    mobapp_error_disabled_msg += ( f"{CRLF_DOT}{conf_mobapp_dname} > "
                                                    f"Assigned to-{Device.fname_devicename}")
                elif status == AMBIGUOUS:
                    update_alert_sensor(Device.fname,
                                        f"Multiple MobApp Device candidates ({conf_mobapp_dname})")
                    Device.set_fname_alert(RED_ALERT)
                    mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                    f"Assigned to {Device.fname_devicename} "
                                                    f"(several renamed candidates)")
                elif status == RESERVED:
                    update_alert_sensor(Device.fname,
                                        f"MobApp Device assigned to another device ({conf_mobapp_dname})")
                    Device.set_fname_alert(RED_ALERT)
                    mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                    f"Assigned to {Device.fname_devicename} "
                                                    f"(already used by another device)")
                else:
                    update_alert_sensor(Device.fname, f"Unknown MobApp Device ({conf_mobapp_dname})")
                    Device.set_fname_alert(RED_ALERT)
                    mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                    f"Assigned to {Device.fname_devicename}")
                continue

            if mobapp_dname in assigned_mobapp_dnames:
                update_alert_sensor(Device.fname,
                                    f"MobApp Device Already Assigned ({mobapp_dname})")
                Device.set_fname_alert(RED_ALERT)
                mobapp_error_not_found_msg += ( f"{CRLF_X}{conf_mobapp_dname} > "
                                                f"Assigned to {Device.fname_devicename} "
                                                f"(already used by another device)")
                continue

            assigned_mobapp_dnames.add(mobapp_dname)
            Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
            Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename
        else:
            mobapp_dname = _scan_for_for_mobapp_device( devicename, Device, conf_mobapp_dname)
            if mobapp_dname and mobapp_dname in assigned_mobapp_dnames:
                mobapp_dname = None
            if mobapp_dname:
                assigned_mobapp_dnames.add(mobapp_dname)
                Gb.devicenames_x_mobapp_dnames[devicename]   = mobapp_dname
                Gb.devicenames_x_mobapp_dnames[mobapp_dname] = devicename
            else:
                update_alert_sensor(Device.fname, f"Unknown ScanFor MobApp Device ({conf_mobapp_dname})")
                Device.set_fname_alert(RED_ALERT)
                mobapp_error_search_msg += (f"{CRLF_X}{conf_mobapp_dname}_??? > "
                                            f"Assigned to {Device.fname_devicename}")

    for devicename, Device in Gb.Devices_by_devicename.items():
        mobapp_dname = Gb.devicenames_x_mobapp_dnames[devicename]
        if mobapp_dname is None:
            continue

        mobapp_id = Gb.mobapp_id_by_mobapp_dname[mobapp_dname]

        # Get fname from MobileApp integration if it is started, otherwise build one for now
        # and reset it when the MobileApp is checked again after HA has started
        if mobapp_id in Gb.mobapp_fnames_by_mobapp_id:
            mobapp_fname = Gb.mobapp_fnames_by_mobapp_id[mobapp_id]
        else:
            mobapp_fname = f"{mobapp_dname.replace('_', ' ').title()}"

            # Fix device type (iphone --> Iphone --> iPhone)
            for _device_type in DEVICE_TYPE_DNS.keys():
                if instr(mobapp_fname, _device_type.title()):
                    mobapp_fname = mobapp_fname.replace(
                            _device_type.title(), DEVICE_TYPE_DNS[_device_type])
                    break

        Device.conf_mobapp_fname = mobapp_fname
        Gb.devicenames_x_mobapp_dnames[mobapp_fname] = devicename

        # device_tracker entity is disabled
        if mobapp_id in Gb.MobileApp_fnames_disabled:
            update_alert_sensor(Device.fname, f"MobApp Device Disabled ({mobapp_dname})")
            Device.set_fname_alert(RED_ALERT)
            Device.is_mobapp_device_unavailable = True
            mobapp_error_disabled_msg += (  f"{CRLF_DOT}{mobapp_dname} > "
                                            f"Assigned to-{Device.fname_devicename}")
            continue

        # Build errors message, can still use the Mobile App for zone changes but sensors are not monitored
        if (Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, '') == ''
                or instr(Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')
                or Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, '') == ''
                or instr(Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, ''), 'DISABLED')):
            Device.set_fname_alert(RED_ALERT)
            mobapp_error_mobile_app_msg += (f"{CRLF_DOT}{mobapp_dname} > "
                                            f"Assigned to {Device.fname_devicename}")

        verified_mobapp_fnames.append(mobapp_fname)
        Gb.mobapp_device_verified_cnt += 1
        Device.verified_MOBAPP = True
        Device.is_mobapp_monitored = True

        # Set raw_model that will get picked up by device_tracker and set in the device registry if it is still
        # at it's default value. Normally, raw_model is set when setting up FamShr if that is available, FmF does not
        # set raw_model since it is only shared via an email addres or phone number. This will also be saved in the
        # iCloud3 configuration file.
        mobapp_fname, raw_model, model, model_display_name = \
                Gb.device_info_by_mobapp_dname[mobapp_dname]

        if ((raw_model and Device.raw_model != raw_model)
                or (model and Device.model != model)
                or (model_display_name and Device.model_display_name != model_display_name)):

            for conf_device in Gb.conf_devices:
                if conf_device[CONF_MOBILE_APP_DEVICE] == mobapp_dname:
                    if raw_model:
                        Device.raw_model = conf_device[CONF_RAW_MODEL] = raw_model
                    if model:
                        Device.model = conf_device[CONF_MODEL] = model
                    if model_display_name:
                        Device.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
                    config_file.write_icloud3_configuration_file()
                    break

        # Setup mobapp entities with data or to be monitored
        Gb.Devices_by_mobapp_dname[mobapp_dname] = Device
        Device.mobapp[DEVICE_TRACKER] = f"device_tracker.{mobapp_dname}"
        Device.mobapp[TRIGGER]        = f"sensor.{Gb.last_updt_trig_by_mobapp_dname.get(mobapp_dname, '')}"
        Device.mobapp[BATTERY_LEVEL]  = Device.sensors['mobapp_sensor-battery_level'] = \
                                        f"sensor.{Gb.battery_level_sensors_by_mobapp_dname.get(mobapp_dname, '')}"
        Device.mobapp[BATTERY_STATUS] = Device.sensors['mobapp_sensor-battery_status'] = \
                                        f"sensor.{Gb.battery_state_sensors_by_mobapp_dname.get(mobapp_dname, '')}"

        device_msg = (  f"{CRLF_CHK}{mobapp_fname}{RARROW}"
                        f"{Device.fname}/{devicename}")
        if len(device_msg) > 40: device_msg += CRLF_TAB
        device_msg += f" ({model_display_name})"

        devices_monitored_cnt += 1
        devices_monitored_msg += device_msg

        # Remove the mobapp device from the list since we know it is tracked
        if mobapp_dname in unmatched_mobapp_devices:
            unmatched_mobapp_devices.pop(mobapp_dname)

    mobapp_interface.setup_notify_service_name_for_mobapp_devices()

    # Devices in the list were not matched with an iCloud3 device or are disabled
    # Setup not monitored message
    for mobapp_dname, mobapp_id in unmatched_mobapp_devices.items():
        devicename = Gb.devicenames_x_mobapp_dnames.get(mobapp_dname, 'unknown')
        Device     = Gb.Devices_by_devicename.get(devicename)
        conf_mobapp_dname = Device.conf_device[CONF_MOBILE_APP_DEVICE] if Device else ''

        try:
            mobapp_fname = Gb.device_info_by_mobapp_dname[mobapp_dname][0]
            mobapp_model = Gb.device_info_by_mobapp_dname[mobapp_dname][3]

        except Exception as err:
            log_exception(err)
            mobapp_fname = f"{RED_ALERT}{mobapp_dname} (UNKNOWN DEVICE)"
            update_alert_sensor(mobapp_dname, "Unknown Mobile App Device")
            mobapp_model = ''

        crlf_sym = CRLF_X
        duplicate_msg = ' (DUPLICATE NAME)' if mobapp_fname in verified_mobapp_fnames else ''
        status_msg = ''
        if Device:
            status_msg = "Not Monitored"

            if mobapp_id in Gb.mobapp_fnames_disabled:
                if Device:
                    status_msg  = ", DISABLED IN MOBAPP"
                    crlf_sym    = CRLF_RED_ALERT
                else:
                    status_msg += ', Disabled in MobApp'
        else:
            crlf_sym = CRLF_HDOT
            # status_msg = 'Not used'

        device_msg = (f"{crlf_sym}{mobapp_fname} ({mobapp_model})")
        if Device:
            Device.set_fname_alert(RED_ALERT)
            device_msg += f", {Device.devicename}, "
            if len(device_msg) > 40: device_msg += CRLF_TAB
        device_msg += f"{status_msg}{duplicate_msg}"

        if crlf_sym == CRLF_X:
            devices_not_monitored_msg += device_msg
        else:
            devices_not_assigned_msg += device_msg

    if devices_not_assigned_msg != '':
        f"{CRLF_X}Not assigned to an iCloud3 Device: "
        f"{devices_not_assigned_msg}"

    evlog_msg =(f"Mobile App Devices > "
                f"{devices_monitored_cnt} of {len(Gb.conf_devices)} monitored"
                f"{devices_monitored_msg}"
                f"{devices_not_monitored_msg}"
                f"{devices_not_assigned_msg}")
    post_event(evlog_msg)

    _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_search_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg)

    return

#--------------------------------------------------------------------
def _scan_for_for_mobapp_device(devicename, Device, conf_mobapp_dname):
    '''
    The conf_mobapp_dname parameter starts with 'ScanFor: '. Scan the list of mobapp
    devices and find the one that starts with the ic3_devicename value

    Return:
        mobapp device_tracker entity name - if it was found
        None - More than one entity or no entities were found
    '''

    conf_mobapp_dname = conf_mobapp_dname.replace('ScanFor: ', '')

    matched_mobapp_devices = [k for k, v in Gb.mobapp_id_by_mobapp_dname.items()
                    if k.startswith(conf_mobapp_dname) and v.startswith('DISABLED') is False]

    Gb.startup_lists['_.matched_mobapp_devices'] = matched_mobapp_devices

    if len(matched_mobapp_devices) == 1:
        return matched_mobapp_devices[0]

    elif len(matched_mobapp_devices) == 0:
        return None

    elif len(matched_mobapp_devices) > 1:
        mobapp_dname = matched_mobapp_devices[-1]
        post_greenbar_msg( f"Mobile App device_tracker entity scan found several devices: "
                            f"{Device.fname_devicename}")

        post_alert( f"DUPLICATE MOBAPP DEVICES FOUND > More than one Device Tracker Entity "
                    f"was found during the scan of the HA Device Registry."
                    f"{CRLF_X}AssignedTo-{Device.fname_devicename}"
                    f"{CRLF}{more_info('mobapp_error_multiple_devices_on_scan')}"
                    f"{CRLF}{'-'*75}"
                    f"{CRLF}Count-{len(matched_mobapp_devices)}, "
                    f"{CRLF}Entities-{', '.join(matched_mobapp_devices)}, "
                    f"{CRLF}Monitored-{mobapp_dname}")

        log_error_msg(f"iCloud3 Error > Mobile App Config Error > Dev Trkr Entity not found "
                    f"during scan_for {conf_mobapp_dname}_???. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")
        return mobapp_dname

    return None

#--------------------------------------------------------------------
def _display_any_mobapp_errors( mobapp_error_mobile_app_msg,
                                mobapp_error_scan_for_msg,
                                mobapp_error_disabled_msg,
                                mobapp_error_not_found_msg):

    if mobapp_error_mobile_app_msg:
        post_greenbar_msg( f"Mobile App Integration missing trigger or battery sensors"
                            f"{mobapp_error_mobile_app_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBILE APP INTEGRATION (Mobile App) SET UP PROBLEM > The Mobile App "
                    f"Integration `last_update_trigger` and `battery_level` sensors are disabled or "
                    f"were not found during the scan of the HA Entities Registry for a Device."
                    f"iCloud3 will use the Mobile App for Zone (State) changes but update triggers and/or "
                    f"battery information will not be available for these devices."
                    f"{mobapp_error_mobile_app_msg}"
                    f"{more_info('mobapp_error_mobile_app_msg')}")

        log_error_msg(f"iCloud3 Error > The Mobile App Integration has not been set up or the "
                    f"battery_level or last_update_trigger sensor entities were not found."
                    f"{mobapp_error_mobile_app_msg}")

    if mobapp_error_scan_for_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_scan_for_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBAPP DEVICE NOT FOUND > An MobApp device_tracker "
                    f"entity was not found in the `Scan for mobile_app devices` in the HA Device Registry."
                    f"{mobapp_error_scan_for_msg}"
                    f"{more_info('mobapp_error_scan_for_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_scan_for_msg}. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_not_found_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity not found"
                            f"{mobapp_error_not_found_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBAPP DEVICE NOT FOUND > The device tracker entity "
                    f"was not found during the scan of the HA Device Registry."
                    f"{mobapp_error_not_found_msg}"
                    f"{more_info('mobapp_error_not_found_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity was not found "
                    f"in the HA Devices List."
                    f"{mobapp_error_not_found_msg}. "
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

    if mobapp_error_disabled_msg:
        post_greenbar_msg( f"Mobile App Config Error > Device Tracker Entity disabled"
                            f"{mobapp_error_disabled_msg.replace(CRLF_X, CRLF_DOT)}")

        post_alert( f"MOBILE APP DEVICE DISABLED > The device tracker entity "
                    f"is disabled so the mobile_app last_update_trigger and bettery_level sensors "
                    f"can not be monitored. iCloud3 will not use the Mobile App for these devices."
                    f"{mobapp_error_disabled_msg}"
                    f"{more_info('mobapp_error_disabled_msg')}")

        log_error_msg(f"iCloud3 Error > Mobile App Device Tracker Entity is disabled and "
                    f"can not be monitored by iCloud3."
                    f"{mobapp_error_disabled_msg}"
                    f"See iCloud3 Event Log > Startup Stage 4 for more info.")

#--------------------------------------------------------------------
def log_debug_stage_4_results():

    # if Gb.is_log_level_debug:
    #     log_debug_msg(f"{Gb.Devices=}")
    #     log_debug_msg(f"{Gb.Devices_by_devicename=}")
    #     log_debug_msg(f"{Gb.conf_devicenames=}")
    #     log_debug_msg(f"{Gb.conf_icloud_dnames=}")
    #     self.devices_not_set_up          = []
    #     self.device_id_by_aadev_dname   = {}       # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
    #     self.aadev_dname_by_device_id   = {}       # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
    #     self.device_info_by_aadev_dname = {}       # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro (iPhone15,2)'}
    #     self.device_model_info_by_aadev_dname  = {}       # {'Gary-iPhone': [raw_model,model,model_display_name]}
    #     self.dup_icloud_dname_cnt
    return

#--------------------------------------------------------------------
def set_devices_verified_status():
    '''
    Cycle thru the Devices and set verified status based on data sources
    '''
    for devicename, Device in Gb.Devices_by_devicename.items():
        Device.was_verified = (Device.verified_ICLOUD
                            or  Device.verified_MOBAPP)

        # If the data source is iCloud and the device is not verified, set the
        # data source to MobApp
        if (Device.was_verified
                and Device.is_data_source_ICLOUD
                and Device.verified_ICLOUD is False
                and Device.verified_MOBAPP):
            Device.primary_data_source = MOBAPP


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def identify_tracked_monitored_devices():
    '''
    Cycle thru the devices and determinine the tracked and monitored ones
    '''
    Gb.Devices_by_devicename_tracked   = {}
    Gb.Devices_by_devicename_monitored = {}
    for devicename, Device in Gb.Devices_by_devicename.items():
        if Device.is_tracked:
            Gb.Devices_by_devicename_tracked[devicename] = Device
        elif Device.is_monitored:
            Gb.Devices_by_devicename_monitored[devicename] = Device

    Gb.startup_lists['Gb.Devices_by_devicename_tracked']   = Gb.Devices_by_devicename_tracked
    Gb.startup_lists['Gb.Devices_by_devicename_monitored'] = Gb.Devices_by_devicename_monitored

#------------------------------------------------------------------------------
def _refresh_all_devices_sensors():
    '''
    Rewrite all device sensors in case anything changed diuring config update
    '''
    for Device in Gb.Devices:
        Device.write_ha_sensors_state()

#------------------------------------------------------------------------------
def setup_trackable_devices():
    '''
    Display a list of all the devices that are tracked and their tracking information
    '''

    from ..mobile_app import mobapp_data_handler

    # Initialize distance_to_other_devices, add other devicenames to this Device's field
    for devicename, Device in Gb.Devices_by_devicename_tracked.items():
        for _devicename, _Device in Gb.Devices_by_devicename.items():
            if devicename != _devicename:
                Device.dist_to_other_devices[_devicename] = [0, 0, 0, '0m/00:00:00']
                Device.near_device_distance         = 0       # Distance to the NearDevice device
                Device.near_device_checked_secs     = 0       # When the nearby devices were last updated
                Device.dist_apart_msg               = ''      # Distance to all other devices msg set in icloud3_main
                Device.dist_apart_msg_by_devicename = {}

        if Device.is_mobapp_monitored:
            Gb.used_data_source_MOBAPP = True

            mobapp_attrs = mobapp_data_handler.get_mobapp_device_trkr_entity_attrs(Device)
            if mobapp_attrs:
                mobapp_data_handler.update_mobapp_data_from_entity_attrs(Device, mobapp_attrs)

        # Set a flag indicating there is a tracked device that does not use the Mobile App
        elif Device.is_tracked:
            Gb.device_not_monitoring_mobapp = True

        # Device is not in configured Apple acct if it was not matched
        username     = Device.conf_apple_acct_username
        apple_acct   = username_id(username)
        icloud_dname = Device.conf_icloud_dname

        # Get Apple acct owner from AppleAcct
        if username in Gb.AppleAcct_by_username:
            _AppleAcct = Gb.AppleAcct_by_username[username]

            if (_AppleAcct.login_successful
                    and icloud_dname not in _AppleAcct.device_id_by_aadev_dname
                    and Gb.internet_error is False):
                Device.verified_ICLOUD = False
                update_alert_sensor(Device.fname, (
                        f"{icloud_dname} Not in Apple Acct ({apple_acct})"))

    if Gb.use_data_source_ICLOUD is False:
        if Gb.conf_data_source_ICLOUD:
            post_event("Data Source > Apple Account not available")
        else:
            post_event("Data Source > Apple Account not used")

    if Gb.conf_data_source_MOBAPP is False:
        post_event("Data Source > Mobile App not used")
