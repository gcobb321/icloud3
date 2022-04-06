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

VERSION = '3.0.0'



from ..global_variables import GlobalVariables as Gb
from ..const            import (FAMSHR, FMF, FMF_FNAME, FAMSHR_FNAME, HHMMSS_ZERO,
                                NAME, ID, LOCATION, TIMESTAMP, ICLOUD_TIMESTAMP, LOCATION_TIME,
                                TRACKING_METHOD, AIRPODS_FNAME, )
from ..helpers.time     import (time_now_secs, secs_to_time, msecs_to_time, )
from ..helpers.base     import (instr, post_event, post_monitor_msg, _trace, _traceha, log_rawdata)

from uuid       import uuid1
from requests   import Session
from tempfile   import gettempdir
from os         import path, mkdir
from re         import match
import inspect
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
DEVICE_STATUS_ERROR_500 = 500
INVALID_GLOBAL_SESSION_421 = 421
APPLE_ID_VERIFICATION_CODE_INVALID_404 = 404
AUTHENTICATION_NEEDED_421_450_500 = [421, 450, 500]
AUTHENTICATION_NEEDED_450 = 450
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
'''

#--------------------------------------------------------------------
class PyiCloudPasswordFilter(logging.Filter):
    '''Password log hider.'''

    def __init__(self, password):
        super(PyiCloudPasswordFilter, self).__init__(password)

    def filter(self, record):
        message = record.getMessage()
        if self.name in message:
            record.msg = message.replace(self.name, "*" * 8)
            record.args = []

        return True

#--------------------------------------------------------------------
class PyiCloudSession(Session):
    '''iCloud session.'''

    def __init__(self, Service):
        self.Service = Service
        Session.__init__(self)
        self.FindMyiPhone = None

    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ

        # Charge logging to the right service endpoint
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        request_logger = logging.getLogger(module.__name__).getChild("http")

        if self.Service.password_filter not in request_logger.filters:
            request_logger.addFilter(self.Service.password_filter)

        log_msg = (f"{secs_to_time(time_now_secs())}, {method}, {url}")
        self._log_debug_msg("REQUEST", log_msg)
        if Gb.log_rawdata_flag:
            # log_pyicloud_rawdata("PyiCloud_ic3 iCloud Request", log_msg)
            log_rawdata("PyiCloud_ic3 iCloud Request", {'raw': log_msg})

        has_retried = kwargs.get("retried", False)
        kwargs.pop("retried", False)
        retry_cnt = kwargs.get("retry_cnt", 0)
        kwargs.pop("retry_cnt", 0)

        response = super(PyiCloudSession, self).request(method, url, **kwargs)

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        json_mimetypes = ["application/json", "text/json"]

        try:
            data = response.json()
        except:
            data = None

        log_msg = ( f"ResponseCode-{response.status_code} ")
                    # f"ContentType-{content_type}")

        # if (has_retried or response.status_code != 200 or not response.ok):
        if (retry_cnt == 3 or response.status_code != 200 or not response.ok):
            log_msg +=  (f", Headers-{response.headers}")
            self._log_debug_msg("RESPONSE", log_msg)

        if Gb.log_rawdata_flag:
            log_rawdata("PyiCloud_ic3 iCloud Response-Header", {'raw': log_msg})
            log_rawdata("PyiCloud_ic3 iCloud Response-Data", {'filter': data})

        for header in HEADER_DATA:
            if response.headers.get(header):
                session_arg = HEADER_DATA[header]
                self.Service.session_data.update(
                    {session_arg: response.headers.get(header)})

        # Save session_data to file
        with open(self.Service.session_directory_filename, "w") as outfile:
            json.dump(self.Service.session_data, outfile)
            LOGGER.debug(f"Session saved to {self.Service.session_directory_filename}")

        # Save cookies to file
        self.cookies.save(ignore_discard=True, ignore_expires=True)
        LOGGER.debug(f"Cookies saved to {self.Service.cookie_directory_filename}")

        if (not response.ok and (content_type not in json_mimetypes
                or response.status_code in AUTHENTICATION_NEEDED_421_450_500)):

            try:
                # Handle re-authentication for Find My iPhone
                fmip_url = self.Service._get_webservice_url("findme")
                # if has_retried == False and response.status_code == 450 and fmip_url in url:
                # if has_retried is False and response.status_code in [421, 450, 500] and fmip_url in url:
                if retry_cnt == 0 and response.status_code in AUTHENTICATION_NEEDED_421_450_500 and fmip_url in url:
                    LOGGER.debug("Re-authenticating Find My iPhone service")

                    try:
                        # If 450, authentication requires a sign in to the account
                        service = None if response.status_code == 450 else 'find'
                        self.Service.authenticate(True, service)

                    except PyiCloudAPIResponseException:
                        LOGGER.debug("Re-authentication failed")

                    kwargs["retried"] = True
                    retry_cnt += 1
                    kwargs['retry_cnt'] = retry_cnt
                    return self.request(method, url, **kwargs)

            except Exception:
                pass

            # if has_retried is None and response.status_code in [421, 450, 500]:
            # if has_retried is False and response.status_code in [421, 450, 500]:
            if retry_cnt == 0 and response.status_code in AUTHENTICATION_NEEDED_421_450_500:
                self._log_debug_msg("AUTHENTICTION NEEDED, Status Code", response.status_code)

                kwargs["retried"] = True
                retry_cnt += 1
                kwargs['retry_cnt'] = retry_cnt

                return self.request(method, url, **kwargs)

            self._raise_error(response.status_code, response.reason)

        if content_type not in json_mimetypes:
            return response

        try:
            data = response.json()

        except:  # pylint: disable=bare-except
            if not response.ok:
                msg = (f"Error handling data returned from iCloud, {response}")
                request_logger.warning(msg)
            return response

        if isinstance(data, dict):
            reason = data.get("errorMessage")
            reason = reason or data.get("reason")
            reason = reason or data.get("errorReason")

            if not reason and data.get("error"):
                reason = f"Unknown reason, will continue {data=}"

            code = data.get("errorCode")
            code = code or data.get("serverErrorCode")
            if reason:
                self._raise_error(code, reason)

        return response

    def _raise_error(self, code, reason):
        api_error = None
        if reason in ("ZONE_NOT_FOUND", "AUTHENTICATION_FAILED"):
            reason = ("Please log into https://icloud.com/ to manually "
                    "finish setting up your iCloud service")
            api_error = PyiCloudServiceNotActivatedException(reason, code)

        elif code in AUTHENTICATION_NEEDED_421_450_500: #[204, 421, 450, 500]:
            LOGGER.info(f"Authentication needed for Account ({code})")
            return

        elif code in [400, 404]:
            reason = f"Apple ID Validation Code Invalid ({code})"

        elif reason == "ACCESS_DENIED":
            reason = (reason + ".  Please wait a few minutes then try again."
                     "The remote servers might be trying to throttle requests.")

        # elif (self.Service.requires_2sa
        #         and reason == "Missing X-APPLE-WEBAUTH-TOKEN cookie"):
        #     code = 450

        api_error = PyiCloudAPIResponseException(reason, code)

        # LOGGER.error(f"{api_error}")
        raise api_error

    def _log_debug_msg(self, title, display_data):
        ''' Display debug data fields '''
        try:
            LOGGER.debug(f"{title} -- {display_data}")
        except:
            LOGGER.debug(f"{title} -- None")


#--------------------------------------------------------------------
class PyiCloudService(object):
    '''
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    '''

    AUTH_ENDPOINT = "https://idmsa.apple.com/appleauth/auth"
    HOME_ENDPOINT = "https://www.icloud.com"
    SETUP_ENDPOINT = "https://setup.icloud.com/setup/ws/1"

    def __init__(
                    self,
                    apple_id,
                    password=None,
                    cookie_directory=None,
                    session_directory=None,
                    verify=True,
                    client_id=None,
                    with_family=True,
                ):

        if not apple_id:
            msg = "The Apple iCloud account username is not specified"
            raise PyiCloudFailedLoginException(msg)
        if not password:
            msg = "The Apple iCloud account password is not specified"
            raise PyiCloudFailedLoginException(msg)


        LOGGER.info(f"Initializing PyiCloud Service for {apple_id}, "
                    f"CookieDir-{cookie_directory}, "
                    f"SessionDir-{session_directory}")
        self.user = {"accountName": apple_id, "password": password}

        self.apple_id = apple_id
        self.data = {}
        self.client_id = client_id or f"auth-{str(uuid1()).lower()}"
        self.params = {
            "clientBuildNumber": "2021Project52",
            "clientMasteringNumber": "2021B29",
            "ckjsBuildVersion": "17DProjectDev77",
            "clientId": self.client_id[5:],  ## remove auth - not used here just raw client ID
            }
        self.with_family = with_family


        # Make cookie directory if needed
        if cookie_directory:
            self._cookie_directory = path.expanduser(path.normpath(cookie_directory))
        else:
            self._cookie_directory = path.join(gettempdir(), "pyicloud")

        if not path.exists(self._cookie_directory):
            mkdir(self._cookie_directory)

        # Clear session data and make session directory if needed
        self.session_data = {}
        if session_directory:
            self._session_directory = session_directory
        else:
            self._session_directory = path.join(gettempdir(), "pyicloud-session")

        if not path.exists(self._session_directory):
            mkdir(self._session_directory)

        try:
            with open(self.session_directory_filename) as session_f:
                self.session_data = json.load(session_f)
        except:  # pylint: disable=bare-except
            LOGGER.info("Session file does not exist")


        self.password_filter = PyiCloudPasswordFilter(password)
        LOGGER.addFilter(self.password_filter)

        if self.session_data.get("client_id"):
            self.client_id = self.session_data.get("client_id")
        else:
            self.session_data.update({"client_id": self.client_id})

        self.Session = PyiCloudSession(self)

        self.Session.verify = verify
            #"Referer": f"{self.HOME_ENDPOINT}/",
        self.Session.headers.update(
            {"Origin": self.HOME_ENDPOINT,
            "Referer": self.HOME_ENDPOINT,})
            #"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/604.1.25 (KHTML, like Gecko) Version/11.0 Safari/604.1.25",})

        cookie_directory_filename = self.cookie_directory_filename
        self.Session.cookies = cookielib.LWPCookieJar(filename=cookie_directory_filename)
        if path.exists(cookie_directory_filename):
            try:
                self.Session.cookies.load(ignore_discard=True, ignore_expires=True)
                LOGGER.debug(f"Read Cookies from {cookie_directory_filename}")
            except:  # pylint: disable=bare-except
                # Most likely a pickled cookiejar from earlier versions.
                # The cookiejar will get replaced with a valid one after
                # successful authentication.
                LOGGER.warning(f"Failed to read cookie file {cookie_directory_filename}")

        self.authenticate()

#----------------------------------------------------------------------------
    def authenticate(self, refresh_session=False, service=None):
        '''
        Handles authentication, and persists cookies so that
        subsequent logins will not cause additional e-mails from Apple.
        '''

        login_successful = False
        self.authenticate_method = ""

        # Validate token - Consider authenticated if token is valid (POST=validate)
        if (refresh_session is False
                and self.session_data.get("session_token")
                and 'dsid' in self.params):
            LOGGER.info("Checking session token validity")

            try:
                self.data = self._validate_token()
                login_successful = True
                self.authenticate_method += ", ValidateToken"

            except PyiCloudAPIResponseException:
                msg = "Invalid authentication token, will log in from scratch."

        # Authenticate with Service
        if login_successful is False and service != None:
            app = self.data["apps"][service]

            if "canLaunchWithOneFactor" in app and app["canLaunchWithOneFactor"] == True:
                LOGGER.debug("Authenticating as %s for %s" % (self.user["accountName"], service))
                try:
                    self._authenticate_with_credentials_service(service)

                    login_successful = True
                    self.authenticate_method += (f", TrustToken/ServiceLogin")

                except:
                    LOGGER.debug("Could not log into service. Attempting brand new login.")

        # Authenticate - Sign into icloud account (POST=/signin)
        if login_successful is False:
            LOGGER.info(f"Authenticating account {self.user['accountName']} using Account/PasswordSignin")

            data = dict(self.user)
            data["rememberMe"] = True
            data["trustTokens"] = []

            if self.session_data.get("trust_token"):
                data["trustTokens"] = [self.session_data.get("trust_token")]

            headers = self._get_auth_headers()

            if self.session_data.get("scnt"):
                headers["scnt"] = self.session_data.get("scnt")

            if self.session_data.get("session_id"):
                headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

            try:
                req = self.Session.post(
                    f"{self.AUTH_ENDPOINT}/signin",
                    params={"isRememberMeEnabled": "true"},
                    data=json.dumps(data),
                    headers=headers,)
                self.authenticate_method += ", Account/PasswordSignin"

            except PyiCloudAPIResponseException as error:
                msg = "Invalid email/password combination."
                raise PyiCloudFailedLoginException(msg, error)

            self._authenticate_with_token()

        self._webservices = self.data["webservices"]

        self.authenticate_method = self.authenticate_method[2:]
        LOGGER.info(f"Authentication completed successfully, method-{self.authenticate_method}")

#----------------------------------------------------------------------------
    def _authenticate_with_token(self):
        '''Authenticate using session token. Return True if successful.'''
        data = {"accountCountryCode": self.session_data.get("account_country"),
                "dsWebAuthToken": self.session_data.get("session_token"),
                "extended_login": True,
                "trustToken": self.session_data.get("trust_token", ""),
                }

        try:
            req = self.Session.post(f"{self.SETUP_ENDPOINT}/accountLogin"
                                            f"?clientBuildNumber=2021Project52&clientMasteringNumber=2021B29"
                                            f"&clientId={self.client_id[5:]}",
                                        data=json.dumps(data))
            data = req.json()

        except PyiCloudAPIResponseException as error:
            msg = "Invalid authentication token."
            raise PyiCloudFailedLoginException(msg, error)

        self.data = req.json()
        self._update_dsid(self.data)

        return True

#----------------------------------------------------------------------------
    def _authenticate_with_credentials_service(self, service):
        '''Authenticate to a specific service using credentials.'''
        data = {
            "appName": service,
            "apple_id": self.user["accountName"],
            "password": self.user["password"],
            "accountCountryCode": self.session_data.get("account_country"),
            "dsWebAuthToken": self.session_data.get("session_token"),
            "extended_login": True,
            "trustToken": self.session_data.get("trust_token", ""),
        }

        try:
            self.Session.post(f"{self.SETUP_ENDPOINT}/accountLogin"
                        f"?clientBuildNumber=2021Project52&clientMasteringNumber=2021B29"
                        f"&clientId={self.client_id[5:]}",
                        data=json.dumps(data))

            self.data = self._validate_token()

        except PyiCloudAPIResponseException as error:
            msg = "Invalid email/password combination."
            raise PyiCloudFailedLoginException(msg, error)

#----------------------------------------------------------------------------
    def _validate_token(self):
        '''Checks if the current access token is still valid.'''
        LOGGER.debug("Checking session token validity")
        try:
            req = self.Session.post("%s/validate" % self.SETUP_ENDPOINT, data="null")
            LOGGER.debug("Session token is still valid")
            return req.json()

        except PyiCloudAPIResponseException as err:
            LOGGER.debug("Invalid authentication token")
            raise err

#----------------------------------------------------------------------------
    def _update_dsid(self, data):
        try:
            if 'dsInfo' in data:  ## check self.data returned and contains dsid
                if 'dsid' in data['dsInfo']:        # as above
                    self.params["dsid"]= str(data["dsInfo"]["dsid"])
            else:
                if 'dsid' in self.params:
                    self.params.pop("dsid")  ## if no dsid given delete it from self.params - until returned.  Otherwise is passing default incorrect dsid

        except:
            LOGGER.debug(u"Error setting dsid field.")
            if 'dsid' in self.params:
                self.params.pop("dsid")  ## if error, self.data None/empty delete

        return

#----------------------------------------------------------------------------
    def _get_auth_headers(self, overrides=None):
        headers = {
            "Accept": "*/*",
            "Content-Type": "application/json",
            "X-Apple-OAuth-Client-Id": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
            "X-Apple-OAuth-Client-Type": "firstPartyAuth",
            "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
            "X-Apple-OAuth-Require-Grant-Code": "true",
            "X-Apple-OAuth-Response-Mode": "web_message",
            "X-Apple-OAuth-Response-Type": "code",
            "X-Apple-OAuth-State": self.client_id,
            "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
        }
            #"X-Apple-OAuth-State": "auth-" + self.client_id,

        if overrides:
            headers.update(overrides)
        return headers

#----------------------------------------------------------------------------
    @property
    def cookie_directory_filename(self):
        '''Get path for cookiejar file.'''
        return path.join(
            self._cookie_directory,
            "".join([c for c in self.user.get("accountName") if match(r"\w", c)]),)

    @property
    def session_directory_filename(self):
        '''Get path for session data file.'''
        return path.join(
            self._session_directory,
            "".join([c for c in self.user.get("accountName") if match(r"\w", c)]),)

    @property
    def authentication_method(self):
        '''
        Returns the type of authentication method performed
            - None = No authentication done
            - TrustToken = Authentication using trust token (/accountLogin)
            - ValidateToken = Trust token was validated (/validate)
            - AccountSignin = Signed into the account (/signin)
        '''
        authenticate_method = self.authenticate_method
        self.authenticate_method = ""
        return authenticate_method

    @property
    def requires_2sa(self):
        '''Returns True if two-step authentication is required.'''
        return self.data.get("dsInfo", {}).get("hsaVersion", 0) >= 1 and (
            self.data.get("hsaChallengeRequired", False) or not self.is_trusted_session)

    @property
    def requires_2fa(self):
        '''Returns True if two-factor authentication is required.'''
        needs_2fa_flag = self.data["dsInfo"].get("hsaVersion", 0) == 2 and (
            self.data.get("hsaChallengeRequired", False) or not self.is_trusted_session)

        if needs_2fa_flag:
            LOGGER.debug(f"NEEDS-2FA, is_trusted_session-{self.is_trusted_session}, data-{self.data}")
        return needs_2fa_flag

    @property
    def is_trusted_session(self):
        '''Returns True if the session is trusted.'''
        return self.data.get("hsaTrustedBrowser", False)

    @property
    def trusted_devices(self):
        '''Returns devices trusted for two-step authentication.'''
        url = f"{self.SETUP_ENDPOINT}/listDevices"
        request = self.Session.get(url, params=self.params)
        return request.json().get("devices")

#----------------------------------------------------------------------------
    def send_verification_code(self, device):
        '''Requests that a verification code is sent to the given device.'''
        data = json.dumps(device)
        request = self.Session.post(
            "%s/sendVerificationCode" % self.SETUP_ENDPOINT,
            params=self.params,
            data=data,)
        return request.json().get("success", False)

#----------------------------------------------------------------------------
    def validate_verification_code(self, device, code):
        '''Verifies a verification code received on a trusted device.'''
        device.update({"verificationCode": code, "trustBrowser": True})
        data = json.dumps(device)

        try:
            self.Session.post(
                "%s/validateVerificationCode" % self.SETUP_ENDPOINT,
                params=self.params,
                data=data,)
        except PyiCloudAPIResponseException as error:
            if error.code == -21669:
                # Wrong verification code
                return False
            raise

        # Re-authenticate, which will both update the HSA data, and
        # ensure that we save the X-APPLE-WEBAUTH-HSA-TRUST cookie.
        self.authenticate()

        return not self.requires_2sa

#----------------------------------------------------------------------------
    def validate_2fa_code(self, code):
        '''Verifies a verification code received via Apple's 2FA system (HSA2).'''
        data = {"securityCode": {"code": code}}

        headers = self._get_auth_headers({"Accept": "application/json"})

        if self.session_data.get("scnt"):
            headers["scnt"] = self.session_data.get("scnt")

        if self.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

        try:
            self.Session.post(
                f"{self.AUTH_ENDPOINT}/verify/trusteddevice/securitycode",
                    data=json.dumps(data), headers=headers,)

        except PyiCloudAPIResponseException as error:
            # Wrong verification code
            if error.code == -21669:
                LOGGER.error("Code verification failed")
                return False
            raise

        LOGGER.debug("Code verification successful")

        self.trust_session()
        return not self.requires_2sa

#----------------------------------------------------------------------------
    def trust_session(self):
        '''Request session trust to avoid user log in going forward.'''
        headers = self._get_auth_headers()

        if self.session_data.get("scnt"):
            headers["scnt"] = self.session_data.get("scnt")

        if self.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.session_data.get("session_id")

        try:
            self.Session.get(
                f"{self.AUTH_ENDPOINT}/2sv/trust",
                headers=headers,)

            self._authenticate_with_token()
            return True
        except PyiCloudAPIResponseException:
            LOGGER.error("Session trust failed")
            return False

#----------------------------------------------------------------------------
    def _get_webservice_url(self, ws_key):
        '''Get webservice URL, raise an exception if not exists.'''
        if self._webservices.get(ws_key) is None:
            raise PyiCloudServiceNotActivatedException(
                "Webservice not available", ws_key)

        return self._webservices[ws_key]["url"]

#----------------------------------------------------------------------------
    @property
    def famshr_devices(self):
        '''
        Initializes the FindMyiPhone class, refresh the iCloud device data for all
        devices and create the PyiCloud_DevData object containing the data for all locatible devices.
        '''
        service_root = self._get_webservice_url("findme")
        Gb.PyiCloud_FamilySharing = PyiCloud_FamilySharing(service_root, self.Session, self.params, self.with_family)

        return Gb.PyiCloud_FamilySharing.response

#----------------------------------------------------------------------------
    @property
    def family_sharing_object(self):
        '''
        Initializes the FindMyiPhone object, refresh the iCloud device data for all
        devices and create the PyiCloud_DevData object containing the data for all locatible devices.
        '''
        try:
            service_root = self._get_webservice_url("findme")
            _PyiCloud_FamilySharing = PyiCloud_FamilySharing(service_root, self.Session, self.params, self.with_family)

            return _PyiCloud_FamilySharing

        except Exception as err:
            LOGGER.exception(err)
            return None

#----------------------------------------------------------------------------
    @property
    def refresh_famshr_data(self):
        '''
        Refresh the iCloud device data for all devices and update the PyiCloud_DevData object
        for all locatible devices that are being tracked by iCloud3.
        '''

        PyiCloud_FamilySharing.refresh_client()
        return

#----------------------------------------------------------------------------
    @property
    def find_my_friends_object(self):       #friends(self):
        '''Gets the 'Friends' service.'''

        try:
            service_root = self._get_webservice_url("findme")  #fmf
            _PyiCloud_FindMyFriends = PyiCloud_FindMyFriends(service_root, self.Session, self.params)

            return _PyiCloud_FindMyFriends

        except Exception as err:
            LOGGER.exception(err)
            return None

#----------------------------------------------------------------------------
    def play_sound(self, device_id, subject="Find My iPhone Alert"):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''
        # self.authenticate_method = ""
        service_root = self._get_webservice_url("findme")
        data = PyiCloud_FamilySharing(service_root, self.Session, self.params, self.with_family,
                    task="PlaySound", device_id=device_id, subject=subject)
        return data


    def __repr__(self):
        return (f"<PyiCloudService: {self.username}>")


####################################################################################
#
#   Find my iPhone service
#
####################################################################################
class PyiCloud_FamilySharing(object):
    '''
    The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.
    '''

    def __init__(self, service_root, Session, params, with_family=False, task="RefreshData",
                device_id=None, subject=None, message=None,
                sounds=False, number="", newpasscode=""):

        self.Session     = Session
        self.params      = params
        self.with_family = with_family
        self.task        = task
        self.devices_without_location_data = []

        fmip_endpoint          = f"{service_root}/fmipservice/client/web"
        self._fmip_refresh_url = f"{fmip_endpoint}/refreshClient"
        self._fmip_sound_url   = f"{fmip_endpoint}/playSound"
        self._fmip_message_url = f"{fmip_endpoint}/sendMessage"
        self._fmip_lost_url    = f"{fmip_endpoint}/lostDevice"

        fmiDict =   {"clientContext":
                        { "appName": "Home Assistant", "appVersion": "0.118",
                        "inactiveTime": 1, "apiVersion": "2.2.2" }
                    }

        if task == "PlaySound":
            if device_id:
                self.play_sound(device_id, subject)

        elif task == "Message":
            if device_id:
                self.display_message(device_id, subject, message)

        elif task == "LostDevice":
            if device_id:
                self.lost_device(device_id, number, message, newpasscode="")

        else:
            self.Session.FindMyiPhone = self
            self.refresh_client(device_id)

    @property
    def timestamp_field(self):
        return ICLOUD_TIMESTAMP

    @property
    def tracking_method(self):
        return FAMSHR_FNAME

#----------------------------------------------------------------------------
    def refresh_client(self, _device_id=None, _with_family=None, refreshing_poor_loc_flag=False):
        '''
        Refreshes the FindMyiPhoneService endpoint,
        This ensures that the location data is up-to-date.
        '''
        selected_device = _device_id   if _device_id else "all"
        fmly_param      = _with_family if _with_family is not None else self.with_family

        req = self.Session.post(
            self._fmip_refresh_url,
            params=self.params,
            data=json.dumps(
                {"clientContext":
                    {"fmly": fmly_param, "shouldLocate": True, "selectedDevice": selected_device,
                        "deviceListVersion": 1, }
                }
            ),
        )

        try:
            self.response = req.json()

        except Exception as err:
            LOGGER.exception(err)
            self.response = {}
            LOGGER.debug("No data returned from fmi refresh request")

        # content contains the device data and the location data
        for device_info in self.response.get("content", {}):
            device_id = device_info[ID]
            device_name = device_info[NAME]
            monitor_msg = ''

            # if instr(device_name, u'\xa0'):
            device_name       = device_name.replace(u'\xa0', ' ')
            device_name       = device_name.replace(u'\2019', "'")
            device_info[NAME] = device_name

            # if device_id.startswith('/UNm01d3'): device_info[LOCATION] = {}

            # Do not add device is no location data
            if (LOCATION not in device_info
                    or device_info[LOCATION] == {}
                    or device_info[LOCATION] is None):
                if device_id not in self.devices_without_location_data:
                    self.devices_without_location_data.append(device_id)
                    monitor_msg = (f"NOT ADDED FamShr PyiCloud_DevData-"
                                    f"{device_name}, No Location Data, (#{device_id[:10]})")
                    if Gb.EvLog:
                        post_monitor_msg(monitor_msg)
                    else:
                        LOGGER.debug(monitor_msg)
                continue

            # Update PyiCloud_DevData with data just received for tracked devices
            if device_id in Gb.PyiCloud_DevData_by_device_id:
                if  device_id in Gb.Devices_by_icloud_device_id:
                    _PyiCloud_DevData = Gb.PyiCloud_DevData_by_device_id[device_id]
                    _PyiCloud_DevData.update(device_info)
                    monitor_msg = (f"UPDATED FamShr PyiCloud_DevData, "
                                    f"{device_name}, (#{device_id[:10]})")
                else:
                    monitor_msg = (f"NOT UPDATED FamShr, Unknown iCloud device_id-(#{device_id[:10]})")

            else:
                _PyiCloud_DevData  = PyiCloud_DevData(
                    device_id, device_info, self.Session, self.params,
                    FmpiOrFmfSvcMgr=self, device_name=device_name,
                    sound_url=self._fmip_sound_url, lost_url=self._fmip_lost_url,
                    message_url=self._fmip_message_url,)

                Gb.PyiCloud_DevData_by_device_id[device_id]        = _PyiCloud_DevData
                Gb.PyiCloud_DevData_by_device_id_famshr[device_id] = _PyiCloud_DevData

                monitor_msg = (f"ADDED FamShr PyiCloud_DevData-#{device_id[:10]}, {device_name}")

            if Gb.EvLog and monitor_msg.startswith('NOT UPDATED') is False:
                post_monitor_msg(monitor_msg)
            else:
                LOGGER.debug(monitor_msg)

        if not Gb.PyiCloud_DevData_by_device_id:
            raise PyiCloudNoDevicesException()

#----------------------------------------------------------------------------
    def play_sound(self, device_id, subject):
        '''
        Send a request to the device to play a sound.
        It's possible to pass a custom message by changing the `subject`.
        '''
        if not subject:
            subject = "Find My iPhone Alert"

        data = json.dumps(
            {"device": device_id, "subject": subject, "clientContext": {"fmly": True}, }
        )
        self.Session.post(self._fmip_sound_url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def display_message(self, device_id, subject="Find My iPhone Alert",
                message="This is a note", sounds=False):
        '''
        Send a request to the device to display a message.
        It's possible to pass a custom message by changing the `subject`.
        '''
        data = json.dumps(
            {"device": device_id, "subject": subject, "sound": sounds,
                "userText": True, "text": message, }
        )
        self.Session.post(self._fmip_message_url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def lost_device(self, device_id, number, message="This iPhone has been lost. Please call me.",
                newpasscode=""):
        '''
        Send a request to the device to trigger 'lost mode'.

        The device will show the message in `text`, and if a number has
        been passed, then the person holding the device can call
        the number without entering the passcode.
        '''
        data = json.dumps(
            {"text": message, "userText": True, "ownerNbr": number, "lostModeEnabled": True,
                "trackingEnabled": True, "device": device_id, "passcode": newpasscode, }
        )
        self.Session.post(self._fmip_lost_url, params=self.params, data=data)
        return

#----------------------------------------------------------------------------
    def __repr__(self):
        return (f"<PyiCloud_FamilySharing: >")


####################################################################################
#
#   Find my Friends service
#
####################################################################################
class PyiCloud_FindMyFriends(object):
    '''
    The 'Find My' (aka 'Find My Friends') iCloud service

    This connects to iCloud and returns friend's data including
    latitude and longitude.
    '''

    def __init__(self, service_root, Session, params):

        # Gb.PyiCloud_FindMyFriends = self
        self.Session          = Session
        self.params           = params
        self._service_root    = service_root
        self._friend_endpoint = f"{self._service_root}/fmipservice/client/fmfWeb/initClient"
        self.refresh_always   = False
        self.response         = {}
        self.devices_without_location_data = []

        self.refresh_client()

    @property
    def timestamp_field(self):
        return TIMESTAMP

    @property
    def tracking_method(self):
        return FMF_FNAME

#----------------------------------------------------------------------------
    def refresh_client(self, refreshing_poor_loc_flag=False):
        '''
        Refreshes all data from 'Find My' endpoint,
        '''
        params = dict(self.params)

        # This is a request payload we mock to fetch the data
        mock_payload = json.dumps(
            {
                "clientContext": {
                    "appVersion": "1.0",
                    "contextApp": "com.icloud.web.fmf",
                    "mapkitAvailable": True,
                    "productType": "fmfWeb",
                    "tileServer": "Apple",
                    "userInactivityTimeInMS": 537,
                    "windowInFocus": False,
                    "windowVisible": True,
                },
                "dataContext": None,
                "serverContext": None,
            }
        )

        response = self.Session.post(self._friend_endpoint, data=mock_payload, params=params)

        try:
            self.response = response.json()
        except:
            self.response = {}
            LOGGER.debug("No data returned on friends refresh request")

        try:
            device_name = ''
            for device_info in self.response.get('locations', {}):
                device_id   = device_info[ID]
                monitor_msg = ''

                # Device was already set up or rejected
                if device_id in self.devices_without_location_data:
                    continue

                # Update PyiCloud_DevData with data just received for tracked devices
                if device_id in Gb.PyiCloud_DevData_by_device_id:
                    if device_id in Gb.Devices_by_icloud_device_id:
                        _PyiCloud_DevData = Gb.PyiCloud_DevData_by_device_id[device_id]
                        _PyiCloud_DevData.update(device_info)

                        monitor_msg = (f"UPDATED FmF PyiCloud_DevData, ({device_id[:8]})")

                    else:
                        monitor_msg = (f"NOT UPDATED FmF, Unknown iCloud device_id-({device_id[:8]})")

                    if Gb.EvLog and monitor_msg.startswith('NOT UPDATED') is False:
                        post_monitor_msg(monitor_msg)
                    else:
                        LOGGER.debug(monitor_msg)

                else:
                    _PyiCloud_DevData = PyiCloud_DevData(
                        device_id, device_info, self.Session, self.params,
                        FmpiOrFmfSvcMgr=self, device_name=device_name,
                        sound_url=None, lost_url=None, message_url=None,)

                    Gb.PyiCloud_DevData_by_device_id[device_id]     = _PyiCloud_DevData
                    Gb.PyiCloud_DevData_by_device_id_fmf[device_id] = _PyiCloud_DevData

                    monitor_msg = (f"ADDED FmF PyiCloud_DevData, ({device_id[:8]})")
                    if (LOCATION not in device_info
                            or device_info[LOCATION] == {}
                            or device_info[LOCATION] is None):
                        _PyiCloud_DevData.locatable_flag = False
                        monitor_msg += " (Not locatable, No location data)"

                    if Gb.EvLog:
                            post_monitor_msg(monitor_msg)
                    else:
                        LOGGER.debug(monitor_msg)

            return self.response

        except Exception as err:
            LOGGER.exception(err)
            return None

#----------------------------------------------------------------------------
    def contact_id_for(self, identifier, default=None):
        '''
        Returns the contact id of your friend with a given identifier
        '''
        lookup_key = "phones"
        if "@" in identifier:
            lookup_key = "emails"

        def matcher(item):
            '''Returns True iff the identifier matches'''
            hit = item.get(lookup_key)
            if not isinstance(hit, list):
                return hit == identifier
            return any([el for el in hit if el == identifier])

        candidates = [
            item.get(ID, default)
            for item in self.contact_details
            if matcher(item)]
        if not candidates:
            return default
        return candidates[0]

#----------------------------------------------------------------------------
    def location_of(self, contact_id, default=None):
        '''
        Returns the location of your friend with a given contact_id
        '''
        candidates = [
            item.get("location", default)
            for item in self.locations
            if item.get(ID) == contact_id]
        if not candidates:
            return default
        return candidates[0]

#----------------------------------------------------------------------------
    @property
    def data(self):
        '''
        Convenience property to return data from the 'Find My' endpoint.
        Call `refresh_client()` before property access for latest data.
        '''
        if not self.response:
            self.refresh_client()
        return self.response

    @property
    def locations(self):
        '''Returns a list of your friends' locations'''
        return self.response.get("locations", [])

    @property
    def followers(self):
        '''Returns a list of friends who follow you'''
        return self.response.get("followers")

    @property
    def following(self):
        '''Returns a list of friends who you follow'''
        return self.response.get("following")

    @property
    def contact_details(self):
        '''Returns a list of your friends contact details'''
        return self.response.get("contactDetails")

    @property
    def my_prefs(self):
        '''Returns a list of your own preferences details'''
        return self.response.get("myPrefs")

    def __repr__(self):
        return (f"<PyiCloud_FindMyFriends: >")

    @property
    def device_identifier(self):
        return  (f"{self.response.get('firstName', '')} {self.response.get('lastName', '')}").strip()
####################################################################################
#
#   PyiCloud_DevData Object - Store all of the data related to the device. It is created
#   and updated in the FindMyPhoneSvcMgr.refresh_client module and is based on the
#   device_id. The Global Variable PyiCloud_DevData_by_device_id contains the object
#   pointer for each device_id.
#
#       - content = all of the data for this device_id
#
####################################################################################
class PyiCloud_DevData(object):
    '''
    PyiCloud_Device stores all the device data for Family Sharing and Find-my-Friends
    tracking methods. FamShr device_data contains the device info and the location
    FmF contains the location
    '''

    def __init__(self, device_id, device_data, Session, params, FmpiOrFmfSvcMgr,
                        device_name, sound_url=None, lost_url=None, message_url=None, ):

        self.device_id       = device_id
        self.device_data     = device_data
        self.FmpiOrFmfSvcMgr = FmpiOrFmfSvcMgr
        self.Session         = Session
        self.params          = params
        self.name            = device_name
        self.update_secs     = time_now_secs()
        self.tracking_method = FmpiOrFmfSvcMgr.tracking_method
        self.timestamp_field = FmpiOrFmfSvcMgr.timestamp_field
        self.locatable_flag  = True
        self.location_secs   = 0
        self.location_time   = HHMMSS_ZERO

        self.sound_url   = sound_url
        self.lost_url    = lost_url
        self.message_url = message_url

        self.change_utc_to_local_time()
        self.device_data[TRACKING_METHOD] = self.tracking_method

    @property
    def device_id8(self):
        return self.device_id[:8]
    @property
    def tracking_method_FMF(self):
        return (self.tracking_method in [FMF, FMF_FNAME])

    @property
    def tracking_method_FAMSHR(self):
        return (self.tracking_method in [FAMSHR, FAMSHR_FNAME])


    def update(self, device_data):
        '''Update the device data.'''
        self.device_data.clear()
        self.device_data.update(device_data)
        self.change_utc_to_local_time()
        self.device_data[TRACKING_METHOD] = self.tracking_method
        return

    @property
    def device_identifier(self):
        if self.tracking_method_FAMSHR:
            display_name = self.device_data['deviceDisplayName'].split(' (')[0]
            display_name = display_name.replace('Series ', '')
            if self.device_data.get('rawDeviceModel').startswith(AIRPODS_FNAME):
                device_class = AIRPODS_FNAME
            else:
                device_class = self.device_data.get('deviceClass', '')
            return (f"{display_name}/{device_class}")

        elif self.tracking_method_FMF:
            full_name = (f"{self.device_data.get('firstName', '')} {self.device_data.get('lastName', '')}").strip()
            return full_name
        else:
            return self.name


#----------------------------------------------------------------------------
    def status(self, additional_fields=[]):  # pylint: disable=dangerous-default-value
        '''
        Returns status information for device.
        This returns only a subset of possible properties.
        '''
        self.FmpiOrFmfSvcMgr.refresh_client(self.device_id, with_family=True)

        fields = ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]
        fields += additional_fields

        properties = {}
        for field in fields:
            properties[field] = self.location.get(field)

        return properties

#----------------------------------------------------------------------------
    def change_utc_to_local_time(self):

        try:
            if self.locatable_flag == False:
                return

            # self.device_data[LOCATION][TIMESTAMP]     = round(self.device_data[LOCATION][self.timestamp_field] / 1000)
            self.device_data[LOCATION][TIMESTAMP]     = int(self.device_data[LOCATION][self.timestamp_field] / 1000)
            self.device_data[LOCATION][LOCATION_TIME] = secs_to_time(self.device_data[LOCATION][TIMESTAMP])
            self.location_secs = self.device_data[LOCATION][TIMESTAMP]
            self.location_time = self.device_data[LOCATION][LOCATION_TIME]

        except TypeError:
            # This will happen if there is no location data in device_data
            self.locatable_flag = False
            self.device_data[LOCATION] = {TIMESTAMP: 0, LOCATION_TIME: HHMMSS_ZERO}
            self.location_secs = 0
            self.location_time = HHMMSS_ZERO

        except Exception as err:
            LOGGER.exception(err)

        self.update_secs = time_now_secs()

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
        return f"<PyiCloud_DevData: {self.name}-{self.tracking_method}-{self.device_id[:8]}>"



####################################################################################
#
#   Exceptions (exceptions.py)
#
####################################################################################
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
        message = reason or ""
        if code:
            message += (f" (Status Code {code})")
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
class PyiCloud2SARequiredException(PyiCloudException):
    '''iCloud 2SA required exception.'''
    def __init__(self, apple_id):
        message = f"Two-Step Authentication (2SA) Required for Account {apple_id}"
        super(PyiCloud2SARequiredException, self).__init__(message)

#----------------------------------------------------------------------------
class PyiCloudNoStoredPasswordAvailableException(PyiCloudException):
    '''iCloud no stored password exception.'''
    pass

#----------------------------------------------------------------------------
class PyiCloudNoDevicesException(PyiCloudException):
    '''iCloud no device exception.'''
    pass
