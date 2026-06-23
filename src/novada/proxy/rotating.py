"""Rotating ISP and rotating datacenter proxy areas and traffic."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from .residential import consume_log
from .types import DCArea, FlowBalance, FlowConsumeLogList, ISPArea, TimeRange


class RotatingISPService:
    """Rotating ISP proxy areas and traffic (the ``/v1/proxy/isp_data_area`` and
    ``/v1/isp_flow/*`` endpoints)."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def countries(self) -> ISPArea:
        """List rotating ISP countries (``POST /v1/proxy/isp_data_area``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/isp_data_area", {})
        return decode(data, ISPArea) if data is not None else ISPArea()

    def balance(self) -> FlowBalance:
        """Return the remaining rotating ISP traffic
        (``POST /v1/isp_flow/balance``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/isp_flow/balance", {})
        return decode(data, FlowBalance) if data is not None else FlowBalance()

    def consume_log(self, tr: TimeRange) -> FlowConsumeLogList:
        """Return the main account's rotating ISP traffic consumption over a time
        range (``POST /v1/isp_flow/consume_log``)."""
        return consume_log(self._t, "RotatingISP.consume_log", "/v1/isp_flow/consume_log", tr)


class RotatingDCService:
    """Rotating datacenter proxy areas and traffic (the
    ``/v1/proxy/dynamic_data_area`` and ``/v1/dc_flow/*`` endpoints)."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def countries(self) -> DCArea:
        """List rotating datacenter countries
        (``POST /v1/proxy/dynamic_data_area``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/dynamic_data_area", {})
        return decode(data, DCArea) if data is not None else DCArea()

    def balance(self) -> FlowBalance:
        """Return the remaining rotating datacenter traffic
        (``POST /v1/dc_flow/balance``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/dc_flow/balance", {})
        return decode(data, FlowBalance) if data is not None else FlowBalance()

    def consume_log(self, tr: TimeRange) -> FlowConsumeLogList:
        """Return the main account's rotating datacenter traffic consumption over
        a time range (``POST /v1/dc_flow/consume_log``)."""
        return consume_log(self._t, "RotatingDC.consume_log", "/v1/dc_flow/consume_log", tr)
