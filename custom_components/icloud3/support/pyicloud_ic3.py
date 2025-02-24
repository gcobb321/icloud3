
'''
Customized version of pyicloud.py to support iCloud3 Custom Component

Platform that supports importing data from the iCloud Location Services
and Find My Friends api routines. Modifications to pyicloud were made
by various people to include:
    - Original pyicloud - picklepete & Quantame
                        - https://github.com/picklepete

    - Updated and maintained by - Quantame
    - 2fa developed by          - Niccolo Zapponi (nzapponi)
    - Find My Friends component - Z Zeleznick

The picklepete version used imports for the services, utilities and exceptions
modules. They are now maintained by Quantame and have been modified by
Niccolo Zapponi Z Zeleznick.
These modules and updates have been incorporated into the pyicloud_ic3.py version
used by iCloud3.
'''

from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_FNAME, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS,
                                    HHMMSS_ZERO, RARROW, PDOT, CRLF, CRLF_DOT, CRLF_STAR, CRLF_CHK, CRLF_HDOT,
                                    ICLOUD, NAME, ID,
                                    APPLE_SERVER_ENDPOINT,
                                    ICLOUD_HORIZONTAL_ACCURACY,
                                    LOCATION, TIMESTAMP, LOCATION_TIME, DATA_SOURCE,
                                    ICLOUD_BATTERY_LEVEL, ICLOUD_BATTERY_STATUS, BATTERY_STATUS_CODES,
                                    BATTERY_LEVEL, BATTERY_STATUS, BATTERY_LEVEL_LOW,
                                    ICLOUD_DEVICE_STATUS, DEVICE_STATUS_CODES,
                                    CONF_USERNAME, CONF_APPLE_ACCOUNT,
                                    CONF_PASSWORD, CONF_MODEL_DISPLAY_NAME, CONF_RAW_MODEL,
                                    CONF_IC3_DEVICENAME, CONF_FNAME, CONF_FAMSHR_DEVICENAME,
                                    CONF_FAMSHR_DEVICE_ID, CONF_LOG_LEVEL_DEVICES,
                                    )
from ..helpers.common       import (instr, is_empty, isnot_empty, list_add, list_del,
                                    encode_password, decode_password, get_username_base, )
from ..helpers.file_io      import (delete_file, read_json_file, save_json_file, file_exists, )
from ..helpers.time_util    import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..helpers.messaging    import (post_event, post_monitor_msg, post_startup_alert, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_rawdata, log_exception, log_rawdata_unfiltered, filter_data_dict, )
from ..support              import pyicloud_session as pyi_session   #(PyiCloudSession, PyiCloudPasswordFilter)

from ..support              import pyicloud_srp as srp
# import srp

from uuid       import uuid1
from os         import path
from re         import match
import hashlib
import base64
import json
import http.cookiejar as cookielib
import logging
LOGGER = logging.getLogger(f"icloud3.pyicloud_ic3")

HEADER_DATA = {
    "X-Apple-ID-Account-Country": "account_country",
    "X-Apple-ID-Session-Id": "session_id",
    "X-Apple-Session-Token": "session_token",
    "X-Apple-TwoSV-Trust-Token": "trust_token",
    "scnt": "scnt",
}

HEADERS_SRP = {
    "Accept": "application/json, text/javascript",
    'referer':'https://www.apple.com/',
}
HEADERS_NON_SRP = {
    "Accept": "*/*",
}
HEADERS = {
    "Accept": "*/*",
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
    -2:  'Apple Server not Available (Connection Error)',
    200: 'iCloud Server Response',
    201: 'Device Offline',
    204: 'Verification Code Accepted',
    302: 'Apple Server not Available (Connection Refused or Other Error)',
    400: 'Invalid Verification Code',
    401: 'INVALID USERNAME/PASSWORD',
    403: 'Verification Code Requested',
    404: 'Apple http Error, Web Page not Found',
    409: 'Valid Username/Password',
    421: 'Verification Code May Be Needed',
    421.1: 'INVALID USERNAME/PASSWORD',
    450: 'Verification Code May Be Needed',
    500: 'Verification Code May Be Needed',
    503: 'Apple Server Refused Password Validation Request, Retry Later',
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

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   CHECK APPLE ACCOUNT USERNAME/PASSWORD
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class PyiCloudValidateAppleAcct():
    '''
    Use the Apple Acct Validation url to validate the username/password
    '''

    def __init__(self):
        self.validate_aa_upw = True
        self.username = 'validate_upw'
        self.password = 'validate_upw'


        self.client_id = f"auth-{str(uuid1()).lower()}"

        self.ValidationPyiCloudSession = pyi_session.PyiCloudSession(self, validate_aa_upw=True)
        self.ValidationPyiCloud        = PyiCloudService(   self.username,
                                                            self.password,
                                                            apple_server_location='usa',
                                                            validate_aa_upw=True)

        # self.AUTH_ENDPOINT   = "https://idmsa.apple.com/appleauth/auth"

        self.response_code       = 0
        self.last_response_code  = 0



#----------------------------------------------------------------------------
    def is_internet_available(self):
        try:
            if Gb.internet_connection_status_waiting_for_response:
                log_debug_msg(  f"Wait for Internet Connection response, "
                                f"Sent-{format_age(Gb.internet_connection_status_request_secs)}")
                return False

            Gb.internet_connection_status_request_cnt += 1
            Gb.internet_connection_status_request_secs = time_now_secs()

            is_internet_available = self.ValidationPyiCloudSession.is_internet_available()

            log_debug_msg(  f"Received Internet Connection status, "
                            f"Available-{is_internet_available}")

            return is_internet_available

        except Exception as err:
            log_exception(err)
            return False

#----------------------------------------------------------------------------
    def validate_username_password(self, username, password):
        '''
        Check if the username and password are still valid
        The response code indicates the validity status (checked in the Session module)
            code=409 is valid
            code=401 is invalid
        '''

        self.ValidationPyiCloud.__init__(username, password, validate_aa_upw=True)

        self.username = username
        self.password = password
        self.username_base = get_username_base(self.username)

        self.session_data  = ''      #Dummy statement for PyiCloudSession
        self.session_id    = ''      #Dummy statement for PyiCloudSession
        self.instance      = ''      #Dummy statement for PyiCloudSession

        log_debug_msg(f"{self.username_base}, Validate Username/Password")
        aa_cookie_files_exist = file_exists(self.ValidationPyiCloud.cookie_dir_filename)

        method = 'TokenPW Session Token'
        valid_upw = self._validate_with_tokenpw_file(username, password)
        log_debug_msg(f"{self.username_base}, Method-{method}, Results-{valid_upw}")

        if valid_upw is False:
            method = 'setup/authenticate URL'
            valid_upw = self.validate_with_verify_via_url(username, password)
            log_debug_msg(f"{self.username_base}, Method-{method}, Results-{valid_upw}")

        if valid_upw is False:
            method = 'Authenticate'
            valid_upw = self.validate_with_authenticate(username, password)
            log_debug_msg(f"{self.username_base}, Method-{method}, Results-{valid_upw}")

        if valid_upw is False:
            method = 'AllTestsFailed'
            if aa_cookie_files_exist is False:
                delete_file(self.ValidationPyiCloud.cookie_dir_filename)
                delete_file(self.ValidationPyiCloud.session_dir_filename)

        log_debug_msg(  f"{self.username_base}, Validate Username/Password, "
                        f" Method-{method}, Result-{valid_upw}")

        return valid_upw

#----------------------------------------------------------------------------
    def _validate_with_tokenpw_file(self, username, password):
        return False

        token_pw_data = self.ValidationPyiCloud.read_token_pw_file()

        if (isnot_empty(token_pw_data)
                and decode_password(token_pw_data.get(CONF_PASSWORD, '')) == password
                and 'session_token' in token_pw_data):
            return True

        return False

#----------------------------------------------------------------------------
    def validate_with_verify_via_url(self, username, password):
        '''
        Verify username/password with the 'authenticate' url
        Return:
            response_code:
                = 409 - Valid
                = 401 - Not Valid

        Note:
            China suffix is not needed for this
        '''

        username_password = f"{username}:{password}"
        upw = username_password.encode('ascii')
        username_password_b64 = base64.b64encode(upw)
        username_password_b64 = username_password_b64.decode('ascii')

        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Apple-iCloud/9.0 (Macintosh; Intel Mac OS X 10_15_1) AppleWebKit/605.1.15 (KHTML, like Gecko)',
            'Authorization': f"Basic {username_password_b64}"}
        # url  = f"https://setup.icloud.com/setup/authenticate/{self.username}"
        url  = f"{APPLE_SERVER_ENDPOINT['auth_url']}/{self.username}"
        data = None

        response_code = self.ValidationPyiCloudSession.post(url, data=data, headers=headers)

        valid_upw = True if response_code == 409 else False
        return valid_upw

#----------------------------------------------------------------------------
    def validate_with_authenticate(self, username, password):

        valid_upw = self.ValidationPyiCloud.authenticate()        #username, password)

        return valid_upw

#............................................................................
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"




# From GitHub iLoot iloot.py
# def download_backup(login, password, output_folder, types, chosen_snapshot_id, combined, itunes_style, domain, threads, keep_existing):
#     print 'Working with %s : %s' % (login, password)
#     print 'Output directory :', output_folder

#     auth = "Basic %s" % base64.b64encode("%s:%s" % (login, password))
#     authenticateResponse = plist_request("setup.icloud.com", "POST", "/setup/authenticate/$APPLE_ID$", "", {"Authorization": auth})
#     if not authenticateResponse:
#         # There was an error authenticating the user.
#         return

#     dsPrsID = authenticateResponse["appleAccountInfo"]["dsPrsID"]
#     auth = "Basic %s" % base64.b64encode("%s:%s" % (dsPrsID, authenticateResponse["tokens"]["mmeAuthToken"]))

#     headers = {
#         'Authorization': auth,
#         'X-MMe-Client-Info': CLIENT_INFO,
#         'User-Agent': USER_AGENT_UBD
#     }
#     account_settings = plist_request("setup.icloud.com", "POST", "/setup/get_account_settings", "", headers)
#     auth = "X-MobileMe-AuthToken %s" % base64.b64encode("%s:%s" % (dsPrsID, authenticateResponse["tokens"]["mmeAuthToken"]))


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PyiCloud_RawData Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable PyiCloud.RawData_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class PyiCloudService():
    '''
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    '''

    def __init__(   self, username, password=None,
                    apple_server_location=None,
                    locate_all_devices=None,
                    cookie_directory=None,
                    session_directory=None,
                    validate_aa_upw=False,
                    config_flow_login=False):

        try:
            if validate_aa_upw is False:
                pass
            elif is_empty(username):
                msg = "Apple Account username is not specified/558"
                raise PyiCloudFailedLoginException(msg)
            elif is_empty(password):
                msg = "Apple Account password is not specified/562"
                raise PyiCloudFailedLoginException(msg)

            self.setup_time     = time_now()
            self.user           = {"accountName": username, "password": password}
            self.apple_id       = username
            self.username       = username
            self.username_base  = username.split('@')[0]
            self.username_base6 = self.username_base if Gb.log_debug_flag else f"{username[:6]}…"

            self.validate_aa_upw = validate_aa_upw

            password = decode_password(password)
            self.password = password

            username_password = f"{username}:{password}"
            upw = username_password.encode('ascii')
            username_password_b64 = base64.b64encode(upw)
            self.username_password_b64 = username_password_b64.decode('ascii')

            self.locate_all_devices  = locate_all_devices if locate_all_devices is not None else True

            self.is_authenticated    = False        # ICloud access has been authenticated via password or token
            self.login_successful    = False
            self.auth_failed_503     = False
            # self.requires_2sa        = self._check_2sa_needed
            self.requires_2fa        = False        # This is set during the authentication function
            self.response_code_pwsrp_err = 0
            self.response_code       = 0
            self.last_response_code  = 0
            self.last_request_secs   = 0            # Keep the last time an internet request was made. Check time since
                                                    # in icloud3_main. Longer than 1-minute indicates internet is down.
            self.token_pw_data       = {}
            self.token_password      = password
            self.account_locked      = False        # set from the locked data item when authenticating with a token
            self.account_name        = ''
            self.account_country_code = ''          # accountCountryCode fro data when token was refreshed

            self.config_flow_login   = config_flow_login  # Indicates this PyiCloud object is beinging created from config_flow
            self.verification_code   = None
            self.authentication_alert_displayed_flag = False
            self.update_requested_by = ''

            self.apple_server_location = 'usa' if apple_server_location is None else apple_server_location
            self._setup_apple_server_url()

            self.cookie_directory    = cookie_directory or Gb.icloud_cookie_directory
            self.session_directory   = session_directory or Gb.icloud_session_directory
            self.cookie_filename     = "".join([c for c in self.username if match(r"\w", c)])
            self.findme_url_root = None # iCloud url initialized from the accountLogin response data


            self.PyiCloudSession    = None
            self.DeviceSvc          = None # PyiCloud_ic3 object for Apple Device Service used to refresh the device's location


            self.session_data       = {}
            self.session_data_token = {}
            self.dsid               = ''
            self.trust_token        = ''
            self.session_token      = ''
            self.session_id         = ''
            self.client_id          = f"auth-{str(uuid1()).lower()}"

            add_log_file_filter(password)
            self._setup_PyiCloudSession()

            self._initialize_variables()

            # Done if setting up ValidatePyiCloud used to verify username/password
            if validate_aa_upw is True:
                return

            Gb.PyiCloudLoggingInto = self    # Identifies a partial login that failed
            Gb.PyiCloud_by_username[username] = self

            self.login_successful = self.authenticate()
            if self.login_successful:
                self.refresh_icloud_data(locate_all_devices=True)
            else:
                err_msg = ( f"Apple Acct > {self.username_base}, Login Failed, "
                            f"{self.response_code_desc}, "
                            f"AppleServerLocation-`{self.apple_server_location}`, "
                            "Location Data not Refreshed")
                post_error_msg(err_msg)

        except Exception as err:
            log_exception(err)

        return

#----------------------------------------------------------------------------
    def _initialize_variables(self):
        '''
        Initialize the PyiCloud variables
        '''

        log_info_msg(f"{self.username_base}, Initialize PyiCloud Service, Set up iCloud Location Services connection")

        self.data      = {}
        #self.client_id = f"auth-{str(uuid1()).lower()}"
        self.params    = {  "clientBuildNumber": "2021Project52",
                            "clientMasteringNumber": "2021B29",
                            "ckjsBuildVersion": "17DProjectDev77",
                            "clientId": self.client_id[5:],  }

        self.new_2fa_code_already_requested_flag = False
        self.last_refresh_secs       = time_now_secs()
        self.token_auth_cnt          = 0
        self.last_token_auth_secs    = 0
        self.password_auth_cnt       = 0
        self.last_password_auth_secs = 0

        # PyiCloud tracking method and raw data control objects
        self.RawData_by_device_id        = {}   # Device data for tracked devices, updated in Pyicloud icloud.refresh_client
        self.RawData_items               = []   # List of all RawData objects used to find non-tracked device data

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
    def is_DeviceSvc_setup_complete(self):
        return (self.findme_url_root is not None)

#---------------------------------------------------------------------------
    @property
    def response_code_desc(self):
        desc = HTTP_RESPONSE_CODES.get(self.response_code, 'Unknown Error')
        return f"Error-{self.response_code}, {desc}"


#---------------------------------------------------------------------------
    @property
    def account_owner_username(self):
        if self.account_name:
            return f"{self.account_name} ({self.username_base})"

        return f"{self.username_base6}"

    @property
    def account_owner(self):
        name = self.account_name or self.username_base6
        return f"{name}"

    @property
    def account_owner_short(self):
        if len(self.account_owner) <= 30:
            return self.account_owner
        else:
            return f"{self.account_owner[:30]}…"

    @property
    def account_owner_username_short(self):
        if len(self.account_owner) <= 30:
            return self.account_owner_username
        else:
            return f"{self.account_owner_username[:30]}…"

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
            True - This is the primary Apple Account' PyiCloud object
        '''
        return Gb.conf_apple_accounts[0][CONF_USERNAME] == self.username

#----------------------------------------------------------------------------
    def authenticate(self, refresh_session=False):
        '''
        Handles authentication, and persists cookies so that
        subsequent logins will not cause additional e-mails from Apple.
        '''

        login_successful = False
        self.auth_method = ""
        self.response_code_pwsrp_err = 0
        self.auth_failed_503 = False

        # Do not reset requires_2fa flag on a reauthenticate session
        # It may have been set on first authentication
        if refresh_session is False:
            self.requires_2fa = False

        self.requires_2fa = self.requires_2fa or self._check_2fa_needed

        # Validate token - Consider authenticated if token is valid (POST=validate)
        if (refresh_session is False
                and self.session_data.get('session_token')
                and 'dsid' in self.params):
            log_info_msg(f"{self.username_base}, Validate Token")

            self.auth_method = "ValidToken"
            login_successful = self._validate_token()
            # if login_successful: self.auth_method = "Token"

        # Authenticate - Sign into Apple Account (POST=/signin)
        if login_successful is False:
            log_info_msg(f"{self.username_base}, Authenticate with Token")

            self.auth_method = "GetNewToken"
            login_successful = self._authenticate_with_token()

        if login_successful is False:
            log_info_msg(f"{self.username_base}, Authenticate with Password")
            self.auth_method = 'Password'
            login_successful = self.authenticate_with_password()

            # The Auth with Token is necessary to fill in the findme_url
            if login_successful:
                login_successful = self._authenticate_with_token()

        # if login_successful is False:
        #     log_info_msg(f"{self.username_base}, Authenticate with Password SRP")
        #     login_successful = self.authenticate_with_password_srp()

        #     self.response_code_pwsrp_err = self.response_code
        #     if login_successful:

        #     # The Auth with Token is necessary to fill in the findme_url
        #     if login_successful:
        #         self.auth_method = 'PasswordSRP'
        #         self._authenticate_with_token()


        if login_successful is False:
            if self.response_code == 200:
                self.response_code = self.last_response_code

            err_msg = f"{self.username_base}, Authentication Failed, "
            if self.response_code == 302:
                err_msg += (f"Apple Server Location-`{self.apple_server_location}`, "
                            f"{HTTP_RESPONSE_CODES[302]}, ")

            elif (self.auth_method == 'PasswordSRP'
                    and self.response_code == 401):
                valid_upw = Gb.PyiCloudValidateAppleAcct.validate_username_password(
                                            self.username, self.password)
                if valid_upw:
                    err_msg += (f"Python SRP Library Credentials Error"
                                f"{more_info('password_srp_error')}")
                else:
                    err_msg += "Authentication error, Invalid Username or Password, "

            elif (self.auth_method == 'PasswordSRP'
                    and (self.response_code == 503
                        or self.response_code_pwsrp_err == 503)):
                self.auth_failed_503 = True
                self.response_code = 503
                list_add(Gb.username_pyicloud_503_connection_error, self.username)
                err_msg += self.response_code_desc

            elif self.response_code == 421:
                err_msg += f"AuthMethod-{self.auth_method}, "
                if self.auth_method == 'Password':
                    self.response_code = 421.1
                    err_msg += "Invalid Username or Password, "
                else:
                    err_msg += ("Invalid Token, Verification Code May be Needed")
            else:
                err_msg += "An unknown error occurred, "

            if self.response_code not in [200, 409]:
                err_msg += f"ErrorCode-{self.response_code}"

                #log_info_msg(err_msg)
                log_info_msg(f"{err_msg}")
                self.is_authenticated = False
                return False
                # raise PyiCloudFailedLoginException(err_msg)

        self.requires_2fa = self.requires_2fa or self._check_2fa_needed

        self._update_token_pw_file(CONF_PASSWORD, encode_password(self.token_password))

        time_between_token_auth    = format_age(self.last_token_auth_secs)
        time_between_password_auth = format_age(self.last_password_auth_secs)
        if instr(self.auth_method, 'Token'):
            self.token_auth_cnt += 1
            self.last_token_auth_secs = time_now_secs()
        elif instr(self.auth_method, 'Password'):
            self.password_auth_cnt += 1
            self.last_password_auth_secs = time_now_secs()

            post_event( f"{EVLOG_NOTICE}Apple Acct Password Auth > {self.account_owner}, "
                        f"#{self.password_auth_cnt} ({time_between_password_auth}), "
                        f"{CRLF_DOT}{apple_server_time()}")

        post_monitor_msg(   f"Apple Acct > {self.account_owner} Authentication >, "
                            f"{self.auth_method}, "
                            f"TokenAuth-#{self.token_auth_cnt} ({time_between_token_auth}), "
                            f"PasswordAuth-#{self.password_auth_cnt} ({time_between_password_auth})")

        self.is_authenticated = self.is_authenticated or login_successful

        return self.is_authenticated



#----------------------------------------------------------------------------
    def _authenticate_with_token(self):
        '''Authenticate using session token. Return True if successful.'''

        this_fct_error_flag = True

        if "session_token" in self.session_data:
            self.account_country_code = self.session_data.get("account_country", "")
            data = {"accountCountryCode": self.session_data.get("account_country"),
                    "dsWebAuthToken": self.session_data.get("session_token"),
                    "extended_login": True,
                    "trustToken": self.session_data.get("trust_token", ""),
                    "appName": "iCloud3"}
        else:
            self.response_code = 421
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with Token > Failed, Invalid Session Data")
            return False

        try:
            url = f"{self.SETUP_ENDPOINT}/accountLogin"

            self.data = self.PyiCloudSession.post(url, params=self.params, data=data)

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
                    self._update_token_pw_file('dsid', self.params)

                if 'fullName' in self.data['dsInfo']:
                    self.account_name   = self.data['dsInfo']['fullName'].replace(' ', '')
                    self.account_locked = self.data['dsInfo']['locked']

            if 'webservices' in self.data:
                try:
                    if self.is_DeviceSvc_setup_complete is False:
                        self.findme_url_root = data['webservices']['findme']['url']
                        self._update_token_pw_file('findme_url', self.findme_url_root)
                except:
                    pass

            elif (self.data.get('success', False) is False
                    or self.data.get('error', 1) == 1):
                return False

            self._update_token_pw_file('session_id', self.session_data_token)
            self._update_token_pw_file('session_token', self.session_data_token)
            self._update_token_pw_file('trust_token', self.session_data_token)

            list_del(Gb.username_pyicloud_503_connection_error, self.username)

            # log_debug_msg( f"{self.username_base}, Authenticate with Token > Successful")
            return True

        except PyiCloudAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with Token > Token is not valid, "
                            f"Error-{err}, 2fa Needed-{self.requires_2fa}")
            return False

        except Exception as err:
            log_exception(err)
            if this_fct_error_flag is False:
                log_exception(err)
                return

        return False

#----------------------------------------------------------------------------
    def authenticate_with_password(self):
        '''
        Sign into Apple account with password. This can be called by:
            - the verify_username_password fct in PyiCloudValidateAppleAcct
            - the authenticate fct in PyiCloudService

        Return:
            True - Successful login
            False - Invalid Password or other error
        '''
        headers = self._get_auth_headers()

        url = f"{self.AUTH_ENDPOINT}/signin"
        params = {"isRememberMeEnabled": "true"}
        data = {"accountName": self.username,
                "password": self.password,
                "rememberMe": True,
                "trustTokens": []}
        if self.session_data.get("trust_token"):
            data["trustTokens"] = [self.session_data_token.get("trust_token")]

        try:
            self.data = self.PyiCloudSession.post(url, params=params, data=data, headers=headers,)

            return ('session_token' in self.session_data)

        except PyiCloudAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with password > Failed, Password is not valid, "
                            f"Error-{err}")     #, 2fa Needed-{self.requires_2fa}")
            raise PyiCloudFailedLoginException()

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

        # srp uses the encoded password at process_challenge(), thus set_encrypt_info() should be called before that
        class SrpPassword():
            def __init__(self, password: str):
                self.pwd = password

            def set_encrypt_info(self, protocol: str, salt: bytes, iterations: int) -> None:
                self.protocol = protocol
                self.salt = salt
                self.iterations = iterations

            def encode(self) -> bytes:
                password_hash = hashlib.sha256(self.pwd.encode())
                password_digest = password_hash.hexdigest().encode() if self.protocol == 's2k_fo' else password_hash.digest()
                key_length = 32
                return hashlib.pbkdf2_hmac('sha256', password_digest, self.salt, self.iterations, key_length)

        # Step 1: client generates private key a (stored in srp.User) and public key A, sends to server
        log_info_msg(f"{self.username_base}, Authenticating with Password SRP, signin/init, Calculate and send private key")

        srp_password = SrpPassword(password)
        srp.rfc5054_enable()
        srp.no_username_in_x()
        usr = srp.User(username, srp_password, hash_alg=srp.SHA256, ng_type=srp.NG_2048)
        uname, A = usr.start_authentication()

        headers = self._get_auth_headers()
        headers["Accept"] = "application/json, text/javascript"

        url  = f"{self.AUTH_ENDPOINT}/signin/init"
        data = {
            'a': base64.b64encode(A).decode(),
            'accountName': uname,
            'protocols': ['s2k', 's2k_fo']
        }

        try:
            response = self.PyiCloudSession.post(url, data=data, headers=headers)

        except PyiCloudAPIResponseException as error:
            msg = "SRP Authentication Failed"
            raise PyiCloudFailedLoginException(msg, error) from error
        except Exception as err:
            post_error_msg(f"SRP Authentication Failed > {err}")

        try:
            data = response.json()
        except Exception as err:
            data = {}

        if 'salt' not in data:
            return False


        # Step 2: server sends public key B, salt, and c to client
        body = response.json()
        salt = base64.b64decode(body['salt'])
        b = base64.b64decode(body['b'])
        c = body['c']
        iterations = body['iteration']
        protocol = body['protocol']

        # Step 3: client generates session key M1 and M2 with salt and b, sends to server
        log_info_msg(f"{self.username_base}, Authenticating with Password SRP, signin/complete, Server will verify Credentials")

        srp_password.set_encrypt_info(protocol, salt, iterations)
        m1 = usr.process_challenge( salt, b )
        m2 = usr.H_AMK

        url  = f"{self.AUTH_ENDPOINT}/signin/complete"
        data = {
            "accountName": uname,
            "c": c,
            "m1": base64.b64encode(m1).decode(),
            "m2": base64.b64encode(m2).decode(),
            "rememberMe": True,
            "trustTokens": [],
        }

        if 'trust_token' in self.session_data:
            self.trust_token  = self.session_data['trust_token']

        params = {"isRememberMeEnabled": "true"}

        try:
            response = self.PyiCloudSession.post(url, params=params, data=data, headers=headers, )

        except PyiCloudAPIResponseException as error:
            self.response_code = 401    #Authentication Error, invalid username/password

        return response.status_code in [200, 409]


#----------------------------------------------------------------------------
    def _validate_token(self):
        '''Checks if the current access token is still valid.'''

        # log_debug_msg(f"{self.username_base}, Checking session token validity")

        url = f"{self.SETUP_ENDPOINT}/validate"
        data = "null"

        try:
            self.data = self.PyiCloudSession.post(url, data=data)

            self.requires_2fa = self.requires_2fa or self._check_2fa_needed

            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token valid, "
                            f"2fa Needed-{self.requires_2fa}")

            return True

        except PyiCloudAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token is not valid, "
                            f"2fa Needed-{self.requires_2fa}, "
                            f"Error-{err}")

        except Exception as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Error encountered validating token > "
                            f"Error, {err}")
            log_exception(err)

        return False

#----------------------------------------------------------------------------
    def _get_auth_headers(self, overrides=None):

        # headers = {
        #     "Accept": "application/json, text/javascript",
        #     "Content-Type": "application/json",
        #     'referer':'https://www.apple.com/',
        #     "X-Apple-OAuth-Client-Id": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
        #     "X-Apple-OAuth-Client-Type": "firstPartyAuth",
        #     "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
        #     "X-Apple-OAuth-Require-Grant-Code": "true",
        #     "X-Apple-OAuth-Response-Mode": "web_message",
        #     "X-Apple-OAuth-Response-Type": "code",
        #     "X-Apple-OAuth-State": self.client_id,
        #     "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
        # }
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

#----------------------------------------------------------------------------
    # def _setup_password_filter(self, password):
    #     '''
    #     Set up the password_filter
    #     '''
    #     # if self.validate_aa_upw is False:
    #     #     return

    #     self.password_filter = pyi_session.PyiCloudPasswordFilter(password)
    #     LOGGER.addFilter(self.password_filter)
    #     Gb.iC3Logger.addFilter(self.password_filter)

#----------------------------------------------------------------------------
    def _setup_PyiCloudSession(self):
        '''
        Set up the password_filter, cookies and session files
        '''

        # If password was changed, delete the session file to generate a new 6-digit
        # verification code from Apple when the new session is created
        self.read_token_pw_file()

        self._update_token_pw_file(CONF_USERNAME, self.username)
        if self.password != self.token_password:
            delete_file(self.session_dir_filename)

        try:
            self.session_data = {}
            self.session_data = read_json_file(self.session_dir_filename)

            if self.session_data != {}:
                self.session_data_token.update(self.session_data)

            # If this username is being opened again with another password, a new PyiCloud
            # object is being created to verify the username/password are correct. Get some
            # token and url values from the original PyiCloud instance in case an asap specific
            # password is being used for this instance.
            if (self.is_DeviceSvc_setup_complete is False
                    and self.username in Gb.PyiCloud_by_username):
                _PyiCloud = Gb.PyiCloud_by_username[self.username]
                if _PyiCloud.findme_url_root:
                    self.findme_url_root = _PyiCloud.findme_url_root
                    self._update_token_pw_file('findme_url', self.findme_url_root)

                self.session_data_token = _PyiCloud.session_data_token.copy()
                self.session_data_token.update(self.session_data)
                self._update_token_pw_file('trust_token', self.session_data_token)
                if 'session_token' in self.session_data_token:
                    self.session_token = self.session_data_token['session_token']
                    self._update_token_pw_file('session_token', self.session_token)

                if 'session_id' in self.session_data:
                    _PyiCloud.session_id = self.session_data['session_id']
                    self._update_token_pw_file('session_id', _PyiCloud.session_id)

        except Exception as err:
            log_exception(err)
            log_info_msg(   f"{self.username_base}, "
                            f"Session file does not exist ({self.session_dir_filename})")

        if self.session_data.get("client_id"):
            self.client_id = self.session_data.get("client_id")
        else:
            self.session_data.update({"client_id": self.client_id})
            self.session_data_token.update({"client_id": self.client_id})

        self.PyiCloudSession = pyi_session.PyiCloudSession(self)

        self.PyiCloudSession.verify = True
        self.PyiCloudSession.headers.update({"Origin":self.HOME_ENDPOINT, 
                                            "Referer":self.HOME_ENDPOINT,})

        self.PyiCloudSession.cookies = cookielib.LWPCookieJar(filename=self.cookie_dir_filename)
        if path.exists(self.cookie_dir_filename):
            try:
                self.PyiCloudSession.cookies.load(ignore_discard=True, ignore_expires=True)
                log_debug_msg(  f"{self.username_base}, "
                                f"Load Cookies File ({self.cookie_dir_filename})")

            except:
                log_warning_msg(f"{self.username_base}, "
                                f"Load Cookies File Failed ({self.cookie_dir_filename})")

#----------------------------------------------------------------------------
    # def _setup_url_endpoint_suffix(self):
    #     '''
    #     Reset the url endpoint suffix if it has changed. This applies to China (.cn)
    #     '''

    #     if (self.endpoint_suffix and self.HOME_ENDPOINT.endswith(self.endpoint_suffix)):
    #         return

    #     if self.endpoint_suffix in ICLOUD_SERVER_COUNTRY_CODE:
    #         self.endpoint_suffix = f".{self.endpoint_suffix}"
    #         post_event(f"Apple Account URL Country Suffix > {self.endpoint_suffix}")
    #     else:
    #         self.endpoint_suffix = ''

    #     # Comment out the following line for non-texting
    #     # self.endpoint_suffix = ''

    #     self.HOME_ENDPOINT  = f"https://www.icloud.com{self.endpoint_suffix}"
    #     self.SETUP_ENDPOINT = f"https://setup.icloud.com{self.endpoint_suffix}/setup/ws/1"
    #     self.AUTH_ENDPOINT  = f"https://idmsa.apple.com/appleauth/auth"

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
            self.token_pw_data = read_json_file(self.tokenpw_dir_filename)

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
            save_json_file(self.tokenpw_dir_filename, self.token_pw_data)

        except Exception as err:
            # log_exception(err)
            log_warning_msg(f"Apple Acct > {self.account_owner}, "
                            f"Failed to update tokenpw file {self.tokenpw_dir_filename}")

#----------------------------------------------------------------------------
    @property
    def cookie_dir_filename(self):
        '''Get path for cookie file'''
        return path.join(self.cookie_directory,
                        f"{self.cookie_filename}")

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
    def _check_2fa_needed(self):
        '''Returns True if two-factor authentication is required.'''
        try:
            needs_2fa_flag = (self.data.get("dsInfo", {}).get("hsaVersion", 0) == 2
                                and (self.is_challenge_required or self.is_trusted_browser is False))

        except AttributeError:
            return False
        except Exception as err:
            log_exception(err)
            return False

        if needs_2fa_flag:
            log_debug_msg(  f"{self.username_base}, "
                            f"NEEDS-2FA, "
                            f"ChallengeRequired-{self.is_challenge_required}, "
                            f"TrustedBrowser-{self.is_trusted_browser}")
        return needs_2fa_flag

    # @property
    # def requires_2sa(self):
    #     """Returns True if two-step authentication is required."""
    #     return (self.data.get("dsInfo", {}).get("hsaVersion", 0) >= 1
    #                 and (is_challenge_required or self.is_trusted_session is False))

    @property
    def is_challenge_required(self):
        '''Returns True if the challenge code is needed.'''
        return self.data.get("hsaChallengeRequired", False)

    @property
    def is_trusted_browser(self):
        '''Returns True if the session is trusted.'''
        return self.data.get("hsaTrustedBrowser", False)

    @property
    def trusted_devices(self):
        return
        '''Returns devices trusted for two-step authentication.'''
        headers = self._get_auth_headers()
        url = f"{self.SETUP_ENDPOINT}/listDevices"

        try:
            data = self.PyiCloudSession.post(url, params=self.params, headers=headers,)
            # _log(f"{data=}")
            # _log(f"{data.get('devices')=}")

            return data.get('devices')

        except Exception as err:
            log_exception(err)


        # try:
            # _log(f"BUILD IN PYICLOUD TRUSTED DEVICES {self.data}")
            # url = f"{self.SETUP_ENDPOINT}/listDevices"
            # return await Gb.hass.async_add_executor_job(
            #                         self.PyiCloudSession.get,
            #                         (f"{self.SETUP_ENDPOINT}/listDevices"
            #                         f"?clientBuildNumber=2021Project52"
            #                         f"&clientMasteringNumber=2021B29"
            #                         f"&clientId={self.client_id[5:]}"))
            #                         # data=json.dumps(self.data))

            # self.data = req.json()


            # _session_request(self, method, url, **kwargs
            # request = self.PyiCloudSession.get(url, params=self.params)
            # return request.json().get("devices")
            # url = f"{self.SETUP_ENDPOINT}/listDevices"
            # request = self.PyiCloudSession.get(url, params=self.params)
            # return request.json().get("devices")
            # headers = self._get_auth_headers()

            # _log(f"BUILD IN PYICLOUD TRUSTED DEVICES {self.params.keys()}")

            # data = dict(self.user)
            # data["rememberMe"] = True
            # data["trustTokens"] = []
            # if self.session_data.get("trust_token"):
            #     data["trustTokens"] = [self.session_data.get("trust_token")]

            # headers = self._get_auth_headers({"Accept": "application/json"})
            # if self.session_data.get("session_id"):
            #     headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

            # _log(f"BUILD IN PYICLOUD TRUSTED DEVICES {headers.keys()}")

            # request = await Gb.hass.async_add_executor_job(
            #                     self.PyiCloudSession.get,
            #                     f"{self.SETUP_ENDPOINT}/listDevices"
            #                     f"?clientBuildNumber=2021Project52"
            #                     f"&clientMasteringNumber=2021B29"
            #                     f"&clientId={self.client_id[5:]}",
            #                     headers)
            # return request.json().get("devices")
        #     request = self.PyiCloudSession.get(
        #                 f"{self.SETUP_ENDPOINT}/listDevices",
        #                 params=self.params,
        #                 data=data,
        #                 headers=headers)
        #     return request.json().get('devices')

        # except Exception as err:
        #     log_exception(err)

        # return {}#request.json().get('devices')

    def new_log_in_needed(self, username):
        return username != self.username

    @property
    def icloud_dnames(self):
        icloud_dnames = [icloud_dname
                    for icloud_dname in self.device_id_by_icloud_dname.keys()]
        icloud_dnames.sort()

        return icloud_dnames

#----------------------------------------------------------------------------
    def send_verification_code(self, device):
        '''Requests that a verification code is sent to the given device.'''

        url  = f"{self.SETUP_ENDPOINT}/sendVerificationCode"
        data = device

        self.data = self.PyiCloudSession.post(url, params=self.params, data=data)

        return self.data.get("success", False)

#----------------------------------------------------------------------------
    def validate_2fa_code(self, code):
        '''Verifies a verification code received via Apple's 2FA system (HSA2).'''

        headers = self._get_auth_headers()      #{"Accept": "application/json"})

        url  = f"{self.AUTH_ENDPOINT}/verify/trusteddevice/securitycode"
        data = {"securityCode": {"code": code}}

        try:
            data = self.PyiCloudSession.post(url, data=data, headers=headers,)

        except PyiCloudAPIResponseException as error:
            # Wrong verification code
            if error.code == -21669:
                log_error_msg(  f"Apple Acct > {self.account_owner}, "
                                f"Incorrect verification code")
                return False
            raise

        except Exception as err:
            log_exception(err)
            return False

        self.trust_session()

        self.requires_2fa = self.requires_2fa or self._check_2fa_needed

        valid_msg = 'Rejected' if self.requires_2fa else 'Accepted'
        log_debug_msg(f"{self.username_base}, Verification Code {valid_msg}")

        # Return true if 2fa code was successful
        return not self.requires_2fa

#----------------------------------------------------------------------------
    def trust_session(self):
        '''Request session trust to avoid user log in going forward.'''

        headers = self._get_auth_headers()

        try:
            self.PyiCloudSession.get(f"{self.AUTH_ENDPOINT}/2sv/trust", headers=headers,)

            if self._authenticate_with_token():
                self.requires_2fa = self._check_2fa_needed
            return True

        except PyiCloudAPIResponseException:
            log_error_msg("Session trust failed")
            self.requires_2fa = self.requires_2fa or self._check_2fa_needed

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

#----------------------------------------------------------------------------
    def create_DeviceSvc_object(self, config_flow_login=False):
        '''
        Initializes the Family Sharing object, refresh the iCloud device data for all
        devices and create the PyiCloud_RawData object containing the data for all locatible devices.

        config_flow_create indicates another Apple acct is being logged into and a new iCloud object
        should be created instead of using the existing iCloud object created when iC3 started
        '''
        try:
            if self.DeviceSvc:
                return self.DeviceSvc

            self.DeviceSvc = PyiCloud_DeviceSvc(self,
                                                self.PyiCloudSession,
                                                self.params)

            log_debug_msg(f"{self.username_base}, Create iCloud object {self.username_base}")

            return self.DeviceSvc

        except Exception as err:
            log_exception(err)

            return None

#----------------------------------------------------------------------------
    def refresh_icloud_data(self, locate_all_devices=None,
                                    requested_by_devicename=None,
                                    device_id=None):
        '''
        Refresh the iCloud device data for all devices and update the PyiCloud_RawData object
        for all locatible devices that are being tracked by iCloud3.
        '''
        try:
            if self.is_DeviceSvc_setup_complete is False:
                return

            elif self.DeviceSvc is None:
                self.create_DeviceSvc_object()

            locate_all_devices = locate_all_devices      if locate_all_devices is not None \
                            else self.locate_all_devices if self.locate_all_devices is not None \
                            else True

            self.DeviceSvc.refresh_client(  locate_all_devices=locate_all_devices,
                                            requested_by_devicename=requested_by_devicename,
                                            device_id=device_id)

            return

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''

        data = self.DeviceSvc.play_sound(device_id, subject)
        return data

#----------------------------------------------------------------------------
    @staticmethod
    def _log_pw(password):
        return f"{password[:4]}{DOTS}{password[4:]}"

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return (f"<PyiCloudService: {self.setup_time}-{self.account_owner}>")
        except:
            return (f"<PyiCloudService: NotSetUp>")


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Find iCloud Devices service (originally find my iphone)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
REFRESH_ENDPOINT    = "/fmipservice/client/web/refreshClient"
PLAYSOUND_ENDPOINT  = "/fmipservice/client/web/playSound"
MESSAGE_ENDPOINT    = "/fmipservice/client/web/sendMessage"
LOSTDEVICE_ENDPOINT = "/fmipservice/client/web/lostDevice"

class PyiCloud_DeviceSvc():
    '''
    The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.
    '''

    def __init__(self,  PyiCloud,
                        PyiCloudSession,
                        params,
                        task="RefreshData",
                        device_id=None, subject=None, message=None,
                        sounds=False, number="", newpasscode=""):

        self.setup_time      = time_now()
        self.PyiCloudSession = PyiCloudSession
        self.PyiCloud        = PyiCloud
        self.username_base   = self.PyiCloud.username_base

        self.params       = params
        self.task         = task
        self.device_id    = device_id
        self.devices_data = {}

        Gb.devices_without_location_data = []

        self.timestamp_field = 'timeStamp'
        self.data_source     = ICLOUD

        fmiDict =   {"clientContext":
                        { "appName": "Home Assistant", "appVersion": "0.118",
                        "inactiveTime": 1, "apiVersion": "2.2.2" }
                    }

        if task == "PlaySound":
            if device_id:
                self.play_sound(device_id, subject)
            return

        elif task == "Message":
            if device_id:
                self.display_message(device_id, subject, message)
            return

        elif task == "LostDevice":
            if device_id:
                self.lost_device(device_id, number, message, newpasscode="")
            return

        try:
            # This will generate an error if the table has not been defined from (init or start_ic3)
            # Init may be in the process of setting up the table and iCloud but then start_ic3/Stage 4
            # thinks it is not done and resets everything.
            if isnot_empty(self.PyiCloud.device_id_by_icloud_dname):
                return
        except:
            pass

        self.refresh_client()

        Gb.devices_not_set_up = self._get_conf_icloud_devices_not_set_up()
        if Gb.devices_not_set_up == []:
            return

        #self.refresh_client()

#----------------------------------------------------------------------------
    def _get_conf_icloud_devices_not_set_up(self):
        '''
        Return a list of devices in the iCloud3 configuration file that are
        not in the  iCloud data returned from Apple.
        '''
        return [conf_device[CONF_IC3_DEVICENAME]
                    for conf_device in Gb.conf_devices
                    if (conf_device[CONF_FAMSHR_DEVICENAME] != NONE_FNAME
                        and conf_device[CONF_FAMSHR_DEVICENAME] not in \
                                self.PyiCloud.device_id_by_icloud_dname)]

#---------------------------------------------------------------------------
    @property
    def is_DeviceSvc_setup_complete(self):
        return self.PyiCloud.is_DeviceSvc_setup_complete

#---------------------------------------------------------------------------
    @property
    def devices_cnt(self):
        # Simulate no devices returned for the first 4 tries
        # if Gb.get_FAMSHR_devices_retry_cnt < 4:
        #     return 0

        if 'content' in self.devices_data:
            return len(self.devices_data.get('content', {}))
        else:
            return 0

#----------------------------------------------------------------------------
    def refresh_client(self, requested_by_devicename=None,
                            locate_all_devices=None, device_id=None):
        '''
        Refreshes the FindMyiPhoneService endpoint,
        This ensures that the location data is up-to-date.

        requested_by_devicename:
            = 'reload_all_devices' - Reload all devices during startup instead of
                only devices that have already been verified
            = devicename - Device that is requesting new location data
        device_id:
            = refresh/locate this device
            = None - Refresh/located all devices in Family Sharing list
        locate_all_devices:
            = True - Locate all devices in the Family Sharing list (overrides device selection)
            = False - Locate only the devices belonging to this Apple acct
        '''
        try:
            # if Gb.this_update_secs > Gb.started_secs + 3600:
            #     # _evlog("Internet Connection Error-End")
            #     # Gb.internet_connection_error = False
            #     pass

            # elif (Gb.internet_connection_error is False
            #         and Gb.this_update_secs > Gb.started_secs + 1800):
            #     _evlog("Internet Connection Error-Start")
            #     Gb.internet_connection_error = True
            #     Gb.internet_connection_error_secs  = time_now_secs()


            if (Gb.internet_connection_error
                    or self.is_DeviceSvc_setup_complete is False):
                return False

            #locate_all_devices = True if locate_all_devices is None else locate_all_devices
            locate_all_devices = locate_all_devices               if locate_all_devices is not None \
                            else self.PyiCloud.locate_all_devices if self.PyiCloud.locate_all_devices is not None \
                            else True

            if requested_by_devicename:
                _Device = Gb.Devices_by_devicename[requested_by_devicename]
                last_update_loc_time = _Device.last_update_loc_time
            else:
                last_update_loc_time = '?'

            if locate_all_devices is False:
                device_msg = f"OwnerDev-{len(Gb.owner_device_ids_by_username.get(self.PyiCloud.username, []))}"
            else:
                device_msg = f"AllDevices-{len(Gb.Devices_by_username.get(self.PyiCloud.username, []))}"

            log_debug_msg( f"Apple Acct > {self.PyiCloud.username_base}, "
                                f"RefreshRequestBy-{requested_by_devicename}, "
                                f"LocateAllDev-{locate_all_devices}, {device_msg}, LastLoc-{last_update_loc_time}")

            url  = f"{self.PyiCloud.findme_url_root}{REFRESH_ENDPOINT}"
            data = {"clientContext":{
                        "fmly": locate_all_devices,
                        "shouldLocate": True,
                        "selectedDevice": device_id,
                        "deviceListVersion": 1, },
                    "accountCountryCode": self.PyiCloud.session_data_token.get("account_country"),
                    "dsWebAuthToken": self.PyiCloud.session_data_token.get("session_token"),
                    "trustToken": self.PyiCloud.session_data_token.get("trust_token", ""),
                    "extended_login": True,}

            try:
                self.devices_data = self.PyiCloudSession.post(url, params=self.params, data=data)

            except Exception as err:
                # log_exception(err)
                self.devices_data = {}
                log_debug_msg(  f"{self.PyiCloud.username_base}, "
                                f"No data returned from iCloud refresh request {err=}")

            if self.PyiCloudSession.response_code == 501:
                self._set_service_available(False)
                post_event( f"{EVLOG_ALERT}iCLOUD ALERT > {self.PyiCloud.account_owner}, "
                            f"Apple Acct Data Source is not available. "
                            f"The web url providing location data returned a "
                            f"Service Not Available error")
                return None

            self.update_device_location_data(requested_by_devicename, self.devices_data.get("content", {}))
            return isnot_empty(self.PyiCloud.RawData_by_device_id)

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def update_device_location_data(self, requested_by_devicename=None, devices_data=None):
        '''
        devices_data is the iCloud response['content'] data for all devices in the iCloud list.
        Cycle through them, determine if the data is good and update each devices with the new location
        info.
        '''
        if devices_data is None:
            return

        try:
            self.PyiCloud.last_refresh_secs = time_now_secs()
            self.PyiCloud.update_requested_by = requested_by_devicename
            monitor_msg = f"UPDATED iCloud Data > RequestedBy-{requested_by_devicename}"

            for device_data in devices_data:

                # TEST CODE - Create duplicate device
                # if device_data[NAME] == 'Gary-iPad':
                #     device_data[NAME] = 'Lillian-iPad'
                #     device_data[LOCATION] = {}


                device_data[NAME] = device_data_name = \
                        PyiCloud_RawData._remove_special_chars(device_data[NAME])

                device_id = device_data[ID]
                rawdata_hdr_msg = ''

                if (device_data_name in Gb.conf_icloud_dnames
                        and requested_by_devicename != 'reload_all_devices'
                        and Gb.start_icloud3_inprocess_flag):
                    pass

                # only check tracked/monitored devices for location data
                elif (LOCATION not in device_data
                        or device_data[LOCATION] == {}
                        or device_data[LOCATION] is None):
                    if device_id not in Gb.devices_without_location_data:
                        list_add(Gb.devices_without_location_data, device_data_name)
                        rawdata_hdr_msg = 'NO LOCATION'
                        if device_data[ICLOUD_DEVICE_STATUS] == 203:
                            rawdata_hdr_msg += ', OFFLINE'
                            monitor_msg += f"{CRLF_STAR}OFFLINE > "
                        else:
                            monitor_msg += f"{CRLF_STAR}NO LOCATION > "
                        monitor_msg += (f"{self.PyiCloud.account_owner}, "
                                        f"{device_data_name}/"
                                        f"{device_id[:8]}, "
                                        f"{device_data['modelDisplayName']} "
                                        f"({device_data['rawDeviceModel']})")

                # Create RawData object if the device_id is not already set up
                if device_id not in self.PyiCloud.RawData_by_device_id:
                    # if device_data_name == 'Gary-iPad':
                    #     self._create_test_data(device_id, device_data_name, device_data)
                    # else:
                    device_msg = self._create_iCloud_RawData_object(device_id, device_data_name, device_data)
                    monitor_msg += device_msg
                    #continue

                # The PyiCloudSession is not recreated on a restart if it already is valid but we need to
                # initialize all devices, not just tracked ones on an iC3 restart.
                elif Gb.start_icloud3_inprocess_flag:
                    device_msg = self._initialize_iCloud_RawData_object(device_id, device_data_name, device_data)
                    monitor_msg += device_msg
                    #continue

                # Non-tracked devices are not updated
                _RawData = self.PyiCloud.RawData_by_device_id[device_id]

                _Device = _RawData.Device
                if (_RawData.Device is None
                        or 'location' not in _RawData.device_data):
                    continue

                _RawData.save_new_device_data(device_data)

                if _RawData.location_secs == 0:
                    continue

                if ('all' in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
                        or _RawData.ic3_devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
                    log_hdr = ( f"{self.PyiCloud.username_base}{LINK}"
                                f"{device_data_name}/{_Device.devicename}{RLINK}, "
                                f"{rawdata_hdr_msg}, iCloud Data ")
                    log_rawdata(log_hdr, _RawData.device_data,
                                data_source='icloud', filter_id=self.PyiCloud.username)

                if _RawData.last_loc_time_gps == _RawData.loc_time_gps:
                    last_loc_time_gps_msg = last_loc_time_msg = ''
                else:
                    last_loc_time_gps_msg = f"{_RawData.last_loc_time_gps}{RARROW}"
                    last_loc_time_msg     = f"{_RawData.last_loc_time}{RARROW}"
                    _Device.loc_time_updates_icloud.append(_RawData.location_time)

                event_msg =(f"Located > iCloud-"
                                    f"{last_loc_time_msg}"
                                    f"{_RawData.location_time}, ")

                if secs_since(_RawData.location_secs) > _Device.old_loc_threshold_secs + 5:
                    event_msg += f", Old, {format_age(_RawData.location_secs)}"

                elif _RawData.battery_level > 0:
                    if _RawData.battery_level != _Device.dev_data_battery_level:
                        event_msg += f"{_Device.dev_data_battery_level}%{RARROW}"
                    event_msg += f"{_RawData.battery_level}%"

                if Gb.start_icloud3_inprocess_flag is True:
                    pass

                elif requested_by_devicename == _Device.devicename:
                    _RawData.last_requested_loc_time_gps = _RawData.loc_time_gps
                    if last_loc_time_msg:
                        post_event(_Device.devicename, event_msg)

                elif _Device.isin_zone:
                    post_monitor_msg(_Device.devicename, event_msg)

                elif _RawData.location_secs > 0:
                    post_event(_Device.devicename, event_msg)

        except Exception as err:
            log_exception(err)

#----------------------------------------------------------------------------
    def _create_test_data(self, device_id, device_data_name, device_data):
        '''
        Create duplicate devices test data in _RawData using data from the
        current device
        '''
        device_data_test1 = device_data.copy()
        device_data_test2 = device_data.copy()
        device_data_test1['location'] = device_data['location'].copy()
        device_data_test2['location'] = device_data['location'].copy()

        device_data['location']['timeStamp'] = 0

        monitor_msg +=\
            self._create_iCloud_RawData_object(device_id, device_data_name, device_data)

        device_data_test1[NAME] = f"{device_data_name}(1)"
        device_data_test1[ID]   = f"XX1_{device_id}"
        device_data_test1['location']['timeStamp'] -= 3000000000
        device_data_test1['rawDeviceModel'] = 'iPad8,91'

        monitor_msg +=\
            self._create_iCloud_RawData_object(device_data_test1[ID], device_data_test1[NAME], device_data_test1)
        device_data_test2[NAME] = f"{device_data_name}(2)"
        device_data_test2[ID]   = f"XX2_{device_id}"
        device_data_test2['rawDeviceModel'] = 'iPad8,92'
        monitor_msg +=\
            self._create_iCloud_RawData_object(device_data_test2[ID], device_data_test2[NAME], device_data_test2)

#----------------------------------------------------------------------------
    def _create_iCloud_RawData_object(self, device_id, device_data_name, device_data):

        _RawData = PyiCloud_RawData(device_id,
                                    device_data,
                                    self.PyiCloudSession,
                                    self.params,
                                    'iCloud',
                                    'timeStamp',
                                    self,
                                    device_data_name,)

        self.set_icloud_rawdata_fields(device_id, _RawData)

        log_debug_msg(  f"{self.PyiCloud.username_base}, "
                        f"Create RawData_icloud object, "
                        f"{self.PyiCloud.account_owner}{LINK}{_RawData.fname}{RLINK}")

        # if ('all' in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
        #         or _RawData.ic3_devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
        #  Log all devices (no filter) on initialization
        log_hdr = f"{self.PyiCloud.account_name}{LINK}{_RawData.fname}{RLINK}, iCloud Data"
        log_rawdata(log_hdr, _RawData.device_data,
                    data_source='icloud', filter_id=self.PyiCloud.username)

        dup_msg = f" as {_RawData.fname}" if _RawData.fname_dup_suffix else ''

        return (f"{CRLF_DOT}ADDED > {device_data_name}{dup_msg}, {_RawData.loc_time_gps}")

#----------------------------------------------------------------------------
    def _initialize_iCloud_RawData_object(self, device_id, device_data_name, device_data):


        _RawData = self.PyiCloud.RawData_by_device_id[device_id]

        dname = _RawData._remove_special_chars(_RawData.name)
        self.PyiCloud.dup_icloud_dname_cnt[dname] = 0

        _RawData.__init__(  device_id,
                            device_data,
                            self.PyiCloudSession,
                            self.params,
                            'iCloud', 'timeStamp',
                            self,
                            device_data_name,)

        self.set_icloud_rawdata_fields(device_id, _RawData)

        log_debug_msg(  f"Initialize RawData_icloud object "
                        f"{self.PyiCloud.username_base}{LINK}<{_RawData.fname}, "
                        f"{device_data_name}")

        # if ('all' in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]
        #         or _RawData.ic3_devicename in Gb.conf_general[CONF_LOG_LEVEL_DEVICES]):
        #  Log all devices (no filter) on initialization
        log_hdr = f"{self.PyiCloud.account_name}{LINK}{_RawData.fname}{RLINK}, iCloud Data"
        log_rawdata(log_hdr, _RawData.device_data,
                    data_source='icloud', filter_id=self.PyiCloud.username)

        return (f"{CRLF_DOT}INITIALIZED > {device_data_name}, {_RawData.loc_time_gps}")

#----------------------------------------------------------------------
    def set_icloud_rawdata_fields(self, device_id, _RawData):
        '''
        The iCloud dictionaries contain info about the devices that is set
        up when the RawData object for the device is created. If the iCloud
        object is recreated during error, the device's RawData object already
        exists and is not recreated. The iCloud dictionaries need to be
        set up again.
        '''
        list_add(self.PyiCloud.RawData_items, _RawData)
        self.PyiCloud.RawData_by_device_id[device_id]             = _RawData
        self.PyiCloud.device_id_by_icloud_dname[_RawData.fname]   = device_id
        self.PyiCloud.icloud_dname_by_device_id[device_id]        = _RawData.fname
        self.PyiCloud.device_info_by_icloud_dname[_RawData.fname] = _RawData.icloud_device_info
        self.PyiCloud.device_model_info_by_fname[_RawData.fname]  = _RawData.icloud_device_model_info
        self.PyiCloud.device_model_name_by_icloud_dname[_RawData.fname]= _RawData.icloud_device_display_name

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')
        name = name.replace(u'\2019', "'")

        return name

#----------------------------------------------------------------------------
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if self.is_DeviceSvc_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.PyiCloud.findme_url_root}{PLAYSOUND_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "clientContext": {"fmly": True}, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def display_message(self, device_id, subject="Find My iPhone Alert",
                        message="This is a note", sounds=False):
        '''
        Send a request to the device to display a message.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if self.is_DeviceSvc_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.PyiCloud.findme_url_root}{MESSAGE_ENDPOINT}"
        data = {"device": device_id,
                "subject": subject,
                "sound": sounds,
                "userText": True,
                "text": message, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def lost_device(self, device_id, number,
                        message="This iPhone has been lost. Please call me.",
                        newpasscode=""):
        '''
        Send a request to the device to trigger 'lost mode'.

        The device will show the message in `text`, and if a number has
        been passed, then the person holding the device can call
        the number without entering the pass
        '''
        if self.is_DeviceSvc_setup_complete is False:
            post_event("iCloud Service is not available, try again later")
            return

        url  = f"{self.PyiCloud.findme_url_root}{LOSTDEVICE_ENDPOINT}"
        data = {"text": message,
                "userText": True,
                "ownerNbr": number,
                "lostModeEnabled": True,
                "trackingEnabled": True,
                "device": device_id,
                "passcode": newpasscode, }

        self.PyiCloudSession.post(url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def __repr__(self):
        try:
            return (f"<PyiCloud.DeviceSvc: {self.PyiCloud.setup_time}-{self.setup_time}-"
                    f"{self.PyiCloud.account_owner}>")
        except:
            return (f"<PyiCloud.DeviceSvc: NotSetUp>")

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   PyiCloud_RawData Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable PyiCloud.RawData_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

class PyiCloud_RawData():
    '''
    PyiCloud_RawData stores all the device data for each Apple Acct

    Parameters:
        - device_id = iCloud device id of the device
        - device_data = data received from Apple
        - PyiCloudSession = PyiCloud instance that authenticates and gets the data
        - params = ?
        - data_source = 'iCloud'
        - timestamp_field = name of the location timestamp field in device_data
        - DeviceSvc = DeviceSvc object that created this RawData object
        - device_data_name = name of the device in device_data (Gary-iPhone)
    '''

    def __init__(self, device_id,
                        device_data,
                        PyiCloudSession,
                        params,
                        data_source,
                        timestamp_field,
                        DeviceSvc,
                        device_data_name,):

        self.setup_time      = time_now()
        self.PyiCloud        = DeviceSvc.PyiCloud  # PyiCloud object (Apple Acct) with the device data
        self.PyiCloudSession = PyiCloudSession

        # __init__ is run several times during to initialize the RawData fields
        # Initialize the identity fields on the initial create
        if device_id not in self.PyiCloud.RawData_by_device_id:
            self.device_id       = device_id
            self.params          = params
            self.data_source     = data_source
            self.timestamp_field = timestamp_field
            self.DeviceSvc       = DeviceSvc           # iCloud object creating this RawData object

        try:
            # Only update the device name fields when the RawData object is created
            # or when it was changed on the device and iCloud3 was restarted. Setting
            # it up again if the RawData is just being reinstalled creates errors
            # detecting duplicate names.
            name_update_flag = (self.name != device_data_name)
        except:
            name_update_flag = True

        if name_update_flag:
            self.name            = device_data_name
            self.fname_original  = ''                               # Original dname after cleanup
            self.fname_dup_suffix= ''                               # Suffix added to fname if duplicates
            self.fname           = self.device_data_fname_dup_check # Clean up fname and check for duplicates

        self.evlog_alert_char= ''
        self.ic3_devicename  = Gb.devicenames_by_icloud_dname.get(self.fname, '')
        self.Device          = Gb.Devices_by_devicename.get(self.ic3_devicename)

        self.device_data     = device_data
        self.status_code     = 0

        self.update_secs     = time_now_secs()
        self.location_secs   = 0
        self.location_time   = HHMMSS_ZERO
        self.last_used_location_secs = 0
        self.last_loc_time           = ''               # location_time_gps_acc from last general update
        self.last_loc_time_gps       = ''               # location_time_gps_acc from last general update
        self.last_used_location_time = HHMMSS_ZERO
        self.last_requested_loc_time_gps = ''           # location_time_gps_acc from last time requested

        self.battery_level = 0

        self.set_located_time_battery_info()
        self.device_data[DATA_SOURCE] = self.data_source
        self.device_data[CONF_IC3_DEVICENAME] = self.ic3_devicename
        self.raw_model = self.device_data.get('rawDeviceModel', self.device_class).replace('_', '')
        Gb.model_display_name_by_raw_model[self.raw_model] = self.icloud_device_display_name

#----------------------------------------------------------------------
    @property
    def device_id8(self):
        return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def fname_device_id(self):
        return f"{self.fname} ({self.device_id8})"

#----------------------------------------------------------------------
    @property
    def devicename(self):
        if Device := Gb.Devices_by_icloud_device_id.get(self.device_id):
            return Device.devicename
        elif self.is_data_source_ICLOUD:
            return self.fname
        else:
            return self.device_id[:8]

#----------------------------------------------------------------------
    @property
    def family_share_device(self):
        return self.device_data['fmlyShare']

#----------------------------------------------------------------------
    @property
    def device_data_fname_dup_check(self):
        '''
        Determine if the iCloud device being set up is the same name as one that has already
        been set up. Is so, add periods('.') to the end of the fname to make it unique.
        Also set the fname suffix value.
        '''
        # Remove non-breakable space and right quote mark
        dname = self.fname_original = self._remove_special_chars(self.name)

        # This is a tracked and configured device if the device_id is already used
        conf_devicename = self._find_conf_device_devicename(CONF_FAMSHR_DEVICE_ID, self.device_id)
        if conf_devicename:
            return dname

        # It is ok if dname has not been seen
        if dname not in self.PyiCloud.device_id_by_icloud_dname:
            return dname

        # This is not a tracked and configured device if the dname is not used
        # but maybe a dupe because the dname is found with a different device_id
        conf_devicename = self._find_conf_device_devicename(CONF_FAMSHR_DEVICENAME, dname)
        if conf_devicename == '':
            found_before = (dname in self.PyiCloud.device_id_by_icloud_dname)
            if found_before is False:
                return dname

        # Dupe dname, it has not been seen and dname has been used
        # Add a period to dname to make it unique
        _dname = f"{dname}."
        while _dname in self.PyiCloud.device_id_by_icloud_dname:
            _dname += '.'
        self.fname_dup_suffix = _dname.replace(dname, '')

        return _dname

#......................................................................
    def _find_conf_device_devicename(self, field, field_value):
        '''
        Cycle through the conf_devices and return the ic3_devicename that matches
        the requested field/field_value
        '''
        conf_devicename = [conf_device[CONF_IC3_DEVICENAME]
                                for conf_device in Gb.conf_devices
                                if (conf_device[CONF_APPLE_ACCOUNT] == self.PyiCloud.username
                                    and conf_device[field] == field_value)]

        if conf_devicename:
            return conf_devicename[0]
        else:
            return ''

#----------------------------------------------------------------------
    @staticmethod
    def _remove_special_chars(name):
        name = name.replace("’", "'")
        name = name.replace(u'\xa0', ' ')
        name = name.replace(u'\2019', "'")
        return name

#----------------------------------------------------------------------
    @property
    def icloud_device_info(self):
        return f"{self.fname} ({self.device_identifier})"

#----------------------------------------------------------------------
    @property
    def device_status_code(self):
        return int(self.device_data.get(ICLOUD_DEVICE_STATUS, '0'))
#----------------------------------------------------------------------
    @property
    def device_status_msg(self):
        status_code = self.device_data.get(ICLOUD_DEVICE_STATUS, '0')
        return (f"{DEVICE_STATUS_CODES.get(status_code, 'Unknown')}/"
                f"{status_code}")

#----------------------------------------------------------------------
    @property
    def device_identifier(self):
        '''
        Format device name:
            - iPhone 14,2; iPhone15,2)
            - Gary-iPhone
        '''
        if self.is_data_source_ICLOUD:
            display_name = self.device_data['deviceDisplayName'].split(' (')[0]
            display_name = display_name.replace('Series ', '')
            if self.device_data.get('rawDeviceModel').startswith(AIRPODS_FNAME):
                device_class = AIRPODS_FNAME
            else:
                device_class = self.device_data.get('deviceClass', '')

            # return (f"{display_name}; {raw_model}").replace("’", "'")
            return (f"{self.icloud_device_display_name}; {self.raw_model}").replace("’", "'")

        else:
            return self.name.replace("’", "'")

#----------------------------------------------------------------------
    @property
    def device_class(self):
        if self.device_data.get('rawDeviceModel').startswith(AIRPODS_FNAME):
            return AIRPODS_FNAME
        else:
            return self.device_data.get('deviceClass', '')

#----------------------------------------------------------------------
    @property
    def icloud_device_display_name(self):
        display_name = self.device_data['deviceDisplayName']
        display_name = display_name.replace('generation', 'gen')
        display_name = display_name.replace('nd gen', '')
        display_name = display_name.replace('th gen', '')
        display_name = display_name.replace('Series ', '')
        display_name = display_name.replace('(', '').replace(')', '')
        idx = display_name.find('-inch')
        if idx > 0:
            display_name = display_name[:idx-3] + display_name[idx+5:]
        return display_name

#----------------------------------------------------------------------
    @property
    def icloud_device_model_info(self):
        return [self.device_data['rawDeviceModel'].replace("_", ""),    # iPhone15,2
                self.device_data['modelDisplayName'],                   # iPhone
                self.icloud_device_display_name]                        # iPhone 14 Pro

#----------------------------------------------------------------------
    @property
    def is_data_source_ICLOUD(self):
        return (self.data_source in [ICLOUD])

    @property
    def loc_time_gps(self):
        return f"{self.location_time}/±{self.gps_accuracy}m"

    @property
    def gps_accuracy(self):
        """ Get location gps accuracy or 9999 if not available """

        try:
            return round(self.location[ICLOUD_HORIZONTAL_ACCURACY])
        except:
            return 9999

    @property
    def is_gps_poor(self):
        return (self.gps_accuracy > Gb.gps_accuracy_threshold
                    or self.gps_accuracy == 9999)

    @property
    def is_gps_good(self):
        return not self.is_gps_poor

    @property
    def gps_accuracy_msg(self):
        """ GPS Accuracy text if available or unknown """
        if self.gps_accuracy == 9999:
            return  'Unknown'
        return round(self.gps_accuracy)

#----------------------------------------------------------------------------
    def save_new_device_data(self, device_data):
        '''Update the device data.'''
        try:
            self.last_loc_time     = self.location_time
            self.last_loc_time_gps = f"{self.location_time}/±{self.gps_accuracy}m"
        except:
            self.last_loc_time_gps = ''

        try:
            self.status_code = device_data['snd']['status_code']
        except:
            pass

        filtered_device_data = {k: v    for k, v in device_data.items()
                                        if k not in DEVICE_DATA_FILTER_OUT}

        # self.device_data.clear()
        self.device_data.update(filtered_device_data)
        self.set_located_time_battery_info()

        self.device_data[DATA_SOURCE] = self.data_source
        return

#----------------------------------------------------------------------------
    def status(self, additional_fields=[]):
        '''
        Returns status information for device.
        This returns only a subset of possible properties.
        '''
        self.DeviceSvc.refresh_client(requested_by_devicename=self.device_id)

        fields = ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]
        fields += additional_fields

        properties = {}
        for field in fields:
            properties[field] = self.location.get(field)

        return properties

#----------------------------------------------------------------------------
    @property
    def is_offline(self):
        return self.device_data[ICLOUD_DEVICE_STATUS] == 201

#----------------------------------------------------------------------------
    @property
    def is_location_data_available(self):
        return not (LOCATION not in self.device_data
                    or self.device_data[LOCATION] == {}
                    or self.device_data[LOCATION] is None)
#----------------------------------------------------------------------------
    def set_located_time_battery_info(self):

        try:
            self.device_data[CONF_IC3_DEVICENAME] = self.ic3_devicename

            if self.is_location_data_available:
                self.device_data[LOCATION][TIMESTAMP] = int(self.device_data[LOCATION][self.timestamp_field] / 1000)
                self.device_data[LOCATION][LOCATION_TIME] = secs_to_time(self.device_data[LOCATION][TIMESTAMP])
                self.location_secs = self.device_data[LOCATION][TIMESTAMP]
                self.location_time = self.device_data[LOCATION][LOCATION_TIME]
            else:
                self.device_data[LOCATION] = {self.timestamp_field: 0}
                self.device_data[LOCATION][TIMESTAMP] = 0
                self.device_data[LOCATION][LOCATION_TIME] = HHMMSS_ZERO
                self.location_secs = 0
                self.location_time = HHMMSS_ZERO

            # This will create old location for testing
            # if self.name=='Gary-iPhone':
            #     raise PyiCloudAPIResponseException('test error', 404)
            #     self.device_data[LOCATION][TIMESTAMP]     = int(self.device_data[LOCATION][self.timestamp_field] / 1000) - 600
            #     _evlog('gary_iphone', f"Reduce loc time to {secs_to_time(self.device_data[LOCATION][TIMESTAMP])}")


        except TypeError:
            # This will happen if there is no location data in device_data
            self.device_data[LOCATION] = {TIMESTAMP: 0, LOCATION_TIME: HHMMSS_ZERO}
            self.location_secs = 0
            self.location_time = HHMMSS_ZERO

        except Exception as err:
            log_exception(err)
            self.device_data[LOCATION] = {TIMESTAMP: 0, LOCATION_TIME: HHMMSS_ZERO}
            self.location_secs = 0
            self.location_time = HHMMSS_ZERO

        self.update_secs = time_now_secs()

        # Reformat and convert batteryStatus and batteryLevel
        try:
            self.battery_level  = self.device_data.get(ICLOUD_BATTERY_LEVEL, 0)
            self.battery_level  = round(self.battery_level*100)
            self.battery_status = self.device_data[ICLOUD_BATTERY_STATUS]
            if self.battery_level > 99:
                self.battery_status = 'Charged'
            elif self.battery_status in ['Charging', 'Unknown']:
                pass
            elif self.battery_level > 0 and self.battery_level < BATTERY_LEVEL_LOW:
                self.battery_status = 'Low'

            self.device_data[BATTERY_LEVEL]  = self.battery_level
            self.device_data[BATTERY_STATUS] = self.battery_status
        except:
            pass

#----------------------------------------------------------------------------
    @property
    def data(self):
        '''Returns all of the device's data'''
        return self.device_data

    @property
    def location(self):
        '''Return the device's location data'''
        return self.device_data["location"]

    def __repr__(self):
        try:
            return f"<PyiCloud_RawData: {self.setup_time}-{self.PyiCloud.username_base}-{self.name}-{self.device_id[:8]}"
        except:
            return f"<PyiCloud_RawData: Undefined>"



#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Exceptions (exceptions.py)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
'''Library exceptions.'''


class PyiCloudException(Exception):
    '''Generic iCloud exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloudAPIResponseException(PyiCloudException):
    '''iCloud response exception.'''
    def __init__(self, reason, code=None, retry=False):

        self.reason = reason
        self.code = code
        message = reason or "Could not connect to iCloud Location Servers"
        if code:
            message += (f" (Error Code {code})")
        if retry:
            message += ". Retrying ..."

        super(PyiCloudAPIResponseException, self).__init__(message)

#----------------------------------------------------------------------------
class PyiCloudServiceNotActivatedException(PyiCloudAPIResponseException):
    '''iCloud service not activated exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloudFailedLoginException(PyiCloudException):
    '''iCloud failed login exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloud2FARequiredException(PyiCloudException):
    '''iCloud 2SA required exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloud2SARequiredException(PyiCloudException):
    """iCloud 2SA required exception."""
    def __init__(self, apple_id):
        message = f"Two-step authentication required for account: {apple_id}"
        super().__init__(message)

#----------------------------------------------------------------------------
class PyiCloudNoStoredPasswordAvailableException(PyiCloudException):
    '''iCloud no stored password exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloudNoDevicesException(PyiCloudException):
    '''iCloud no device exception.'''
    pass
