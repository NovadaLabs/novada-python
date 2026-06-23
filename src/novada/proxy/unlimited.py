"""Unlimited proxy servers (the ``/v1/unlimited/*`` endpoints)."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, default_page
from .types import UnlimitedHostList


class UnlimitedService:
    """Unlimited proxy servers."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def hosts(self, page: int = 0, limit: int = 0) -> UnlimitedHostList:
        """List unlimited proxy servers (``POST /v1/unlimited/host_list``). Page
        and limit default to 1 and 10 when left at zero."""
        page, limit = default_page(page, limit)
        f = Form()
        f.req_int("page", page)
        f.req_int("limit", limit)
        data = self._t.do_multipart(self._t.base_url, "/v1/unlimited/host_list", f.fields)
        return decode(data, UnlimitedHostList) if data is not None else UnlimitedHostList()
