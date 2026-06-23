"""Blocked-domain management (the ``/v1/prohibit_domain/*`` endpoints)."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator
from .types import DeleteProhibitParams, ProhibitDomainList


class ProhibitDomainService:
    """Manages the blocked-domain list."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def add(self, address: str) -> None:
        """Add a blocked domain (``POST /v1/prohibit_domain/add``). *address* is
        required."""
        v = Validator("ProhibitDomain.add")
        v.require_str("address", address)
        v.check()
        self._t.do_multipart(self._t.base_url, "/v1/prohibit_domain/add", {"address": address})

    def list(self) -> ProhibitDomainList:
        """Return the blocked-domain list (``POST /v1/prohibit_domain/list``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/prohibit_domain/list", {})
        return decode(data, ProhibitDomainList) if data is not None else ProhibitDomainList()

    def delete(self, params: DeleteProhibitParams) -> None:
        """Remove blocked domains (``POST /v1/prohibit_domain/del``). Set
        ``all`` to delete every entry, otherwise ``id`` is required."""
        v = Validator("ProhibitDomain.delete")
        if not params.all:
            v.require_str("id", params.id)
        v.check()
        f = Form()
        f.req_str("is_all", "1" if params.all else "2")
        f.opt_str("id", params.id)
        self._t.do_multipart(self._t.base_url, "/v1/prohibit_domain/del", f.fields)
