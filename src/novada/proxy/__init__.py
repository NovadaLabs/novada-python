"""Proxy management endpoints (the ``/v1/*`` multipart/form-data APIs).

Reach the sub-services through the attributes of :class:`ProxyService`, e.g.
``client.proxy.whitelist.list(...)``.
"""

from __future__ import annotations

from .._transport import Transport
from .account import AccountService
from .dedicated import DedicatedDCService
from .mobile import MobileService
from .prohibit_domain import ProhibitDomainService
from .residential import ResidentialService
from .rotating import RotatingDCService, RotatingISPService
from .static import StaticISPService
from .unlimited import UnlimitedService
from .whitelist import WhitelistService


class ProxyService:
    """Entry point for proxy management endpoints.

    Sub-services are attached as snake_case attributes mirroring the Go SDK's
    exported fields.
    """

    def __init__(self, transport: Transport) -> None:
        #: Proxy sub-accounts (``/v1/proxy_account/*``).
        self.account = AccountService(transport)
        #: IP whitelists (``/v1/white_list/*``).
        self.whitelist = WhitelistService(transport)
        #: Residential proxy areas and traffic.
        self.residential = ResidentialService(transport)
        #: Mobile proxy areas and traffic.
        self.mobile = MobileService(transport)
        #: Rotating ISP proxy areas and traffic.
        self.rotating_isp = RotatingISPService(transport)
        #: Rotating datacenter proxy areas and traffic.
        self.rotating_dc = RotatingDCService(transport)
        #: Static ISP proxies (``/v1/static_house/*``).
        self.static_isp = StaticISPService(transport)
        #: Dedicated datacenter proxies (``/v1/static/*``).
        self.dedicated_dc = DedicatedDCService(transport)
        #: Unlimited proxy servers (``/v1/unlimited/*``).
        self.unlimited = UnlimitedService(transport)
        #: Blocked domains (``/v1/prohibit_domain/*``).
        self.prohibit_domain = ProhibitDomainService(transport)


__all__ = ["ProxyService"]
