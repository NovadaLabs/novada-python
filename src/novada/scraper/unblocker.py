"""Web Unblocker scraping plus its area queries.

The area queries are ``/v1/*`` APIs on the general host; the scrape itself uses
:meth:`UnblockerService.scrape`, which routes to the Web Unblocker host.
"""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ..errors import ValidationError
from ._base import require_field, set_opt_bool, set_opt_str
from .types import Areas, CityList, ISPList, StateList, UnblockerParams, UnblockerResult


class UnblockerService:
    """Web Unblocker scraping and area queries."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def scrape(self, params: UnblockerParams) -> UnblockerResult:
        """Submit a Web Unblocker scrape job (``POST /request`` on the Web
        Unblocker host) and decode the structured result. target_url is
        required."""
        require_field("Unblocker.scrape", "target_url", params.target_url)

        fmt = params.response_format.strip() or "html"
        values: dict[str, str] = {
            "target_url": params.target_url,
            "response_format": fmt,
        }
        set_opt_bool(values, "js_render", params.js_render)
        set_opt_str(values, "headers", params.headers)
        set_opt_str(values, "cookies", params.cookies)
        set_opt_str(values, "country", params.country)
        if params.wait_ms > 0:
            values["wait_ms"] = str(params.wait_ms)
        set_opt_str(values, "wait_selector", params.wait_selector)
        set_opt_bool(values, "follow_redirects", params.follow_redirects)
        set_opt_bool(values, "block_resources", params.block_resources)
        set_opt_bool(values, "clear", params.clear)
        if params.auto_runs is not None:
            values["auto_runs"] = str(params.auto_runs)

        data = self._t.do_form_urlencoded(self._t.web_unblocker_url, "/request", values)
        return decode(data, UnblockerResult) if data is not None else UnblockerResult()

    def countries(self) -> Areas:
        """List Web Unblocker countries (``POST /v1/proxy/unblocker_area``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/proxy/unblocker_area", {})
        return decode(data, Areas) if data is not None else Areas()

    def states(self, code: str) -> StateList:
        """List the states of a country
        (``POST /v1/proxy/unblocker_area_by_country``). *code* is required."""
        require_field("Unblocker.states", "code", code)
        data = self._t.do_multipart(
            self._t.base_url, "/v1/proxy/unblocker_area_by_country", {"code": code}
        )
        return decode(data, StateList) if data is not None else StateList()

    def cities(self, code: str, region: str) -> CityList:
        """List the cities of a region (``POST /v1/proxy/unblocker_city_by_area``).
        Both code and region are required."""
        missing = []
        if not code or not code.strip():
            missing.append("code")
        if not region or not region.strip():
            missing.append("region")
        if missing:
            raise ValidationError("Unblocker.cities", missing)
        data = self._t.do_multipart(
            self._t.base_url,
            "/v1/proxy/unblocker_city_by_area",
            {"code": code, "region": region},
        )
        return decode(data, CityList) if data is not None else CityList()

    def isps(self, code: str) -> ISPList:
        """List the carriers of a country (``POST /v1/proxy/unblocker_city_isp``).
        *code* is required."""
        require_field("Unblocker.isps", "code", code)
        data = self._t.do_multipart(
            self._t.base_url, "/v1/proxy/unblocker_city_isp", {"code": code}
        )
        return decode(data, ISPList) if data is not None else ISPList()
