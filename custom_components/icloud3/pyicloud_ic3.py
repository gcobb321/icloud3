"""
Customized version of pyicloud.py to support iCloud3  Custom Component

Platform that supports importing data from the iCloud Location Services
and Find My Friends api routines. Modifications to pyicloud were made
by various people to include:
    - Original pyicloud - picklepete
                        - https://github.com/picklepete
    - Update to 2fa     - Peter Hadley
                        - https://github.com/PeterHedley94/pyicloud
    - Persistant Cookies - JiaJiunn Chiou
                        - https://github.com/chumachuma/iSync
    - Find My Friends Update - Z Zeleznick
                        - https://github.com/picklepete/pyicloud/pull/160

The piclkepete version used imports for the services, utilities and exceptions
modules. These modules have been incorporated into the pyicloud-ic3 version.
"""

VERSION = '1.0'

import six
import uuid
import hashlib
import inspect
import json
import logging
import requests
import sys
import tempfile
import os
from re import match
from uuid import uuid1 as generateClientID


#from pyicloud.exceptions import (
#    PyiCloudFailedLoginException,
#    PyiCloudAPIResponseError,
#    PyiCloud2SARequiredError,
#    PyiCloudServiceNotActivatedErrror
#)
#from . findmyiphone_tst import FindMyiPhoneServiceManager
#from pyicloud.services import (
#    FindMyiPhoneServiceManager,
#    CalendarService,
#    UbiquityService,
#    ContactsService,
#    RemindersService,
#    PhotosService,
#    AccountService
#)
#from pyicloud.utils import get_password_from_keyring

if six.PY3:
    import http.cookiejar as cookielib
else:
    import cookielib


logger = logging.getLogger(__name__)


#==================================================================
class PyiCloudPasswordFilter(logging.Filter):
    def __init__(self, password):
        self.password = password

    def filter(self, record):
        message = record.getMessage()
        if self.password in message:
            record.msg = message.replace(self.password, "*" * 8)
            record.args = []

        return True

#==================================================================
class PyiCloudSession(requests.Session):
    def __init__(self, service):
        self.req_no = 0

        self.service = service
        super(PyiCloudSession, self).__init__()

#------------------------------------------------------------------
    def request(self, *args, **kwargs):
        try:
            # Charge logging to the right service endpoint
            callee = inspect.stack()[2]
            module = inspect.getmodule(callee[0])
            logger = logging.getLogger(module.__name__).getChild('http')

            self.req_no+=1

            if self.service._password_filter not in logger.filters:
                logger.addFilter(self.service._password_filter)

        except Exception as err:
            logger.exception(err)
        try:
            response = super(PyiCloudSession, self).request(*args, **kwargs)

        except Exception as err:
            logger.exception(err)

        try:
            content_type = response.headers.get('Content-Type', '').split(';')[0]
            json_mimetypes = ['application/json', 'text/json']

            if not response.ok and content_type not in json_mimetypes:
                #return response
                self._raise_error(response.status_code, response.reason)

            if content_type not in json_mimetypes:
                self.req_no-=1
                return response
                
        except Exception as err:
            logger.exception(err)
            
        try:
            json = response.json()

        except:
            logger.warning('Failed to parse response with JSON mimetype')
            response = None
            return response

        reason = json.get('errorMessage')
        reason = reason or json.get('reason')
        reason = reason or json.get('errorReason')
        if not reason and isinstance(json.get('error'), six.string_types):
            reason = json.get('error')
        if not reason and json.get('error'):
            reason = "Unknown reason"

        code = json.get('errorCode')
        if not code and json.get('serverErrorCode'):
            code = json.get('serverErrorCode')

        if reason:
            acceptable_reason = 'Missing X-APPLE-WEBAUTH-TOKEN cookie'
            if reason != acceptable_reason:
                return ("Error={}, ({})").format(code, reason)
                #self._raise_error(code, reason)

        self.req_no-=1

        return response
#reason = reason or json.get('errorReason')
#acceptable_reason = 'Missing X-APPLE-WEBAUTH-TOKEN cookie'
#            if reason != acceptable_reason:
#------------------------------------------------------------------
    def _raise_error(self, code, reason):
        try:
            if self.service.requires_2sa and \
                    reason == 'Missing X-APPLE-WEBAUTH-TOKEN cookie':
                raise PyiCloud2SARequiredError(response.url)

            if code == 'ZONE_NOT_FOUND' or code == 'AUTHENTICATION_FAILED':
                reason = 'Please log into https://icloud.com/ to manually ' \
                    'finish setting up your iCloud service'
                api_error = PyiCloudServiceNotActivatedErrror(reason, code)
                logger.error(api_error)
                error_msg = "Error {}".format(code)
                return error_msg, reason
                #raise(api_error)

            if code == 'ACCESS_DENIED':
                reason = reason + '.  Please wait a few minutes then try ' \
                    'again.  The remote servers might be trying to ' \
                    'throttle requests.'

            api_error = PyiCloudAPIResponseError(reason, code)
            logger.error(api_error)

            self.session.cookies.clear()
            self.session.cookies.save()

            error_msg = "Error {}".format(code)
            
        except Exception as err:
            _LOGGER.exception(err)
            error_msg = "Other Error"
            
        return error_msg, reason
        #raise(api_error)


#==================================================================
class PyiCloudService(object):
    """
    A base authentication class for the iCloud service. Handles the
    authentication required to access iCloud services.

    Usage:
        from pyicloud import PyiCloudService
        pyicloud = PyiCloudService('username@apple.com', 'password')
        pyicloud.iphone.location()
    """

    def __init__(self, apple_id, password=None, cookie_directory=None, 
            verify=True, client_id=None):
        #if password is None:
        #    password = get_password_from_keyring(apple_id)
        try:
            self.data = {}
            self.client_id = client_id or str(uuid.uuid1()).upper()
            self.apple_id = apple_id
            self.user = {'apple_id': apple_id, 'password': password}
            self.appleWidgetKey = None
            self.webservices = None
            self.dsid = None
            self.account_country = None
            self.session_token = None

            self._password_filter = PyiCloudPasswordFilter(password)
            logger.addFilter(self._password_filter)

            #self.user_agent = 'Opera/9.52 (X11; Linux i686; U; en)'
            self.user_agent = ('Mozilla/5.0 (iPad; CPU OS 9_3_4 like Mac OS X)'
            'AppleWebKit/601.1.46 (KHTML, like Gecko) '
            'Version/9.0 Mobile/13G35 Safari/601.1')
            self._setup_endpoint = 'https://setup.icloud.com/setup/ws/1'
            self.referer = 'https://www.icloud.com'
            self.origin = 'https://www.icloud.com'
            self.response = None

            self._base_login_url = '%s/login' % self._setup_endpoint

            if cookie_directory:
                self._cookie_directory = os.path.expanduser(
                    os.path.normpath(cookie_directory))
            else:
                self._cookie_directory = os.path.join(
                    tempfile.gettempdir(),
                    'pyicloud')

            self.session = PyiCloudSession(self)
            self.session.verify = verify
            self.session.headers.update({
                'Origin': self.referer,
                'Referer': '%s/' % self.referer,
                'User-Agent': self.user_agent})
            
        except Exception as err:
            _LOGGER.exception(err)
            
        try:
            self.cookiejar_path = self._get_cookiejar_path()
            self.session.cookies = cookielib.LWPCookieJar(filename=self.cookiejar_path)
            if os.path.exists(self.cookiejar_path):
                self.session.cookies.load()

        except:
            # Most likely a pickled cookiejar from earlier versions.
            # The cookiejar will get replaced with a valid one after
            # successful authentication.
            logger.warning("Failed to read cookiejar %s", self.cookiejar_path)

        self.params = {
            'clientBuildNumber': '17DHotfix5',
            'clientMasteringNumber': '17DHotfix5',
            'ckjsBuildVersion': '17DProjectDev77',
            'ckjsVersion': '2.0.5',
            'clientId': self.client_id}

        self.clientID = self.generateClientID()
        self.setupiCloud = SetupiCloudService(self)
        self.idmsaApple = IdmsaAppleService(self)

        self.authenticate()

#------------------------------------------------------------------
    def authenticate(self):
        """
        Handles authentication, and persists the X-APPLE-WEB-KB cookie so that
        subsequent logins will not cause additional e-mails from Apple.
        """

        logger.info("Authenticating as %s", self.user['apple_id'])

        self.session_token = self.get_session_token()
        if self.session_token is None:
            logger.info(("Error logging into iCloud account {}"). \
                    format(self.apple_id))
            logger.info("Clearing cookies and retrying")
            self.session.cookies.clear()
            self.session.cookies.save()
            self.session.cookies.load()
            self.session_token = self.get_session_token()
            if self.session_token is None:
                logger.error(("Error logging into iCloud account {}"). \
                    format(self.apple_id))
                logger.error("iCloud API Authentication Failure, Aborted")
                #return
                msg = 'Invalid username/password'
                raise PyiCloudFailedLoginException(msg, 0)

        data = {
                'accountCountryCode': self.account_country,
                'extended_login': True,
                'dsWebAuthToken': self.session_token
               }
        try:
            ###### Post ==> /acountLogin
            req = self.session.post(
                self._setup_endpoint + '/accountLogin',
                data=json.dumps(data))
                
        except PyiCloudAPIResponseError as error:
            msg = 'Invalid user email/password credentials'
            raise PyiCloudFailedLoginException(msg, error)

        response = req.json()
        self.dsid = response['dsInfo']['dsid']
        self.webservices = response['webservices']

        self.params.update({'dsid': self.dsid})

        if not os.path.exists(self._cookie_directory):
            os.mkdir(self._cookie_directory)

        self.session.cookies.save()

        logger.info("Authentication completed successfully")

#------------------------------------------------------------------
    def get_session_token(self):
        self.clientID = self.generateClientID()
        status, self.appleWidgetKey = \
                self.setupiCloud.requestAppleWidgetKey(self.clientID)
        #return self.idmsaApple.requestAppleSessionToken(self.user['apple_id'],
        #                                                self.user['password'],
        #                                                widgetKey
        #                                                )

        if status:
            session_token, account_country = \
                    self.idmsaApple.requestAppleSessionToken(
                                self.user['apple_id'],
                                self.user['password'],
                                self.appleWidgetKey)
        else:
            #self.appleWidgetKey=response('error')
            return None

        return session_token

#------------------------------------------------------------------
    def generateClientID(self):

        client_id = str(generateClientID()).upper()

        return client_id


#------------------------------------------------------------------
    def _get_cookiejar_path(self):
        # Get path for cookiejar file
        #return os.path.join(
        #    self._cookie_directory,
        #    ''.join([c for c in self.user.get('apple_id') if match(r'\w', c)])
        #)
        cookiejar_path = os.path.join(
            self._cookie_directory,
            ''.join([c for c in self.user.get('apple_id') if match(r'\w', c)])
        )

        return cookiejar_path


#------------------------------------------------------------------
    @property
    def requires_2fa(self):
        return self.requires_2sa()

    @property
    def requires_2sa(self):
        """ Returns True if two-step authentication is required."""
        #return self.data.get('hsaChallengeRequired', False) \
        #    and self.data['dsInfo'].get('hsaVersion', 0) >= 1
        # FIXME: Implement 2FA for hsaVersion == 2
        rtn = self.data.get('hsaChallengeRequired', False) \
            and self.data['dsInfo'].get('hsaVersion', 0) >= 1

        return rtn

#------------------------------------------------------------------
    @property
    def trusted_devices(self):
        """ Returns devices trusted for two-step authentication."""
        request = self.session.get(
            '%s/listDevices' % self._setup_endpoint,
            params=self.params
        )
        rtn_value = request.json().get('devices')
        return rtn_value


#------------------------------------------------------------------
    def send_verification_code(self, device):
        """ Requests that a verification code is sent to the given device"""
        data = json.dumps(device)
        request = self.session.post(
            '%s/sendVerificationCode' % self._setup_endpoint,
            params=self.params,
            data=data
        )
        verif_code = request.json().get('success', False)
        return verif_code


#------------------------------------------------------------------
    def validate_verification_code(self, device, code):
        """ Verifies a verification code received on a trusted device"""
        device.update({
            'verificationCode': code,
            'trustBrowser': True
        })
        data = json.dumps(device)

        try:
            request = self.session.post(
                '%s/validateVerificationCode' % self._setup_endpoint,
                params=self.params,
                data=data
            )
        except PyiCloudAPIResponseError as error:
            if error.code == -21669:
                # Wrong verification code
                return False
            raise

        # Re-authenticate, which will both update the HSA data, and
        # ensure that we save the X-APPLE-WEBAUTH-HSA-TRUST cookie.
        self.authenticate()

        #return not self.requires_2sa
        needs_2sa = not self.requires_2sa
        return needs_2sa

#------------------------------------------------------------------
    @property
    def devices(self):
        """ Return all devices."""
        service_root = self.webservices['findme']['url']
        return FindMyiPhoneServiceManager(service_root, self.session,
                                          self.params)

#------------------------------------------------------------------
    @property
    def account(self):
        service_root = self.webservices['account']['url']
        return AccountService(service_root, self.session, self.params)

#------------------------------------------------------------------
    @property
    def friends(self):
        service_root = self.webservices['fmf']['url']
        return FindFriendsService(service_root, self.session, self.params)

#------------------------------------------------------------------
    '''
    @property
    def calendar(self):
        service_root = self.webservices['calendar']['url']
        return CalendarService(service_root, self.session, self.params)

    @property
    def iphone(self):
        return self.devices[0]

    @property
    def files(self):
        if not hasattr(self, '_files'):
            service_root = self.webservices['ubiquity']['url']
            self._files = UbiquityService(
                service_root,
                self.session,
                self.params
            )
        return self._files

    @property
    def photos(self):
        if not hasattr(self, '_photos'):
            service_root = self.webservices['ckdatabasews']['url']
            self._photos = PhotosService(
                service_root,
                self.session,
                self.params
            )
        return self._photos

    @property
    def contacts(self):
        service_root = self.webservices['contacts']['url']
        return ContactsService(service_root, self.session, self.params)

    @property
    def reminders(self):
        service_root = self.webservices['reminders']['url']
        return RemindersService(service_root, self.session, self.params)

    def __unicode__(self):
        return 'iCloud API: %s' % self.user.get('apple_id')

    def __str__(self):
        as_unicode = self.__unicode__()
        if sys.version_info[0] >= 3:
            return as_unicode
        else:
            return as_unicode.encode('ascii', 'ignore')

    def __repr__(self):
        return '<%s>' % str(self)

    '''
#==================================================================
class HTTPService:
    def __init__(self, session, response=None, origin=None, referer=None):
        try:
            self.session = session.session
            self.response = session.response
            self.origin = session.origin
            self.referer = session.referer
            self.user_agent = session.user_agent
        except:
            session = session
            self.response = response
            self.origin = origin
            self.referer = referer
            self.user_agent = "Python (X11; Linux x86_64)"


#==================================================================
class SetupiCloudService(HTTPService):
    def __init__(self, session):
        super(SetupiCloudService, self).__init__(session)
        self.url = "https://setup.icloud.com/setup/ws/1"
        self.urlKey = self.url + "/validate"
        self.urlLogin = self.url + "/accountLogin"

        self.appleWidgetKey = None
        self.cookies = None
        self.dsid = None

#------------------------------------------------------------------
    def requestAppleWidgetKey(self, clientID):
        error_msg = ""
        self.session.headers.update(self.getRequestHeader())
        apple_widget_params = self.getQueryParameters(clientID)

        self.response = self.session.get(self.urlKey,
                                         params=apple_widget_params)

        try:
            response_json = self.response.json()
            if ('error' in response_json):
                error_msg = str(response_json.get('error'))

            if (error_msg != '' and
                    error_msg != "Missing X-APPLE-WEBAUTH-TOKEN cookie"):
                return False, error_msg

            self.appleWidgetKey = self.findQyery(self.response.text,
                                                 "widgetKey=")
        except Exception as e:
            if error_msg == '':
                error_msg = "Unknown Error"
            return False, error_msg
            #raise Exception(err_str,
            #                self.urlKey, repr(e))
        return True, self.appleWidgetKey

#------------------------------------------------------------------
    def requestCookies(self, appleSessionToken, clientID):
        self.session.headers.update(self.getRequestHeader())
        login_payload = self.getLoginRequestPayload(appleSessionToken)
        login_params = self.getQueryParameters(clientID)

        self.response = self.session.post(self.urlLogin,
                                          login_payload,
                                          params=login_params)
        try:
            self.cookies = self.response.headers["Set-Cookie"]
        except Exception as e:
            raise Exception("requestCookies: Cookies query failed",
                            self.urlLogin, repr(e))
        try:
            self.dsid = self.response.json()["dsInfo"]["dsid"]
        except Exception as e:
            raise Exception("requestCookies: dsid query failed",
                            self.urlLogin, repr(e))

        return self.cookies, self.dsid

#------------------------------------------------------------------
    def findQyery(self, data, query):
        response = ''
        foundAt = data.find(query)
        if foundAt == -1:
            except_str = "findQyery: " + query + " could not be found in data"
            raise Exception(except_str)
        foundAt += len(query)
        char = data[foundAt]
        while char.isalnum():
            response += char
            foundAt += 1
            char = data[foundAt]
        return response

#------------------------------------------------------------------
    def getRequestHeader(self):
        header = {
            "Accept": "*/*",
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "Origin": self.origin,
            "Referer": self.referer,
            }

        return header

#------------------------------------------------------------------
    def getQueryParameters(self, clientID):
        if not clientID:
            raise NameError("getQueryParameters: clientID not found")
        data = {
            "clientBuildNumber": "16CHotfix21",
            "clientID": clientID,
            "clientMasteringNumber": "16CHotfix21",
            }
        return data


#------------------------------------------------------------------
    def getLoginRequestPayload(self, appleSessionToken):
        if not appleSessionToken:
            err_str = "getLoginRequestPayload: X-Apple-ID-Session-Id not found"
            raise NameError(err_str)
        data=json({
            "dsWebAuthToken": appleSessionToken,
            "extended_login": True,
            })
        return data


#==================================================================
class IdmsaAppleService(HTTPService):
    def __init__(self, session):
        super(IdmsaAppleService, self).__init__(session)
        self.url     = "https://idmsa.apple.com"
        self.urlAuth = self.url + "/appleauth/auth/signin?widgetKey="
        self.url2sv  = self.url + "/appleauth/auth/2sv/trust"
        self.account_country = 'USA'
        self.session_token   = None
        self.session_id      = None
        self.request_id      = None
        self.scnt            = None
        self.twoSV_trust_eligible = True
        self.twoSV_trust_token    = None

#------------------------------------------------------------------
    def requestAppleSessionToken(self, user, password, appleWidgetKey):
        self.session.headers.update(self.getRequestHeader(appleWidgetKey))

        url = self.urlAuth + appleWidgetKey
        user_pw_payload = self.getRequestPayload(user, password)
        
        self.response = self.session.post(self.urlAuth + appleWidgetKey,
                                          user_pw_payload)
        try:
            headers = self.response.headers

            self.session_token   = headers["X-Apple-Session-Token"]
            self.session_id      = headers["X-Apple-ID-Session-Id"]
            self.request_id      = headers["X-Apple-I-Request-ID"]
            self.scnt            = headers["scnt"]
            if "X-Apple-ID-Account-Country" in headers:
                self.account_country = headers["X-Apple-ID-Account-Country"]
            if "X-Apple-TwoSV-Trust-Eligible" in headers:
                self.twoSV_trust_eligible = headers["X-Apple-TwoSV-Trust-Eligible"]
            else:
                self.twoSV_trust_eligible = False

        except KeyError:
            return None, None

        except Exception as e:
            err_str = "requestAppleSessionToken: " + \
                      "Apple Session Token query failed"

            raise Exception(err_str,
                            self.urlAuth, repr(e))

        if self.twoSV_trust_eligible:
            self.requestApple2svToken(appleWidgetKey, user_pw_payload)

        return self.session_token, self.account_country

        #'X-Apple-I-Request-ID': '13edc839-129a-455c-994a-1ee280478d8e'
        #'X-Apple-TwoSV-Trust-Eligible': 'true'
        #'X-Apple-ID-Session-Id': '982A266AF7E9B9C6D1FB948D4542C687'
        #'scnt': 'f0003baa27ac5181307b73a5573e6bd2'
        #'X-Apple-ID-Account-Country': 'USA',

#------------------------------------------------------------------
    def requestApple2svToken(self, appleWidgetKey, user_pw_payload):
        self.session.headers.update(self.get2svRequestHeader(appleWidgetKey))

        self.response = self.session.post(self.url2sv, user_pw_payload)

        try:
            headers = self.response.headers
            
        except Exception as e:
            err_str = "requestAppleTwoSVToken: " + \
                      "Apple Session 2SV Token query failed"

            raise Exception(err_str,
                            self.urlAuth, repr(e))
        return

#------------------------------------------------------------------
    def getRequestHeader(self, appleWidgetKey):
        if not appleWidgetKey:
            raise NameError("getRequestHeader: clientID not found")
        header = {
            "Accept": "application/json, text/javascript",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "X-Apple-Widget-Key": appleWidgetKey,
            "X-Requested-With": "XMLHttpRequest",
            "Origin": self.origin,
            "Referer": self.referer,
            }
        return header

#------------------------------------------------------------------
    def get2svRequestHeader(self, appleWidgetKey):
        if not appleWidgetKey:
            logger.error("getRequestHeader: clientID not found")
            raise NameError("getRequestHeader: clientID not found")

        header = {
            "Origin": self.origin,
            "Referer": self.referer,
            "Content-Type": "application/json",
            "Accept": "application/json, text/javascript",
            "User-Agent": self.user_agent,
            "X-Requested-With": "XMLHttpRequest",
            "X-Apple-Widget-Key": appleWidgetKey,
            "X-Apple-ID-Session-Id": self.session_id,
            "scnt": self.scnt
            }
        return header
        #"User-Agent": self.user_ageny,
        #"Accept": "application/json, text/javascript",
        #"Content-Type": "application/json",

#------------------------------------------------------------------
    def getRequestPayload(self, user, password):
        if not user:
            raise NameError("getAuthenticationRequestPayload: user not found")
        if not password:
            err_str = "getAuthenticationRequestPayload: password not found"
            raise NameError(err_str)
        data = json.dumps({
            "accountName": user,
            "password": password,
            "rememberMe": True,
            })
        return data

#==================================================================
class FindFriendsService(object):
    """
    The 'Find my Friends' iCloud service
    This connects to iCloud and returns friend data including the near-realtime
    latitude and longitude.
    """
    def __init__(self, service_root, session, params):
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        logger = logging.getLogger(module.__name__).getChild('http')
        
        self.session = session
        self.params = params
        self._service_root = service_root
        self._friend_endpoint = '%s/fmipservice/client/fmfWeb/initClient' % (
            self._service_root,
        )
        self._data = {}


    def refresh_data(self):
        """
        Fetches all data from Find my Friends endpoint
        """
        params = dict(self.params)
        fake_data = json.dumps({
            'clientContext': {
                'appVersion': '1.0',
                'contextApp': 'com.icloud.web.fmf',
                'mapkitAvailable': True,
                'productType': 'fmfWeb',
                'tileServer': 'Apple',
                'userInactivityTimeInMS': 537,
                'windowInFocus': False,
                'windowVisible': True
            },
            'dataContext': None,
            'serverContext': None
        })
        req = self.session.post(self._friend_endpoint,
                                data=fake_data, params=params)
        self.response = req.json()
        return self.response

    @property
    def data(self):
        if not self._data:
            self._data = self.refresh_data()
        return self._data


    @property
    def locations(self):
        return self.data.get('locations')

    @property
    def followers(self):
        return self.data.get('followers')

    @property
    def friend_fences(self):
        return self.data.get('friendFencesISet')

    @property
    def my_fences(self):
        return self.data.get('myFencesISet')

    @property
    def contacts(self):
        return self.data.get('contactDetails')

    @property
    def details(self):
        return self.data.get('contactDetails')
#==================================================================
class FindMyiPhoneServiceManager(object):
    """ The 'Find my iPhone' iCloud service

    This connects to iCloud and return phone data including the near-realtime
    latitude and longitude.

    """

    def __init__(self, service_root, session, params):
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        logger = logging.getLogger(module.__name__).getChild('http')
        

        self.session = session
        self.params = params
        self._service_root = service_root
        self._fmip_endpoint = '%s/fmipservice/client/web' % self._service_root
        self._fmip_refresh_url = '%s/refreshClient' % self._fmip_endpoint
        self._fmip_sound_url = '%s/playSound' % self._fmip_endpoint
        self._fmip_message_url = '%s/sendMessage' % self._fmip_endpoint
        self._fmip_lost_url = '%s/lostDevice' % self._fmip_endpoint

        self._devices = {}
        self.refresh_client()


#------------------------------------------------------------------
    def refresh_client(self):
        """ Refreshes the FindMyiPhoneService endpoint,

        This ensures that the location data is up-to-date.

        """
        callee = inspect.stack()[2]
        module = inspect.getmodule(callee[0])
        logger = logging.getLogger(module.__name__).getChild('http')
        #logger = logging.getLogger(__name__)

        req = self.session.post(
            self._fmip_refresh_url,
            params=self.params,
            data=json.dumps(
                {
                    'clientContext': {
                        'fmly': True,
                        'shouldLocate': True,
                        'selectedDevice': 'all',
                    }
                }
            )
        )
        self.response = req.json()

        for device_info in self.response['content']:
            device_id = device_info['id']
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

#------------------------------------------------------------------
    def __getitem__(self, key):
        if isinstance(key, int):
            if six.PY3:
                key = list(self.keys())[key]
            else:
                key = self.keys()[key]
        return self._devices[key]

    def __getattr__(self, attr):
        return getattr(self._devices, attr)

    def __unicode__(self):
        return six.text_type(self._devices)

    def __str__(self):
        as_unicode = self.__unicode__()
        if sys.version_info[0] >= 3:
            return as_unicode
        else:
            return as_unicode.encode('ascii', 'ignore')

    def __repr__(self):
        return six.text_type(self)

#==================================================================
class AppleDevice(object):
    def __init__(
        self, content, session, params, manager,
        sound_url=None, lost_url=None, message_url=None
    ):
        self.content = content
        self.manager = manager
        self.session = session
        self.params = params

        self.sound_url = sound_url
        self.lost_url = lost_url
        self.message_url = message_url

#------------------------------------------------------------------
    def update(self, data):
        self.content = data

#------------------------------------------------------------------
    def location(self):
        self.manager.refresh_client()
        return self.content['location']

#------------------------------------------------------------------
    def status(self, additional=[]):
        """ Returns status information for device.

        This returns only a subset of possible properties.
        """
        self.manager.refresh_client()
        fields = ['batteryLevel', 'deviceDisplayName', 'deviceStatus', 'name']
        fields += additional
        properties = {}
        for field in fields:
            properties[field] = self.content.get(field)
        return properties

#------------------------------------------------------------------
    def play_sound(self, subject='Find My iPhone Alert'):
        """ Send a request to the device to play a sound.

        It's possible to pass a custom message by changing the `subject`.
        """
        data = json.dumps({
            'device': self.content['id'],
            'subject': subject,
            'clientContext': {
                'fmly': True
            }
        })
        self.session.post(
            self.sound_url,
            params=self.params,
            data=data
        )

#------------------------------------------------------------------
    def display_message(
        self, subject='Find My iPhone Alert', message="This is a note",
        sounds=False
    ):
        """ Send a request to the device to play a sound.

        It's possible to pass a custom message by changing the `subject`.
        """
        data = json.dumps(
            {
                'device': self.content['id'],
                'subject': subject,
                'sound': sounds,
                'userText': True,
                'text': message
            }
        )
        self.session.post(
            self.message_url,
            params=self.params,
            data=data
        )

#------------------------------------------------------------------
    def lost_device(
        self, number,
        text='This iPhone has been lost. Please call me.',
        newpasscode=""
    ):
        """ Send a request to the device to trigger 'lost mode'.

        The device will show the message in `text`, and if a number has
        been passed, then the person holding the device can call
        the number without entering the passcode.
        """
        data = json.dumps({
            'text': text,
            'userText': True,
            'ownerNbr': number,
            'lostModeEnabled': True,
            'trackingEnabled': True,
            'device': self.content['id'],
            'passcode': newpasscode
        })
        self.session.post(
            self.lost_url,
            params=self.params,
            data=data
        )

#------------------------------------------------------------------
    @property
    def data(self):
        return self.content

    def __getitem__(self, key):
        return self.content[key]

    def __getattr__(self, attr):
        return getattr(self.content, attr)

    def __unicode__(self):
        display_name = self['deviceDisplayName']
        name = self['name']
        return '%s: %s' % (
            display_name,
            name,
        )

    def __str__(self):
        as_unicode = self.__unicode__()
        if sys.version_info[0] >= 3:
            return as_unicode
        else:
            return as_unicode.encode('ascii', 'ignore')

    def __repr__(self):
        return '<AppleDevice(%s)>' % str(self)

#==================================================================
class PyiCloudException(Exception):
    pass


class PyiCloudNoDevicesException(PyiCloudException):
    pass


class PyiCloudAPIResponseError(PyiCloudException):
    def __init__(self, reason, code):
        self.reason = reason
        self.code = code
        message = reason
        if code:
            message += " (%s)" % code

        super(PyiCloudAPIResponseError, self).__init__(message)


class PyiCloudFailedLoginException(PyiCloudException):
    pass


class PyiCloud2SARequiredError(PyiCloudException):
    def __init__(self, url):
        message = "Two-step authentication required for %s" % url
        super(PyiCloud2SARequiredError, self).__init__(message)


#class PyiCloudNoDevicesException(Exception):
#    pass


class NoStoredPasswordAvailable(PyiCloudException):
    pass


class PyiCloudServiceNotActivatedErrror(PyiCloudAPIResponseError):
    pass


