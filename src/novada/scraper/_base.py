"""Small helpers shared by the scraper services."""

from __future__ import annotations

from typing import Optional

from ..errors import ValidationError


def require_field(method: str, name: str, val: str) -> None:
    """Raise :class:`~novada.errors.ValidationError` when *val* is empty."""
    if val is None or val.strip() == "":
        raise ValidationError(method, [name])


def bool_str(val: bool) -> str:
    """Format a bool the way Go's strconv.FormatBool does: ``"true"``/``"false"``."""
    return "true" if val else "false"


def set_opt_bool(values: dict[str, str], key: str, val: Optional[bool]) -> None:
    """Set *key* to the lowercased bool when *val* is not None."""
    if val is not None:
        values[key] = bool_str(val)


def set_opt_str(values: dict[str, str], key: str, val: str) -> None:
    """Set *key* when *val* is non-empty."""
    if val != "":
        values[key] = val
