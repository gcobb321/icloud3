
from ..global_variables     import GlobalVariables as Gb
from ..const                import (AIRPODS_FNAME, NONE_FNAME,
                                    EVLOG_NOTICE, EVLOG_ALERT, LINK, RLINK, LLINK, DOTS,
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
                                    encode_password, decode_password, username_id, is_running_in_event_loop,)
from ..utils                import file_io
from ..utils.time_util      import (time_now, time_now_secs, secs_to_time, s2t, apple_server_time,
                                    secs_since, format_secs_since, format_age, format_time_age )
from ..utils.messaging      import (post_event, post_alert, post_alert, post_monitor_msg, post_error_msg,
                                    _evlog, _log, more_info, add_log_file_filter,
                                    log_info_msg, log_error_msg, log_debug_msg, log_warning_msg,
                                    log_data, log_exception, log_data_unfiltered, )
from ..utils                import gps

from .                      import icloud_requests_io  as icloud_io

#--------------------------------------------------------------------
import base64
import base64
from typing import Any, Dict, List, Optional
from uuid import uuid1

from fido2.client           import DefaultClientDataCollector, Fido2Client
from fido2.hid              import CtapHidDevice
from fido2.webauthn         import (AuthenticationResponse,
                                    PublicKeyCredentialDescriptor,
                                    PublicKeyCredentialRequestOptions,
                                    PublicKeyCredentialType,
                                    UserVerificationRequirement, )

CONTENT_TYPE_JSON = "application/json"

#--------------------------------------------------------------------
class iCloud_Fido2():

    def __init__(self, AppleAcct):
        self.AppleAcct = AppleAcct

#--------------------------------------------------------------------
    @property
    def trusted_devices(self) -> list[dict[str, Any]]:
        """Returns devices trusted for two-step authentication."""
        AppleAcct = self.AppleAcct

        url = f"{AppleAcct._setup_endpoint}/listDevices"

        data = icloud_io.get(AppleAcct, url, params=self.params)

        return data.get("devices")

#--------------------------------------------------------------------
    def send_verification_code(self, device: dict[str, Any]) -> bool:
        """Requests that a verification code is sent to the given device."""
        AppleAcct = self.AppleAcct

        url = f"{AppleAcct._setup_endpoint}/sendVerificationCode"

        data = icloud_io.post(AppleAcct, url, params=self.params, json=device)

        return data.get("success", False)

#--------------------------------------------------------------------
    def validate_verification_code(self, device: dict[str, Any], code: str) -> bool:
        """Verifies a verification code received on a trusted device."""
        AppleAcct = self.AppleAcct

        device.update({"verificationCode": code, "trustBrowser": True})

        try:
            url = f"{AppleAcct._setup_endpoint}/validateVerificationCode"

            icloud_io.post(AppleAcct, url, params=self.params, json=device)

        except AppleAcctAPIResponseException as error:
            if error.code == -21669:
                # Wrong verification code
                return False
            raise

        self.trust_session()

        return not self.requires_2sa

#--------------------------------------------------------------------
    def _get_webauthn_options(self) -> Dict:
        """Retrieve WebAuthn request options (PublicKeyCredentialRequestOptions) for assertion."""
        AppleAcct = self.AppleAcct

        url     = AppleAcct.AUTH_ENDPOINT
        headers = self._get_auth_headers({"Accept": CONTENT_TYPE_JSON})

        data = icloud_io.get(AppleAcct, url, headers=headers)

        return data
#--------------------------------------------------------------------
    def _get_auth_headers(self, overrides=None):
        headers = {
            "Accept": f"{CONTENT_TYPE_JSON}, text/javascript",
            "Content-Type": CONTENT_TYPE_JSON,
            "X-Apple-OAuth-Client-Id": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
            "X-Apple-OAuth-Client-Type": "firstPartyAuth",
            "X-Apple-OAuth-Redirect-URI": "https://www.icloud.com",
            "X-Apple-OAuth-Require-Grant-Code": "true",
            "X-Apple-OAuth-Response-Mode": "web_message",
            "X-Apple-OAuth-Response-Type": "code",
            "X-Apple-OAuth-State": self.AppleAcct.client_id,
            "X-Apple-Widget-Key": "d39ba9916b7251055b22c7f910e2ea796ee65e98b2ddecea8f5dde8d9d1a815d",
        }

        if self.AppleAcct.session_data.get("scnt"):
            headers["scnt"] = self.AppleAcct.session_data["scnt"]

        if self.AppleAcct.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = self.AppleAcct.session_data["session_id"]

        if overrides:
            headers.update(overrides)

        return headers

#--------------------------------------------------------------------
    @property
    def fido2_devices(self) -> List[CtapHidDevice]:
        """List the available FIDO2 devices."""
        _log(f"{CtapHidDevice.__dict__=}")
        _log(f"{CtapHidDevice.list_devices()=}")
        return list(CtapHidDevice.list_devices())

#--------------------------------------------------------------------
    @property
    def security_key_names(self) -> Optional[List[str]]:
        """
        Security key names which can be used for the WebAuthn assertion.

        This can not be called directly from an async function using the
        Gb.hass.async_add_executor_job function - it will be running in the
        Event Loop and will generate a downstream error.

        When running in an async function, use Gb.hass.async_add_executor_job to
        call a function in AppleAcct (non-Event Loop) which will then call this
        function.
        """

        _security_key_names = self._get_webauthn_options().get("keyNames")
        return _security_key_names

#--------------------------------------------------------------------
    def _submit_webauthn_assertion_response(self, data: Dict) -> None:
        """Submit the WebAuthn assertion response for authentication."""
        AppleAcct = self.AppleAcct

        url     = f"{AppleAcct.AUTH_ENDPOINT}/verify/security/key"
        headers = AppleAcct._get_auth_headers({"Accept": CONTENT_TYPE_JSON})

        icloud_io.post(AppleAcct, url, json=data, headers=headers)

#--------------------------------------------------------------------
    def confirm_security_key(self, device: Optional[CtapHidDevice] = None) -> None:
        """Conduct the WebAuthn assertion ceremony with user's FIDO2 device."""
        options   = self._get_webauthn_options()
        challenge = options["fsaChallenge"]["challenge"]
        allowed_credentials = options["fsaChallenge"]["keyHandles"]
        rp_id     = options["fsaChallenge"]["rpId"]
        _log(f'{device=}')

        if not device:
            devices = list(CtapHidDevice.list_devices())
            _log(f'{devices=}')

            if is_empty(devices):
                raise RuntimeError("No FIDO2 devices found")

            device = devices[0]

        client = Fido2Client(device,
                            client_data_collector=DefaultClientDataCollector("https://apple.com"))
        _log(f'{client=}')

        credentials = [PublicKeyCredentialDescriptor(
                                    id=base64.b64url_decode(cred_id),
                                    type=PublicKeyCredentialType("public-key"))
                            for cred_id in allowed_credentials]
        _log(f'{credentials=}')

        assertion_options = PublicKeyCredentialRequestOptions(
                            challenge=base64.b64url_decode(challenge),
                            rp_id=rp_id,
                            allow_credentials=credentials,
                            user_verification=UserVerificationRequirement("discouraged"))
        _log(f'{assertion_options=}')

        result = client.get_assertion(assertion_options).get_response(0)
        _log(f'{result=}')

        self._submit_webauthn_assertion_response({
                            "challenge": challenge,
                            "clientData": base64.b64_encode(result.response.client_data),
                            "signatureData": base64.b64_encode(result.response.signature),
                            "authenticatorData": base64.b64_encode(result.response.authenticator_data),
                            "userHandle": base64.b64_encode(result.response.user_handle)
                            if result.response.user_handle
                            else None,
                            "credentialID": base64.b64_encode(result.raw_id),
                            "rpId": rp_id})

        self.trust_session()

#--------------------------------------------------------------------
class AppleAcctException(Exception):
    """Generic iCloud exception."""

class AppleAcctAPIResponseException(AppleAcctException):
    """iCloud response exception."""

    def __init__(self, reason, code=None) -> None:
        self.reason: str = reason
        self.code = code
        message: str = reason or ""
        if code:
            message += f" ({code})"

        super().__init__(message)

'''
| 🟡 url='https://idmsa.apple.com/appleauth/auth'    |
10-27 04:41:06 | _LOG | [icloud_fido:117/_get_webau] [icloud_fido:117,126; pyicloud_ic3:1268; icloud_dat…handle:238]
| 🟡 data={'trustedPhoneNumbers': [{'numberWithDialCode': '+1 (772) 321-3766', 'nonFTEU': False,
 'pushMode': 'sms', 'obfuscatedNumber': '(•••) •••-••66', 'lastTwoDigits': '66', 'id': 1},
 {'numberWithDialCode': '+1 (772) 321-3765', 'nonFTEU': False, 'pushMode': 'sms',
 'obfuscatedNumber': '(•••) •••-••65', 'lastTwoDigits': '65', 'id': 2}], 'securityCode': {'length':
 6, 'tooManyCodesSent': False, 'tooManyCodesValidated': False, 'securityCodeLocked': False,
 'securityCodeCooldown': False}, 'authenticationType': 'hsa2',
 'recoveryUrl': 'https://iforgot.apple.com/phone/add?prs_account_nm=gco**1**21@%40&autoSubmitAccount=true&appId=142',
 'cantUsePhoneNumberUrl': 'https://iforgot.apple.com/iforgot/phone/add?context=cantuse&
 prs_account_nm=gco**1**21@%40&autoSubmitAccount=true&appId=142',
 'recoveryWebUrl': 'https://iforgot.apple.com/password/verify/appleid?prs_account_nm=gco**1**21@%40&autoSubmitAccount=true&appId=142', 'repairPhoneNumberUrl':
 'https://gsa.apple.com/appleid/account/manage/repair/verify/phone',
 'repairPhoneNumberWebUrl': 'https://appleid.apple.com/widget/account/repair?#!repair', 'aboutTwoFactorAuthenticationUrl': 'https://support.apple.com/kb/HT204921', 'twoFactorVerificationSupportUrl': 'https://support.apple.com/HT208072',
 'hasRecoveryKey': True, 'supportsRecoveryKey': False, 'autoVerified': False,
 'showAutoVerificationUI': False, 'supportsCustodianRecovery': False, 'hideSendSMSCodeOption':
 False, 'supervisedChangePasswordFlow': False, 'enableNonFTEU': True, 'content':
 {'enterCodeDescription': 'Enter the verification code sent to your Apple devices.',
 'sendCodeDescription': 'Apple can send another verification code to your other Apple devices.',
 'resendCodeLink': 'Resend code to devices', 'canNotGetCodeLink': 'Can’t get to your devices?',
  'canNotGetCodeTitle': 'Can’t get to your devices?'},
  'trustedPhoneNumber': {'numberWithDialCode': '+1 (772) 321-3766', 'nonFTEU': False, 'pushMode':
  'sms', 'obfuscatedNumber': '(•••) •••-••66', 'lastTwoDigits': '66', 'id': 1},
  'hsa2Account': True, 'restrictedAccount': False, 'supportsRecovery': True,
  'managedAccount': False}    |
'''