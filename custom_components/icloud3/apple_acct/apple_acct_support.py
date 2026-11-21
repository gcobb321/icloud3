
from ..global_variables import GlobalVariables as Gb
from ..const            import (HIGH_INTEGER,
                                    EVLOG_ALERT, EVLOG_NOTICE, EVLOG_ERROR,
                                    ALERT_CRITICAL, ALERT_APPLE_ACCT, ALERT_DEVICE, ALERT_STARTUP, ALERT_OTHER,
                                    ICLOUD,
                                    SETTINGS_INTEGRATIONS_MSG, INTEGRATIONS_IC3_CONFIG_MSG,
                                    INACTIVE,
                                    APPLE_ACCT_KEEPALIVE_SECS, APPLE_ACCT_LOGIN_RETRY_SECS,
                                    APPLE_ACCT_LOGIN_RETRY_5XX_SECS, APPLE_ACCT_LOGIN_RETRY_5XX_CODES,
                                    APPLE_ACCT_SRP_RETRY_MIN_GAP_SECS,
                                    APPLE_ACCT_LOGIN_NO_RETRY_CODES, CONFIGURE_IDLE_TIMEOUT_SECS,
                                    AUTH_CODE_NEEDED_FIRST_REMINDER_SECS,
                                    AUTH_CODE_NEEDED_REMINDER_SECS, )
from ..const_config     import (CONF_APPLE_ACCT, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_TRACKING_MODE, )
from ..const_char       import (NL, NL3, CRLF, CRLF_DOT, DASH_20, RED_X, CRLF_RED_MARK,
                                CRLF_RED_STOP, RED_ALERT, CRLF_RED_ALERT, CRLF_CHK, )


from .apple_acct        import (AppleAcctManager,
                                AppleAcctNoDevicesException, AppleAcctFailedLoginException,
                                AppleAcctAPIResponseException, AppleAcct2FARequiredException,)

# from ..startup          import start_ic3_control
from ..utils.messaging  import (post_event, post_alert, post_alert, post_error_msg,
                                post_greenbar_msg, update_alert_sensor, alert_key_for, log_banner,
                                post_repair_issue, clear_repair_issue,
                                log_debug_msg, log_info_msg, log_exception, log_error_msg, log_warning_msg,
                                internal_error_msg2, _evlog, _log, )
from ..utils.time_util  import (time_now_secs, secs_to_time, format_age, secs_to_hhmm,
                                format_time_age, secs_since, )
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
def keep_apple_accts_alive():
    '''
    Keep every Apple Acct's session token valid and retry a failed signin. Checked every
    5-mins in icloud3_main._main_5sec_loop_special_time_control.

    An Apple Acct is only refreshed when one of its devices needs a location. If that does
    not happen for a while (tracked devices paused or in a zone with a long inzone interval,
    default 2-hrs), the token expires (dead after 2-hrs idle on 11/13) and the next refresh needs a
    Password SRP signin, which Apple may refuse (-900007, 503).

    - Logged in: refresh it when it has not been refreshed for APPLE_ACCT_KEEPALIVE_SECS.
    - Signin failed: nothing else retries it (the 450 handler does not resend). Retry the
        refresh (refreshClient 450 -> authenticate) after APPLE_ACCT_LOGIN_RETRY_SECS
        (15-mins, 30-mins, then every hour) or, when Apple refused the signin (5xx),
        APPLE_ACCT_LOGIN_RETRY_5XX_SECS (1, 2, then every 4-hrs). Not within 30-mins of
        the last Password signin (_is_srp_retry_too_soon).
    Not done while waiting for an auth code or when the account is locked.
    '''
    if (Gb.use_data_source_ICLOUD is False
            or Gb.is_all_tracking_paused
            or Gb.internet_error):
        return

    # Configure may log into an Apple Acct (Update Apple Acct), a keep alive or retry signin
    # would run at the same time with the same cookie/session files. A login retry restart
    # would also reload iCloud3 under the open Configure window. Wait until it is closed.
    if is_config_flow_in_use():
        return

    for AppleAcct in list(Gb.AppleAcct_by_apple_id.values()):
        try:
            if AppleAcct is None:
                continue

            if AppleAcct.is_reauth_needed:
                remind_auth_code_needed(AppleAcct)
                continue

            AppleAcct.auth_code_reminder_cnt = 0

            if AppleAcct.account_locked:
                continue

            # The login failed during startup, the devices were never set up
            if AppleAcct.is_AADevices_setup_complete is False:
                _retry_startup_login(AppleAcct)
                continue

            if AppleAcct.login_successful:
                # It recovered (tracked device refresh reauth), start any later retries over
                if AppleAcct.login_retry_secs != 0:
                    AppleAcct.login_retry_secs = 0
                    AppleAcct.login_retry_cnt  = 0

                if secs_since(AppleAcct.last_refresh_secs) < APPLE_ACCT_KEEPALIVE_SECS:
                    continue

                # No tracked devices (all inactive or none assigned). It is logged into to get
                # its device list but is not kept alive, the token expires
                if AppleAcct.apple_id not in [Device.conf_apple_acct_apple_id
                                for Device in Gb.Devices_by_devicename_tracked.values()]:
                    continue
                log_info_msg(f"{AppleAcct.apple_user}, Keep Alive Refresh, Last Refresh-"
                                f"{format_age(AppleAcct.last_refresh_secs)}")

            # The retries were stopped (Configure > Update Apple Acct > Stop Retrying Login)
            elif AppleAcct.login_retry_secs < 0:
                continue

            # The signin failed, set the first retry time
            elif AppleAcct.login_retry_secs == 0:
                AppleAcct.login_retry_cnt  = 0
                AppleAcct.login_retry_secs = time_now_secs() +                                 _login_retry_delay_secs(0, _login_error_code(AppleAcct))
                post_event( f"Apple Acct > {AppleAcct.account_owner}, Login Failed, "
                            f"Will retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")
                continue

            elif time_now_secs() < AppleAcct.login_retry_secs:
                continue

            elif _is_srp_retry_too_soon(AppleAcct):
                continue

            else:
                AppleAcct.login_retry_cnt += 1
                log_info_msg(f"{AppleAcct.apple_user}, Login Retry #{AppleAcct.login_retry_cnt}")

            AppleAcct.refresh_icloud_data(locate_all_devices=True)
            _update_apple_acct_devices_loc_data(AppleAcct)

            if AppleAcct.login_successful:
                if AppleAcct.login_retry_secs > 0:
                    post_event( f"Apple Acct > {AppleAcct.account_owner}, Login Retry "
                                f"#{AppleAcct.login_retry_cnt} Successful")
                AppleAcct.login_retry_secs = 0
                AppleAcct.login_retry_cnt  = 0

            elif AppleAcct.login_retry_secs > 0:
                AppleAcct.login_retry_secs = time_now_secs() +                                 _login_retry_delay_secs(AppleAcct.login_retry_cnt,
                                                        _login_error_code(AppleAcct))
                post_event( f"Apple Acct > {AppleAcct.account_owner}, Login Retry "
                            f"#{AppleAcct.login_retry_cnt} Failed, "
                            f"Will retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")

        except Exception as err:
            log_exception(err)

#....................................................................
def _update_apple_acct_devices_loc_data(AppleAcct):
    '''
    The keep alive refresh only updates the AADev data. Move it into the Devices' loc_data
    fields (a tracked device's refresh does this for all Devices) so the moved in zone
    (tracked) and the moved 50m (monitored) checks see the new location.
    '''
    # Imported here, icloud_data_handler imports this module
    from .icloud_data_handler import update_device_with_latest_raw_data

    for Device in Gb.Devices:
        try:
            if Device.AppleAcct is AppleAcct:
                update_device_with_latest_raw_data(Device)

        except Exception as err:
            log_exception(err)

#....................................................................
def is_config_flow_in_use():
    '''
    Configure is open and a screen was displayed within CONFIGURE_IDLE_TIMEOUT_SECS.
    A browser tab closed without exiting leaves Gb.is_config_flow_open set, the timeout
    keeps it from holding up the Apple Acct keep alive forever.
    '''
    OptFlow = Gb.OptionsFlowHandler
    if Gb.is_config_flow_open is False or OptFlow is None:
        return False

    last_activity_secs = getattr(OptFlow, 'last_activity_secs', 0) or 0
    return (time_now_secs() - last_activity_secs) < CONFIGURE_IDLE_TIMEOUT_SECS

#....................................................................
def _retry_startup_login(AppleAcct):
    '''
    The Apple Acct login failed during startup (AppleAcct exists, devices not set up).
    Retry the login on the APPLE_ACCT_LOGIN_RETRY_SECS backoff (5xx uses the 1, 2, 4-hr
    APPLE_ACCT_LOGIN_RETRY_5XX_SECS one, not within 30-mins of the last Password signin).
    When it works, restart iCloud3. The restart reuses the logged in AppleAcct (Method-1,
    no new signin) and sets up and verifies its devices (start_ic3 Stage 4).

    Not retried:
        - APPLE_ACCT_LOGIN_NO_RETRY_CODES (403 locked/unknown acct, 423), the user has to fix it
        - 401 invalid password, retried once (401 -20101 was seen with a correct password)
        - Terms of Use not accepted
    login_retry_secs = -1 when the retries were stopped
    '''
    if AppleAcct.login_retry_secs < 0:
        return

    code = _login_error_code(AppleAcct)

    if AppleAcct.login_retry_secs == 0:
        if (code in APPLE_ACCT_LOGIN_NO_RETRY_CODES
                or AppleAcct.terms_of_use_update_needed):
            AppleAcct.login_retry_secs = -1
            return

        AppleAcct.login_retry_cnt  = 0
        AppleAcct.login_retry_secs = time_now_secs() + _login_retry_delay_secs(0, code)
        post_event( f"Apple Acct > {AppleAcct.account_owner}, Startup Login Failed ({code}), "
                    f"Will retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")
        _add_login_retry_note(AppleAcct,
                    f"Login Retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")
        return

    if time_now_secs() < AppleAcct.login_retry_secs:
        return

    if _is_srp_retry_too_soon(AppleAcct):
        return

    AppleAcct.login_retry_cnt += 1
    log_info_msg(f"{AppleAcct.apple_user}, Startup Login Retry #{AppleAcct.login_retry_cnt}")

    AppleAcct.authenticate_and_refresh_data()

    if AppleAcct.login_successful and AppleAcct.is_AADevices_setup_complete:
        post_event( f"Apple Acct > {AppleAcct.account_owner}, Login Retry "
                    f"#{AppleAcct.login_retry_cnt} Successful, Restarting iCloud3")
        AppleAcct.login_retry_secs = 0
        AppleAcct.login_retry_cnt  = 0
        Gb.was_icloud3_restart_requested = True
        return

    code = _login_error_code(AppleAcct)
    if (code in APPLE_ACCT_LOGIN_NO_RETRY_CODES
            or code == 401
            or AppleAcct.terms_of_use_update_needed
            or AppleAcct.account_locked):
        AppleAcct.login_retry_secs = -1
        post_event( f"{EVLOG_ALERT}Apple Acct > {AppleAcct.account_owner}, Login Retry "
                    f"#{AppleAcct.login_retry_cnt} Failed ({code}), Not retried again, "
                    f"Check the Apple Account, then restart iCloud3")
        _add_login_retry_note(AppleAcct,
                    f"Login Retry #{AppleAcct.login_retry_cnt} Failed, Not retried again, "
                    f"Check the Apple Account, then restart iCloud3", code=code)
        return

    AppleAcct.login_retry_secs = time_now_secs() + \
                    _login_retry_delay_secs(AppleAcct.login_retry_cnt, code)
    post_event( f"Apple Acct > {AppleAcct.account_owner}, Login Retry "
                f"#{AppleAcct.login_retry_cnt} Failed ({code}), "
                f"Will retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")
    _add_login_retry_note(AppleAcct,
                f"Login Retry #{AppleAcct.login_retry_cnt + 1} "
                f"at {secs_to_hhmm(AppleAcct.login_retry_secs)}", code=code)

    # The 503 was not recovered by the retry
    if code == 503:
        post_ha_icloud_integration_503_warning(AppleAcct)

#....................................................................
LOGIN_RETRY_NOTE_SEP = ', Login Retry'

def _add_login_retry_note(AppleAcct, retry_note, code=None):
    '''
    Add the startup login retry note to the Apple Acct's login_failed alert (alerts
    sensor and Event Log greenbar), 'gco**1**21@ > Login Failed, <reason>, Login Retry
    at 12:25p'. A failed retry rewrites the alert (apple_acct.authenticate_and_refresh_data),
    a note already there is replaced. A successful retry restarts iCloud3, which
    clears it.

    retry_note - Starts with 'Login Retry' (LOGIN_RETRY_NOTE_SEP)
    code - The failed retry's error code. The reason is rebuilt from it, the alert
        kept the startup login's reason (Reauth (500) after a retry failed with a 421)
    '''
    if code:
        alert_msg = f"{AppleAcct.apple_user} > Login Failed, {AppleAcct.code_description(code)}"
    else:
        alert_key = alert_key_for(AppleAcct.apple_id, 'login_failed')
        alert_msg = AppleAcct.alerts_by_alert_key.get(alert_key,
                                    f"{AppleAcct.apple_user} > Login Failed")
        alert_msg = alert_msg.split(LOGIN_RETRY_NOTE_SEP)[0]

    update_alert_sensor(Source=AppleAcct, error='login_failed',
                        alert_msg=f"{alert_msg}, {retry_note}")

#....................................................................
def _login_error_code(AppleAcct):
    '''
    The code that ended the failed login. response_code_pw is the Password SRP signin code
    (set by _set_srp_return_error_code), response_code the last request's code
    '''
    return AppleAcct.response_code_pw or AppleAcct.response_code

def _login_retry_delay_secs(retry_cnt, code):
    '''
    Apple refusing the signin (500, 502, 503, 504) is throttling it, retrying on the
    normal 15/30/60-min schedule keeps the throttle going. Use the 1, 2, 4-hr one.
    '''
    retry_secs = (APPLE_ACCT_LOGIN_RETRY_5XX_SECS
                        if code in APPLE_ACCT_LOGIN_RETRY_5XX_CODES
                        else APPLE_ACCT_LOGIN_RETRY_SECS)
    idx = min(retry_cnt, len(retry_secs) - 1)

    return retry_secs[idx]

def _is_srp_retry_too_soon(AppleAcct):
    '''
    A login retry ends in a Password signin when the token login fails. Do not send one
    within APPLE_ACCT_SRP_RETRY_MIN_GAP_SECS of the last Password signin (startup,
    Configure, Auth Code request or another retry). Move the retry time instead.

    Return:
        True  - Too soon, login_retry_secs was moved
    '''
    last_secs = AppleAcct.last_password_auth_secs
    if last_secs == 0 or secs_since(last_secs) >= APPLE_ACCT_SRP_RETRY_MIN_GAP_SECS:
        return False

    AppleAcct.login_retry_secs = last_secs + APPLE_ACCT_SRP_RETRY_MIN_GAP_SECS
    log_info_msg(   f"{AppleAcct.apple_user}, Login Retry Delayed, Last Password Signin-"
                    f"{format_age(last_secs)}, Retry at {secs_to_hhmm(AppleAcct.login_retry_secs)}")
    return True

#--------------------------------------------------------------------
HA_ICLOUD_INTEGRATION_DOMAIN = 'icloud'
HA_ICLOUD_INTEGRATION_503_MSG = (
                f"The Home Assistant Apple iCloud integration is also signing into this "
                f"Apple Account. Two integrations signing into the same account can "
                f"contribute to Apple refusing signins (503) and to locked accounts. "
                f"Consider disabling it")

def is_ha_icloud_integration_using_apple_id(apple_id):
    '''
    The HA Apple iCloud integration (domain 'icloud') does its own Password SRP
    signins. Check if an enabled config entry of it uses this apple_id. Its
    entry.data['username'] is the apple_id (also its unique_id).

    Only shown when a 503 was not recovered from. A different apple_id does not
    share Apple's signin throttling, so it is not checked.
    '''
    try:
        if Gb.hass is None or not apple_id:
            return False

        apple_id = apple_id.strip().lower()
        for entry in Gb.hass.config_entries.async_entries(HA_ICLOUD_INTEGRATION_DOMAIN):
            if entry.disabled_by is not None:
                continue
            username = (entry.data.get('username') or entry.unique_id or '')
            if username.strip().lower() == apple_id:
                return True

    except Exception as err:
        log_exception(err)

    return False

def post_ha_icloud_integration_503_warning(AppleAcct):
    '''
    Post the HA Apple iCloud integration warning once per AppleAcct when its 503 was
    not recovered from
    '''
    if (getattr(AppleAcct, 'ha_icloud_503_warning_posted', False)
            or is_ha_icloud_integration_using_apple_id(AppleAcct.apple_id) is False):
        return

    AppleAcct.ha_icloud_503_warning_posted = True
    post_event( f"{EVLOG_ALERT}Apple Acct > {AppleAcct.account_owner}, "
                f"Apple Refused the Signin (503){CRLF_DOT}{HA_ICLOUD_INTEGRATION_503_MSG}")

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

        # Start the login retries over (keep_apple_accts_alive), they may have been
        # stopped (-1) before this restart
        if AppleAcct:
            AppleAcct.login_retry_secs = 0
            AppleAcct.login_retry_cnt  = 0

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
    refreshed = AppleAcct.refresh_icloud_data(locate_all_devices=True)

    # The device data was received, so the session works. Clear a login_successful=False
    # left by an earlier failed signin (a reauth Request Auth Code that Apple refused)
    # or the reused AppleAcct is never matched to the Devices (start_ic3 only runs
    # setup_tracked_devices_for_icloud when login_successful is True) and its
    # iCloud-only devices are not verified on every iCloud3 restart.
    if (refreshed
            and AppleAcct.response_code == 200
            and isnot_empty(AppleAcct.AADev_by_device_id)):
        AppleAcct.login_successful = True

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


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   APPLE ACCT AUTHENTICATION NEEDED FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def is_authentication_2fa_code_needed(AppleAcct, initial_setup=False):
    '''
    A wrapper for seeing if an authentication is needed and setting up the config_flow
    reauth request

    Return:
        True  - An Auth Code is needed (AppleAcct.is_reauth_needed)
        False - It is not needed. It returned None here before 11/15/2026, the
                start_ic3 'is False' AppleAcct reuse check was never True
    '''
    if AppleAcct is None:
        return False
    elif AppleAcct.is_reauth_needed:
        pass
    # elif Gb.conf_data_source_MOBAPP is False:
    #     return False
    elif initial_setup:
        pass
    elif Gb.is_icloud3_startup_inprocess:
        return False

    alert_msg = ''
    if (new_2fa_authentication_code_requested(AppleAcct, initial_setup)
            and AppleAcct.was_ha_display_orange_reauth_button_sent is False):

        alert_msg =(f"{AppleAcct.apple_user_short} > "
                    f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_reauth_needed_secs)})")
        post_alert(alert_msg)
        update_alert_sensor(Source=AppleAcct, error='auth_needed', alert_msg=alert_msg)

        # There is one HA Reconfigure button for all Apple Accts (one config entry).
        # Request it unless another Apple Acct that still needs a code already has.
        # The reauth screen moves on to the next Apple Acct needing a code.
        if (Gb.AppleAcct_reauth_needed is None
                or Gb.AppleAcct_reauth_needed is AppleAcct
                or Gb.AppleAcct_reauth_needed.is_reauth_needed is False):
            try:
                Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

                post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.apple_user_short}, "
                            f"Auth Reconfigure button requested")
            except Exception as err:
                log_exception(err)

            Gb.AppleAcct_reauth_needed = AppleAcct

        AppleAcct.was_ha_display_orange_reauth_button_sent = True



    # Post the Repairs issue when Apple starts asking for the Terms of Use, remove it
    # when they were accepted somewhere else (www.icloud.com). The issue posted
    # during startup is handled by start_ic3._check_apple_acct_status_issues
    if AppleAcct.terms_of_use_update_needed:
        if AppleAcct.terms_of_use_repair_issue_posted is False:
            post_repair_issue_aa_terms_of_use(AppleAcct)

    elif AppleAcct.terms_of_use_repair_issue_posted:
        clear_repair_issue_aa_terms_of_use(AppleAcct)

    # The code may no longer be needed without one being entered (a token refresh
    # re-derived it from dsInfo, or a full login reset it). Clear the flag so the
    # alert and orange button are posted the next time a code is needed.
    if AppleAcct.is_reauth_needed is False:
        AppleAcct.was_ha_display_orange_reauth_button_sent = False

    return AppleAcct.is_reauth_needed

#--------------------------------------------------------------------
def remind_auth_code_needed(AppleAcct):
    '''
    An Auth Code is needed and has not been entered. The Event Log alert and the HA
    Reconfigure button are only posted when it is first needed, so a user who does not
    look at them never knows. Post an HA log error and an Event Log alert after
    AUTH_CODE_NEEDED_FIRST_REMINDER_SECS (12-hrs), then every
    AUTH_CODE_NEEDED_REMINDER_SECS (24-hrs). The count is reset when the code is
    entered (keep_apple_accts_alive).

    To test: request an Auth Code and do not enter it, shorten the const.py
    AUTH_CODE_NEEDED_* timers (e.g. 1800/3600) and restart HA.
    '''
    needed_secs   = AppleAcct.is_reauth_needed_secs
    first_secs    = AUTH_CODE_NEEDED_FIRST_REMINDER_SECS
    interval_secs = AUTH_CODE_NEEDED_REMINDER_SECS

    if needed_secs == 0:
        return

    reminder_cnt  = getattr(AppleAcct, 'auth_code_reminder_cnt', 0)
    reminder_secs = needed_secs + first_secs + reminder_cnt * interval_secs
    if time_now_secs() < reminder_secs:
        return

    # A restart can be days later, post one reminder, not one for each 24-hrs missed
    AppleAcct.auth_code_reminder_cnt = \
                    int((secs_since(needed_secs) - first_secs) // interval_secs) + 1

    log_error_msg(  f"{AppleAcct.apple_user_short} > Apple Acct Auth Code needed "
                    f"since {format_time_age(needed_secs, hhmm=True)} and has not been entered. "
                    f"iCloud location data may stop and Apple may refuse its signins. "
                    f"Select `Settings > Devices & Services`, then select `Reconfigure` "
                    f"to enter the code")
    post_alert( f"Apple Acct > {AppleAcct.apple_user_short}, Auth Code needed "
                f"since {format_time_age(needed_secs, hhmm=True)}"
                f"{CRLF_DOT}Select `Settings > Devices & Services`, then select `Reconfigure` "
                f"to enter the code")

    # The 12-hr reminder goes to the first owner device, the later ones to all of them
    _send_auth_code_needed_mobapp_msg(AppleAcct, needed_secs,
                        first_device_only=(AppleAcct.auth_code_reminder_cnt == 1))

    # Show HA's Reconfigure button again. HA does not start a 2nd reauth flow if one is
    # already in progress. Not done while Configure is open, the reauth screen would be
    # displayed on top of it (apple_acct_support_cf).
    if Gb.config_entry and Gb.is_config_flow_open is False:
        Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

#--------------------------------------------------------------------
def _send_auth_code_needed_mobapp_msg(AppleAcct, needed_secs, first_device_only=False):
    '''
    Send the Auth Code needed reminder to the Mobile App of the Apple Acct owner's
    Devices (not a Family Sharing member's device, Device.family_share_device is False).
    A notify service shared by several Devices gets one message.

    first_device_only:
        True  - Send it to the first owner Device with a Mobile App (12-hr reminder)
        False - Send it to all of them (the 24-hr reminders)
    '''
    # Imported here, mobapp_interface imports modules that import this one
    from ..mobile_app import mobapp_interface
    from ..const      import NOTIFY

    pending_hrs  = max(1, int(secs_since(needed_secs) // 3600))
    service_data = {
        "title":   f"{AppleAcct.apple_user} > Apple Acct Auth Needed",
        "message": (f"The Apple Account auth code has been pending "
                    f"since {format_time_age(needed_secs, hhmm=True)}. The auth code needs to be "
                    f"entered to continue tracking with iCloud location data. "
                    f"Select `Settings > Devices & Services`, then select `Reconfigure` "
                    f"to enter the code")}
    notify_services_sent = []
    for Device in Gb.Devices_by_apple_id.get(AppleAcct.apple_id, []):
        try:
            # Only the account owner's devices, not the Family Sharing members' devices
            if getattr(Device, 'family_share_device', True) is not False:
                continue

            notify_service = Device.mobapp.get(NOTIFY, '')
            if notify_service == '' or notify_service in notify_services_sent:
                continue

            if mobapp_interface.send_message_to_device(Device, service_data):
                notify_services_sent.append(notify_service)

                if first_device_only:
                    break

        except Exception as err:
            log_exception(err)

    if notify_services_sent == []:
        log_info_msg(f"{AppleAcct.apple_user}, Auth Code Needed Reminder, Mobile App message "
                        f"not sent, No account owner device with a Mobile App notify service")

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
    start_ic3.repair_issue_fix_aa_terms_of_use. The Event Log alert and the
    sensor.icloud3_alerts entry (Event Log greenbar) are posted with it,
    post_repair_issue does not update the alerts sensor.
    '''
    alert_msg = ("Accept Apple `Terms of Use` needed "
                    "(HA Repairs or Authenticate Apple Account Sign-in)")
    post_alert(f"{AppleAcct.apple_user} > {alert_msg}")
    log_warning_msg(f"{AppleAcct.apple_user} > {alert_msg}")
    update_alert_sensor(Source=AppleAcct, error=REPAIR_ISSUE_TERMS_OF_USE,
                        alert_msg=f"{AppleAcct.apple_user} > Accept Apple Terms of Use needed")

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
    update_alert_sensor(Source=AppleAcct, error=REPAIR_ISSUE_TERMS_OF_USE, clear=True)

    AppleAcct.terms_of_use_repair_issue_posted = False

#--------------------------------------------------------------------
# UNUSED (10/31/2026) - not called anywhere. Commented out, delete after v3.8.0
# def check_all_devices_online_status():
#     '''
#     See if all the devices are 'pending'. If so, the devices are probably in airplane mode.
#     Set the time and display a message
#     '''
#     any_device_online_flag = False
#     for Device in Gb.Devices_by_devicename_tracked.values():
#         if Device.is_online:
#             Device.offline_secs = 0
#             Device.pending_secs = 0
#             any_device_online_flag = True

#         elif Device.is_offline:
#             if Device.offline_secs == 0:
#                 Device.offline_secs = Gb.this_update_secs
#             post_event(Device,
#                         f"Device Offline and not available > "
#                         f"OfflineSince-{format_time_age(Device.offline_secs)}")

#         elif Device.is_pending:
#             if Device.pending_secs == 0:
#                 Device.pending_secs = Gb.this_update_secs
#             post_event(Device,
#                         f"Device status is Pending/Unknown > "
#                         f"PendingSince-{format_time_age(Device.pending_secs)}")

#     if any_device_online_flag == False:
#         post_event( f"All Devices are offline or have a pending status. "
#                     f"They may be in AirPlane Mode and not available")

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
def relink_AppleAcct_conf_apple_acct():
    '''
    On an iCloud3 restart (Gb.was_icloud3_reloaded) the configuration file is read
    again, Gb.conf_apple_accounts has new conf_apple_acct items, and the AppleAcct
    objects are reused. Point them to the new items. A change to the old item (auth
    method, trusted devices) would not be saved in the configuration file.
    '''
    for apple_id, AppleAcct in Gb.AppleAcct_by_apple_id.items():
        conf_apple_acct, aa_idx = config_file.conf_apple_acct(apple_id)
        if aa_idx >= 0:
            AppleAcct.conf_apple_acct = conf_apple_acct
            AppleAcct.aa_idx          = aa_idx

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
        list_del(Gb.AppleAccts, AppleAcct)

        for devicename, _AppleAcct in list(Gb.AppleAcct_by_devicename.items()):
            if _AppleAcct is AppleAcct:
                Gb.AppleAcct_by_devicename.pop(devicename)

        if  Gb.AppleAcct_reauth_needed == AppleAcct:
            Gb.AppleAcct_reauth_needed = None
        del AppleAcct.iCloudSession
        del AppleAcct

    config_file.decode_all_passwords()
