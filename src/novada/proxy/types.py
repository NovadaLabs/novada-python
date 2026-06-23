"""Parameter and response dataclasses for the proxy services, plus the
:class:`Product` enum.

Parameter dataclasses mirror the Go SDK's ``*Params`` structs (required fields
have no default; optional fields default to an empty/zero value and are omitted
from the request when unset). Response dataclasses name their fields exactly as
the JSON snake_case keys and give every field a zero-value default so decoding
tolerates missing keys and ignores unknown ones.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


class Product(IntEnum):
    """A Novada proxy product line. The numeric values are fixed by the API;
    not every product is valid for every endpoint."""

    RESIDENTIAL = 1
    ROTATING_ISP = 2
    ROTATING_DC = 3
    UNLIMITED = 4
    STATIC_ISP = 5
    UNBLOCKER = 7
    MOBILE = 9
    BROWSER_API = 10


# --- Shared ----------------------------------------------------------------


@dataclass
class TimeRange:
    """A start/end window used by the traffic-consumption endpoints. Both bounds
    use the ``"2006-01-02 15:04:05"`` layout and are required."""

    start: str
    end: str


@dataclass
class FlowBalance:
    """Remaining-traffic payload shared by the residential, rotating ISP and
    rotating datacenter balance endpoints. ``expire_time`` is a Unix timestamp
    (seconds) and is zero for products that do not report it."""

    balance: int = 0
    expire_time: int = 0


@dataclass
class FlowConsumeLog:
    """A single traffic-consumption record shared by the residential, rotating
    ISP, rotating datacenter and mobile consumption endpoints. Byte counts are
    in bytes."""

    id: int = 0
    uid: int = 0
    balance: int = 0
    all_buy: int = 0
    use: int = 0
    day: int = 0
    expire_flow: int = 0


@dataclass
class FlowConsumeLogList:
    """Data payload of the traffic-consumption endpoints."""

    list: list[FlowConsumeLog] = field(default_factory=list)


# --- Account ---------------------------------------------------------------


@dataclass
class CreateAccountParams:
    """Parameters for ``account.create``. Product, account, password and status
    are required."""

    product: Product
    account: str
    password: str
    status: int
    remark: str = ""
    #: Dynamic residential data cap in GB, sent as a string.
    limit_flow: str = ""


@dataclass
class ListAccountParams:
    """Parameters for ``account.list``. Product is required; page and limit
    default to 1 and 10 when left at zero."""

    product: Product
    status: int = 0
    account: str = ""
    page: int = 0
    limit: int = 0


@dataclass
class UpdateAccountParams:
    """Parameters for ``account.update``. ID, account and password are
    required."""

    id: int
    account: str
    password: str
    status: int = 0
    remark: str = ""
    limit_flow: str = ""


@dataclass
class ConsumeLogParams:
    """Parameters for ``account.consume_log``. AccountID is required; page and
    limit default to 1 and 10. Times use the ``"2006-01-02 15:04:05"`` layout."""

    account_id: int
    start_time: str = ""
    end_time: str = ""
    page: int = 0
    limit: int = 0


@dataclass
class Account:
    """A proxy sub-account as returned by ``account.list``."""

    created_at: int = 0
    updated_at: int = 0
    id: int = 0
    uid: int = 0
    account: str = ""
    password: str = ""
    status: int = 0
    residential_balance: int = 0
    residential_all_buy: int = 0
    residential_status: int = 0
    dc_balance: int = 0
    dc_all_buy: int = 0
    dc_status: int = 0
    isp_balance: int = 0
    isp_all_buy: int = 0
    isp_status: int = 0
    flow_type: str = ""
    account_type: str = ""
    check_white_list: int = 0
    remark: str = ""
    consumed_residential_flow: int = 0
    limit_residential_flow: int = 0
    consumed_dc_flow: int = 0
    limit_dc_flow: int = 0
    consumed_isp_flow: int = 0
    limit_isp_flow: int = 0


@dataclass
class AccountList:
    """Data payload of ``account.list``."""

    list: list[Account] = field(default_factory=list)
    page: int = 0
    total: int = 0


@dataclass
class AccountConsumeLog:
    """A single daily traffic-consumption record."""

    id: int = 0
    account_id: int = 0
    uid: int = 0
    residential_balance: int = 0
    residential_all_buy: int = 0
    consumed_residential_flow: int = 0
    dc_balance: int = 0
    dc_all_buy: int = 0
    consumed_dc_flow: int = 0
    isp_balance: int = 0
    isp_all_buy: int = 0
    consumed_isp_flow: int = 0
    #: Unix timestamp (seconds) of the record's day.
    day: int = 0


@dataclass
class AccountConsumeLogList:
    """Data payload of ``account.consume_log``."""

    list: list[AccountConsumeLog] = field(default_factory=list)


# --- Whitelist -------------------------------------------------------------


@dataclass
class AddWhitelistParams:
    """Parameters for ``whitelist.add``. Product and IP are required. Valid
    products: RESIDENTIAL, STATIC_ISP, UNLIMITED."""

    product: Product
    ip: str
    remark: str = ""


@dataclass
class ListWhitelistParams:
    """Parameters for ``whitelist.list``. Product is required; the remaining
    fields are optional filters."""

    product: Product
    ip: str = ""
    start_time: str = ""
    end_time: str = ""
    #: Lock state filter: 0=unlocked, 1=locked. None means no filter.
    lock: Optional[int] = None


@dataclass
class DeleteWhitelistParams:
    """Parameters for ``whitelist.delete``. Product and IPs are required; pass
    multiple IPs comma-separated."""

    product: Product
    #: Comma-separated list, e.g. ``"1.1.1.1,2.2.2.2"``.
    ips: str


@dataclass
class RemarkWhitelistParams:
    """Parameters for ``whitelist.remark``. Product and ID are required."""

    product: Product
    #: The whitelist entry ID.
    id: str
    remark: str = ""


@dataclass
class WhitelistIP:
    """A whitelist entry as returned by ``whitelist.list``."""

    created_at: int = 0
    updated_at: int = 0
    id: int = 0
    uid: int = 0
    #: Human-readable IP string (e.g. ``"10.10.10.1"``).
    mark_ip: str = ""
    #: Integer form of the address as stored by the API.
    ip: int = 0
    status: int = 0
    lock: bool = False
    lock_uid: int = 0
    flag: int = 0
    is_biger: int = 0
    is_limit: int = 0
    mark: str = ""


@dataclass
class WhitelistList:
    """Data payload of ``whitelist.list``."""

    list: list[WhitelistIP] = field(default_factory=list)
    total: int = 0


# --- Residential -----------------------------------------------------------


@dataclass
class CityParams:
    """Selects a city listing by country code and region/state. Both fields are
    required."""

    code: str
    region: str


@dataclass
class ResidentialCountry:
    """A single residential proxy country."""

    code: str = ""
    continent: int = 0
    ip_num: int = 0
    name: str = ""
    name_en: str = ""
    protocol: int = 0


@dataclass
class ResidentialContinentGroup:
    """A continent with its list of countries."""

    continent: str = ""
    continent_code: int = 0
    list: list[ResidentialCountry] = field(default_factory=list)


@dataclass
class ResidentialAreas:
    """Country listing returned by ``residential.countries``. ``continent`` maps
    continent codes to names; ``country`` groups countries by continent."""

    continent: dict[str, str] = field(default_factory=dict)
    country: list[ResidentialContinentGroup] = field(default_factory=list)


@dataclass
class ResidentialState:
    """A state/region within a country."""

    state: str = ""


@dataclass
class ResidentialStateList:
    """Data payload of ``residential.states``."""

    data: list[ResidentialState] = field(default_factory=list)


@dataclass
class ResidentialCity:
    """A city within a region."""

    code: str = ""


@dataclass
class ResidentialCityList:
    """Data payload of ``residential.cities``."""

    data: list[ResidentialCity] = field(default_factory=list)


@dataclass
class ResidentialISP:
    """An ISP available in a country."""

    asn: str = ""
    show_name: str = ""


@dataclass
class ResidentialISPList:
    """Data payload of ``residential.isps``."""

    list: list[ResidentialISP] = field(default_factory=list)


# --- Mobile ----------------------------------------------------------------


@dataclass
class MobileUseParams:
    """Selects a mobile traffic window. Start, end and granularity are
    required."""

    start: str
    end: str
    #: Bucket size: ``"1"``=hour, ``"2"``=day.
    granularity: str


@dataclass
class MobileBalance:
    """Remaining mobile traffic in bytes."""

    balance: int = 0


# --- Rotating ISP / DC -----------------------------------------------------


@dataclass
class ISPCountry:
    """A single rotating ISP country."""

    code: str = ""
    node: str = ""


@dataclass
class ISPArea:
    """Country listing returned by ``rotating_isp.countries``."""

    country: list[ISPCountry] = field(default_factory=list)


@dataclass
class DCCity:
    """City descriptor nested in a :class:`DCCountry`."""

    code: str = ""


@dataclass
class DCCountry:
    """A single rotating datacenter country."""

    id: int = 0
    code: str = ""
    status: int = 0
    continents: int = 0
    area_code: int = 0
    name_en: str = ""
    available: int = 0
    city: DCCity = field(default_factory=DCCity)


@dataclass
class DCArea:
    """Country listing returned by ``rotating_dc.countries``."""

    country: list[DCCountry] = field(default_factory=list)


# --- Static ISP / Dedicated DC ---------------------------------------------


@dataclass
class StaticIP:
    """A purchased static IP (ISP or dedicated datacenter)."""

    id: int = 0
    ip: str = ""
    port: str = ""
    duration: int = 0
    region: str = ""
    expire_time: int = 0
    create_time: int = 0
    country: str = ""
    country_en: str = ""
    status: int = 0
    remark: str = ""
    auto_renew: int = 0
    type: int = 0
    diff_day: int = 0
    account: str = ""
    password: str = ""


@dataclass
class StaticIPList:
    """Data payload of the static IP list endpoints."""

    list: list[StaticIP] = field(default_factory=list)
    page: int = 0
    total: int = 0


@dataclass
class RegionNode:
    """A single selectable region in the region listings."""

    node: str = ""
    node_en: str = ""
    param: int = 0
    region: str = ""


@dataclass
class RegionList:
    """Data payload of the static region endpoints; regions are grouped by area
    name (e.g. ``"Asia-Pacific"``)."""

    list: dict[str, list[RegionNode]] = field(default_factory=dict)


@dataclass
class ListStaticParams:
    """Filters for the static IP list endpoints. Page and limit default to 1 and
    10 when left at zero."""

    #: ``""`` = all, ``"1"`` = in use, ``"2"`` = expired, ``"3"`` = released.
    status: str = ""
    #: Area code filter.
    region: str = ""
    #: Keyword filter (remark, order number, IP).
    key_word: str = ""
    #: Auto-renew filter (1 = yes, -1 = no). None = no filter.
    is_auto_renew: Optional[int] = None
    page: int = 0
    limit: int = 0


@dataclass
class ExportStaticParams:
    """Filters for the static IP export endpoints."""

    status: str = ""
    region: str = ""
    key_word: str = ""
    is_auto_renew: Optional[int] = None


@dataclass
class RenewStaticParams:
    """Renews one or more static IPs. Both fields are required."""

    #: Comma-separated list of IPs, e.g. ``"1.1.1.1,2.2.2.2"``.
    ips: str
    #: Activation period: ``"week"`` or ``"month"``.
    duration: str


@dataclass
class RenewSettingParams:
    """Updates the auto-renewal settings of static IPs. All fields are
    required; the product type is supplied automatically by the service
    method."""

    #: Comma-separated list of IP IDs, e.g. ``"100,111,112"``.
    ids: str
    #: Activation period: ``"week"`` or ``"month"``.
    package_type: str
    #: Renewal status: 1 = normal, -1 = disabled.
    status: int
    #: Renewal method: 1 = wallet, 2 = credit card.
    renew_type: int


@dataclass
class OpenStaticISPParams:
    """Opens static ISP IPs. All fields are required."""

    #: IP grade: ``"normal"`` = standard, ``"premium"`` = premium.
    ip_type: str
    #: An ``"area:num"`` spec, e.g. ``"hk:1|us-va:2"``.
    region: str
    #: Activation period: ``"week"`` or ``"month"``.
    duration: str
    #: Number of IPs to open.
    num: int


@dataclass
class OpenDedicatedDCParams:
    """Opens dedicated datacenter IPs. All fields are required."""

    #: An ``"area:num"`` spec, e.g. ``"hk:1|tw:2"``.
    region: str
    #: Activation period: ``"week"`` or ``"month"``.
    duration: str
    #: Number of IPs to open.
    num: int


# --- Unlimited -------------------------------------------------------------


@dataclass
class UnlimitedHost:
    """A single unlimited proxy server."""

    id: int = 0
    create_time: int = 0
    expire_time: int = 0
    state: int = 0
    host: str = ""
    user_rate_limit_bytes: int = 0
    order_id: str = ""
    days: int = 0
    duration: int = 0
    band_width: int = 0
    hardware: str = ""


@dataclass
class UnlimitedHostList:
    """Data payload of ``unlimited.hosts``."""

    list: list[UnlimitedHost] = field(default_factory=list)
    page: int = 0
    total: int = 0


# --- Prohibit domain -------------------------------------------------------


@dataclass
class ProhibitDomain:
    """A single blocked-domain entry."""

    created_at: int = 0
    updated_at: int = 0
    id: int = 0
    uid: int = 0
    status: int = 0
    address: str = ""


@dataclass
class ProhibitDomainList:
    """Data payload of ``prohibit_domain.list``."""

    list: list[ProhibitDomain] = field(default_factory=list)
    total: int = 0


@dataclass
class DeleteProhibitParams:
    """Identifies which blocked domains to delete. When ``all`` is true every
    entry is deleted and ``id`` is ignored; otherwise ``id`` is required."""

    #: Entry ID; required unless ``all`` is true.
    id: str = ""
    #: Delete all entries.
    all: bool = False


# Mobile/Browser area listings have no documented fixed shape; their raw decoded
# payload is returned to the caller as Any.
RawData = Any
