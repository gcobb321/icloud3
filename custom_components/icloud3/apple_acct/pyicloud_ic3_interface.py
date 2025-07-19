
from ..global_variables import GlobalVariables as Gb
from ..const            import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE, EVLOG_ERROR,
                                    ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                    CRLF, CRLF_DOT, DASH_20, RED_X, CRLF_RED_MARK, CRLF_RED_STOP,
                                    RED_ALERT, CRLF_RED_ALERT,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY, CONF_LOCATE_ALL,
                                    CONF_SERVER_LOCATION,
                                    CONF_TRACKING_MODE, INACTIVE_DEVICE,
                                    )


from .pyicloud_ic3      import (PyiCloudManager,
                                PyiCloudNoDevicesException, PyiCloudFailedLoginException,
                                PyiCloudAPIResponseException, PyiCloud2FARequiredException,)
from ..startup          import start_ic3_control
from ..startup          import config_file
from ..utils.messaging  import (post_event, post_error_msg, post_monitor_msg,
                                post_evlog_greenbar_msg, post_alert,
                                log_debug_msg, log_info_msg, log_exception, log_error_msg, log_warning_msg,
                                internal_error_msg2, _evlog, _log, )
from ..utils.time_util  import (time_now_secs, secs_to_time, format_age,
                                format_time_age, )
from ..utils.utils      import (instr, list_to_str, list_add, list_del, is_empty, isnot_empty,
                                username_id, )

#--------------------------------------------------------------------
import traceback
from re import match


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PYICLOUD-IC3 INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def log_into_apple_account(username, password, apple_server_location, locate_all_devices=None):
    '''
    Log in and Authenticate the Apple Account via pyicloud

    If successful - PyiCloud = PyiCloudManager object
    If not        - PyiCloud = None
    '''
    # If not using the iCloud location svcs, nothing to do
    if (Gb.use_data_source_ICLOUD is False
            or username == ''
            or password == ''):
        return

    PyiCloud = Gb.PyiCloud_by_username.get(username)

    if locate_all_devices is not None:
        locate_all_devices = locate_all_devices
    elif PyiCloud and PyiCloud.locate_all_devices is not None:
        locate_all_devices = PyiCloud.locate_all_devices
    else:
        True

    login_err = 0
    post_evlog_greenbar_msg(f"Apple Acct > Setting up {username_id(username)}")

    try:
        PyiCloud = Gb.PyiCloud_by_username.get(username)

        # Make sure the Device Service set up was completed. It will not be
        # if there was a connection error during startup
        if PyiCloud and PyiCloud.is_AADevices_setup_complete is False:
            PyiCloud.create_AADevices_object()

        pyicloud_msg = (f"{PyiCloud=}")
        if PyiCloud:
            pyicloud_msg += f"{PyiCloud.is_AADevices_setup_complete=} {PyiCloud.AADevices=}"
            if PyiCloud.AADevices:
                pyicloud_msg += f"{PyiCloud.AADevData_by_device_id.values()=}"
        username_base = username_id(username)
        debug_msg_hdr =f"APPLE ACCT SETUP > {username_base}, Step-"
        log_debug_msg(f"{debug_msg_hdr}0, Login Started, {pyicloud_msg}")

        if Gb.internet_error:
            post_event( f"{EVLOG_ALERT}INTERNET CONNECTION ERROR > "
                        f"Apple Acct not available:"
                        f"{CRLF_DOT}{username_base}")
            return None

        if (PyiCloud
                and PyiCloud.is_AADevices_setup_complete
                and PyiCloud.AADevices):
            PyiCloud.dup_icloud_dname_cnt = {}


            PyiCloud.refresh_icloud_data(locate_all_devices=True)

            pyicloud_msg = f"{PyiCloud=} {PyiCloud.is_AADevices_setup_complete=} {PyiCloud.AADevices=}"
            if PyiCloud.AADevices:
                pyicloud_msg += f"{PyiCloud.AADevData_by_device_id.values()=}"
            log_debug_msg(f"{debug_msg_hdr}1, Request iCloud Refresh, {pyicloud_msg}")
            post_event(f"Apple Acct > {PyiCloud.account_owner}, Device Data Refreshed")

        # Setup iCloud
        elif (PyiCloud
                and PyiCloud.is_AADevices_setup_complete):

            try:
                PyiCloud.create_AADevices_object()
                Gb.PyiCloud_by_username[username] = PyiCloud

                pyicloud_msg = f"{PyiCloud=} {PyiCloud.is_AADevices_setup_complete=} {PyiCloud.AADevices=}"
                if PyiCloud.AADevices:
                    pyicloud_msg += f"{PyiCloud.AADevData_by_device_id.values()=}"
                log_debug_msg(f"{debug_msg_hdr}2, Create AADevices, {pyicloud_msg}")
                post_event(f"Apple Acct > {PyiCloud.account_owner}, iCloud Created & Refreshed")

                return PyiCloud

            except Exception as err:
                log_exception(err)

        # Setup PyiCloud and iCloud
        else:
            try:
                PyiCloud = None
                PyiCloud = PyiCloudManager( username,
                                            password,
                                            apple_server_location=apple_server_location,
                                            locate_all_devices=locate_all_devices,
                                            cookie_directory=Gb.icloud_cookie_directory,
                                            session_directory=Gb.icloud_session_directory)

                # Stage 4 checks to see if PyiCloud exists and it has AADevData device info. These values exists
                # if the __init__ login was completed. However, if it was not completed and they do not exist,
                # Stage 4 will do another login and set these values when it finishes, which is before the
                # __init__ is complete. Do not set them again when __init__ login finially completes.

                pyicloud_msg = (f"{PyiCloud.account_owner_username}, "
                                f"Complete={PyiCloud.is_AADevices_setup_complete}, ")

            except Exception as err:
                log_exception(err)

            if Gb.internet_error:
                post_event( f"{EVLOG_ALERT}INTERNET CONNECTION ERROR > "
                            f"Apple Acct unavailable:"
                            f"{CRLF_DOT}{username_base}")
                return None

            if PyiCloud.AADevices:
                if is_empty(PyiCloud.AADevData_by_device_id):
                    PyiCloud.refresh_icloud_data(locate_all_devices=True)

                aadevdata_items = [_AADevData.fname_device_id
                                        for _AADevData in PyiCloud.AADevData_by_device_id.values()]

                if is_empty(aadevdata_items):
                    PyiCloud.refresh_icloud_data(locate_all_devices=True)

                    aadevdata_items = [_AADevData.fname_device_id
                                            for _AADevData in PyiCloud.AADevData_by_device_id.values()]

                pyicloud_msg += f"AADevDataItems-({list_to_str(aadevdata_items)})"

            log_debug_msg(f"{debug_msg_hdr}3, Setup PyiCloud, {pyicloud_msg}")
            code_msg = f" ({PyiCloud.response_code})"
            if PyiCloud.is_authenticated:
                post_event(f"Apple Acct > {PyiCloud.account_owner}, "
                            f"Login Successful, "
                            f"{PyiCloud.auth_method}")
            else:
                retry_at = secs_to_time(time_now_secs() + 900)
                post_event( f"{EVLOG_ALERT}Apple Acct > {PyiCloud.username_id}, Login Failed"
                            f"{CRLF_DOT}Apple Server Location-`{PyiCloud.apple_server_location}`"
                            f"{CRLF_DOT}{PyiCloud.response_code_desc}")
                post_alert(PyiCloud.username_id, "Apple Acct Login Failed")


        verify_icloud_device_info_received(PyiCloud)
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)

        return PyiCloud

    except PyiCloud2FARequiredException as err:
        login_err = str(err)
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        return PyiCloud

    except PyiCloudAPIResponseException as err:
        login_err = str(err)
        pass

    except PyiCloudFailedLoginException as err:
        PyiCloud = Gb.PyiCloudLoggingInto
        login_err = str(err)
        login_err + ", Will retry logging into the Apple Account later"
        # Gb.username = Gb.username_base = Gb.password = ''

    except Exception as err:
        PyiCloud = Gb.PyiCloudLoggingInto
        login_err = str(err)
        log_exception(err)

    Gb.PyiCloud_by_username[username] = PyiCloud
    if Gb.PyiCloud and Gb.PyiCloud.response_code_pwsrp_err == 503:
        list_add(Gb.username_pyicloud_503_internet_error, username)

    else:
        list_add(Gb.usernames_setup_error_retry_list, username)

    # list_del(Gb.PyiCloud_by_username, username)
    post_error_msg( f"{EVLOG_ALERT}{login_err}")
    post_alert(username_base, "Apple Acct Login Failed")

    return PyiCloud

#--------------------------------------------------------------------
def log_into_apple_acct_restart_icloud3():
    '''
    Log into the Apple acct when Restart iCloud3 was selected on the EvLog
    This bypasses the async ValidateUPW check, which is not needed on a restart
    '''
    post_event('Log into Apple Accounts')

    results_msg = ''
    for conf_apple_acct in Gb.conf_apple_accounts:
        username   = conf_apple_acct[CONF_USERNAME]
        password   = Gb.PyiCloud_password_by_username[username]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices = conf_apple_acct[CONF_LOCATE_ALL]

        if is_empty(username) or is_empty(password):
            continue

        post_evlog_greenbar_msg(f"Apple Acct > Setting up {username_id(username)}")

        valid_upw = Gb.username_valid_by_username.get(username, False)
        if valid_upw is False:
            valid_upw = Gb.ValidateAppleAcctUPW.validate_username_password(username, password)

        # Fix to original v2.3.2
        if valid_upw:
            log_into_apple_account(username, password, apple_server_location, locate_all_devices)

            results_msg += f"{CRLF_DOT}{username}, Login Successful)"

        else:
            results_msg += f"{RED_ALERT}{username_id(username)}, Login Failed, Invalid Username or Password"
            post_alert(f"Apple Acct Error > {username_id(username)}, Login Failed")

    post_event(f"Log into Apple Accounts{results_msg}")
    post_evlog_greenbar_msg('')

    Gb.startup_lists['Gb.PyiCloud_by_username']       = Gb.PyiCloud_by_username
    Gb.startup_lists['Gb.username_valid_by_username'] = Gb.username_valid_by_username
    Gb.startup_lists['Gb.username_pyicloud_503_internet_error'] = Gb.username_pyicloud_503_internet_error

#--------------------------------------------------------------------
def log_into_apple_acct_retry():
    '''
    Retry to log into the Apple acct after receiving a 503 Connection Error.
    This is done in the 15-min cycle of icoud3_main
    '''
    for username in Gb.username_pyicloud_503_internet_error:
        conf_apple_acct, apple_acct_id = config_file.conf_apple_acct(username)
        password = conf_apple_acct[CONF_PASSWORD]
        apple_server_location = conf_apple_acct[CONF_SERVER_LOCATION]
        locate_all_devices = conf_apple_acct[CONF_LOCATE_ALL]

        PyiCloud = log_into_apple_account(username, password, apple_server_location, locate_all_devices)

        if PyiCloud and PyiCloud.is_authenticated:
            post_event(f"{EVLOG_ERROR}Apple Acct > {PyiCloud.account_owner}, Login Successful")
            list_del(Gb.username_pyicloud_503_internet_error, username)

            list_add(Gb.usernames_setup_error_retry_list, username)
            start_ic3_control.stage_4_setup_data_sources_retry()

    post_evlog_greenbar_msg('')

#--------------------------------------------------------------------
def verify_icloud_device_info_received(PyiCloud):
    if (PyiCloud is None
            or PyiCloud.AADevices is None):
        return False

    if PyiCloud.AADevices.devices_cnt >= 0:
        return True

    Gb.get_ICLOUD_devices_retry_cnt = 0

    while Gb.get_ICLOUD_devices_retry_cnt < 8:
        Gb.get_ICLOUD_devices_retry_cnt += 1
        if Gb.get_ICLOUD_devices_retry_cnt > 1:
            post_event( f"Apple Acct > {PyiCloud.account_owner}, "
                        f"Family Sharing List Refresh "
                        f"(#{Gb.get_ICLOUD_devices_retry_cnt} of 8)")

        PyiCloud.refresh_icloud_data(locate_all_devices=True)

        if PyiCloud.AADevices.devices_cnt >= 0:
            return True

    post_event( f"{EVLOG_ERROR}Apple Account > {PyiCloud.account_owner}, "
                f"Family Sharing List Refresh failed")

    return (PyiCloud.AADevices.devices_cnt >= 0)

#--------------------------------------------------------------------
def is_authentication_2fa_code_needed(PyiCloud, initial_setup=False):
    '''
    A wrapper for seeing if an authentication is needed and setting up the config_flow
    reauth request
    '''
    if PyiCloud is None:
        return False
    elif PyiCloud.requires_2fa:
        pass
    elif Gb.conf_data_source_MOBAPP is False:
        return False
    elif initial_setup:
        pass
    elif Gb.start_icloud3_inprocess_flag:
        return False

    if new_2fa_authentication_code_requested(PyiCloud, initial_setup):
        alert_msg =(f"{PyiCloud.username_id} > Apple Acct Authentication Needed")
        post_alert(PyiCloud.username_id, "Apple Acct Authentication Needed")

        log_warning_msg(alert_msg)

        if PyiCloud.new_2fa_code_already_requested_flag is False:
            post_event(f"{EVLOG_ALERT}{alert_msg}")
            # Tell HA to generate reauth needed notification that will be handled
            # handled in config_flow
            try:
                Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
            except Exception as err:
                log_exception(err)

            PyiCloud.new_2fa_code_already_requested_flag = True
            post_event( f"Apple Acct > {PyiCloud.account_owner}, "
                        f"Auth Request Submitted to HA")
            Gb.PyiCloud_needing_reauth_via_ha = {
                    CONF_USERNAME: PyiCloud.username,
                    CONF_PASSWORD: PyiCloud.password,
                    'account_owner': PyiCloud.account_owner}

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
def new_2fa_authentication_code_requested(PyiCloud, initial_setup=False):
    '''
    Make sure iCloud is still available and doesn't need to be authenticationd
    in 15-second polling loop

    Returns True  if Authentication is needed.
    Returns False if Authentication succeeded
    '''

    try:
        if initial_setup is False:
            if PyiCloud is None:
                event_msg =(f"{EVLOG_ALERT}iCloud Web Svcs Error, Interface has not been setup, "
                            "resetting iCloud")
                post_error_msg(event_msg)
                Gb.restart_icloud3_request_flag = True

            elif Gb.restart_icloud3_request_flag:         # via service call
                event_msg =("iCloud Restarting, Reset command issued")
                post_error_msg(event_msg)

            if PyiCloud is None:
                event_msg =("iCloud Authentication Required, will retry")
                post_error_msg(event_msg)
                return True         # Authentication needed

        if PyiCloud is None:
            return True

        #See if 2fa Verification needed
        if PyiCloud.requires_2fa is False:
            return False

        return True

    except Exception as err:
        internal_error_msg2('Apple ID Verification', traceback.format_exc)
        return True
