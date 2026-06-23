"""Generic JSON-to-dataclass decoding.

The Go SDK relies on ``encoding/json`` to unmarshal each endpoint's ``data``
payload into a typed struct, ignoring unknown fields. This module provides the
Python equivalent: :func:`decode` maps a JSON value (already parsed into
dict/list/scalar) onto a target type — recursing through dataclasses, lists,
dicts and ``Optional`` — while tolerating missing keys (they fall back to the
field default) and ignoring unknown keys (forward compatibility).

Return dataclasses name their fields exactly as the JSON snake_case keys, so no
field-tag mapping is needed. A field typed ``Any`` is passed through verbatim,
which mirrors Go's ``json.RawMessage`` (e.g. the raw Google result array).
"""

from __future__ import annotations

import dataclasses
import typing
from typing import Any, TypeVar, Union, get_args, get_origin

T = TypeVar("T")

# Cache resolved type hints per dataclass; resolving forward references via
# get_type_hints is comparatively expensive and the set of types is fixed.
_hints_cache: dict[type, dict[str, Any]] = {}


def _hints(tp: type) -> dict[str, Any]:
    cached = _hints_cache.get(tp)
    if cached is None:
        cached = typing.get_type_hints(tp)
        _hints_cache[tp] = cached
    return cached


def decode(data: Any, tp: Any) -> Any:
    """Decode *data* (a parsed JSON value) into the shape described by *tp*."""
    if data is None:
        return None
    if tp is Any or tp is object:
        return data

    origin = get_origin(tp)

    if origin is Union:
        # Optional[X] / Union[X, None]: decode as the first non-None arg.
        args = [a for a in get_args(tp) if a is not type(None)]
        if len(args) == 1:
            return decode(data, args[0])
        return data

    if origin is list:
        list_args = get_args(tp)
        elem = list_args[0] if list_args else Any
        return [decode(item, elem) for item in data]

    if origin is dict:
        dict_args = get_args(tp)
        val_t = dict_args[1] if len(dict_args) == 2 else Any
        return {key: decode(val, val_t) for key, val in data.items()}

    if dataclasses.is_dataclass(tp) and isinstance(data, dict):
        cls = typing.cast("type[Any]", tp)
        hints = _hints(cls)
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):
            if f.name in data:
                kwargs[f.name] = decode(data[f.name], hints[f.name])
        return cls(**kwargs)

    # Scalars (int, float, str, bool) and anything else: return as-is.
    return data


def decode_optional(data: Any, tp: type[T]) -> T | None:
    """Decode *data* into *tp*, returning ``None`` when *data* is ``None``."""
    if data is None:
        return None
    return typing.cast(T, decode(data, tp))
