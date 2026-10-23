
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
from ..const                import (EVLOG_ALERT, LINK, RLINK, LLINK,
                                    DOTS, RED_X, NL3, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                    APPLE_SERVER_ENDPOINT,
                                    CONF_AUTH_METHODS, CURRENT,
                                    PUSH, TEXT, TEXT_1, TEXT_2, HWKEY,
                                    CONF_USERNAME, HIGH_INTEGER,
                                    AUTH_METHOD_FNAME, )
from ..utils.utils          import (instr, is_empty, isnot_empty, list_add, list_del, list_to_str, dict_del,
                                    decode_password, username_id, is_running_in_event_loop, )
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t,
                                    secs_since, secs_to_hhmm, format_date,
                                    format_secs_since, format_time_age )
from ..utils.messaging      import (post_alert, post_greenbar_msg, update_alert_sensor,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg,
                                    log_data, log_exception, log_data_unfiltered, log_banner, )
from ..utils                import gps
from ..startup              import config_file
from .apple_acct_devices    import iCloud_AppleAcctDevices
from .apple_acct_auth       import AppleAcctAuthMixin, SRP_SIGNIN_TOKEN_INFO_MAX_AGE_SECS
from .apple_acct_session    import AppleAcctSessionMixin
from .icloud_hwkey          import iCloud_HwKey
from .                      import icloud_requests_io  as icloud_io
from .exceptions            import (AppleAcctException, AppleAcctAPIResponseException,
                                    AppleAcctManagerNotActivatedException, AppleAcctFailedLoginException,
                                    AppleAcct2FARequiredException, AppleAcct2SARequiredException,
                                    AppleAcctNoStoredPasswordAvailableException, AppleAcctNoDevicesException,)
import http.cookiejar as cookielib

#--------------------------------------------------------------------
from typing                 import TYPE_CHECKING, Any, NoReturn, Optional, Union
from uuid                   import uuid1
from os                     import path
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

APPLE_ACCT_ALERT_MSG_REAUTH_DAYS = [-5, 10, 20, 88, 89, 86, 87]

HEADERS_SRP = {
    "Accept": "application/json, text/javascript",
    'referer':'https://www.apple.com/',
}
HEADERS_NON_SRP = {
    "Accept": "*/*",
}
    # "Accept": "*/*",

DEVICE_STATUS_ERROR_500 = 500
INVALID_GLOBAL_SESSION_421 = 421
APPLE_ID_AUTH_CODE_INVALID_404 = 404
AUTHENTICATION_NEEDED_421_450_500 = [421, 450, 500]
AUTHENTICATION_NEEDED_450 = 450
CONNECTION_ERROR_503 = 503

HTTP_RESPONSE_CODES = {
    -4:  'Internet Connection Error',
    -3:  'Apple PwSRP Initialization Failed',
    -2:  'Server not Available',
    200: 'Accepted',
    201: 'Device Offline',
    204: 'Authentication Code Accepted',
    302: 'Server can not be accessed',
    400: 'Invalid Authentication Code',
    401: 'Invalid Username/Password',
    401.1: 'Invalid Username',
    403: 'Access Denied, Acct maybe Locked',
    404: 'URL/Web Page not Found',
    409: 'Valid Username/Password',
    421: 'Trust Token Expired',
    421.1: 'INVALID USERNAME/PASSWORD',
    423: 'Too Many Auth Codes Requested, Retry Later',
    450: 'Trust Token Reset',
    500: 'Trust Token Expired',
    503: 'Server Refused PwSRP Request, Retry Later',
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

class AppleAcctManager(AppleAcctAuthMixin, AppleAcctSessionMixin):
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
                    srp_validate_only=False,
                    config_flow_login=False):

        try:
            if validate_aa_upw is False:
                pass
            elif is_empty(username):
                msg = "Apple Account username is not specified"
                raise AppleAcctFailedLoginException(msg)
            elif is_empty(password):
                msg = f"Apple Account password is not specified , {username}"
                raise AppleAcctFailedLoginException(msg)


            self.setup_time     = time_now()
            self.user           = {"accountName": username, "password": password}
            self.apple_id       = username
            self.username       = username
            self.username_id    = username_id(username)
            self.username_base  = self.username_id
            self.username_base6 = self.username_base if Gb.is_log_level_debug else f"{username[:6]}…"
            self.conf_apple_acct, self.aa_idx = config_file.conf_apple_acct(self.username)

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

            self.response_code_pw           = 0
            self.was_auth_code_requested = False
            self.is_reauth_needed = False        # This is set during the authentication function
            self.is_reauth_needed_secs = \
                        Gb.restore_state_apple_accts.get(self.username, {}).get('is_reauth_needed_secs', 0)

            # Time the auth code needed first detectedfunction
            self.login_auth_method    = ""
            self.login_successful     = False
            self.login_successful_srp = None
            self.auth_failed_503      = False
            self.is_authenticated     = False        # ICloud access has been authenticated via password or token

            self.HwKey                = iCloud_HwKey(self)
            self.hwkey_names          = self.auth_methods.get(HWKEY, '')

            # Keep the last time an internet request was made. Check time since
            # in icloud3_main. Longer than 1-minute indicates internet is down.
            self.last_request_secs    = 0

            self.token_pw_data        = {}
            self.token_password       = password
            self.account_locked       = False       # set from the locked data item when authenticating with a token
            self.account_name         = ''
            self.account_country_code = ''          # accountCountryCode fro data when token was refreshed
            self.srp_valid_upw_secs   = 0           # time when the srp password was validated and accepted

            self.config_flow_login   = config_flow_login  # Indicates this AppleAcct object is beinging created from config_flow
            self.auth_code           = None          # Initial value sets forms > reauth > request_code
            self.is_auth_alert_displayed = False
            self.update_requested_by = ''

            if apple_server_location is None:
                self.apple_server_location = 'usa'
            else:
                self.apple_server_location = f"{apple_server_location},".split(',')[0]

            # GPS returned by Apple servers in China is GCJ02 or BD09 coded, convert to WGS84
            self.china_gps_coordinates    = ''  if instr(apple_server_location, ',') is False \
                                                else apple_server_location.split(',')[1]
            self._setup_apple_server_url()

            self.cookie_directory   = Gb.icloud_cookies_directory
            self.session_directory  = Gb.icloud_session_directory
            self.cookie_username    = self.cookie_username_base()
            self.findme_url_root    = None # iCloud url initialized from the accountLogin response data

            self.iCloudSession      = None
            self.AADevices          = None # AppleAcct_ic3 object for Apple Device Service used to refresh the device's location

            self.session_data       = {}
            self.dsid               = ''
            self.session_id         = ''
            self.trust_token        = ''
            self.trust_token_expire_in_days = HIGH_INTEGER
            self.session_token      = ''
            self.scnt               = ''
            self.client_id          = client_id or (f"auth-{str(uuid1()).lower()}")

            # login/setup error information
            self.error_codes  = ''
            self.error_secs   = 0
            self.error_reason = ''
            self.error_next_retry_secs = 0
            self.error_retry_cnt = 0

            # When True, icloud_io re-raises AppleAcctException instead of
            # returning an empty dict. Set only around a request whose caller
            # has a dedicated error branch for it.
            self.raise_api_errors = False

            add_log_file_filter(password)

            self._setup_iCloudSession()
            self._initialize_variables()

            # Lightweight Username/Password validation only. The session has been
            # set up so a SRP signin/init+signin/complete can be sent to verify
            # the credentials (see validate_upw_via_srp), but the full login,
            # data refresh and global AppleAcct registration are skipped.
            if srp_validate_only:
                return

            self.authenticate_and_refresh_data()

            Gb.AppleAcctLoggingInto = self    # Identifies a partial login that might have failed
            Gb.AppleAcct_by_username[username] = self
            Gb.AppleAcct_password_by_username[username] = password

            # A 421 may mean the cookies have expired an an authentication is
            # needed. But we do not exactly know yet
            if (self.is_authenticated is False
                    and self.response_code == 421):
                post_alert( f"Apple Acct > {self.username_base}, "
                            f"Resetting cookie and session files, "
                            f"Retrying Authentication and data refresh")
                self.delete_cookie_and_session_files()
                self._setup_iCloudSession()
                self._initialize_variables()
                self.authenticate_and_refresh_data()

        except Exception as err:
            log_exception(err)

        return

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
            self.get_trusted_devices()

            post_greenbar_msg(f"Apple Acct > {self.username_base}, Refresh Location Data")

            self.refresh_icloud_data(locate_all_devices=True)

            log_banner('finish', self.username_id)
            return True
        upw_msg = 'Invalid Username/Password, ' if self.response_code == 401 else ''
        self.setup_error(self.response_code)

        if self.validate_aa_upw is False:
            post_alert( f"Login or Authentication Failed, "
                    f"{upw_msg}{self.error_reason}, "
                    f"Server-{self.apple_server_location}, "
                    "Location data not refreshed")
            update_alert_sensor(self.username_id, f"Login Failed, {upw_msg}{self.error_reason}")

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

        self.was_ha_auth_code_alert_sent = False
        self.last_refresh_secs           = time_now_secs()
        self.token_auth_cnt              = 0
        self.last_token_auth_secs        = 0
        self.password_auth_cnt           = 0
        self.last_password_auth_secs     = 0

        self.response_code_pw            = 0
        self.login_successful            = False
        self.login_successful_srp        = None   # None=SRP not done, True=OK, False=Failed
        self.auth_failed_503             = False
        self.is_authenticated            = False  # ICloud access has been authenticated via pw or token

        self.trusted_phone_data          = []
        self.trusted_phone_number_by_devid = {}
        self.auth_type                   = 'hsa2'
        self.security_code_locked        = False
        self.security_code_cooldown      = False

        # AppleAcct tracking method and raw data control objects
        self.AADevData_by_device_id      = {}   # Device data for tracked devices, updated in Pyicloud icloud.refresh_client
        self.AADevData_items             = []   # List of all AADevData objects used to find non-tracked device data

        # iCloud Device information - These is used verify the device, display on the EvLog and in the Config Flow
        # device selection list on the iCloud3 Devices screen
        self.device_id_by_aadev_dname         = {}  # Example: {'Gary-iPhone': 'n6ofM9CX4j...'}
        self.aadev_dname_by_device_id         = {}  # Example: {'n6ofM9CX4j...': 'Gary-iPhone14'}
        self.device_info_by_aadev_dname       = {}  # Example: {'Gary-iPhone': 'Gary-iPhone (iPhone 14 Pro; iPhone15,2)'}
        self.device_model_name_by_aadev_dname = {}  # Example: {'Gary-iPhone': 'iPhone 14 Pro'}
        self.device_model_info_by_aadev_dname = {}  # {'Gary-iPhone': [raw_model, model, model_display_name]}
        self.dup_icloud_dname_cnt             = {}  # Used to create a suffix for duplicate devicenames
                                                    # {'Gary-iPhone': ['iPhone15,2', 'iPhone', 'iPhone 14 Pro']}
        self.first_name_by_prs_id             = {}  # Device owner's first name from the Apple device data
                                                    # {None: 'Gary', 'NDM0NTU2NzE3': 'Lillian'} (None=acct owner)

        # self.AppleAcct.AADevData_items                  = []
        # self.AppleAcct.aadev_dname_by_device_id         = {}
        # self.AppleAcct.device_id_by_aadev_dname         = {}
        # self.AppleAcct.device_info_by_aadev_dname       = {}
        # self.AppleAcct.device_model_info_by_aadev_dname = {}
        # self.AppleAcct.device_model_name_by_aadev_dname = {}


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
        try:
            return self.iCloudSession.response_code
        except:
            return 404

#---------------------------------------------------------------------------
    @property
    def response_ok(self):
        return self.iCloudSession.response_ok

#---------------------------------------------------------------------------
    # @property
    # def response_code_desc(self, code=None):
    #     if code is None:
    #         code = self.response_code
    #     return (f"{HTTP_RESPONSE_CODES.get(code, 'Other Error')}-"
    #             f"{self.response_code}")

#---------------------------------------------------------------------------
    @property
    def response_code_desc(self):
        return self.code_description(self.response_code)

#----------------------------------------------------------------------------
    def code_description(self, code):
        return f"{HTTP_RESPONSE_CODES.get(code, 'Other Error')} ({code})"

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

    @property
    def auth_methods(self)-> list[{dict}]:
        '''
        return the auth_methods list
        '''
        return self.conf_apple_acct[CONF_AUTH_METHODS]

    @property
    def current_auth_method(self):
        '''
        return the current auth_method
            - 'push'
            - 'text_1', 'text_2'
            - 'hwkey'
        '''

        return self.conf_apple_acct[CONF_AUTH_METHODS][CURRENT]

    @property
    def current_auth_method_value(self):
        '''
        return the last auth_method and it's info vlaue
            - 'push' = ''
            - 'text_1' = '**66'
            - 'hwkey' = 'green, pink'
        '''
        return self.conf_apple_acct[CONF_AUTH_METHODS].get(self.current_auth_method, '')

    def auth_method_value(self, auth_method):
        '''
        return the last auth_method and it's info vlaue
            - 'push' = ''
            - 'text_1' = '**66'
            - 'hwkey' = 'green, pink'
        '''
        return self.conf_apple_acct[CONF_AUTH_METHODS].get(auth_method, '')

    @property
    def is_auth_method_PUSH(self):
        return self.current_auth_method == PUSH

    @property
    def is_auth_method_TEXT(self):
        return self.current_auth_method.startswith(TEXT)

    @property
    def is_auth_method_HWKEY(self):
        return self.current_auth_method == HWKEY

    def update_auth_method(self, auth_method):
        '''
        Update the Apple Acct auth method info, Force HWKEY is their are security keys
        '''
        self.conf_apple_acct[CONF_AUTH_METHODS][HWKEY] = self.hwkey_names
        self.conf_apple_acct[CONF_AUTH_METHODS][CURRENT] = \
                            HWKEY if self.hwkey_names != '' else \
                            auth_method

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
        will force Apple to display a new Authentication code
        '''
        self.session_data       = {}
        self.session_data_token = {}
        self.session_token      = ''
        self.session_id         = ''
        self.trust_token        = ''

        self.authenticate()

    @property
    def tokenpw_filename(self):
        '''
        Token Password - This file stores the username's password associated with the session
        token and is used to determine if the password has changed and the session needs to be reset
        '''
        return path.join(self.cookie_directory, f"{self.cookie_username}.tpw")

    @property
    def tokenpw_filename_short(self):
        '''
        Token Password - This file stores the username's password associated with the session
        token and is used to determine if the password has changed and the session needs to be reset
        '''
        return  f"{self.cookie_username}.tpw"

    @property
    def authentication_method(self):
        return self.current_auth_method

    @property
    def login_failed(self):
        return (self.username in Gb.AppleAcct_error_by_username)

    @property
    def _check_2sa_needed(self):
        '''Returns True if two-step authentication is required.'''
        try:
            _is_reauth_needed = (self.data.get("dsInfo", {}).get("hsaVersion", 0) >= 1
                                    and (self.is_challenge_required or self.is_trusted_browser is False))

            return _is_reauth_needed

        except AttributeError:
            return False
        except:
            return False

    @property
    def _set_is_reauth_needed(self):
        '''
        Returns True if two-factor authentication is required. This is determined by the
        data["hsaChallengeRequired"] value.

        If it is needed, the 'is_reauth_needed_secs' is set to the current time.
        '''
        # if self.is_reauth_needed:
        #     return True

        try:
            _is_reauth_needed = (self.data.get("dsInfo", {}).get("hsaVersion", 0) == 2
                                    and (self.is_challenge_required or self.is_trusted_browser is False))
        except AttributeError:
            return False
        except Exception as err:
            log_exception(err)
            return False

        if _is_reauth_needed is False:
            self.is_reauth_needed_secs = 0
        else:
            if self.is_reauth_needed_secs == 0:
                self.is_reauth_needed_secs = time_now_secs()

            log_debug_msg(  f"{self.username_base}, "
                            f"NEEDS-2FA, "
                            f"ChallengeRequired-{self.is_challenge_required}, "
                            f"TrustedBrowser-{self.is_trusted_browser}")
        return _is_reauth_needed

    @property
    def is_challenge_required(self):
        '''Returns True if the challenge code is needed.'''
        return self.data.get("hsaChallengeRequired", False)

    @property
    def is_trusted_browser(self):
        '''Returns True if the session is trusted.'''
        return self.data.get("hsaTrustedBrowser", False)

    def new_log_in_needed(self, username):
        return username != self.username

    @property
    def aadevice_dnames(self):
        aadevice_dnames = [aadevice_dname
                    for aadevice_dname in self.device_id_by_aadev_dname.keys()]
        aadevice_dnames.sort()

        return aadevice_dnames

#----------------------------------------------------------------------------
    def _get_webservice_url(self, ws_key):
        '''Get webservice URL, raise an exception if not exists.'''
        try:
            if self.webservices.get(ws_key) is None:
                return None

            return self.webservices[ws_key]["url"]
        except:
            return None

#----------------------------------------------------------------------------
    def update_token_pw_valid_reauth_data(self):
        '''
        The Apple acct needs to be reauthenticated about every 90-days. Keep track of
        the last time this was done and use it as a basis
        '''

        self._update_token_pw('valid_reauth_method', self.current_auth_method)
        self._update_token_pw('valid_reauth_secs', time_now_secs())

#--------------------------------------------------------------------
    def issue_reauth_in_days_alert_msg(self, evlog_msg=False):
        '''
        Check to see if an Apple acct is approaching  it's
        reauthentication date. if it is,  issue an alert warning message
        '''
        reauth_in_days, reauth_msg = \
                self.get_next_reauth_in_days_info_msg(APPLE_ACCT_ALERT_MSG_REAUTH_DAYS)
        if (self.is_reauth_needed is False
                and reauth_in_days <= 10
                and reauth_msg is not None):
            alert_msg = (f"AppleAcct {reauth_msg}")
            update_alert_sensor(self.username_id, alert_msg)

            # if evlog_msg:
            return reauth_msg
#----------------------------------------------------------------------------
    def get_next_reauth_in_days_info_msg(self, in_days_filter=None):
        '''
        Get the number of days until the next reauthentication. If that value
        is in the 'in_days_filter', return the number of days and a message
        that can be posted to toe event log.

        in_days_filter:
            - list of days to display the message = [10, 20, 30]
            - a single day = 8
            - a range of days = -5 (display every day between 5 --> 0)

        return:
            - [number of days, days message] = [10, 'reauth in ~10 days']
            - [0, None] = no reauth in days information
        '''
        DAYS_90_SECS  = 7776000    # =90*86,400

        reauth_secs =  self.token_pw_data.get('valid_reauth_secs', None)
        if reauth_secs is None:
            # No reauth time/method field in token_pw. If filtering by days,
            # return so an alert will not be generated. Otherwise we are
            # just getting information
            if in_days_filter is not None:
                return (0, None)
            return (0, 'No Reauth Information')

        reauth_secs += DAYS_90_SECS

        reauth_method =  self.token_pw_data.get('valid_reauth_method', None)
        reauth_method = ''  if reauth_method is None \
                            else f"{AUTH_METHOD_FNAME.get(reauth_method, 'NoInfo')}"

        days_to_reauth =  int((reauth_secs - time_now_secs()) / 86400)
        reauth_date = format_date(reauth_secs)

        # Return the number of days and message
        if in_days_filter is None:
            if days_to_reauth < 0:
                return (abs(days_to_reauth),
                        f"Reauth {reauth_date}, overdue by ±{abs(days_to_reauth)} days")
            return (days_to_reauth, f"Reauth on {reauth_date} ({days_to_reauth} days)")

        # Prepare the filter list and see if the number of days is in the filter list
        if type(in_days_filter) is int: in_days_filter = [in_days_filter]

        # The reauth date has gone by
        if days_to_reauth < 0:
            return (abs(days_to_reauth), f"Reauth overdue by ±{abs(days_to_reauth)} days")

        # A negative item indicates a range of days from that day to 0, add them to the list
        in_days_range = [abs(in_days) for in_days in in_days_filter if in_days < 0]
        if isnot_empty(in_days_range):
            in_days_filter.extend(list(range(in_days_range[0])))
            in_days_filter = [abs(i) for i in in_days_filter]

        if days_to_reauth in in_days_filter:
            return (days_to_reauth, f"Reauth on {reauth_date} ({days_to_reauth} days)")

        return (0, None)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            PUSH NOTIFICATION AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def request_auth_code_via_push_notification(self):

        headers = self.get_auth_headers({"Accept": "application/json"})
        url     = f"{self.AUTH_ENDPOINT}/verify/trusteddevice/securitycode"

        icloud_io.put(self, url, headers=headers)

        # Apple answers this endpoint with a 202 (Accepted), not a 200/204
        return self.response_code in (200, 202, 204)

#----------------------------------------------------------------------------
    def validate_2fa_push_popup_window_code(self, code):
        '''Verifies a Authentication code received via Apple's 2FA system (HSA2).'''

        headers = self.get_auth_headers()      #{"Accept": "application/json"})
        url     = f"{self.AUTH_ENDPOINT}/verify/trusteddevice/securitycode"
        data    = {"securityCode": {"code": code}}

        try:
            data = icloud_io.post(self, url, data=data, headers=headers,)

        except AppleAcctAPIResponseException as error:
            # Wrong Authentication code
            if error.code == -21669:
                log_error_msg(  f"Apple Acct > {self.account_owner}, "
                                f"Incorrect Authentication Code")
                return False

        except Exception as err:
            log_exception(err)
            return False

        self.trust_session()

        self.is_reauth_needed = False
        self.is_reauth_needed = self._set_is_reauth_needed

        if self.is_reauth_needed:
            valid_msg = 'Rejected'
        else:
            # Code was accepted, Update reauth method and time
            valid_msg = 'Accepted'
            self.update_token_pw_valid_reauth_data()

        log_debug_msg(f"{self.username_base}, Auth Code {valid_msg}")
        post_greenbar_msg('')

        # Return true if 2fa code was successful
        return not self.is_reauth_needed


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TEXT MESSAGE AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def get_text_message_phone_numbers(self, auth_data=None):
        '''
        Extract the HSA2 trusted phone numbers from the /appleauth/auth response
        body and update the configuration file Text entries.
            - conf_apple_acct[text_1/text_2/etc] fields.

        auth_data - the /appleauth/auth body already fetched and shared by
            get_trusted_devices. When None (a standalone caller), it is fetched
            here, but only on the SRP 2FA-pending path (TrustToken returns 401).
        '''
        if auth_data is None:
            return

        # Baseline = last-known numbers cached in the token_pw (.tpw) file. A
        # TrustToken session that can not re-read them keeps the found values.
        self.trusted_phone_data = self.token_pw_data.get('trusted_phone_data', [])


        # if auth_data is None and self.login_successful_srp:
        #     try:
        #         auth_data = icloud_io.get(self, self.AUTH_ENDPOINT, headers=self.get_auth_headers())
        #         if self.response_code != 200:
        #             auth_data = None

        #     except Exception:
        #         auth_data = None


        # Apple's HSA2 trusted phone numbers:
        #   [{'id': 1, 'lastTwoDigits': '66', 'numberWithDialCode': ...}, ...]
        # Normalize to the internal {deviceId, phoneNumber} shape used below and
        # persisted to token_pw. Only overwrite the cached list on a real read so
        # an empty/failed fetch does not wipe previously discovered numbers.
        # if auth_data is not None:
        trusted_phone_numbers = (auth_data.get('trustedPhoneNumbers', [])
                                or  (auth_data.get('phoneNumberVerification', {})
                                                .get('trustedPhoneNumbers', [])))

        self.trusted_phone_data = [
                {'deviceId': phone['id'], 'phoneNumber': phone.get('lastTwoDigits', '')}
                for phone in trusted_phone_numbers]
        self._update_token_pw('trusted_phone_data', self.trusted_phone_data)

        # Delete and readd 'text_' items in case anything changed
        conf_auth_methods = self.conf_apple_acct[CONF_AUTH_METHODS]
        # If hwkeys are available, change last_method to 'hwkey'
        if (self.is_auth_method_HWKEY is False and conf_auth_methods[HWKEY] != ''):
            conf_auth_methods[CURRENT] = HWKEY

        # If hwkeys are not available, change last_method to 'push'
        if (self.is_auth_method_HWKEY and conf_auth_methods[HWKEY] == ''):
            conf_auth_methods[CURRENT] = PUSH

        # Clear Text_x phone number
        for auth_method, method_info in conf_auth_methods.items():
            if auth_method.startswith(TEXT):
                conf_auth_methods[auth_method] = ''

        # Reset Text_x phone numbers
        default_text_method = None
        for trusted_phone_item in self.trusted_phone_data:
            auth_method_key = f"text_{trusted_phone_item['deviceId']}"
            conf_auth_methods[auth_method_key] = f"**{trusted_phone_item['phoneNumber']}"
            if default_text_method is None:
                default_text_method = auth_method_key

        # Make sure text_1 is in the conf_auth_methods list
        if TEXT_1 not in self.auth_methods:
            conf_auth_methods[TEXT_1] = ''

        # Make sure last auth is still available if it is text
        last_auth_method = conf_auth_methods[CURRENT]
        if (last_auth_method.startswith(TEXT)
                and conf_auth_methods.get(last_auth_method, '')) == '':
            conf_auth_methods[CURRENT] = default_text_method or PUSH

        return


#----------------------------------------------------------------------------
    def request_auth_code_via_text_msg(self, auth_method):
        '''
        Request Apple send a 6-digit Text Authentication code to a trusted phone number.
        This is the hsa2 path. Use when the trusted device popup does not appear.

        phone_id: The 'id' value from trustedPhoneNumbers (defaults to first available)
        '''
        phone_id = int(auth_method[-1:])

        headers = self.get_auth_headers()
        url     = f"{self.AUTH_ENDPOINT}/verify/phone"
        data    = {"phoneNumber": {"id": phone_id}, "mode": "sms"}

        try:
            icloud_io.put(self, url, data=data, headers=headers)

            if self.response_code in (200, 202, 204):
                log_info_msg(f"{self.username_base}, Text Authentication Code sent to Phone-{phone_id}")
                return True

            # Apple accepted the request but refused to send the code. 423 is the
            # rate limiter - too many codes have been requested for this phone
            # number and Apple will not send another one for a while.
            log_error_msg(  f"{self.username_base}, Apple did not send the Text Authentication "
                            f"Code to Phone-{phone_id}, {self.response_code_desc}")

            return False

        except Exception as err:
            log_exception(err)

        return False

#----------------------------------------------------------------------------
    def validate_2fa_text_code(self, auth_code):
        '''
        Validate the Text Authentication code entered by the user (hsa2 phone path).
        This is separate from validate_2fa_code() which uses the trusted device path.
        '''
        self.iCloudSession.cookies.list()
        phone_id = int(self.current_auth_method[-1:])

        headers = self.get_auth_headers()
        url     = f"{self.AUTH_ENDPOINT}/verify/phone/securitycode"
        data    = {
            "phoneNumber":  {"id": phone_id},
            "securityCode": {"code": auth_code},
            "mode":         "sms"
        }

        try:
            icloud_io.post(self, url, data=data, headers=headers)

        except AppleAcctAPIResponseException as err:
            if err.code == -21669:
                log_error_msg(f"{self.username_base}, Incorrect Text Authentication Code")
            return False
        except Exception as err:
            log_exception(err)
            return False

        # Same trust+relogin sequence as validate_2fa_code()
        self.trust_session()

        self.is_reauth_needed = self._set_is_reauth_needed

        if self.is_reauth_needed is False:
            self.update_token_pw_valid_reauth_data()

        return not self.is_reauth_needed

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            TRUSE/UNTRUST SESSION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def trust_session(self):
        '''
        Request session trust to avoid user log in going forward
        '''
        url     = f"{self.AUTH_ENDPOINT}/2sv/trust"
        headers = self.get_auth_headers()

        try:
            icloud_io.get(self, url, headers=headers)

            if self._authenticate_with_token():
                self.is_reauth_needed = self._set_is_reauth_needed
            return True

        except AppleAcctAPIResponseException:
            log_error_msg("Session trust failed")
            self.is_reauth_needed = self._set_is_reauth_needed

        return False

#----------------------------------------------------------------------------
    # The idmsa signin session identifiers. The 'aasp' cookie IS the signin
    # session id (the same value Apple returns in the X-Apple-ID-Session-Id
    # header) and scnt/session_id are its header form.
    SRP_SIGNIN_SESSION_COOKIES = ['aasp']
    SRP_SIGNIN_SESSION_DATA    = ['scnt', 'session_id']

    def clear_srp_signin_session(self):
        '''
        Drop the idmsa signin session identifiers so the next signin/init opens
        a NEW auth session.

        get_auth_headers re-attaches session_id/scnt to every /appleauth/auth
        request. Apple's signin/init only starts a new auth session when the
        request does not already identify one, so if those identifiers still
        point at a session that is sitting at the 2FA step (or one that has
        already been spent), Apple continues THAT session instead of opening a
        fresh one - and then refuses the new M1 proof posted by signin/complete
        with a 401 even though the password is correct.

        delete_cookie_and_session_files() removes the files but not the values
        already read into session_data, so this has to be done separately.
        '''
        try:
            self.scnt       = ''
            self.session_id = ''
            for session_data_item in self.SRP_SIGNIN_SESSION_DATA:
                dict_del(self.session_data, session_data_item)

            if self.iCloudSession is None:
                return

            cookies = self.iCloudSession.cookies
            cleared_cookies = [ cookie_name
                                for cookie_name in self.SRP_SIGNIN_SESSION_COOKIES
                                if cookies.delete(cookie_name)]
            if cleared_cookies:
                cookies.save()

            log_debug_msg(  f"{self.username_base}, Cleared SRP Signin Session, "
                            f"Cookies-{cleared_cookies}")

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def untrust_session(self):
        '''
        Initialize the session file and authenticate the apple account access. This
        will force Apple to display a new Authentication code
        '''
        if secs_since(self.srp_valid_upw_secs) < SRP_SIGNIN_TOKEN_INFO_MAX_AGE_SECS:
            return

        self.session_data['session_token'] = ''
        self.session_data['trust_token']   = ''
        self.session_token = ''
        self.trust_token   = ''

        self.delete_trust_cookie()
        self.clear_srp_signin_session()

#----------------------------------------------------------------------------
    def untrust_session_and_authenticate(self):
        '''
        Initialize the session file and authenticate the apple account access. This
        will force Apple to display a new Authentication code
        '''

        self.session_data['session_token'] = ''
        self.session_data['trust_token']   = ''
        self.session_token = ''
        self.trust_token   = ''

        self.delete_trust_cookie()

        # The password sign-in that follows must open a brand new idmsa signin
        # session - the one identified by the current session_id/scnt/aasp is
        # either spent or stuck at the 2FA step and Apple will refuse it (401)
        self.clear_srp_signin_session()

        self.authenticate()

#----------------------------------------------------------------------------
    # The trusted session values (session/trust tokens, session_id, scnt, etc)
    # are persisted in token_pw_data and the [username].tpw file. They can be
    # snapshotted and restored to re-establish a trusted session.
    TRUSTED_SESSION_KEYS = ['session_token', 'trust_token', 'session_id',
                            'scnt', 'account_country', 'dsid']

    def snapshot_trusted_session(self):
        '''
        Return a copy of the persisted trusted-session values from token_pw_data
        so they can be restored later (see restore_trusted_session). Used before
        a forced password sign-in that would otherwise overwrite them.
        '''
        return {key: self.token_pw_data.get(key)
                    for key in self.TRUSTED_SESSION_KEYS}

#----------------------------------------------------------------------------
    def restore_trusted_session(self, saved_session):
        '''
        Re-establish the trusted session from values previously captured by
        snapshot_trusted_session. Authenticates with the saved trust token
        which, if still valid, re-issues the X-APPLE-WEBAUTH-HSA-TRUST cookie
        and avoids forcing the user back into a 2FA prompt.

        Return:
            True  - Trusted session restored
            False - Saved trust token no longer valid (account remains NEEDS-2FA)
        '''
        if is_empty(saved_session.get('trust_token')):
            return False

        for key, value in saved_session.items():
            if value is not None:
                self.session_data[key] = value
                self.token_pw_data[key] = value

        self.session_token = saved_session.get('session_token', '')
        self.trust_token   = saved_session.get('trust_token', '')

        login_successful = self._authenticate_with_token()
        self.is_reauth_needed = self._set_is_reauth_needed

        log_debug_msg(f"{self.username_base}, Restore Trusted Session > "
                        f"Successful-{login_successful}, 2fa Needed-{self.is_reauth_needed}")

        return login_successful


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#            HARDWARE KEY (FIDO2) AND SOFTWARE KEY AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def get_hwkey_names(self, auth_data=None):
        '''
        Get the registered hardware key names from Apple (AUTH_ENDPOINT GET) from the data received
        from Apple. Then extract them and update the configuration file HwKey entries.
            - conf_apple_acct[CONF_AUTH_METHODS][HWKEY] field.

        auth_data - the /appleauth/auth body already fetched and shared by
            get_trusted_devices. When None (a standalone caller), it is fetched
            here on the SRP 2FA-pending path.
        '''
        if Gb.hwkey_authentication_enabled is False:
            return False

        self.hwkey_names = self.auth_methods.get(HWKEY, '')

        # /appleauth/auth only returns keyNames when a fresh SRP sign-in has put
        # the idmsa session into the 2FA-pending (409) state. On the TrustToken
        # path it always returns 401, so keep the cached value (auth_method_value)
        # instead of overwriting it with an empty result.
        if auth_data is None and self.login_successful_srp:
            data = icloud_io.get(self, self.AUTH_ENDPOINT,
                                    headers=self.get_auth_headers())
            if self.response_code == 200:
                auth_data = data

        # A 200 response is the authoritative account state. An empty or
        # absent keyNames means the security keys were removed from the Apple
        # Account, so reset hwkey_names to '' rather than keeping the stale
        # cached value. Only the non-200 (401 TrustToken) path keeps the cache.
        if auth_data is not None:
            self.hwkey_names = list_to_str(auth_data.get('keyNames') or [])

        self.token_pw_data[HWKEY] = self.hwkey_names
        self._write_token_pw_file()

        return True

#............................................................................
    def refresh_hwkey_names_preserve_trust(self):
        '''
        Refresh the registered security key (hwkey) names without permanently
        losing the trusted session.

        Reading the key names requires Apple's /appleauth/auth 2FA-challenge
        state, which can only be reached by a password (SRP) sign-in that is not
        backed by a trust token. That sign-in puts the account into a NEEDS-2FA
        state. To avoid forcing the user to re-enter a 2FA code, the trusted
        session values (persisted in token_pw_data/.tpw) are snapshotted before
        the sign-in and restored afterward via a TrustToken authentication.

        Return:
            True - hwkey names refreshed (self.hwkey_names updated)
        '''
        # Snapshot before the forced password sign-in overwrites these values
        saved_session = self.snapshot_trusted_session()
        was_trusted   = isnot_empty(saved_session.get('trust_token'))

        # Force the 2FA-challenge state and read the key names from /appleauth/auth
        # (untrust_session_and_authenticate runs PasswordSRP which sets
        # login_successful_srp, so get_hwkey_names will query the auth endpoint).
        self.untrust_session_and_authenticate()
        self.get_hwkey_names()

        # Restore the trusted session so the user is not knocked into a 2FA prompt.
        # Must run after get_hwkey_names (re-trusting makes /appleauth/auth 401).
        if was_trusted:
            self.restore_trusted_session(saved_session)

        return True

#--------------------------------------------------------------------
    # def get_webauthn_options(self):

    #     url     = self.AUTH_ENDPOINT
    #     headers = self.get_auth_headers()

    #     data    = icloud_io.get(self, url, headers=headers)

    #     return data

#............................................................................
    def authenticate_with_hwkey(self):
        '''
        Authenticate sign-on using a security key
        '''

        self.hwkey_auth_status = False
        self.hwkey_auth_status = self.HwKey.security_key_assertion_ceremony(self.hwkey_names)

        # Update reauth method and time
        if self.hwkey_auth_status:
            self.update_token_pw_valid_reauth_data()

        return self.hwkey_auth_status


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
            return self.username_account_owner
        except:
            return "<NotSetUp>"

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#       EXCEPTION HANDLERS
#
#   The Apple Acct exception classes live in exceptions.py. They are imported
#   at the top of this module and re-exported under their original names.
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
