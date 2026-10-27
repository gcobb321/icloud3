

from ..global_variables import GlobalVariables as Gb
from ..const            import (DOMAIN, DEVICE_TRACKER,
                                EVLOG_NOTICE, EVLOG_ERROR, EVLOG_ALERT,
                                ICLOUD,
                                IPHONE_DN, WATCH_DN, IPAD_DN, MAC_DN, DEVICE_TYPES, DEVICE_TYPE_TRACKING_MODE,
                                DEVICE_TYPE_PICTURE_FILENAMES, DEVICE_TYPE_ICONS,
                                TRACK, MONITOR, INACTIVE, TRACKING_MODES, )
from ..const_config     import (CONF_DATA_SOURCE, CONF_APPLE_ACCT, CONF_APPLE_ACCT, CONF_PASSWORD,
                                CONF_LOCATE_ALL, CONF_SERVER_LOCATION, CONF_IC3_DEVICENAME,
                                CONF_FNAME, CONF_DEVICE_TYPE, CONF_AADEV_NAME,
                                CONF_AADEV_DEVICE_ID, CONF_RAW_MODEL, CONF_MODEL,
                                CONF_MODEL_DISPLAY_NAME, CONF_TRACKING_MODE,
                                CONF_MOBILE_APP_DEVICE, CONF_PICTURE, CONF_ICON, )
from ..const_char       import (CRLF_DOT, )

from ..utils.utils      import (instr, isnot_empty,
                                list_add, list_del, dict_del, dict_sort,
                                encode_password, decode_password, apple_user,
                                is_running_in_event_loop, )
from ..utils.messaging  import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                update_alert_sensor,
                                _log, log_exception, log_debug_msg, log_info_msg,
                                add_log_file_filter, )
from ..utils.time_util  import (time_now_secs, secs_to_hhmm, )


from ..apple_acct.apple_acct import (AppleAcctManager, AppleAcctFailedLoginException, HTTP_RESPONSE_CODES)
from .device_name_parser     import make_ic3_fname_from_aadevice_dname
from .                       import apple_acct_support as aas
from ..startup          import start_ic3
from ..utils            import file_io
from ..utils            import entity_io

#--------------------------------------------------------------------
from homeassistant.util import slugify
from re                 import match
from os                 import path

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#          APPLE ACCOUNT ICLOUD SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_log_into_apple_account(self, user_input):
    '''
    Log into the icloud account and check to see if a Authentication code is needed.
    If so, the calling step displays the Authentication form and gets the code from the user.

    Input:
        user_input  = A dictionary with the apple_id and password, or
                        {apple_id: icloudAccountUsername, password: icloudAccountPassword}
                    = {} to use the apple_id/password in the tracking configuration parameters

    Exception:
        The self.AppleAcct.requres_2fa must be checked after a login to see if the account
        access needs to be verified. If so, the Authentication code entry form must be displayed.

    Returns:
        self.Pyicloud object
        self.iCloud_AppleAcctDevices object
        self.AppleAcct_FindMyFriends object
        self.opt_icloud_dname_list & self.device_form_icloud_famf_list =
                A dictionary with the devicename and identifiers
                used in the tracking configuration devices icloud_device parameter
    '''
    try:
        self.errors = {}
        self.login_successful     = False
        self.login_successful_srp = None
        self.auth_failed_503      = False

        # The apple_id may be changed to assign a new account, if so, log into the new one
        if CONF_APPLE_ACCT not in user_input or CONF_PASSWORD not in user_input:
            return False

        apple_id = user_input[CONF_APPLE_ACCT].lower()
        password = user_input[CONF_PASSWORD]

        add_log_file_filter(apple_id, f"**{self.aa_idx}**")
        add_log_file_filter(apple_id.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(password)

        apple_server_location = user_input.get(CONF_SERVER_LOCATION,'usa')

        log_user_input = {**user_input, CONF_PASSWORD: '********'}
        log_info_msg(   f"Apple Acct > {apple_id}, Logging in, "
                        f"UserInput-{log_user_input}, Errors-{self.errors}, "
                        f"Step-{self.step_id}")

        # Already logged in and no changes
        AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
        if (AppleAcct
                and password == AppleAcct.password
                and AppleAcct.login_successful
                and AppleAcct.login_successful_srp != False
                and AppleAcct.auth_failed_503 is False
                and apple_server_location == AppleAcct.apple_server_location
                and AppleAcct.login_successful):
            self.AppleAcct = AppleAcct
            self.apple_id = apple_id
            self.password = password
            # self.header_msg = 'apple_acct_logged_into'

            log_info_msg(f"Apple Acct > {apple_id}, Already Logged in, {self.AppleAcct}")
            # return True

            # Validate the account before actually logging in
            upw_valid = await Gb.ValidateAppleAcctUPW.async_validate_apple_id_password(apple_id, password)
            if upw_valid is False:
                Gb.upw_valid_by_apple_id.pop(apple_id, None)
                Gb.upw_code_by_apple_id.pop(apple_id, None)
                self.errors[CONF_APPLE_ACCT] = 'apple_acct_inupw_valid'
                log_info_msg(f"Apple Acct > {apple_id}, Invalid Username/password")
                return False


        event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into Apple Account {apple_id}")
        if apple_server_location != 'usa':
            event_msg += f", iCloud.com ServerSuffix-{apple_server_location}"
        log_info_msg(event_msg)

    except Exception as err:
        log_exception(err)

    try:
        await file_io.async_make_directory(Gb.icloud_cookies_directory)

        AppleAcct = None
        AppleAcct = await Gb.hass.async_add_executor_job(
                                    create_AppleAcctManager_config_flow,
                                    apple_id,
                                    password,
                                    apple_server_location)

        # TEST CODE -Test Internet error and AppleAcct login failure
        # _log("TEST CODE ENABLED")
        # AppleAcct = None
        # Gb.internet_error = True

        if AppleAcct is None:
            self.AppleAcct = None
            log_info_msg(f"Apple Acct > {apple_id}, Login Failed")
            return False

        # Successful login, set AppleAcct fields
        self.AppleAcct = AppleAcct
        self.apple_id = apple_id
        self.password = password
        self.apple_server_location = apple_server_location
        Gb.upw_valid_by_apple_id[apple_id] = True
        log_info_msg(f"Apple Acct > {apple_id}, Login successful, {self.AppleAcct}")

        start_ic3.dump_startup_lists_to_log()

        if AppleAcct.is_reauth_needed:
            log_info_msg(f"Apple Acct > {apple_id}, 2fa Authentication Needed, {self.AppleAcct}")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_reauth_needed_secs)})"
            update_alert_sensor(Source=AppleAcct, error='auth_needed', alert_msg=alert_msg)

            # Display the orange 'Reconfigure' button on the HA Settings screen as
            # soon as the login reports that an Auth Code is needed. Waiting until
            # the code is actually requested (step_reauth) leaves HA showing no
            # indication that the account is not usable yet.
            #
            # Do not do this while the iCloud3 Configure (OptionsFlow) dialog is open.
            # `async_start_reauth` does not just light up the orange button, it starts a
            # real HA reauth ConfigFlow, which immediately runs the ConfigFlow's
            # async_step_reauth and displays a 2nd reauth screen on top of the OptionsFlow
            # reauth screen that step_apple_acct is about to display. The orange button is
            # set by start_ic3_control when iCloud3 restarts as the Configure dialog is
            # exited if the acct still needs to be authenticated.
            if Gb.config_entry and Gb.is_config_flow_open is False:
                Gb.hass.add_job(Gb.config_entry.async_start_reauth, Gb.hass)

            return True

        self.header_msg = 'apple_acct_logged_into'

        return True

    # Login Failed, display error messages
    except (AppleAcctFailedLoginException) as err:
        err = str(err)
        Gb.HALogger.error(f"Error logging into Apple Acct: {err}")

        response_code = Gb.AppleAcctLoggingInto.response_code
        if Gb.AppleAcctLoggingInto.response_code_pw == 503:
            Gb.AppleAcctLoggingInto.setup_error(503)

        elif response_code == 302:
            Gb.AppleAcctLoggingInto.setup_error(302, 'Server Location')
            apple_server_location = Gb.AppleAcctLoggingInto.apple_server_location
            if (apple_server_location == 'usa'):
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-cn')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_cn'
            elif (apple_server_location == '.cn'):
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-usa')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_usa'
            else:
                Gb.AppleAcctLoggingInto.setup_error(302, 'Server Loc-??')
                self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302'

        elif response_code == 400:
            self.errors['base'] = 'apple_acct_inupw_valid'
        elif response_code == 401 and instr(err, 'Python SRP'):
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors['base'] = 'apple_acct_login_error_srp_401'
        elif response_code == 401:
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors[CONF_APPLE_ACCT] = 'apple_acct_inupw_valid'
        elif response_code == 403:
            Gb.AppleAcctLoggingInto.setup_error(403)
            self.errors[CONF_APPLE_ACCT] = 'apple_acct_locked'
        else:
            Gb.AppleAcctLoggingInto.setup_error(response_code)
            self.errors['base'] = 'apple_acct_login_error_other'
        error_msg = HTTP_RESPONSE_CODES.get(response_code, 'Other Error')

        post_error_msg( f"Apple Acct > {apple_id}, Login Failed, "
                        f"Error-{err}/{error_msg}, Code-{response_code}")

    except Exception as err:
        log_exception(err)
        Gb.HALogger.error(f"Error logging into Apple Account: {err}")
        self.errors['base'] = 'apple_acct_login_error_other'

    start_ic3.dump_startup_lists_to_log()
    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CREATE APPLE ACCOUNT SERVICE OBJECTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_AppleAcctManager_config_flow(apple_id, password, apple_server_location):
    '''
    Create the AppleAcctManager object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    AppleAcct session
    '''
    try:
        AppleAcct = None
        AppleAcct = AppleAcctManager( apple_id,
                                    password,
                                    apple_server_location=apple_server_location,
                                    cookie_directory=Gb.icloud_cookies_directory,
                                    session_directory=Gb.icloud_session_directory,
                                    config_flow_login=True)

    except Exception as err:
        AppleAcct = None
        pass

    # TEST CODE -Test Internet error and AppleAcct login failure
    # _log("TEST CODE ENABLED")
    # AppleAcct = None
    # Gb.internet_error = True

    if AppleAcct and AppleAcct.login_successful:
        log_debug_msg(  f"Apple Acct > {AppleAcct.account_owner}, Login Successful, "
                        f"Error-{AppleAcct.response_code_desc}, "
                        f"Update Configuration")
    else:
        # raise AppleAcctFailedLoginException
        return None

    # start_ic3.dump_startup_lists_to_log()
    return AppleAcct

#--------------------------------------------------------------------
@staticmethod
def create_AADevices_config_flow(AppleAcct):

    _AADevices = AppleAcct.create_AADevices_object(config_flow_login=True)

    start_ic3.dump_startup_lists_to_log()
    return _AADevices


#..............................................................................................
def clear_AppleAcct_auth_alerts():
    for apple_id, AppleAcct in Gb.AppleAcct_by_apple_id.items():
        if AppleAcct.is_reauth_needed:
            AppleAcct.was_ha_auth_code_alert_sent = False

#--------------------------------------------------------------------
async def async_finish_authentication_and_data_refresh(caller_self):
    '''
    Refresh the device list if the apple acct is being setup for the first time
    If AppleAcct.device_id_by_aadev_dname is empty, a Authentication code was needed
    when first logged in and the apple acct data was not authenticated and it's
    device data was never loaded/initialized by refreshed_icloud_data. This
    prevents the device's list tables to never be initialized and location data
    is not available. Do this now.
    '''
    AppleAcct = caller_self.AppleAcct

    # The accountLogin request accepts the Terms of Use (_handle_accept_terms_of_use).
    # refresh_session=True skips the session token validation, authenticate() returns
    # before accountLogin is done when the token is still valid.
    accepting_terms_of_use = (AppleAcct.terms_of_use_update_needed
                                and AppleAcct.terms_of_use_accepted)
    AppleAcct.login_successful = \
        await Gb.hass.async_add_executor_job(AppleAcct.authenticate, accepting_terms_of_use)

    if AppleAcct.login_successful is False:
        err_msg = ( f"Apple Acct > {AppleAcct.apple_user}, Authentication Failed, "
                    f"Error-{AppleAcct.response_code_desc}, "
                    f"AppleServerLocation-`{AppleAcct.apple_server_location}`, "
                    "Location Data not Refreshed")
        post_error_msg(err_msg)
        return

    locate_all_devices = True

    # refresh_icloud_data is treated as a startup refresh so all of the devices are
    # initialized, not just the tracked ones. Save and restore the flag instead of
    # clearing it - iCloud3 may really be starting up, and a failure in the executor job
    # would leave the flag set and stop the 5-sec polling loop.
    was_startup_inprocess = Gb.is_icloud3_startup_inprocess
    Gb.is_icloud3_startup_inprocess = True

    try:
        await Gb.hass.async_add_executor_job(
                                AppleAcct.refresh_icloud_data,
                                locate_all_devices)

        if AppleAcct.is_authenticated:
            # terms_of_use_update_needed is set from Apple's accountLogin response
            if accepting_terms_of_use and AppleAcct.terms_of_use_update_needed:
                post_error_msg( f"{EVLOG_ALERT}Apple Acct > {AppleAcct.apple_user}, "
                                f"Apple did not accept the Terms of Use")

            elif accepting_terms_of_use:
                post_event( f"{AppleAcct.apple_user} > "
                            f"Apple Acct > Terms of Service agreement approved")
                aas.clear_repair_issue_aa_terms_of_use(AppleAcct)

            if AppleAcct.terms_of_use_update_needed is False:
                update_alert_sensor(Source=AppleAcct, clear=True)

    finally:
        Gb.is_icloud3_startup_inprocess = was_startup_inprocess

#--------------------------------------------------------------------
def any_conf_devices_for_apple_acct(ui_apple_id):
    existing_devices = [conf_device[CONF_IC3_DEVICENAME]
                                    for conf_device in Gb.conf_devices
                                    if conf_device[CONF_APPLE_ACCT] == ui_apple_id]

    return isnot_empty(existing_devices)

#--------------------------------------------------------------------
def any_apple_accts_not_used():
    aa_list = list(Gb.AppleAcct_by_apple_id.keys())
    aa_used = [conf_device[CONF_APPLE_ACCT]
                            for conf_device in Gb.conf_devices]
    aa_unused = [apple_id   for apple_id in aa_list
                            if apple_id not in aa_used]

    return isnot_empty(aa_unused)

#--------------------------------------------------------------------
# def delete_AppleAcct_trust_cookie(AppleAcct):
#     AppleAcct.iCloudSession.cookies.delete('X-APPLE-WEBAUTH-HSA-TRUST')
#     AppleAcct.iCloudSession.cookies.save()

#--------------------------------------------------------------------
async def async_delete_icloud_session_file(AppleAcct, apple_id):
    '''
    Delete the cookies and session files as part of the reset_session
    and request_auth_code. This is called from config_flow/step_reauth
    and pyicloud_reset_session
    '''
    if AppleAcct:
        cookies_filename = AppleAcct.cookies_filename
        session_filename = AppleAcct.session_filename
        AppleAcct.delete_cookie_and_session_files()

        apple_id_msg = AppleAcct.account_owner

    elif AppleAcct is None:
        cookies_base = "".join([c for c in apple_id if match(r"\w", c)])
        cookies_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.cookies")
        session_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.session")
        await file_io.async_delete_file(cookies_filename)
        await file_io.async_delete_file(session_filename)

        apple_id_msg = apple_user(apple_id)

    elif AppleAcct not in Gb.AppleAcct_by_apple_id:
        return

    post_event( f"{EVLOG_NOTICE}Apple Acct > {apple_id_msg}, "
                f"Resetting iCloud Session Files")
    log_info_msg(   f"Apple Acct > {apple_id_msg}, "
                    f"Deleting Session Files ({Gb.icloud_cookies_directory})"
                    f"{CRLF_DOT}Cookies ({cookies_filename})"
                    f"{CRLF_DOT}Session ({session_filename})")

#--------------------------------------------------------------------
def is_apple_acct_logged_into(apple_id):
    '''
    An Apple Acct can be authenticated (reauth) only if its apple_id/password is valid
    and it was logged into. A login that only needs the 2fa code is logged into.

    Return:
        True  - Valid apple_id/password and logged into
        False - Unknown acct, invalid apple_id/password or the login failed
    '''
    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)

    return (AppleAcct is not None
            and AppleAcct.login_successful is True
            and Gb.upw_valid_by_apple_id.get(apple_id, False) is True)

#--------------------------------------------------------------------
def _apple_acct_filenames(apple_id):
    '''
    The .cookies, .session and .tpw files AppleAcctManager uses for the apple_id
    (see AppleAcctManager.make_cookie_filename_base_from_apple_id)
    '''
    cookies_base = "".join([c for c in apple_id if match(r"\w", c)])

    return [path.join(Gb.icloud_cookies_directory, f"{cookies_base}.{file_ext}")
                    for file_ext in ['cookies', 'session', 'tpw']]

#--------------------------------------------------------------------
async def async_delete_apple_acct_files(apple_id):
    '''
    Delete the .cookies, .session and .tpw files of an Apple Acct that was deleted
    '''
    if apple_id == '':
        return

    for filename in _apple_acct_filenames(apple_id):
        await file_io.async_delete_file(filename)

    log_info_msg(   f"Apple Acct > {apple_user(apple_id)}, Deleted the Session Files "
                    f"(.cookies, .session, .tpw)")

#--------------------------------------------------------------------
async def async_is_login_verifying_upw(apple_id):
    '''
    Determine if logging into the apple_id will verify the password itself, without
    a separate ValidateAppleAcctUPW SRP check first.

    An apple_id with no session token can only be signed into with a Password SRP
    signin, which verifies the password. Validating it first adds a second SRP signin
    that has to wait out SRP_SIGNIN_MIN_INTERVAL_SECS and sends a second 2fa push.

    Return:
        True  - Not logged in and no session token (new acct, session files deleted)
        False - Logged in or has a session token. The login signs in with the token
                without checking the password and a failed login would replace the
                working session, validate it first.
    '''
    AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
    if AppleAcct and AppleAcct.login_successful:
        return False

    session_filename = _apple_acct_filenames(apple_id)[1]
    session_data = await Gb.hass.async_add_executor_job(
                                    file_io.read_json_file, session_filename)

    return not (session_data or {}).get('session_token')

#--------------------------------------------------------------------
def _read_files(filenames):
    files_data = {}
    for filename in filenames:
        if path.exists(filename):
            with open(filename, 'rb') as f:
                files_data[filename] = f.read()
        else:
            files_data[filename] = None

    return files_data

def _restore_files(files_data):
    for filename, data in files_data.items():
        if data is None:
            file_io.delete_file(filename)
        else:
            with open(filename, 'wb') as f:
                f.write(data)

#--------------------------------------------------------------------
async def async_save_apple_acct_login_state(apple_id):
    '''
    Save what a login of the apple_id changes so it can be undone if Apple rejects
    the apple_id/password. A login creates and registers a new AppleAcct and writes
    the .cookies, .session and .tpw files even when it fails. The .tpw file gets the
    entered password, the TokenPW validation would accept it the next time.
    '''
    try:
        files_data = await Gb.hass.async_add_executor_job(
                                    _read_files, _apple_acct_filenames(apple_id))

    except Exception as err:
        log_exception(err)
        files_data = None

    return {'AppleAcct':  Gb.AppleAcct_by_apple_id.get(apple_id),
            'password':   Gb.AppleAcct_password_by_apple_id.get(apple_id),
            'files_data': files_data, }

#--------------------------------------------------------------------
async def async_restore_apple_acct_login_state(apple_id, saved_login_state):
    '''
    Undo a login of an apple_id/password Apple rejected
    (see async_save_apple_acct_login_state)
    '''
    failed_AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
    prev_AppleAcct   = saved_login_state['AppleAcct']

    if failed_AppleAcct and failed_AppleAcct is not prev_AppleAcct:
        update_alert_sensor(Source=failed_AppleAcct, error='login_failed', clear=True)

    if prev_AppleAcct:
        Gb.AppleAcct_by_apple_id[apple_id] = prev_AppleAcct
    else:
        Gb.AppleAcct_by_apple_id.pop(apple_id, None)

    if saved_login_state['password'] is not None:
        Gb.AppleAcct_password_by_apple_id[apple_id] = saved_login_state['password']
    else:
        Gb.AppleAcct_password_by_apple_id.pop(apple_id, None)

    if Gb.AppleAcctLoggingInto is failed_AppleAcct:
        Gb.AppleAcctLoggingInto = prev_AppleAcct

    if saved_login_state['files_data'] is not None:
        try:
            await Gb.hass.async_add_executor_job(
                                    _restore_files, saved_login_state['files_data'])

        except Exception as err:
            log_exception(err)

    log_info_msg(   f"Apple Acct > {apple_user(apple_id)}, Login rejected by Apple, "
                    f"Removed the failed login and restored the Session Files")

#--------------------------------------------------------------------
def is_asp_password(ui_password):
    '''
    True if the password is App Specific Password (ASP) format: uqvf-gguc-tzpd-knor
    '''

    return (len(ui_password) == 19
                and ui_password[4:5] == '-'
                and ui_password[9:10] == '-'
                and ui_password[14:15] == '-')

#--------------------------------------------------------------------
def login_err_msg(AppleAcct, apple_id):
    ipv6_info = Gb.InternetError.ha_system_network_ipv6_info()
    if ipv6_info:
        err_msg = 'apple_acct_login_error_ipv6'
    elif Gb.internet_error:
        err_msg = 'internet_error'
    elif AppleAcct and AppleAcct.response_code_pw == 503:
        err_msg = 'apple_acct_login_error_503'
    elif Gb.upw_valid_by_apple_id.get(apple_id, None) is False:
        err_msg = 'apple_acct_inupw_valid'
    else:
        err_msg = 'apple_acct_login_error_other'

    return err_msg

#--------------------------------------------------------------------
async def async_delete_icloud_session_requests_file(apple_id=None):
    '''
    Delete the cookies and session files as part of the reset_session and request_Authentication_code
    This is called from config_flow/setp_reauth and pyicloud_reset_session
    '''

    if apple_id is None:
        return

    post_event(f"{EVLOG_NOTICE}Configure Apple Acct > Resetting Cookie/Session Files")
    cookie_directory  = Gb.icloud_cookies_directory
    cookie_filename   = "".join([c for c in apple_id if match(r"\w", c)])

    delete_msg =  f"Apple Acct > Deleting Session Files > ({cookie_directory})"

    delete_msg += f"{CRLF_DOT}Session ({cookie_filename}.session)"
    await file_io.async_delete_file_with_msg(
                    'Apple Acct Session', cookie_directory, f"{cookie_filename}.session", delete_old_sv_file=True)

    post_monitor_msg(delete_msg)



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HARDWARE KEY AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_get_hwkey_names(self, AppleAcct=None):
    '''
    Retrieve HwKey names from Apple and update conf_auth_methods.
    Runs AppleAcct.get_hwkey_names() in executor (not in event loop).
    '''

    _AppleAcct_list = Gb.AppleAcct_by_apple_id.values() if AppleAcct is None else [AppleAcct]
    for _AppleAcct in _AppleAcct_list:
        try:
            await Gb.hass.async_add_executor_job(_AppleAcct.get_hwkey_names)

        except Exception as err:
            log_exception(err)

    return


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            DISCOVER APPLE ACCT DEVICES-IC3 DEVICES
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def build_import_devices_config_from_aadevices(self, AppleAcct):
    '''
    'iPhone de S': 'jso',
    'gary': 'gary', 'Gryphon': 'gryphon',
    iphone_van_bob': Bob,
    Annelinde (iphone_van_linde)
    iPad Air Bob (ipad_air_bob)
    Marco (device_tracker_marcos_iphone_app)
    Doris (device_tracker_doris_iphone_app)
    Marco’s iPhone (Schaeffler) (marcos_iphone_schaeffler)
    Marco's iPad Pro (marcos_ipad_pro_ic3)
    Doris' iPad Air (doris_ipad_air_ic3
    Marcos Watch (iwatch_marco)
    Doris Watch (iwatch_doris)
    'Apple Watch (Marcin)': 'apple_watch_marcin',
    'iPhone (Marcin)': 'iphone_15pro_marcin',
    'AirPods Pro (Marcin)': 'airpods_pro_marcin',
    'mmarczyk-mPK': 'macbook_pro_marcin',
    "Marcin Marczyk's iPad": 'ipad_marcin',
    'Apple Watch (Anna)': 'apple_watch_anna',
    'AirPods Pro (Anna)': 'airpods_pro_anna',
    'iPhone (Anna) (3)': 'iphone_15_anna',
    'MacBook Air': 'macbook_air_anna'}
    iPhone de Jorge E.': 'iphone_oso'}

    '''
    device_id_filter = [conf_device[CONF_AADEV_DEVICE_ID]
                            for conf_device in Gb.conf_devices
                            if conf_device[CONF_APPLE_ACCT] == AppleAcct.apple_id]

    # Build list of existing devicenames and fnames. Then add devicenames and fnames just imported
    dt_devicenames, _    = entity_io.get_entity_registry_data(domain=DEVICE_TRACKER)
    existing_devicenames = [dt_devicename.replace('device_tracker.', '') for dt_devicename in dt_devicenames]
    existing_fnames      = [conf_device[CONF_FNAME] for conf_device in Gb.conf_devices]

    for item_key, ic3_conf_device in self.imported_aa_ic3_conf_devices.items():
        list_add(existing_devicenames, ic3_conf_device[CONF_IC3_DEVICENAME])
        list_add(existing_fnames, ic3_conf_device[CONF_FNAME])

    aa_devices_to_add = {}
    for aadevice_dname, device_id in AppleAcct.device_id_by_aadev_dname.items():
        # Filter devices that already been added to the config file
        if (device_id in device_id_filter):
            continue

        raw_model, model, model_display_name = \
                    AppleAcct.device_model_info_by_aadev_dname[aadevice_dname]

        AADev  = AppleAcct.AADev_by_device_id.get(device_id)
        first_name = AADev.owner_first_name if AADev else None
        aadev_name = AADev.name if AADev else aadevice_dname
        ic3_fname  = make_ic3_fname_from_aadevice_dname(aadev_name, model, first_name)

        ic3_devicename = slugify(ic3_fname)
        ic3_fname      = ic3_fname.replace('-iPhone', '')

        # Check if an iCloud3 device that is inactive, change trk mode instead of add again
        conf_device_idx = Gb.conf_devices_idx_by_devicename.get(ic3_devicename, -1)
        if conf_device_idx == -1:
            pass
        elif Gb.conf_devices[conf_device_idx][CONF_TRACKING_MODE] == INACTIVE:
            pass
        else:
            ic3_devicename = _make_unique_ic3_devicename(existing_devicenames, ic3_devicename)
            ic3_fname      = _make_unique_ic3_fname(existing_fnames, ic3_fname)

        list_add(existing_devicenames, ic3_devicename)
        list_add(existing_fnames, ic3_fname)

        ic3_conf_device = {}
        ic3_conf_device[CONF_IC3_DEVICENAME]     = ic3_devicename
        ic3_conf_device[CONF_FNAME]              = ic3_fname
        ic3_conf_device[CONF_APPLE_ACCT]      = AppleAcct.apple_id
        ic3_conf_device[CONF_AADEV_NAME]  = aadevice_dname
        # ic3_conf_device.update(aadevice_conf( aadevice_dname, device_id,
        #                     model, raw_model, model_display_name))
        ic3_conf_device[CONF_AADEV_DEVICE_ID]   = device_id
        ic3_conf_device[CONF_DEVICE_TYPE]        = model.lower() if model in DEVICE_TYPES else 'iphone'
        ic3_conf_device[CONF_RAW_MODEL]          = raw_model
        ic3_conf_device[CONF_MODEL]              = model
        ic3_conf_device[CONF_MODEL_DISPLAY_NAME] = model_display_name
        ic3_conf_device[CONF_MOBILE_APP_DEVICE]  = 'None'
        device_type = model.lower()
        ic3_conf_device[CONF_TRACKING_MODE] = DEVICE_TYPE_TRACKING_MODE(device_type)
        ic3_conf_device[CONF_ICON] = DEVICE_TYPE_ICONS.get(device_type, 'mdi:account')
        if device_type in DEVICE_TYPE_PICTURE_FILENAMES:
            ic3_conf_device[CONF_PICTURE] = f'{Gb.www_evlog_js_directory}/{DEVICE_TYPE_PICTURE_FILENAMES[device_type]}'

        # Gb.device_info_by_mobapp_dname={'lillian_ipad_app': ['Lillian-iPad-app', 'iPad14,3', 'iPad14,3', 'iPadPro4'],
        # 'gary_iphone_app': ['Gary-iPhone-app', 'iPhone17,2', 'iPhone', 'iPhone16ProMax'],
        # 'gary_ipad_app': ['Gary-iPad-app', 'iPad16,3', 'iPad16,3', 'iPadPro']}

        for mobapp_dname, mobapp_info in Gb.device_info_by_mobapp_dname.items():
            mobapp_fname, mobapp_raw_model, mobapp_device_type, mobapp_model_display_name = mobapp_info

            if mobapp_raw_model == raw_model:
                if (instr(mobapp_dname, ic3_devicename)
                        or instr(ic3_devicename, mobapp_dname)
                        or instr(ic3_fname, mobapp_fname)
                        or instr(mobapp_fname, ic3_fname)):
                    ic3_conf_device[CONF_MOBILE_APP_DEVICE] = mobapp_dname
                    break

        # Create a sort_key = Tracking_mode (track/monitor/inactive),device_type,ic3_fname
        sk_tracking_mode = sk_device_type = 99
        if ic3_conf_device[CONF_TRACKING_MODE] in TRACKING_MODES:
            sk_tracking_mode = TRACKING_MODES.index(ic3_conf_device[CONF_TRACKING_MODE])
        if model in DEVICE_TYPES:
            sk_device_type = DEVICE_TYPES.index(model)
        sort_key = f"{sk_tracking_mode},{sk_device_type:02},{ic3_fname}"

        aa_devices_to_add[sort_key] = ic3_conf_device

    sorted_aa_devices_to_add = dict_sort(aa_devices_to_add)

    return sorted_aa_devices_to_add

# ---------------------------------------------------------------------------
def aadevice_conf( aadevice_dname, device_id,
                            model, raw_model, model_display_name):

    aadev_info = {}
    aadev_info[CONF_AADEV_NAME]  = aadevice_dname
    aadev_info[CONF_AADEV_DEVICE_ID]   = device_id
    aadev_info[CONF_DEVICE_TYPE]        = model.lower() if model in DEVICE_TYPES else 'iphone'
    aadev_info[CONF_RAW_MODEL]          = raw_model
    aadev_info[CONF_MODEL]              = model
    aadev_info[CONF_MODEL_DISPLAY_NAME] = model_display_name

    return aadev_info
# ---------------------------------------------------------------------------
def _make_unique_ic3_devicename(existing_devicenames, ic3_devicename):
    '''
    The devicename is built from the Apple Device dname field. Make sure it
    is not used for another HA device. If so, generate a unique name
    '''
    if ic3_devicename not in existing_devicenames:
        return ic3_devicename

    # If ic3_devicename already used, add '_ic3' and then a '_#' suffix
    ic3_devicename += '_ic3'

    cnt = 1
    while ic3_devicename in existing_devicenames:
        cnt += 1
        ic3_devicename = f"{ic3_devicename}_{cnt}"

    return ic3_devicename

# ---------------------------------------------------------------------------
def _make_unique_ic3_fname(existing_fnames, ic3_fname):
    '''
    The fname is built from the Apple Device dname field. Make sure it
    is not used for another iCloud3 device. If so, generate a unique name.
    '''
    if ic3_fname not in existing_fnames:
        return ic3_fname

    # If ic3_fename already used, add '_ic3' and then a '_#' suffix
    ic3_fname += '_ic3'

    cnt = 1
    while ic3_fname in existing_fnames:
        cnt += 1
        ic3_fname = f"{ic3_fname}_{cnt}"

    return ic3_fname
