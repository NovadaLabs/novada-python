"""Python SDK for the Novada API — proxy management, scraping, and wallet.

Quick start::

    from novada import Client

    client = Client("YOUR_API_KEY")  # or "" to read NOVADA_API_KEY
    result = client.proxy.whitelist.list(
        ListWhitelistParams(product=Product.RESIDENTIAL)
    )
    print(result.total)
"""

from __future__ import annotations

from ._version import __version__
from .client import (
    DEFAULT_BASE_URL,
    DEFAULT_SCRAPER_URL,
    DEFAULT_WEB_UNBLOCKER_URL,
    Client,
)
from .errors import (
    APIError,
    AuthError,
    NovadaError,
    RateLimitError,
    ValidationError,
    code_of,
    is_auth_error,
    is_rate_limited,
)
from .proxy.types import Product
from .scraper.types import Target

__all__ = [
    "Client",
    "Product",
    "Target",
    "NovadaError",
    "APIError",
    "AuthError",
    "RateLimitError",
    "ValidationError",
    "is_auth_error",
    "is_rate_limited",
    "code_of",
    "DEFAULT_BASE_URL",
    "DEFAULT_WEB_UNBLOCKER_URL",
    "DEFAULT_SCRAPER_URL",
    "__version__",
]
