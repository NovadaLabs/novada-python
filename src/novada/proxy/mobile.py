"""Mobile proxy areas and traffic (the ``/v1/proxy/mobile_area`` and
``/v1/mobile_flow/*`` endpoints)."""

from __future__ import annotations

from typing import Any

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator
from .types import FlowConsumeLogList, MobileBalance, MobileUseParams


class MobileService:
    """Mobile proxy areas and traffic."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def countries(self) -> Any:
        """List mobile proxy countries (``POST /v1/proxy/mobile_area``). The API
        does not document a fixed response shape, so the raw decoded data
        payload is returned for the caller to inspect."""
        return self._t.do_multipart(self._t.base_url, "/v1/proxy/mobile_area", {})

    def balance(self) -> MobileBalance:
        """Return the remaining mobile traffic
        (``POST /v1/mobile_flow/mobile_flow_balance``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/mobile_flow/mobile_flow_balance", {})
        return decode(data, MobileBalance) if data is not None else MobileBalance()

    def consume_log(self, params: MobileUseParams) -> FlowConsumeLogList:
        """Return the main account's mobile traffic consumption
        (``POST /v1/mobile_flow/mobile_flow_use``). Start, end and granularity
        are required."""
        v = Validator("Mobile.consume_log")
        v.require_str("start_time", params.start)
        v.require_str("end_time", params.end)
        v.require_str("day_or_hour", params.granularity)
        v.check()
        f = Form()
        f.req_str("start_time", params.start)
        f.req_str("end_time", params.end)
        f.req_str("day_or_hour", params.granularity)
        data = self._t.do_multipart(self._t.base_url, "/v1/mobile_flow/mobile_flow_use", f.fields)
        return decode(data, FlowConsumeLogList) if data is not None else FlowConsumeLogList()
