

from ..global_variables import GlobalVariables as Gb
from ..const            import (CRLF_DOT, EVLOG_NOTICE, EVLOG_ERROR, EVLOG_ALERT,
                                ICLOUD, CONF_DATA_SOURCE,
                                CONF_APPLE_ACCOUNT, CONF_USERNAME, CONF_PASSWORD, CONF_LOCATE_ALL,
                                CONF_SERVER_LOCATION, CONF_AUTH_CODE,
                                CONF_AUTH_METHODS, CONF_LAST_METHOD, PUSH, TEXT,
                                )

from ..utils.utils      import (instr, is_number, is_empty, isnot_empty,
                                list_add, list_del, dict_del,
                                encode_password, decode_password, username_id,
                                is_running_in_event_loop, )
from ..utils.messaging  import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                post_greenbar_msg, clear_greenbar_msg,
                                update_alert_sensor,
                                log_exception, log_debug_msg, log_info_msg, _log, _evlog,
                                add_log_file_filter, )
from ..utils.time_util  import (time_now_secs, secs_to_hhmm, )


from ..apple_acct.apple_acct import (AppleAcctManager, AppleAcctFailedLoginException, HTTP_RESPONSE_CODES)
from ..configure        import utils_configure as utils
from ..configure        import selection_lists as lists
from ..configure.const_form_lists import REAUTH_AUTH_METHODS
from ..startup          import config_file
from ..startup          import start_ic3
from ..utils            import file_io

#--------------------------------------------------------------------
from re                 import match
from os                 import path

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#          APPLE ACCOUNT ICLOUD SUPPORT ROUTINES
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_log_into_apple_account(self, user_input, return_to_step_id=None):
    '''
    Log into the icloud account and check to see if a verification code is needed.
    If so, show the verification form, get the code from the user, verify it and
    return to the 'return_to_step_id' (icloud_account).

    Input:
        user_input  = A dictionary with the username and password, or
                        {username: icloudAccountUsername, password: icloudAccountPassword}
                    = {} to use the username/password in the tracking configuration parameters
        return_to_step_id
                    = The step logging into the iCloud account. This step will be returned
                        to when the login is complete.

    Exception:
        The self.AppleAcct.requres_2fa must be checked after a login to see if the account
        access needs to be verified. If so, the verification code entry form must be displayed.

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
        return_to_step_id = return_to_step_id or 'update_apple_acct'

        # The username may be changed to assign a new account, if so, log into the new one
        if CONF_USERNAME not in user_input or CONF_PASSWORD not in user_input:
            return False

        username = user_input[CONF_USERNAME].lower()
        password = user_input[CONF_PASSWORD]

        add_log_file_filter(username, f"**{self.aa_idx}**")
        add_log_file_filter(username.upper(), f"**{self.aa_idx}**")
        add_log_file_filter(password)

        apple_server_location = user_input.get(CONF_SERVER_LOCATION,'usa')

        log_info_msg(   f"Apple Acct > {username}, Logging in, "
                        f"UserInput-{user_input}, Errors-{self.errors}, "
                        f"Step-{self.step_id}, CalledFrom-{return_to_step_id}")

        # Already logged in and no changes
        AppleAcct = Gb.AppleAcct_by_username.get(username)
        if (AppleAcct
                and password == AppleAcct.password
                and apple_server_location == AppleAcct.apple_server_location
                and AppleAcct.login_successful):
            self.AppleAcct = AppleAcct
            self.username = username
            self.password = password
            self.header_msg = 'apple_acct_logged_into'

            log_info_msg(f"Apple Acct > {username}, Already Logged in, {self.AppleAcct}")
            # return True

        # Validate the account before actually logging in
        valid_upw = await Gb.ValidateAppleAcctUPW.async_validate_username_password(username, password)
        if valid_upw is False:
            if username in Gb.valid_upw_by_username:
                del Gb.valid_upw_by_username[username]
            self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
            log_info_msg(f"Apple Acct > {username}, Invalid Username/password")
            return False


        event_msg =(f"{EVLOG_NOTICE}Configure Settings > Logging into Apple Account {username}")
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
                                    username,
                                    password,
                                    apple_server_location)

        # TEST CODE -Test Internet error and AppleAcct login failure
        # _log("TEST CODE ENABLED")
        # AppleAcct = None
        # Gb.internet_error = True

        if AppleAcct is None:
            self.AppleAcct = None
            log_info_msg(f"Apple Acct > {username}, Login Failed")
            return False

        # Successful login, set AppleAcct fields
        self.AppleAcct = AppleAcct
        self.username = username
        self.password = password
        self.apple_server_location = apple_server_location
        Gb.valid_upw_by_username[username] = True
        log_info_msg(f"Apple Acct > {username}, Login successful, {self.AppleAcct}")

        start_ic3.dump_startup_lists_to_log()

        if AppleAcct.is_auth_code_needed or return_to_step_id is None:
            log_info_msg(f"Apple Acct > {username}, 2fa Verification Needed, {self.AppleAcct}")
            alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_auth_code_needed_secs)})"
            update_alert_sensor(AppleAcct.username_id, alert_msg)
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
            self.errors['base'] = 'apple_acct_invalid_upw'
        elif response_code == 401 and instr(err, 'Python SRP'):
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors['base'] = 'apple_acct_login_error_srp_401'
        elif response_code == 401:
            Gb.AppleAcctLoggingInto.setup_error(401)
            self.errors[CONF_USERNAME] = 'apple_acct_invalid_upw'
        elif response_code == 403:
            Gb.AppleAcctLoggingInto.setup_error(403)
            self.errors[CONF_USERNAME] = 'apple_acct_locked'
        else:
            Gb.AppleAcctLoggingInto.setup_error(response_code)
            self.errors['base'] = 'apple_acct_login_error_other'
        error_msg = HTTP_RESPONSE_CODES.get(response_code, 'Other Error')

        post_error_msg( f"Apple Acct > {username}, Login Failed, "
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
def create_AppleAcctManager_config_flow(username, password, apple_server_location):
    '''
    Create the AppleAcctManager object without going through the error checking and
    authentication test routines. This is used by config_flow to open a second
    AppleAcct session
    '''
    try:
        AppleAcct = None
        AppleAcct = AppleAcctManager( username,
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
                        f"Update Connfiguration")
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
    for username, AppleAcct in Gb.AppleAcct_by_username.items():
        if AppleAcct.is_auth_code_needed:
            AppleAcct.was_ha_auth_code_alert_sent = False

#--------------------------------------------------------------------
async def async_finish_authentication_and_data_refresh(caller_self):
    '''
    Refresh the device list if the apple acct is being setup for the first time
    If AppleAcct.device_id_by_icloud_dname is empty, a verification code was needed
    when first logged in and the apple acct data was not authenticated and it's
    device data was never loaded/initialized by refreshed_icloud_data. This
    prevents the device's list tables to never be initialized and location data
    is not available. Do this now.
    '''
    AppleAcct = caller_self.AppleAcct
    AppleAcct.login_successful = \
        await Gb.hass.async_add_executor_job(AppleAcct.authenticate)

    if AppleAcct.login_successful is False:
        err_msg = ( f"Apple Acct > {AppleAcct.username_base}, Authentication Failed, "
                    f"Error-{AppleAcct.response_code_desc}, "
                    f"AppleServerLocation-`{AppleAcct.apple_server_location}`, "
                    "Location Data not Refreshed")
        post_error_msg(err_msg)
        return

    locate_all_devices = True
    Gb.is_icloud3_startup_inprocess = True
    await Gb.hass.async_add_executor_job(
                            AppleAcct.refresh_icloud_data,
                            locate_all_devices)
    Gb.is_icloud3_startup_inprocess = False

#--------------------------------------------------------------------
async def async_get_fido2_key_names(AppleAcct=None):
    '''
    Update the fido2 Security Key Names list in all or the selected AppleAcct account.

    THIS IS RUNNING IN THE EVENT LOOP. CALL AppleAcct.get_fido2_key_names TO GET THE KEY NAMES
    SINCE IT IS NOT RUNNING IN THE EVENT LOOP AND CAN DO REQUEST CALLS
    '''
    if Gb.fido2_security_keys_enabled is False:
        return None

    _AppleAcct_list = Gb.AppleAcct_by_username.values() if AppleAcct is None else [AppleAcct]

    for AppleAcct in _AppleAcct_list:
        try:
            _fido2_key_names = await Gb.hass.async_add_executor_job(AppleAcct.get_fido2_key_names)
            # _log(f'{AppleAcct.username} {_fido2_key_names=} {AppleAcct.fido2_key_names=}')

            # if _fido2_key_names is not None:
            #     _trusted_session = await Gb.hass.async_add_executor_job(AppleAcct.trust_session)
            #     _log(f'{AppleAcct.username} {_trusted_session=}')

            #     _fido2_key_names = await Gb.hass.async_add_executor_job(AppleAcct.get_fido2_key_names)
            #     _log(f'{AppleAcct.username} {_fido2_key_names=}')

            #     _trusted_devices = await Gb.hass.async_add_executor_job(AppleAcct.trusted_devices)
            #     _log(f'{AppleAcct.username} {_trusted_devices=}')

        except Exception as err:
            log_exception(err)


#--------------------------------------------------------------------
async def async_confirm_fido2_security_key(AppleAcct, fido2_key_name):
    '''
    Update the fido2 Security Key Names list in all or the selected AppleAcct account.
    Use a AppleAcct non-Event Loop function to do the actual fido2 call to prevent
    running in Event Loop errors.
    '''

    try:
        # _log(f'{AppleAcct=} {fido2_key_name=}')
        valid_key = await Gb.hass.async_add_executor_job(
                                                AppleAcct.confirm_fido2_security_key,
                                                fido2_key_name)

    except Exception as err:
        log_exception(err)
        valid_key = False

    # _log(f'{valid_key=}')

    return valid_key

#--------------------------------------------------------------------
# def delete_AppleAcct_trust_cookie(AppleAcct):
#     AppleAcct.iCloudSession.cookies.delete('X-APPLE-WEBAUTH-HSA-TRUST')
#     AppleAcct.iCloudSession.cookies.save()

#--------------------------------------------------------------------
async def async_delete_icloud_session_file(AppleAcct, username):
    '''
    Delete the cookies and session files as part of the reset_session
    and request_auth_code. This is called from config_flow/step_reauth
    and pyicloud_reset_session
    '''
    if AppleAcct:
        cookies_filename = AppleAcct.cookies_filename
        session_filename = AppleAcct.session_filename
        AppleAcct.delete_cookie_and_session_files()

        username_msg = AppleAcct.account_owner

    elif AppleAcct is None:
        cookies_base = "".join([c for c in username if match(r"\w", c)])
        cookies_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.cookies")
        session_filename = path.join(Gb.icloud_cookies_directory, f"{cookies_base}.session")
        await file_io.async_delete_file(cookies_filename)
        await file_io.async_delete_file(session_filename)

        username_msg = username_id(username)

    elif AppleAcct not in Gb.AppleAcct_by_username:
        return

    post_event( f"{EVLOG_NOTICE}Apple Acct > {username_msg}, "
                f"Resetting iCloud Session Files")
    log_info_msg(   f"Apple Acct > {username_msg}, "
                    f"Deleting Session Files ({Gb.icloud_cookies_directory})"
                    f"{CRLF_DOT}Cookies ({cookies_filename})"
                    f"{CRLF_DOT}Session ({session_filename})")

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
def login_err_msg(AppleAcct, username):
    ipv6_info = Gb.InternetError.ha_system_network_ipv6_info()
    if ipv6_info:
        err_msg = 'apple_acct_login_error_ipv6'
    elif Gb.internet_error:
        err_msg = 'internet_error'
    elif AppleAcct and AppleAcct.response_code_pw == 503:
        err_msg = 'apple_acct_login_error_503'
    elif Gb.valid_upw_by_username.get(username, None) is False:
        err_msg = 'apple_acct_invalid_upw'
    else:
        err_msg = 'apple_acct_login_error_other'

    return err_msg

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#           APPLE ACCOUNT REAUTHENTICATION SUPPORT ROUTINES
#           USED IN CONFIG_FLOW IN THE REAUTH ONLY AND THE DATA_FLOW REAUTH HANDLER
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
async def async_step_reauth_handler(self,
                                    user_input=None, errors=None,
                                    return_to_step_id=None, reauth_username=None):
    '''
    Ask the verification code to the user.

    The iCloud account needs to be verified. Show the code entry form, get the
    code from the user, send the code back to Apple ID iCloud via pyicloud and get
    a valid code indicator or invalid code error.

    If the code is valid, either:
        - return to the return_to_step_id (icloud_account form) if in the config_flow configuration routine or,
        - issue a 'create_entry' indicating a successful verification. This will return
        to the function it wass called from. This will be when a validation request was
        needed during the normal tracking.

    If invalid, display an error message and ask for the code again.

    Input:
        - return_to_step_id
                = the step_id in the config_glow if the icloud3 configuration
                    is being updated
                = None if the rquest is from another regular function during the normal
                    tracking operation.
    '''
    action_item = ''
    AppleAcct = self.AppleAcct

    if Gb.internet_error:
        self.errors['base'] = 'internet_error_no_change'

    if len(Gb.conf_apple_accounts) == 0:
        self.header_msg = 'apple_acct_not_set_up'

    elif AppleAcct is None:
        self.errors['account_selected'] = 'apple_acct_not_logged_into'

    if user_input is None:
        # await async_get_fido2_key_names()
        reauth_username = self.apple_acct_reauth_username
        return 'refresh_screen', reauth_username, user_input, errors

    if reauth_username is None:
        reauth_username = self.apple_acct_reauth_username

    try:
        user_input, action_item = utils.action_text_to_item(self, user_input)

        user_input = utils.strip_spaces(user_input, [CONF_AUTH_CODE])
        user_input = utils.option_text_to_parm(user_input, 'account_selected',
                                                self.apple_acct_auth_items_by_username)

        if action_item == 'auth_code_from_applecom_login':
            return 'auth_code_from_applecom_login', reauth_username, user_input, errors

        if action_item == 'change_auth_method':
            return 'change_auth_method', reauth_username, user_input, errors

        if Gb.fido2_security_keys_enabled:
            user_input = utils.option_text_to_parm(user_input, 'fido2_key_name',
                                                self.reauth_form_fido2_key_names_list)
        else:
            user_input['fido2_key_name'] = ['']

        ui_account_selected   = user_input.get('account_selected')
        ui_conf_auth_code     = user_input.get(CONF_AUTH_CODE, '')
        ui_conf_fido_key_name = user_input['fido2_key_name']
        if 'terms_of_use' not in user_input:
            user_input['terms_of_use'] = False

        log_debug_msg(  f"⭐ REAUTH HANDLER ({action_item}) > "
                        f"From-{return_to_step_id}, "
                        f"UserInput-{user_input}, Errors-{errors}")

        if (ui_account_selected is not None
                and ui_account_selected.startswith('.')):
            action_item = 'goto_previous'

        elif (ui_conf_auth_code != ''
                and len(ui_conf_auth_code) == 6
                and is_number(ui_conf_auth_code)):
            action_item = 'send_auth_code'

        elif (Gb.internet_error and action_item != 'goto_previous'):
            self.errors['base'] = 'internet_error_no_change'
            user_input = None
            return await self.async_step_reauth(
                                    user_input=user_input, errors=self.errors)

        if action_item == 'goto_previous':
            return 'goto_previous', '', None, errors

        ui_username = None
        if 'account_selected' in user_input:
            ui_username = user_input['account_selected']
            self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(ui_username)

            username = user_input[CONF_USERNAME] = self.conf_apple_acct[CONF_USERNAME]
            password = user_input[CONF_PASSWORD] = self.conf_apple_acct[CONF_PASSWORD]

        elif CONF_USERNAME in user_input:
            self.aa_idx = 0
            username = self.conf_apple_acct[CONF_USERNAME] = user_input[CONF_USERNAME]
            password = self.conf_apple_acct[CONF_PASSWORD] = user_input[CONF_PASSWORD]
        else:
            username = password = ' '

        self.apple_acct_reauth_username = username
        AppleAcct = self.AppleAcct = Gb.AppleAcct_by_username.get(username, AppleAcct)

        if (action_item != 'log_into_apple_acct'
                and AppleAcct
                and AppleAcct.login_successful is False):
            return 'refresh_screen', reauth_username, user_input, errors

        if (AppleAcct
                and AppleAcct.terms_of_use_update_needed
                and user_input['terms_of_use']):
            AppleAcct.terms_of_use_accepted = True

        if action_item == 'accept_terms_of_use':
            if (user_input['terms_of_use']
                    and AppleAcct.terms_of_use_update_needed):
                await async_finish_authentication_and_data_refresh(self)

                if AppleAcct.is_authenticated:
                    AppleAcct.terms_of_use_update_needed = False
                    post_event( f"{AppleAcct.username_base} > "
                                f"Apple Acct > Terms of Service agreement approved")
                    update_alert_sensor(AppleAcct.username_id, '')
                    self.errors['account_selected'] = 'apple_acct_terms_update_accepted'

        if (action_item == 'send_auth_code'
                and ui_conf_auth_code == ''
                and len(self.reauth_form_fido2_key_names_list) == 1):
            action_item = 'refresh_screen'

        if action_item == 'goto_previous':
            clear_AppleAcct_auth_alerts()
            self.apple_acct_reauth_username = ''
            return 'goto_previous', '', None, errors

        if (action_item == 'refresh_screen'
                or action_item is None):
            pass

        elif AppleAcct is None:
            self.errors['account_selected'] = 'auth_code_requested'

        #.......................................................................
        elif action_item == 'send_auth_code':
            if ui_conf_auth_code == '':
                return

            auth_successful = await send_auth_code_back_to_apple(self, AppleAcct, ui_conf_auth_code)

            # elif Gb.fido2_security_keys_enabled is False:
            #     valid_code = False
            #     pass

            # elif (AppleAcct.fido2_key_names is None
            #         and len(self.reauth_form_fido2_key_names_list) == 1):
            #         action_item = 'refresh_screen'

            # elif ui_conf_fido_key_name in AppleAcct.fido2_key_names:
            #         valid_code_key = await async_confirm_fido2_security_key(AppleAcct, user_input['fido2_key_name'])

            if auth_successful is False:
                self.errors[CONF_AUTH_CODE] = 'auth_code_invalid'
                return

            self.errors[CONF_AUTH_CODE] = ''
            self.errors['account_selected'] = self.header_msg = 'auth_code_accepted'
            if instr(str(self.apple_acct_auth_items_by_username), 'AUTH'):
                self.conf_apple_acct = ''
            else:
                clear_AppleAcct_auth_alerts()
                post_greenbar_msg('')
                self.apple_acct_reauth_username = reauth_username
                if len(Gb.conf_apple_accounts) <= 1:
                    return 'refresh_screen', reauth_username, None, errors

        #.......................................................................
        elif action_item.startswith('request_auth_code'):
            auth_method = self.AppleAcct.auth_method

            self.errors['account_selected'] = 'auth_code_requested'
            post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                        f"Requested a new Verification Code "
                        f"({self.AppleAcct.auth_method.title()}-"
                        f"({self.AppleAcct.auth_method_info}")

            # comment out cookie list
            # AppleAcct.iCloudSession.cookies.list()

            #REALCODE
            self.apple_acct_reauth_username = reauth_username = ui_username
            await async_request_new_auth_code(self, AppleAcct)

            # from v3.3.4.3
            # await async_v3_3_4_3_reset_session(self, username, password)

            # await async_get_fido2_key_names(AppleAcct)

            return 'send_auth_code', reauth_username, user_input, errors

        return 'refresh_screen', reauth_username, user_input, errors

    except Exception as err:
        log_exception(err)


#--------------------------------------------------------------------
async def async_send_applecom_login_auth_code(self, user_input=None, errors=None):

    AppleAcct  = self.AppleAcct
    user_input = utils.strip_spaces(user_input, [CONF_AUTH_CODE])
    ui_conf_auth_code = user_input.get(CONF_AUTH_CODE, '')

    log_debug_msg(f"⭐ {self.step_id.upper()} Handler > UserInput-{user_input}, Errors-{errors}")

    if (ui_conf_auth_code == ''
            or len(ui_conf_auth_code) != 6
            or is_number(ui_conf_auth_code) is False):
        return

    await Gb.hass.async_add_executor_job(self.AppleAcct.untrust_session_and_authenticate)
    auth_successful = await send_auth_code_back_to_apple(self, AppleAcct, ui_conf_auth_code, force_PUSH=True)

    if auth_successful is False:
        self.errors[CONF_AUTH_CODE] = 'auth_code_invalid'
        return

    self.errors[CONF_AUTH_CODE] = self.header_msg = 'auth_code_accepted'
    if instr(str(self.apple_acct_auth_items_by_username), 'AUTH'):
        self.conf_apple_acct = ''
    else:
        clear_AppleAcct_auth_alerts()
        post_greenbar_msg('')
        if len(Gb.conf_apple_accounts) <= 1:
            return 'refresh_screen', self.apple_acct_reauth_username, None, errors


#--------------------------------------------------------------------
async def async_request_new_auth_code(self, AppleAcct):
    '''
    Reset the current session and authenticate to restart pyicloud_ic3
    and enter a new verification code

    The username & password are specified in case the Apple acct is not logged
    into because of an error
    '''
    try:
        post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, Authentication Inprocess")

        if AppleAcct.is_auth_alert_displayed is False:
            AppleAcct.is_auth_alert_displayed = True

        # AppleAcct.iCloudSession.cookies.list()
        auth_method = AppleAcct.auth_method
        if auth_method not in AppleAcct.conf_apple_acct[CONF_AUTH_METHODS]:
            auth_method = AppleAcct.conf_apple_acct[CONF_AUTH_METHODS][CONF_LAST_METHOD] = PUSH

        if AppleAcct.auth_method_PUSH:
            AppleAcct.iCloudSession.cookies.list()
            await Gb.hass.async_add_executor_job(AppleAcct.untrust_session_and_authenticate)

        # Send a code via a text message
        elif AppleAcct.auth_method_TEXT:
            Gb.hass.async_add_executor_job(AppleAcct.request_auth_code_via_text_msg, auth_method)

        elif AppleAcct.auth_method_HWKEY:
            pass

        # await async_get_fido2_key_names(AppleAcct)
        # AppleAcct.auth_code = None

        AppleAcct.was_auth_code_requested = True
        post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, "
                    f"Waiting for the 6-digit Verification Code to be entered")
        alert_msg = f"Apple Authentication needed ({secs_to_hhmm(AppleAcct.is_auth_code_needed_secs)})"
        update_alert_sensor(AppleAcct.username_id, alert_msg)

    except Exception as err:
        login_err = str(err)
        log_exception(err)

#--------------------------------------------------------------------
async def send_auth_code_back_to_apple(caller_self, AppleAcct, auth_code, force_PUSH=False):
    '''
    Handle the send_authentication_code action. This is called from the ConfigFlow and OptionFlow
    reauth steps in each Flow. This provides this function with the appropriate data and return objects.

    Parameters:
        - caller_self = 'self' for OptionFlow and the _OptFlow object when calling from ConfigFlow
                        OptionFlow --> valid_code = await self.send_auth_code_back_to_apple(
                                                                self, user_input)
                        ConfigFlow --> valid_code = await _OptFlow.send_auth_code_back_to_apple(
                                                                _OptFlow, user_input)
        - user_input = user_input dictionary
    '''
    try:
        AppleAcct = caller_self.AppleAcct
        AppleAcct.was_ha_auth_code_alert_sent = False

        if AppleAcct.auth_method_PUSH or force_PUSH:
            auth_successful = await Gb.hass.async_add_executor_job(
                                    AppleAcct.validate_2fa_push_popup_window_code,
                                    auth_code)

        elif AppleAcct.auth_method_TEXT:
            auth_successful = await Gb.hass.async_add_executor_job(
                                    AppleAcct.validate_2fa_text_code,
                                    auth_code)

        # Do not restart iC3 right now if the username/password was changed on the
        # iCloud setup screen. If it was changed, another account is being logged into
        # and it will be restarted when exiting the configurator.
        if auth_successful is False:
            if auth_code != '':
                AppleAcct.was_auth_code_requested = False
                post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                            f"Verification Code invalid "
                            f"({auth_code})")
            return False

        post_event( f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.account_owner}, "
                    f"Authentication Successful")

        # Refresh the device list if the apple acct is being setup for the first time
        # If AppleAcct.device_id_by_icloud_dname is empty, a verification code was needed
        # when first logged in and the apple acct data was not authenticated and it's
        # device data was never loaded/initialized by refreshed_icloud_data. This
        # prevents the device's list tables to never be initialized and location data
        # is not available. Do this now.
        if (is_empty(AppleAcct.device_id_by_icloud_dname)
                or (AppleAcct.terms_of_use_update_needed and AppleAcct.terms_of_use_accepted)):
            await async_finish_authentication_and_data_refresh(caller_self)

        await lists.build_icloud_device_selection_list(caller_self)

        AppleAcct.was_auth_code_requested = False
        Gb.EvLog.clear_greenbar_msg()
        Gb.is_force_icloud_update = True
        update_alert_sensor(AppleAcct.username_id, '')

        return True

    except Exception as err:
        log_exception(err)

        return False

#--------------------------------------------------------------------
async def async_v3_3_4_3_reset_session(self, username, password):
    '''
    Reset the current session and authenticate to restart pyicloud_ic3
    and enter a new verification code

    The username & password are specified in case the Apple acct is not logged
    into because of an error
    '''
    try:
        AppleAcct = self.AppleAcct
        if AppleAcct:
            aa_username = AppleAcct.username or self.username

            post_event(f"{EVLOG_NOTICE}Apple Acct > {AppleAcct.username_id}, Authentication Needed")

            await async_delete_icloud_session_requests_file(aa_username)

            if AppleAcct.is_auth_alert_displayed is False:
                AppleAcct.is_auth_alert_displayed = True

            await Gb.hass.async_add_executor_job(AppleAcct.setup_new_apple_account_session)

            # Initialize AppleAcct object to force a new one that will trigger the 2fa process
            AppleAcct.verification_code = None

        # The Apple acct is not logged into. There may have been some type Of error.
        # Delete the session files for the username selected on the request form and
        # try to login
        elif username and password:
            post_event(f"{EVLOG_NOTICE}Apple Acct > {username_id(username)}, Authentication Needed")

            await async_delete_icloud_session_requests_file(username)

            user_input = {}
            user_input[CONF_USERNAME] = username
            user_input[CONF_PASSWORD] = password

            login_successful = await async_log_into_apple_account(self, user_input)

            AppleAcct = self.AppleAcct

        if AppleAcct:
            post_event( f"{EVLOG_NOTICE}Configure Apple Acct > {AppleAcct.username_id}, "
                        f"Waiting for the 6-digit Verification Code to be entered")
            return

    except AppleAcctFailedLoginException as err:
        login_err = str(err)
        login_err + ", Will retry logging into the Apple Account later"

    except Exception as err:
        login_err = str(err)
        log_exception(err)

    if instr(login_err, '-200') is False:
        if AppleAcct and AppleAcct.response_code == 503:
            Gb.AppleAcctLoggingInto.setup_error(503)
            self.errors['base'] = 'apple_acct_login_error_503'

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
async def async_delete_icloud_session_requests_file(username=None):
    '''
    Delete the cookies and session files as part of the reset_session and request_verification_code
    This is called from config_flow/setp_reauth and pyicloud_reset_session
    '''

    if username is None:
        return

    post_event(f"{EVLOG_NOTICE}Configure Apple Acct > Resetting Cookie/Session Files")
    cookie_directory  = Gb.icloud_cookies_directory
    cookie_filename   = "".join([c for c in username if match(r"\w", c)])

    delete_msg =  f"Apple Acct > Deleting Session Files > ({cookie_directory})"

    delete_msg += f"{CRLF_DOT}Session ({cookie_filename}.session)"
    await file_io.async_delete_file_with_msg(
                    'Apple Acct Session', cookie_directory, f"{cookie_filename}.session", delete_old_sv_file=True)
    # delete_msg += f"{CRLF_DOT}Token Password ({cookie_filename}.tpw)"
    # await file_io.async_delete_file_with_msg(
    #                 'Apple Acct Tokenpw', cookie_directory, f"{cookie_filename}.tpw")
    post_monitor_msg(delete_msg)
