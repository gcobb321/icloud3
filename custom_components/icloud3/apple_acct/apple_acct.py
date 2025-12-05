
'''
Customized version of pyicloud.py to support iCloud3 Custom Component

Platform that supports importing data from the iCloud Location Services
and Find My Friends api routines. Modifications to pyicloud were made
by various people to include:
    - Original pyicloud - picklepete & Quantame
                        - https://github.com/picklepete

    - Updated and maintained by - Quantame
    - 2fa developed by          - Niccolo Zapponi (@nzapponi)
    - Find My Friends component - Z Zeleznick
    - SRP, Terms of Use and Fido2 components - Tim Laing (@timlaing - https://github.com/timlaing/pyicloud)


'''

from ..global_variables     import GlobalVariables as Gb
from ..const                import (EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK,
                                    DOTS, RED_X, NL3, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                    APPLE_SERVER_ENDPOINT,
                                    CONF_USERNAME, CONF_PASSWORD, )
from ..utils.utils          import (instr, is_empty, isnot_empty, list_add, list_del, list_to_str,
                                    encode_password, decode_password, username_id, is_running_in_event_loop, )
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, secs_to_hhmm, next_min_mark_secs,
                                    format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_alert, post_alert, post_monitor_msg, post_error_msg,
                                    post_greenbar_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_data, log_exception, log_data_unfiltered, log_banner, )
from ..utils                import gps

from .apple_acct_devices    import iCloud_AppleAcctDevices
from .icloud_fido           import iCloud_Fido2
from .srp_password          import SrpPassword
# from .srp_encode_password   import SrpEncodePassword as SrpPassword
from .                      import icloud_requests_io  as icloud_io

from .icloud_cookie_jar     import PyiCloudCookieJar
import http.cookiejar as cookielib
#--------------------------------------------------------------------
from typing                 import TYPE_CHECKING, Any, NoReturn, Optional, Union, cast
from uuid                   import uuid1
from os                     import path
from re                     import match
import srp
import hashlib
import base64
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

#--------------------------------------------------------------------
HEADER_DATA = {
    "X-Apple-ID-Account-Country": "account_country",
    "X-Apple-ID-Session-Id": "session_id",
    "X-Apple-Session-Token": "session_token",
    "X-Apple-TwoSV-Trust-Token": "trust_token",
    "scnt": "scnt",
}

# big_list = list(range(1000000))
# big_set = set(big_list)
# start = time.time()
# print(999999 in big_list)
# print(f"List lookup: {time.time() - start:.6f}s")
# start = time.time()
# print(999999 in big_set)
# print(f"Set lookup: {time.time() - start:.6f}s")

HEADERS_SRP = {
    "Accept": "application/json, text/javascript",
    'referer':'https://www.apple.com/',
}
HEADERS_NON_SRP = {
    "Accept": "*/*",
}
    # "Accept": "*/*",
HEADERS = {
    "Accept": "application/json, text/javascript",
    "Content-Type": "application/json",
    "X-Apple-OAuth-Client-Id": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
    "X-Apple-OAuth-Client-Type": "firstPartyAuth",
    "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
    "X-Apple-OAuth-Require-Grant-Code": "true",
    "X-Apple-OAuth-Response-Mode": "web_message",
    "X-Apple-OAuth-Response-Type": "code",
    "X-Apple-OAuth-State": "",
    "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
}

DEVICE_STATUS_ERROR_500 = 500
INVALID_GLOBAL_SESSION_421 = 421
APPLE_ID_VERIFICATION_CODE_INVALID_404 = 404
AUTHENTICATION_NEEDED_421_450_500 = [421, 450, 500]
AUTHENTICATION_NEEDED_450 = 450
CONNECTION_ERROR_503 = 503

HTTP_RESPONSE_CODES = {
    -2:  'Server not Available',
    200: 'Accepted',
    201: 'Device Offline',
    204: 'Verification Code Accepted',
    302: 'Server can not be accessed',
    400: 'Invalid Verification Code',
    401: 'Invalid Username-Password',
    403: 'ACCESS DENIED/ACCT LOCKED?',
    404: 'URL/Web Page not Found',
    409: 'Valid Username/Password',
    421: 'Trust Token Expired',
    421.1: 'INVALID USERNAME/PASSWORD',
    450: 'Trust Token Reset',
    500: 'Trust Token Expired',
    503: 'Server Refused PwSRP Request',
}
HTTP_RESPONSE_CODES_IDX = {str(code): code for code in HTTP_RESPONSE_CODES.keys()}

DEVICE_DATA_FILTER_OUT = [
    'features', 'scd',
    'rm2State', 'pendingRemoveUntilTS', 'repairReadyExpireTS', 'repairReady', 'lostModeCapable', 'wipedTimestamp',
    'encodedDeviceId', 'scdPh', 'locationCapable', 'trackingInfo', 'nwd', 'remoteWipe', 'canWipeAfterLock', 'baUUID',
    'snd', 'continueButtonTitle', 'alertText', 'cancelButtonTitle', 'createTimestamp',  'alertTitle',
    'lockedTimestamp', 'locFoundEnabled', 'lostDevice', 'pendingRemove', 'maxMsgChar', 'darkWake', 'wipeInProgress',
    'repairDeviceReason', 'deviceColor', 'deviceDiscoveryId', 'activationLocked', 'passcodeLength',
    ]
    # 'BTR', 'LLC', 'CLK', 'TEU', 'SND', 'ALS', 'CLT', 'PRM', 'SVP', 'SPN', 'XRM', 'NWF', 'CWP',
    # 'MSG', 'LOC', 'LME', 'LMG', 'LYU', 'LKL', 'LST', 'LKM', 'WMG', 'SCA', 'PSS', 'EAL', 'LAE', 'PIN',
    # 'LCK', 'REM', 'MCS', 'REP', 'KEY', 'KPD', 'WIP',

'''
https://developer.apple.com/library/archive/documentation/DataManagement/Conceptual/CloudKitWebServicesReference/ErrorCodes.html#//apple_ref/doc/uid/TP40015240-CH4-SW1

#Other Device Status Codes
SEND_MESSAGE_MSG_DISPLAYED = 200
REMOTE_WIPE_STARTED = 200
REMOVE_DEVICE_SUCCESS = 200
UPDATE_LOCATION_PREF_SUCCESS = 200
LOST_MODE_SUCCESS = 200
PLAY_SOUND_SUCCESS = 200
PLAY_SOUND_NEEDS_SAFETY_CONFIRM = 203
SEND_MESSAGE_MSG_SENT = 205
REMOTE_WIPE_SENT = 205
LOST_MODE_SENT = 205
LOCK_SENT = 205
PLAY_SOUND_SENT = 205
LOCK_SERVICE_FAILURE = 500
SEND_MESSAGE_FAILURE = 500
PLAY_SOUND_FAILURE = 500
REMOTE_WIPE_FAILURE = 500
UPDATE_LOCATION_PREF_FAILURE = 500
LOCK_SUCC_PASSCODE_SET = 2200
LOCK_SUCC_PASSCODE_NOT_SET_PASSCD_EXISTS = 2201
LOCK_SUCCESSFUL_2 = 2204
LOCK_FAIL_PASSCODE_NOT_SET_CONS_FAIL = 2403
LOCK_FAIL_NO_PASSCD_2 = 2406


app specific password notes
"appIdKey=ba2ec180e6ca6e6c6a542255453b24d6e6e5b2be0cc48bc1b0d8ad64cfe0228f&appleId=APPLE_ID&password=password2&protocolVersion=A1234&userLocale=en_US&format=plist" --header "application/x-www-form-urlencoded" "https://idmsa.apple.com/IDMSWebAuth/clientDAW.cgi"

--data "appIdKey=ba2ec180e6ca6e6c6a542255453b24d6e6e5b2be0cc48bc1b0d8ad64cfe0228f&appleId=APPLE_ID&password=password2&protocolVersion=A1234&userLocale=en_US&format=plist"
--header "application/x-www-form-urlencoded" "https://idmsa.apple.com/IDMSWebAuth/clientDAW.cgi"
'''



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   AADevData Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable AppleAcct.AADevData_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class AppleAcctManager(object):
    '''
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import AppleAcctManager
        pyicloud = AppleAcctManager('username@apple.com', 'password')
        pyicloud.iphone.location()
    '''

    def __init__(   self,
                    username,
                    password=None,
                    apple_server_location=None,
                    locate_all_devices=None,
                    client_id = None,
                    cookie_directory=None,
                    session_directory=None,
                    validate_aa_upw=False,
                    config_flow_login=False):

        try:
            if validate_aa_upw is False:
                pass
            elif is_empty(username):
                msg = "Apple Account username is not specified/558"
                raise AppleAcctFailedLoginException(msg)
            elif is_empty(password):
                msg = "Apple Account password is not specified/562"
                raise AppleAcctFailedLoginException(msg)


            self.setup_time     = time_now()
            self.user           = {"accountName": username, "password": password}
            self.apple_id       = username
            self.username       = username
            self.username_id    = username_id(username)
            self.username_base  = self.username_id
            self.username_base6 = self.username_base if Gb.log_debug_flag else f"{username[:6]}…"

            self.validate_aa_upw = validate_aa_upw

            password = decode_password(password)
            self.password = password

            username_password = f"{username}:{password}"
            upw = username_password.encode('ascii')
            username_password_bytes = base64.b64encode(upw)
            self.username_password_bytes = username_password_bytes.decode('ascii')

            self.locate_all_devices  = locate_all_devices if locate_all_devices is not None else True
            self.terms_of_use_update_needed = False
            self.terms_of_use_accepted      = False

            self.response_code_pw     = 0
            self.auth_2fa_code_needed = False        # This is set during the authentication function
            self.auth_2fa_code_needed_secs = 0       # Time the auth code needed first detectedfunction
            self.login_successful     = False
            self.login_successful_srp = False
            self.is_authenticated     = False        # ICloud access has been authenticated via password or token
            self.auth_failed_503      = False

            self.Fido2                = iCloud_Fido2(self)
            self.fido2_devices        = None
            self.fido2_key_names      = None

            # Keep the last time an internet request was made. Check time since
            # in icloud3_main. Longer than 1-minute indicates internet is down.
            self.last_request_secs    = 0

            self.token_pw_data       = {}
            self.token_password      = password
            self.account_locked      = False        # set from the locked data item when authenticating with a token
            self.account_name        = ''
            self.account_country_code = ''          # accountCountryCode fro data when token was refreshed

            self.config_flow_login   = config_flow_login  # Indicates this AppleAcct object is beinging created from config_flow
            self.verification_code   = None
            self.authentication_alert_displayed_flag = False
            self.update_requested_by = ''

            if apple_server_location is None:
                self.apple_server_location = 'usa'
            else:
                self.apple_server_location = f"{apple_server_location},".split(',')[0]

            # GPS returned by Apple servers in China is GCJ02 or BD09 coded, convert to WGS84
            self.china_gps_coordinates    = ''  if instr(apple_server_location, ',') is False \
                                                else apple_server_location.split(',')[1]

            self._setup_apple_server_url()

            self.cookie_directory   = cookie_directory or Gb.icloud_cookie_directory
            self.session_directory  = session_directory or Gb.icloud_session_directory
            self.cookie_filename    = "".join([c for c in self.username if match(r"\w", c)])
            self.findme_url_root    = None # iCloud url initialized from the accountLogin response data

            self.iCloudSession      = None
            self.AADevices          = None # AppleAcct_ic3 object for Apple Device Service used to refresh the device's location

            self.session_data       = {}
            self.session_data_token = {}
            self.dsid               = ''
            self.trust_token        = ''
            self.session_token      = ''
            self.session_id         = ''
            self.client_id          = client_id or (f"auth-{str(uuid1()).lower()}")

            # login/setup error information
            self.error_codes  = ''
            self.error_secs   = 0
            self.error_reason = ''
            self.error_next_retry_secs = 0
            self.error_retry_cnt = 0

            add_log_file_filter(password)

            self._setup_iCloudSession()
            self._initialize_variables()
            self.authenticate_and_refresh_data()

            Gb.AppleAcctLoggingInto = self    # Identifies a partial login that might have failed
            Gb.AppleAcct_by_username[username] = self
            Gb.AppleAcct_password_by_username[username] = password


        except Exception as err:
            log_exception(err)

        return

#----------------------------------------------------------------------------
    def setup_error(self, code=None, reason=None):


        if code is None or code == 200:
            Gb.AppleAcct_error_by_username.pop(self.username, None)
            self.error_codes  = ''
            self.error_reason = ''
            self.error_secs   = 0
            self.error_next_retry_secs = 0
            self.error_retry_cnt = 0
            return

        if reason is None:
            reason = HTTP_RESPONSE_CODES.get(code, 'Other Error')

        if self.username not in Gb.AppleAcct_error_by_username:
            Gb.AppleAcct_error_by_username[self.username] = self

            self.error_codes  = f"{code}"
            self.error_reason = f"{reason}-{code}"
            self.error_secs   = time_now_secs()

        elif instr(self.error_reason, reason) is False:
            self.error_codes  += f",{code}"
            self.error_reason += f", {reason}-{code}"

        # Set retry at next 5-min + 10-mins
        if (code in [503]
                and self.error_next_retry_secs == 0):
            self.error_next_retry_secs = next_min_mark_secs(5, 10)

#----------------------------------------------------------------------------
    def authenticate_and_refresh_data(self):
        '''
        Authenticate the icloud acct and refresh the icloud data
        This is not done during the startup process and the username/password is being
        validated
        '''
        log_banner('start', self.username_id)

        self.login_successful = self.authenticate()

        log_banner('mid', self.username_id)

        if self.login_successful:
            self.setup_error(None)
            self.get_fido2_key_names()

            post_greenbar_msg(f"Apple Acct > {self.username_base}, Refresh Location Data")
            self.refresh_icloud_data(locate_all_devices=True)

            log_banner('finish', self.username_id)
            return True

        post_alert( f"{RED_X}Apple Acct > {self.username_base}, Login Failed, "
                    f"{self.error_reason}, "
                    f"AppleServerLocation-`{self.apple_server_location}`, "
                    "Location Data not Refreshed")

        log_banner('finish', self.username_id)
        return False


#----------------------------------------------------------------------------
    def _initialize_variables(self):
        '''
        Initialize the AppleAcct variables
        '''

        log_info_msg(f"{self.username_base}, Initialize AppleAcct Service, Set up iCloud Location Services connection")

        self.data      = {}
        self.params    = {  "clientBuildNumber": "2021Project52",
                            "clientMasteringNumber": "2021B29",
                            "ckjsBuildVersion": "17DProjectDev77",
                            "clientId": self.client_id[5:],  }

        self.new_2fa_code_already_requested_flag = False
        self.last_refresh_secs           = time_now_secs()
        self.token_auth_cnt              = 0
        self.last_token_auth_secs        = 0
        self.password_auth_cnt           = 0
        self.last_password_auth_secs     = 0

        # AppleAcct tracking method and raw data control objects
        self.AADevData_by_device_id      = {}   # Device data for tracked devices, updated in Pyicloud icloud.refresh_client
        self.AADevData_items             = []   # List of all AADevData objects used to find non-tracked device data

        # iCloud Device information - These is used verify the device, display on the EvLog and in the Config Flow
        # device selection list on the iCloud3 Devices screen
        self.device_id_by_icloud_dname   = {}       # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
        self.icloud_dname_by_device_id   = {}       # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
        self.device_info_by_icloud_dname = {}       # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro; iPhone15,2)'}
        self.device_model_name_by_icloud_dname= {}       # Example: {'Gary-iPhone': 'iPhone 14 Pro'}
        self.device_model_info_by_fname  = {}       # {'Gary-iPhone': [raw_model, model, model_display_name]}
        self.dup_icloud_dname_cnt        = {}       # Used to create a suffix for duplicate devicenames
                                                    # {'Gary-iPhone': ['iPhone15,2', 'iPhone', 'iPhone 14 Pro']}

#------------------------------------------------------------------------------
    def _setup_apple_server_url(self):
        '''
        Set up the icloud.com server endpoint urls for China (icloud.com.cn)
        '''
        if self.apple_server_location.startswith('.'):
            endpoint_suffix = f"icloud.com{self.apple_server_location}"
        else:
            endpoint_suffix = 'icloud.com'

        self.HOME_ENDPOINT  = APPLE_SERVER_ENDPOINT['home'].replace('icloud.com', endpoint_suffix)
        self.SETUP_ENDPOINT = APPLE_SERVER_ENDPOINT['setup'].replace('icloud.com', endpoint_suffix)
        self.AUTH_ENDPOINT  = APPLE_SERVER_ENDPOINT['auth']

#---------------------------------------------------------------------------
    @property
    def is_AADevices_setup_complete(self):
        return (self.findme_url_root is not None)

#---------------------------------------------------------------------------
    @property
    def response_code(self):
        return self.iCloudSession.response_code

#---------------------------------------------------------------------------
    @property
    def response_ok(self):
        return self.iCloudSession.response_ok

#---------------------------------------------------------------------------
    @property
    def response_code_desc(self):
        return (f"{HTTP_RESPONSE_CODES.get(self.response_code, 'Other Error')}-"
                f"{self.response_code}")

#---------------------------------------------------------------------------
    @property
    def account_owner_username(self):
        if self.account_name:
            return f"{self.account_name} ({self.username_id})"

        return f"{self.username_base6}"

    @property
    def username_account_owner(self):
        if self.account_name:
            return f"{self.username_id} ({self.account_name})"

        return f"{self.username_id}"

    @property
    def account_owner(self):
        name = self.account_name or self.username_base6
        return f"{name}"

    @property
    def account_owner_short(self):
        if len(self.account_owner) <= 26:
            return self.account_owner
        else:
            return f"{self.account_owner[:24]}…)"

    @property
    def account_owner_username_short(self):
        if len(self.account_owner_username) <= 26:
            return self.account_owner_username
        else:
            return f"{self.account_owner_username[:24]}…)"

    @property
    def username_account_owner_short(self):
        if len(self.username_account_owner) <= 16:
            return self.username_account_owner
        else:
            return f"{self.username_account_owner[:24]}…)"

    @property
    def username_id_short(self):
        if len(self.username_id) <= 19:
            return self.username_id
        else:
            return f"{self.username_id[:18]}…"

    @property
    def account_owner_link(self):
        name = self.account_name or self.username_base6
        return f"{LINK}{name}{RLINK}"

#----------------------------------------------------------------------------
    @property
    def primary_apple_account(self):
        '''
        The primary Apple account is the first username in the iCloud3
        configuration file. It will not have the username as the iCloud
        parameter (Gary-iPhone). A secondary Apple account will have it
        specified (lillian@email:Gare-iPlone)

        Return:
            True - This is the primary Apple Account' AppleAcct object
        '''
        return Gb.conf_apple_accounts[0][CONF_USERNAME] == self.username

#----------------------------------------------------------------------------
    def setup_new_apple_account_session(self):
        '''
        Initialize the session file and authenticate the apple account access. This
        will force Apple to display a new verification code
        '''
        self.session_data       = {}
        self.session_data_token = {}
        self.session_token      = ''
        self.session_id         = ''

        self.authenticate()

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           HANDLE ACCOUNT AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def authenticate(self, refresh_session=False):
        '''
        Handles authentication, and persists cookies so that
        subsequent logins will not cause additional e-mails from Apple.
        '''
        login_successful      = False
        self.auth_method      = ""
        self.auth_failed_503  = False
        self.response_code_pw = 0

        # Do not reset auth_2fa_code_needed flag on a reauthenticate session
        # It may have been set on first authentication
        if refresh_session is False:
            self.auth_2fa_code_needed = False
            self.auth_2fa_code_needed_secs = 0

        self.auth_2fa_code_needed = self._is_auth_2fa_code_needed

        # Validate token - Consider authenticated if token is valid (POST=validate)
        if (refresh_session is False
                and self.session_data.get('session_token')
                and 'dsid' in self.params):
            self.auth_method = "ValidToken"
            login_successful = self._validate_token()

            log_debug_msg(f"{self.username_base}, {self.auth_method}, {login_successful=}")

        # Authenticate - Sign into Apple Account (POST=/signin)
        if login_successful is False:
            self.auth_method = "TrustToken"
            login_successful = self._authenticate_with_token()

            log_debug_msg(f"{self.username_base}, {self.auth_method}, {login_successful=}")

        if login_successful is False:
            self.auth_method = 'Password'
            login_successful = self.authenticate_with_password_srp()

            # The Auth with Token is necessary to fill in the findme_url
            self.response_code_pw     = self.response_code
            self.login_successful_srp = login_successful
            if login_successful:
                self._authenticate_with_token()

                log_debug_msg(f"{self.username_base}, {self.auth_method}/TrustToken, {login_successful=}")

        #TESTCODE
        # login_successful = False

        # if login_successful is False:
        #     self.auth_method = 'Password'
        #     login_successful = self.authenticate_with_password()

        #     log_debug_msg(f"{self.username_base}, {self.auth_method}, {login_successful=}")

        #     self.response_code_pw = self.response_code

            # The Auth with Token is necessary to fill in the findme_url
            # if login_successful:
            #     login_successful = self._authenticate_with_token()

            #     log_debug_msg(f"{self.username_base}, {self.auth_method}/TrustToken, {login_successful=}")

        self.auth_2fa_code_needed = self._is_auth_2fa_code_needed
        self._update_token_pw_file(CONF_PASSWORD, encode_password(self.token_password))

        self.list_cookies()

        time_between_token_auth    = format_age(self.last_token_auth_secs)
        time_between_password_auth = format_age(self.last_password_auth_secs)
        if instr(self.auth_method, 'Token'):
            self.token_auth_cnt += 1
            self.last_token_auth_secs = time_now_secs()
        elif instr(self.auth_method, 'Password'):
            self.password_auth_cnt += 1
            self.last_password_auth_secs = time_now_secs()

            post_event( f"{EVLOG_NOTICE}Apple Acct {self.auth_method} Auth > {self.account_owner}, "
                        f"#{self.password_auth_cnt} ({time_between_password_auth}), "
                        f"{CRLF_DOT}Apple Time-{apple_server_time()}")

        post_monitor_msg(   f"Apple Acct {self.auth_method} Auth > {self.account_owner}, "
                            f"TokenAuth-#{self.token_auth_cnt} ({time_between_token_auth}), "
                            f"PasswordAuth-#{self.password_auth_cnt} ({time_between_password_auth})")

        self.is_authenticated = self.is_authenticated or login_successful
        if self.is_authenticated:
            self.setup_error(None)

        return self.is_authenticated

#----------------------------------------------------------------------------
    def _authenticate_with_token(self):
        '''Authenticate using session token. Return True if successful.'''
        try:
            log_info_msg(f"{self.username_base}, Authenticate with TrustToken")
            post_greenbar_msg(f"Apple Acct > {self.username_base}, Auth with TrustToken")

            if "session_token" in self.session_data:
                self.account_country_code = self.session_data.get("account_country", "")
                login_data={"accountCountryCode": self.session_data.get("account_country"),
                            "dsWebAuthToken": self.session_data.get("session_token"),
                            "extended_login": True,
                            "trustToken": self.session_data.get("trust_token", ""),
                            "appName": "iCloud3"}
            else:
                # self.response_code = 421
                log_debug_msg(  f"{self.username_base}, "
                                f"Authenticate with Token > Failed, Invalid Session Data")
                return False

        except Exception as err:
            log_exception(err)

        login_successful = self.log_into_account(login_data)

        return login_successful

#----------------------------------------------------------------------------
    def log_into_account(self, login_data):
        try:
            url = f"{self.SETUP_ENDPOINT}/accountLogin"

            self.data = icloud_io.post(self, url, params=self.params, data=login_data)

            if self.data is None:
                log_debug_msg( f"{self.username_base}, "
                                "Authenticate with Token > Failed, "
                                "No data received from Apple (icloud.com)")
                return False

            self._handle_accept_terms_of_use(login_data)

            if 'items' in self.data:
                if 'hsaTrustedBrowser' in self.data['items']:
                    self._update_token_pw_file('items', self.data['items'])
                else:
                    log_debug_msg(  f"{self.username_base}, "
                            "Authenticate with Token > Failed, "
                            "Invalid 2fa hsaTrustedBrowser/hsaChallengeRequired Items")
                    return False

            if 'dsInfo' in self.data:
                if 'dsid' in self.data['dsInfo']:
                    self.params['dsid'] = self.dsid = str(self.data['dsInfo']['dsid'])
                    self._update_token_pw_file('dsid', self.dsid)

                if 'fullName' in self.data['dsInfo']:
                    self.account_name   = self.data['dsInfo']['fullName'].replace(' ', '')
                    self.account_locked = self.data['dsInfo']['locked']

            if 'webservices' in self.data:
                try:
                    if self.is_AADevices_setup_complete is False:
                        self.findme_url_root = self.data['webservices']['findme']['url']
                        self._update_token_pw_file('findme_url', self.findme_url_root)
                except:
                    pass

            elif (self.data.get('success', False) is False
                    or self.data.get('error', 1) == 1):
                return False

            self._update_token_pw_file('session_id', self.session_data_token)
            self._update_token_pw_file('session_token', self.session_data_token)
            self._update_token_pw_file('trust_token', self.session_data_token)

            self.setup_error(None)

            # log_debug_msg( f"{self.username_base}, Authenticate with Token > Successful")
            return True

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with Token > Token is not valid, "
                            f"Error-{err}, 2fa Needed-{self.auth_2fa_code_needed}")
            return False

        except Exception as err:
            log_exception(err)

        return False

#----------------------------------------------------------------------------
    def authenticate_with_password(self):
        '''
        Sign into Apple account with password. This can be called by:
            - the verify_username_password fct in ValidateAppleAcctUPW
            - the authenticate fct in AppleAcctManager

        Return:
            True - Successful login
            False - Invalid Password or other error
        '''
        log_info_msg(f"{self.username_base}, Authenticate with Password")
        post_greenbar_msg(f"Apple Acct > {self.username_base}, Auth with Password")

        headers = self._get_auth_headers()

        url = f"{self.AUTH_ENDPOINT}/signin"
        params = {"isRememberMeEnabled": "true"}
        login_data = {  "accountName": self.username,
                        "password": self.password,
                        "rememberMe": True,
                        "trustTokens": []}

        if self.session_data.get("trust_token"):
            login_data["trustTokens"] = [self.session_data_token.get("trust_token")]

        try:
            self.data = icloud_io.post(self, url, params=params, data=login_data,
                                                    headers=headers,)

            self.response_code_pw = self.response_code

            self._handle_accept_terms_of_use(login_data)
            if self.terms_of_use_update_needed:
                return False

            return ('session_token' in self.session_data)

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with password > Failed, Password is not valid, "
                            f"Error-{err}")     #, 2fa Needed-{self.auth_2fa_code_needed}")
            raise AppleAcctFailedLoginException()

        except Exception as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with password > Failed, "
                            f"Other Error, {err}")
            log_exception(err)
            return False

        return False

#----------------------------------------------------------------------------
    def authenticate_with_password_srp(self, username=None, password=None):
        '''
        Sign into Apple account with password via Secure Remote Password verification

        Return:
            True - Successful login
            False - Invalid Password or other error
        '''
        username = username if username is not None else self.username
        password = password if password is not None else self.password

        log_info_msg(f"{self.username_base}, Authenticate with PasswordSRP")
        post_greenbar_msg(f"Apple Acct > {self.username_base}, Auth with PasswordSRP")

        log_info_msg(  f"{self.username_base}, signin/init, Calculate and send private key")

        # Step 1: client generates private key a (stored in srp.User) and public key A, sends to server
        srp.rfc5054_enable()
        srp.no_username_in_x()

        try:
            SrpPW   = SrpPassword(password)
            SrpUser = srp.User(username, SrpPW, hash_alg=srp.SHA256, ng_type=srp.NG_2048)
            _, A = SrpUser.start_authentication()
            A_bytes = base64.b64encode(A).decode()

            data = {'a': A_bytes}
            data = self._srp_icloud_io_signin_init(username, data)

        except Exception as err:
            log_exception(err)
            return False

        if self.response_code == 401:
            post_error_msg("Password SRP Error, "
                            "Failed to connect to Apple Acct, maybe Locked (401)")
            return False

        elif 'salt' not in data:
            post_error_msg( "Password SRP Error, "
                            "Apple did not return salt/hash values")
            return False

        if (Gb.internet_error
                or 'salt' not in data):
            return False

        # Step 2: server sends salt, public key B and c to client
        salt       = base64.b64decode(data['salt'])
        b          = base64.b64decode(data['b'])
        c          = data['c']
        iterations = data['iteration']
        key_length = 32
        protocol   = data["protocol"]

        log_info_msg(  f"{self.username_base}, Authenticating with PasswordSRP, "
                        "signin/complete, Server will verify Credentials")

        # Step 3: client generates session key M1 and M2 with salt and b, sends to server
        SrpPW.set_encrypt_info(salt, iterations, key_length, protocol)

        if (SrpPW.salt is None
                or SrpPW.error_reason is not None):
            post_error_msg(f"Password SRP Error, {SrpPW.error_reason}")
            return False

        m1_srpusr = SrpUser.process_challenge(salt, b)
        m1        = base64.b64encode(m1_srpusr).decode()
        m2_srpusr = SrpUser.H_AMK
        m2        = base64.b64encode(m2_srpusr).decode()

        if m1 and m2:
            data = {"c": c, "m1": m1, "m2": m2}

        data = self._srp_icloud_io_signin_complete(username, data)

        valid_upw = self.response_code in [200, 409]
        self.response_code_pw = self.response_code
        if valid_upw is False:
            self.setup_error(self.response_code)

        return valid_upw

#............................................................................
    def _srp_icloud_io_signin_init(self, username, data):
        '''
        Process the endpoint/signin/init request
        '''

        data.update({'protocols': ['s2k', 's2k_fo']})

        return self._srp_icloud_io('init', username, data)

#............................................................................
    def _srp_icloud_io_signin_complete(self, username, data):
        '''
        Process the endpoint/signin/complete request
        '''

        params       = {"isRememberMeEnabled": "true"}
        trust_token  = self.session_data.get('trust_token')
        trust_tokens = [trust_token] if trust_token else []
        data.update({"rememberMe": True, "trustTokens": trust_tokens})

        return self._srp_icloud_io('complete', username, data, params)

#............................................................................
    def _srp_icloud_io(self, url_suffix, username, data, params=None):

        url     = f"{self.AUTH_ENDPOINT}/signin/{url_suffix}"
        headers = self._get_auth_headers()
        headers["Accept"] = "application/json, text/javascript"
        data.update({"accountName": username})

        try:
            data = icloud_io.post(self, url, json=data, headers=headers)
            return data

        except AppleAcctAPIResponseException as err:
            pass
        except Exception as err:
            log_exception(err)


#----------------------------------------------------------------------------
    def _validate_token(self):
        '''Checks if the current access token is still valid.'''

        log_info_msg(f"{self.username_base}, Validate Token")

        url = f"{self.SETUP_ENDPOINT}/validate"
        data = "null"

        try:
            self.data = icloud_io.post(self, url, data=data)

            self.auth_2fa_code_needed = self._is_auth_2fa_code_needed

            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token valid, "
                            f"2fa Needed-{self.auth_2fa_code_needed}")

            return True

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token is not valid, "
                            f"2fa Needed-{self.auth_2fa_code_needed}, "
                            f"Error-{err}")

        except Exception as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Error encountered validating token > "
                            f"Error, {err}")
            log_exception(err)

        return False

#----------------------------------------------------------------------------
    def _get_auth_headers(self, overrides=None):

        headers = HEADERS.copy()
        headers["X-Apple-OAuth-State"] = self.client_id

        if self.session_data.get("scnt"):
            headers["scnt"] = self.session_data.get("scnt")
        if self.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")
            self.session_id = self.session_data.get("session_id")

        if overrides:
            headers.update(overrides)
        return headers

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            FIDO SECURITY KEY SETUP AND AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def get_fido2_key_names(self):

        if Gb.fido2_security_keys_enabled is False:
            return None

        self.fido2_key_names = self.Fido2.security_key_names
        _log(f'{self=} {self.fido2_key_names=}')
        self.fido2_devices   = self.Fido2.fido2_devices
        _log(f'{self=} {self.fido2_devices=}')

        return self.fido2_key_names

#----------------------------------------------------------------------------
    def confirm_fido2_security_key(self, fido2_key_name):

        self.Fido2.confirm_security_key(fido2_key_name)

        return True

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HANDLE ACCEPTING TERMS OF USE
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _handle_accept_terms_of_use(self, login_data):
        """Handle accepting updated terms of use"""

        self.terms_of_use_update_needed = self.data.get('termsUpdateNeeded', False)
        if self.terms_of_use_update_needed is False:
            return

        if self.terms_of_use_accepted is False:
            post_alert(f"{self.username_base} > "
                        "Apple Acct > Accept `Terms of Use` is needed "
                        "(Auth Code entry screen)")
            return False

        url    = f"{self.SETUP_ENDPOINT}/getTerms"
        json   = {"locale": self.data.get("dsInfo", {}).get("languageCode", "en_US")}

        data = icloud_io.post(self, url, params=self.params, data=login_data, json=json)
        if data == {}:
            return

        # Terms version in Sept25 with iOS26 is 628201
        terms_info = data
        version    = terms_info.get("iCloudTerms", {}).get("version")
        if version is None:
            self._handle_accept_terms_of_use_error("Could not get terms version")
            return False

        url    = f"{self.SETUP_ENDPOINT}/repairDone"
        json   = {"acceptedICloudTerms": version}

        data = icloud_io.get(self, url, params=self.params, json=json)

        url = f"{self.SETUP_ENDPOINT}/accountLogin"

        self.data = icloud_io.post(self, url, params=self.params, data=login_data)

        if self.data:
            self.terms_of_use_update_needed = False

#----------------------------------------------------------------------------
    def _handle_accept_terms_of_use_error(self, error_msg):
        log_error_msg(error_msg)


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            SETUP SESSION FOR THIS APPLE ACCOUNT
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def _setup_iCloudSession(self):
        '''
        Set up the password_filter, cookies and session files
        '''

        # If password was changed, delete the session file to generate a new 6-digit
        # verification code from Apple when the new session is created
        self.read_token_pw_file()

        self._update_token_pw_file(CONF_USERNAME, self.username)
        if self.password != self.token_password:
            file_io.delete_file(self.session_dir_filename)

        try:
            self.session_data = {}
            self.session_data = file_io.read_json_file(self.session_dir_filename)

            if self.session_data != {}:
                self.session_data_token.update(self.session_data)

            # If this username is being opened again with another password, a new AppleAcct
            # object is being created to verify the username/password are correct. Get some
            # token and url values from the original AppleAcct instance in case an asap specific
            # password is being used for this instance.
            if (self.is_AADevices_setup_complete is False
                    and self.username in Gb.AppleAcct_by_username):
                _AppleAcct = Gb.AppleAcct_by_username[self.username]
                if _AppleAcct.findme_url_root:
                    self.findme_url_root = _AppleAcct.findme_url_root
                    self._update_token_pw_file('findme_url', self.findme_url_root)

                self.session_data_token = _AppleAcct.session_data_token.copy()
                self.session_data_token.update(self.session_data)
                self._update_token_pw_file('trust_token', self.session_data_token)
                if 'session_token' in self.session_data_token:
                    self.session_token = self.session_data_token['session_token']
                    self._update_token_pw_file('session_token', self.session_token)

                if 'session_id' in self.session_data:
                    _AppleAcct.session_id = self.session_data['session_id']
                    self._update_token_pw_file('session_id', _AppleAcct.session_id)

        except Exception as err:
            log_exception(err)
            log_info_msg(   f"{self.username_base}, "
                            f"Session file does not exist ({self.session_dir_filename})")

        if 'client_id' in self.token_pw_data:
            self.client_id = self.token_pw_data['client_id']
        if 'client_id' in self.session_data:
            self.client_id = self.session_data['client_id']
        else:
            self.session_data['client_id'] = self.client_id
            self.session_data_token['client_id'] = self.client_id
        self._update_token_pw_file('client_id', self.client_id)

        self.iCloudSession = icloud_io.new_session(self)

        success = self.load_cookies(self.cookie_dir_filename)
        if success:
            log_debug_msg(  f"{self.username_base}, "
                            f"Loaded Cookies File ({self.cookie_dir_filename})")

        else:
            log_warning_msg(f"{self.username_base}, "
                            f"Load Cookies File Failed ({self.cookie_dir_filename})")

#--------------------------------------------------------------------
    def load_cookies(self, cookie_dir_filename):
        self.iCloudSession.cookies = PyiCloudCookieJar(filename=cookie_dir_filename)

        # Added .cookies to filename, rename old file (v3.3.3.1)
        old_cookie_dir_filename = cookie_dir_filename.replace('.cookies', '')
        file_io.rename_file(old_cookie_dir_filename, cookie_dir_filename)

        if path.exists(cookie_dir_filename):
            try:
                cast(PyiCloudCookieJar, self.iCloudSession.cookies).load()

            except (OSError, ValueError) as err:
                log_warning_msg(f"{self.username_base}, "
                                f"Failed to load cookies {cookie_dir_filename}, "
                                f"Starting without persisted cookies",
                                f"{err}")
                cast(PyiCloudCookieJar, self.iCloudSession.cookies).clear()
                return False

        return True

#----------------------------------------------------------------------------
    def list_cookies(self):
        if Gb.log_debug_flag is False:
            return

        try:
            cast(PyiCloudCookieJar, self.iCloudSession.cookies).list()
        except:
            (f"\n⠂  ❗ _.Cookie.file-{self.AppleAcct.cookie_dir_filename}, None")

#----------------------------------------------------------------------------
    '''
    The token password file stores the encoded password associated with the session
    token. It is used to see if the user is changing the username's password. It so,
    the session and it's token must be deleted to create a session token and cause a
    2fa verification. It this is not done, the user will be logged into the session
    without checking the password and a password change will not be handled until the
    token wxpires.
    '''
    def read_token_pw_file(self):
        try:
            self.token_password = ''
            self.token_pw_data = file_io.read_json_file(self.tokenpw_dir_filename)

            if self.username not in self.token_pw_data:
                self.token_pw_data[CONF_USERNAME] = self.username

            self.token_password = decode_password(self.token_pw_data[CONF_PASSWORD])

        except:
            self.token_password = self.password

        return self.token_pw_data

#----------------------------------------------------------------------------
    def _update_token_pw_file(self, item_key, source_data):

        if self.validate_aa_upw:
            return

        try:
            new_value = source_data               if type(source_data) is str else \
                        source_data.get(item_key) if type(source_data) is dict else \
                        None

            if True is True or isnot_empty(new_value):
                if self.token_pw_data.get(item_key) != new_value:
                    self.token_pw_data[item_key] = new_value
                    self._write_token_pw_file()

        except Exception as err:
            log_exception(err)
            pass

#...................................................
    def _write_token_pw_file(self):

        self.token_password = self.password

        try:
            file_io.save_json_file(self.tokenpw_dir_filename, self.token_pw_data)

        except Exception as err:
            # log_exception(err)
            log_warning_msg(f"Apple Acct > {self.account_owner}, "
                            f"Failed to update tokenpw file {self.tokenpw_dir_filename}")

#----------------------------------------------------------------------------
    @property
    def cookie_dir_filename(self):
        '''Get path for cookie file'''
        return path.join(self.cookie_directory,
                        f"{self.cookie_filename}.cookies")

    @property
    def session_dir_filename(self):
        '''Get path for session data file'''
        return path.join(self.cookie_directory,
                        f"{self.cookie_filename}.session")

    @property
    def tokenpw_dir_filename(self):
        '''
        Token Password - This file stores the username's password associated with the session
        token and is used to determine if the password has changed and the session needs to be reset
        '''
        return path.join(self.cookie_directory,
                        f"{self.cookie_filename}.tpw")

    @property
    def authentication_method(self):
        return self.auth_method

    @property
    def login_failed(self):
        return (self.username in Gb.AppleAcct_error_by_username)

    @property
    def _check_2sa_needed(self):
        '''Returns True if two-step authentication is required.'''
        try:
            needs_2sa_flag = (self.data.get("dsInfo", {}).get("hsaVersion", 0) >= 1
                                and (self.is_challenge_required or self.is_trusted_browser is False))

            return needs_2sa_flag

        except AttributeError:
            return False
        except:
            return False

    @property
    def _is_auth_2fa_code_needed(self):
        '''
        Returns True if two-factor authentication is required. This is determined by the
        data["hsaChallengeRequired"] value.

        If it is needed, the 'auth_2fa_code_needed_secs' is set to the current time.
        '''
        # if self.auth_2fa_code_needed:
        #     return True

        try:
            needs_2fa_flag = (self.data.get("dsInfo", {}).get("hsaVersion", 0) == 2
                                    and (self.is_challenge_required or self.is_trusted_browser is False))

        except AttributeError:
            return False
        except Exception as err:
            log_exception(err)
            return False

        if needs_2fa_flag:
            if self.auth_2fa_code_needed_secs == 0:
                self.auth_2fa_code_needed_secs = time_now_secs()

            log_debug_msg(  f"{self.username_base}, "
                            f"NEEDS-2FA, "
                            f"ChallengeRequired-{self.is_challenge_required}, "
                            f"TrustedBrowser-{self.is_trusted_browser}")
        return needs_2fa_flag

    @property
    def is_challenge_required(self):
        '''Returns True if the challenge code is needed.'''
        return self.data.get("hsaChallengeRequired", False)

    @property
    def is_trusted_browser(self):
        '''Returns True if the session is trusted.'''
        return self.data.get("hsaTrustedBrowser", False)

    # @property
    def trusted_devices(self):
        '''Returns devices trusted for two-step authentication.'''
        headers = self._get_auth_headers()
        url     = f"{self.SETUP_ENDPOINT}/listDevices"

        try:
            data = icloud_io.post(self, url, params=self.params, headers=headers,)

            return data.get('devices')

        except Exception as err:
            log_exception(err)

        return {}

    def new_log_in_needed(self, username):
        return username != self.username

    @property
    def icloud_dnames(self):
        icloud_dnames = [icloud_dname
                    for icloud_dname in self.device_id_by_icloud_dname.keys()]
        icloud_dnames.sort()

        return icloud_dnames

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HANDLE 6-DIGIT VERIFICATION CODE AND TRUST SESSION TASKS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def send_verification_code(self, device):
        '''Requests that a verification code is sent to the given device.'''

        url  = f"{self.SETUP_ENDPOINT}/sendVerificationCode"
        data = device

        self.data = icloud_io.post(self, url, params=self.params, data=data)

        return self.data.get("success", False)

#----------------------------------------------------------------------------
    def validate_2fa_code(self, code):
        '''Verifies a verification code received via Apple's 2FA system (HSA2).'''

        headers = self._get_auth_headers()      #{"Accept": "application/json"})

        url  = f"{self.AUTH_ENDPOINT}/verify/trusteddevice/securitycode"
        data = {"securityCode": {"code": code}}

        try:
            data = icloud_io.post(self, url, data=data, headers=headers,)

        except AppleAcctAPIResponseException as error:
            # Wrong verification code
            if error.code == -21669:
                log_error_msg(  f"Apple Acct > {self.account_owner}, "
                                f"Incorrect verification code")
                return False

        except Exception as err:
            log_exception(err)
            return False

        self.trust_session()

        self.auth_2fa_code_needed = False
        self.auth_2fa_code_needed = self._is_auth_2fa_code_needed

        valid_msg = 'Rejected' if self.auth_2fa_code_needed else 'Accepted'
        log_debug_msg(f"{self.username_base}, Verification Code {valid_msg}")
        post_greenbar_msg('')

        # Return true if 2fa code was successful
        return not self.auth_2fa_code_needed

#----------------------------------------------------------------------------
    def trust_session(self):
        '''
        Request session trust to avoid user log in going forward
        '''
        url     = f"{self.AUTH_ENDPOINT}/2sv/trust"
        headers = self._get_auth_headers()

        try:
            icloud_io.get(self, url, headers=headers)

            if self._authenticate_with_token():
                self.auth_2fa_code_needed = self._is_auth_2fa_code_needed
            return True

        except AppleAcctAPIResponseException:
            log_error_msg("Session trust failed")
            self.auth_2fa_code_needed = self._is_auth_2fa_code_needed

        return False

#----------------------------------------------------------------------------
    def _get_webservice_url(self, ws_key):
        '''Get webservice URL, raise an exception if not exists.'''
        try:
            if self.webservices.get(ws_key) is None:
                return None

            return self.webservices[ws_key]["url"]
        except:
            return None

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HANDLE APPLE ACCOUNT DATA REQUESTS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def create_AADevices_object(self, config_flow_login=False):
        '''
        Initializes the Family Sharing object, refresh the iCloud device data for all
        devices and create the AADevData object containing the data for all locatible devices.

        config_flow_create indicates another Apple acct is being logged into and a new iCloud object
        should be created instead of using the existing iCloud object created when iC3 started
        '''
        try:
            if self.AADevices:
                return self.AADevices

            self.AADevices = iCloud_AppleAcctDevices(self, self.iCloudSession, self.params)

            log_debug_msg(f"{self.username_base}, Create iCloud object {self.username_base}")

            return self.AADevices

        except Exception as err:
            log_exception(err)

            return None

#----------------------------------------------------------------------------
    def refresh_icloud_data(self, locate_all_devices=None,
                                    requested_by_devicename=None,
                                    device_id=None):
        '''
        Refresh the iCloud device data for all devices and update the AADevData object
        for all locatible devices that are being tracked by iCloud3.
        '''
        try:
            if self.is_AADevices_setup_complete is False:
                return False

            elif self.username in Gb.AppleAcct_error_by_username:
                return False

            elif self.AADevices:
                locate_all_devices = locate_all_devices      if locate_all_devices is not None \
                                else self.locate_all_devices if self.locate_all_devices is not None \
                                else True

                self.AADevices.refresh_device(  locate_all_devices=locate_all_devices,
                                                requested_by_devicename=requested_by_devicename,
                                                device_id=device_id)
            else:
                # Refresh, then Create all devices
                self.create_AADevices_object()

            return True

        except Exception as err:
            log_exception(err)

        return False

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            OTHER SUPPORT FUNCTIONS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''

        data = self.AADevices.play_sound(device_id, subject)
        return data

#----------------------------------------------------------------------------
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return (f"<AppleAcctManager: {self.setup_time}-{self.account_owner}>")
        except:
            return (f"<AppleAcctManager: NotSetUp>")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#       EXCEPTION HANDLERS
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''Library exceptions.'''


class AppleAcctException(Exception):
    '''Generic iCloud exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctAPIResponseException(AppleAcctException):
    '''iCloud response exception.'''
    def __init__(self, reason, code=None, retry=False):

        self.reason = reason
        self.code = code
        message = reason or "Could not connect to iCloud Location Servers"
        if code:
            message += (f" (Error Code {code})")
        if retry:
            message += ". Retrying ..."

        super(AppleAcctAPIResponseException, self).__init__(message)

#----------------------------------------------------------------------------
class AppleAcctManagerNotActivatedException(AppleAcctAPIResponseException):
    '''iCloud service not activated exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctFailedLoginException(AppleAcctException):
    '''iCloud failed login exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcct2FARequiredException(AppleAcctException):
    '''iCloud 2SA required exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcct2SARequiredException(AppleAcctException):
    """iCloud 2SA required exception."""
    def __init__(self, apple_id):
        message = f"Two-step authentication required for account: {apple_id}"
        super().__init__(message)

#----------------------------------------------------------------------------
class AppleAcctNoStoredPasswordAvailableException(AppleAcctException):
    '''iCloud no stored password exception.'''
    pass

#----------------------------------------------------------------------------
class AppleAcctNoDevicesException(AppleAcctException):
    '''iCloud no device exception.'''
    pass
