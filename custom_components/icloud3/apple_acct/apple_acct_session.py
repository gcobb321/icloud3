"""
Session, token and cookie routines for :class:`AppleAcctManager`.

The methods here are mixed into ``AppleAcctManager``; they call each other and
the auth helpers through ``self`` and must not import ``apple_acct``.
"""

from ..global_variables     import GlobalVariables as Gb
from ..const                import (TRUST_COOKIE_NAME, TEXT_1,
                                    CONF_USERNAME, CONF_PASSWORD,)
from ..utils.utils          import dict_del, decode_password
from ..utils.time_util      import secs_since
from ..utils                import file_io
from ..utils.messaging      import (log_info_msg, log_debug_msg, log_warning_msg,
                                    log_exception)
from .                      import icloud_requests_io  as icloud_io
from .icloud_cookie_jar     import PyiCloudCookieJar
from .exceptions            import AppleAcctAPIResponseException

from typing                 import cast
from os                     import path
from re                     import match

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

# How long the 2FA-pending (409) idmsa signin session is assumed to still
# accept a verify/phone request. Reusing that session is what keeps a Text
# code resend from making Apple push a new popup to every trusted device.
# Apple does not publish the real lifetime so this is deliberately short -
# an over-estimate only costs one rejected verify/phone, which falls back
# to the full password sign-in.
SRP_2FA_CHALLENGE_MAX_AGE_SECS = 600


class AppleAcctSessionMixin:
#----------------------------------------------------------------------------
    @property
    def trust_token_expire_date_time(self):
        cookie_info = self.iCloudSession.cookies.get_trust_cookie_info()
        return f"{cookie_info['expire_date_time']}, ({cookie_info['expire_in_text']})"

#----------------------------------------------------------------------------
    def set_trust_token_expire_in_days(self):
        '''
        At 1:15am during the end-of-day processing,  update the trust_token_expire_in_days
        value from the X-APPLE-WEBAUTH-HSA-TRUST cookie. When this reached 45-days,
        reauthenticatta the Apple acct which creates a new cookie that expires in 90-days.
        This should eliminate the need of the user getting the popup window that
        with a new code.

        This is run in authentication() and icloud_main.timer_tasks_midnight()
        '''
        if (self.login_auth_method != "TrustToken"
                or Gb.is_icloud3_startup_inprocess):
            self.list_cookies()
        else:
            self.list_cookies(TRUST_COOKIE_NAME)

        if self.is_reauth_needed:
            self.trust_token_expire_in_days = -1
            return

        self.trust_token_expire_in_days = self.iCloudSession.cookies.expire_in_days()

        return self.trust_token_expire_in_days

#--------------------------------------------------------------------
    def _validate_token(self):
        '''Checks if the current access token is still valid.'''

        log_info_msg(f"{self.username_base}, Validate Token")

        url = f"{self.SETUP_ENDPOINT}/validate"
        data = "null"

        try:
            self.data = icloud_io.post(self, url, data=data)

            self.is_reauth_needed = self._set_is_reauth_needed

            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token valid, "
                            f"2fa Needed-{self.is_reauth_needed}")

            return not self.is_reauth_needed

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Session Token is not valid, "
                            f"2fa Needed-{self.is_reauth_needed}, "
                            f"Error-{err}")

        except Exception as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Error encountered validating token > "
                            f"Error, {err}")
            log_exception(err)

        return False

#----------------------------------------------------------------------------
    def is_session_trusted_auth_check(self):
        '''
        Re-trigger the 2FA push notification popup on all trusted devices
        WITHOUT deleting session/cookie files or re-doing password authentication.

        This works by GETting /appleauth/auth with the existing session headers.
        Apple re-dispatches the push to all trusted devices if the session is
        still in a pending-2FA-challenge state.

        Returns:
            True  - Session has expired; full re-auth needed
            False - Push re-sent, session still valid, phone numbers re-captured
        '''
        headers = self.get_auth_headers()
        url     = f"{self.AUTH_ENDPOINT}/auth"

        try:
            log_info_msg(f"{self.username_base}, Check Session Trust")

            data = icloud_io.get(self, url, headers=headers)

            # Get trusted phone numbers and hwkeys
            if self.response_code in (200, 409):
                self.get_trusted_devices()
                log_debug_msg(f"{self.username_base}, Session Trust Valid ({self.response_code}))")
                return True

            log_debug_msg(  f"{self.username_base}, Session Trust Invalid ({self.response_code})")
            return False

        except AppleAcctAPIResponseException as err:
            # 403/404 means session is fully expired — need fresh login
            if self.response_code in (403, 404):
                log_warning_msg(f"{self.username_base}, Session Trust Expired ({self.response_code})")
            else:
                log_warning_msg(f"{self.username_base}, Session Trust Error ({self.response_code})")

        except Exception as err:
            log_exception(err)

        return True

#----------------------------------------------------------------------------
    def is_session_still_trusted(self):
        '''
        Determine if the current session is still valid for SMS 2FA
        without triggering a push notification or making an auth attempt.

        Returns:
            True  - Session appears valid, safe to send SMS
            False - Session is expired, full re-auth needed
        '''
        # Check 1: scnt must be present — it's the idmsa session key
        # Without it, ALL /appleauth/auth/* endpoints will fail
        if not self.session_data.get('scnt'):
            log_debug_msg(f"{self.username_base}, is_sms_session_valid > "
                        f"EXPIRED: scnt missing from session_data")
            return False

        # Check 2: session_id must be present
        if not self.session_data.get('session_id'):
            log_debug_msg(f"{self.username_base}, is_sms_session_valid > "
                        f"EXPIRED: session_id missing from session_data")
            return False

        return True

#----------------------------------------------------------------------------
    @property
    def is_2fa_challenge_session_live(self):
        '''
        Determine if the idmsa signin session opened by the last SRP password
        sign-in is still sitting at the 2FA challenge (409) and can be reused
        to request another Text authentication code.

        Apple fans out the trusted-device push popup when the CHALLENGE is
        created (the signin/complete that answers 409), not when a code is
        requested. Asking for a text code against an existing challenge sends
        the SMS without lighting up every device on the account again, so this
        is checked before falling back to untrust_session_and_authenticate.

        Returns:
            True  - Reuse the challenge, request the text code directly
            False - No usable challenge, a new password sign-in is needed
        '''
        if self.login_successful_srp is not True:
            return False

        if self.is_session_still_trusted() is False:
            return False

        return secs_since(self.srp_valid_upw_secs) < SRP_2FA_CHALLENGE_MAX_AGE_SECS

#----------------------------------------------------------------------------
    def get_auth_headers(self, overrides=None):

        headers = HEADERS.copy()
        headers["X-Apple-OAuth-State"] = self.client_id

        if self.session_data.get("scnt"):
            self.scnt = self.session_data.get("scnt") or self.token_pw_data.get("scnt")
            headers["scnt"] = self.scnt
        if self.session_data.get("session_id"):
            self.session_id = self.session_data.get("session_id") or self.token_pw_data.get("session_id")
            headers["X-Apple-ID-Session-Id"] = self.session_id

        if overrides:
            headers.update(overrides)
        return headers

#----------------------------------------------------------------------------
    def get_trusted_devices(self):
        '''
        Read the HSA2 trusted phone numbers and the registered hardware-key
        names. Both are returned in the body of a SINGLE /appleauth/auth GET,
        and only while the idmsa session is in the 2FA-pending state created by
        a fresh SRP password sign-in (the TrustToken path returns 401).

        Apple returns the full body (phoneNumberVerification + keyNames) only on
        the FIRST read of this endpoint - a second GET comes back empty. So the
        body is fetched once here and shared with both extractors; letting each
        function do its own GET returns nothing to whichever runs second.

        (The legacy setup/ws/1/listDevices endpoint is no longer used - it
        returns {'devices': []} for 2FA/HSA2 accounts.)
        '''
        auth_data = None
        if self.login_successful_srp:
            try:
                auth_data = icloud_io.get(self, self.AUTH_ENDPOINT,
                                            headers=self.get_auth_headers())
                if self.response_code != 200:
                    auth_data = None

            except Exception as err:
                log_exception(err)
                auth_data = None

        if auth_data:
            self.get_text_message_phone_numbers(auth_data)
            self.get_hwkey_names(auth_data)

#----------------------------------------------------------------------------
    def _read_session_data(self):
        '''
        Read the session file into session_data.

        Credential validation is stateless - it needs a signin session Apple has
        never seen before, so a validate-only AppleAcct carries nothing in from
        the file except the trust token. Keeping the trust token lets an account
        that is already trusted answer the signin/complete with a 200 instead of
        being pushed into the 2FA-pending state (409) on every validation; the
        signin session identifiers (session_id, scnt) and the session token are
        exactly what must NOT be reused - see AppleAcctManager.get_auth_headers
        and clear_srp_signin_session.
        '''
        session_data = file_io.read_json_file(self.session_filename)

        if self.validate_aa_upw is False:
            return session_data

        trust_token = session_data.get('trust_token')

        return {'trust_token': trust_token} if trust_token else {}

#----------------------------------------------------------------------------
    def _setup_iCloudSession(self):
        '''
        Set up the password_filter, cookies and session files
        '''

        # If password was changed, delete the session file to generate a new 6-digit
        # Authentication code from Apple when the new session is created.
        #
        # A validate-only AppleAcct shares all three files with the real AppleAcct
        # for this username. It still READS the .tpw file (the password saved there
        # drives the no-request Method-0 check in ValidateAppleAcctUPW), but it must
        # never create, modify or delete any of them - deleting the real session
        # here would discard a working session before the new password has even
        # been verified.
        self.read_token_pw_file()

        self._update_token_pw(CONF_USERNAME, self.username)
        if (self.validate_aa_upw is False
                and self.password != self.token_password):
            file_io.delete_file(self.session_filename)

        try:
            self.session_data = {}
            self.session_data = self._read_session_data()

            # If this username is being opened again with another password, a new AppleAcct
            # object is being created to verify the username/password are correct. Get some
            # token and url values from the original AppleAcct instance in case an asap specific
            # password is being used for this instance.
            #
            # Skipped for a validate-only AppleAcct - copying the live AppleAcct's
            # session_data would put the signin session identifiers straight back
            # into the session that _read_session_data just kept them out of.
            if (self.validate_aa_upw is False
                    and self.is_AADevices_setup_complete is False
                    and self.username in Gb.AppleAcct_by_username):
                _AppleAcct = Gb.AppleAcct_by_username[self.username]
                if _AppleAcct.findme_url_root:
                    self.findme_url_root = _AppleAcct.findme_url_root
                    self._update_token_pw('findme_url', self.findme_url_root)

                self.session_data  = _AppleAcct.session_data.copy()

            self._update_token_pw_session_data()

        except Exception as err:
            log_exception(err)
            log_info_msg(   f"{self.username_base}, "
                            f"Session file does not exist ({self.session_filename})")

        self._use_srp_signin_token_info()

        if 'client_id' in self.token_pw_data:
            self.client_id = self.token_pw_data['client_id']
        if 'client_id' in self.session_data:
            self.client_id = self.session_data['client_id']
        else:
            self.session_data['client_id'] = self.client_id
        self._update_token_pw('client_id', self.client_id)

        self.iCloudSession = icloud_io.new_session(self)

        if self.validate_aa_upw:
            # Bind the cookie jar to no file at all - PyiCloudCookieJar.load() and
            # .save() are both no-ops without a filename. The signin cookies
            # (notably 'aasp', which IS the idmsa signin session id) are then
            # neither inherited from nor written back to the real AppleAcct's
            # cookie file, so a validation cannot collide with a login.
            self.iCloudSession.cookies = PyiCloudCookieJar(filename=None)
            log_debug_msg(  f"{self.username_base}, Validate Username/Password, "
                            f"Using a transient cookie jar (nothing persisted)")
            return

        success = self.load_cookies(self.cookies_filename)
        if success:
            log_debug_msg(  f"{self.username_base}, "
                            f"Loaded Cookies File ({self.cookies_filename_short})")

        else:
            log_warning_msg(f"{self.username_base}, "
                            f"Load Cookies File Failed ({self.cookies_filename_short})")

#--------------------------------------------------------------------
    def load_cookies(self, cookies_filename):
        self.iCloudSession.cookies = PyiCloudCookieJar(filename=cookies_filename)

        # Added .cookies to filename, rename old file (v3.3.3.1)
        old_cookies_filename = cookies_filename.replace('.cookies', '')
        file_io.rename_file(old_cookies_filename, cookies_filename)

        if path.exists(cookies_filename):
            try:
                cast(PyiCloudCookieJar, self.iCloudSession.cookies).load()

            except (OSError, ValueError) as err:
                log_warning_msg(f"{self.username_base}, "
                                f"Failed to load cookies {cookies_filename}, "
                                f"Starting without persisted cookies",
                                f"{err}")
                cast(PyiCloudCookieJar, self.iCloudSession.cookies).clear()
                return False

        return True

#----------------------------------------------------------------------------
    def list_cookies(self, selected_cookie=None):
        if Gb.is_log_level_debug is False:
            return

        try:
            self.iCloudSession.cookies.list(selected_cookie)
        except Exception as err:
            log_debug_msg(f"list_cookies > Unable to list the cookies-{type(err).__name__}")

#----------------------------------------------------------------------------
    def delete_cookie_and_session_files(self):

        file_io.delete_file(self.cookies_filename)
        file_io.delete_file(self.session_filename)

        self.iCloudSession.cookies.clear()
        self.iCloudSession.cookies.save()

        dict_del(self.token_pw_data, 'session_id')
        dict_del(self.token_pw_data, 'session_token')

#----------------------------------------------------------------------------
    def delete_trust_cookie(self):
        '''
        Delete the X-APPLE-WEBAUTH-HSA-TRUST cookie to cause Apple to display the
        Push Notification Authentication Code window.

        But, If Text-1 Device phone number has not been set up, it means the
        X-APPLE-WEBAUTH-HSA-LOGIN cookie was never created by the PasswordSrp
        authentication routine. To force this to happen, all cookies and session
        files must be deleted so they will be recreated.
        '''
        if self.auth_methods.get(TEXT_1, '') == '':
            self.delete_cookie_and_session_files()
        else:
            self.iCloudSession.cookies.delete('X-APPLE-WEBAUTH-HSA-TRUST')
            self.iCloudSession.cookies.save()

#----------------------------------------------------------------------------
    '''
    The token password file stores the encoded password associated with the session
    token. It is used to see if the user is changing the username's password. It so,
    the session and it's token must be deleted to create a session token and cause a
    2fa Authentication. It this is not done, the user will be logged into the session
    without checking the password and a password change will not be handled until the
    token wxpires.
    '''
    def read_token_pw_file(self):
        try:
            self.token_password = ''
            self.token_pw_data = file_io.read_json_file(self.tokenpw_filename)

            if self.username not in self.token_pw_data:
                self.token_pw_data[CONF_USERNAME] = self.username

            self.token_password = decode_password(self.token_pw_data[CONF_PASSWORD])

        except Exception as err:
            log_debug_msg(f"read_token_pw_file > Unable to load the token/pw data-{type(err).__name__}")
            self.token_password = self.password

        return self.token_pw_data

#----------------------------------------------------------------------------
    def _update_token_pw_session_data(self):

        # _write_token_pw_file is called directly here, so the validate_aa_upw
        # test done by _update_token_pw has to be repeated - a validate-only
        # AppleAcct shares the .tpw file with the real one for this username
        if self.validate_aa_upw:
            return

        self.token_pw_data.update(self.session_data)
        self._write_token_pw_file()

#----------------------------------------------------------------------------
    def _update_token_pw(self, item_key, source_data):
        if item_key in ['trusted_phone_data', 'hwkey']:
            pass
        elif self.validate_aa_upw:
            return

        try:
            new_value = source_data.get(item_key) if type(source_data) is dict else \
                        source_data

            # if True is True or isnot_empty(new_value):
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
            file_io.save_json_file(self.tokenpw_filename, self.token_pw_data)

        except Exception as err:
            # log_exception(err)
            log_warning_msg(f"Apple Acct > {self.account_owner}, "
                            f"Failed to update tokenpw file {self.tokenpw_filename}")

#----------------------------------------------------------------------------
    def cookie_username_base(self, username=None):
        if username is None:
            username = self.username
        return "".join([c for c in username if match(r"\w", c)])

    @property
    def cookies_filename(self):
        '''Get path for cookie file'''
        return path.join(self.cookie_directory, f"{self.cookie_username}.cookies")

    @property
    def cookies_filename_short(self):
        '''Get path for cookie file'''
        return f"{self.cookie_username}.cookies"

    @property
    def session_filename(self):
        '''Get path for session data file'''
        return path.join(self.cookie_directory, f"{self.cookie_username}.session")

    @property
    def session_filename_short(self):
        '''Get path for session data file'''
        return  f"{self.cookie_username}.session"
