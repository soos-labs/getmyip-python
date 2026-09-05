"""Tiny, dependency-free Python client for the getmyip.pro IP geolocation API.

Privacy-first (no logs, no trackers), ip-api-compatible JSON.
See https://getmyip.pro/docs (API at https://api.getmyip.pro).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field, fields

__all__ = ["DEFAULT_BASE_URL", "APIError", "Client", "Result"]
__version__ = "0.1.2"

DEFAULT_BASE_URL = "https://api.getmyip.pro"


class APIError(Exception):
    """Non-200 API response; carries HTTP status and the API's error code."""

    def __init__(self, status: int, error: str = ""):
        self.status = status
        self.error = error
        super().__init__(f"getmyip: {error or 'unexpected status'} (status {status})")


@dataclass
class Result:
    """A single geolocation lookup response."""

    ip: str = ""
    ip_version: int = 0
    is_private: bool = False
    country_code: str = ""
    country: str = ""
    region: str = ""
    city: str = ""
    postal: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    timezone: str = ""
    asn: int = 0
    org: str = ""
    hostname: str = ""
    # поля, которых клиент ещё не знает, не теряются при апгрейде API
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> Result:
        known = {f.name for f in fields(cls)} - {"extra"}
        kw = {k: v for k, v in d.items() if k in known}
        extra = {k: v for k, v in d.items() if k not in known}
        return cls(**kw, extra=extra)


class Client:
    """Talks to the getmyip API.

    An API key is optional — the free anonymous tier needs none; a key
    (``X-API-Key``) raises rate limits.
    """

    def __init__(self, api_key: str = "", base_url: str = DEFAULT_BASE_URL, timeout: float = 10.0):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def me(self) -> Result:
        """Geolocation for the caller's own public IP."""
        return Result.from_dict(self._request("GET", "/v1/json"))

    def lookup(self, ip: str) -> Result:
        """Geolocation for the given IPv4 or IPv6 address."""
        return Result.from_dict(self._request("GET", "/v1/" + urllib.parse.quote(ip, safe="")))

    def batch(self, ips: list[str]) -> list[Result]:
        """Look up many addresses in a single request."""
        out = self._request("POST", "/v1/batch", {"ips": ips})
        return [Result.from_dict(r) for r in out.get("results", [])]

    def _request(self, method: str, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method)
        req.add_header("Accept", "application/json")
        # дефолтный Python-urllib/* UA режется ботозащитой edge — представляемся собой
        req.add_header("User-Agent", f"getmyip-pro-python/{__version__}")
        if data is not None:
            req.add_header("Content-Type", "application/json")
        if self.api_key:
            req.add_header("X-API-Key", self.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.load(resp)
        except urllib.error.HTTPError as e:
            try:
                err = json.load(e).get("error", "")
            except (ValueError, OSError):
                err = ""
            raise APIError(e.code, err) from None
