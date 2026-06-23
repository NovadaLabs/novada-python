"""Strongly typed Scraper API scrapers (Target = SCRAPER_API)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .._decode import decode
from .._transport import Transport
from ._base import bool_str, require_field, set_opt_bool, set_opt_str
from .types import (
    GoogleSearchParams,
    GoogleSearchResult,
    Request,
    Response,
    Target,
    YouTubeVideoParams,
)

if TYPE_CHECKING:
    from . import ScraperService


class YouTubeService:
    """YouTube scrapers (scraper_name ``"youtube.com"``)."""

    def __init__(self, svc: ScraperService) -> None:
        self._svc = svc

    def video_post(self, params: YouTubeVideoParams) -> Response:
        """Scrape a YouTube video post (scraper_id
        ``"youtube_video-post_explore"``). A thin wrapper over
        :meth:`ScraperService.do`."""
        return self._svc.do(
            Request(
                target=Target.SCRAPER_API,
                scraper_name="youtube.com",
                scraper_id="youtube_video-post_explore",
                params=[{"url": params.url}],
            )
        )


class GoogleService:
    """Google scrapers (scraper_name ``"google.com"``).

    Unlike the generic :meth:`ScraperService.do` path, Google scrapers send
    their parameters as flat form fields (not a ``scraper_params`` JSON array),
    so this service builds the form directly and decodes the envelope into a
    structured result.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def search(self, params: GoogleSearchParams) -> GoogleSearchResult:
        """Scrape Google search results (scraper_id ``"google_search"``) and
        decode the structured result. Query is required."""
        require_field("Google.search", "q", params.query)

        values: dict[str, str] = {
            "scraper_name": "google.com",
            "scraper_id": "google_search",
            "q": params.query,
            "json": "0" if params.html else "1",
        }
        set_opt_str(values, "device", params.device)
        set_opt_bool(values, "render_js", params.render_js)
        set_opt_bool(values, "no_cache", params.no_cache)
        set_opt_bool(values, "ai_overview", params.ai_overview)
        set_opt_str(values, "domain", params.domain)
        set_opt_str(values, "country", params.country)
        set_opt_str(values, "hl", params.hl)
        if params.return_errors:
            values["scraper_errors"] = bool_str(True)

        data = self._t.do_form_urlencoded(self._t.scraper_url, "/request", values)
        return decode(data, GoogleSearchResult) if data is not None else GoogleSearchResult()


class APIService:
    """Groups the strongly typed Scraper API scrapers."""

    def __init__(self, svc: ScraperService, transport: Transport) -> None:
        #: YouTube scrapers.
        self.youtube = YouTubeService(svc)
        #: Google scrapers (SerpApi).
        self.google = GoogleService(transport)
