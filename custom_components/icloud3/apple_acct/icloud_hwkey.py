
from ..global_variables     import GlobalVariables as Gb
from ..utils.messaging      import (_log, log_info_msg, log_error_msg, log_exception, )
from ..utils.utils          import (instr, is_empty, isnot_empty, list_add, list_del, list_to_str, dict_del, )
from .                      import icloud_requests_io as icloud_io

#--------------------------------------------------------------------
import base64
from typing import Any, Dict, List, Optional

try:
    from fido2.client   import DefaultClientDataCollector, Fido2Client
    from fido2.hid      import CtapHidDevice
    from fido2.webauthn import (PublicKeyCredentialDescriptor,
                                PublicKeyCredentialRequestOptions,
                                PublicKeyCredentialType,
                                UserVerificationRequirement, )
    FIDO2_AVAILABLE = True
except ImportError:
    FIDO2_AVAILABLE = False

CONTENT_TYPE_JSON = "application/json"

#--------------------------------------------------------------------
def _b64url_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + '=' * (-len(s) % 4))

#--------------------------------------------------------------------
class iCloud_HwKey():

    def __init__(self, AppleAcct):
        self.AppleAcct    = AppleAcct
        self.fido2_device = None
        self.auth_error   = None

#--------------------------------------------------------------------
    def is_fido2_key_available(self) -> bool:
        """
        Determine if at least one FIDO2/USB HID security key is plugged in.

        Return: True/False
        Set:    fide2_device is product name of device plugged in
        """
        self.fido2_device = None
        if not FIDO2_AVAILABLE:
            return False

        for device in CtapHidDevice.list_devices():
            self.fido2_device = device.descriptor.product_name
            device.close()      # release it right away — just probing
            return True

        return False

# #--------------------------------------------------------------------
    def get_webauthn_options(self) -> Dict:
        AppleAcct = self.AppleAcct

        url     = AppleAcct.AUTH_ENDPOINT
        headers = self.get_auth_headers()
        data    = icloud_io.get(AppleAcct, url, headers=headers)

        return data

# #--------------------------------------------------------------------
    def get_auth_headers(self, overrides=None):
        AppleAcct = self.AppleAcct

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
        if AppleAcct.session_data.get("scnt"):
            headers["scnt"] = AppleAcct.session_data["scnt"]
        if AppleAcct.session_data.get("session_id"):
            headers["X-Apple-ID-Session-Id"] = AppleAcct.session_data["session_id"]
        if overrides:
            headers.update(overrides)
        return headers

#--------------------------------------------------------------------
    def _submit_webauthn_assertion_response(self, data: Dict) -> None:
        AppleAcct = self.AppleAcct


        url     = f"{AppleAcct.AUTH_ENDPOINT}/verify/security/key"
        headers = self.get_auth_headers({"Accept": CONTENT_TYPE_JSON})

        icloud_io.post(AppleAcct, url, json=data, headers=headers)

#--------------------------------------------------------------------
    def security_key_assertion_ceremony(self, hwkey_names=None) -> bool:
        """
        6-phase FIDO2 assertion ceremony. Returns True on success.

        This assertion challenge runs in 2-steps. This step sets up the hwkey
        challenge environment, finds the hardware keys and builds the public
        credentials.

        Then the user is instructed to Submit Authenticate on the step_reauth screen,
        which executes step #2 (parts 4 & 5) below.
        """
        self.error_msg = None
        if not FIDO2_AVAILABLE:
            self.error = 'Fido2 package not installed, cannot authenticate'
            log_error_msg(f"HwKey > {self.error_msg}")
            return False

        AppleAcct = self.AppleAcct

        # Phase 1: Get challenge + keyHandles + rpId from Apple
        try:
            options          = self.get_webauthn_options()
            fsa_challenge    = options.get("fsaChallenge", {})
            challenge_str    = fsa_challenge.get("challenge", "")
            allowed_creds    = fsa_challenge.get("keyHandles", [])
            rp_id            = fsa_challenge.get("rpId", "apple.com")
            log_info_msg(f"HwKey > Phase1 challenge retrieved, rpId={rp_id}")

        except Exception as err:
            self.error_msg = f"Phase1 failed — Could not get WebAuthn options: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False


        # Phase 2: Find USB HID key on HA server
        try:
            self.fido2_device = None
            devices = list(CtapHidDevice.list_devices())

            if devices == []:
                self.error_msg = "❌ The Hardware Key is not inserted into the HA Server, insert and retry",
                log_error_msg(f"HwKey > {self.error_msg}")
                return False

            device = devices[0]
            self.fido2_device = device.descriptor.product_name

            self.fido2_device = device.descriptor.product_name
            log_info_msg(f"HwKey > Phase2 using device: {self.fido2_device}, HwKeys: {hwkey_names}")

        except Exception as err:
            self.error_msg = f"Phase2 failed — Error listing FIDO2 devices: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False


        # Phase 3: Build PublicKeyCredentialRequestOptions
        try:
            credentials = [
                PublicKeyCredentialDescriptor(
                    id=_b64url_decode(cred_id),
                    type=PublicKeyCredentialType("public-key"))
                for cred_id in allowed_creds
            ]
            assertion_options = PublicKeyCredentialRequestOptions(
                challenge=_b64url_decode(challenge_str),
                rp_id=rp_id,
                allow_credentials=credentials,
                user_verification=UserVerificationRequirement("discouraged"))
            log_info_msg(f"HwKey > Phase3 options built, {len(credentials)} allowed credential(s)")

        except Exception as err:
            self.error_msg = f"Phase3 failed — Could not build assertion options: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False


        # Phase 4: Fido2Client.get_assertion — BLOCKS waiting for user to press key
        try:
            log_info_msg(f"HwKey > Phase4 waiting for key press on {device}...")
            client = Fido2Client(   device,
                                    client_data_collector=DefaultClientDataCollector("https://apple.com"))
            result = client.get_assertion(assertion_options).get_response(0)
            log_info_msg("HwKey > Phase4 assertion received")

        except Exception as err:
            self.error_msg = f"Phase4 failed — Assertion error: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False


        # Phase 5: Submit assertion to Apple
        try:
            self._submit_webauthn_assertion_response({
                "challenge":         challenge_str,
                "clientData":        base64.b64encode(result.response.client_data).decode(),
                "signatureData":     base64.b64encode(result.response.signature).decode(),
                "authenticatorData": base64.b64encode(result.response.authenticator_data).decode(),
                "userHandle":        base64.b64encode(result.response.user_handle).decode()
                                        if result.response.user_handle else None,
                "credentialID":      base64.b64encode(result.raw_id).decode(),
                "rpId":              rp_id,
            })
            log_info_msg("HwKey > Phase5 assertion submitted to Apple")

        except Exception as err:
            self.error_msg = f"Phase5 failed — Could not submit assertion: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False

        # Phase 6: Trust the session
        try:
            self.AppleAcct.trust_session()
            log_info_msg("HwKey > Phase6 session trusted — authentication complete")
            return True

        except Exception as err:
            self.error_msg = f"Phase6 failed — trust_session error: {err}"
            log_error_msg(f"HwKey > {self.error_msg}")
            return False
