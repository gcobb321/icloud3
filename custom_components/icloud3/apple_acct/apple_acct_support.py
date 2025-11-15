
from ..global_variables import GlobalVariables as Gb
from ..const            import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE, EVLOG_ERROR,
                                    ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                    NL, NL3, CRLF, CRLF_DOT, DASH_20, RED_X, CRLF_RED_MARK, CRLF_RED_STOP,
                                    RED_ALERT, CRLF_RED_ALERT, CRLF_CHK,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY, CONF_LOCATE_ALL,
                                    CONF_SERVER_LOCATION,
                                    CONF_TRACKING_MODE, INACTIVE_DEVICE,
                                    )


from .apple_acct        import (AppleAcctManager,
                                AppleAcctNoDevicesException, AppleAcctFailedLoginException,
                                AppleAcctAPIResponseException, AppleAcct2FARequiredException,)

# from ..startup          import start_ic3_control
from ..utils.messaging  import (post_event, post_alert, post_alert, post_error_msg, post_monitor_msg,
                                post_greenbar_msg, update_alert_sensor,
                                log_debug_msg, log_info_msg, log_exception, log_error_msg, log_warning_msg,
                                internal_error_msg2, _evlog, _log, )
from ..utils.time_util  import (time_now_secs, secs_to_time, format_age, secs_to_hhmm,
                                format_time_age, )
from ..utils.utils      import (instr, list_to_str, list_add, list_del, is_empty, isnot_empty,
                                username_id, is_running_in_event_loop,)
from ..startup          import config_file

#--------------------------------------------------------------------
import traceback
from re import match


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   APPLE ACCT INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_into_apple_account(username, password, apple_server_location, locate_all_devices=None):
    '''
    Log in and Authenticate the Apple Account via pyicloud

    If successful - AppleAcct = AppleAcctManager object
    If not        - AppleAcct = None
    '''
    # If not using the iCloud location svcs, nothing to do
    if (Gb.use_data_source_ICLOUD is False
            or username == ''
            or password == ''):
        return

    AppleAcct = Gb.AppleAcct_by_username.get(username)

    if locate_all_devices is not None:
        locate_all_devices = locate_all_devices
    elif AppleAcct and AppleAcct.locate_all_devices is not None:
        locate_all_devices = AppleAcct.locate_all_devices
    else:
        True

    login_err = 0
    post_greenbar_msg(f"Apple Acct > Logging into {username_id(username)}")

    try:
        if Gb.internet_error:
            post_alert( f"INTERNET CONNECTION ERROR > "
                        f"Apple Acct not available:"
                        f"{CRLF_DOT}{username_id(username)}")
            return None

        AppleAcct = Gb.AppleAcct_by_username.get(username)

        # Make sure the Device Service set up was completed. It will not be
        # if there was a connection error during startup
        if AppleAcct and AppleAcct.is_AADevices_setup_complete is False:
            AppleAcct.create_AADevices_object()
            setup_status_msg(AppleAcct, "0, Setup Devices", username)

        if (AppleAcct and AppleAcct.is_AADevices_setup_complete
                and AppleAcct.AADevices):
            AppleAcct.dup_icloud_dname_cnt = {}
            refresh_AppleAcct_AADdevices_data(AppleAcct)

        # Setup iCloud
        elif (AppleAcct and AppleAcct.is_AADevices_setup_complete):
            create_AppleAcct_AADevices(AppleAcct)

        # Setup AppleAcct and iCloud
        else:
            try:
                AppleAcct = create_AppleAcct(username, password, apple_server_location, locate_all_devices)
            except Exception as err:
                log_exception(err)

        verify_icloud_device_info_received(AppleAcct)
        is_authentication_2fa_code_needed(AppleAcct, initial_setup=True)

        Gb.AppleAcct_by_username[username] = AppleAcct

        return AppleAcct

    except AppleAcct2FARequiredException as err:
        login_err = str(err)
        is_authentication_2fa_code_needed(AppleAcct, initial_setup=True)
        return AppleAcct

    except AppleAcctAPIResponseException as err:
        login_err = str(err)
        pass

    except AppleAcctFailedLoginException as err:
        AppleAcct = Gb.AppleAcctLoggingInto
        login_err = str(err)
        login_err + ", Will retry logging into the Apple Account later"
        # Gb.username = Gb.username_base = Gb.password = ''

    except Exception as err:
        AppleAcct = Gb.AppleAcctLoggingInto
        login_err = str(err)
        log_exception(err)


    list_add(Gb.usernames_setup_error_retry_list, username)

    post_error_msg( f"{EVLOG_ALERT}{login_err}")
    _log(f'{username=} {Gb.aalogin_error_reason_by_username=}')
    _log(f'{username=} {Gb.aalogin_error_secs_by_username=}')
    update_alert_sensor(username_id(username), (
                                f"Apple Acct Login Failed, "
                                f"{Gb.aalogin_error_reason_by_username.get(username, 'Unknown')}"))

    return AppleAcct

#....................................................................
def refresh_AppleAcct_AADdevices_data(AppleAcct):
    '''
    Refresh the device data for an existing Apple acct
    '''
    AppleAcct.refresh_icloud_data(locate_all_devices=True)

    setup_status_msg(AppleAcct, "1, Refresh iCloud Devices")

#....................................................................
def create_AppleAcct_AADevices(AppleAcct):
    '''
    The AppleAcct Apple acct object exists but the devices do not. Create them.
    '''
    try:
        AppleAcct.create_AADevices_object()

        Gb.AppleAcct_by_username[AppleAcct.username] = AppleAcct

    except Exception as err:
        log_exception(err)

    setup_status_msg(AppleAcct, "2, Create AADevices")

#....................................................................
def create_AppleAcct(username, password, apple_server_location, locate_all_devices):
    try:
        AppleAcct = Gb.AppleAcct_by_username.get(username)
        if AppleAcct is None:
            log_info_msg(f"{NL3}🔻{'—'*20} {username.upper()} {'—'*5} SETUP APPLE ACCOUNT {'—'*20}🔻")
            AppleAcct = AppleAcctManager(
                                username,
                                password,
                                apple_server_location=apple_server_location,
                                locate_all_devices=locate_all_devices,
                                cookie_directory=Gb.icloud_cookie_directory,
                                session_directory=Gb.icloud_session_directory)

            log_info_msg(f'{AppleAcct=} {AppleAcct.apple_id=}')
            log_info_msg(f"{NL3}🔺{'—'*20} {username.upper()} {'—'*5} SETUP APPLE ACCOUNT {'—'*20}🔺")

            # log_info_msg(f"{NL3}🔻{'—'*20}🔻  {username.upper()} SETUP APPLE ACCOUNT  🔻{'—'*20}🔻")
            # PyAppleAcct = PyiCloudService(
            #                     username,
            #                     password,
            #                     cookie_directory=Gb.icloud_cookie_directory,
            #                     with_family=locate_all_devices,
            #                     china_mainland=False,)
            #                     # apple_server_location=apple_server_location,
            #                     # locate_all_devices=locate_all_devices,
            #                     # session_directory=Gb.icloud_session_directory)

            # log_info_msg(f'{PyAppleAcct=} {PyAppleAcct._apple_id=}')
            # log_info_msg(f'{PyAppleAcct.devices=}')
            # log_info_msg(f"{NL3}🔺{'—'*20}🔺  {username.upper()} SETUP APPLE ACCOUNT  🔺{'—'*20}🔺")


        # Stage 4 checks to see if AppleAcct exists and it has AADevData device info. These values exists
        # if the __init__ login was completed. However, if it was not completed and they do not exist,
        # Stage 4 will do another login and set these values when it finishes, which is before the
        # __init__ is complete. Do not set them again when __init__ login finially completes.

    except Exception as err:
        log_exception(err)

    if Gb.internet_error:
        post_alert( f"INTERNET CONNECTION ERROR > "
                    f"Apple Acct unavailable:"
                    f"{CRLF_DOT}{username_id(username)}")
        return None

    if AppleAcct is None:
        post_alert( f"Apple Acct > Apple Acct unavailable"
                    f"{CRLF_DOT}{username_id(username)}")
        return None

    if AppleAcct.AADevices:
        if is_empty(AppleAcct.AADevData_by_device_id):
            AppleAcct.refresh_icloud_data(locate_all_devices=True)

        aadevdata_items = [_AADevData.fname_device_id
                                for _AADevData in AppleAcct.AADevData_by_device_id.values()]

        # Refresh devices if none returned
        if is_empty(aadevdata_items):
            AppleAcct.refresh_icloud_data(locate_all_devices=True)

            aadevdata_items = [_AADevData.fname_device_id
                                    for _AADevData in AppleAcct.AADevData_by_device_id.values()]

    setup_status_msg(AppleAcct, "3, Create AppleAcct & Devices", username)

    return AppleAcct

#....................................................................
def setup_status_msg(AppleAcct, setup_method, username=None):

    if AppleAcct is None:
        post_event(f"Apple Acct > Error setting up {username}, ")
        log_debug_msg(  f"APPLE ACCT SETUP > Step-{setup_method}")
        return

    dev_data = list(AppleAcct.AADevData_by_device_id.values()) if AppleAcct.AADevices else []
    aadevdata_items = [_AADevData.fname_device_id
                                    for _AADevData in AppleAcct.AADevData_by_device_id.values()]
    # post_event(f"Apple Acct > {AppleAcct.account_owner}, iCloud Data Handler Setup")
    log_debug_msg(  f"APPLE ACCT SETUP > {AppleAcct.username_id} ({AppleAcct.account_owner}), "
                    f"Method-{setup_method}, "
                    f"SetupComplete-{AppleAcct.is_AADevices_setup_complete}, "
                    f"Devices-{list_to_str(aadevdata_items)}")

#--------------------------------------------------------------------
def verify_icloud_device_info_received(AppleAcct):
    if (AppleAcct is None
            or AppleAcct.AADevices is None):
        return False

    if AppleAcct.AADevices.devices_cnt >= 0:
        return True

    Gb.get_ICLOUD_devices_retry_cnt = 0

    while Gb.get_ICLOUD_devices_retry_cnt < 8:
        Gb.get_ICLOUD_devices_retry_cnt += 1
        if Gb.get_ICLOUD_devices_retry_cnt > 1:
            post_event( f"Apple Acct > {AppleAcct.account_owner}, "
                        f"Family Sharing List Refresh "
                        f"(#{Gb.get_ICLOUD_devices_retry_cnt} of 8)")

        AppleAcct.refresh_icloud_data(locate_all_devices=True)

        if AppleAcct.AADevices.devices_cnt >= 0:
            return True

    post_event( f"{EVLOG_ERROR}Apple Account > {AppleAcct.account_owner}, "
                f"Family Sharing List Refresh failed")

    return (AppleAcct.AADevices.devices_cnt >= 0)

#--------------------------------------------------------------------
def is_authentication_2fa_code_needed(AppleAcct, initial_setup=False):
    '''
    A wrapper for seeing if an authentication is needed and setting up the config_flow
    reauth request
    '''
    if AppleAcct is None:
        return False
    elif AppleAcct.auth_2fa_code_needed:
        pass
    elif Gb.conf_data_source_MOBAPP is False:
        return False
    elif initial_setup:
        pass
    elif Gb.start_icloud3_inprocess_flag:
        return False

    alert_msg = ''
    if (new_2fa_authentication_code_requested(AppleAcct, initial_setup)
            and AppleAcct.new_2fa_code_already_requested_flag is False):
        alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.auth_2fa_code_needed_secs)})"

        post_alert(f"{AppleAcct.username_id_short} > {alert_msg}")
        update_alert_sensor(AppleAcct.username_id, alert_msg)

        Gb.AppleAcct_needing_reauth_via_ha = {
                    CONF_USERNAME: AppleAcct.username,
                    CONF_PASSWORD: AppleAcct.password,
                    'account_owner': AppleAcct.account_owner}

    if AppleAcct.terms_of_use_update_needed:
        alert_msg = "Apple Acct > Accept `Terms of Use` needed (Auth Code entry screen)"
        post_alert(f"{AppleAcct.username_id} > {alert_msg}")
        update_alert_sensor(AppleAcct.username_id, alert_msg)
        log_warning_msg(f"{AppleAcct.username_id} > {alert_msg}")

#--------------------------------------------------------------------
def check_all_devices_online_status():
    '''
    See if all the devices are 'pending'. If so, the devices are probably in airplane mode.
    Set the time and display a message
    '''
    any_device_online_flag = False
    for Device in Gb.Devices_by_devicename_tracked.values():
        if Device.is_online:
            Device.offline_secs = 0
            Device.pending_secs = 0
            any_device_online_flag = True

        elif Device.is_offline:
            if Device.offline_secs == 0:
                Device.offline_secs = Gb.this_update_secs
            post_event(Device,
                        f"Device Offline and not available > "
                        f"OfflineSince-{format_time_age(Device.offline_secs)}")

        elif Device.is_pending:
            if Device.pending_secs == 0:
                Device.pending_secs = Gb.this_update_secs
            post_event(Device,
                        f"Device status is Pending/Unknown > "
                        f"PendingSince-{format_time_age(Device.pending_secs)}")

    if any_device_online_flag == False:
        post_event( f"All Devices are offline or have a pending status. "
                    f"They may be in AirPlane Mode and not available")

#--------------------------------------------------------------------
def new_2fa_authentication_code_requested(AppleAcct, initial_setup=False):
    '''
    Make sure iCloud is still available and doesn't need to be authenticationd
    in 15-second polling loop

    Returns True  if Authentication is needed.
    Returns False if Authentication succeeded
    '''

    try:
        if initial_setup is False:
            if AppleAcct is None:
                event_msg =(f"{EVLOG_ALERT}iCloud Web Svcs Error, Interface has not been setup, "
                            "resetting iCloud")
                post_error_msg(event_msg)
                Gb.restart_icloud3_request_flag = True

            elif Gb.restart_icloud3_request_flag:         # via service call
                event_msg =("iCloud Restarting, Reset command issued")
                post_error_msg(event_msg)

            if AppleAcct is None:
                event_msg =("iCloud Authentication Required, will retry")
                post_error_msg(event_msg)
                return True         # Authentication needed

        if AppleAcct is None:
            return True

        #See if 2fa Verification needed
        if AppleAcct.auth_2fa_code_needed is False:
            return False

        return True

    except Exception as err:
        internal_error_msg2('Apple ID Verification', traceback.format_exc)
        return True

#--------------------------------------------------------------------
def reset_AppleAcct_variables():
    '''
    Delete all Apple account objects and clear all dictionaries
    so new AppleAcct objects will be set up again on a restart
    '''
    log_info_msg("Resetting Apple Acct objects and variables")

    Gb.AppleAcct             = None
    Gb.AppleAcctLoggingInto  = None
    # Gb.ValidateAppleAcctUPW  = None
    Gb.valid_upw_results_msg = ''

    for iCloudSession in Gb.iCloudSession_by_username.values():
        del(iCloudSession)

    for AppleAcct in Gb.AppleAcct_by_username.values():
        del(AppleAcct)

    Gb.iCloudSession_by_username       = {}
    Gb.AppleAcct_by_username           = {}
    Gb.AppleAcct_needing_reauth_via_ha = {}
    Gb.AppleAcct_by_devicename         = {}
    Gb.AppleAcct_by_username           = {}
    Gb.AppleAcct_password_by_username  = {}
    Gb.AppleAcct_logging_in_usernames  = []

    Gb.username_valid_by_username      = {}
    Gb.server_err_503_usernames        = []
    Gb.aalogin_error_secs_by_username  = {}
    Gb.aalogin_error_reason_by_username = {}

    config_file.decode_all_passwords()
