"""Static ISP proxies (the ``/v1/static_house/*`` endpoints), plus the shared
implementations reused by the dedicated datacenter service."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator, default_page
from .types import (
    ExportStaticParams,
    ListStaticParams,
    OpenStaticISPParams,
    RegionList,
    RenewSettingParams,
    RenewStaticParams,
    StaticIPList,
)


def list_static(transport: Transport, path: str, p: ListStaticParams) -> StaticIPList:
    """Shared implementation of the static IP list endpoints."""
    page, limit = default_page(p.page, p.limit)
    f = Form()
    f.opt_str("status", p.status)
    f.opt_str("region", p.region)
    f.opt_str("key_word", p.key_word)
    f.opt_int_ptr("is_auto_renew", p.is_auto_renew)
    f.req_int("page", page)
    f.req_int("limit", limit)
    data = transport.do_multipart(transport.base_url, path, f.fields)
    return decode(data, StaticIPList) if data is not None else StaticIPList()


def export_fields(p: ExportStaticParams) -> dict[str, str]:
    """Build the multipart fields for the static IP export endpoints."""
    f = Form()
    f.opt_str("status", p.status)
    f.opt_str("region", p.region)
    f.opt_str("key_word", p.key_word)
    f.opt_int_ptr("is_auto_renew", p.is_auto_renew)
    return f.fields


def renew_static(transport: Transport, method: str, path: str, p: RenewStaticParams) -> None:
    """Shared implementation of the static IP renew endpoints."""
    v = Validator(method)
    v.require_str("renew_ip_list", p.ips)
    v.require_str("duration", p.duration)
    v.check()
    f = Form()
    f.req_str("renew_ip_list", p.ips)
    f.req_str("duration", p.duration)
    transport.do_multipart(transport.base_url, path, f.fields)


def renew_setting_static(
    transport: Transport, method: str, path: str, type_val: str, p: RenewSettingParams
) -> None:
    """Shared implementation of the static IP auto-renewal setting endpoints."""
    v = Validator(method)
    v.require_str("ids", p.ids)
    v.require_str("package_type", p.package_type)
    v.require_nonzero("status", p.status)
    v.require_nonzero("renew_type", p.renew_type)
    v.check()
    f = Form()
    f.req_str("type", type_val)
    f.req_str("ids", p.ids)
    f.req_str("package_type", p.package_type)
    f.req_int("status", p.status)
    f.req_int("renew_type", p.renew_type)
    transport.do_multipart(transport.base_url, path, f.fields)


class StaticISPService:
    """Static ISP proxies (the ``/v1/static_house/*`` endpoints)."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def open(self, params: OpenStaticISPParams) -> None:
        """Purchase static ISP IPs (``POST /v1/static_house/open``). All fields
        are required."""
        v = Validator("StaticISP.open")
        v.require_str("ip_type", params.ip_type)
        v.require_str("region", params.region)
        v.require_str("duration", params.duration)
        v.require_nonzero("num", params.num)
        v.check()
        f = Form()
        f.req_str("ip_type", params.ip_type)
        f.req_str("region", params.region)
        f.req_str("duration", params.duration)
        f.req_int("num", params.num)
        self._t.do_multipart(self._t.base_url, "/v1/static_house/open", f.fields)

    def list(self, params: ListStaticParams) -> StaticIPList:
        """Return purchased static ISP IPs (``POST /v1/static_house/list``)."""
        return list_static(self._t, "/v1/static_house/list", params)

    def export(self, params: ExportStaticParams) -> bytes:
        """Return the static ISP IP list as a file stream
        (``POST /v1/static_house/export``). The bytes are typically CSV and are
        returned without envelope decoding."""
        return self._t.do_multipart_raw(
            self._t.base_url, "/v1/static_house/export", export_fields(params)
        )

    def region(self, isp_type: str) -> RegionList:
        """List the available static ISP regions (``POST /v1/static_house/region``).
        *isp_type* is required: ``"isp-resi"`` = static residential,
        ``"isp-resi-hq"`` = premium."""
        v = Validator("StaticISP.region")
        v.require_str("isp_type", isp_type)
        v.check()
        data = self._t.do_multipart(
            self._t.base_url, "/v1/static_house/region", {"isp_type": isp_type}
        )
        return decode(data, RegionList) if data is not None else RegionList()

    def renew(self, params: RenewStaticParams) -> None:
        """Renew static ISP IPs (``POST /v1/static_house/renew``)."""
        renew_static(self._t, "StaticISP.renew", "/v1/static_house/renew", params)

    def renew_setting(self, params: RenewSettingParams) -> None:
        """Update static ISP auto-renewal settings
        (``POST /v1/static_house/renew_setting``)."""
        renew_setting_static(
            self._t,
            "StaticISP.renew_setting",
            "/v1/static_house/renew_setting",
            "static_house",
            params,
        )
