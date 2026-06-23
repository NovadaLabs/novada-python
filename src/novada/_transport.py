"""HTTP transport: Bearer injection, two body encodings, retries.

The top-level :class:`~novada.client.Client` owns a single :class:`Transport`
and passes it to every sub-service. ``Transport`` is the Python equivalent of
the Go SDK's ``transport.Doer`` interface — it exposes the two encoding helpers
(multipart for ``/v1/*`` management endpoints, x-www-form-urlencoded for the
scraper ``/request`` endpoints), each with a ``_raw`` variant that skips
envelope decoding, plus the three host attributes so a service can pick the
right base URL per endpoint.
"""

from __future__ import annotations

import binascii
import os
import time
from typing import Any, Optional
from urllib.parse import urlencode

import httpx

from ._envelope import decode_envelope, http_error_message
from .errors import APIError, AuthError, NovadaError, RateLimitError

# retry_base_delay is the base backoff between retry attempts; it is multiplied
# by the attempt index to produce a simple linear backoff (200ms, 400ms, ...).
RETRY_BASE_DELAY = 0.2


def _error_for_status(status: int, message: str) -> APIError:
    """Map a non-2xx HTTP status onto the matching APIError subclass."""
    if status in (401, 403):
        return AuthError(message, http_status=status)
    if status == 429:
        return RateLimitError(message, http_status=status)
    return APIError(message, http_status=status)


def _build_multipart(fields: dict[str, str]) -> tuple[bytes, str]:
    """Encode *fields* as a multipart/form-data body, omitting empty values.

    Returns the body bytes and the matching Content-Type (with boundary).
    Mirrors the Go SDK's buildMultipart: only non-empty text fields are written.
    """
    boundary = binascii.hexlify(os.urandom(16)).decode("ascii")
    parts: list[bytes] = []
    for key, value in fields.items():
        if value == "":
            continue
        # Escape per RFC 2388 / Go's escapeQuotes: backslash and double quote.
        name = key.replace("\\", "\\\\").replace('"', '\\"')
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode())
        parts.append(value.encode("utf-8"))
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _join_url(base: str, path: str) -> str:
    """Concatenate a base URL and a path, tolerating a trailing slash on the
    base and a missing leading slash on the path."""
    base = base.rstrip("/")
    if not path.startswith("/"):
        path = "/" + path
    return base + path


class Transport:
    """Performs HTTP requests with Bearer injection and retry handling."""

    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        web_unblocker_url: str,
        scraper_url: str,
        http_client: httpx.Client,
        max_retries: int,
        user_agent: str,
    ) -> None:
        self._api_key = api_key
        self.base_url = base_url
        self.web_unblocker_url = web_unblocker_url
        self.scraper_url = scraper_url
        self._http = http_client
        self._max_retries = max_retries
        self._user_agent = user_agent

    # --- public encoding helpers -------------------------------------------

    def do_multipart(self, base_url: str, path: str, fields: dict[str, str]) -> Any:
        """POST *fields* as multipart/form-data and return the decoded envelope
        ``data`` payload (the encoding used by every ``/v1/*`` endpoint)."""
        body, content_type = _build_multipart(fields)
        resp_body, status = self._do_raw(_join_url(base_url, path), content_type, body)
        return decode_envelope(status, resp_body)

    def do_multipart_raw(self, base_url: str, path: str, fields: dict[str, str]) -> bytes:
        """Like :meth:`do_multipart` but return the raw response body without
        envelope decoding (for endpoints that return a file stream)."""
        body, content_type = _build_multipart(fields)
        resp_body, _ = self._do_raw(_join_url(base_url, path), content_type, body)
        return resp_body

    def do_form_urlencoded(self, base_url: str, path: str, values: dict[str, str]) -> Any:
        """POST *values* as x-www-form-urlencoded and return the decoded
        envelope ``data`` payload (used by the structured scraper queries)."""
        body = urlencode(values).encode("utf-8")
        resp_body, status = self._do_raw(
            _join_url(base_url, path), "application/x-www-form-urlencoded", body
        )
        return decode_envelope(status, resp_body)

    def do_form_urlencoded_raw(self, base_url: str, path: str, values: dict[str, str]) -> bytes:
        """Like :meth:`do_form_urlencoded` but return the raw response body.
        Scraper ``/request`` responses are the scraped payload itself (JSON,
        CSV or XLSX), not the management envelope."""
        body = urlencode(values).encode("utf-8")
        resp_body, _ = self._do_raw(
            _join_url(base_url, path), "application/x-www-form-urlencoded", body
        )
        return resp_body

    # --- core request loop --------------------------------------------------

    def _do_raw(self, full_url: str, content_type: str, body: bytes) -> tuple[bytes, int]:
        """Perform the POST with Bearer injection and retry handling.

        Retries apply only to network errors and HTTP 429/5xx (linear backoff);
        a non-2xx response after retries is raised as an :class:`APIError`. The
        business code in a 2xx envelope is never retried.
        """
        last_err: Optional[BaseException] = None
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": content_type,
            "Accept": "application/json",
            "User-Agent": self._user_agent,
        }

        for attempt in range(self._max_retries + 1):
            if attempt > 0:
                time.sleep(RETRY_BASE_DELAY * attempt)

            try:
                resp = self._http.post(full_url, content=body, headers=headers)
            except httpx.HTTPError as exc:
                last_err = exc  # network error: retry
                continue

            resp_body = resp.content
            status = resp.status_code

            if status == 429 or status >= 500:
                last_err = _error_for_status(
                    status, http_error_message(resp_body, resp.reason_phrase)
                )
                continue  # 429/5xx: retry

            if status < 200 or status >= 300:
                raise _error_for_status(status, http_error_message(resp_body, resp.reason_phrase))

            return resp_body, status

        if isinstance(last_err, APIError):
            raise last_err
        raise NovadaError(f"novada: request failed: {last_err}") from last_err
