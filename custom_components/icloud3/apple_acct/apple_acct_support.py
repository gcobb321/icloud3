
from ..global_variables import GlobalVariables as Gb
from ..const            import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE, EVLOG_ERROR,
                                    ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    INACTIVE, )
from ..const_config     import (CONF_APPLE_ACCT, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_TRACKING_MODE, )
from ..const_char       import (NL, NL3, CRLF, CRLF_DOT, DASH_20, RED_X, CRLF_RED_MARK,
                                CRLF_RED_STOP, RED_ALERT, CRLF_RED_ALERT, CRLF_CHK, )


from .apple_acct        import (AppleAcctManager,
                                AppleAcctNoDevicesException, AppleAcctFailedLoginException,
                                AppleAcctAPIResponseException, AppleAcct2FARequiredException,)

# from ..startup          import start_ic3_control
from ..utils.messaging  import (post_event, post_alert, post_alert, post_error_msg, post_monitor_msg,
                                post_greenbar_msg, update_alert_sensor, log_banner,
                                post_repair_issue, clear_repair_issue,
                                log_debug_msg, log_info_msg, log_exception, log_error_msg, log_warning_msg,
                                internal_error_msg2, _evlog, _log, )
from ..utils.time_util  import (time_now_secs, secs_to_time, format_age, secs_to_hhmm,
                                format_time_age, )
from ..utils.utils      import (instr, list_to_str, list_add, list_del, dict_del,
                                is_empty, isnot_empty,
                                apple_user, is_running_in_event_loop,)
from ..startup          import config_file
from ..utils            import file_io

#--------------------------------------------------------------------
import asyncio
import traceback
from re import match
from os import path

APPLE_ACCT_ALERT_MSG_REAUTH_DAYS = [-5, 10, 20, 88, 89, 86, 87]
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   APPLE ACCT INTERFACE FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def retry_apple_acct_login_after_error():
    '''
    Retry logging into and authenticating the Apple account if an error was encountered when
    starting iCloud3. This will retry the 503 error authenticating the acct via PasswordSRP

    This is checked every 5-mins in the icloud3_main._main_5sec_loop_special_time_control function
    '''
    for apple_id, AppleAcct in Gb.AppleAcct_error_by_apple_id.items():
        if (AppleAcct.error_next_retry_secs == 0
                or AppleAcct.error_next_retry_secs > time_now_secs()):
            continue

        AppleAcct.authenticate_and_refresh_data()
        if AppleAcct.login_successful:
            AppleAcct.setup_error(None)
        else:
            AppleAcct.error_retry_cnt += 1
            if AppleAcct.error_retry_cnt < 6:
                AppleAcct.error_next_retry_secs += AppleAcct.error_retry_cnt * 600
            else:
                AppleAcct.error_next_retry_secs += 3600

            post_alert( f"Apple Acct > {AppleAcct.apple_user}, "
                        f"Retry Login (#{AppleAcct.error_retry_cnt}) "
                        f"at {secs_to_hhmm(AppleAcct.error_next_retry_secs)}")
            alert_msg =(f"Apple Login Failed, {AppleAcct.error_reason}, "
                        f"Retry at {secs_to_hhmm(AppleAcct.error_next_retry_secs)}")
            update_alert_sensor(Source=AppleAcct, error='login_failed', alert_msg=alert_msg)


#--------------------------------------------------------------------
def log_into_apple_account(apple_id, password, apple_server_location, locate_all_devices=None):
    '''
    Log in and Authenticate the Apple Account via pyicloud

    If successful - AppleAcct = AppleAcctManager object
    If not        - AppleAcct = None
    '''
    # If not using the iCloud location svcs, nothing to do
    if (Gb.use_data_source_ICLOUD is False
            or apple_id == ''
            or password == ''):
        return

    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

    if locate_all_devices is not None:
        locate_all_devices = locate_all_devices
    elif AppleAcct and AppleAcct.locate_all_devices is not None:
        locate_all_devices = AppleAcct.locate_all_devices
    else:
        True

    login_err = 0
    post_greenbar_msg(f"Apple Acct > Logging into {apple_user(apple_id)}")

    try:
        if Gb.internet_error:
            post_alert( f"INTERNET CONNECTION ERROR > "
                        f"Apple Acct not available:"
                        f"{CRLF_DOT}{apple_user(apple_id)}")
            return None

        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

        # Make sure the Device Service set up was completed. It will not be
        # if there was a connection error during startup
        if AppleAcct and AppleAcct.is_AADevices_setup_complete is False:
            AppleAcct.create_AADevices_object()
            setup_status_msg(AppleAcct, "0, Setup Devices", apple_id)

        if (AppleAcct and AppleAcct.is_AADevices_setup_complete
                and AppleAcct.AADevices):
            AppleAcct.dup_icloud_dname_cnt = {}
            refresh_AppleAcct_AADdevices_data(AppleAcct)

        # Setup iCloud
        elif (AppleAcct and AppleAcct.is_AADevices_setup_complete):
            AppleAcct.create_AADevices_object()
            setup_status_msg(AppleAcct, "2, Create AADevices")

        # Setup AppleAcct and iCloud
        else:
            try:
                AppleAcct = create_AppleAcct(apple_id, password, apple_server_location, locate_all_devices)
            except Exception as err:
                log_exception(err)

        verify_device_info_received(AppleAcct)
        is_authentication_2fa_code_needed(AppleAcct, initial_setup=True)

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
        login_err += ", Will retry logging into the Apple Account later"

    except Exception as err:
        AppleAcct = Gb.AppleAcctLoggingInto
        login_err = str(err)
        log_exception(err)

    if apple_id in Gb.AppleAcct_error_by_apple_id:
        reason = f"{AppleAcct.error_reason} ({AppleAcct.error_codes})"
    else:
        reason = 'Unknown'

    post_error_msg( f"{EVLOG_ALERT}{login_err}")
    update_alert_sensor(Source=AppleAcct, error='login_failed',
                        alert_msg=f"Apple Acct Login Failed, {reason}")

    return AppleAcct

#....................................................................
def refresh_AppleAcct_AADdevices_data(AppleAcct):
    '''
    Refresh the device data for an existing Apple acct
    '''
    AppleAcct.refresh_icloud_data(locate_all_devices=True)

    setup_status_msg(AppleAcct, "1, Refresh iCloud Devices")

#....................................................................
def create_AppleAcct_validate_upw(apple_id, password):
    '''
    Create a lightweight, validate-only AppleAcctManager used solely to check
    that a apple_id/password is valid via a SRP signin/init+signin/complete
    exchange (AppleAcct.validate_upw_via_srp).

    The session is set up but the full login, data refresh and global AppleAcct
    registration are skipped (srp_validate_only=True), so this does NOT replace
    any real AppleAcct in Gb.AppleAcct_by_apple_id.

    Return:
        - AppleAcctManager object (session ready for the SRP validation)
        - None if an internet error occurred or the object could not be created
    '''
    AppleAcct = None
    try:
        AppleAcct = AppleAcctManager(
                            apple_id,
                            password,
                            apple_server_location='usa',
                            locate_all_devices=False,
                            cookie_directory=Gb.icloud_cookies_directory,
                            session_directory=Gb.icloud_session_directory,
                            srp_validate_only=True,
                            validate_aa_upw=True)

    except Exception as err:
        log_exception(err)

    if Gb.internet_error:
        post_alert( f"INTERNET CONNECTION ERROR > "
                    f"Apple Acct unavailable:"
                    f"{CRLF_DOT}{apple_user(apple_id)}")
        return None

    if AppleAcct is None:
        post_alert( f"Apple Acct > Apple Acct unavailable"
                    f"{CRLF_DOT}{apple_user(apple_id)}")
        return None

    return AppleAcct

#....................................................................
def create_AppleAcct(apple_id, password, apple_server_location, locate_all_devices):
    try:
        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
        if AppleAcct:
            AppleAcct.__init__(
                                apple_id,
                                password,
                                apple_server_location=apple_server_location,
                                locate_all_devices=locate_all_devices,
                                cookie_directory=Gb.icloud_cookies_directory,
                                session_directory=Gb.icloud_session_directory)

        if AppleAcct and AppleAcct.is_AADevices_setup_complete is False:
            dict_del(Gb.AppleAcct_by_apple_id, apple_id)
            dict_del(Gb.AppleAcct_password_by_apple_id, apple_id)
            AppleAcct = None

        if AppleAcct is None:
            AppleAcct = AppleAcctManager(
                                apple_id,
                                password,
                                apple_server_location=apple_server_location,
                                locate_all_devices=locate_all_devices,
                                cookie_directory=Gb.icloud_cookies_directory,
                                session_directory=Gb.icloud_session_directory)

    except Exception as err:
        log_exception(err)

    if Gb.internet_error:
        post_alert( f"INTERNET CONNECTION ERROR > "
                    f"Apple Acct unavailable:"
                    f"{CRLF_DOT}{apple_user(apple_id)}")
        return None

    if AppleAcct is None:
        post_alert( f"Apple Acct > Apple Acct unavailable"
                    f"{CRLF_DOT}{apple_user(apple_id)}")
        return None

    if AppleAcct.AADevices:
        if is_empty(AppleAcct.AADev_by_device_id):
            AppleAcct.refresh_icloud_data(locate_all_devices=True)

        aadevdata_items = [_AADev.dname_device_id
                                for _AADev in AppleAcct.AADev_by_device_id.values()]

        # Refresh devices if none returned
        if is_empty(aadevdata_items):
            AppleAcct.refresh_icloud_data(locate_all_devices=True)

            aadevdata_items = [_AADev.dname_device_id
                                    for _AADev in AppleAcct.AADev_by_device_id.values()]

    setup_status_msg(AppleAcct, "3, Create AppleAcct & Devices", apple_id)

    return AppleAcct

#....................................................................
def setup_status_msg(AppleAcct, setup_method, apple_id=None):

    if AppleAcct is None:
        post_event(f"Apple Acct > Error setting up {apple_id}, ")
        log_debug_msg(  f"APPLE ACCT SETUP > Step-{setup_method}")
        return

    dev_data = list(AppleAcct.AADev_by_device_id.values()) if AppleAcct.AADevices else []
    aadevdata_items = [_AADev.dname_device_id
                                    for _AADev in AppleAcct.AADev_by_device_id.values()]
    # post_event(f"Apple Acct > {AppleAcct.account_owner}, iCloud Data Handler Setup")
    log_debug_msg(  f"APPLE ACCT SETUP > {AppleAcct.apple_user} ({AppleAcct.account_owner}), "
                    f"Method-{setup_method}, "
                    f"Setup Complete-{AppleAcct.is_AADevices_setup_complete}")
    log_debug_msg(  f"APPLE ACCT SETUP > Devices-{list_to_str(aadevdata_items)}")

#--------------------------------------------------------------------
def verify_device_info_received(AppleAcct):
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
    elif AppleAcct.is_reauth_needed:
        pass
    elif Gb.conf_data_source_MOBAPP is False:
        return False
    elif initial_setup:
        pass
    elif Gb.is_icloud3_startup_inprocess:
        return False

    alert_msg = ''
    if (new_2fa_authentication_code_requested(AppleAcct, initial_setup)
            and AppleAcct.was_ha_auth_code_alert_sent is False):
        alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_reauth_needed_secs)})"
        post_alert(f"{AppleAcct.apple_user_short} > {alert_msg}")
        update_alert_sensor(Source=AppleAcct, error='auth_needed', alert_msg=alert_msg)

        if Gb.AppleAcct_reauth_needed is None:
            Gb.AppleAcct_reauth_needed = AppleAcct

    # Post the Repairs issue when Apple starts asking for the Terms of Use, remove it
    # when they were accepted somewhere else (www.icloud.com). The issue posted
    # during startup is handled by start_ic3._check_apple_acct_status_issues
    if AppleAcct.terms_of_use_update_needed:
        if AppleAcct.terms_of_use_repair_issue_posted is False:
            alert_msg = ("Apple Acct > Accept `Terms of Use` needed "
                            "(HA Repairs or Authenticate Apple Account Sign-in)")
            post_alert(f"{AppleAcct.apple_user} > {alert_msg}")
            log_warning_msg(f"{AppleAcct.apple_user} > {alert_msg}")
            post_repair_issue_aa_terms_of_use(AppleAcct)

    elif AppleAcct.terms_of_use_repair_issue_posted:
        clear_repair_issue_aa_terms_of_use(AppleAcct)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   HA REPAIRS ISSUES FOR THE APPLE ACCT STATUS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
# The issue's text is in 'issues' in strings.json & translations/en.json. The
# translation key is the issue_id prefix.
REPAIR_ISSUE_TERMS_OF_USE = 'apple_acct_terms_of_use'
REPAIR_ISSUE_ACCT_LOCKED  = 'apple_acct_locked'

#--------------------------------------------------------------------
def apple_acct_repair_issue_id(issue, AppleAcct):
    '''
    The full apple_id is used. The apple_user ('gary@') is the same for
    gary@gmail.com and gary@icloud.com.
    '''
    return f"{issue}_{AppleAcct.apple_id}"

#--------------------------------------------------------------------
def post_repair_issue_aa_terms_of_use(AppleAcct):
    '''
    Post the Repairs issue asking to accept Apple's Terms of Use. Submit runs
    start_ic3.repair_issue_fix_aa_terms_of_use.
    '''
    issue_id = post_repair_issue(
                issue_id   = apple_acct_repair_issue_id(REPAIR_ISSUE_TERMS_OF_USE, AppleAcct),
                alert_key  = AppleAcct.apple_id,
                title      = "Accept Apple Terms of Use needed",
                alert_msg  = '',
                fix_action = 'accept_terms_of_use',
                fix_data   = {'apple_id': AppleAcct.apple_id},
                severity   = 'error',
                translation_key = REPAIR_ISSUE_TERMS_OF_USE,
                translation_placeholders = {'account': AppleAcct.apple_user})

    AppleAcct.terms_of_use_repair_issue_posted = True

    return issue_id

#--------------------------------------------------------------------
def clear_repair_issue_aa_terms_of_use(AppleAcct):
    clear_repair_issue(apple_acct_repair_issue_id(REPAIR_ISSUE_TERMS_OF_USE, AppleAcct))

    AppleAcct.terms_of_use_repair_issue_posted = False

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
                Gb.was_icloud3_restart_requested = True

            elif Gb.was_icloud3_restart_requested:         # via service call
                event_msg =("iCloud Restarting, Reset command issued")
                post_error_msg(event_msg)

            if AppleAcct is None:
                event_msg =("iCloud Authentication Required, will retry")
                post_error_msg(event_msg)
                return True         # Authentication needed

        if AppleAcct is None:
            return True

        #See if 2fa Verification needed
        if AppleAcct.is_reauth_needed is False:
            return False

        return True

    except Exception as err:
        internal_error_msg2('Apple ID Verification', traceback.format_exc)
        return True

#--------------------------------------------------------------------
def issue_reauth_in_days_alert_msg(evlog_msg=False):
    '''
    Check to see if an Apple acct is approaching  it's
    reauthentication date. if it is,  issue an alert warning message
    '''
    for AppleAcct in Gb.AppleAcct_by_apple_id.values():
        reauth_in_days, reauth_msg = \
                AppleAcct.get_next_reauth_in_days_info_msg(APPLE_ACCT_ALERT_MSG_REAUTH_DAYS)
        if (AppleAcct.is_reauth_needed is False
                and reauth_in_days <= 10
                and reauth_msg is not None):
            alert_msg = (f"AppleAcct {reauth_msg}")
            update_alert_sensor(Source=AppleAcct, error='auth-warning',
                                alert_msg=f"{AppleAcct.apple_user} > {alert_msg}")

            if evlog_msg:
                post_event( f"{EVLOG_ALERT}Apple Acct > "
                            f"{AppleAcct.account_owner}, "
                            f"Reauth Warning, {reauth_msg}")

#--------------------------------------------------------------------
def reset_AppleAcct_Gb_variables():
    '''
    Delete all Apple account objects and clear all dictionaries
    so new AppleAcct objects will be set up again on a restart
    '''
    log_info_msg("Resetting Apple Acct objects and variables")

    Gb.AppleAcct             = None
    Gb.AppleAcctLoggingInto  = None

    for AppleAcct in Gb.AppleAcct_by_apple_id.values():
        del AppleAcct.iCloudSession
        del(AppleAcct)

    Gb.AppleAcct_by_apple_id          = {}
    Gb.AppleAcct_by_devicename        = {}
    Gb.AppleAcct_password_by_apple_id = {}
    Gb.AppleAcct_error_by_apple_id    = {}
    Gb.iCloudSession_by_apple_id      = {}
    Gb.Devices_by_apple_id            = {}
    Gb.famshr_device_ids_by_apple_id   = {}
    Gb.famshr_Devices_by_apple_id      = {}
    Gb.AppleAcct_reauth_needed = None

    Gb.AppleAcct_logging_in_apple_ids = []
    Gb.conf_apple_ids                 = set()

    config_file.decode_all_passwords()

#--------------------------------------------------------------------
def cleanup_unknown_AppleAcct_Gb_variables_apple_id():
    '''
    Verify the Apple acct 'by_apple_id' dicts contain only real Apple accts.
    If an invalid Apple acct was added and then corrected, the invalid one
    still exists in the 'by_apple_id' tables. Check and remove them.

    Invalid/Unknown accts are in Gb.upw_valid_by_apple_id
    '''
    conf_apple_ids = [conf_apple_acct[CONF_APPLE_ACCT] for conf_apple_acct in Gb.conf_apple_accounts]
    for apple_id in Gb.upw_valid_by_apple_id.copy().keys():
        if apple_id not in conf_apple_ids:
            delete_AppleAcct_Gb_variables_apple_id(apple_id)

#--------------------------------------------------------------------
def apple_acct_filename(apple_id, extn):
    '''
    The apple_id's session file name (.cookies, .session, .tpw). It is the same as the
    AppleAcct cookies_filename, session_filename & tokenpw_filename.
    '''
    cookie_filename_base = "".join([c for c in apple_id if match(r"\w", c)])
    return path.join(Gb.icloud_cookies_directory, f"{cookie_filename_base}{extn}")

def apple_acct_session_files_exist(apple_id):
    '''
    The session files are created when an Apple Acct is logged into and are not
    deleted when it is removed from the configuration. They show the apple_id was a
    valid Apple Acct that was set up in iCloud3.
    '''
    return (file_io.file_exists(apple_acct_filename(apple_id, '.tpw'))
                or file_io.file_exists(apple_acct_filename(apple_id, '.session')))

def apple_acct_saved_password(apple_id):
    '''
    The encoded password saved in the apple_id's .tpw file, '' if there is none
    '''
    try:
        token_pw_data = file_io.read_json_file(apple_acct_filename(apple_id, '.tpw'))
        if token_pw_data.get(CONF_APPLE_ACCT, apple_id) == apple_id:
            return token_pw_data.get(CONF_PASSWORD, '')

    except Exception as err:
        log_exception(err)

    return ''

#--------------------------------------------------------------------
def delete_AppleAcct_Gb_variables_apple_id(apple_id):
    '''
    Delete all Apple account objects and clear all dictionaries
    so new AppleAcct objects will be set up again on a restart
    '''
    log_info_msg("Resetting Apple Acct objects and variables")

    dict_del(Gb.upw_valid_by_apple_id, apple_id)
    dict_del(Gb.upw_code_by_apple_id, apple_id)
    dict_del(Gb.AppleAcct_by_devicename, apple_id)
    dict_del(Gb.AppleAcct_password_by_apple_id, apple_id)
    dict_del(Gb.AppleAcct_error_by_apple_id, apple_id)
    dict_del(Gb.iCloudSession_by_apple_id, apple_id)
    dict_del(Gb.Devices_by_apple_id, apple_id)
    dict_del(Gb.famshr_device_ids_by_apple_id, apple_id)
    dict_del(Gb.famshr_Devices_by_apple_id, apple_id)
    list_del(Gb.AppleAcct_logging_in_apple_ids, apple_id)
    list_del(Gb.conf_apple_ids, apple_id)

    AppleAcct = Gb.AppleAcct_by_apple_id.pop(apple_id, None)
    if AppleAcct:
        if  Gb.AppleAcct_reauth_needed == AppleAcct:
            Gb.AppleAcct_reauth_needed = None
        del AppleAcct.iCloudSession
        del AppleAcct

    config_file.decode_all_passwords()
