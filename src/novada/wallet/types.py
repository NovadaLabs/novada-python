"""Parameter and response dataclasses for the wallet service."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Balance:
    """The wallet balance payload."""

    balance: int = 0


@dataclass
class UsageRecordParams:
    """Paginates the usage records. Page and limit default to 1 and 10 when left
    at zero."""

    page: int = 0
    limit: int = 0


@dataclass
class UsageRecord:
    """A single wallet usage/order record."""

    created_at: int = 0
    updated_at: int = 0
    id: int = 0
    uid: int = 0
    order_type: str = ""
    type: int = 0
    source: int = 0
    order_id: str = ""
    money: float = 0.0
    pay_money: float = 0.0
    pay_type: str = ""
    pay_sn: str = ""
    pay_status: int = 0
    pay_cate: int = 0
    description: str = ""
    status: int = 0
    create_admin: str = ""
    is_first_order: int = 0
    pay_time: int = 0
    closed_at: int = 0


@dataclass
class UsageRecordList:
    """Data payload of ``wallet.usage_record``."""

    count: int = 0
    list: list[UsageRecord] = field(default_factory=list)
