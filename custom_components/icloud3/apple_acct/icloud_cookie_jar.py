"""Cookie jar with persistence support."""

from ..const             import HIGH_INTEGER
from ..utils.messaging   import (_log, log_info_msg, log_exception, shrink_item, )
from ..utils.time_util   import (secs_to_datetime, format_date_time)

from http.cookiejar import LWPCookieJar
from typing import Optional
import time
from datetime import datetime

from requests.cookies import RequestsCookieJar

_FMIP_AUTH_COOKIE_NAME: str = "X-APPLE-WEBAUTH-FMIP"


class PyiCloudCookieJar(RequestsCookieJar, LWPCookieJar):
    """Mix the Requests CookieJar with the LWPCookieJar to allow persistance"""

    def __init__(self, filename: Optional[str] = None) -> None:
        """Initialise both bases; do not pass filename positionally to RequestsCookieJar."""
        RequestsCookieJar.__init__(self)
        LWPCookieJar.__init__(self, filename=filename)

    def _resolve_filename(self, filename: Optional[str]) -> Optional[str]:
        resolved: Optional[str] = filename or getattr(self, "filename", None)
        if not resolved:
            return  # No-op if no filename is bound
        return resolved

    def load(
        self,
        filename: Optional[str] = None,
        ignore_discard: bool = True,
        ignore_expires: bool = False,
    ) -> None:
        """Load cookies from file."""
        resolved: Optional[str] = self._resolve_filename(filename)
        if not resolved:
            return  # No-op if no filename is bound
        super().load(
            filename=resolved,
            ignore_discard=ignore_discard,
            ignore_expires=ignore_expires,
        )
        # Clear any FMIP cookie regardless of domain/path to avoid stale auth.
        cookies_to_clear: list[tuple[str, str, str]] = [
            (cookie.domain, cookie.path, cookie.name)
            for cookie in self
            if cookie.name == _FMIP_AUTH_COOKIE_NAME
        ]
        for domain, path, name in cookies_to_clear:
            try:
                self.clear(domain=domain, path=path, name=name)
            except KeyError:
                pass

    def save(
        self,
        filename: Optional[str] = None,
        ignore_discard: bool = True,
        ignore_expires: bool = False,
    ) -> None:
        """Save cookies to file."""
        resolved: Optional[str] = self._resolve_filename(filename)
        if not resolved:
            return  # No-op if no filename is bound
        super().save(
            filename=resolved,
            ignore_discard=ignore_discard,
            ignore_expires=ignore_expires,
        )

    def list(self):
        _log_msg = ''
        for cookie in self:
            _log_msg +=(f"\n⠂  ❗ _.Cookie.{cookie.name}, "
                        f"Expires-{secs_to_datetime(cookie.expires)}, "
                        f"{shrink_item(cookie.value)}")

        log_info_msg(_log_msg)

    def exists(self, cookie_name=None):
        if cookie_name is None:
            return False

        for cookie in self:
            if cookie.name == cookie_name:
                return True

        return False


    def get_cookie(self, cookie_name=None):
        if cookie_name is None:
            return None

        for cookie in self:
            if cookie.name == cookie_name:
                return cookie

        return None


    def delete(self, delete_cookie):
        '''
        Remove X-APPLE-WEBAUTH-HSA-TRUST cookie regardless of exact
        domain it was stored under.
        '''

        for cookie in self:
            if cookie.name == delete_cookie:
                self.clear(cookie.domain, cookie.path, cookie.name)
                return True

        removed = False

    def get_trust_cookie_info(self):
        '''
        Read the X-APPLE-WEBAUTH-HSA-TRUST cookie expiry directly from the
        cookie jar without making any network request.

        Returns a dict with:
            'found'       : bool   - cookie exists in jar
            'expired'     : bool   - cookie is already past its expiry
            'expires_secs': float  - Unix timestamp of expiry (0 if session cookie)
            'expires_time': str    - Human readable expiry time
            'secs_remaining': int  - Seconds until expiry (-1 if already expired)
            'expire_in_days': float - Days until expiry (-1 if already expired)
            'is_session_cookie': bool - True if no expiry set (expires when HA restarts)
        '''
        result = {
            'found':        False,
            'expired':      True,
            'expire_secs': 0,
            'expire_date_time': 'Unknown',
            'expire_in_secs':  -1,
            'expire_in_days':  -1,
            'expire_in_text': '-1 day',
            'is_session_cookie': False,
        }

        try:
            cookie = self.get_cookie('X-APPLE-WEBAUTH-HSA-TRUST')

            if cookie is None:
                return result

            result['found'] = True
            now_secs = time.time()

            # Session cookie — no expiry date, lives until the process/HA restarts
            if cookie.expires is None:
                result['is_session_cookie'] = True
                result['expired']           = False
                result['expire_date_time']       = 'Session cookie (expires on HA restart)'
                result['expire_in_secs']    = HIGH_INTEGER
                result['expire_in_days']    = HIGH_INTEGER
                result['expire_in_text']    = '99999 days'
                return result

            result['expire_secs'] = cookie.expires
            result['expire_date_time'] = format_date_time(cookie.expires)
            # result['expire_date_time'] = datetime.fromtimestamp(cookie.expires).strftime(
            #                             '%m-%d %H:%M:%S')

            secs_remaining = cookie.expires - now_secs
            result['expired']         = secs_remaining <= 0
            result['expire_in_secs']  = int(secs_remaining)
            if secs_remaining < 86400:
                result['expire_in_days'] = round(secs_remaining / 86400, 1)
                result['expire_in_text'] = f"{result['expire_in_days']:.1f} days"
            else:
                result['expire_in_days'] = round(secs_remaining / 86400)
                result['expire_in_text'] = f"{result['expire_in_days']:.0f} days"

            return result

        except Exception as err:
            log_exception(err)
            return result


    def expire_in_days(self):
        cookie = self.get_cookie('X-APPLE-WEBAUTH-HSA-TRUST')

        if cookie is None:
            return -1

        secs_remaining  = cookie.expires - time.time()
        _expire_in_days = round(secs_remaining / 86400, 1)
        if secs_remaining < 86400:
            return _expire_in_days

        return int(_expire_in_days)


# def is_trust_cookie_valid(self, warn_days=3):
#     '''
#     Quick boolean check — is the trust cookie present, not expired,
#     and not expiring within warn_days?

#     Args:
#         warn_days: Log a warning if expiry is within this many days (default 3)

#     Returns:
#         True  - Cookie is valid and not about to expire
#         False - Cookie is missing, expired, or expiring very soon
#     '''
#     info = self.get_trust_cookie_info()

#     if not info['found']:
#         log_warning_msg(f"{self.username_base}, Trust cookie MISSING from cookie jar — "
#                         f"full re-authentication required")
#         return False

#     if info['is_session_cookie']:
#         # Session cookies are valid until HA restarts — treat as valid
#         return True

#     if info['expired']:
#         log_warning_msg(f"{self.username_base}, Trust cookie EXPIRED — "
#                         f"full re-authentication required")
#         return False

#     # Warn if expiring soon
#     if info['expire_in_days'] <= warn_days:
#         log_warning_msg(f"{self.username_base}, Trust cookie expiring soon — "
#                         f"{info['expire_in_days']} days remaining "
#                         f"(expires {info['expires_time']})")
#         # Still valid though — don't return False
#         post_alert( f"Apple Acct > {self.username_base}, "
#                     f"Trust cookie expires in {info['expire_in_days']} days "
#                     f"({info['expires_time']}) — re-authentication will be needed soon")

#     return True


# def log_all_cookie_expiries(self):
#     '''
#     Log the name and expiry of every cookie in the jar.
#     Useful for debugging the full cookie state.
#     '''
#     if not Gb.is_log_level_debug:
#         return

#     try:
#         cookies = list(self.iCloudSession.cookies)
#         if not cookies:
#             log_debug_msg(f"{self.username_base}, Cookie jar is empty")
#             return

#         now_secs = time.time()
#         lines = [f"{self.username_base}, Cookie jar contents ({len(cookies)} cookies):"]

#         for cookie in cookies:
#             if cookie.expires is None:
#                 expiry_str = "session cookie"
#             elif cookie.expires <= now_secs:
#                 expiry_str = f"EXPIRED ({datetime.fromtimestamp(cookie.expires).strftime('%Y-%m-%d %H:%M')})"
#             else:
#                 days = (cookie.expires - now_secs) / 86400
#                 expiry_str = (  f"expires {datetime.fromtimestamp(cookie.expires).strftime('%Y-%m-%d %H:%M')} "
#                                 f"({days:.1f} days)")

#             lines.append(f"  {cookie.name}: {expiry_str}")

#         log_debug_msg("\n".join(lines))

#     except Exception as err:
#         log_exception(err)
