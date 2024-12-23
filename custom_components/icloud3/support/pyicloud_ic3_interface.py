
from ..global_variables     import GlobalVariables as Gb
from ..const                import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE, EVLOG_ERROR,
                                    CRLF, CRLF_DOT, DASH_20, RED_X, CRLF_RED_MARK, CRLF_RED_STOP, CRLF_RED_ALERT,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_USERNAME, CONF_PASSWORD, CONF_TOTP_KEY, CONF_LOCATE_ALL,
                                    CONF_TRACKING_MODE, INACTIVE_DEVICE,
                                    )

from ..support              import start_ic3 as start_ic3
from ..support              import start_ic3_control
from ..support.pyicloud_ic3 import (PyiCloudValidateAppleAcct, PyiCloudService,
                                    PyiCloudNoDevicesException, PyiCloudFailedLoginException,
                                    PyiCloudAPIResponseException, PyiCloud2FARequiredException,)
from ..helpers.common       import (instr, list_to_str, list_add, list_del, is_empty, isnot_empty, )
from ..helpers              import file_io
from ..support              import config_file
from ..helpers.messaging    import (post_event, post_error_msg, post_monitor_msg,
                                    post_evlog_greenbar_msg, post_startup_alert, log_debug_msg,
                                    log_info_msg, log_exception, log_error_msg, log_warning_msg,
                                    internal_error_msg2, _evlog, _log, )
from ..helpers.time_util    import (time_now_secs, secs_to_time, format_age,
                                    format_time_age, )

import time
import pyotp
import traceback
from re import match
from homeassistant.util    import slugify


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PYICLOUD-IC3 INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_all_PyiCloudServices():
    '''
    This is the entry point for the hass.async_add_executor_job statement from __init__
    '''
    if Gb.PyiCloudValidateAppleAcct is None:
        Gb.PyiCloudValidateAppleAcct = PyiCloudValidateAppleAcct()
    post_event('Log into Apple Accounts')

    for conf_apple_acct in Gb.conf_apple_accounts:
        username   = conf_apple_acct[CONF_USERNAME]
        password   = Gb.PyiCloud_password_by_username[username]
        locate_all_devices = conf_apple_acct[CONF_LOCATE_ALL]

        if is_empty(username) or is_empty(password):
            continue

        post_evlog_greenbar_msg(f"Apple Acct > Setting up {username.split('@')[0]}")

        # Validate username/password so we know all future login attempts will be with valid apple accts
        if username not in Gb.username_valid_by_username:
            username_password_valid = \
                    Gb.PyiCloudValidateAppleAcct.validate_username_password(username, password)

            Gb.username_valid_by_username[username] = username_password_valid

        if Gb.username_valid_by_username[username]:
            log_into_apple_account(username, password, locate_all_devices)
        else:
            event_msg =(f"Apple Acct > "
                        f"{username.split('@')[0]}, Invalid Username or Password")
            post_event( f"{EVLOG_ALERT}{event_msg}")
            post_startup_alert(event_msg)

    post_evlog_greenbar_msg('')

    Gb.startup_lists['Gb.PyiCloud_by_username']       = Gb.PyiCloud_by_username
    Gb.startup_lists['Gb.username_valid_by_username'] = Gb.username_valid_by_username
    Gb.startup_lists['Gb.username_pyicloud_503_connection_error'] = Gb.username_pyicloud_503_connection_error

#--------------------------------------------------------------------
def retry_apple_acct_login():
    '''
    Retry to log into the Apple acct after receiving a 503 Connection Error.
    This is done in the 15-min cycle of icoud3_main
    '''
    for username in Gb.username_pyicloud_503_connection_error:
        conf_apple_acct, apple_acct_id = config_file.conf_apple_acct(username)
        password = conf_apple_acct[CONF_PASSWORD]
        locate_all_devices = conf_apple_acct[CONF_LOCATE_ALL]

        PyiCloud = log_into_apple_account(username, password, locate_all_devices)

        if PyiCloud and PyiCloud.is_authenticated:
            post_event(f"{EVLOG_ERROR}Apple Acct > {PyiCloud.account_owner}, Login Successful")
            list_del(Gb.username_pyicloud_503_connection_error, username)

            list_add(Gb.usernames_setup_error_retry_list, username)
            start_ic3_control.stage_4_setup_data_sources_retry()

        # else:
        #     retry_at = secs_to_time(timenow_secs() + 900)
        #     post_event( f"Apple Acct > {username_base}, Login Failed, "
        #                 f"{PyiCloud.response_code_desc}, "
        #                 f"Retry At-{retry_at}")

    post_evlog_greenbar_msg('')

#--------------------------------------------------------------------
def check_all_apple_accts_valid_upw():
    '''
    Cycle through the apple accounts and validate that each one is valid

    This is done when iCloud3 starts in __init__
    '''
    # if Gb.PyiCloudValidateAppleAcct is None:
    #     Gb.PyiCloudValidateAppleAcct = PyiCloudValidateAppleAcct()

    results_msg = ''
    cnt = -1
    alert_symb = ''
    for conf_apple_acct in Gb.conf_apple_accounts:
        cnt += 1

        username = conf_apple_acct[CONF_USERNAME]
        password = Gb.PyiCloud_password_by_username[username]

        if is_empty(username) or is_empty(password):
            # Gb.username_valid_by_username[f"AppleAcctNoUserPW-#{cnt}"] = False
            continue

        # Validate username/password so we know all future login attempts will be with valid apple accts
        valid_upw = Gb.PyiCloudValidateAppleAcct.validate_username_password(username, password)

        Gb.username_valid_by_username[username]= valid_upw

        # if valid_apple_acct is False: alert_symb = EVLOG_ALERT
        crlf_symb = CRLF_DOT if valid_upw else f"{CRLF_RED_ALERT}"
        results_msg += f"{crlf_symb}{username}, Valid-{valid_upw}"

    post_event(f"{alert_symb}Verify Apple Account Username/Password{results_msg}")

    Gb.startup_lists['Gb.username_valid_by_username'] = Gb.username_valid_by_username

#--------------------------------------------------------------------
def log_into_apple_account(username, password, locate_all_devices=None):
    '''
    Log in and Authenticate the Apple Account via pyicloud

    If successful - PyiCloud = PyiCloudService object
    If not        - PyiCloud = None
    '''

    # If not using the iCloud location svcs, nothing to do
    if (Gb.use_data_source_ICLOUD is False
            or username == ''
            or password == ''):
        return

    locate_all_devices = locate_all_devices \
                            if   locate_all_devices is not None \
                            else PyiCloud.locate_all_devices if PyiCloud.locate_all_devices is not None \
                            else True

    login_err = 0
    post_evlog_greenbar_msg(f"Apple Acct > Setting up {username.split('@')[0]}")

    try:
        PyiCloud = Gb.PyiCloud_by_username.get(username)

        pyicloud_msg = (f"{PyiCloud=}")
        if PyiCloud:
            pyicloud_msg += f"{PyiCloud.is_DeviceSvc_setup_complete=} {PyiCloud.DeviceSvc=}"
            if PyiCloud.DeviceSvc:
                pyicloud_msg += f"{PyiCloud.RawData_by_device_id.values()=}"
        username_base = username.split('@')[0]
        debug_msg_hdr =f"APPLE ACCT SETUP > {username_base}, Step-"
        log_debug_msg(f"{debug_msg_hdr}0, Login Started, {pyicloud_msg}")

        # # Refresh existing PyiCloud/iCloud
        # if PyiCloud and PyiCloud.connection_error_retry_cnt > 5:
        #     return

        if (PyiCloud
                and PyiCloud.is_DeviceSvc_setup_complete
                and PyiCloud.DeviceSvc):
            PyiCloud.dup_icloud_dname_cnt = {}

            # PyiCloud.DeviceSvc.refresh_client()
            PyiCloud.refresh_icloud_data(locate_all_devices=True)

            pyicloud_msg = f"{PyiCloud=} {PyiCloud.is_DeviceSvc_setup_complete=} {PyiCloud.DeviceSvc=}"
            if PyiCloud.DeviceSvc:
                pyicloud_msg += f"{PyiCloud.RawData_by_device_id.values()=}"
            log_debug_msg(f"{debug_msg_hdr}1, Request iCloud Refresh, {pyicloud_msg}")
            post_event(f"Apple Acct > {PyiCloud.account_owner}, Device Data Refreshed")

        # Setup iCloud
        elif (PyiCloud
                and PyiCloud.is_DeviceSvc_setup_complete):

            try:
                PyiCloud.create_DeviceSvc_object()
                Gb.PyiCloud_by_username[username] = PyiCloud

                pyicloud_msg = f"{PyiCloud=} {PyiCloud.is_DeviceSvc_setup_complete=} {PyiCloud.DeviceSvc=}"
                if PyiCloud.DeviceSvc:
                    pyicloud_msg += f"{PyiCloud.RawData_by_device_id.values()=}"
                log_debug_msg(f"{debug_msg_hdr}2, Create DeviceSvc, {pyicloud_msg}")
                post_event(f"Apple Acct > {PyiCloud.account_owner}, iCloud Created & Refreshed")

                return PyiCloud

            except Exception as err:
                log_exception(err)

        # Setup PyiCloud and iCloud
        else:
            try:
                PyiCloud = None
                PyiCloud = PyiCloudService( username, password,
                                            locate_all_devices=locate_all_devices,
                                            cookie_directory=Gb.icloud_cookie_directory,
                                            session_directory=Gb.icloud_session_directory)

                # Stage 4 checks to see if PyiCloud exists and it has RawData device info. These values exists
                # if the __init__ login was completed. However, if it was not completed and they do not exist,
                # Stage 4 will do another login and set these values when it finishes, which is before the
                # __init__ is complete. Do not set them again when __init__ login finially completes.

                pyicloud_msg = (f"{PyiCloud.account_owner_username}, "
                                f"Complete={PyiCloud.is_DeviceSvc_setup_complete}, ")

            except Exception as err:
                log_exception(err)

            if PyiCloud.DeviceSvc:
                if is_empty(PyiCloud.RawData_by_device_id):
                    PyiCloud.refresh_icloud_data(locate_all_devices=True)

                rawdata_items = [_RawData.fname_device_id
                                        for _RawData in PyiCloud.RawData_by_device_id.values()]

                if is_empty(rawdata_items):
                    PyiCloud.refresh_icloud_data(locate_all_devices=True)

                    rawdata_items = [_RawData.fname_device_id
                                            for _RawData in PyiCloud.RawData_by_device_id.values()]

                pyicloud_msg += f"RawDataItems-({list_to_str(rawdata_items)})"

            log_debug_msg(f"{debug_msg_hdr}3, Setup PyiCloud, {pyicloud_msg}")
            code_msg = f" ({PyiCloud.response_code})"
            if PyiCloud.is_authenticated:
                post_event(f"Apple Acct > {PyiCloud.account_owner}, "
                            f"Login Successful, "
                            f"{PyiCloud.auth_method}")
            else:
                retry_at = secs_to_time(time_now_secs() + 900)
                post_event( f"Apple Acct > {username_base}, Login Failed, "
                        f"{PyiCloud.response_code_desc}, "
                        f"Retry At-{retry_at}")

        verify_icloud_device_info_received(PyiCloud)
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)

        #display_authentication_msg(PyiCloud)

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
        list_add(Gb.username_pyicloud_503_connection_error, username)

    else:
        list_add(Gb.usernames_setup_error_retry_list, username)

    # list_del(Gb.PyiCloud_by_username, username)
    post_error_msg( f"{EVLOG_ALERT}{login_err}")
    post_startup_alert(f"Apple Acct > {username_base}, Login Failed")

    return PyiCloud

#--------------------------------------------------------------------
def verify_icloud_device_info_received(PyiCloud):
    if (PyiCloud is None
            or PyiCloud.DeviceSvc is None):
        return False

    if PyiCloud.DeviceSvc.devices_cnt >= 0:
        return True

    Gb.get_ICLOUD_devices_retry_cnt = 0

    while Gb.get_ICLOUD_devices_retry_cnt < 8:
        Gb.get_ICLOUD_devices_retry_cnt += 1
        if Gb.get_ICLOUD_devices_retry_cnt > 1:
            post_event( f"Apple Acct > {PyiCloud.account_owner}, "
                        f"Family Sharing List Refresh "
                        f"(#{Gb.get_ICLOUD_devices_retry_cnt} of 8)")

        PyiCloud.refresh_icloud_data(locate_all_devices=True)

        if PyiCloud.DeviceSvc.devices_cnt >= 0:
            return True

    post_event( f"{EVLOG_ERROR}Apple Account > {PyiCloud.account_owner}, "
                f"Family Sharing List Refresh failed")

    return (PyiCloud.DeviceSvc.devices_cnt >= 0)

#--------------------------------------------------------------------
# def display_authentication_msg(PyiCloud):
#     '''
#     If an authentication was done, update the count & time and display
#     an Event Log message
#     '''
#     authentication_method = PyiCloud.authentication_method
#     if authentication_method == '':
#         return

#     last_authenticated_secs = PyiCloud.last_authenticated_secs
#     PyiCloud.last_authenticated_secs = time_now_secs()
#     PyiCloud.authentication_cnt += 1

#     event_msg =(f"Apple Acct > {PyiCloud.account_owner}, "
#                 f"Auth #{PyiCloud.authentication_cnt} > {authentication_method}")
#     post_monitor_msg(event_msg)

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
        alert_msg =(f"Apple Acct > {PyiCloud.account_owner}, Authentication Needed")
        post_startup_alert(alert_msg)
        log_warning_msg(alert_msg)

        if PyiCloud.new_2fa_code_already_requested_flag is False:
            post_event(f"{EVLOG_ALERT}{alert_msg}")
            # Tell HA to generate reauth needed notification that will be handled
            # handled in config_flow
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

            PyiCloud.new_2fa_code_already_requested_flag = True
            post_event( f"Apple Acct > {PyiCloud.account_owner}, "
                        f"Auth Request Submitted to HA")
            Gb.PyiCloud_needing_reauth_via_ha = {
                    CONF_USERNAME: PyiCloud.username,
                    CONF_PASSWORD: PyiCloud.password,
                    'account_owner': PyiCloud.account_owner}

#--------------------------------------------------------------------
def send_totp_key(conf_apple_accts):
    '''
    The 30-sec check in icloud3_main identified apple accts that need to be verified
    using the otp token. Generate the token and send to the Apple acct
    '''
    return

    for conf_apple_acct in conf_apple_accts:
        PyCloud = Gb.PyiCloud_by_username[conf_apple_acct[CONF_USERNAME]]
        OTP = pyotp.TOTP(conf_apple_acct[CONF_TOTP_KEY].replace('-', ''))
        otp_code = OTP.now()
        #_evlog(f"{conf_apple_acct[CONF_USERNAME]} {otp_code}")
    pass

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
