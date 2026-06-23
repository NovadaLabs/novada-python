"""The top-level Novada client.

``Client`` injects the Bearer API key on every request and routes calls to one
of three hosts depending on the endpoint. Sub-services (``proxy``, ``scraper``,
``wallet``) are attached as attributes and share the client's single
:class:`~novada._transport.Transport`.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

from ._transport import Transport
from ._version import __version__
from .errors import NovadaError
from .proxy import ProxyService
from .scraper import ScraperService
from .wallet import WalletService

# Default base URLs and tuning values. All three hosts can be overridden via the
# constructor; the defaults target Novada's public production endpoints.

#: General host serving every ``/v1/*`` management endpoint (proxy, wallet, and
#: the scraper area/balance/unit queries).
DEFAULT_BASE_URL = "https://api-m.novada.com"
#: Host serving the Web Unblocker ``POST /request`` endpoint.
DEFAULT_WEB_UNBLOCKER_URL = "https://webunlocker.novada.com"
#: Host serving the Scraper API ``POST /request`` endpoint.
DEFAULT_SCRAPER_URL = "https://scraper.novada.com"

DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 2
DEFAULT_USER_AGENT = f"novada-python/{__version__}"


class Client:
    """The top-level Novada API client.

    The *api_key* argument takes precedence; when it is empty the
    ``NOVADA_API_KEY`` environment variable is used as a fallback. A
    :class:`~novada.errors.NovadaError` is raised when neither is set.

    All three base URLs default to Novada's public hosts and only need to be
    overridden for private deployments or testing. When *http_client* is
    supplied, *timeout* is ignored and the caller owns the client's
    configuration.
    """

    def __init__(
        self,
        api_key: str = "",
        *,
        base_url: str = DEFAULT_BASE_URL,
        web_unblocker_url: str = DEFAULT_WEB_UNBLOCKER_URL,
        scraper_url: str = DEFAULT_SCRAPER_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: Optional[httpx.Client] = None,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        if not api_key:
            api_key = os.environ.get("NOVADA_API_KEY", "")
        if not api_key:
            raise NovadaError(
                "novada: API key is required (pass it to Client or set NOVADA_API_KEY)"
            )

        # Track ownership: a client we created here is closed by close(); a
        # caller-supplied one is left for the caller to manage.
        self._owns_http_client = http_client is None
        if http_client is None:
            http_client = httpx.Client(timeout=timeout)

        self._transport = Transport(
            api_key=api_key,
            base_url=base_url,
            web_unblocker_url=web_unblocker_url,
            scraper_url=scraper_url,
            http_client=http_client,
            max_retries=max_retries,
            user_agent=user_agent,
        )

        #: Proxy management endpoints (the ``/v1/*`` multipart APIs).
        self.proxy = ProxyService(self._transport)
        #: Scraping endpoints (scrape ``/request`` plus the area/balance queries).
        self.scraper = ScraperService(self._transport)
        #: Wallet endpoints (``/v1/wallet/*``).
        self.wallet = WalletService(self._transport)

    @property
    def base_url(self) -> str:
        """The general host used for ``/v1/*`` endpoints."""
        return self._transport.base_url

    @property
    def web_unblocker_url(self) -> str:
        """The host used for the Web Unblocker ``POST /request`` endpoint."""
        return self._transport.web_unblocker_url

    @property
    def scraper_url(self) -> str:
        """The host used for the Scraper API ``POST /request`` endpoint."""
        return self._transport.scraper_url

    def close(self) -> None:
        """Close the underlying HTTP client, unless it was supplied by the
        caller (in which case the caller owns its lifecycle)."""
        if self._owns_http_client:
            self._transport._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
