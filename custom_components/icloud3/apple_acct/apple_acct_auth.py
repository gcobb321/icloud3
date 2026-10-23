"""
Apple Account authentication routines for :class:`AppleAcctManager`.

The methods here are mixed into ``AppleAcctManager``; they call each other and
the session helpers through ``self`` and must not import ``apple_acct``.
"""

from ..global_variables     import GlobalVariables as Gb
from ..const                import EVLOG_NOTICE, CRLF_DOT, CONF_PASSWORD
from ..utils.utils          import instr, is_empty, encode_password
from ..utils.time_util      import (time_now_secs, apple_server_time, format_age,
                                    secs_since, next_min_mark_secs)
from ..utils.messaging      import (post_event, post_alert, post_monitor_msg, post_error_msg,
                                    post_greenbar_msg, log_info_msg, log_debug_msg,
                                    log_error_msg, log_exception)
from .srp_password          import SrpPassword
from .                      import icloud_requests_io  as icloud_io
from .exceptions            import (AppleAcctAPIResponseException,
                                    AppleAcctFailedLoginException,)
import srp
import base64

# Max age of a signin token_info. config_flow logs in within a second of
# validating, so anything older is from an unrelated validation and the
# token it carries may already be dead.
SRP_SIGNIN_TOKEN_INFO_MAX_AGE_SECS = 60


class AppleAcctAuthMixin:
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
#           HANDLE ACCOUNT AUTHENTICATION
#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    def authenticate(self, refresh_session=False):
        '''
        Handles authentication, and persists cookies so that
        subsequent logins will not cause additional e-mails from Apple.
        '''
        login_successful          = False
        self.login_auth_method    = ""
        self.login_successful_srp = None
        self.auth_failed_503      = False
        self.response_code_pw     = 0

        # Do not reset is_reauth_needed flag on a reauthenticate session
        # It may have been set on first authentication
        if refresh_session is False:
            self.is_reauth_needed = False


        # self.is_reauth_needed = self._set_is_reauth_needed

        # Validate token - Consider authenticated if token is valid (POST=validate)
        if (refresh_session is False
                and self.session_data.get('session_token')
                and 'dsid' in self.params):
            self.login_auth_method = "ValidToken"
            login_successful = self._validate_token()

            log_debug_msg(f"{self.username_base}, {self.login_auth_method}, {login_successful=}")

        # Authenticate - Sign into Apple Account (POST=/signin)
        if login_successful is False:
            self.login_auth_method = "TrustToken"
            login_successful = self._authenticate_with_token()

            log_debug_msg(f"{self.username_base}, {self.login_auth_method}, {login_successful=}")

        if login_successful is False:
            self.login_auth_method = 'Password'
            login_successful = self.authenticate_with_password_srp()

            if login_successful is False:
                self._set_srp_return_error_code()

        #TESTCODE
        # login_successful = False

        # if login_successful is False:
        #     self.login_auth_method = 'Password'
        #     login_successful = self.authenticate_with_password()

        #     log_debug_msg(f"{self.username_base}, {self.login_auth_method}, {login_successful=}")

        #     self.response_code_pw = self.response_code

            # The Auth with Token is necessary to fill in the findme_url
            # if login_successful:
            #     login_successful = self._authenticate_with_token()

            #     log_debug_msg(f"{self.username_base}, {self.login_auth_method}/TrustToken, {login_successful=}")

        # Only re-evaluate the flag when the authentication actually completed.
        # _set_is_reauth_needed is derived from self.data, and after a failed
        # request self.data holds the error response (no 'dsInfo'), so it reads
        # back as False and the reauth screens lose the fact that a code is
        # still needed.

        if login_successful:
            self.is_reauth_needed = self._set_is_reauth_needed

        self._update_token_pw(CONF_PASSWORD, encode_password(self.token_password))

        # self.list_cookies()

        time_between_token_auth    = format_age(self.last_token_auth_secs)
        time_between_password_auth = format_age(self.last_password_auth_secs)
        if instr(self.login_auth_method, 'Token'):
            self.token_auth_cnt += 1
            self.last_token_auth_secs = time_now_secs()
        elif instr(self.login_auth_method, 'Password'):
            self.password_auth_cnt += 1
            self.last_password_auth_secs = time_now_secs()

            post_event( f"{EVLOG_NOTICE}Apple Acct {self.login_auth_method} Auth > {self.account_owner}, "
                        f"#{self.password_auth_cnt} ({time_between_password_auth}), "
                        f"{CRLF_DOT}Apple Time-{apple_server_time()}")

        post_monitor_msg(   f"Apple Acct {self.login_auth_method} Auth > {self.account_owner}, "
                            f"TokenAuth-#{self.token_auth_cnt} ({time_between_token_auth}), "
                            f"PasswordAuth-#{self.password_auth_cnt} ({time_between_password_auth})")

        self.is_authenticated = self.is_authenticated or login_successful
        if self.is_authenticated:
            self.setup_error(None)

        self.set_trust_token_expire_in_days()

        return self.is_authenticated

#----------------------------------------------------------------------------
    def _authenticate_with_token(self):
        '''Authenticate using session token. Return True if successful.'''
        try:
            log_info_msg(f"{self.username_base}, Authenticate with TrustToken")
            post_greenbar_msg(f"Apple Acct > {self.username_base}, Auth with TrustToken")

            if self.session_data.get("session_token"):
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

            self.response_code_pw = self.response_code
            self.auth_failed_503  = self.auth_failed_503 or self.response_code==503

            if self.data is None:
                log_debug_msg( f"{self.username_base}, "
                                "Authenticate with Token > Failed, "
                                "No data received from Apple (icloud.com)")
                return False

            self._handle_accept_terms_of_use(login_data)

            if 'items' in self.data:
                if 'hsaTrustedBrowser' in self.data['items']:
                    self._update_token_pw('items', self.data['items'])
                else:
                    log_debug_msg(  f"{self.username_base}, "
                            "Authenticate with Token > Failed, "
                            "Invalid 2fa hsaTrustedBrowser/hsaChallengeRequired Items")
                    return False

            if 'dsInfo' in self.data:
                if 'dsid' in self.data['dsInfo']:
                    self.params['dsid'] = self.dsid = str(self.data['dsInfo']['dsid'])
                    self._update_token_pw('dsid', self.dsid)

                if 'fullName' in self.data['dsInfo']:
                    self.account_name   = self.data['dsInfo']['fullName'].replace(' ', '')
                    self.account_locked = self.data['dsInfo']['locked']

            if 'webservices' in self.data:
                try:
                    if self.is_AADevices_setup_complete is False:
                        self.findme_url_root = self.data['webservices']['findme']['url']
                        self._update_token_pw('findme_url', self.findme_url_root)
                except:
                    pass

            elif (self.data.get('success', False) is False
                    or self.data.get('error', 1) == 1):
                return False

            self._update_token_pw_session_data()
            self.setup_error(None)

            # log_debug_msg( f"{self.username_base}, Authenticate with Token > Successful")
            return True

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with Token > Token is not valid, "
                            f"Error-{err}, 2fa Needed-{self.is_reauth_needed}")
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

        headers = self.get_auth_headers()

        url = f"{self.AUTH_ENDPOINT}/signin"
        params = {"isRememberMeEnabled": "true"}
        login_data = {  "accountName": self.username,
                        "password": self.password,
                        "rememberMe": True,
                        "trustTokens": []}

        if self.session_data.get("trust_token"):
            login_data["trustTokens"] = [self.session_data.get("trust_token")]

        try:
            self.raise_api_errors = True
            self.data = icloud_io.post(self, url, params=params, data=login_data,
                                                    headers=headers,)

            self.response_code_pw = self.response_code
            self.auth_failed_503  = self.auth_failed_503 or self.response_code==503

            self._handle_accept_terms_of_use(login_data)
            if self.terms_of_use_update_needed:
                return False

            return ('session_token' in self.session_data)

        except AppleAcctAPIResponseException as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with password > Failed, Password is not valid, "
                            f"Error-{err}")     #, 2fa Needed-{self.is_reauth_needed}")
            raise AppleAcctFailedLoginException()

        except Exception as err:
            log_debug_msg(  f"{self.username_base}, "
                            f"Authenticate with password > Failed, "
                            f"Other Error, {err}")
            log_exception(err)
            return False

        finally:
            self.raise_api_errors = False

#----------------------------------------------------------------------------
    def authenticate_with_password_srp(self, username=None, password=None):
        '''
        Sign into Apple account with password via Secure Remote Password Authentication

        Return:
            True - Successful login
            False - Invalid Password or other error
        '''
        self.login_successful_srp = False
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

            self.response_code_pw = self.response_code
            self.auth_failed_503  = self.auth_failed_503 or (self.response_code==503)

        except Exception as err:
            log_exception(err)
            self._set_srp_return_error_code()
            return False

        # error_msg = ''
        # if Gb.internet_error:
        #     error_msg = HTTP_RESPONSE_CODES(-4)
        # elif self.response_code in [403, 503]:
        #     error_msg = HTTP_RESPONSE_CODES[self.response_code]
        # elif 'salt' not in data:
        #     error_msg = HTTP_RESPONSE_CODES(-3)
        error_msg = ''
        if Gb.internet_error:
            error_msg = self.code_description(-4)
        elif self.response_code in [403, 503]:
            error_msg = self.code_description(self.response_code)
        elif 'salt' not in data:
            error_msg = self.code_description(-3)

        if error_msg:
            post_error_msg(f"Password SRP Error, {error_msg} ({self.response_code})")
            return False

#..........................................................................
        # Step 2: server sends salt, public key B and c to client
        salt       = base64.b64decode(data['salt'])
        b          = base64.b64decode(data['b'])
        c          = data['c']
        iterations = data['iteration']
        key_length = 32
        protocol   = data["protocol"]

        log_info_msg(  f"{self.username_base}, Authenticating with PasswordSRP, "
                        "signin/complete, Server will verify Credentials")

#..........................................................................
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

        self.response_code_pw = self.response_code
        self.auth_failed_503  = self.auth_failed_503 or (self.response_code==503)

        # if valid_upw is False:
        if self.response_code not in [200, 409]:
            self.setup_error(self.response_code)
            return False

        # The Auth with Token is necessary to fill in the findme_url
        self.login_successful_srp = True
        self.srp_valid_upw_secs = time_now_secs()
        self._authenticate_with_token()
        self.get_trusted_devices()
        log_debug_msg(  f"{self.username_base}, {self.login_auth_method}/TrustToken, "
                        f"login_successful=True")
        return True

#............................................................................
    def _srp_icloud_io_signin_init(self, username, data):
        '''
        Process the endpoint/signin/init request
        '''

        data.update({'protocols': ['s2k', 's2k_fo']})

        self.response_code_pw = self.response_code
        self.auth_failed_503  = self.auth_failed_503 or self.response_code==503

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
        headers = self.get_auth_headers()
        headers["Accept"] = "application/json, text/javascript"
        data.update({"accountName": username})

        try:
            data = icloud_io.post(self, url, json=data, headers=headers)

            self.response_code_pw = self.response_code
            self.auth_failed_503  = self.auth_failed_503 or self.response_code==503
            return data

        except AppleAcctAPIResponseException as err:
            pass
        except Exception as err:
            log_exception(err)

#............................................................................
    def validate_upw_via_srp(self, username=None, password=None):
        '''
        Lightweight Username/Password validation using the SRP signin/init and
        signin/complete exchange. This verifies the credentials with the Apple
        server without completing a full login (no trust-token auth and no
        device data refresh).

        Apple deprecated the old Basic-auth 'setup/authenticate/{username}' url
        (it now always returns 401 regardless of the credentials), so SRP is the
        supported way to check that a username/password is valid.

        Return:
            True  - Response 200 (signed in) or 409 (valid, 2FA/HSA2 required)
            False - Invalid Username/Password or other error
        '''
        username = username if username is not None else self.username
        password = password if password is not None else self.password

        log_info_msg(f"{self.username_base}, Validate Username/Password via SRP")

        # Step 1: client generates private key a and public key A, sends A to
        # the server via signin/init.
        srp.rfc5054_enable()
        srp.no_username_in_x()

        try:
            SrpPW   = SrpPassword(password)
            SrpUser = srp.User(username, SrpPW, hash_alg=srp.SHA256, ng_type=srp.NG_2048)
            _, A    = SrpUser.start_authentication()

            data = self._srp_icloud_io_signin_init(username, {'a': base64.b64encode(A).decode()})

        except Exception as err:
            log_exception(err)
            self._set_srp_return_error_code()
            return False

        if (self.response_code in [401, 401.1]
                or Gb.internet_error
                or is_empty(data)
                or 'salt' not in data):
            return False

        # Step 2/3: server returns salt/b/c; client computes the M1/M2 proof and
        # sends it via signin/complete. The server validates the proof - the
        # password itself is never transmitted.
        try:
            salt = base64.b64decode(data['salt'])
            b    = base64.b64decode(data['b'])
            SrpPW.set_encrypt_info(salt, data['iteration'], 32, data['protocol'])

            if (SrpPW.salt is None
                    or SrpPW.error_reason is not None):
                self._set_srp_return_error_code()
                return False

            m1 = base64.b64encode(SrpUser.process_challenge(salt, b)).decode()
            m2 = base64.b64encode(SrpUser.H_AMK).decode()

            self._srp_icloud_io_signin_complete(username, {"c": data['c'], "m1": m1, "m2": m2})

        except Exception as err:
            log_exception(err)
            self._set_srp_return_error_code()
            return False

        # 200 = valid & signed in, 409 = valid but 2FA/HSA2 verification required
        self.response_code_pw = self.response_code
        self.auth_failed_503  = self.auth_failed_503 or self.response_code==503

        return self.response_code in [200, 409]

#----------------------------------------------------------------------------
    def _set_srp_return_error_code(self):
        self.login_successful     = False
        self.login_successful_srp = False
        self.response_code_pw     = self.response_code
        self.auth_failed_503      = self.auth_failed_503 or (self.response_code==503)

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

        # if reason is None:
            # reason = HTTP_RESPONSE_CODES.get(code, 'Other Error')
        reason = self.code_description(code) if reason is None else f"{reason} ({code})"

        if self.username not in Gb.AppleAcct_error_by_username:
            # v7.3-Commented out so logging into apple accts with 503 errors will not be retried
            # Gb.AppleAcct_error_by_username[self.username] = self

            self.error_codes  = f"{code}"
            self.error_reason = f"{reason}-{code}"
            self.error_secs   = time_now_secs()

        elif instr(self.error_reason, reason) is False:
            self.error_codes  += f", {code}"
            self.error_reason += f", {reason}-{code}"

        # Set retry at next 5-min + 10-mins
        if (code in [503]
                and self.error_next_retry_secs == 0):
            self.error_next_retry_secs = next_min_mark_secs(5, 10)

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
                        "(Authenticate Apple Account Sign-in)")
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
    def _use_srp_signin_token_info(self):
        '''
        Adopt the signin session token that the username/password validation just
        earned (ValidateAppleAcctUPW._save_srp_signin_token_info).

        The validation verifies the password with its own SRP
        signin/init+complete and Apple answers 409 - credentials valid, 2FA
        required - returning an X-Apple-Session-Token with it. Adopting that
        token lets authenticate() succeed at _authenticate_with_token and go
        straight to accountLogin. Without it the login posts a SECOND M1
        password proof to signin/complete seconds after the validation's, and
        Apple refuses that with a 503.

        Only the session token and account country are taken - never session_id
        or scnt, which identify the validation's idmsa signin session.
        '''
        if self.validate_aa_upw:
            return

        try:
            token_info = Gb.srp_token_info_by_username.pop(self.username, None)

            # Nothing to adopt, or this account already has a session of its own
            if (token_info is None
                    or is_empty(token_info.get('session_token'))
                    or self.session_data.get('session_token')):
                return

            if secs_since(token_info.get('secs', 0)) > SRP_SIGNIN_TOKEN_INFO_MAX_AGE_SECS:
                log_debug_msg(  f"{self.username_base}, Discarded the Username/Password "
                                f"validation's signin session token (too old)")
                return

            self.srp_valid_upw_secs = token_info['secs']
            self.session_data['session_token'] = token_info['session_token']
            if token_info.get('account_country'):
                self.session_data['account_country'] = token_info['account_country']

            log_debug_msg(  f"{self.username_base}, Adopted the Username/Password "
                            f"validation's signin session token, the login will use "
                            f"accountLogin instead of a second signin/complete")

        except Exception as err:
            log_exception(err)
