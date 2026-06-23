"""Shared helpers for the proxy services: a multipart form builder, a
required-field validator, and the pagination default.

These mirror the Go SDK's ``form`` map helpers, ``validator`` and
``defaultPage`` so each service method reads the same way.
"""

from __future__ import annotations

from typing import Optional

from ..errors import ValidationError


class Form:
    """A builder for multipart field maps.

    Optional setters drop empty/zero values; required setters always write so
    the server-side required check is satisfied. The accumulated fields are read
    back via :attr:`fields`.
    """

    def __init__(self) -> None:
        self.fields: dict[str, str] = {}

    def req_str(self, key: str, val: str) -> None:
        self.fields[key] = val

    def opt_str(self, key: str, val: str) -> None:
        if val != "":
            self.fields[key] = val

    def req_int(self, key: str, val: int) -> None:
        self.fields[key] = str(val)

    def opt_int(self, key: str, val: int) -> None:
        if val != 0:
            self.fields[key] = str(val)

    def opt_int_ptr(self, key: str, val: Optional[int]) -> None:
        if val is not None:
            self.fields[key] = str(val)


class Validator:
    """Accumulates missing required fields and raises a
    :class:`~novada.errors.ValidationError`."""

    def __init__(self, method: str) -> None:
        self.method = method
        self.missing: list[str] = []

    def require_str(self, name: str, val: str) -> None:
        if val is None or val.strip() == "":
            self.missing.append(name)

    def require_nonzero(self, name: str, val: int) -> None:
        if val == 0:
            self.missing.append(name)

    def check(self) -> None:
        """Raise if any required field was missing."""
        if self.missing:
            raise ValidationError(self.method, self.missing)


def default_page(page: int, limit: int) -> tuple[int, int]:
    """Apply the API's pagination defaults (page=1, limit=10) when the caller
    leaves them at zero."""
    return (page or 1, limit or 10)
