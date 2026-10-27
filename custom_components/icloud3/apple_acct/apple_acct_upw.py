
from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_DN, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT,
                                    HHMMSS_ZERO,
                                    ICLOUD, NAME, ID,
                                    APPLE_SERVER_ENDPOINT,
                                    ICLOUD_HORIZONTAL_ACCURACY,
                                    LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE, LATITUDE, LONGITUDE,
                                    ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                    BATTERY_LEVEL, BATTERY_LEVEL_LOW,
                                    ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES, )
from ..const_config         import (BATTERY_STATUS, CONF_AUTH_METHODS, DEFAULT_AUTH_METHODS,
                                    TEXT_1, CONF_APPLE_ACCT, CONF_APPLE_ACCT, CONF_PASSWORD,
                                    CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL, CONF_IC3_DEVICENAME,
                                    CONF_FNAME, CONF_AADEV_NAME, CONF_AADEV_DEVICE_ID,
                                    CONF_LOG_LEVEL_DEVICES, )
from ..const_char           import (LINK, RLINK, LLINK, DOTS, RARROW, DOT, CRLF, CRLF_DOT,
                                    CRLF_STAR, CRLF_CHK, CRLF_HDOT, CRLF_CIRCLE_X, CRLF_RED_ALERT,
                                    CRLF_RED_X, )
from ..utils.utils          import (instr, yes_no, is_empty, isnot_empty, list_add, list_del, dict_del,
                                    encode_password, decode_password, apple_user, is_running_in_event_loop, )
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_exception, alert_key_for, post_config_error,
                                    update_alert_sensor, )
from ..utils                import gps

# from .icloud_session        import iCloudSession
# from .apple_acct            import HEADERS, AppleAcctManager
from ..startup              import config_file
from ..support              import test_controls as TEST
from .                      import apple_acct_support as aas
from .                      import icloud_requests_io as icloud_io

#--------------------------------------------------------------------
from urllib.parse import urlparse
import socket
import errno
from uuid               import uuid1
import base64
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

APPLE_ACCT_INVALID_USERNAME_PASSWORD_CODES = [401, 401.1, 403, 421.1, 423, 503]

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CHECK APPLE ACCOUNT Username-Password
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''

In Stage 3, Gb.ValidateAppleAcctUPW,validate_upw_all_apple_accts() runs at start_ic3_control.py:184, and Stage 4 only shows the result again (line 225). Moving startup into its own thread hasn't made that check unnecessary. What it changed is the cost: the check used to slow HA's startup, and now it doesn't. I'd keep it where it is.

Why it's still needed

Stage 3 depends on the result. create_Devices_object → _display_stage3_event_log_device_info at start_ic3.py:1331 checks apple_id not in Gb.upw_valid_by_apple_id to decide when to post the "Unknown Apple Acct" repair. Line 1352 uses it to set ERR_USERNAME_PW. Without the Stage 3 check that dict would be empty, so every iCloud device would get an "Unknown Apple Acct" repair issue and the wrong status in the Event Log.
It keeps Stage 4 from logging in with a bad password. Gb.conf_apple_ids (line 231) only includes accounts that were checked. log_into_apple_accounts (start_ic3.py:1483) skips any account that failed with 401/403/423/503. That way Apple isn't hit with a full login on a bad password, which risks locking the account or getting throttled.
Users hear about a bad password sooner. On a cold start, Stage 4 can wait for HA to finish starting (run_startup_stages_4_6_after_ha_started), which can take minutes on a Pi. Stage 3 runs right away, so the "Invalid Username/Password" alert shows up early.
Why it costs almost nothing

On a normal restart, Method 0 (comparing against the saved password in the .tpw file) succeeds and no request goes to Apple. The SRP handshake only runs after a password change or on a new install.
On a reload, accounts already marked valid are skipped (if upw_valid is False: at apple_acct_upw.py:120).
The check now runs in the background task, so it no longer holds up HA's startup. That was the only real argument against doing it early.
One thing to be aware of (not a bug)

The session token from the check is only handed to the login if the login starts within SRP_SIGNIN_TOKEN_INFO_MAX_AGE_SECS = 60 (apple_acct.py:71). On a reload, Stages 1–3 and 4–6 run back to back, so the login picks up the token. On a cold start where Stage 4 waits for HA, the gap can be over 60s. The token is then thrown away and the login does its own signin/complete. That's safe: from the earlier 503 investigation, a token-less signin/complete about 30s or more after the check doesn't get a 503. The 503 only happens when the two are seconds apart, and the token handoff covers that case. This only matters when an SRP request was actually sent, i.e. after a password change or on a new install.
'''


class ValidateAppleAcctUPW():
    '''
    Validation the Apple Account Username-Password
    '''

    def __init__(self):
        self.validate_aa_upw = True
        self.apple_id = 'validate_upw'
        self.apple_user = ''
        self.password = 'validate_upw'
        self.method   = ''

        self.client_id = f"auth-{str(uuid1()).lower()}"

        self.response_code      = 0

        self.AppleAcct          = None
        self.iCloudSession      = None
        self.config_flow_login  = False

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return self.AppleAcct.apple_id_account_owner
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
            - Gb.upw_valid_by_apple_id
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

            apple_id     = conf_apple_acct[CONF_APPLE_ACCT]
            password     = Gb.AppleAcct_password_by_apple_id[apple_id]
            _apple_user = apple_user(apple_id)

            if is_empty(apple_id) or is_empty(password):
                continue

            upw_valid = Gb.upw_valid_by_apple_id.get(apple_id, False)

            if upw_valid is False:
                upw_valid = self.validate_apple_id_password(apple_id, password)

            Gb.upw_valid_by_apple_id[apple_id] = upw_valid
            Gb.upw_code_by_apple_id[apple_id]  = self.response_code

            if upw_valid:
                crlf_symb = CRLF_CHK
            else:
                crlf_symb = CRLF_CIRCLE_X
                alert_msg = EVLOG_ALERT

                if self.response_code == 503:
                    reason_msg = "Apple Refused the Signin Request, Try again later"
                else:
                    reason_msg = "Invalid Username/Password"
                error_msg =(f"{_apple_user} > Verification Failed, "
                            f"{reason_msg} ({self.response_code})")
                post_alert( f"{error_msg}")
                update_alert_sensor(Source=apple_id, name=_apple_user, error='verif_failed', alert_msg=error_msg)

            results_msg += f"{crlf_symb}{_apple_user}, Valid-{yes_no(upw_valid)}, {self.method}"

        self.results_msg = f"Apple Acct > Verify Username/Password{results_msg}"
        post_event(self.results_msg)

        Gb.startup_lists['Gb.upw_valid_by_apple_id'] = Gb.upw_valid_by_apple_id
        Gb.startup_lists['Gb.upw_code_by_apple_id']  = Gb.upw_code_by_apple_id


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password via TOKEN_PW, PASSWORD SRP AND FULL LOGIN
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_validate_apple_id_password(self, apple_id, password):
        '''
        Verify the apple_id and password are valid using a lightweight SRP signin.
        This is used in config_flow to validate the Username-Password.

        The SRP session I/O uses the blocking `requests` library, so it is run in
        an executor to keep the event loop free.
        '''
        upw_valid = await Gb.hass.async_add_executor_job(
                                        self.validate_apple_id_password,
                                        apple_id, password)

        return upw_valid

#----------------------------------------------------------------------------
    def validate_apple_id_password(self, apple_id, password):
        '''
        Check if the apple_id and password are still valid. Three methods are
        tried in order, from cheapest to most complete:
            0. TokenPW  -   compare the password to the one saved in the apple_id's
                            token-pw (.tpw) file by the last successful login. A
                            match means the credentials were already validated by
                            Apple, so they are assumed valid with NO request sent.
            1. AuthSRP  -   a lightweight SRP signin (signin/init + signin/complete)
                            that verifies the credentials without a full login or
                            data refresh.
            2. Login    -   a complete login & authentication (can succeed via a
                            saved trust-token, bypassing a throttled SRP signin).

        Note: Apple deprecated the old Basic-auth 'setup/authenticate/{apple_id}'
        url (it now always returns 401 regardless of the credentials).

        Return:
            True/False
        '''
        self.AppleAcct = self._create_AppleAcct_validate_upw(apple_id, password)

        if self.AppleAcct is None:
            return False

        # Method-0 > TokenPW file password match (NO request sent to Apple)
        if self._validate_upw_via_tokenpw():
            return True

        # Method-1 > Lightweight SRP credential validation
        if self._validate_upw_via_srp():
            return True

        # Apple answered the SRP check (4xx) or throttled it (503), don't do a full
        # login. It authenticates with the saved session/trust tokens first, which do
        # not check the password, so a wrong password would be reported as valid. If
        # the tokens fail, it sends another password proof toward Apple's lockout.
        if self._is_apple_credentials_answer(self.AppleAcct.response_code):
            return False

        # Method-2 > Fall back to a complete login & authentication. This is only
        # done when Apple did not answer the SRP check (no response, connection
        # error, SRP setup failed, server error).
        return self._validate_upw_via_full_login(apple_id, password)

#----------------------------------------------------------------------------
    @staticmethod
    def _is_apple_credentials_answer(response_code):
        '''
        Return True if the SRP check's response code is Apple's answer on the
        apple_id/password (4xx, or one of APPLE_ACCT_INVALID_USERNAME_PASSWORD_CODES)
        or the PasswordSRP throttle (503).
        Return False if Apple did not answer (0/None, -2/-3/-4, 3xx, other 5xx).
        '''
        if response_code in APPLE_ACCT_INVALID_USERNAME_PASSWORD_CODES:
            return True

        try:
            return 400 <= int(response_code) < 500

        except (TypeError, ValueError):
            return False


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password via PASSWORD-SRP
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_validate_apple_id_password_srp(self, apple_id, password):
        '''
        Verify the apple_id and password are valid using a lightweight SRP signin.
        This is used in config_flow to validate the Username-Password.

        The SRP session I/O uses the blocking `requests` library, so it is run in
        an executor to keep the event loop free.
        '''
        upw_valid = await Gb.hass.async_add_executor_job(
                                        self.validate_apple_id_password_srp,
                                        apple_id, password)

        return upw_valid

#----------------------------------------------------------------------------
    def validate_apple_id_password_srp(self, apple_id, password):

        self.AppleAcct = self._create_AppleAcct_validate_upw(apple_id, password)

        if self.AppleAcct is None:
            return False

        # Method-1 > Lightweight SRP credential validation
        if self._validate_upw_via_srp():
            return True

        return False

#----------------------------------------------------------------------------
    def apple_id_exists(self, apple_id):
        '''
        Check if the apple_id is an Apple Account without its password using the
        validate-only AppleAcct (it does not create or change the apple_id's session
        files). See AppleAcct.apple_id_exists_via_srp_init.

        Return:
            True  - The apple_id exists
            False - The apple_id does not exist
            None  - Unknown
        '''
        self.AppleAcct = self._create_AppleAcct_validate_upw(apple_id, 'apple_id_exists_check')

        if self.AppleAcct is None:
            return None

        apple_id_exists = self.AppleAcct.apple_id_exists_via_srp_init()
        self.response_code = self.AppleAcct.response_code

        log_debug_msg(  f"Apple Acct Exists Check > {self.apple_user}, "
                        f"Exists-{apple_id_exists} (Response-{self.response_code})")

        return apple_id_exists

#----------------------------------------------------------------------------
    def _create_AppleAcct_validate_upw(self, apple_id, password):
        self.apple_id = apple_id
        self.password = password
        self.apple_user = self.apple_user = apple_user(self.apple_id)

        self.method = ''
        try:
            if self.AppleAcct:
                self.AppleAcct.__init__(
                                            apple_id,
                                            password,
                                            apple_server_location='usa',
                                            locate_all_devices=False,
                                            cookie_directory=Gb.icloud_cookies_directory,
                                            session_directory=Gb.icloud_session_directory,
                                            srp_validate_only=True,
                                            validate_aa_upw=True)
            else:
                self.AppleAcct = aas.create_AppleAcct_validate_upw(apple_id, password)

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
        the apple_id's token-pw (.tpw) file. That password was stored by the last
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
            # apple_id, so its absence means there is nothing to match against.
            token_pw_data = self.AppleAcct.token_pw_data
            if (is_empty(token_pw_data)
                    or 'dsid' not in token_pw_data
                    or CONF_PASSWORD not in token_pw_data):

                return False

            tpw_password = decode_password(token_pw_data[CONF_PASSWORD])
            upw_valid = (tpw_password == self.AppleAcct.password)

        except Exception as err:
            log_exception(err)
            return False

        log_debug_msg(f"TokenPW Results > {self.apple_user}, Method-{self.method}, Results-{upw_valid}")

        return upw_valid

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
        # this apple_id (see AppleAcctManager._setup_iCloudSession).

        # The AppleAcct already holds the decoded password, so no args are passed.
        if self.AppleAcct.apple_user in TEST.UPW_VIA_SRP_CHECK_INVALID:
            upw_valid = False
            # AppleAcct.response_code is a read-only property of iCloudSession.response_code
            self.AppleAcct.iCloudSession.response_code = 401
        else:
            upw_valid = self.AppleAcct.validate_upw_via_srp()

        self.response_code = self.AppleAcct.response_code

        # A 503 on the srp signin/init means the apple_id is invalid, change it to 401.1.
        # A 503 on signin/complete is Apple refusing (throttling) the signin, the
        # apple_id/password may be valid, keep the 503.
        error_msg = ''
        if (self.response_code == 503
                and getattr(self.AppleAcct, 'srp_signin_init_503', False)):
            self.response_code = 401.1

        if self.response_code in [401, 401.1]:
            error_msg = ', Invalid apple_id'
        elif self.response_code == 503:
            error_msg = ', Apple Refused the Signin Request'
        log_debug_msg(  f"PasswordSRP Results > {self.apple_user}, Method-{self.method}, "
                        f"Valid-{upw_valid}{error_msg} (Response-{self.AppleAcct.response_code})")

        if upw_valid is False:
            return False

        self._save_srp_signin_token_info()

        conf_apple_acct, aa_idx = config_file.conf_apple_acct(self.apple_id)
        conf_auth_methods = conf_apple_acct[CONF_AUTH_METHODS]

        self._update_trusted_device_auth_method(conf_apple_acct, aa_idx)

        return upw_valid

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

        # The apple_id is not in the config (-1), there is no acct to update
        if aa_idx >= 0:
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

            Gb.srp_token_info_by_apple_id[self.AppleAcct.apple_id] = {
                        'session_token':    session_token,
                        'account_country':  session_data.get('account_country'),
                        'secs':             time_now_secs(), }

            log_debug_msg(  f"{self.apple_user}, Saved the SRP Signin Session Token "
                            f"for the login that follows")

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _validate_upw_via_full_login(self, apple_id, password):
        '''
        Method-2 > Validate the Username-Password by setting up the AppleAcct
        manager & session and doing a complete login/authentication and data
        refresh. This can authenticate via a saved trust-token, bypassing the
        SRP signin endpoint when it is being throttled (503).
        '''
        self.method = 'Login/Authenticate'
        try:
            self.AppleAcct = Gb.AppleAcct_by_apple_id.get(apple_id)
            if self.AppleAcct is None:
                self.AppleAcct = aas.create_AppleAcct(  apple_id, password,
                                                        apple_server_location='usa',
                                                        locate_all_devices=True)
                if self.AppleAcct is None:
                    # create_AppleAcct posts its own alert (internet error, etc.)
                    self.method = 'Apple Acct Unavailable'
                    return False

                self.iCloudSession = self.AppleAcct.iCloudSession

            else:
                self.AppleAcct.__init__(apple_id, password, validate_aa_upw=False)

        except Exception as err:
            log_exception(err)
            log_error_msg(f"iCloud3 Error > Error setting up Apple Account I/O handler, "
                            f"Password could not be validated, Error-{err}")
            return False

        log_debug_msg(  f"Full Login Results > {self.apple_user}, Method-{self.method}, "
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
