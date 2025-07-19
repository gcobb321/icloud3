

from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF_DOT, EVLOG_NOTICE, EVLOG_ERROR, EVLOG_ALERT,
                                CONF_APPLE_ACCOUNT, CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_VERIFICATION_CODE,
                                ALERT_APPLE_ACCT,
                                )

from ..utils.utils      import (instr, isnumber, is_empty, isnot_empty, list_add, list_del,
                                encode_password, decode_password, username_id, )
from ..utils.messaging  import (post_event, post_monitor_msg, post_error_msg, post_alert,
                                log_exception, log_debug_msg, log_info_msg, _log, _evlog,
                                add_log_file_filter, )

from .                  import selection_lists as lists

from ..apple_acct.pyicloud_ic3  import (PyiCloudManager, PyiCloudFailedLoginException, )
from ..startup          import start_ic3
from ..utils            import file_io

#--------------------------------------------------------------------
from re                  import match

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#          APPLE ACCOUNT ICLOUD SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def log_into_apple_account(self, user_input, called_from_step_id=None):
    '''
    Log into the icloud account and check to see if a verification code is needed.
    If so, show the verification form, get the code from the user, verify it and
    return to the 'called_from_step_id' (icloud_account).

    Input:
        user_input  = A dictionary with the username and password, or
                        {username: icloudAccountUsername, password: icloudAccountPassword}
                    = {} to use the username/password in the tracking configuration parameters
        called_from_step_id
                    = The step logging into the iCloud account. This step will be returned
                        to when the login is complete.

    Exception:
        The self.PyiCloud.requres_2fa must be checked after a login to see if the account
        access needs to be verified. If so, the verification code entry form must be displayed.

    Returns:
        self.Pyicloud object
        self.PyiCloud_AppleAcctDevices object
        self.PyiCloud_FindMyFriends object
        self.opt_icloud_dname_list & self.device_form_icloud_famf_list =
                A dictionary with the devicename and identifiers
                used in the tracking configuration devices icloud_device parameter
    '''
    self.errors = {}
    called_from_step_id = called_from_step_id or 'update_apple_acct'

    # The username may be changed to assign a new account, if so, log into the new one
    if CONF_USERNAME not in user_input or CONF_PASSWORD not in user_input:
        return

    username = user_input[CONF_USERNAME].lower()
    password = user_input[CONF_PASSWORD]

    add_log_file_filter(username, f"**{self.aa_idx}**")
    add_log_file_filter(password)

    apple_server_location = user_input.get(CONF_SERVER_LOCATION,'usa')

    log_info_msg(   f"Apple Acct > {username}, Logging in, "
                    f"UserInput-{user_input}, Errors-{self.errors}, "
                    f"Step-{self.step_id}, CalledFrom-{called_from_step_id}")

    # Already logged in and no changes
    PyiCloud = Gb.PyiCloud_by_username.get(username)
    if (PyiCloud
            and password == PyiCloud.password
            and apple_server_location == PyiCloud.apple_server_location
            and PyiCloud.login_successful):
        self.PyiCloud = PyiCloud
        self.username = username
        self.password = password
        self.header_msg = 'apple_acct_logged_into'

        log_info_msg(f"Apple Acct > {username}, Already Logged in, {self.PyiCloud}")
        return True

    # Validate the account before actually logging in
    valid_upw = await Gb.ValidateAppleAcctUPW.async_validate_username_password(username, password)

    if valid_upw is False:
        if username in Gb.username_valid_by_username:
            del Gb.username_valid_by_username[username]
        self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
        log_info_msg(f"Apple Acct > {username}, Invalid Username/password")
        return False


    event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into Apple Account {username}")
    if apple_server_location != 'usa':
        event_msg += f", iCloud.com ServerSuffix-{apple_server_location}"
    log_info_msg(event_msg)

    try:
        await file_io.async_make_directory(Gb.icloud_cookie_directory)

        PyiCloud = None
        PyiCloud = await Gb.hass.async_add_executor_job(
                                    create_PyiCloudManager_config_flow,
                                    username,
                                    password,
                                    apple_server_location)

        # Successful login, set PyiCloud fields
        self.PyiCloud = PyiCloud
        self.username = username
        self.password = password
        self.apple_server_location = apple_server_location
        Gb.username_valid_by_username[username] = True
        log_info_msg(f"Apple Acct > {username}, Login successful, {self.PyiCloud}")

        start_ic3.dump_startup_lists_to_log()

        if PyiCloud.requires_2fa or called_from_step_id is None:
            log_info_msg(f"Apple Acct > {username}, 2fa Verification Needed, {self.PyiCloud}")
            return True

        self.header_msg = 'apple_acct_logged_into'

        if called_from_step_id is None:
            return True

        return self.async_show_form(step_id=called_from_step_id,
                    data_schema=self.form_schema(called_from_step_id),
                    errors=self.errors)

    # Login Failed, display error messages
    except (PyiCloudFailedLoginException) as err:
        err = str(err)
        Gb.HALogger.error(f"Error logging into Apple Acct: {err}")

        # if called_from_step_id == 'update_apple_acct':
        response_code = Gb.PyiCloudLoggingInto.response_code
        if Gb.PyiCloudLoggingInto.response_code_pwsrp_err == 503:
            list_add(Gb.username_pyicloud_503_internet_error, username)
            error_msg = 'apple_acct_login_error_503'
        elif response_code == 302:
            error_msg = 'apple_acct_login_error_302'

            if Gb.PyiCloudLoggingInto is not None:
                country_code = Gb.PyiCloudLoggingInto.account_country_code
                apple_server_location = Gb.PyiCloudLoggingInto.apple_server_location

                if (country_code == 'CHN' and apple_server_location == 'usa'):
                    self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_cn'
                elif (country_code != 'CHN' and apple_server_location == '.cn'):
                    self.errors[CONF_SERVER_LOCATION] = 'apple_acct_login_error_302_usa'

        elif response_code == 400:
            self.errors['base'] = 'apple_acct_invalid_upw'
        elif response_code == 401 and instr(err, 'Python SRP'):
            self.errors['base'] = 'apple_acct_login_error_srp_401'
        elif response_code == 401:
            self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
        else:
            self.errors['base'] = 'apple_acct_login_error_other'

        log_info_msg(   f"Apple Acct > {username}, Login Failed, "
                        f"Error-{err}/{error_msg}, Code-{response_code}")

    except Exception as err:
        log_exception(err)
        Gb.HALogger.error(f"Error logging into Apple Account: {err}")
        self.errors['base'] = 'apple_acct_login_error_other'

    start_ic3.dump_startup_lists_to_log()
    return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            CREATE PYICLOUD SERVICE OBJECTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
def create_PyiCloudManager_config_flow(username, password, apple_server_location):
    '''
    Create the PyiCloudManager object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    PyiCloud session
    '''
    PyiCloud = PyiCloudManager( username,
                                password,
                                apple_server_location=apple_server_location,
                                cookie_directory=Gb.icloud_cookie_directory,
                                session_directory=Gb.icloud_session_directory,
                                config_flow_login=True)

    if PyiCloud and PyiCloud.login_successful:
        log_debug_msg(  f"Apple Acct > {PyiCloud.account_owner}, Login Successful, "
                        f"{PyiCloud.response_code_desc}, "
                        f"Update Connfiguration")
    else:
        raise PyiCloudFailedLoginException

    # start_ic3.dump_startup_lists_to_log()
    return PyiCloud

#--------------------------------------------------------------------
@staticmethod
def create_AADevices_config_flow(PyiCloud):

    _AADevices = PyiCloud.create_AADevices_object(config_flow_login=True)

    start_ic3.dump_startup_lists_to_log()
    return _AADevices


#..............................................................................................
def clear_PyiCloud_2fa_flags():
    for username, PyiCloud in Gb.PyiCloud_by_username.items():
        if PyiCloud.requires_2fa:
            PyiCloud.new_2fa_code_already_requested_flag = False

#..............................................................................................
@staticmethod
async def reauth_send_verification_code_handler(caller_self, user_input):
    '''
    Handle the send_verification_code action. This is called from the ConfigFlow and OptionFlow
    reauth steps in each Flow. This provides this function with the appropriate data and return objects.

    Parameters:
        - caller_self = 'self' for OptionFlow and the _OptFlow object when calling from ConfigFlow
                        OptionFlow --> valid_code = await self.reauth_send_verification_code_handler(
                                                                self, user_input)
                        ConfigFlow --> valid_code = await _OptFlow.reauth_send_verification_code_handler(
                                                                _OptFlow, user_input)
        - user_input = user_input dictionary
    '''
    try:
        PyiCloud = caller_self.PyiCloud
        valid_code = await Gb.hass.async_add_executor_job(
                                    PyiCloud.validate_2fa_code,
                                    user_input[CONF_VERIFICATION_CODE])

        # Do not restart iC3 right now if the username/password was changed on the
        # iCloud setup screen. If it was changed, another account is being logged into
        # and it will be restarted when exiting the configurator.
        if valid_code:
            post_event( f"{EVLOG_NOTICE}Configure Apple Acct > {PyiCloud.account_owner}, "
                        f"Code accepted, Verification completed")

            # Refresh the device list if the apple acct is being setup for the first time
            # If PyiCloud.device_id_by_icloud_dname is empty, a verification code was needed
            # when first logged in and the apple acct data was not authenticated and it's
            # device data was never loaded/initialized by refreshed_icloud_data. This
            # prevents the device's list tables to never be initialized and location data
            # is not available. Do this now.
            if is_empty(PyiCloud.device_id_by_icloud_dname):
                await async_finish_authentication_and_data_refresh(caller_self)

            await lists.build_icloud_device_selection_list(caller_self)

            Gb.EvLog.clear_evlog_greenbar_msg()
            Gb.icloud_force_update_flag = True
            PyiCloud.new_2fa_code_already_requested_flag = False
            lists.build_apple_accounts_list(caller_self)

            caller_self.errors['base'] = caller_self.header_msg = 'verification_code_accepted'
            post_alert(PyiCloud.username_id, '')

        else:
            post_event( f"{EVLOG_NOTICE}Configure Apple Acct > Verification Code is invalid "
                        f"({user_input[CONF_VERIFICATION_CODE]})")
            caller_self.errors[CONF_VERIFICATION_CODE] = 'verification_code_invalid'

        return valid_code

    except Exception as err:
        log_exception(err)


#--------------------------------------------------------------------
async def async_finish_authentication_and_data_refresh(caller_self):
    '''
    Refresh the device list if the apple acct is being setup for the first time
    If PyiCloud.device_id_by_icloud_dname is empty, a verification code was needed
    when first logged in and the apple acct data was not authenticated and it's
    device data was never loaded/initialized by refreshed_icloud_data. This
    prevents the device's list tables to never be initialized and location data
    is not available. Do this now.
    '''
    PyiCloud = caller_self.PyiCloud
    PyiCloud.login_successful = await Gb.hass.async_add_executor_job(
                                PyiCloud.authenticate)

    if PyiCloud.login_successful is False:
        err_msg = ( f"Apple Acct > {caller_self.username_base}, Authentication Failed, "
                            f"{caller_self.response_code_desc}, "
                            f"AppleServerLocation-`{caller_self.apple_server_location}`, "
                            "Location Data not Refreshed")
        post_error_msg(err_msg)
        return

    locate_all_devices = True
    Gb.start_icloud3_inprocess_flag = True
    await Gb.hass.async_add_executor_job(
                            PyiCloud.refresh_icloud_data,
                            locate_all_devices)
    Gb.start_icloud3_inprocess_flag = False

#--------------------------------------------------------------------
async def async_pyicloud_reset_session(self, username, password):
    '''
    Reset the current session and authenticate to restart pyicloud_ic3
    and enter a new verification code

    The username & password are specified in case the Apple acct is not logged
    into because of an error
    '''
    try:
        PyiCloud = self.PyiCloud
        if PyiCloud:
            pyicloud_username = PyiCloud.username or self.username

            post_event(f"{EVLOG_NOTICE}Configure Apple Acct > {PyiCloud.username_id}, Authentication Needed")

            await async_delete_pyicloud_session_file(pyicloud_username)
            # await async_delete_pyicloud_session_file(PyiCloud.username)

            if PyiCloud.authentication_alert_displayed_flag is False:
                PyiCloud.authentication_alert_displayed_flag = True

            await Gb.hass.async_add_executor_job(PyiCloud.setup_new_apple_account_session)

            # Initialize PyiCloud object to force a new one that will trigger the 2fa process
            PyiCloud.verification_code = None

        # The Apple acct is not logged into. There may have been some type Of error.
        # Delete the session files for the username selected on the request form and
        # try to login
        elif username and password:
            post_event(f"{EVLOG_NOTICE}Configure Apple Acct > {username_id(username)}, Authentication Needed")

            await self.async_delete_pyicloud_session_file(username)

            user_input = {}
            user_input[CONF_USERNAME] = username
            user_input[CONF_PASSWORD] = password

            await log_into_apple_account(self, user_input)

            PyiCloud = self.PyiCloud

        if PyiCloud:
            post_event( f"{EVLOG_NOTICE}Configure Apple Acct > {PyiCloud.username_id}, "
                        f"Waiting for the 6-digit Verification Code to be entered")
            return

    except PyiCloudFailedLoginException as err:
        login_err = str(err)
        login_err + ", Will retry logging into the Apple Account later"

    except Exception as err:
        login_err = str(err)
        log_exception(err)

    if instr(login_err, '-200') is False:
        PyiCloudSession = Gb.PyiCloudSession_by_username.get(username)
        if PyiCloudSession and PyiCloudSession.response_code == 503:
            list_add(Gb.username_pyicloud_503_internet_error, username)
            self.errors['base'] = 'apple_acct_login_error_503'

        if PyiCloudSession.response_code == 503:
            post_event( f"{EVLOG_ERROR}Configure Apple Acct > {username}, "
                        f"Apple is delaying displaying a new Verification code to "
                        f"prevent Suspicious Activity, probably due to too many requests. "
                        f"It should be displayed in about 20-30 minutes. "
                        f"{CRLF_DOT}The Apple Acct login will be retried within 15-mins. "
                        f"The Verification Code will be displayed then if successful")
        else:
            post_event( f"{EVLOG_ERROR}Configure Apple Acct > {username}, "
                        f"An Error was encountered requesting the 6-digit Verification Code, "
                        f"{login_err}")


#--------------------------------------------------------------------
async def async_delete_pyicloud_session_file(username=None):
    '''
    Delete the cookies and session files as part of the reset_session and request_verification_code
    This is called from config_flow/setp_reauth and pyicloud_reset_session
    '''

    if username is None:
        return

    post_event(f"{EVLOG_NOTICE}Configure Apple Acct > Resetting Cookie/Session Files")
    cookie_directory  = Gb.icloud_cookie_directory
    cookie_filename   = "".join([c for c in username if match(r"\w", c)])

    delete_msg =  f"Apple Acct > Deleting Session Files > ({cookie_directory})"

    delete_msg += f"{CRLF_DOT}Session ({cookie_filename}.session)"
    await file_io.async_delete_file_with_msg(
                    'Apple Acct Session', cookie_directory, f"{cookie_filename}.session", delete_old_sv_file=True)
    # delete_msg += f"{CRLF_DOT}Token Password ({cookie_filename}.tpw)"
    # await file_io.async_delete_file_with_msg(
    #                 'Apple Acct Tokenpw', cookie_directory, f"{cookie_filename}.tpw")
    post_monitor_msg(delete_msg)

#--------------------------------------------------------------------
async def async_delete_all_pyicloud_cookies_session_files():
    '''
    Cycle through the Apple accounts and delete the cookie and session files
    '''

    post_event(f"{EVLOG_ALERT}Configure All Apple Account Cookies and Session files are being deleted")

    for Device in Gb.Devices:
        Device.pause_tracking()

    start_dir = Gb.icloud_cookie_directory
    file_filter = []
    apple_acct_cookie_files = await Gb.hass.async_add_executor_job(
                                        file_io.get_filename_list,
                                        start_dir,
                                        file_filter)

    try:
        for apple_acct_cookie_file in apple_acct_cookie_files:
            await file_io.async_delete_file(f"{Gb.icloud_cookie_directory}/{apple_acct_cookie_file}")

        if isnot_empty(apple_acct_cookie_files):
            await file_io.async_delete_directory(Gb.icloud_cookie_directory)

    except Exception as err:
        log_exception(err)
