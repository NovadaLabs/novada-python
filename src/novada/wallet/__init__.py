"""Wallet endpoints (``/v1/wallet/*``). Reach it via ``client.wallet``."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ..proxy._base import default_page
from .types import Balance, UsageRecordList, UsageRecordParams


class WalletService:
    """Entry point for wallet endpoints."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def balance(self) -> Balance:
        """Return the wallet balance (``POST /v1/wallet/balance``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/wallet/balance", {})
        return decode(data, Balance) if data is not None else Balance()

    def usage_record(self, params: UsageRecordParams) -> UsageRecordList:
        """Return paginated wallet usage records
        (``POST /v1/wallet/usage_record``). Page and limit default to 1 and 10."""
        page, limit = default_page(params.page, params.limit)
        fields = {"page": str(page), "limit": str(limit)}
        data = self._t.do_multipart(self._t.base_url, "/v1/wallet/usage_record", fields)
        return decode(data, UsageRecordList) if data is not None else UsageRecordList()


__all__ = ["WalletService"]
