#------------------------------------------------------------------------------
#
#   iCloud3 Apple Account and Device Setup -- Startup Stages 3-4
#
#   Moved verbatim from start_ic3.py. Modules that import start_ic3 at module
#   level (config_file, entity_reg_util, device, apple_acct*) are imported
#   inside the functions that use them so this module can be loaded without
#   re-entering start_ic3.
#
#------------------------------------------------------------------------------
from ..global_variables import GlobalVariables as Gb
from ..const            import (CHECK_MARK,
                                CONF_AADEV_DEVICE_ID, CONF_AADEV_NAME, CONF_APPLE_ACCOUNT,
                                CONF_AWAY_TIME_ZONE_1_DEVICES, CONF_AWAY_TIME_ZONE_1_OFFSET,
                                CONF_AWAY_TIME_ZONE_2_DEVICES, CONF_AWAY_TIME_ZONE_2_OFFSET,
                                CONF_DEVICE_TYPE, CONF_FNAME, CONF_IC3_DEVICENAME,
                                CONF_LOCATE_ALL, CONF_MOBILE_APP_DEVICE,
                                CONF_MODEL, CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL,
                                CONF_SERVER_LOCATION, CONF_TRACKING_MODE,
                                CRLF, CRLF_CHK, CRLF_DOT, CRLF_RED_ALERT2, CRLF_RED_X,
                                CRLF_SP5_DOT, CRLF_STAR,
                                DEVICE_TRACKER, DEVICE_TYPE_DN, DOT, EVLOG_ALERT,
                                HOME, ICLOUD, INACTIVE, INACTIVE_SYMB, LINK, MOBAPP,
                                NBSP2, NBSP6, RARROW, RED_ALERT, YELLOW_ALERT,
                                )

from ..utils.utils      import (dict_del, dict_sort, is_empty, isnot_empty,
                                list_add, list_del, list_sort, list_to_str,
                                username_id, zone_dname, )
from ..utils.messaging  import (broadcast_info_msg, clear_repair_issues,
                                log_error_msg, log_exception,
                                post_alert, post_dotted_line, post_error_msg, post_event,
                                post_greenbar_msg, post_monitor_msg, post_repair_issue,
                                register_repair_fix_handler, update_alert_sensor, )

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   ICLOUD3 STARTUP MODULES -- STAGE 3
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


#------------------------------------------------------------------------------
#
#   CREATE THE DEVICES OBJECT FROM THE DEVICE PARAMETERS IN THE
#   CONFIGURATION FILE
#
#   Set up the devices to be tracked and it's associated information
#   for the configuration line entry. This will fill in the following
#   fields based on the extracted devicename:
#       device_type
#       friendly_name
#       sensor.picture name
#       device tracking flags
#       tracked_devices list
#   These fields may be overridden by the routines associated with the
#   operating mode (icloud, mobapp)
#
#------------------------------------------------------------------------------
def setup_validate_apple_accts_upw():
    return

    from ..apple_acct.apple_acct_upw import ValidateAppleAcctUPW

    if Gb.ValidateAppleAcctUPW is None:
        Gb.ValidateAppleAcctUPW = ValidateAppleAcctUPW()
        Gb.valid_upw_by_username = {}

#------------------------------------------------------------------------------
def create_Devices_object():
    from ..device import iCloud3_Device
    from ..utils import entity_reg_util as er_util

    try:
        # _set_ha_device_id_x_devicename()
        er_util.set_ha_device_id_x_devicename()

        old_Devices_by_devicename      = Gb.Devices_by_devicename.copy()
        Gb.Devices                     = []
        Gb.Devices_by_devicename       = {}
        Gb.Devices_by_username         = {}
        Gb.conf_devicenames            = []
        Gb.conf_icloud_dnames          = []
        Gb.devicenames_by_aadev_dname = {}
        Gb.aadev_dnames_by_devicename= {}
        Gb.startup_alerts_by_source    = {}

        # Update the ha_device_id_x_devicename dict and correct any
        # disabled device conflicts between iCloud3 and the ha_device_reg

        for conf_device in Gb.conf_devices:
            devicename   = conf_device[CONF_IC3_DEVICENAME]
            device_fname = conf_device[CONF_FNAME]
            aadev_name = conf_device[CONF_AADEV_NAME]
            username     = conf_device[CONF_APPLE_ACCOUNT]
            apple_acct   = username_id(username)

            # # Device's Apple Acct was not found in the Apple Accts list. It is invalid or
            # # the password has not been verified yet
            # if (Gb.use_data_source_ICLOUD
            #         and username != ''
            #         and aadev_name != 'None'
            #         and username not in Gb.valid_upw_by_username):
            #     conf_apple_acct, _idx = config_file.conf_apple_acct(username)
            #     if _idx < 0:
            #         error_msg = f"Unknown Apple Acct ({apple_acct})"
            #         post_alert( f"{device_fname} > {error_msg}")
            #         update_alert_sensor(device_fname, error_msg)

            #     else:
            #         # Open Apple Acct, Create Apple Acct Objects and login
            #         password = conf_apple_acct[CONF_PASSWORD]
            #         valid_upw = Gb.ValidateAppleAcctUPW.validate_username_password(username, password)

            #         Gb.valid_upw_by_username[username] = valid_upw

            if devicename == '':
                post_greenbar_msg(f"HA device_tracker entity id not configured for {aadev_name}")
                post_alert( f"CONFIGURATION ALERT > The device_tracker entity id (devicename) "
                            f"has not been configured for {aadev_name}/"
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}")
                continue

            Gb.conf_icloud_dnames.append(aadev_name)
            broadcast_info_msg(f"Setting up Device > {devicename}")

            # Do not set up inactive device or one disabled in HA
            if devicename in Gb.ha_disabled_by_by_devicename:
                do_not_track_reason = f'{INACTIVE_SYMB}HA.DISABLED'
            elif conf_device[CONF_TRACKING_MODE] == INACTIVE:
                do_not_track_reason = f'{INACTIVE_SYMB}INACTIVE'
            else:
                do_not_track_reason = ''
            if do_not_track_reason:
                post_event( f"{INACTIVE_SYMB}{conf_device[CONF_FNAME]} ({devicename}) > "
                            f"{DEVICE_TYPE_DN(conf_device[CONF_DEVICE_TYPE])}, "
                            f"{do_not_track_reason}"
                            f"{CRLF_SP5_DOT}Apple Device-{aadev_name} ({conf_device[CONF_MODEL_DISPLAY_NAME]})"
                            f"{CRLF_SP5_DOT}MobApp Entity-{conf_device[CONF_MOBILE_APP_DEVICE]}")
                continue

            # This list is based on the configuration, it will be rebuilt when the devices are verified
            # after the iCloud data has been read. It is also rebuild in config_flow when a device is updated
            Gb.devicenames_by_aadev_dname[aadev_name] = devicename
            Gb.aadev_dnames_by_devicename[devicename] = aadev_name

            # Reinitialize or add device, preserve the Sensor object if reinitializing
            if devicename in old_Devices_by_devicename:
                post_monitor_msg(f"INITIALIZE Device > {devicename}")
                Device = old_Devices_by_devicename[devicename]
                Device.__init__(devicename, conf_device)

            else:
                post_monitor_msg(f"ADD Device > {devicename}")
                Device = iCloud3_Device(devicename, conf_device)

            Gb.Devices.append(Device)
            Gb.conf_devicenames.append(devicename)
            Gb.Devices_by_devicename[devicename] = Device

            if conf_device[CONF_TRACKING_MODE] ==  INACTIVE:
                continue

            # If Apple acct specified, make sure it is configured and this device is available
            if Device.conf_apple_acct_username in ['', 'None']:
                apple_acct_msg = '✪ NONE'

            elif Gb.internet_error:
                apple_acct_msg =f"{Device.conf_apple_acct_username_id}, INTERNERT UNAVAILABLE"

            elif Device.conf_apple_acct_username not in Gb.valid_upw_by_username:
                apple_acct_msg =f"{RED_ALERT}{Device.conf_apple_acct_username}, UNKNOWN APPLE ACCT"

            elif Gb.valid_upw_by_username.get(Device.conf_apple_acct_username, False) is False:
                apple_acct_msg = f"{RED_ALERT}{Device.conf_apple_acct_username}, INVALID USERNAME/PW"

            else:
                apple_acct_msg = Device.conf_apple_acct_username_id

            #  Build the device's configuration evlog message
            # apple_acct_msg = f"{CRLF_SP5_DOT}Apple Account: {apple_acct_msg}"
            if Device.conf_icloud_dname:
                icloud_dev_msg = f"{Device.conf_icloud_dname} ({Device.model_display_name})"
            else:
                icloud_dev_msg = '✪ NONE'
            mobapp_dev_msg = Device.mobapp[DEVICE_TRACKER] \
                                    if Device.mobapp[DEVICE_TRACKER] else '✪ NONE'
            if ((apple_acct_msg == '✪ NONE' or icloud_dev_msg == '✪ NONE')
                    and mobapp_dev_msg == '✪ NONE'):
                monitored_msg = f"{RED_ALERT}NO DATA SOURCE"
            elif Device.is_monitored:
                monitored_msg = 'Monitored'
            else:
                monitored_msg = 'Tracked'

            evlog_msg = (   f"{CHECK_MARK}{Device.fname_devicename} > {Device.devtype_fname}, {monitored_msg}"
                            f"{CRLF_SP5_DOT}Apple Account: {apple_acct_msg}"
                            f"{CRLF_SP5_DOT}Apple Device: {icloud_dev_msg}"
                            f"{CRLF_SP5_DOT}MobApp Entity: {mobapp_dev_msg}")

            if Device.track_from_base_zone != HOME:
                evlog_msg += f"{CRLF_SP5_DOT}Primary 'Home' Zone: {zone_dname(Device.track_from_base_zone)}"
            if Device.track_from_zones != [HOME]:
                evlog_msg += f"{CRLF_SP5_DOT}Track from Zones: {list_to_str(Device.track_from_zones)}"
            post_event(evlog_msg)

            # Initialize device_tracker entity to display before AppleAcct starts up
            Device.write_ha_device_tracker_state()

    except Exception as err:
        log_exception(err)

    _verify_away_time_zone_devicenames()
    _log_device_dictionaries()

    return

#--------------------------------------------------------------------
def update_devices_non_tracked_fields():
    for conf_device in Gb.conf_devices:
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if Device := Gb.Devices_by_devicename.get(devicename):
            Device.initialize_non_tracking_config_fields(conf_device)

#--------------------------------------------------------------------
def _log_device_dictionaries():

    Gb.startup_lists['Gb.Devices']                     = Gb.Devices
    Gb.startup_lists['Gb.DeviceTrackers_by_devicename']= Gb.DeviceTrackers_by_devicename
    Gb.startup_lists['Gb.Devices_by_devicename']       = Gb.Devices_by_devicename
    Gb.startup_lists['Gb.ha_device_id_x_devicename']  = Gb.ha_device_id_x_devicename
    Gb.startup_lists['Gb.conf_devicenames']            = Gb.conf_devicenames
    Gb.startup_lists['Gb.conf_icloud_dnames']          = Gb.conf_icloud_dnames
    Gb.startup_lists['Gb.devicenames_by_aadev_dname'] = Gb.devicenames_by_aadev_dname
    Gb.startup_lists['Gb.icloud_dname_by_devicenames'] = Gb.aadev_dnames_by_devicename

#--------------------------------------------------------------------
def _verify_away_time_zone_devicenames():
    '''
    Verify the devicenames in the Away time zone fields
    '''
    from ..startup import config_file

    update_conf_file_flag = False

    if ('none' in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]
            or 'all' in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]):
        pass
    else:
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                list_del(Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES], devicename)
                update_conf_file_flag = True

        if Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_1_OFFSET] = 0

    if ('none' in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]
            or 'all' in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]):
        pass
    else:
        for devicename in Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES]:
            if devicename not in Gb.Devices_by_devicename:
                list_del(Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES], devicename)
                update_conf_file_flag = True

        if Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] == []:
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_DEVICES] = ['none']
            Gb.conf_general[CONF_AWAY_TIME_ZONE_2_OFFSET] = 0

    if update_conf_file_flag:
        config_file.write_icloud3_configuration_file()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SET UP ICLOUD3 ACCOUNTS/DEVICES -- STAGE 4
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_into_apple_accounts():
    '''
    Verify that all Apple Account AppleAcct objects have been created
    '''
    from ..apple_acct import apple_acct_support as aas
    from ..startup import config_file

    if Gb.use_data_source_ICLOUD is False:
        return False

    if is_empty(Gb.conf_usernames):
        return False

    # Setup access tp the Apple acct if is is not already setup or anything
    # has changed
    aa_login_error = ''
    results_msg    = ''
    alert_msg      = ''
    for username in Gb.conf_usernames:
        conf_apple_acct, _idx = config_file.conf_apple_acct(username)
        password              = Gb.AppleAcct_password_by_username[username]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices    = conf_apple_acct[CONF_LOCATE_ALL]

        post_dotted_line()
        post_event( f"Setting up Apple Account > {username_id(username)}")

        AppleAcct = Gb.AppleAcct_by_username.get(username)

        # Initial check to see if AppleAcct is available
        can_reuse_AppleAcct = (
            Gb.was_icloud3_reloaded is True
            and AppleAcct is not None
            and isnot_empty(AppleAcct.AADevData_by_device_id)
            and username == AppleAcct.username
            and password == AppleAcct.password
            and apple_server_location == AppleAcct.apple_server_location
            and locate_all_devices == AppleAcct.locate_all_devices)

        # Second check to see if AppleAcct is has no exceptions and can be reused
        if can_reuse_AppleAcct:
            can_reuse_AppleAcct = (
                AppleAcct.is_AADevices_setup_complete
                and AppleAcct.is_authenticated
                and aas.is_authentication_2fa_code_needed(AppleAcct) is False
                and Gb.AppleAcct_error_by_username.get(username, False) is False
                and Gb.iCloudSession_by_username.get(username, None is not None)
                and Gb.valid_upw_by_username.get(username, False)
                and AppleAcct.login_successful is True
                and AppleAcct.auth_failed_503 is False)

        if Gb.valid_upw_by_username.get(username) is False:
            post_alert(f"Logged Failed, Invalid Username/Password")

        elif can_reuse_AppleAcct is False:
            AppleAcct = aas.log_into_apple_account(
                                        username,
                                        password,
                                        apple_server_location,
                                        locate_all_devices)

            if AppleAcct:
                apple_login_msg = 'Login Successful'

            else:
                post_event( f"{CRLF_RED_X} Login Failed, "
                            f"Server Loc-{apple_server_location}")
                alert_msg = EVLOG_ALERT
                update_alert_sensor(username_id(username), "Apple Acct Login Failed")

        else:
            apple_login_msg = 'Already logged in'

        if AppleAcct and AppleAcct.login_successful:
            if AppleAcct.is_authenticated:
                reauth_in_days, reauth_msg = AppleAcct.get_next_reauth_in_days_info_msg()
                AppleAcct.issue_reauth_in_days_alert_msg()
                post_event( f"{apple_login_msg}"
                            f"{CRLF_DOT}Authentication Method-{AppleAcct.login_auth_method}"
                            f"{CRLF_DOT}{reauth_msg}")

            setup_tracked_devices_for_icloud(AppleAcct)

        post_event( f"Setting up Apple Account > {username_id(AppleAcct.username_id)}, Complete")

    Gb.startup_lists['Gb.AppleAcct_error_by_username'] = Gb.AppleAcct_error_by_username

    # Check if the pyicloud_ic3_interface detected the internet is down
    if Gb.internet_error:
        return False

    if (aa_login_error
            or AppleAcct is None
            or is_empty(AppleAcct.AADevData_by_device_id)):
        pass

    elif isnot_empty(Gb.devices_without_location_data):
        post_event( f"Apple Acct > Location data is not available for:"
                    f"{CRLF}{NBSP6}{DOT}{list_to_str(Gb.devices_without_location_data)}")
        post_dotted_line()

    return True

#------------------------------------------------------------------
def are_all_devices_verified(retry=False):
    '''
    See if all tracked devices are verified.

    Arguments:
        retry   - True  - The verification was retried
                - False - This is the first time the verification was done

    Return:
        True  - All were verifice
        False - Some were not verified
    '''


    # Get a list of all tracked devices that have not been set up by icloud or the Mobile App
    unverified_devices = [Device.fname_devicename
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if Device.was_verified is False and Device.isnot_inactive]
    unverified_device_usernames = [Device.conf_apple_acct_username
                            for devicename, Device in Gb.Devices_by_devicename.items()
                            if (Device.was_verified is False
                                    and Device.isnot_inactive)]

    Gb.usernames_setup_error_retry_list   = list(set(unverified_device_usernames))
    Gb.devicenames_setup_error_retry_list = list(set(unverified_devices))

    Gb.startup_lists['_.usernames_setup_error_retry_list']   = Gb.usernames_setup_error_retry_list
    Gb.startup_lists['_.devicenames_setup_error_retry_list'] = Gb.devicenames_setup_error_retry_list

    if is_empty(unverified_devices):
        return True

    if retry:
        post_greenbar_msg("1444 Some Tracked Devices could not be verified. Restart may be needed.")
        alert_msg = ("Some Tracked Devices could not be verified. Review and correct "
                    "any configuration errors. Then restart iCloud3")
    else:
        alert_msg = "UNVERIFIED DEVICES ALERT > Some Tracked Devices could not be verified."
    alert_msg += (f"{CRLF_DOT}Unverified Devices > {', '.join(unverified_devices)}")
    post_alert(alert_msg)

    return False

#--------------------------------------------------------------------
def setup_tracked_devices_for_icloud(AppleAcct):
    '''
    The Family Share device data is available from AppleAcct when logging into the iCloud
    account. This routine will get all the available Apple devices from this data.
    The raw data devices are then cycled through and matched with the conf tracked devices.
    Their status is displayed on the Event Log. The device is also marked as verified.

    Arguments:
        AppleAcct: Object containing data to be processed. This might be from Gb.AppleAcct (normal/default)
                    or the one created in config_flow if the username was changed.
    '''

    if Gb.conf_data_source_ICLOUD is False:
        post_event("Apple Account > Not used as a data source")
        return

    if Gb.conf_icloud_device_cnt == 0:
        return

    try:
        missing_aadev_devices = _get_conf_devices_apple_did_not_locate(AppleAcct)
        if isnot_empty(missing_aadev_devices):
            _refresh_icloud_data_retry(AppleAcct, missing_aadev_devices)

        _set_device_data_source(AppleAcct)
        _verify_conf_apple_device_parameters(AppleAcct)
        _match_AppleAcct_devices_to_Device(AppleAcct)

        _post_evlog_apple_acct_devices_info(AppleAcct)

    except Exception as err:
        log_exception(err)

    owner = AppleAcct.username_base
    Gb.startup_lists[f"{owner}.AppleAcct.device_id_by_aadev_dname"] = \
                        {k: v[:10] for k, v in AppleAcct.device_id_by_aadev_dname.items()}
    Gb.startup_lists[f"{owner}.AppleAcct.aadev_dname_by_device_id"] = \
                        {k[:10]: v for k, v in AppleAcct.aadev_dname_by_device_id.items()}
    Gb.startup_lists[f"Gb.Devices_by_icloud_device_id"]     = \
                        {k[:10]: v for k, v in Gb.Devices_by_icloud_device_id.items()}

#----------------------------------------------------------------------------
def _get_conf_devices_apple_did_not_locate(AppleAcct):
    aadev_names = [_AADevData.name for _AADevData in AppleAcct.AADevData_items]
    missing_aadev_devices = {}
    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        devicename = conf_device[CONF_IC3_DEVICENAME]
        device_id  = conf_device[CONF_AADEV_DEVICE_ID]
        aadev_name = conf_device[CONF_AADEV_NAME]

        if (aadev_name not in aadev_names
                and device_id not in AppleAcct.AADevData_by_device_id):
            missing_aadev_devices[devicename] = aadev_name

    return missing_aadev_devices

#----------------------------------------------------------------------------
def _verify_conf_apple_device_parameters(AppleAcct):
    '''
    Check the apple acct devices name and device_id. Update the conf if the name
    was changed or if the name was assigned to another device. Then see if a newer
    device replaced the tracked device (_check_for_replacement_device).
    '''
    # Test Code - Do not update a newer device when starting up. This will test
    # detected a newer device when the device data is refreshed
    # if Gb.is_icloud3_initial_startup:
    #     return

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        try:
            conf_device_id  = conf_device[CONF_AADEV_DEVICE_ID]
            conf_aadev_name = conf_device[CONF_AADEV_NAME]
            broadcast_info_msg(f"Verifying Apple Device > {conf_aadev_name}")

            # Get Device specified in config file using the device_id
            AADevData = AppleAcct.AADevData_by_device_id.get(conf_device_id)

            # The config AA device was found using the device_id but this device is now a
            # duplicate. This means a newer device with the same name and owner has
            # been added to the Apple Acct (current config=iPhone16, AA data=iPhone18).
            # Change the ic3_devicename to now use the newer device .
            if AADevData and AADevData.is_duplicate_dname:
                NewerAADevData = _find_newer_same_name_device(AppleAcct, AADevData)
                if NewerAADevData:
                    _change_config_to_new_device(AppleAcct, NewerAADevData, conf_device)
                continue

            # The config AA device with this device_id is no longer in the Apple Acct
            # device list (it was removed), get the AA device that now has the config
            # name (Gary-iPhone) if it exists
            if AADevData is None:
                device_id  = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
                AADevData  = AppleAcct.AADevData_by_device_id.get(device_id)

                # An AA device was found with the same name, change config to it
                if AADevData:
                    _change_config_to_new_device(AppleAcct, AADevData, conf_device)

                # The AA device with the config name (Gary-iPhone) is no longer in
                # the Apple Acct devices list. Make sure the login was successful and
                # all devices were returned instead of Apple returning a partial device list
                elif AppleAcct.login_successful is False:
                    post_alert( f"{conf_device[CONF_FNAME]} > "
                                f"Device was not found"
                                f"{CRLF_DOT}{conf_aadev_name}, "
                                f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")
                continue

            # The config file device_id was found, see if it was renamed. The dname has
            # the owner's name if another family member has a device with the same name.
            if conf_aadev_name != AADevData.dname:
                _change_config_to_new_device_name(AppleAcct, conf_device, AADevData.dname)
                continue

            # if conf_device[CONF_TRACKING_MODE] != INACTIVE:
            # The AA device was not found using the config name or replaced with a device
            # with the same name. Review the devices available and see if there is a
            # device with another name that matches the parameters of the one being checked
            _check_for_replacement_device(AppleAcct, conf_device, AADevData)

        except Exception as err:
            log_exception(err)
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Error verifying Apple Acct Device"
                        f"{CRLF_DOT}{conf_aadev_name}, "
                        f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")

#............................................................................
def _find_newer_same_name_device(AppleAcct, AADevData):
    '''
    Return the device with the same name and owner that is not a duplicate. It is
    the newest device with that name (_resolve_duplicate_dnames).
    '''
    for _AADevData in AppleAcct.AADevData_by_device_id.values():
        if (_AADevData
                and _AADevData.active
                and _AADevData.is_duplicate_dname is False
                and _AADevData.name == AADevData.name
                and _AADevData.prs_id == AADevData.prs_id):
            return _AADevData

    return None

#............................................................................
def _check_for_replacement_device(AppleAcct, conf_device, AADevData):
    '''
    See if a newer device that is not tracked replaced the tracked device. We are
    chedking for a device that was not restored from a backup when the device was
    being set up. The 'configure as new' gets Apple's default name ("Lillian's Apple Watch").

    Candidates: Same owner and device type (not AirPods or accessories), a higher
        model number, not tracked by an iCloud3 device.
    Name match: The candidate's name is the tracked device's name without the model
        or possessive ('s) (device_name_parser.owner_device_name_key).
    Retired: The tracked device was unpaired, erased or is being removed.
    Offline: The tracked device has been offline for more than an hour.

        Name match, retired or offline  - Track the newer device
        Name match, both are online     - Repairs issue, Submit tracks the newer device
        No name match, retired, 1 found - Repairs issue, Submit tracks the newer device
        More than 1 found               - Repairs notice listing them

    An HA Repair Issue is created notifying the user of the config change if there
    is no clear winner.

    Issues that no longer apply are removed. Issues posted again keep their HA
    'Ignore' state.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname      = conf_device[CONF_FNAME]
    issue_id_prefix = f"device_replaced_{devicename}"

    # The same rules are used by AADevices._request_restart_if_tracked_device_replaced
    # during a refresh so a restart it requests reassigns the device here
    candidates, name_matches = AppleAcct.AADevices.find_replacement_devices(AADevData)
    if candidates is None:
        clear_repair_issues(issue_id_prefix)
        return

    old_device_msg = f"{AADevData.name} ({AADevData.model_display_name})"
    old_device_status_msg = (
                'unpaired or erased' if AADevData.is_retired else
                'offline for more than 1 hour' if AADevData.is_offline_stale else
                'online and available')

    issue_id = None

    # If there is only 1 match, and the config device is retired or offline,
    # change the config to the new device
    if len(name_matches) == 1:
        NewAADevData = name_matches[0]
        if AADevData.is_retired or AADevData.is_offline_stale:
            _change_config_to_new_device(AppleAcct, NewAADevData, conf_device)
        else:
            issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADevData,
                                                NewAADevData, old_device_status_msg)

    # If there are no matches but there is 1 candidate device that may work, the config
    # is not changed but a Repair Issue is created. Submitting the Repair Issue will
    # accept the new device as the replacement and update the config
    elif len(name_matches) == 0 and len(candidates) == 1 and AADevData.is_retired:
        issue_id = _post_repair_issue_aa_device_assignment(
                                                AppleAcct, conf_device, AADevData,
                                                candidates[0], old_device_status_msg)

    elif len(name_matches) > 1 or (len(candidates) > 1 and AADevData.is_retired):
        found_AADevData_items = name_matches or candidates
        found_devices_msg     = CRLF_DOT.join([f"{_AADevData.name} ({_AADevData.model_display_name})"
                                                for _AADevData in found_AADevData_items])
        issue_id = _post_repair_issue_no_aa_device_assignment(
                                                issue_id_prefix, devicename, dev_fname,
                                                old_device_msg, old_device_status_msg,
                                                found_devices_msg)

    clear_repair_issues(issue_id_prefix, keep_issue_ids=[issue_id])

#............................................................................
def _post_repair_issue_aa_device_assignment(AppleAcct, conf_device, AADevData, NewAADevData,
                                            old_device_status_msg):
    '''
    Post the Repairs issue asking to track the newer device. Submit runs
    _fix_repair_issue_aa_device_assignment.
    '''
    devicename = conf_device[CONF_IC3_DEVICENAME]
    dev_fname  = conf_device[CONF_FNAME]
    name_model = f"{NewAADevData.name} ({NewAADevData.model_display_name})"

    issue_id = post_repair_issue(
                issue_id   = f"device_replaced_{devicename}_{NewAADevData.device_id8}",
                alert_key  = devicename,
                title      = f"{dev_fname}, Newer Apple Device detected",
                alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                f"The iCloud3 Configuration needs to be updated to use "
                                f"the newer device."
                                f"{CRLF}{CRLF}Change Apple Device for *{dev_fname}*:"
                                f"{CRLF_DOT}{AADevData.name} ({AADevData.model_display_name}){RARROW}"
                                f"{NewAADevData.name} ({NewAADevData.model_display_name})"
                                f"{CRLF}{CRLF}Click Submit to confirm this selection and "
                                f"update the configuration for *{dev_fname}*"),
                fix_action = 'reassign_apple_device',
                fix_data   = {  'username': AppleAcct.username,
                                'device_id': NewAADevData.device_id,
                                'name_model': name_model})

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF_DOT}{AADevData.name} ({AADevData.model_display_name}){RARROW}"
                f"{NewAADevData.name} ({NewAADevData.model_display_name})")

    return issue_id

#............................................................................
def _fix_repair_issue_aa_device_assignment(fix_data):
    '''
    Repairs Submit handler for _post_repair_issue_aa_device_assignment. Track the newer
    device and restart iCloud3. Runs in an executor thread.
    '''
    devicename  = fix_data.get('devicename')
    name_model  = fix_data.get('name_model')
    AppleAcct   = Gb.AppleAcct_by_username.get(fix_data.get('username'))
    AADevData   = AppleAcct.AADevData_by_device_id.get(fix_data.get('device_id')) if AppleAcct else None
    conf_device = [_conf_device for _conf_device in Gb.conf_devices
                            if _conf_device[CONF_IC3_DEVICENAME] == devicename]

    if AADevData is None or conf_device == []:
        post_alert(devicename,  f"HA Repairs > Newer Apple Device is no longer available, "
                                f"{CRLF_DOT}{name_model}")
        return False

    _change_config_to_new_device(AppleAcct, AADevData, conf_device[0], post_notice=False)

    post_event(devicename,
                f"HA Repairs > Newer Apple Device will now be tracked, "
                f"{AADevData.name} ({AADevData.model_display_name}), Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('reassign_apple_device', _fix_repair_issue_aa_device_assignment)

#............................................................................
def _fix_repair_issue_clear_mobapp_mapping(fix_data):
    '''
    Repairs Submit handler for a mobile_app_device that is not in the HA Mobile
    App integration. Clear the mapping so iCloud tracking is used, then restart.
    Runs in an executor thread.
    '''
    from ..startup import config_file

    devicename = fix_data.get('devicename')
    conf_device = next((_conf_device for _conf_device in Gb.conf_devices
                        if _conf_device[CONF_IC3_DEVICENAME] == devicename), None)
    if conf_device is None:
        return False

    old_mobapp_dname = conf_device.get(CONF_MOBILE_APP_DEVICE, '')
    conf_device[CONF_MOBILE_APP_DEVICE] = 'None'
    config_file.write_icloud3_configuration_file()

    post_event(devicename,
                f"HA Repairs > Mobile App device cleared ({old_mobapp_dname}), "
                f"Restarting iCloud3")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('clear_mobapp_mapping', _fix_repair_issue_clear_mobapp_mapping)

#............................................................................
def _fix_repair_issue_update_ic3_device_name(fix_data):
    '''
    Repairs Submit handler for a device renamed in HA. Copy the HA device name into
    the iCloud3 configuration as the display name, then restart. Runs in an
    executor thread.
    '''
    from ..startup import config_file

    devicename  = fix_data.get('devicename')
    new_name    = (fix_data.get('new_name') or '').strip()
    conf_device = next((_conf_device for _conf_device in Gb.conf_devices
                        if _conf_device[CONF_IC3_DEVICENAME] == devicename), None)
    if conf_device is None or new_name == '':
        return False

    conf_device[CONF_FNAME] = new_name
    config_file.write_icloud3_configuration_file()

    post_event(devicename, f"HA Repairs > iCloud3 display name updated to {new_name}")
    Gb.was_icloud3_restart_requested = True

    return True

register_repair_fix_handler('update_ic3_device_name', _fix_repair_issue_update_ic3_device_name)

#............................................................................
def  _post_repair_issue_no_aa_device_assignment(
                                        issue_id_prefix, devicename, dev_fname,
                                        old_device_msg, old_device_status_msg,
                                        found_devices_msg):

    issue_id = post_repair_issue(
                    issue_id   = f"{issue_id_prefix}_multiple",
                    alert_key  = devicename,
                    title      = f"{dev_fname}, Newer Apple Devices detected",
                    alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                    f"Several candidates have been identifiedd and the "
                                    f"correct one could not be selected."
                                    f"{CRLF}{CRLF}Configured Apple Device for *{dev_fname}*:"
                                    f"{CRLF_DOT}{old_device_msg} ({old_device_status_msg})"
                                    f"{CRLF}{CRLF}Available Devices:"
                                    f"{CRLF_DOT}{found_devices_msg}"
                                    f"{CRLF}{CRLF}Select the correct Apple Device on the *iCloud3 "
                                    f"Update Device* Configuration screen for *{dev_fname}*."))

    post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Current device:"
                f"{CRLF_DOT}{old_device_msg} ({old_device_status_msg})"
                f"{CRLF}Candidates:"
                f"{CRLF_DOT}{found_devices_msg}")

    # Returned so _check_for_replacement_device keeps this issue instead of removing it
    return issue_id

#............................................................................
def _change_config_to_new_device(AppleAcct, AADevData, conf_device, post_notice=True):
    '''
    Track the newer device. Update the iCloud3 configuration with the new device's
    device_id, name and model.

    post_notice:
        True - Post the 'Newer Apple Device detected' notice in HA Repairs, the
            alerts sensor and the Event Log. Submit acknowledges and removes it.
        False - The change was requested in HA Repairs
    '''
    from ..startup import config_file

    try:
        devicename     = conf_device[CONF_IC3_DEVICENAME]
        dev_fname      = conf_device[CONF_FNAME]
        old_aadev_name = conf_device[CONF_AADEV_NAME]
        old_model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]

        conf_device[CONF_AADEV_DEVICE_ID]    = AADevData.device_id
        conf_device[CONF_DEVICE_TYPE]        = AADevData.device_type.lower()
        conf_device[CONF_RAW_MODEL]          = AADevData.raw_model
        conf_device[CONF_MODEL]              = AADevData.model
        conf_device[CONF_MODEL_DISPLAY_NAME] = AADevData.model_display_name
        _update_Device_model_fields(conf_device)

        if old_aadev_name != AADevData.dname:
            _change_config_to_new_device_name(AppleAcct, conf_device, AADevData.dname,
                                                write_config_file=False, post_msg=False)

        config_file.write_icloud3_configuration_file()

        AADevData.startup_msg = 'UPGRADED'

        if post_notice:
            post_repair_issue(
                        issue_id   = f"device_reassigned_{devicename}_{AADevData.device_id8}",
                        alert_key  = devicename,
                        title      = f"{dev_fname}, Newer Apple Device detected",
                        alert_msg  = (  f"A newer version of one of your Apple Devices is available. "
                                        f"The iCloud3 configuration was updated to use "
                                        f"the newer device."
                                        f"{CRLF}{CRLF}Updated Apple Device for *{dev_fname}*:"
                                        f"{CRLF_DOT}{old_aadev_name} ({old_model_display_name}){RARROW}"
                                        f"{AADevData.name} ({AADevData.model_display_name})"
                                        f"{CRLF}{CRLF}If this is wrong, change the name of the device "
                                        f"in the *Settings App* to another name. Then select it on the "
                                        f"*iCloud3 Update Device* Configuration screen for *{dev_fname}*"))

            post_alert(f"{dev_fname} > "
                f"Newer Apple Device detected, HA Repair issue created"
                f"{CRLF}Configuration updated, New device will be tracked:"
                f"{CRLF_DOT}{old_aadev_name} ({old_model_display_name}){RARROW}"
                f"{AADevData.name} ({AADevData.model_display_name})")

    except Exception as err:
        log_exception(err)

#............................................................................
def _update_Device_model_fields(conf_device):
    '''
    The Device and its device_tracker entity are set up from the configuration in
    Stage 2, before the Apple acct devices are verified and the newer device is
    assigned. Update their model fields and the HA device registry model from the
    updated configuration.
    '''
    from ..utils import entity_reg_util as er_util

    devicename = conf_device[CONF_IC3_DEVICENAME]

    for _Device in [Gb.Devices_by_devicename.get(devicename),
                    Gb.DeviceTrackers_by_devicename.get(devicename)]:
        if _Device is None:
            continue
        _Device.device_type        = conf_device[CONF_DEVICE_TYPE]
        _Device.raw_model          = conf_device[CONF_RAW_MODEL]
        _Device.model              = conf_device[CONF_MODEL]
        _Device.model_display_name = conf_device[CONF_MODEL_DISPLAY_NAME]

    er_util.update_device_model(devicename, conf_device[CONF_RAW_MODEL])

#............................................................................
def _change_config_to_new_device_name(AppleAcct, conf_device, new_icloud_dname,
                                        write_config_file=True, post_msg=True):
    from ..startup import config_file

    try:
        # Update the iCloud3 configuration file with the new Apple devicename
        # Set new icloud name in config and internal table, remove the old one:
        old_icloud_dname = conf_device[CONF_AADEV_NAME]
        devicename = conf_device[CONF_IC3_DEVICENAME]
        if Device := Gb.Devices_by_devicename.get(devicename):
            Device.conf_icloud_dname = new_icloud_dname

        dict_del(Gb.devicenames_by_aadev_dname, old_icloud_dname)
        list_del(Gb.conf_icloud_dnames, old_icloud_dname)
        list_add(Gb.conf_icloud_dnames, new_icloud_dname)
        Gb.aadev_dnames_by_devicename[devicename] = new_icloud_dname
        Gb.devicenames_by_aadev_dname[new_icloud_dname] = devicename

        conf_device[CONF_AADEV_NAME] = new_icloud_dname

        if write_config_file:
            config_file.write_icloud3_configuration_file()

        if post_msg:
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Updating Apple Acct Device Name"
                        f"{CRLF_DOT}{old_icloud_dname}{RARROW}{new_icloud_dname}")

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def _match_AppleAcct_devices_to_Device(AppleAcct, retry_match_devicenames=None):
    '''
    Cycle through the AppleAcct raw data and match that item with the
    conf_devices iCloud entry. Then set the data fields to tie it to
    the Device object.
    '''
    evlog_msg = ''
    missing_aadev_devicenames = []
    AADevice = AppleAcct.AADevices
    if AADevice is None:
        return

    for conf_device in Gb.conf_devices:
        if conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username:
            continue

        devicename      = conf_device[CONF_IC3_DEVICENAME]
        device_id       = conf_device[CONF_AADEV_DEVICE_ID]
        conf_aadev_name = conf_device[CONF_AADEV_NAME]
        Device          = Gb.Devices_by_devicename.get(devicename)

        if Device is None or Device.is_inactive:
            continue

        if retry_match_devicenames and devicename not in retry_match_devicenames:
            continue

        broadcast_info_msg(f"Matching Apple Device > {conf_aadev_name}")

        AADevData = AppleAcct.AADevData_by_device_id.get(device_id)

        # The device_id is not in the Apple Acct Devices list
        if AADevData is None:
            device_id  = AppleAcct.device_id_by_aadev_dname.get(conf_aadev_name)
            AADevData  = AppleAcct.AADevData_by_device_id.get(device_id)

        # The same aadev_name is there, the device name now belongs to another device
        if AADevData is None:
            list_add(missing_aadev_devicenames, conf_aadev_name)
            post_alert( f"{conf_device[CONF_FNAME]} > "
                        f"Error Matching Apple Acct Device"
                        f"{CRLF_DOT}{conf_aadev_name}, "
                        f"{conf_device[CONF_MODEL_DISPLAY_NAME]}")
            continue

        Gb.devicenames_by_aadev_dname[conf_aadev_name] = devicename
        Gb.aadev_dnames_by_devicename[devicename]      = conf_aadev_name

        AADevData.Device           = Device
        AADevData.ic3_devicename   = devicename
        Device.AppleAcct           = AppleAcct
        Device.icloud_device_id    = device_id

        Device.icloud_person_id    = AADevData.device_data.get('prsId', '')
        Device.family_share_device = AADevData.device_data.get('fmlyShare', False)
        AADevData.device_data[CONF_IC3_DEVICENAME] = devicename
        AADevData.device_data['dname'] = AADevData.dname

        Gb.Devices_by_icloud_device_id[device_id] = Device
        Gb.AppleAcct_by_devicename[devicename]    = AppleAcct

        if Device.family_share_device is False:
            owner_device_ids = Gb.owner_device_ids_by_username.get(AppleAcct.username, [])
            list_add(owner_device_ids, device_id)
            Gb.owner_device_ids_by_username[AppleAcct.username] = owner_device_ids

        # Set verify status to a valid device_id exists instead of always True
        # This will pick up devices in the configuration file that no longer exist
        Device.verified_ICLOUD = device_id in AppleAcct.AADevData_by_device_id
        Gb.icloud_device_verified_cnt += 1

    return missing_aadev_devicenames

#----------------------------------------------------------------------------
def _refresh_icloud_data_retry(AppleAcct, missing_aadev_devices=None):
    '''
    Get all the devices that have the Apple device configured that are not
    in the AppleAcct devices list. This  indicates we have a device that
    is tracked via Apple but that device is not in the Apple Account.
    '''

    event_msg =(f"Devices not Found in Apple Data")
    for _devicename, aadev_name in missing_aadev_devices.items():
        devicename = _devicename

        Device = Gb.Devices_by_devicename[devicename]
        event_msg += f"{CRLF_RED_ALERT2}{Device.fname}{RARROW}{Device.conf_icloud_dname}"
    post_event(event_msg)

    try:
        retry_cnt = 0 if AppleAcct.AADevices else 10
        while retry_cnt < 5:
            retry_cnt += 1

            event_msg = f"Refreshing Location Data (#{retry_cnt})"
            post_greenbar_msg(event_msg)
            post_event(f"{event_msg}")

            AppleAcct.refresh_icloud_data()

            missing_aadev_devices = _get_conf_devices_apple_did_not_locate(AppleAcct)
            if is_empty(missing_aadev_devices):
                post_event("All Devices Found, Continuing with Setup")
                return

    except Exception as err:
        log_exception(err)

    event_msg =(f"Devices still not Found, Continuing with Setup")
    for devicename, aadev_name in missing_aadev_devices.items():
        Device = Gb.Devices_by_devicename[devicename]
        event_msg += f"{CRLF_RED_ALERT2}{Device.fname}{RARROW}{Device.conf_icloud_dname}"
    post_event(event_msg)

#--------------------------------------------------------------------
def _set_any_Device_alerts():
    '''
    Set Alerts for devices
    '''

    device_not_found_msg = ''
    apple_acct_not_found_msg = ''
    apple_acct_login_failed_devices = ''

    for Device in Gb.Devices:
        # Device's Apple acct error
        if (Device.conf_apple_acct_username == ''
                or Device.conf_icloud_dname == ''
                or Device.was_verified is False
                or Device.conf_apple_acct_username in Gb.AppleAcct_error_by_username):
            continue

        if Device.conf_apple_acct_username not in Gb.AppleAcct_by_username:
            Device.set_fname_alert(YELLOW_ALERT)
            apple_acct_not_found_msg += (
                    f"{CRLF_DOT}Apple Acct-{Device.conf_apple_acct_username_id} > "
                    f"{Device.fname_devicename}")

            update_alert_sensor(Device.fname, (
                    f"{Device.conf_icloud_dname} "
                    f"Apple Acct Login Problem ({Device.conf_apple_acct_username_id})"))

        # Device's Apple acct ok but device not in Apple acct
        elif (Device.AppleAcct
                and Device.AppleAcct.device_id_by_aadev_dname.get(Device.conf_icloud_dname) is None):
            Device.set_fname_alert(YELLOW_ALERT)
            error_msg = (
                    f"{Device.conf_icloud_dname} "
                    f"Not in Apple Acct ({Device.AppleAcct.username_base})")
            device_not_found_msg += (f"{CRLF_DOT}{Device.fname_devicename} > {error_msg}")
            update_alert_sensor(Device.fname, error_msg)

            log_error_msg(f"iCloud3 Device Configuration Error > "
                        f"{Device.fname_devicename}, {error_msg}")

    if Gb.internet_error:
        return

    if device_not_found_msg:
        post_alert( f"APPLE ACCOUNT DEVICE NOT FOUND > "
                    f"A device was not found in it's Apple Acct, iCloud Location will not be used:"
                    f"{device_not_found_msg}")
    if apple_acct_not_found_msg:
        post_alert( f"APPLE ACCOUNT NOT LOGGED INTO > "
                    f"A device's Apple Acct was not logged into, iCloud Location will not be used:"
                    f"{apple_acct_not_found_msg}")

#--------------------------------------------------------------------
def _post_evlog_apple_acct_devices_info(AppleAcct):
    '''
    Cycle through the AppleAcct raw data and display the Event Log message for
    the device indicating if it is:
        - tracked (show the devicename that raw data item is tied to)
        - tracked by another username ( show the other username)
        - not tracked
    '''
    _post_family_share_info(AppleAcct)
    _post_not_assigned_info(AppleAcct)
    _post_tracked_devices_info(AppleAcct)

#--------------------------------------------------------------------
def _post_tracked_devices_info(AppleAcct):
    devices_assigned_msg = reauth_needed_msg = aadev_startup_msg= ''
    devices_assigned_cnt = 0

    if AppleAcct.terms_of_use_update_needed:
        reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Accept Terms of Service Needed"
    if AppleAcct.is_reauth_needed:
        reauth_needed_msg += f"{CRLF}{NBSP2}{RED_ALERT}Authentication Needed"

    device_cnt = len(AppleAcct.AADevData_by_device_id)
    AADevData_tracked =  {AADevData.dname: AADevData
                            for _, AADevData in AppleAcct.AADevData_by_device_id.items()
                            if AADevData.Device}

    dict_sort(AADevData_tracked)

    for aadev_dname, AADevData in AADevData_tracked.items():
        try:
            aadev_startup_msg = ''
            aadev_startup_msg= f", {RED_ALERT}{AADevData.startup_msg}" if AADevData.startup_msg else ''

            # If the Device is None, this AppleAcct is not tracked or assigned to another username
            # aadevice_dname ending with '.' indicates this is a duplicate device
            try:
                devicename = AADevData.ic3_devicename
                Device     = AADevData.Device
                if Device is None:
                    continue

                if Device.tracking_mode == INACTIVE:
                    aadev_startup_msg += f', {INACTIVE_SYMB}INACTIVE'

                devices_assigned_msg += (
                            f"{CRLF_CHK}{AADevData.name}{RARROW}"
                            f"{Device.fname} "
                            f"({AADevData.model_display_name})"
                            f"{aadev_startup_msg}")

                if AADevData and Gb.is_log_level_rawdata:
                    log_title =(f"AADevice Data {AppleAcct.account_name}{LINK}"
                                f"{devicename}/{aadev_dname} "
                                f"({AADevData.device_identifier})")

            except Exception as err:
                log_exception(err)
            devices_assigned_cnt += 1

        except Exception as err:
            log_exception(err)
            post_error_msg( f"{EVLOG_ALERT}Apple Acct {AppleAcct.username_id} > "
                            f"{CRLF_DOT}{aadev_dname} Error Listing Device Info")

    evlog_msg =(f"Tracked Devices, "
                f"{devices_assigned_cnt} of {device_cnt}"
                f"{reauth_needed_msg}"
                f"{devices_assigned_msg}")

    post_event(evlog_msg)

#--------------------------------------------------------------------
def _post_family_share_info(AppleAcct):
    owner_icloud_dnames =[_AADevData.dname
                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                    if _AADevData.family_share_device is False]
    famshr_dnames_msg = [_AADevData.dname
                    for device_id, _AADevData in AppleAcct.AADevData_by_device_id.items()
                    if _AADevData.family_share_device]
    devices_assigned_to_other_aa = [
                    f"{conf_device[CONF_AADEV_NAME]} ({username_id(conf_device[CONF_APPLE_ACCOUNT])})"
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_AADEV_NAME] in AppleAcct.device_id_by_aadev_dname.items()
                        and conf_device[CONF_APPLE_ACCOUNT] != AppleAcct.username)]

    list_sort(owner_icloud_dnames)
    list_sort(famshr_dnames_msg)
    list_sort(devices_assigned_to_other_aa)

    devices_assigned_to_msg = ''
    if isnot_empty(devices_assigned_to_other_aa):
        devices_assigned_to_msg = ( f"{CRLF_DOT}Family Devices tracked by another Apple Acct:"
                                    f"{list_to_str(devices_assigned_to_other_aa)}")

    family_not_located_msg = ''
    if AppleAcct.locate_all_devices is False:
        family_not_located_msg = f"{CRLF_STAR} Family Devices are not located"

    post_event( f"Family Sharing List Info"
                f"{CRLF_DOT} myDevices-{list_to_str(owner_icloud_dnames)}"
                f"{CRLF_DOT} Family Devices-{list_to_str(famshr_dnames_msg)}"
                f"{family_not_located_msg}"
                f"{devices_assigned_to_msg}")

#--------------------------------------------------------------------
def _post_not_assigned_info(AppleAcct):
    devices_not_assigned     = {}
    for aadev_dname, device_id in AppleAcct.device_id_by_aadev_dname.items():
        AADevData = AppleAcct.AADevData_by_device_id.get(device_id)
        # if AADevData is None or AADevData.Device:
        #     continue
        if AADevData and AADevData.Device is None:
            devices_not_assigned[aadev_dname] = AADevData

    dict_sort(devices_not_assigned)

    devices_not_assigned_msg = ''
    for aadev_dname, AADevData in devices_not_assigned.items():
        aadev_msg = f", {RED_ALERT}{AADevData.startup_msg}" if AADevData.startup_msg else ''
        devices_not_assigned_msg +=(f"{CRLF_DOT}{aadev_dname} "
                                    f"({AADevData.model_display_name})"
                                    f"{aadev_msg}")

    if devices_not_assigned_msg != '':
        post_event( f"Devices Not Tracked"
                    f"{devices_not_assigned_msg}")

#--------------------------------------------------------------------
def _set_device_data_source(AppleAcct):
    '''
    Cycle through the devices and change the iCloud data source to MobApp
    if there is a problem with the iCloud setup and the MobApp is available
    '''
    broadcast_info_msg(f"Stage 3 > Set up device data source")

    try:
        if Gb.Devices_by_devicename == {}:
            return

        # Gb.Devices_by_icloud_device_id = {}
        for devicename, Device in Gb.Devices_by_devicename.items():
            data_source = None
            broadcast_info_msg(f"Determine Device Tracking Method >{devicename}")

            if Device.icloud_device_id:
                device_id = Device.icloud_device_id
                if device_id in AppleAcct.AADevData_by_device_id:
                    data_source = ICLOUD
                    Gb.Devices_by_icloud_device_id[device_id] = Device
                    AADevData = AppleAcct.AADevData_by_device_id[device_id]

            if (Device.is_mobapp_monitored and data_source is None):
                data_source = MOBAPP

            if data_source != MOBAPP:
                info_msg = (f"Set AppleAcct Device Id > {Device.devicename}, "
                            f"DataSource-{data_source}, "
                            f"{CRLF}iCloud-({Device.device_id8_icloud}), "
                            f"{Device.model_display_name}")
                post_monitor_msg(info_msg)

            Device.primary_data_source = data_source

        info_msg = ''
        for _device_id, AADevData in AppleAcct.AADevData_by_device_id.items():
            info_msg += (f"{AADevData.name}/{_device_id[:8]}-{AADevData.data_source}, ")
        if info_msg == '': info_msg = 'None'
        post_monitor_msg(f"AppleAcct Devices > {info_msg}")

    except Exception as err:
        log_exception(err)


