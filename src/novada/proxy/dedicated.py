"""Dedicated datacenter proxies (the ``/v1/static/*`` endpoints). Shares the
StaticIP/RegionList response types and helper implementations with the static
ISP service."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator
from .static import export_fields, list_static, renew_setting_static, renew_static
from .types import (
    ExportStaticParams,
    ListStaticParams,
    OpenDedicatedDCParams,
    RegionList,
    RenewSettingParams,
    RenewStaticParams,
    StaticIPList,
)


class DedicatedDCService:
    """Dedicated datacenter proxies (the ``/v1/static/*`` endpoints)."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def open(self, params: OpenDedicatedDCParams) -> None:
        """Purchase dedicated datacenter IPs (``POST /v1/static/open``). All
        fields are required."""
        v = Validator("DedicatedDC.open")
        v.require_str("region", params.region)
        v.require_str("duration", params.duration)
        v.require_nonzero("num", params.num)
        v.check()
        f = Form()
        f.req_str("region", params.region)
        f.req_str("duration", params.duration)
        f.req_int("num", params.num)
        self._t.do_multipart(self._t.base_url, "/v1/static/open", f.fields)

    def list(self, params: ListStaticParams) -> StaticIPList:
        """Return purchased dedicated datacenter IPs (``POST /v1/static/list``)."""
        return list_static(self._t, "/v1/static/list", params)

    def export(self, params: ExportStaticParams) -> bytes:
        """Return the dedicated datacenter IP list as a file stream
        (``POST /v1/static/export``). The bytes are typically CSV and are
        returned without envelope decoding."""
        return self._t.do_multipart_raw(
            self._t.base_url, "/v1/static/export", export_fields(params)
        )

    def region(self) -> RegionList:
        """List the available dedicated datacenter regions
        (``POST /v1/static/region``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/static/region", {})
        return decode(data, RegionList) if data is not None else RegionList()

    def renew(self, params: RenewStaticParams) -> None:
        """Renew dedicated datacenter IPs (``POST /v1/static/renew``)."""
        renew_static(self._t, "DedicatedDC.renew", "/v1/static/renew", params)

    def renew_setting(self, params: RenewSettingParams) -> None:
        """Update dedicated datacenter auto-renewal settings
        (``POST /v1/static/renew_setting``)."""
        renew_setting_static(
            self._t,
            "DedicatedDC.renew_setting",
            "/v1/static/renew_setting",
            "static",
            params,
        )
