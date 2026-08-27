
from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_DN, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS, CRLF_RED_ALERT, CRLF_RED_X,
                                    HHMMSS_ZERO, RARROW, DOT, CRLF, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                    ICLOUD, NAME, ID,
                                    APPLE_SERVER_ENDPOINT,
                                    ICLOUD_HORIZONTAL_ACCURACY,
                                    LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE, LATITUDE, LONGITUDE,
                                    ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                    BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW,
                                    ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES,
                                    CONF_AUTH_METHODS, DEFAULT_AUTH_METHODS, TEXT_1,
                                    CONF_USERNAME, CONF_APPLE_ACCOUNT,
                                    CONF_PASSWORD, CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                    CONF_FAMSHR_DEVICE_ID, CONF_LOG_LEVEL_DEVICES,
                                    )
from ..utils.utils          import (instr, yes_no, is_empty, isnot_empty, list_add, list_del, dict_del,
                                    encode_password, decode_password, username_id, is_running_in_event_loop, )
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_request_data, log_exception, log_data_unfiltered, )
from ..utils                import gps

# from .icloud_session        import iCloudSession
# from .apple_acct            import HEADERS, AppleAcctManager
from ..startup              import config_file
from .                      import apple_acct_support as aas
from .                      import icloud_requests_io  as icloud_io

#--------------------------------------------------------------------
from urllib.parse import urlparse
import socket
import errno
from uuid               import uuid1
import base64
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CHECK APPLE ACCOUNT Username-Password
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class ValidateAppleAcctUPW():
    '''
    Validation the Apple Account Username-Password
    '''

    def __init__(self):
        self.validate_aa_upw = True
        self.username = 'validate_upw'
        self.username_base = ''
        self.password = 'validate_upw'
        self.method   = ''

        self.client_id = f"auth-{str(uuid1()).lower()}"

        self.response_code      = 0

        self.AppleAcct          = None
        self.iCloudSession      = None
        self.config_flow_login  = False
        self.valid_upw_results_msg = ''

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return self.AppleAcct.username_account_owner
        except:
            return "<NotSetUp>"

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def validate_upw_all_apple_accts(self):
        '''
        Cycle through the apple accounts, Validate the Username-Password for each one.
        Do this so we know all future login attempts will be with valid apple accts
        This is run is startup Stage 3

        Update:
            - Gb.valid_upw_by_username
            - results_msg
        '''
        if (Gb.use_data_source_ICLOUD is False
                or Gb.internet_error):
            return

        cnt         = -1
        results_msg = ''
        alert_msg   = ''
        for conf_apple_acct in Gb.conf_apple_accounts:
            cnt += 1

            username     = conf_apple_acct[CONF_USERNAME]
            password     = Gb.AppleAcct_password_by_username[username]

            if is_empty(username) or is_empty(password):
                continue

            valid_upw = Gb.valid_upw_by_username.get(username, False)

            if valid_upw is False:
                valid_upw = self.validate_username_password(username, password)

            Gb.valid_upw_by_username[username] = valid_upw

            if valid_upw:
                crlf_symb = CRLF_CHK
            else:
                crlf_symb = CRLF_RED_X
                alert_msg = EVLOG_ALERT
            _username_id = username_id(username)
            results_msg += f"{crlf_symb}{_username_id}, Validated-{yes_no(valid_upw)}, {self.method}"

        self.results_msg = f"{alert_msg}Apple Acct > Verify Username/Password{results_msg}"
        post_event(self.results_msg)

        Gb.startup_lists['Gb.valid_upw_by_username'] = Gb.valid_upw_by_username


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password via TOKEN_PW, PASSWORD SRP AND FULL LOGIN
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_validate_username_password(self, username, password):
        '''
        Verify the username and password are valid using a lightweight SRP signin.
        This is used in config_flow to validate the Username-Password.

        The SRP session I/O uses the blocking `requests` library, so it is run in
        an executor to keep the event loop free.
        '''
        valid_upw = await Gb.hass.async_add_executor_job(
                                        self.validate_username_password,
                                        username, password)

        return valid_upw

#----------------------------------------------------------------------------
    def validate_username_password(self, username, password):
        '''
        Check if the username and password are still valid. Three methods are
        tried in order, from cheapest to most complete:
            0. TokenPW  -   compare the password to the one saved in the username's
                            token-pw (.tpw) file by the last successful login. A
                            match means the credentials were already validated by
                            Apple, so they are assumed valid with NO request sent.
            1. AuthSRP  -   a lightweight SRP signin (signin/init + signin/complete)
                            that verifies the credentials without a full login or
                            data refresh.
            2. Login    -   a complete login & authentication (can succeed via a
                            saved trust-token, bypassing a throttled SRP signin).

        Note: Apple deprecated the old Basic-auth 'setup/authenticate/{username}'
        url (it now always returns 401 regardless of the credentials).

        Return:
            True/False
        '''
        AppleAcct = self._create_AppleAcct_validate_upw(username, password)

        if AppleAcct is None:
            return False

        # Method-0 > TokenPW file password match (NO request sent to Apple)
        if self._validate_upw_via_tokenpw():
            return True

        # Method-1 > Lightweight SRP credential validation
        if self._validate_upw_via_srp():
            return True

        # Method-2 > Fall back to a complete login & authentication. The SRP
        # validation can fail for reasons other than an invalid password (most
        # commonly Apple throttling the signin/init with a 503), and a full
        # login may still succeed - e.g. via a saved trust-token.
        return self._validate_upw_via_full_login(username, password)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password via PASSWORD-SRP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_validate_username_password_srp(self, username, password):
        '''
        Verify the username and password are valid using a lightweight SRP signin.
        This is used in config_flow to validate the Username-Password.

        The SRP session I/O uses the blocking `requests` library, so it is run in
        an executor to keep the event loop free.
        '''
        valid_upw = await Gb.hass.async_add_executor_job(
                                        self.validate_username_password_srp,
                                        username, password)

        return valid_upw

#----------------------------------------------------------------------------
    def validate_username_password_srp(self, username, password):

        AppleAcct = self._create_AppleAcct_validate_upw(username, password)

        if AppleAcct is None:
            return False

        # Method-1 > Lightweight SRP credential validation
        if self._validate_upw_via_srp():
            return True

        return False

#----------------------------------------------------------------------------
    def _create_AppleAcct_validate_upw(self, username, password):
        self.username = username
        self.password = password
        self.username_id = self.username_base = username_id(self.username)

        self.method = ''
        try:
            if self.AppleAcct:
                self.AppleAcct.__init__(
                                            username,
                                            password,
                                            apple_server_location='usa',
                                            locate_all_devices=False,
                                            cookie_directory=Gb.icloud_cookies_directory,
                                            session_directory=Gb.icloud_session_directory,
                                            srp_validate_only=True,
                                            validate_aa_upw=True)
            else:
                self.AppleAcct = aas.create_AppleAcct_validate_upw(username, password)

            if self.AppleAcct:
                self.iCloudSession = self.AppleAcct.iCloudSession
                return self.AppleAcct

        except Exception as err:
            log_exception(err)
            log_error_msg(f"iCloud3 Error > Error setting up Apple Account I/O handler, "
                            f"Password could not be validated, Error-{err}")

            self.method = 'Apple Acct Unavailable'
            return None


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATION FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _validate_upw_via_tokenpw(self):
        '''
        Method-0 > Validate the Username-Password against the password saved in
        the username's token-pw (.tpw) file. That password was stored by the last
        successful login and read/decoded into the AppleAcct's token_pw_data when
        the validate-only session was set up (read_token_pw_file). If the current
        password matches it, the credentials were already validated by Apple and
        are assumed valid - no request is sent to Apple.

        Return:
            True  - current password matches the saved (previously validated) one
            False - no match, no .tpw file, or the file has no saved password
        '''
        self.method = 'TokenFilePW'

        try:
            # token_pw_data holds the decoded-on-read .tpw contents. The saved
            # 'password' item is only present when a .tpw file existed for the
            # username, so its absence means there is nothing to match against.
            token_pw_data = self.AppleAcct.token_pw_data
            if is_empty(token_pw_data) or CONF_PASSWORD not in token_pw_data:
                return False

            tpw_password = decode_password(token_pw_data[CONF_PASSWORD])
            valid_upw = (tpw_password == self.AppleAcct.password)

        except Exception as err:
            log_exception(err)
            return False

        log_debug_msg(f"TokenPW Results > {self.username_base}, Method-{self.method}, Results-{valid_upw}")

        return valid_upw

#----------------------------------------------------------------------------
    def _validate_upw_via_srp(self):
        '''
        Method-1 > Validate the Username-Password using the validate-only
        AppleAcct/session by running only the SRP signin/init+complete exchange
        (no full login, no device data refresh).
        '''
        self.method = 'AuthSRP'

        # No session hygiene is needed here. The validate-only AppleAcct holds a
        # transient cookie jar and carries no signin session identifiers in from
        # the session file, so its signin/init always opens a session Apple has
        # never seen and nothing it does is visible to the real AppleAcct for
        # this username (see AppleAcctManager._setup_iCloudSession).

        # The AppleAcct already holds the decoded password, so no args are passed.
        valid_upw = self.AppleAcct.validate_upw_via_srp()

        log_debug_msg(  f"PasswordSRP Results > {self.username_base}, Method-{self.method}, "
                        f"Results-{valid_upw} (Response-{self.AppleAcct.response_code})")

        if valid_upw is False:
            return False

        self._save_srp_signin_token_info()

        conf_apple_acct, aa_idx = config_file.conf_apple_acct(self.username)
        conf_auth_methods = conf_apple_acct[CONF_AUTH_METHODS]
        #if conf_auth_methods == DEFAULT_AUTH_METHODS:
        self._update_trusted_device_auth_method(conf_apple_acct, aa_idx)

        return valid_upw

#----------------------------------------------------------------------------
    def _update_trusted_device_auth_method(self, conf_apple_acct, aa_idx):
        '''
        The trusted device info (text sms phone numbers and hwkey names) is only available
        when the srp validates the password. If the current auth_methods for this account
        are the default values (which it will be on an acct that was just added), get the
        trusted device info and update the auth methods because we can do it now.
        '''
        AppleAcct = self.AppleAcct
        AppleAcct.login_successful_srp = True
        AppleAcct.conf_apple_acct = conf_apple_acct
        AppleAcct.aa_idx          = aa_idx

        AppleAcct.get_trusted_devices()

        if aa_idx > 0 and AppleAcct.auth_method_value(TEXT_1) != '':
            AppleAcct.update_auth_method(TEXT_1)

        Gb.conf_apple_accounts[aa_idx] = AppleAcct.conf_apple_acct

#----------------------------------------------------------------------------
    def _save_srp_signin_token_info(self):
        '''
        Keep the signin session token this validation just earned so the login
        that follows can adopt it (AppleAcctManager._use_srp_signin_token_info).

        Apple returns an X-Apple-Session-Token alongside the 409 (credentials
        valid, 2FA required) and iCloud3 captures it into session_data. Without
        this handoff the login runs its own full SRP a second later, posting a
        SECOND M1 password proof to signin/complete - which Apple refuses with a
        503. Handing the token over lets the login go straight to accountLogin.

        Only the session token and account country are kept. session_id and scnt
        identify the validation's idmsa signin session and must NOT be reused -
        that is the collision clear_srp_signin_session exists to prevent.
        '''
        try:
            session_data  = self.AppleAcct.session_data
            session_token = session_data.get('session_token')

            if is_empty(session_token):
                return

            Gb.srp_token_info_by_username[self.AppleAcct.username] = {
                        'session_token':    session_token,
                        'account_country':  session_data.get('account_country'),
                        'secs':             time_now_secs(), }

            log_debug_msg(  f"{self.username_base}, Saved the SRP Signin Session Token "
                            f"for the login that follows")

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _validate_upw_via_full_login(self, username, password):
        '''
        Method-2 > Validate the Username-Password by setting up the AppleAcct
        manager & session and doing a complete login/authentication and data
        refresh. This can authenticate via a saved trust-token, bypassing the
        SRP signin endpoint when it is being throttled (503).
        '''
        self.method = 'Login/Authenticate'
        try:
            self.AppleAcct = Gb.AppleAcct_by_username.get(username)
            if self.AppleAcct is None:
                self.AppleAcct = aas.create_AppleAcct(  username, password,
                                                        apple_server_location='usa',
                                                        locate_all_devices=True)
                if self.AppleAcct is None:
                    # create_AppleAcct posts its own alert (internet error, etc.)
                    self.method = 'Apple Acct Unavailable'
                    return False

                self.iCloudSession = self.AppleAcct.iCloudSession

            else:
                self.AppleAcct.__init__(username, password, validate_aa_upw=False)

        except Exception as err:
            log_exception(err)
            log_error_msg(f"iCloud3 Error > Error setting up Apple Account I/O handler, "
                            f"Password could not be validated, Error-{err}")
            return False

        log_debug_msg(  f"Full Login Results > {self.username_base}, Method-{self.method}, "
                        f"Results-{self.AppleAcct.login_successful}")

        if self.AppleAcct.login_successful:
            return True

        # Both the SRP check and the full login failed - Username-Password invalid
        self.method = 'Invalid Username-Password'
        self.AppleAcct.setup_error(401)

        return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"

#............................................................................
    def delete_password_from_token_pw(self):

        dict_del(self.AppleAcct.token_pw_data, CONF_PASSWORD)
        try:
            file_io.save_json_file(self.AppleAcct.tokenpw_filename, self.AppleAcct.token_pw_data)

        except Exception as err:
            log_exception(err)
            log_warning_msg(f"Apple Acct > {self.AppleAcct.account_owner}, "
                            f"Failed to update tokenpw file {self.AppleAcct.tokenpw_filename}")
