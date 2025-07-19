
from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_FNAME, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS, CRLF_RED_ALERT,
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
from ..utils.utils          import (instr, is_empty, isnot_empty, list_add, list_del,
                                    encode_password, decode_password, username_id, )
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_monitor_msg, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_data, log_exception, log_data_unfiltered, filter_data_dict, )
from ..utils                import gps

from .pyicloud_session      import PyiCloudSession
from .pyicloud_ic3          import PyiCloudManager

#--------------------------------------------------------------------
from uuid               import uuid1
import base64
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CHECK APPLE ACCOUNT USERNAME/PASSWORD
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class ValidateAppleAcctUPW():
    '''
    Validation the Apple Account Username/Password
    '''

    def __init__(self):
        self.validate_aa_upw = True
        self.username = 'validate_upw'
        self.password = 'validate_upw'
        self.method   = ''


        self.client_id = f"auth-{str(uuid1()).lower()}"

        self.response_code      = 0
        self.last_response_code = 0

        self.PyiCloudSession = None
        self.PyiCloud = None

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE USING HTTPX REQUEST
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    async def async_validate_all_apple_accts_upw_httpx(self):
        '''
        Cycle through the apple accounts, Validate the username/password for each one.
        This is done when iCloud3 starts in __init__

        Update:
            - Gb.username_valid_by_username
        '''
        results_msg = ''
        cnt = -1
        alert_symb = ''
        for conf_apple_acct in Gb.conf_apple_accounts:
            cnt += 1

            username     = conf_apple_acct[CONF_USERNAME]
            _username_id = username_id(username)
            password     = Gb.PyiCloud_password_by_username[username]
            self.method  = 'URL/httpx'

            if is_empty(username) or is_empty(password):
                continue

            if Gb.username_valid_by_username.get(username, False):
                results_msg += f"{CRLF_CHK}{_username_id}, Valid-True"
                continue

            try:
                valid_upw = await self.async_validate_username_password_via_url_httpx(username, password)
            except Exception as err:
                log_exception(err)

            Gb.username_valid_by_username[username] = valid_upw

            crlf_symb = CRLF_CHK if valid_upw else CRLF_RED_ALERT
            results_msg += f"{crlf_symb}{_username_id}, Valid-{valid_upw}, Method-URL/httpx"

        post_event(f"{alert_symb}Verify Apple Account Username/Password{results_msg}")

        Gb.startup_lists['Gb.username_valid_by_username'] = Gb.username_valid_by_username


#----------------------------------------------------------------------------
    async def async_validate_username_password_via_url_httpx(self, username, password):
        '''
        Verify the username and password are valid using the apple auth-url via an httpx request

        Return:
            True/False
        '''
        username_password_b64 = self.b64encode_username_passsword(username,password)
        url     = f"{APPLE_SERVER_ENDPOINT['auth_url']}/{username}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Apple-iCloud/9.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko)',
            'Authorization': f"Basic {username_password_b64}"}

        _hdr = ( f"{username_id(username)}, HTTPX-REQUEST, VALIDATE USERNAME/PASSWORD VIA HTTPX ▲")
        _data = {'url': url[8:], 'headers': headers}
        log_data_unfiltered(_hdr, _data)


        data = await file_io.async_httpx_request_url_data(url, headers)


        _hdr = ( f"{username_id(username)}, HTTPX-RESPONSE, VALIDATE USERNAME/PASSWORD VIA HTTPX ▼")
        _data = {'data': data}
        log_data_unfiltered(_hdr, _data)

        Gb.internet_error = data.get('error', '').startswith('InternetError')

        valid_upw = True if data['status_code'] == 409 else False

        return valid_upw

#----------------------------------------------------------------------------
    async def async_validate_username_password(self, username, password):
        '''
        Verify the username and password are valid using the apple auth-url via an httpx request
        '''
        valid_upw = \
            await self.async_validate_username_password_via_url_httpx(username, password)
        if valid_upw:
            return

        valid_upw = await Gb.hass.async_add_executor_job(
                                        Gb.ValidateAppleAcctUPW.validate_username_password,
                                        username,
                                        password)

        return valid_upw

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   VALIDATE USING PYICLOUD
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def validate_all_apple_accts_upw(self):
        '''
        Cycle through the apple accounts, Validate the username/password for each one
        This is run is startup Stage 3

        Update:
            - Gb.username_valid_by_username
        '''
        results_msg = ''
        cnt = -1
        alert_symb = ''
        for conf_apple_acct in Gb.conf_apple_accounts:
            cnt += 1

            username     = conf_apple_acct[CONF_USERNAME]
            _username_id = username_id(username)
            password     = Gb.PyiCloud_password_by_username[username]

            if is_empty(username) or is_empty(password):
                continue

            if Gb.username_valid_by_username.get(username, False):
                results_msg += f"{CRLF_CHK}{_username_id}, Valid-True"
                continue

            # Validate username/password so we know all future login attempts will be with valid apple accts
            valid_upw = self.validate_username_password(username, password)

            Gb.username_valid_by_username[username] = valid_upw

            crlf_symb = CRLF_CHK if valid_upw else CRLF_RED_ALERT
            results_msg += f"{crlf_symb}{_username_id}, Valid-{valid_upw}, Method-{self.method}"

            log_debug_msg(  f"{_username_id}, Validate Username/Password, "
                            f" Valid-{valid_upw}, Method-{self.method}")

        post_event(f"{alert_symb}Verify Apple Account Username/Password{results_msg}")

        Gb.startup_lists['Gb.username_valid_by_username'] = Gb.username_valid_by_username

#----------------------------------------------------------------------------
    def validate_username_password(self, username, password):
        '''
        Check if the username and password are still valid. Check using the following methods:
            - URL (Response-409 is valid, 401- is invalid)
            - PyiCloud Authenticate
        '''
        self.username = username
        self.password = password
        self.username_id = self.username_base = username_id(self.username)

        self.session_data  = ''      #Dummy statement for PyiCloudSession
        self.session_id    = ''      #Dummy statement for PyiCloudSession
        self.instance      = ''      #Dummy statement for PyiCloudSession

        if self.PyiCloudSession is None:
            self.PyiCloudSession = PyiCloudSession(self, validate_aa_upw=True)
            self.PyiCloud        = PyiCloudManager(username, password,
                                                    apple_server_location='usa',
                                                    validate_aa_upw=True)
        else:
            self.PyiCloud.__init__(username, password, validate_aa_upw=True)

        log_debug_msg(f"{self.username_base}, Validate Username/Password")
        aa_cookie_files_exist = file_io.file_exists(self.PyiCloud.cookie_dir_filename)

        self.method = 'URL'
        valid_upw = self.validate_username_password_via_url_pyisession(username, password)
        log_debug_msg(f"{self.username_base}, Method-{self.method}, Results-{valid_upw}")
        if valid_upw:
            return valid_upw

        self.method = 'Authenticate'
        valid_upw = self.validate_with_authenticate(username, password)
        log_debug_msg(f"{self.username_base}, Method-{self.method}, Results-{valid_upw}")
        if valid_upw:
            return valid_upw

        self.method = 'Failed'
        if aa_cookie_files_exist is False:
            file_io.delete_file(self.PyiCloud.cookie_dir_filename)
            file_io.delete_file(self.PyiCloud.session_dir_filename)

        return valid_upw

#----------------------------------------------------------------------------
    def _validate_with_tokenpw_file(self, username, password):

        token_pw_data = self.PyiCloud.read_token_pw_file()

        if (isnot_empty(token_pw_data)
                and decode_password(token_pw_data.get(CONF_PASSWORD, '')) == password
                and 'session_token' in token_pw_data):
            return True

        return False

#----------------------------------------------------------------------------
    def validate_username_password_via_url_pyisession(self, username, password):

        username_password_b64 = self.b64encode_username_passsword(username,password)

        url     = f"{APPLE_SERVER_ENDPOINT['auth_url']}/{username}"
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Apple-iCloud/9.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko)',
            'Authorization': f"Basic {username_password_b64}"}
        data = None

        response_code = self.PyiCloudSession.post(url, data=data, headers=headers)

        valid_upw = True if response_code == 409 else False
        return valid_upw

#----------------------------------------------------------------------------
    def validate_with_authenticate(self, username, password):

        valid_upw = self.PyiCloud.authenticate()        #username, password)

        return valid_upw

#............................................................................
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   SUPPORT FUNCTIONS
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def b64encode_username_passsword(self, username, password):
        '''
       Return the b64 encoded the password used for url password validation
        '''

        username_password = f"{username}:{password}"
        upw = username_password.encode('ascii')
        username_password_b64 = base64.b64encode(upw)
        username_password_b64 = username_password_b64.decode('ascii')

        return username_password_b64
