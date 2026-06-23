"""Shared scraper account queries (balance, usage logs, unit prices) on the
general host."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from .types import ScraperBalance, UnitPrices, UsageLogList


class UniversalService:
    """The shared scraper account queries."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def balance(self) -> ScraperBalance:
        """Return the remaining scraper balance
        (``POST /v1/capture/get_balance``). The endpoint returns the balance as
        a bare number in the ``data`` field, which is wrapped here."""
        data = self._t.do_multipart(self._t.base_url, "/v1/capture/get_balance", {})
        balance = float(data) if data is not None else 0.0
        return ScraperBalance(scraper_balance=balance)

    def logs(self) -> UsageLogList:
        """Return the scraper consumption records (``POST /v1/capture/logs``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/capture/logs", {})
        return decode(data, UsageLogList) if data is not None else UsageLogList()

    def unit(self) -> UnitPrices:
        """Return the user's capture unit prices (``POST /v1/capture/unit``)."""
        data = self._t.do_multipart(self._t.base_url, "/v1/capture/unit", {})
        return decode(data, UnitPrices) if data is not None else UnitPrices()
