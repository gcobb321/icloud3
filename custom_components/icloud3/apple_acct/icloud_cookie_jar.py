"""Cookie jar with persistence support."""

from ..utils.messaging   import (_log, log_info_msg, shrink_item, )
from ..utils.time_util   import (secs_to_datetime)

from http.cookiejar import LWPCookieJar
from typing import Optional

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
