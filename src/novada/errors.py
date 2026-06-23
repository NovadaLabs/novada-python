"""Error types raised by the Novada SDK.

The hierarchy mirrors the Go SDK's ``APIError`` plus its ``IsAuthError`` /
``IsRateLimited`` / ``CodeOf`` helpers, but expresses the distinctions as
Python subclasses so callers can use ``except`` / ``isinstance``:

    NovadaError                 # base for everything raised by this package
    ├── APIError                # a failed API call (.http_status / .code / .message)
    │   ├── AuthError           # HTTP 401 / 403
    │   └── RateLimitError      # HTTP 429
    └── ValidationError         # client-side required-field check (.method / .fields)
"""

from __future__ import annotations


class NovadaError(Exception):
    """Base class for all errors raised by the Novada SDK."""


class APIError(NovadaError):
    """A failed Novada API call.

    Raised in two situations:

    * the HTTP response status was outside the 2xx range, in which case
      ``http_status`` is set and ``code`` is 0; or
    * the HTTP status was 2xx but the response envelope carried a non-zero
      business code, in which case both ``http_status`` and ``code`` are set.

    Only ``code == 0`` is success, so an HTTP 200 alone never means success.
    """

    def __init__(self, message: str, *, http_status: int = 0, code: int = 0) -> None:
        super().__init__(message)
        #: HTTP status code of the response.
        self.http_status = http_status
        #: Novada business code from the response envelope (0 means success; it
        #: is 0 when the failure occurred at the HTTP layer).
        self.code = code
        #: Human-readable error message (the envelope "msg" field when available).
        self.message = message

    def __str__(self) -> str:
        if self.code != 0:
            return f"novada: api error (code={self.code}, http={self.http_status}): {self.message}"
        return f"novada: http error (status={self.http_status}): {self.message}"


class AuthError(APIError):
    """An authentication or authorization failure (HTTP 401 or 403)."""


class RateLimitError(APIError):
    """A rate-limiting failure (HTTP 429)."""


class ValidationError(NovadaError):
    """One or more required parameters were missing, detected client-side
    before any request was sent."""

    def __init__(self, method: str, fields: list[str]) -> None:
        self.method = method
        self.fields = fields
        super().__init__(f"{method}: missing required field(s): {', '.join(fields)}")


def is_auth_error(err: BaseException) -> bool:
    """Report whether *err* is an :class:`AuthError` (HTTP 401/403).

    Provided for parity with the Go SDK's ``IsAuthError``; ``isinstance`` works
    just as well.
    """
    return isinstance(err, AuthError)


def is_rate_limited(err: BaseException) -> bool:
    """Report whether *err* is a :class:`RateLimitError` (HTTP 429).

    Provided for parity with the Go SDK's ``IsRateLimited``.
    """
    return isinstance(err, RateLimitError)


def code_of(err: BaseException) -> int | None:
    """Return the Novada business code carried by *err*, or ``None`` when *err*
    is not an :class:`APIError`.

    Provided for parity with the Go SDK's ``CodeOf``.
    """
    if isinstance(err, APIError):
        return err.code
    return None
