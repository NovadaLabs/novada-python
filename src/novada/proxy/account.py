"""Proxy sub-account management via the ``/v1/proxy_account/*`` endpoints."""

from __future__ import annotations

from .._decode import decode
from .._transport import Transport
from ._base import Form, Validator, default_page
from .types import (
    AccountConsumeLogList,
    AccountList,
    ConsumeLogParams,
    CreateAccountParams,
    ListAccountParams,
    UpdateAccountParams,
)


class AccountService:
    """Manages proxy sub-accounts via the ``/v1/proxy_account/*`` endpoints."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    def create(self, params: CreateAccountParams) -> None:
        """Add a proxy sub-account (``POST /v1/proxy_account/create``). Product,
        account, password and status are required."""
        v = Validator("Account.create")
        v.require_nonzero("product", int(params.product))
        v.require_str("account", params.account)
        v.require_str("password", params.password)
        v.require_nonzero("status", params.status)
        v.check()

        f = Form()
        f.req_int("product", int(params.product))
        f.req_str("account", params.account)
        f.req_str("password", params.password)
        f.req_int("status", params.status)
        f.opt_str("remark", params.remark)
        f.opt_str("limit_flow", params.limit_flow)

        self._t.do_multipart(self._t.base_url, "/v1/proxy_account/create", f.fields)

    def list(self, params: ListAccountParams) -> AccountList:
        """Return proxy sub-accounts (``POST /v1/proxy_account/list``). Product
        is required; page and limit default to 1 and 10."""
        v = Validator("Account.list")
        v.require_nonzero("product", int(params.product))
        v.check()
        page, limit = default_page(params.page, params.limit)

        f = Form()
        f.req_int("product", int(params.product))
        f.opt_int("status", params.status)
        f.opt_str("account", params.account)
        f.req_int("page", page)
        f.req_int("limit", limit)

        data = self._t.do_multipart(self._t.base_url, "/v1/proxy_account/list", f.fields)
        return decode(data, AccountList) if data is not None else AccountList()

    def update(self, params: UpdateAccountParams) -> None:
        """Modify a proxy sub-account (``POST /v1/proxy_account/update``). ID,
        account and password are required."""
        v = Validator("Account.update")
        v.require_nonzero("id", params.id)
        v.require_str("account", params.account)
        v.require_str("password", params.password)
        v.check()

        f = Form()
        f.req_int("id", params.id)
        f.req_str("account", params.account)
        f.req_str("password", params.password)
        f.opt_int("status", params.status)
        f.opt_str("remark", params.remark)
        f.opt_str("limit_flow", params.limit_flow)

        self._t.do_multipart(self._t.base_url, "/v1/proxy_account/update", f.fields)

    def consume_log(self, params: ConsumeLogParams) -> AccountConsumeLogList:
        """Return per-day traffic consumption for an account
        (``POST /v1/proxy_account/consume_log``). AccountID is required; page
        and limit default to 1 and 10."""
        v = Validator("Account.consume_log")
        v.require_nonzero("account_id", params.account_id)
        v.check()
        page, limit = default_page(params.page, params.limit)

        f = Form()
        f.req_int("account_id", params.account_id)
        f.opt_str("start_time", params.start_time)
        f.opt_str("end_time", params.end_time)
        f.req_int("page", page)
        f.req_int("limit", limit)

        data = self._t.do_multipart(self._t.base_url, "/v1/proxy_account/consume_log", f.fields)
        return decode(data, AccountConsumeLogList) if data is not None else AccountConsumeLogList()
