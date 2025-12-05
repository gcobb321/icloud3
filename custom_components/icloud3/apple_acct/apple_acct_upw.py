
from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_FNAME, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS, CRLF_RED_ALERT, CRLF_RED_X,
                                    HHMMSS_ZERO, RARROW, DOT, CRLF, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                    ICLOUD, NAME, ID,
                                    APPLE_SERVER_ENDPOINT,
                                    ICLOUD_HORIZONTAL_ACCURACY,
                                    LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE, LATITUDE, LONGITUDE,
                                    ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                    BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW,
                                    ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES,
                                    CONF_USERNAME, CONF_APPLE_ACCOUNT,
                                    CONF_PASSWORD, CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                    CONF_FAMSHR_DEVICE_ID, CONF_LOG_LEVEL_DEVICES,
                                    )
from ..utils.utils          import (instr, yes_no, is_empty, isnot_empty, list_add, list_del,
                                    encode_password, decode_password, username_id, is_running_in_event_loop, )
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_request_data, log_exception, log_data_unfiltered, )
from ..utils                import gps

from .icloud_session        import iCloudSession
from .apple_acct            import HEADERS, AppleAcctManager
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
        self.password = 'validate_upw'
        self.method   = ''

        self.client_id = f"auth-{str(uuid1()).lower()}"

        self.response_code      = 0

        self.AppleAcct          = None
        self.iCloudSession      = None
        self.config_flow_login  = False
        self.valid_upw_results_msg = ''

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

            _username_id = username_id(username)

            valid_upw = self.validate_username_password(username, password)

            Gb.valid_upw_by_username[username] = valid_upw

            if valid_upw:
                crlf_symb = CRLF_CHK
            else:
                crlf_symb = CRLF_RED_X
                alert_msg = EVLOG_ALERT
            results_msg += f"{crlf_symb}{_username_id}, Validated-{yes_no(valid_upw)}, {self.method}"

        self.results_msg = f"{alert_msg}Apple Acct > Verify Username/Password{results_msg}"
        post_event(self.results_msg)

        Gb.startup_lists['Gb.valid_upw_by_username'] = Gb.valid_upw_by_username

#----------------------------------------------------------------------------
    def validate_username_password(self, username, password):
        '''
        Check if the username and password are still valid. Check using the following methods:
            - URL (Response-409 is valid, 401- is invalid)
            - AppleAcct Authenticate
        '''
        self.username = username
        self.password = password
        self.username_id = self.username_base = username_id(self.username)

        # Validate the Username-Password using the 'auth_url/usernameurl endpoint
        self.method = 'AuthURL'
        valid_upw = self.validate_upw_via_auth_url(username, password)

        #TESTCODE
        # valid_upw = False

        log_debug_msg(f"{self.username_base}, Method-{self.method}, Results-{valid_upw}")
        if valid_upw:
            return valid_upw

        # Validate the Username-Password by setting up the AppleAcct manager & session
        # for the Username-Password and doing a full authentication and data refresh
        try:
            self.AppleAcct = Gb.AppleAcct_by_username.get(username)
            if self.AppleAcct is None:

                self.AppleAcct = aas.create_AppleAcct(  username, password,
                                                        apple_server_location='usa',
                                                        locate_all_devices=True)


                self.iCloudSession = self.AppleAcct.iCloudSession

            else:
                self.AppleAcct.__init__(username, password, validate_aa_upw=False)

        except Exception as err:
            log_exception(err)
            log_error_msg(f"iCloud3 Error > Error setting up Apple Account I/O handler, "
                            f"Password could not be validated, Error-{err}")
            return False

        log_debug_msg(f"{self.username_base}, Validate Username-Password")

        self.method = 'Login/Authenticate'
        log_debug_msg(  f"{self.username_base}, Method-{self.method}, "
                        f"Results-{self.AppleAcct.login_successful}")
        if self.AppleAcct.login_successful:
            return True

        # Authentication failed, do some cleanup
        self.method = 'Invalid Username-Password'
        self.AppleAcct.setup_error(401)

        return False

#............................................................................
    def _validate_via_authenticate(self, username, password):

        valid_upw = self.AppleAcct.authenticate()

        return valid_upw

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE Username-Password WITH SINGLE URL CALL
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def validate_upw_via_auth_url(self, username, password):
        '''
        Verify the username and password are valid using the apple auth-url

        Return:
            True/False
        '''
        url, headers = self._validate_upw_setup_url_headers(username, password)

        log_request_data('Request HTTPX', 'Get', url, headers, username_id(username))

        data = icloud_io.request(url, headers=headers)

        valid_upw = self._validate_upw_check_results(data, username)

        log_request_data('Response HTTPX', 'Get', url, data, username_id(username))

        return valid_upw

#............................................................................
    async def async_validate_upw_via_auth_url_httpx(self, username, password):
        '''
        Verify the username and password are valid using the apple auth-url via an httpx request

        Return:
            True/False
        '''
        url, headers = self._validate_upw_setup_url_headers(username, password, 'HTTPX')

        log_request_data('Request HTTPX', 'Get', url, headers, username_id(username))

        data = await icloud_io.async_httpx_request(url, headers=headers)

        log_request_data('Response HTTPX', 'Get', url, data, username_id(username))

        valid_upw = self._validate_upw_check_results(data, username, 'HTTPX')

        return valid_upw

#............................................................................
    def _validate_upw_setup_url_headers(self, username, password, httpx_msg=''):
        '''
        Prepare the url and headers for the request_io or https_io call to validate the
        username and password
        '''
        username_password_b64 = self.b64encode_username_passsword(username, password)
        url     = f"{APPLE_SERVER_ENDPOINT['auth_url']}/{username}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Apple-iCloud/9.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko)',
            'Authorization': f"Basic {username_password_b64}"}

        return url, headers

#............................................................................
    def _validate_upw_check_results(self, data, username, httpx_msg=''):
        '''
        Check to see if ups is valid or not vbalid
        '''
        Gb.internet_error = data.get('error', '').startswith('InternetError')

        valid_upw = True if data['code'] == 409 else False

        return valid_upw

#----------------------------------------------------------------------------
    async def async_validate_username_password(self, username, password):
        '''
        Verify the username and password are valid using the apple auth-url via an httpx request
        This is used in config_flow to validate the Username-Password
        '''
        valid_upw = \
            await self.async_validate_upw_via_auth_url_httpx(username, password)
        if valid_upw:
            return

        valid_upw = await Gb.hass.async_add_executor_job(
                                        self.validate_username_password,
                                        username,
                                        password)

        return valid_upw


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"

#............................................................................
    def b64encode_username_passsword(self, username, password):
        '''
        Return the b64 encoded the password used for url password validation
        '''
        username_password = f"{username}:{password}"
        upw = username_password.encode('ascii')
        username_password_b64 = base64.b64encode(upw)
        username_password_b64 = username_password_b64.decode('ascii')

        return username_password_b64
