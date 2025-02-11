
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
from ..helpers.common       import (instr, is_empty, isnot_empty, list_add, list_del, )
from ..helpers.file_io      import (save_json_file, )
from ..helpers.time_util    import (time_now,  time_now_secs, secs_to_time, format_time_age, )
from ..helpers.messaging    import (_log, _evlog,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_rawdata, log_exception, log_rawdata_unfiltered, filter_data_dict, )

from requests   import Session, adapters
import requests
from requests.exceptions import ConnectionError
from os         import path
import inspect
import json
import random
import time
# import http.cookiejar as cookielib

HEADER_DATA = {
    "X-Apple-ID-Account-Country": "account_country",
    "X-Apple-ID-Session-Id": "session_id",
    "X-Apple-Session-Token": "session_token",
    "X-Apple-TwoSV-Trust-Token": "trust_token",
    "scnt": "scnt",
}

DEVICE_STATUS_ERROR_500 = 500
INVALID_GLOBAL_SESSION_421 = 421
APPLE_ID_VERIFICATION_CODE_INVALID_404 = 404
AUTHENTICATION_NEEDED_421_450_500 = [421, 450, 500]
AUTHENTICATION_NEEDED_450 = 450
CONNECTION_ERROR_503 = 503

HTTP_RESPONSE_CODES = {
    200: 'iCloud Server Responded',
    204: 'Verification Code Accepted',
    421: 'Verification Code May Be Needed',
    450: 'Verification Code May Be Needed',
    500: 'Verification Code May Be Needed',
    503: 'Apple Server Refused SRP Password Validation Request',
    400: 'Invalid Verification Code',
    403: 'Verification Code Requested',
    404: 'Apple http Error, Web Page not Found',
    201: 'Device Offline',
    -2:  'Apple Server not Available (Connection Error)',
    302: 'Apple Server not Available (Connection Error)',
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
#   PYICLOUD SESSION
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
class PyiCloudSession(Session):
    '''iCloud session.'''

    def __init__(self, PyiCloud, validate_aa_upw=False):
        self.setup_time = time_now()
        self.PyiCloud   = PyiCloud

        self.validate_aa_upw = validate_aa_upw
        if validate_aa_upw is False:
            self.username   = PyiCloud.username
            Gb.PyiCloudSession_by_username[self.username] = self
        else:
            self.username = 'validate_upw'

        self.response_code = 0
        self.response_ok = True

        super().__init__()

        # Increase the number of connections to prevent timeouts
        # authenticting the Apple Account
        adapter = adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)

    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ
        # callee.function and callee.lineno provice calling function and the line number
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])

        if 'retry_cnt' in kwargs:
            pass
        elif Gb.internet_connection_error:
            return {}

        try:
            # If data is a str, unconvert it from json format, it will be reconverted  to json later
            if 'data' in kwargs and type(kwargs['data']) is str:
                kwargs['data'] = json.loads(kwargs['data'])
            retry_cnt = kwargs.get('retry_cnt', 0)

            log_rawdata_flag = (url.endswith('refreshClient') is False)
            if Gb.log_rawdata_flag or log_rawdata_flag or Gb.initial_icloud3_loading_flag:
                try:
                    log_hdr = ( f"{self.PyiCloud.username_base}, {method}, Request, "
                                f"{callee.function}/{callee.lineno} ▲")
                    log_data = {'url': url[8:], 'retry': kwargs.get("retry_cnt", 0)}
                    log_data.update(kwargs)
                    log_rawdata(log_hdr, log_data, log_rawdata_flag=log_rawdata_flag)

                except Exception as err:
                    log_exception(err)

            kwargs.pop("retried", False)
            kwargs.pop("retry_cnt", 0)

            if 'data' in kwargs and type(kwargs['data']) is dict:
                kwargs['data'] = json.dumps(kwargs['data'])

        except Exception as err:
            log_exception(err)

        try:
            response = None

            #++++++++++++++++ REQUEST ICLOUD DATA ++++++++++++++++
            Gb.last_PyiCloud_request_secs = time_now_secs()

            if Gb.internet_connection_test:
                raise requests.exceptions.ConnectionError

            response = Session.request(self, method, url, **kwargs)

            try:
                data = response.json()

            except Exception as err:
                # log_exception(err)
                data = {}

            Gb.last_PyiCloud_request_secs = 0
            #++++++++++++++++ REQUEST ICLOUD DATA +++++++++++++++


        except (requests.exceptions.RetryError,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                OSError,
                requests.exceptions.SSLError,
                requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.InvalidURL,
                requests.exceptions.InvalidHeader,
                requests.exceptions.InvalidProxyURL,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.StreamConsumedError,
                requests.exceptions.RetryError,
                requests.exceptions.UnrewindableBodyError,
                ) as err:

            log_error_msg(  f"iCloud3 Error > An error occurred connecting to the Internet, "
                            f"Home Assistant may be Offline > "
                            f"Error-{err}")

            Gb.internet_connection_error = True

            self.response_code = -3
            self.PyiCloud.response_code = -3
            self.response_ok = False
            return {}

        except Exception as err:
            log_exception(err)

            self._raise_error(-3, f"Error setting up iCloud Server Connection ({err})")
            return {}

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        json_mimetypes = ["application/json", "text/json"]

        self.PyiCloud.last_response_code = self.PyiCloud.response_code
        self.PyiCloud.response_code      = response.status_code
        self.response_code          = response.status_code
        self.response_ok            = response.ok

        log_rawdata_flag = (url.endswith('refreshClient') is False) or response.status_code != 200
        if Gb.log_rawdata_flag or log_rawdata_flag or Gb.initial_icloud3_loading_flag:
            log_hdr = ( f"{self.PyiCloud.username_base}, {method}, Response, "
                        f"{callee.function}/{callee.lineno} ▼")
            log_data = {'code': response.status_code, 'ok': response.ok, 'data': data}

            if retry_cnt >= 2 or Gb.log_rawdata_flag_unfiltered:
                log_data['headers'] = response.headers
            logged = log_rawdata(log_hdr, log_data, log_rawdata_flag=log_rawdata_flag)
            # _log(f"noYK-{log_hdr=}")
            # _log(f"noYK-{data=}")

        # Validating the username/password, code=409 is valid, code=401 is invalid
        if (response.status_code in [401, 409]
                and instr(url, 'setup/authenticate/')):
            return response.status_code

        for header_key, session_arg in HEADER_DATA.items():
            response_header_value = response.headers.get(header_key)
            if response_header_value:
                self.PyiCloud.session_data.update({session_arg: response_header_value})

        # cookie variable reference - self.cookies._cookies['.apple.com']['/']['acn01'].expires
        if self.PyiCloud.validate_aa_upw is False:
            self.cookies.save(ignore_discard=True, ignore_expires=True)
            self.PyiCloud.session_data_token.update(self.PyiCloud.session_data)

            save_json_file(self.PyiCloud.session_dir_filename, self.PyiCloud.session_data)

        if data and "webservices" in data:
            try:
                self.PyiCloud.findme_url_root = data["webservices"]['findme']["url"]
                self.PyiCloud._update_token_pw_file('findme_url', self.PyiCloud.findme_url_root)
            except:
                pass

        try:
            if (response.ok is False
                    and (content_type not in json_mimetypes
                        or response.status_code in AUTHENTICATION_NEEDED_421_450_500)):

                # Handle re-authentication for Find My iPhone
                if (response.status_code in AUTHENTICATION_NEEDED_421_450_500
                            and self.PyiCloud.findme_url_root
                            and url.startswith(self.PyiCloud.findme_url_root)):

                    log_debug_msg(  f"{self.PyiCloud.username_base}, "
                                    f"Authenticating Apple Account ({response.status_code})")

                    kwargs["retried"] = True
                    retry_cnt += 1
                    kwargs['retry_cnt'] = retry_cnt

                    try:
                        # If 421/450/503, retry sign in request
                        if retry_cnt <= 2:
                            self.PyiCloud.authenticate(refresh_session=True)

                    except PyiCloudAPIResponseException:
                        log_debug_msg(f"{self.username_base}, Authentication failed")
                        return self.request(method, url, **kwargs)

                    #if retry_cnt == 0 and response.status_code in AUTHENTICATION_NEEDED_421_450_500:
                    if (retry_cnt <= 2
                            and response.status_code in AUTHENTICATION_NEEDED_421_450_500):
                                                        # CONNECTION_ERROR_503]):
                        log_debug_msg(f"{self.username_base}, "
                                            f"AUTHENTICTION NEEDED, Code-{response.status_code}, "
                                            f"RetryCnt-{retry_cnt}")


                        return self.request(method, url, **kwargs)

                    error_code, error_reason = self._resolve_error_code_reason(data)

                    self._raise_error(response.status_code, error_reason)

        except Exception as err:
            log_exception(err)

        if content_type not in json_mimetypes:
            return data

        error_code, error_reason = self._resolve_error_code_reason(data)

        if error_reason:
            self._raise_error(error_code, error_reason)

        return data

#------------------------------------------------------------------
    def is_internet_available(self):
        '''
        Try to connect to Google servers to determine if the internet is really down
        or there is an error connecting to Apple servers
        '''

        try:
            # Prevent a new status check being requested while waiting for a response
            if Gb.internet_connection_status_waiting_for_response:
                return False

            Gb.internet_connection_status_waiting_for_response = True

            log_debug_msg(  f"Request  Internet Connection status "
                            f"(#{Gb.internet_connection_status_request_cnt}), "
                            f"Sent-{time_now()}")

            # Use TestCode in service_handler > Show Tracking Monitor
            if Gb.internet_connection_test:
                ri = random.randint(1, 61)
                time.sleep(ri)
                raise requests.exceptions.ConnectionError

            # Connect to google.com
            Session.request(self, 'get', "https://8.8.8.8")
            Gb.internet_connection_status_waiting_for_response = False
            return True

        except (requests.exceptions.RetryError,
                requests.exceptions.ConnectionError,
                requests.exceptions.HTTPError,
                requests.exceptions.Timeout,
                OSError,
                requests.exceptions.SSLError,
                requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout,
                requests.exceptions.URLRequired,
                requests.exceptions.TooManyRedirects,
                requests.exceptions.InvalidURL,
                requests.exceptions.InvalidHeader,
                requests.exceptions.InvalidProxyURL,
                requests.exceptions.ChunkedEncodingError,
                requests.exceptions.StreamConsumedError,
                requests.exceptions.RetryError,
                requests.exceptions.UnrewindableBodyError,
                ) as err:
            pass

        except Exception as err:
            log_exception(err)
            pass

        Gb.internet_connection_status_waiting_for_response = False
        return False

#------------------------------------------------------------------
    @staticmethod
    def _resolve_error_code_reason(data):
        '''
        Determine if there is an error message in the data returned.

        Return:
            error code - Error Code
            error reason - Text reason for the error
        '''

        code = reason = None
        if isinstance(data, dict):
            reason = data.get("error")
            reason = reason or data.get("errorMessage")
            reason = reason or data.get("reason")
            reason = reason or data.get("errorReason")

            code = data.get("errorCode")
            code = code or data.get("serverErrorCode")

            if (reason in [1, '1', '2fa Already Processed']
                    or code == 1):
                return None, None

        return code, reason

#------------------------------------------------------------------
    @staticmethod
    def _raise_error(code, reason):

        api_error = None
        if code is None and reason is None:
            return

        if reason in ("ZONE_NOT_FOUND", "AUTHENTICATION_FAILED"):
            reason = ("Please log into https://icloud.com/ to manually "
                    "finish setting up your iCloud service")
            api_error = PyiCloudServiceNotActivatedException(reason, code)

        elif code in AUTHENTICATION_NEEDED_421_450_500: #[204, 421, 450, 500]:
            # log_info_msg(f"Apple Account Verification Code may be needed ({code})")
            return

        elif reason ==  'Missing X-APPLE-WEBAUTH-TOKEN cookie':
            log_info_msg(f"Apple Account Verification Code may be needed, No WebAuth Token")
            return
            # api_error = PyiCloud2FARequiredException()

        # 2fa needed that has already been requested and processed
        elif reason == '2fa Already Processed':
            return

        elif code == 403:
            reason = f"Apple Verification Code not requested ({code})"
            return

        elif code == 400:
            reason = f"Apple Verification Code Invalid ({code})"

        elif code == 404:
            reason = f"iCloud Web Page not Found ({code})"

        elif code == 503:
            reason = f"{HTTP_RESPONSE_CODES[503]}"
            log_info_msg(reason)
            return

        elif reason == "ACCESS_DENIED":
            reason = (reason + ". Please wait a few minutes then try again."
                                "The remote servers might be trying to throttle requests.")

        if api_error is None:
            api_error = PyiCloudAPIResponseException(reason, code)

        log_error_msg(f"{api_error}")
        raise api_error

#------------------------------------------------------------------
    @staticmethod
    def _log_debug_msg(title, display_data):
        ''' Display debug data fields '''
        try:
            log_debug_msg(f"{title} -- {display_data}")
        except:
            log_debug_msg(f"{title} -- None")

#------------------------------------------------------------------
    def _shrink_items(self, prefiltered_dict):
        '''
        Obscure account name and password in rawdata
        '''


        if (prefiltered_dict is None
                or type(prefiltered_dict) is not dict
                or 'data' not in prefiltered_dict
                or type(prefiltered_dict['data']) is not dict):
            return prefiltered_dict

        try:
            filtered_dict    = prefiltered_dict.copy()
            prefiltered_data = prefiltered_dict['data']
            filtered_data    = prefiltered_data.copy()

            if 'trustTokens'   in prefiltered_data:
                filtered_data['trustTokens'] = self._shrink(prefiltered_data['trustTokens'])
            if 'trustToken'    in prefiltered_data:
                filtered_data['trustToken'] = self._shrink(prefiltered_data['trustToken'])
            if 'dsWebAuthToken' in prefiltered_data:
                filtered_data['dsWebAuthToken'] = self._shrink(prefiltered_data['dsWebAuthToken'])
            if 'a' in prefiltered_data:
                filtered_data['a'] = self._shrink(prefiltered_data['a'])

            filtered_dict['data'] = filtered_data

            return filtered_dict

        except Exception as err:
            log_exception(err)
            pass

        return prefiltered_dict

    @property
    def username_base(self):
        return self.PyiCloud.username_base

#------------------------------------------------------------------
    @staticmethod
    def _shrink(value):
        return  f"{value[:6]}………{value[-6:]}"


#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#
#   Exceptions (exceptions.py)
#
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

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
