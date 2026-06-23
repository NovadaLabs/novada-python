"""Residential proxy area listings and traffic (the ``/v1/proxy/*`` and
``/v1/residential_flow/*`` endpoints)."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator
from .types import (
    CityParams,
    FlowBalance,
    FlowConsumeLogList,
    ResidentialAreas,
    ResidentialCityList,
    ResidentialISPList,
    ResidentialStateList,
    TimeRange,
)


def consume_log(transport: Transport, method: str, path: str, tr: TimeRange) -> FlowConsumeLogList:
    """Shared implementation for the residential/ISP/DC traffic-consumption
    endpoints, which share the same request and response shapes."""
    v = Validator(method)
    v.require_str("start_time", tr.start)
    v.require_str("end_time", tr.end)
    v.check()
    f = Form()
    f.req_str("start_time", tr.start)
    f.req_str("end_time", tr.end)
    data = transport.do_multipart(transport.base_url, path, f.fields)
    return decode(data, FlowConsumeLogList) if data is not None else FlowConsumeLogList()


class ResidentialService:
    """Residential proxy areas and traffic."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def countries(self) -> ResidentialAreas:
        """List residential proxy countries grouped by continent
        (``POST /v1/proxy/domestic_dynamic_area``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/domestic_dynamic_area", {})
        return decode(data, ResidentialAreas) if data is not None else ResidentialAreas()

    def states(self, code: str) -> ResidentialStateList:
        """List the states/regions of a country (``POST /v1/proxy/city_by_code``).
        *code* is the country code, e.g. ``"us"``."""
        v = Validator("Residential.states")
        v.require_str("code", code)
        v.check()
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/city_by_code", {"code": code})
        return decode(data, ResidentialStateList) if data is not None else ResidentialStateList()

    def cities(self, params: CityParams) -> ResidentialCityList:
        """List the cities of a country region (``POST /v1/proxy/region_by_city``).
        Both code and region are required."""
        v = Validator("Residential.cities")
        v.require_str("code", params.code)
        v.require_str("region", params.region)
        v.check()
        f = {"code": params.code, "region": params.region}
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/region_by_city", f)
        return decode(data, ResidentialCityList) if data is not None else ResidentialCityList()

    def isps(self, code: str) -> ResidentialISPList:
        """List the ISPs available in a country (``POST /v1/proxy/city_isp``).
        *code* is the country code, e.g. ``"us"``."""
        v = Validator("Residential.isps")
        v.require_str("code", code)
        v.check()
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/city_isp", {"code": code})
        return decode(data, ResidentialISPList) if data is not None else ResidentialISPList()

    def balance(self) -> FlowBalance:
        """Return the remaining residential traffic
        (``POST /v1/residential_flow/balance``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/residential_flow/balance", {})
        return decode(data, FlowBalance) if data is not None else FlowBalance()

    def consume_log(self, tr: TimeRange) -> FlowConsumeLogList:
        """Return the main account's residential traffic consumption over a time
        range (``POST /v1/residential_flow/consume_log``)."""
        return consume_log(
            self._t, "Residential.consume_log", "/v1/residential_flow/consume_log", tr
        )
