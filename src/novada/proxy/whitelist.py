"""IP whitelist management via the ``/v1/white_list/*`` endpoints."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator
from .types import (
    AddWhitelistParams,
    DeleteWhitelistParams,
    ListWhitelistParams,
    RemarkWhitelistParams,
    WhitelistList,
)


class WhitelistService:
    """Manages IP whitelists via the ``/v1/white_list/*`` endpoints."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def add(self, params: AddWhitelistParams) -> None:
        """Add an IP to a product's whitelist (``POST /v1/white_list/add``).
        Product and IP are required. Valid products: RESIDENTIAL, STATIC_ISP,
        UNLIMITED."""
        v = Validator("Whitelist.add")
        v.require_nonzero("product", int(params.product))
        v.require_str("ip", params.ip)
        v.check()

        f = Form()
        f.req_int("product", int(params.product))
        f.req_str("ip", params.ip)
        f.opt_str("remark", params.remark)

        self._t.do_multipart(self._t.base_url, "/v1/white_list/add", f.fields)

    def list(self, params: ListWhitelistParams) -> WhitelistList:
        """Return whitelisted IPs for a product (``POST /v1/white_list/list``).
        Product is required; the remaining fields are optional filters."""
        v = Validator("Whitelist.list")
        v.require_nonzero("product", int(params.product))
        v.check()

        f = Form()
        f.req_int("product", int(params.product))
        f.opt_str("ip", params.ip)
        f.opt_str("start_time", params.start_time)
        f.opt_str("end_time", params.end_time)
        f.opt_int_ptr("lock", params.lock)

        data = self._t.do_multipart(self._t.base_url, "/v1/white_list/list", f.fields)
        return decode(data, WhitelistList) if data is not None else WhitelistList()

    def delete(self, params: DeleteWhitelistParams) -> None:
        """Remove one or more IPs from a product's whitelist
        (``POST /v1/white_list/del``). Product and IPs are required; pass
        multiple IPs comma-separated."""
        v = Validator("Whitelist.delete")
        v.require_nonzero("product", int(params.product))
        v.require_str("ips", params.ips)
        v.check()

        f = Form()
        f.req_int("product", int(params.product))
        f.req_str("ips", params.ips)

        self._t.do_multipart(self._t.base_url, "/v1/white_list/del", f.fields)

    def remark(self, params: RemarkWhitelistParams) -> None:
        """Update the remark of a whitelist entry
        (``POST /v1/white_list/remark``). Product and ID are required."""
        v = Validator("Whitelist.remark")
        v.require_nonzero("product", int(params.product))
        v.require_str("id", params.id)
        v.check()

        f = Form()
        f.req_int("product", int(params.product))
        f.req_str("id", params.id)
        f.opt_str("remark", params.remark)

        self._t.do_multipart(self._t.base_url, "/v1/white_list/remark", f.fields)
