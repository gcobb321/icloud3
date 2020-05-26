"""
Customized version of pyicloud.py to support iCloud3 Custom Component

Platform that supports importing data from the iCloud Location Services
and Find My Friends api routines. Modifications to pyicloud were made
by various people to include:
    - Original pyicloud - picklepete & Quantame
                        - https://github.com/picklepete

    - Updated and maintained by - Quantame

    - Find My Friends Update - Z Zeleznick

The piclkepete version used imports for the services, utilities and exceptions
modules. They have been modified and are now maintained by Quantame & Z Zeleznick.
These modules have been incorporated into the pyicloud_ic3.py version used by iCloud3.
"""

VERSION = '2.2.0'

"""Library base file."""
from six import PY2, string_types
from uuid import uuid1
import inspect
import json
import logging
from requests import Session
import sys
from tempfile import gettempdir
from os import path, mkdir
from re import match
import http.cookiejar as cookielib

LOGGER = logging.getLogger(__name__)


class PyiCloudPasswordFilter(logging.Filter):
    """Password log hider."""

    def __init__(self, password):
        super(PyiCloudPasswordFilter, self).__init__(password)

    def filter(self, record):
        message = record.getMessage()
        if self.name in message:
            record.msg = message.replace(self.name, "*" * 8)
            record.args = []

        return True


class PyiCloudSession(Session):
    """iCloud session."""

    def __init__(self, service):
        self.service = service
    #    self.count450 = 0
        Session.__init__(self)

    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ

        # Charge logging to the right service endpoint
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        request_logger = logging.getLogger(module.__name__).getChild("http")
        if self.service.password_filter not in request_logger.filters:
            request_logger.addFilter(self.service.password_filter)

        request_logger.debug(f"{method}, {url}, {kwargs.get('data', '')}")
        #request_logger.info(f"{method}, {url}, {kwargs.get("data", "")}"")

        kwargs_retry_flag = kwargs.get("retried", None)
        kwargs.pop("retried", None)
        response = super(PyiCloudSession, self).request(method, url, **kwargs)

        content_type = response.headers.get("Content-Type", "").split(";")[0]
        json_mimetypes = ["application/json", "text/json"]

        #try:
            #if response is not None:
            #    LOGGER.info(f">>>>> 102, response.text={response.text}")

        #except:
        #    pass
        #Error 450 Test Code Start-Generate 450 error every 6th request to reauthenticate account
        #self.count450 += 1
        #request_logger.debug(f"pyicloud request count {self.count450}")
        #test_response_ok = response.ok
        #test_response_status_code = response.status_code
        #if ((self.count450 % 6) == 0):
        #    test_response_ok = False
        #    test_response_status_code = 450


        #if not test_response_ok:
        #    if kwargs_retry_flag is None and test_response_status_code == 450:
        #        self.count450 -= 1
        kwargs_retry_flag = True
        if not response.ok and content_type not in json_mimetypes:
            if kwargs_retry_flag is None and response.status_code == 450:
                message = ("Apple Web Service error, Authentication needed")

                api_error = PyiCloudAPIResponseException(
                    message, response.status_code, retry=True
                )

                request_logger.info(api_error)
                kwargs["retried"] = True
                return self.request(method, url, **kwargs)
            self._raise_error(response.status_code, response.reason)

        if content_type not in json_mimetypes:
            return response

        try:
            data = response.json()
        except:  # pylint: disable=bare-except
            request_logger.warning("Failed to parse response with JSON mimetype")
            return response

        request_logger.debug(data)
        #request_logger.info(data)

        reason = data.get("errorMessage")
        reason = reason or data.get("reason")
        reason = reason or data.get("errorReason")
        if not reason and isinstance(data.get("error"), string_types):
            reason = data.get("error")
        if not reason and data.get("error"):
            reason = "Unknown reason"

        code = data.get("errorCode")
        if not code and data.get("serverErrorCode"):
            code = data.get("serverErrorCode")

        if reason:
            self._raise_error(code, reason)

        return response

    def _raise_error(self, code, reason):
        if (
            self.service.requires_2sa
            and reason == "Missing X-APPLE-WEBAUTH-TOKEN cookie"
        ):
            raise PyiCloud2SARequiredException(self.service.user["apple_id"])
        if code in ("ZONE_NOT_FOUND", "AUTHENTICATION_FAILED"):
            reason = (
                "Please log into https://icloud.com/ to manually "
                "finish setting up your iCloud service"
            )
            api_error = PyiCloudServiceNotActivatedException(reason, code)
            LOGGER.error(api_error)

            raise (api_error)
        if code == "ACCESS_DENIED":
            reason = (
                reason + ".  Please wait a few minutes then try again."
                "The remote servers might be trying to throttle requests."
            )

        api_error = PyiCloudAPIResponseException(reason, code)
        LOGGER.error(api_error)
        raise api_error


class PyiCloudService(object):
    """
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    """

    HOME_ENDPOINT = "https://www.icloud.com"
    SETUP_ENDPOINT = "https://setup.icloud.com/setup/ws/1"
    #"logout_no_services": "https://setup.icloud.com/setup/ws/1/logout",

    def __init__(
        self,
        apple_id,
        password=None,
        cookie_directory=None,
        verify=True,
        client_id=None,
        with_family=True,
    ):
        if password is None:
            password = get_password_from_keyring(apple_id)

        self.data = {}
        self.client_id = client_id or str(uuid1()).upper()
        self.with_family = with_family
        self.user = {"apple_id": apple_id, "password": password}

        self.password_filter = PyiCloudPasswordFilter(password)
        LOGGER.addFilter(self.password_filter)

        self._base_login_url = f"{self.SETUP_ENDPOINT}/login"

        if cookie_directory:
            self._cookie_directory = path.expanduser(path.normpath(cookie_directory))
        else:
            self._cookie_directory = path.join(gettempdir(), "pyicloud")

        self.session = PyiCloudSession(self)
        self.session.verify = verify
        self.session.headers.update(
            {
                "Origin": self.HOME_ENDPOINT,
                "Referer": f"{self.HOME_ENDPOINT}/",
                "User-Agent": "Opera/9.52 (X11; Linux i686; U; en)",
            }
        )

        cookiejar_path = self._get_cookiejar_path()
        self.session.cookies = cookielib.LWPCookieJar(filename=cookiejar_path)
        if path.exists(cookiejar_path):
            try:
                self.session.cookies.load()
                LOGGER.debug(f"Read cookies from {cookiejar_path}")
            except:  # pylint: disable=bare-except
                # Most likely a pickled cookiejar from earlier versions.
                # The cookiejar will get replaced with a valid one after
                # successful authentication.
                LOGGER.warning(f"Failed to read cookiejar {cookiejar_path}")

        self.params = {
            "clientBuildNumber": "17DHotfix5",
            "clientMasteringNumber": "17DHotfix5",
            "ckjsBuildVersion": "17DProjectDev77",
            "ckjsVersion": "2.0.5",
            "clientId": self.client_id,
        }

        self.authenticate()

        self._files = None
        self._photos = None

    def authenticate(self):
        """
        Handles authentication, and persists the X-APPLE-WEB-KB cookie so that
        subsequent logins will not cause additional e-mails from Apple.
        """

        LOGGER.info(f"Authenticating as {self.user['apple_id']}")

        data = dict(self.user)

        # We authenticate every time, so "remember me" is not needed
        #data.update({"extended_login": False})
        data.update({"extended_login": True})

        try:
            req = self.session.post(
                self._base_login_url, params=self.params, data=json.dumps(data)
            )
        except PyiCloudAPIResponseException as error:
            msg = "Invalid email/password combination."
            raise PyiCloudFailedLoginException(msg, error)

        self.data = req.json()
        self.params.update({"dsid": self.data["dsInfo"]["dsid"]})
        self._webservices = self.data["webservices"]

        if not path.exists(self._cookie_directory):
            mkdir(self._cookie_directory)
        self.session.cookies.save()
        LOGGER.debug(f"Cookies saved to {self._get_cookiejar_path()}")

        LOGGER.info("Authentication completed successfully")
        LOGGER.debug(self.params)

    def _get_cookiejar_path(self):
        """Get path for cookiejar file."""
        return path.join(
            self._cookie_directory,
            "".join([c for c in self.user.get("apple_id") if match(r"\w", c)]),
        )

    @property
    def requires_2sa(self):
        """Returns True if two-step authentication is required."""
        return (
            self.data.get("hsaChallengeRequired", False)
            and self.data["dsInfo"].get("hsaVersion", 0) >= 1
        )
        # FIXME: Implement 2FA for hsaVersion == 2  # pylint: disable=fixme

    @property
    def trusted_devices(self):
        """Returns devices trusted for two-step authentication."""
        request = self.session.get(
            f"{self.SETUP_ENDPOINT}/listDevices", params=self.params
        )
        return request.json().get("devices")

    def send_verification_code(self, device):
        """Requests that a verification code is sent to the given device."""
        data = json.dumps(device)
        request = self.session.post(
            f"{self.SETUP_ENDPOINT}/sendVerificationCode",
            params=self.params,
            data=data,
        )
        return request.json().get("success", False)

    def validate_verification_code(self, device, code):
        """Verifies a verification code received on a trusted device."""
        device.update({
            'verificationCode': code,
            'trustBrowser': True})
        data = json.dumps(device)

        try:
            self.session.post(
                f"{self.SETUP_ENDPOINT}/validateVerificationCode",
                params=self.params,
                data=data,
            )
        except PyiCloudAPIResponseException as error:
            if error.code == -21669:
                # Wrong verification code
                return False
            raise

        # Re-authenticate, which will both update the HSA data, and
        # ensure that we save the X-APPLE-WEBAUTH-HSA-TRUST cookie.
        self.authenticate()

        return not self.requires_2sa

    def logout(self):
        """ Logout from iCloud """
        try:
            req = self.session.post(
                f"{self.SETUP_ENDPOINT}/logout",
                params=self.params,
            )
        except Exception as error:
            msg = f"Error Logging out of Apple Web Services - {error}"
            api_error = PyiCloudAPIResponseException(msg, 1)
            LOGGER.error(api_error)
            raise api_error

    def close_session(self):
        """ Close current Session """
        try:
            req = self.session.close()

        except Exception as error:
            msg = f"Error Closing Session - {error}"
            api_error = PyiCloudAPIResponseException(msg, 1)
            LOGGER.error(api_error)
            raise api_error


    def _get_webservice_url(self, ws_key):
        """Get webservice URL, raise an exception if not exists."""
        if self._webservices.get(ws_key) is None:
            raise PyiCloudServiceNotActivatedException(
                "Webservice not available", ws_key
            )
        return self._webservices[ws_key]["url"]

######################################################################
    @property
    def devices(self):
        """Returns all devices."""
        service_root = self._get_webservice_url("findme")
        return FindMyiPhoneServiceManager(
            service_root, self.session, self.params, self.with_family
        )

    @property
    def friends(self):
        """Gets the 'Friends' service."""
        service_root = self._get_webservice_url("fmf")
        return FindFriendsService(service_root, self.session, self.params)

    @property
    def contacts(self):
        """Gets the 'Contacts' service."""
        service_root = self._get_webservice_url("contacts")
        return ContactsService(service_root, self.session, self.params)

    def __unicode__(self):
        return f"iCloud API: {self.user.get('apple_id')}"

    def __str__(self):
        as_unicode = self.__unicode__()
        if PY2:
            return as_unicode.encode("utf-8", "ignore")
        return as_unicode

    def __repr__(self):
        return "<{str(self)}>"
####################################################################################
#
#   Find my iPhone service
#
####################################################################################
"""Find my iPhone service."""
#import json
#from six import PY2, text_type
#from pyicloud.exceptions import PyiCloudNoDevicesException

class FindMyiPhoneServiceManager(object):
    """The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.
    """

    def __init__(self, service_root, session, params, with_family=False):
        self.session = session
        self.params = params
        self.with_family = with_family

        fmip_endpoint = f"{service_root}/fmipservice/client/web"
        self._fmip_refresh_url = f"{fmip_endpoint}/refreshClient"
        self._fmip_sound_url = f"{fmip_endpoint}/playSound"
        self._fmip_message_url = f"{fmip_endpoint}/sendMessage"
        self._fmip_lost_url = f"{fmip_endpoint}/lostDevice"

        self._devices = {}
        self.refresh_client()

    def refresh_client(self):
        """Refreshes the FindMyiPhoneService endpoint,

        This ensures that the location data is up-to-date.

        """
        req = self.session.post(
            self._fmip_refresh_url,
            params=self.params,
            data=json.dumps(
                {
                    "clientContext": {
                        "fmly": self.with_family,
                        "shouldLocate": True,
                        "selectedDevice": "all",
                        "deviceListVersion": 1,
                    }
                }
            ),
        )
        self.response = req.json()

        for device_info in self.response["content"]:
            device_id = device_info["id"]
            if device_id not in self._devices:
                self._devices[device_id] = AppleDevice(
                    device_info,
                    self.session,
                    self.params,
                    manager=self,
                    sound_url=self._fmip_sound_url,
                    lost_url=self._fmip_lost_url,
                    message_url=self._fmip_message_url,
                )
            else:
                self._devices[device_id].update(device_info)

        if not self._devices:
            raise PyiCloudNoDevicesException()

    def __getitem__(self, key):
        if isinstance(key, int):
            if PY2:
                key = self.keys()[key]
            else:
                key = list(self.keys())[key]
        return self._devices[key]

    def __getattr__(self, attr):
        return getattr(self._devices, attr)

    def __unicode__(self):
        return text_type(self._devices)

    def __str__(self):
        as_unicode = self.__unicode__()
        if PY2:
            return as_unicode.encode("utf-8", "ignore")
        return as_unicode

    def __repr__(self):
        return text_type(self)


class AppleDevice(object):
    """Apple device."""

    def __init__(
        self,
        content,
        session,
        params,
        manager,
        sound_url=None,
        lost_url=None,
        message_url=None,
    ):
        self.content = content
        self.manager = manager
        self.session = session
        self.params = params

        self.sound_url = sound_url
        self.lost_url = lost_url
        self.message_url = message_url

    def update(self, data):
        """Updates the device data."""
        self.content = data

    def location(self):
        """Updates the device location."""
        self.manager.refresh_client()
        return self.content["location"]

    def status(self, additional=[]):  # pylint: disable=dangerous-default-value
        """Returns status information for device.

        This returns only a subset of possible properties.
        """
        self.manager.refresh_client()
        fields = ["batteryLevel", "deviceDisplayName", "deviceStatus", "name"]
        fields += additional
        properties = {}
        for field in fields:
            properties[field] = self.content.get(field)
        return properties

    def play_sound(self, subject="Find My iPhone Alert"):
        """Send a request to the device to play a sound.

        It's possible to pass a custom message by changing the `subject`.
        """
        data = json.dumps(
            {
                "device": self.content["id"],
                "subject": subject,
                "clientContext": {"fmly": True},
            }
        )
        self.session.post(self.sound_url, params=self.params, data=data)

    def display_message(
        self, subject="Find My iPhone Alert", message="This is a note", sounds=False
    ):
        """Send a request to the device to play a sound.

        It's possible to pass a custom message by changing the `subject`.
        """
        data = json.dumps(
            {
                "device": self.content["id"],
                "subject": subject,
                "sound": sounds,
                "userText": True,
                "text": message,
            }
        )
        self.session.post(self.message_url, params=self.params, data=data)

    def lost_device(
        self, number, text="This iPhone has been lost. Please call me.", newpasscode=""
    ):
        """Send a request to the device to trigger 'lost mode'.

        The device will show the message in `text`, and if a number has
        been passed, then the person holding the device can call
        the number without entering the passcode.
        """
        data = json.dumps(
            {
                "text": text,
                "userText": True,
                "ownerNbr": number,
                "lostModeEnabled": True,
                "trackingEnabled": True,
                "device": self.content["id"],
                "passcode": newpasscode,
            }
        )
        self.session.post(self.lost_url, params=self.params, data=data)

    @property
    def data(self):
        """Gets the device data."""
        return self.content

    def __getitem__(self, key):
        return self.content[key]

    def __getattr__(self, attr):
        return getattr(self.content, attr)

    def __unicode__(self):
        display_name = self["deviceDisplayName"]
        name = self["name"]
        return f"{display_name}: {name}"

    def __str__(self):
        as_unicode = self.__unicode__()
        if PY2:
            return as_unicode.encode("utf-8", "ignore")
        return as_unicode

    def __repr__(self):
        return f"<AppleDevice({str(self)})>"
####################################################################################
#
#   Find my Friends service
#
####################################################################################
"""Find my Friends service."""
#from __future__ import absolute_import
#import json

class FindFriendsService(object):
    """
    The 'Find My' (FKA 'Find My Friends') iCloud service

    This connects to iCloud and returns friend data including
    latitude and longitude.
    """

    def __init__(self, service_root, session, params):
        self.session = session
        self.params = params
        self._service_root = service_root
        #self._friend_endpoint = "%s/fmipservice/client/fmfWeb/initClient" % (self._service_root,)
        self._friend_endpoint = f"{self._service_root}/fmipservice/client/fmfWeb/initClient"
        self.refresh_always = False
        self.response = {}

    def refresh_client(self):
        """
        Refreshes all data from 'Find My' endpoint,
        """
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
        req = self.session.post(self._friend_endpoint, data=mock_payload, params=params)
        self.response = req.json()

    @staticmethod
    def should_refresh_client_fnc(response):
        """Function to override to set custom refresh behavior"""
        return not response

    def should_refresh_client(self):
        """
        Customizable logic to determine whether the data should be refreshed.

        By default, this returns False.

        Consumers can set `refresh_always` to True or assign their own function
        that takes a single-argument (the last reponse) and returns a boolean.
        """
        return self.refresh_always or FindFriendsService.should_refresh_client_fnc(
            self.response
        )

    @property
    def data(self):
        """
        Convenience property to return data from the 'Find My' endpoint.

        Call `refresh_client()` before property access for latest data.
        """
        if not self.response or self.should_refresh_client():
            self.refresh_client()
        return self.response

    def contact_id_for(self, identifier, default=None):
        """
        Returns the contact id of your friend with a given identifier
        """
        lookup_key = "phones"
        if "@" in identifier:
            lookup_key = "emails"

        def matcher(item):
            """Returns True iff the identifier matches"""
            hit = item.get(lookup_key)
            if not isinstance(hit, list):
                return hit == identifier
            return any([el for el in hit if el == identifier])

        candidates = [
            item.get("id", default) for item in self.contact_details if matcher(item)
        ]
        if not candidates:
            return default
        return candidates[0]

    def location_of(self, contact_id, default=None):
        """
        Returns the location of your friend with a given contact_id
        """
        candidates = [
            item.get("location", default)
            for item in self.locations
            if item.get("id") == contact_id
        ]
        if not candidates:
            return default
        return candidates[0]

    @property
    def locations(self):
        """Returns a list of your friends' locations"""
        return self.data.get("locations", [])

    @property
    def followers(self):
        """Returns a list of friends who follow you"""
        return self.data.get("followers")

    @property
    def following(self):
        """Returns a list of friends who you follow"""
        return self.data.get("following")

    @property
    def contact_details(self):
        """Returns a list of your friends contact details"""
        return self.data.get("contactDetails")


####################################################################################
#
#   Exceptions (exceptions.py)
#
####################################################################################
"""Library exceptions."""


class PyiCloudException(Exception):
    """Generic iCloud exception."""
    pass


# API
class PyiCloudAPIResponseException(PyiCloudException):
    """iCloud response exception."""
    def __init__(self, reason, code=None, retry=False):
        self.reason = reason
        self.code = code
        message = reason or ""
        if code:
            message += (f" (Error Code {code})")
        if retry:
            message += ". Retrying ..."

        super(PyiCloudAPIResponseException, self).__init__(message)


class PyiCloudServiceNotActivatedException(PyiCloudAPIResponseException):
    """iCloud service not activated exception."""
    pass


# Login
class PyiCloudFailedLoginException(PyiCloudException):
    """iCloud failed login exception."""
    pass


class PyiCloud2SARequiredException(PyiCloudException):
    """iCloud 2SA required exception."""
    def __init__(self, apple_id):
        message = f"Two-step authentication required for account: {apple_id}"
        super(PyiCloud2SARequiredException, self).__init__(message)


class PyiCloudNoStoredPasswordAvailableException(PyiCloudException):
    """iCloud no stored password exception."""
    pass


# Webservice specific
class PyiCloudNoDevicesException(PyiCloudException):
    """iCloud no device exception."""
    pass


####################################################################################
#
#   Utilities (utils.py)
#
####################################################################################
"""Utils."""
import getpass
import keyring
import sys
#from .exceptions import PyiCloudNoStoredPasswordAvailableException

KEYRING_SYSTEM = "pyicloud://icloud-password"


def get_password(username, interactive=sys.stdout.isatty()):
    """Get the password from a username."""
    try:
        return get_password_from_keyring(username)
    except PyiCloudNoStoredPasswordAvailableException:
        if not interactive:
            raise

        return getpass.getpass(
            "Enter iCloud password for {username}: ".format(username=username,)
        )


def password_exists_in_keyring(username):
    """Return true if the password of a username exists in the keyring."""
    try:
        get_password_from_keyring(username)
    except PyiCloudNoStoredPasswordAvailableException:
        return False

    return True


def get_password_from_keyring(username):
    """Get the password from a username."""
    result = keyring.get_password(KEYRING_SYSTEM, username)
    if result is None:
        raise PyiCloudNoStoredPasswordAvailableException(
            "No pyicloud password for {username} could be found "
            "in the system keychain.  Use the `--store-in-keyring` "
            "command-line option for storing a password for this "
            "username.".format(username=username,)
        )

    return result


def store_password_in_keyring(username, password):
    """Store the password of a username."""
    return keyring.set_password(KEYRING_SYSTEM, username, password,)


def delete_password_in_keyring(username):
    """Delete the password of a username."""
    return keyring.delete_password(KEYRING_SYSTEM, username,)


def underscore_to_camelcase(word, initial_capital=False):
    """Transform a word to camelCase."""
    words = [x.capitalize() or "_" for x in word.split("_")]
    if not initial_capital:
        words[0] = words[0].lower()

    return "".join(words)
