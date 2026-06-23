"""M5 acceptance: wallet balance and paginated usage records."""

from __future__ import annotations

import httpx
import respx

from novada import Client
from novada.wallet.types import UsageRecordParams

from .conftest import envelope, parse_multipart


@respx.mock
def test_wallet_balance(client: Client) -> None:
    respx.post("http://base.test/v1/wallet/balance").mock(
        return_value=httpx.Response(200, text=envelope({"balance": 123456}))
    )
    res = client.wallet.balance()
    assert res.balance == 123456


@respx.mock
def test_wallet_usage_record_defaults(client: Client) -> None:
    route = respx.post("http://base.test/v1/wallet/usage_record").mock(
        return_value=httpx.Response(
            200,
            text=envelope({"count": 1, "list": [{"id": 9, "order_id": "o1", "money": 3.5}]}),
        )
    )
    res = client.wallet.usage_record(UsageRecordParams())
    fields = parse_multipart(route.calls.last.request)
    assert fields == {"page": "1", "limit": "10"}
    assert res.count == 1
    assert res.list[0].order_id == "o1"
    assert res.list[0].money == 3.5


@respx.mock
def test_wallet_usage_record_explicit_pagination(client: Client) -> None:
    route = respx.post("http://base.test/v1/wallet/usage_record").mock(
        return_value=httpx.Response(200, text=envelope({"count": 0, "list": []}))
    )
    client.wallet.usage_record(UsageRecordParams(page=2, limit=20))
    assert parse_multipart(route.calls.last.request) == {"page": "2", "limit": "20"}
