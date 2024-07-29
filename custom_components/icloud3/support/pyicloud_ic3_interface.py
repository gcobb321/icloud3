
from ..global_variables     import GlobalVariables as Gb
from ..const                import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE,
                                    CRLF, CRLF_DOT, DASH_20,
                                    ICLOUD, FAMSHR,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    CONF_USERNAME
                                    )

from ..support              import start_ic3 as start_ic3
from ..support.pyicloud_ic3 import (PyiCloudService, PyiCloudFailedLoginException, PyiCloudNoDevicesException,
                                    PyiCloudAPIResponseException, PyiCloud2FARequiredException,)

from ..helpers.common       import (instr, list_to_str, list_add, list_del, delete_file, )
from ..helpers.messaging    import (post_event, post_error_msg, post_monitor_msg, post_startup_alert, log_debug_msg,
                                    log_info_msg, log_exception, log_error_msg, internal_error_msg2, _trace, _traceha, )
from ..helpers.time_util    import (time_now_secs, secs_to_time, format_age,
                                    format_time_age, )

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
    create_PyiCloudService(Gb.PyiCloudInit, instance='initial')

#--------------------------------------------------------------------
def create_PyiCloudService(PyiCloud, instance='unknown'):
    #See if pyicloud_ic3 is available

    Gb.pyicloud_authentication_cnt  = 0
    Gb.pyicloud_location_update_cnt = 0
    Gb.pyicloud_calls_time          = 0.0

    if Gb.username == '' or Gb.password == '':
        return

    if authenticate_icloud_account(PyiCloud, instance=instance, initial_setup=True):
        if ((Gb.PyiCloud and Gb.PyiCloud.is_authenticated)
                or (Gb.PyiCloudInit and Gb.PyiCloudInit.is_authenticated)):
            event_msg =(f"iCloud Location Service interface > Verified ({instance})")
            post_event(event_msg)

            if Gb.PyiCloud:
                log_debug_msg(f"PyiCloud Instance Verified > {Gb.PyiCloud.instance}")
            if Gb.PyiCloudInit:
                log_debug_msg(f"PyiCloudInit Instance Verified > {Gb.PyiCloudInit.instance}")
    else:
        event_msg =(f"iCloud Location Service interface > Not Verified ({instance})")
        post_event(event_msg)

#--------------------------------------------------------------------
def verify_pyicloud_setup_status():
    '''
    The PyiCloud Services interface set up was started in __init__
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
    # iCloud was never started
    if Gb.PyiCloudInit is None:
        return False

    # The verify can be requested during started or after a restart request before
    # the restart has begun
    if (Gb.restart_icloud3_request_flag
            and Gb.start_icloud3_inprocess_flag):
        Gb.PyiCloudInit.init_step_needed   = ['FamShr']
        Gb.PyiCloudInit.init_step_complete = ['Setup', 'Authenticate']

    if 'Complete' in Gb.PyiCloudInit.init_step_complete:
        Gb.PyiCloud = Gb.PyiCloudInit

        log_debug_msg(f"PyiCloud Instance Selected > {Gb.PyiCloud.instance}")
        if _get_famshr_devices(Gb.PyiCloud):
            return True

        if Gb.get_FAMSHR_devices_retry_cnt == 0:
            post_event(f"iCloud Location Svcs > Setup Complete")
            return
        else:
            if Gb.PyiCloud.FamilySharing:
                Gb.PyiCloud.FamilySharing.refresh_client()
                post_event( f"iCloud Location Svcs > Refreshing FamShr Data "
                            f"(#{Gb.get_FAMSHR_devices_retry_cnt})")
                return True
            else:
                Gb.PyiCloudInit.init_step_needed = ['FamShr']

    if 'Authenticate' not in Gb.PyiCloudInit.init_step_complete:
        Gb.PyiCloudInit._set_step_completed('Cancel')
        create_PyiCloudService(Gb.PyiCloud, instance='startup')

        Gb.PyiCloud = Gb.PyiCloud or Gb.PyiCloudInit
        if (Gb.PyiCloud is None
                or 'Authenticate' not in Gb.PyiCloud.init_step_complete):
            create_PyiCloudService(Gb.PyiCloud, instance='startup')
        Gb.PyiCloud = Gb.PyiCloud or Gb.PyiCloudInit
        if Gb.PyiCloud is None:
            return False

        log_debug_msg(f"PyiCloud Instance Created > {Gb.PyiCloud.instance}")

    # FamShare object exists, check/refresh the devices list
    Gb.PyiCloud = Gb.PyiCloud or Gb.PyiCloudInit
    if 'FamShr' in Gb.PyiCloud.init_step_complete:
        if _get_famshr_devices(Gb.PyiCloud):
            return True

    # Create FamShare object and then check/refresh the devices list
    Gb.PyiCloud.create_FamilySharing_object()
    Gb.PyiCloud.init_step_needed == []
    Gb.PyiCloud._set_step_completed('FamShr')
    Gb.PyiCloud._set_step_completed('Complete')
    if _get_famshr_devices(Gb.PyiCloud):
        return True

    return False

#--------------------------------------------------------------------
def _get_famshr_devices(PyiCloud):
    if PyiCloud is None:
        return False
    if PyiCloud.FamilySharing.devices_cnt >= 0:
        return True

    Gb.get_FAMSHR_devices_retry_cnt = 0
    while Gb.get_FAMSHR_devices_retry_cnt < 8:
        Gb.get_FAMSHR_devices_retry_cnt += 1
        if Gb.get_FAMSHR_devices_retry_cnt > 1:
            post_event( f"Family Sharing List Refresh "
                        f"(#{Gb.get_FAMSHR_devices_retry_cnt} of 8)")

        PyiCloud.FamilySharing.refresh_client()
        if PyiCloud.FamilySharing.devices_cnt >= 0:
            return True

    return (PyiCloud.FamilySharing.devices_cnt >= 0)

#--------------------------------------------------------------------
def authenticate_icloud_account(PyiCloud, instance='unknown', initial_setup=False):
    '''
    Authenticate the iCloud Account via pyicloud

    Arguments:
        PyiCloud - Gb.PyiCloud or Gb.PyiCloudInit object depending on instance module
        instance - Called from module (init or start_ic3)

    If successful - Gb.PyiCloud or Gb.PyiCloudInit = PyiCloudService object
    If not        - Gb.PyiCloud or Gb.PyiCloudInit = None
    '''

    # If not using the iCloud location svcs, nothing to do
    if (Gb.primary_data_source_ICLOUD is False
            or Gb.username == ''
            or Gb.password == ''):
        return

    this_fct_error_flag = True

    try:
        Gb.pyicloud_auth_started_secs = time_now_secs()
        if PyiCloud and 'Complete' in Gb.PyiCloudInit.init_step_complete:
            PyiCloud.authenticate(refresh_session=True, service='find')

        elif PyiCloud:
            PyiCloud.__init__(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    instance=instance)
            log_debug_msg(f"PyiCloud Instance Initialized > {PyiCloud.instance}")

        else:
            log_info_msg(f"Connecting to and Authenticating iCloud Location Service Interface ({instance})")
            PyiCloud = PyiCloudService(Gb.username, Gb.password,
                                    cookie_directory=Gb.icloud_cookies_dir,
                                    session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                    instance=instance)

            #PyiCloud.instance = instance    #f"{instance}-{str(id(PyiCloud))[-5:]}"
            log_debug_msg(f"PyiCloud Instance Created > {PyiCloud.instance}")

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
                    f"{err})")
                    # f"Authentication Process, Error-({Gb.PyiCloud.authenticate_method[2:]})")
        post_error_msg(event_msg)
        post_startup_alert('iCloud Account Login Error')

        Gb.PyiCloud = Gb.PyiCloudInit = PyiCloud = None
        Gb.username = Gb.password = ''
        return False

    except PyiCloud2FARequiredException as err:
        is_authentication_2fa_code_needed(PyiCloud, initial_setup=True)
        return False

    except Exception as err:
        if this_fct_error_flag is False:
            log_exception(err)
            return

        event_msg =(f"{EVLOG_ALERT}iCloud3 Error > An error occurred logging into the iCloud Account. "
                    f"Error-{err}")
        post_error_msg(event_msg)
        log_exception(err)
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

    last_authenticated_time =  Gb.authenticated_time

    Gb.authenticated_time = time_now_secs()
    Gb.pyicloud_authentication_cnt += 1

    event_msg =(f"iCloud Acct Auth "
                f"#{Gb.pyicloud_authentication_cnt} > {authentication_method}, "
                f"Last-{secs_to_time(last_authenticated_time)}")
    if instr(authentication_method, 'Password') is False:
        event_msg += f" ({format_age(last_authenticated_time)})"


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
    elif Gb.conf_data_source_MOBAPP is False:
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
                post_event( f"{EVLOG_NOTICE}Select `HA Notifications Bell`, then Select `Integration Requires "
                            f"Reconfiguration > Check it out`, then `iCloud3 > Reconfigure`."
                            f"{CRLF}Note: If the code is not accepted or has expired, request a "
                            f"new code and try again")
        post_event(f"{EVLOG_NOTICE}iCLOUD ALERT > Apple ID Verification is needed {requested_by}")
        post_event(f"{EVLOG_NOTICE}Resetting iCloud Session Files")

        delete_pyicloud_cookies_session_files()

        post_event(f"{EVLOG_NOTICE}Initializing iCloud Interface")
        PyiCloud.__init__(   Gb.username, Gb.password,
                                cookie_directory=Gb.icloud_cookies_dir,
                                session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                                with_family=True,
                                instance='reset')

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
                                        endpoint_suffix, instance,
                                        verify_password, request_verification_code=False):
    '''
    Create the PyiCloudService object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    PyiCloud session
    '''
    PyiCloud = PyiCloudService( username, password,
                            cookie_directory=Gb.icloud_cookies_dir,
                            session_directory=(f"{Gb.icloud_cookies_dir}/session"),
                            endpoint_suffix=endpoint_suffix,
                            instance=instance,
                            verify_password=verify_password,
                            request_verification_code=request_verification_code)

    #PyiCloud.instance = instance    #f"{instance}-{str(id(PyiCloud))[-5:]}"

    log_debug_msg(f"PyiCloud Instance Created > {PyiCloud.instance}")
    return PyiCloud

def create_FamilySharing_secondary(PyiCloud, config_flow_login):

    FamShr = PyiCloud.create_FamilySharing_object(config_flow_login)
    return FamShr
