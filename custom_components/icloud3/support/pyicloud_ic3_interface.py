
from ..global_variables     import GlobalVariables as Gb
from ..const                import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_IC3_STARTING, EVLOG_NOTICE,
                                    CRLF, CRLF_DOT, DASH_20,
                                    ICLOUD, FAMSHR,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    )

from ..support              import start_ic3 as start_ic3
from ..support.pyicloud_ic3 import (PyiCloudService, PyiCloudFailedLoginException, PyiCloudNoDevicesException,
                                    PyiCloudAPIResponseException, PyiCloud2FARequiredException,)

from ..helpers.common       import (instr, list_to_str, delete_file, )
from ..helpers.messaging    import (post_event, post_error_msg, post_monitor_msg, post_startup_alert, log_debug_msg,
                                    log_info_msg, log_exception, log_error_msg, internal_error_msg2, _trace, _traceha, )
from ..helpers.time_util    import (time_secs, secs_to_time, secs_to_datetime, secs_to_time_str, format_age,
                                    secs_to_time_age_str, )

import os
import time
import traceback
from re import match
from homeassistant.util    import slugify


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PYICLOUD-IC3 INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_PyiCloudService_executor_job():
    '''
    This is the entry point for the hass.async_add_executor_job statement from __init__
    '''
    create_PyiCloudService(Gb.PyiCloudInit, called_from='init')

#--------------------------------------------------------------------
def create_PyiCloudService(PyiCloud, called_from='unknown'):
    #See if pyicloud_ic3 is available

    Gb.pyicloud_authentication_cnt  = 0
    Gb.pyicloud_location_update_cnt = 0
    Gb.pyicloud_calls_time          = 0.0

    if Gb.username == '' or Gb.password == '':
        # event_msg =(f"{EVLOG_ALERT}CONFIGURATION ALERT > The iCloud username or password has not been "
        #             f"configured. iCloud will not be used for location tracking")
        # post_event(event_msg)
        return

    authenticate_icloud_account(PyiCloud, called_from=called_from, initial_setup=True)

    if Gb.PyiCloud or Gb.PyiCloudInit:
        event_msg =(f"iCloud Location Services interface > Verified ({called_from})")
        post_event(event_msg)

    else:
        event_msg =(f"iCLOUD3 ERROR > Apple ID Verification is needed or "
                    f"another error occurred. The iOSApp tracking method will be "
                    f"used until the Apple ID Verification code has been entered. See the "
                    f"HA Notification area to continue. iCloud3 will then restart.")
        post_error_msg(event_msg)

#--------------------------------------------------------------------
def verify_pyicloud_setup_status():
    '''
    The PyiCloud Servicesinterface set up was started in __init__
    via create_PyiCloudService_executor_job above. The following steps are done to set up
    PyiCloudService:
        1. Initialize the variables and authenticate the account.
        2. Create the FamShr object and get the FamShr devices.
        3. Create the FmF object and get the FamShr devices.

    This function is called from Stage 4 to determine the set up status.
        1. If the set up started in __init__ is comlete, return the PyiCloudInit object
        2. If FamShr has not been completed, rerequest setting up the FamShr object.
        3. If FmF has not been completed, rerequest setting up the FmF object.
        4. Return the PyiCloudInit object after #2 and #3 above.
        5. If the the authenticate step from the original set up request is not done,
        start all over. The original request will eventually be comleted but it will
        not be used. This will prevent HA from issuing Blocking call errors indicating
        the PyiCloud session data requests must be run in the event loop.

    '''
    # if Gb.PyiCloudInit is None and Gb.PyiCloud:
    #     Gb.PyiCloudInit = Gb.PyiCloud

    init_step_needed   = list_to_str(Gb.PyiCloudInit.init_step_needed)
    init_step_complete = list_to_str(Gb.PyiCloudInit.init_step_complete)

    # PyiCloud is started early in __init__ and set up is complete
    event_msg = f"iCloud Location Svcs Interface > Started during initialization"
    if Gb.PyiCloudInit and 'Complete' in Gb.PyiCloudInit.init_step_complete:
        Gb.PyiCloud = Gb.PyiCloudInit
        event_msg += f"{CRLF_DOT}All steps completed"

    # Authenticate is completed, continue with setup of FamShr and FmF objects
    elif Gb.PyiCloudInit and 'Authenticate' in Gb.PyiCloudInit.init_step_complete:
        Gb.PyiCloud = Gb.PyiCloudInit

        event_msg += (  f"{CRLF_DOT}Completed: {init_step_complete}"
                        f"{CRLF_DOT}Inprocess: {Gb.PyiCloudInit.init_step_inprocess}"
                        f"{CRLF_DOT}Needed: {init_step_needed}")

        Gb.PyiCloud.__init__(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from='stage4')

    else:
        if Gb.PyiCloudInit:
            # __init__ set up was not authenticated, start all over
            event_msg += (  f"{CRLF_DOT}Completed: {init_step_complete}"
                            f"{CRLF_DOT}Inprocess: {Gb.PyiCloudInit.init_step_inprocess}"
                            f"{CRLF_DOT}Needed: {init_step_needed}")

        # else:
        #     event_msg += (  f"{CRLF_DOT}Completed: {init_step_complete}"
        #                     f"{CRLF_DOT}Inprocess: {Gb.PyiCloudInit.init_step_inprocess}"
        #                     f"{CRLF_DOT}Needed: Restarting the interface now")

        post_event(event_msg)

        create_PyiCloudService(Gb.PyiCloud, called_from='stage4')

#--------------------------------------------------------------------
def authenticate_icloud_account(PyiCloud, called_from='unknown', initial_setup=False):
    '''
    Authenticate the iCloud Account via pyicloud

    Arguments:
        PyiCloud - Gb.PyiCloud or Gb.PyiCloudInit object depending on called_from module
        called_from - Called from module (init or start_ic3)

    If successful - Gb.PyiCloud or Gb.PyiCloudInit = PyiCloudService object
    If not        - Gb.PyiCloud or Gb.PyiCloudInit = None
    '''

    # If not using the iCloud location svcs, nothing to do
    if (Gb.primary_data_source_ICLOUD is False
            or Gb.username == ''
            or Gb.password == ''):
        return

    try:
        Gb.pyicloud_auth_started_secs = time_secs()
        if PyiCloud and 'Complete' in Gb.PyiCloudInit.init_step_complete:
            PyiCloud.authenticate(refresh_session=True, service='find')

        elif PyiCloud:
            PyiCloud.__init__(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from=called_from)

        else:
            log_info_msg(f"Connecting to and Authenticating iCloud Location Services Interface ({called_from})")
            PyiCloud = PyiCloudService(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    called_from=called_from)

        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        display_authentication_msg(PyiCloud)

    except PyiCloudAPIResponseException as err:
        event_msg =(f"{EVLOG_ALERT}iCloud3 Error > An error occurred communicating with "
                    f"iCloud Account servers. This can be caused by:"
                    f"{CRLF_DOT}Your network or wifi is down, or"
                    f"{CRLF_DOT}Apple iCloud servers are down"
                    f"{CRLF}Error-{err}")
        post_startup_alert('Error occurred logging into the iCloud Account')

    except PyiCloudFailedLoginException as err:
        event_msg =(f"{EVLOG_ALERT}iCloud3 Error > An error occurred logging into the iCloud Account. "
                    f"Authentication Process/Error-{Gb.PyiCloud.authenticate_method[2:]})")
        post_error_msg(event_msg)
        post_startup_alert('Username/Password error logging into the iCloud Account')

        if instr(Gb.PyiCloud.authenticate_method, 'Invalid username/password'):
            Gb.PyiCloud = PyiCloud = None
            Gb.username = Gb.password = ''
            return False

        check_all_devices_online_status()
        return False

    except (PyiCloud2FARequiredException) as err:
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        return False

    except Exception as err:
        event_msg =(f"{EVLOG_ALERT}iCloud3 Error > An error occurred logging into the iCloud Account. "
                    f"Error-{err}")
        post_error_msg(event_msg)
        # log_exception(err)
        return False

    return True

#--------------------------------------------------------------------
def reset_authentication_time(PyiCloud, authentication_took_secs):
    display_authentication_msg(PyiCloud)

def display_authentication_msg(PyiCloud):
    '''
    If an authentication was done, update the count & time and display
    an Event Log message
    '''
    authentication_method = PyiCloud.authentication_method
    if authentication_method == '':
        return

    last_authenticated_time = last_authenticated_age = Gb.authenticated_time
    if last_authenticated_time > 0:
        last_authenticated_age = time_secs() - last_authenticated_time

    Gb.authenticated_time = time_secs()
    Gb.pyicloud_authentication_cnt += 1

    event_msg =(f"iCloud Acct Auth "
                f"#{Gb.pyicloud_authentication_cnt} > {authentication_method}, "
                f"Last-{secs_to_time(last_authenticated_time)}")
    if instr(authentication_method, 'Password') is False:
        event_msg += f" ({format_age(last_authenticated_age)})"


    if instr(authentication_method, 'Password'):
        post_event(event_msg)
    else:
        post_monitor_msg(event_msg)

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
    # elif Gb.data_source_IOSAPP is False:  (beta 17)
    elif Gb.conf_data_source_IOSAPP is False:
        return False
    elif initial_setup:
        pass
    elif Gb.start_icloud3_inprocess_flag:
        return False

    if new_2fa_authentication_code_requested(PyiCloud, initial_setup):
        if PyiCloud.new_2fa_code_already_requested_flag is False:
            Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)
            PyiCloud.new_2fa_code_already_requested_flag = True

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
            event_msg = (   f"Device Offline and not available > "
                            f"OfflineSince-{secs_to_time_age_str(Device.offline_secs)}")
            post_event(Device.devicename, event_msg)

        elif Device.is_pending:
            if Device.pending_secs == 0:
                Device.pending_secs = Gb.this_update_secs
            event_msg = (   f"Device status is Pending/Unknown > "
                            f"PendingSince-{secs_to_time_age_str(Device.pending_secs)}")
            post_event(Device.devicename, event_msg)

    if any_device_online_flag == False:
        event_msg = (   f"All Devices are offline or have a pending status. "
                        f"They may be in AirPlane Mode and not available")
        post_event(event_msg)

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
                Gb.restart_icloud3_request_flag = True

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

#--------------------------------------------------------------------
def pyicloud_reset_session(PyiCloud=None):
    '''
    Reset the current session and authenticate to restart pyicloud_ic3
    and enter a new verification code
    '''
    if PyiCloud is None:
        PyiCloud = Gb.PyiCloud
        requested_by = ' (Apple)'
    else:
        requested_by = ' (User)'

    if Gb.PyiCloud is None:
        return

    resetting_primary_pyicloud_flag = (PyiCloud == Gb.PyiCloud)
    try:
        if Gb.authentication_alert_displayed_flag is False:
            Gb.authentication_alert_displayed_flag = True

            if requested_by == ' (Apple)':
                alert_msg =    (f"{EVLOG_NOTICE}Select `HA Notifications Bell`, then Select `Integration Requires "
                                f"Reconfiguration > Check it out`, then `iCloud3 > Reconfigure`."
                                f"{CRLF}Note: If the code is not accepted or has expired, request a "
                                f"new code and try again")
                post_event(alert_msg)
        post_event(f"{EVLOG_NOTICE}iCLOUD ALERT > Apple ID Verification is needed {requested_by}")
        post_event(f"{EVLOG_NOTICE}Resetting iCloud Session Files")

        delete_pyicloud_cookies_session_files()

        post_event(f"{EVLOG_NOTICE}Initializing iCloud Interface")
        PyiCloud.__init__(   Gb.username, Gb.password,
                                cookie_directory=Gb.icloud_cookies_dir,
                                session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                with_family=True,
                                called_from='reset')

        # Initialize PyiCloud object to force a new one that will trigger the 2fa process
        PyiCloud = None
        Gb.verification_code = None

        authenticate_icloud_account(PyiCloud, initial_setup=True)

        post_event(f"{EVLOG_NOTICE}Waiting for 6-digit Verification Code Entry")

        Gb.EvLog.update_event_log_display(Gb.EvLog.devicename)

    except Exception as err:
        log_exception(err)

#--------------------------------------------------------------------
def delete_pyicloud_cookies_session_files(cookie_filename=None):
    '''
    Delete the cookies and session files as part of the reset_session and request_verification_code
    This is called from config_flow/setp_reauth and pyicloud_reset_session

    '''
    cookie_directory  = Gb.PyiCloud.cookie_directory
    cookie_filename   = cookie_filename or Gb.PyiCloud.cookie_filename
    session_directory = f"{cookie_directory}/session"

    delete_msg =  f"Deleting iCloud Cookie & Session Files > ({cookie_directory})"
    delete_msg += f"{CRLF_DOT}Cookies ({cookie_filename})"
    delete_file('iCloud Acct cookies', cookie_directory,  cookie_filename, delete_old_sv_file=True)
    delete_msg += f"{CRLF_DOT}Token Password ({cookie_filename}.tpw)"
    delete_file('iCloud Acct tokenpw', session_directory, f"{cookie_filename}.tpw")
    delete_msg += f"{CRLF_DOT}Session (/session/{cookie_filename})"
    delete_file('iCloud Acct session', session_directory, cookie_filename, delete_old_sv_file=True)
    post_monitor_msg(delete_msg)

#--------------------------------------------------------------------
def create_PyiCloudService_secondary(username, password,
                                        endpoint_suffix, called_from,
                                        verify_password, request_verification_code=False):
    '''
    Create the PyiCloudService object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    PyiCloud session
    '''
    return PyiCloudService( username, password,
                            cookie_directory=Gb.icloud_cookies_dir,
                            session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                            endpoint_suffix=endpoint_suffix,
                            called_from=called_from,
                            verify_password=verify_password,
                            request_verification_code=request_verification_code)
