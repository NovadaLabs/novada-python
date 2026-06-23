"""Decoding of the uniform Novada response envelope.

Every ``/v1`` management endpoint returns the same wrapper::

    {"code": 0, "data": {...}, "msg": "success", "timestamp": 1732084616}

A ``code`` of 0 indicates success; any other value is a business-level failure.
Callers must never treat HTTP 200 as success on its own — the business code is
authoritative.
"""

from __future__ import annotations

import json
from typing import Any

from .errors import APIError


def http_error_message(body: bytes, status_reason: str) -> str:
    """Extract a human-readable message for a non-2xx response.

    Prefers the envelope ``msg`` field when the body parses, otherwise falls
    back to the supplied HTTP status reason phrase.
    """
    try:
        env = json.loads(body)
    except (ValueError, TypeError):
        return status_reason
    if isinstance(env, dict):
        msg = env.get("msg")
        if isinstance(msg, str) and msg:
            return msg
    return status_reason


def decode_envelope(http_status: int, body: bytes) -> Any:
    """Parse a 2xx management response body, enforce the business code, and
    return the inner ``data`` payload (already JSON-decoded).

    Raises :class:`APIError` when the body does not parse or the envelope
    carries a non-zero ``code``. Returns ``None`` when there is no ``data``.
    """
    try:
        env = json.loads(body)
    except (ValueError, TypeError) as exc:
        raise APIError(f"invalid response body: {exc}", http_status=http_status) from exc
    if not isinstance(env, dict):
        raise APIError("invalid response body: expected a JSON object", http_status=http_status)

    code = env.get("code", 0)
    if code != 0:
        raise APIError(env.get("msg", ""), http_status=http_status, code=int(code))

    return env.get("data")
