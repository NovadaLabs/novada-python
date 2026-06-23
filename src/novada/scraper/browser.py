"""Browser API area and traffic queries on the general host."""

from __future__ import annotations

from typing import Any

from .._decode import decode
from .._transport import Transport
from ..errors import ValidationError
from .types import BrowserFlowUseList


class BrowserService:
    """The Browser API area and traffic queries."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def countries(self) -> Any:
        """List Browser API countries (``POST /v1/proxy/browser_area``). The API
        does not document a fixed response shape, so the raw decoded data
        payload is returned."""
        return self._t.do_multipart(self._t.base_url, "/v1/proxy/browser_area", {})

    def flow_use(self, start: str, end: str) -> BrowserFlowUseList:
        """Return the main account's Browser API traffic consumption over a time
        range (``POST /v1/browser_flow/browser_flow_use``). Both bounds use the
        ``"2006-01-02 15:04:05"`` layout and are required."""
        missing = []
        if not start or not start.strip():
            missing.append("start_time")
        if not end or not end.strip():
            missing.append("end_time")
        if missing:
            raise ValidationError("Browser.flow_use", missing)
        data = self._t.do_multipart(
            self._t.base_url,
            "/v1/browser_flow/browser_flow_use",
            {"start_time": start, "end_time": end},
        )
        return decode(data, BrowserFlowUseList) if data is not None else BrowserFlowUseList()
