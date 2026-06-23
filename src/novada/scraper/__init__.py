"""Scraping endpoints.

Scrape jobs are submitted to a single ``POST /request`` endpoint
(application/x-www-form-urlencoded) and distinguished by their ``scraper_id``;
the host depends on the :class:`~novada.scraper.types.Target`. The query
endpoints (areas, balance, unit price) are regular ``/v1/*`` APIs on the general
host. Reach the sub-services via ``client.scraper``.
"""

from __future__ import annotations

import json

from .._transport import Transport
from ..errors import ValidationError
from ._base import bool_str
from .types import Request, Response, Target


class ScraperService:
    """Entry point for scraping endpoints.

    Sub-services are attached as snake_case attributes mirroring the Go SDK's
    exported fields.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

        # Imported lazily to avoid a circular import: api.py type-checks against
        # ScraperService.
        from .api import APIService
        from .browser import BrowserService
        from .unblocker import UnblockerService
        from .universal import UniversalService

        #: Strongly typed Scraper API scrapers.
        self.api = APIService(self, transport)
        #: Web Unblocker scraping and area queries.
        self.unblocker = UnblockerService(transport)
        #: Shared balance/logs/unit-price queries.
        self.universal = UniversalService(transport)
        #: Browser API area and traffic queries.
        self.browser = BrowserService(transport)

    def do(self, req: Request) -> Response:
        """Submit a generic scrape job.

        Marshals ``req.params`` into ``scraper_params``, URL-encodes the form,
        and routes to the host selected by ``req.target``. The response is
        returned raw because scrape payload formats vary by scraper.
        """
        missing = []
        if not req.scraper_name or not req.scraper_name.strip():
            missing.append("scraper_name")
        if not req.scraper_id or not req.scraper_id.strip():
            missing.append("scraper_id")
        if not req.params:
            missing.append("scraper_params")
        if missing:
            raise ValidationError("Scraper.do", missing)

        # Compact separators match Go's encoding/json output (no spaces).
        encoded_params = json.dumps(req.params, separators=(",", ":"))

        values: dict[str, str] = {
            "scraper_name": req.scraper_name,
            "scraper_id": req.scraper_id,
            "scraper_params": encoded_params,
        }
        if req.return_errors:
            values["scraper_errors"] = bool_str(True)

        host = (
            self._t.web_unblocker_url if req.target == Target.WEB_UNBLOCKER else self._t.scraper_url
        )
        body = self._t.do_form_urlencoded_raw(host, "/request", values)
        return Response(raw=body.decode("utf-8"))


__all__ = ["ScraperService", "Request", "Response", "Target"]
