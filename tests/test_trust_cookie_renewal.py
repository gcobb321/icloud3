from copy import copy
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event, Thread
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import requests

from custom_components.icloud3.apple_acct import apple_acct, icloud_session
from custom_components.icloud3.apple_acct.icloud_cookie_jar import PyiCloudCookieJar
from custom_components.icloud3.const import TRUST_COOKIE_NAME


class TrustCookieRenewalTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(TemporaryDirectory())
        self.filename = str(Path(directory) / "cookies")
        self.transport = object.__new__(icloud_session.iCloudSession)
        self.transport.headers = {"Origin": "https://www.icloud.com"}
        self.transport.cookies = PyiCloudCookieJar(filename=self.filename)
        self.current = requests.cookies.create_cookie(
            TRUST_COOKIE_NAME, "existing-trust", domain=".icloud.com",
            path="/", expires=2_100_000_000, secure=True,
        )
        self.transport.cookies.set_cookie(self.current)
        self.transport.cookies.save()
        self.original_file = Path(self.filename).read_bytes()
        self.transport.AppleAcct = SimpleNamespace(
            session_data={"session_token": "web-token", "trust_token": "proof"},
            SETUP_ENDPOINT="https://setup.icloud.com/setup/ws/1",
            params={"clientId": "client"},
            dsid="123",
            cookies_filename=self.filename,
            cookies_filename_short="cookies",
            session_filename=str(Path(directory) / "session.json"),
            iCloudSession=self.transport,
            validate_aa_upw=False,
        )
        account = self.transport.AppleAcct
        account._token_login_data = lambda: apple_acct.AppleAcctManager._token_login_data(account)
        self.session_class = self.enterContext(patch.object(icloud_session, "Session"))
        self.probe = self.session_class.return_value.__enter__.return_value
        self.probe.cookies = requests.cookies.RequestsCookieJar()
        self.response = self.probe.post.return_value
        self.response.status_code = 200
        self.response.json.return_value = {
            "hsaTrustedBrowser": True, "hsaChallengeRequired": False,
            "dsInfo": {"dsid": "123"},
        }
        self.renewed = copy(self.current)
        self.renewed.expires += 3600
        self.response.cookies = [self.renewed]

    def test_renewed_expiry_persists_for_the_existing_cookie(self):
        self.response.cookies.append(requests.cookies.create_cookie("unrelated", "value"))
        self.assertTrue(self.transport.renew_trust_cookie(self.current))
        self.probe.post.assert_called_once()
        self.assertEqual(self.probe.post.call_args.args[0],
                         "https://setup.icloud.com/setup/ws/1/accountLogin")
        self.assertFalse(self.probe.post.call_args.kwargs["allow_redirects"])
        self.assertEqual(self.probe.post.call_args.kwargs["json"]["dsWebAuthToken"], "web-token")
        self.assertEqual(list(self.transport.cookies), [self.renewed])
        saved = PyiCloudCookieJar(filename=self.filename)
        saved.load()
        self.assertEqual(saved.get_cookie(TRUST_COOKIE_NAME).expires, self.renewed.expires)
        self.assertEqual(self.transport.AppleAcct.session_data["session_token"], "web-token")

    def test_declined_or_inconclusive_refresh_preserves_the_session(self):
        rotated = copy(self.renewed)
        rotated.value = "different-trust"
        normal_body = self.response.json.return_value
        cases = (
            (403, {}, []),
            (503, {}, []),
            (200, {**normal_body, "hsaChallengeRequired": True}, [self.renewed]),
            (200, {**normal_body, "dsInfo": {"dsid": "456"}}, [self.renewed]),
            (200, normal_body, []),
            (200, normal_body, [self.current]),
            (200, normal_body, [rotated]),
        )
        for status, body, cookies in cases:
            with self.subTest(status=status, body=body, cookies=len(cookies)):
                self.response.status_code = status
                self.response.json.return_value = body
                self.response.cookies = cookies
                self.assertFalse(self.transport.renew_trust_cookie(self.current))
                self.assertEqual(list(self.transport.cookies), [self.current])
                self.assertEqual(Path(self.filename).read_bytes(), self.original_file)

    def test_a_parallel_sign_in_takes_precedence(self):
        def sign_in(*args, **kwargs):
            self.transport.AppleAcct.session_data["session_token"] = "new-web-token"
            return self.response

        self.probe.post.side_effect = sign_in
        self.assertFalse(self.transport.renew_trust_cookie(self.current))
        self.assertEqual(list(self.transport.cookies), [self.current])
        self.assertEqual(Path(self.filename).read_bytes(), self.original_file)

    def test_failed_persistence_leaves_the_current_cookie(self):
        with patch.object(icloud_session, "replace", side_effect=OSError), patch.object(
            icloud_session, "log_warning_msg"
        ):
            self.assertFalse(self.transport.renew_trust_cookie(self.current))
        self.assertEqual(list(self.transport.cookies), [self.current])
        self.assertEqual(Path(self.filename).read_bytes(), self.original_file)

    def test_sign_in_at_file_replacement_keeps_the_newer_cookie(self):
        account = self.transport.AppleAcct
        jar = self.transport.cookies
        newer = copy(self.renewed)
        newer.value = "interactive-trust"
        writer_ready = Event()
        result = []

        response = requests.Response()
        response.status_code = 200
        response.headers.update({
            "Content-Type": "application/json",
            "X-Apple-Session-Token": "interactive-token",
        })
        response._content = b"{}"

        def complete_sign_in(*args, **kwargs):
            # Simulate Requests extracting cookies before _request saves the response.
            if jar._cookies_lock.acquire(blocking=False):
                jar._cookies_lock.release()
            else:
                writer_ready.set()
            jar.set_cookie(newer)
            return response

        def interactive_sign_in():
            result.append(self.transport._request("POST", f"{account.SETUP_ENDPOINT}/accountLogin"))
            writer_ready.set()

        writer = Thread(target=interactive_sign_in, daemon=True)
        replace = icloud_session.replace

        def replace_while_sign_in_is_ready(source, destination):
            writer.start()
            self.assertTrue(writer_ready.wait(3))
            return replace(source, destination)

        self.session_class.request.side_effect = complete_sign_in
        self.transport._is_test_acct_locked = Mock(return_value=False)
        with patch.object(icloud_session, "replace", side_effect=replace_while_sign_in_is_ready), patch.object(
            icloud_session, "log_request_data"
        ), patch.object(icloud_session, "log_debug_msg"), patch.object(
            icloud_session.Gb, "internet_error", False
        ):
            self.assertTrue(self.transport.renew_trust_cookie(self.current))
            writer.join(3)
            self.assertFalse(writer.is_alive())

        self.assertEqual(result, [{}])
        self.assertEqual(account.session_data["session_token"], "interactive-token")
        self.assertIs(jar.get_cookie(TRUST_COOKIE_NAME), newer)
        persisted = PyiCloudCookieJar(filename=self.filename)
        persisted.load()
        self.assertEqual(persisted.get_cookie(TRUST_COOKIE_NAME).value, newer.value)

    def test_sign_in_from_another_client_wins_during_the_probe(self):
        newer = copy(self.renewed)
        newer.value = "other-client-trust"

        def save_from_another_client(*args, **kwargs):
            other = PyiCloudCookieJar(filename=self.filename)
            other.set_cookie(newer)
            other.save()
            return self.response

        self.probe.post.side_effect = save_from_another_client
        self.assertFalse(self.transport.renew_trust_cookie(self.current))
        persisted = PyiCloudCookieJar(filename=self.filename)
        persisted.load()
        self.assertEqual(persisted.get_cookie(TRUST_COOKIE_NAME).value, newer.value)
        self.assertEqual(list(self.transport.cookies), [self.current])

    def test_daily_check_only_uses_a_live_near_expiry_cookie(self):
        account = object.__new__(apple_acct.AppleAcctManager)
        account.iCloudSession = Mock(cookies=self.transport.cookies)
        account.validate_aa_upw = False
        account.is_authenticated = True
        account.is_reauth_needed = False
        account.session_data = self.transport.AppleAcct.session_data.copy()
        account.iCloudSession.renew_trust_cookie.return_value = False

        with patch.object(apple_acct, "time_now_secs") as now:
            for remaining in (-1, 0, 15 * 86400):
                now.return_value = self.current.expires - remaining
                account.renew_trust_cookie_if_needed()
            account.iCloudSession.renew_trust_cookie.assert_not_called()

            now.return_value = self.current.expires - 14 * 86400
            account.is_reauth_needed = True
            account.renew_trust_cookie_if_needed()
            account.iCloudSession.renew_trust_cookie.assert_not_called()

            account.is_reauth_needed = False
            account.renew_trust_cookie_if_needed()
            account.iCloudSession.renew_trust_cookie.assert_called_once_with(self.current)
