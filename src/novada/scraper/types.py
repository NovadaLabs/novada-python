"""Parameter and response dataclasses for the scraper services, plus the
:class:`Target` enum.

As with the proxy types, parameter dataclasses put required fields first and
omit unset optional fields from the request; response dataclasses name their
fields exactly as the JSON snake_case keys and default every field. Fields that
mirror Go's ``json.RawMessage`` (the raw Google result array) are typed ``Any``
and passed through verbatim.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


class Target(IntEnum):
    """Selects which host a scrape ``/request`` is sent to."""

    #: Route to the Scraper API host (``scraper.novada.com``).
    SCRAPER_API = 0
    #: Route to the Web Unblocker host (``webunlocker.novada.com``).
    WEB_UNBLOCKER = 1


@dataclass
class Request:
    """A generic scrape job. It covers every ``scraper_id``; the strongly typed
    helpers under ``scraper.api`` build a Request for known scrapers."""

    #: The site name, e.g. ``"youtube.com"``. Required.
    scraper_name: str
    #: Identifies the scrape operation, e.g. ``"youtube_video-post_explore"``.
    #: Required.
    scraper_id: str
    #: JSON array of per-item parameters; marshaled into the ``scraper_params``
    #: form field. Required (at least one item).
    params: list[dict[str, Any]]
    #: Selects the host (Scraper API or Web Unblocker).
    target: Target = Target.SCRAPER_API
    #: Sets ``scraper_errors=true`` so the response includes scrape errors.
    return_errors: bool = False


@dataclass
class Response:
    """A raw scrape result. The body format depends on the scraper (JSON, CSV or
    XLSX), so it is returned verbatim."""

    #: The unparsed response body.
    raw: str


# --- YouTube ---------------------------------------------------------------


@dataclass
class YouTubeVideoParams:
    """Parameters for ``scraper.api.youtube.video_post``."""

    #: The YouTube video URL. Required.
    url: str


# --- Google ----------------------------------------------------------------


@dataclass
class GoogleSearchParams:
    """Configures a Google Search scrape (scraper_id ``"google_search"``). Query
    is required; optional fields are sent only when set."""

    #: The search query or URL. Required (``q``).
    query: str
    #: Emulates a device type: ``"desktop"``, ``"tablet"`` or ``"mobile"``.
    device: str = ""
    #: Requests HTML output (``json=0``) instead of the default JSON output
    #: (``json=1``).
    html: bool = False
    #: Enables JavaScript rendering (``render_js``).
    render_js: Optional[bool] = None
    #: Skips the cache and forces a real-time request (``no_cache``).
    no_cache: Optional[bool] = None
    #: Fetches the AI Overview block (``ai_overview``).
    ai_overview: Optional[bool] = None
    #: The Google domain to crawl, e.g. ``"google.com"``.
    domain: str = ""
    #: Two-letter country/region code (``gl``); server default ``"us"``.
    country: str = ""
    #: Results language (``hl``).
    hl: str = ""
    #: Sets ``scraper_errors=true`` so the response includes scrape errors.
    return_errors: bool = False


@dataclass
class GoogleSearchData:
    """Scraped output of a Google Search. ``json`` is the raw result array (its
    structure is large and varies by query, so it is left unparsed); ``html`` is
    set instead when HTML output was requested."""

    filename: str = ""
    html: Optional[str] = None
    json: Any = None
    task_id: str = ""


@dataclass
class GoogleSearchResult:
    """Decoded ``data`` payload of a Google Search scrape."""

    #: Page-level status (200 on success).
    code: int = 0
    #: Scrape duration in milliseconds.
    cost_time: int = 0
    #: Short status message.
    msg: str = ""
    #: Scraped output.
    data: GoogleSearchData = field(default_factory=GoogleSearchData)


# --- Web Unblocker ---------------------------------------------------------


@dataclass
class UnblockerParams:
    """Configures a Web Unblocker scrape (``POST /request``). Only target_url is
    required; response_format defaults to ``"html"`` when empty, and the
    remaining optional fields are sent only when set."""

    #: The destination address to scrape. Required.
    target_url: str
    #: Output format: ``"html"``, ``"png"`` or ``"html,png"``. Defaults to
    #: ``"html"`` when empty.
    response_format: str = ""
    #: Enables JS rendering to capture dynamically loaded content.
    js_render: Optional[bool] = None
    #: Custom request headers used to access the site.
    headers: str = ""
    #: Custom cookies used to access the site.
    cookies: str = ""
    #: Proxy country/region, e.g. ``"us"``.
    country: str = ""
    #: Maximum page wait time in milliseconds (max 100000). Sent only when
    #: positive.
    wait_ms: int = 0
    #: Waits for a CSS selector to appear in the DOM (max 30s). Takes precedence
    #: over wait_ms when both are set.
    wait_selector: str = ""
    #: Follows redirects from expired URLs to their new target.
    follow_redirects: Optional[bool] = None
    #: Skips loading images, JS files and videos to speed up the crawl.
    block_resources: Optional[bool] = None
    #: Strips unnecessary JS and CSS from the crawl result.
    clear: Optional[bool] = None
    #: Number of automatic retries on proxy failure (0-10, server default 2).
    #: Sent only when non-None.
    auto_runs: Optional[int] = None


@dataclass
class UnblockerResult:
    """Decoded data payload of a Web Unblocker scrape."""

    #: Page-level status (200 on success).
    code: int = 0
    #: Scraped content.
    html: str = ""
    #: Short status message.
    msg: str = ""
    #: Additional error detail when the scrape fails.
    msg_detail: str = ""
    #: Balance consumed by this call.
    use_balance: float = 0.0


# --- Universal queries -----------------------------------------------------


@dataclass
class ScraperBalance:
    """Remaining scraper balance."""

    scraper_balance: float = 0.0


@dataclass
class UsageLog:
    """A single daily scraper/unblocker/browser consumption record."""

    time_label: str = ""
    unlocker_total_cost: float = 0.0
    scraper_total_cost: float = 0.0
    unlocker_used_res: int = 0
    scraper_used_res: int = 0
    scraper_used_flow: int = 0
    browser_total_cost: float = 0.0
    browser_used_flow: int = 0


@dataclass
class UsageLogList:
    """Data payload of ``scraper.universal.logs``."""

    list: list[UsageLog] = field(default_factory=list)


@dataclass
class UnitPrice:
    """A single price tier for a scraper package."""

    package: str = ""
    level: int = 0
    price: float = 0.0
    available: int = 0


@dataclass
class UnitPrices:
    """Data payload of ``scraper.universal.unit``, grouping prices by product."""

    scraper: list[UnitPrice] = field(default_factory=list)
    unblocker: list[UnitPrice] = field(default_factory=list)


# --- Area listings (shared) ------------------------------------------------


@dataclass
class Country:
    """A single country in an area listing."""

    code: str = ""
    continent: int = 0
    ip_num: int = 0
    name: str = ""
    name_en: str = ""
    protocol: int = 0


@dataclass
class ContinentGroup:
    """A continent with its countries."""

    continent: str = ""
    continent_code: int = 0
    list: list[Country] = field(default_factory=list)


@dataclass
class Areas:
    """A country listing grouped by continent, shared by the unblocker area
    endpoint and the residential-style listings."""

    continent: dict[str, str] = field(default_factory=dict)
    country: list[ContinentGroup] = field(default_factory=list)


@dataclass
class State:
    """A state/region within a country."""

    state: str = ""


@dataclass
class StateList:
    """Data payload of the state listings."""

    data: list[State] = field(default_factory=list)


@dataclass
class City:
    """A city within a region."""

    code: str = ""


@dataclass
class CityList:
    """Data payload of the city listings."""

    data: list[City] = field(default_factory=list)


@dataclass
class ISP:
    """A carrier available in a country."""

    asn: str = ""
    show_name: str = ""


@dataclass
class ISPList:
    """Data payload of the ISP listings."""

    list: list[ISP] = field(default_factory=list)


# --- Browser ---------------------------------------------------------------


@dataclass
class BrowserFlowUse:
    """A single Browser API traffic-consumption record."""

    id: int = 0
    uid: int = 0
    balance: int = 0
    all_buy: int = 0
    use: int = 0
    day: int = 0
    expire_flow: int = 0


@dataclass
class BrowserFlowUseList:
    """Data payload of ``scraper.browser.flow_use``."""

    list: list[BrowserFlowUse] = field(default_factory=list)
