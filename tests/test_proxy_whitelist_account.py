"""M1 acceptance: proxy whitelist + account encoding, decoding, validation."""

from __future__ import annotations

import httpx
import pytest
import respx

from novada import Client, Product, ValidationError
from novada.proxy.types import (
    AddWhitelistParams,
    ConsumeLogParams,
    CreateAccountParams,
    DeleteWhitelistParams,
    ListAccountParams,
    ListWhitelistParams,
    RemarkWhitelistParams,
    UpdateAccountParams,
)

from .conftest import envelope, parse_multipart


@respx.mock
def test_whitelist_add_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/add").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.whitelist.add(
        AddWhitelistParams(product=Product.RESIDENTIAL, ip="10.10.10.1", remark="test")
    )
    assert parse_multipart(route.calls.last.request) == {
        "product": "1",
        "ip": "10.10.10.1",
        "remark": "test",
    }


@respx.mock
def test_whitelist_add_omits_empty_remark(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/add").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.whitelist.add(AddWhitelistParams(product=Product.RESIDENTIAL, ip="1.2.3.4"))
    assert "remark" not in parse_multipart(route.calls.last.request)


@respx.mock
def test_whitelist_list_unwrap(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/list").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "list": [
                        {
                            "id": 12,
                            "uid": 81,
                            "mark_ip": "10.10.10.1",
                            "ip": 168430081,
                            "status": 1,
                            "lock": False,
                            "mark": "test",
                        }
                    ],
                    "total": 1,
                }
            ),
        )
    )
    lock = 1
    res = client.proxy.whitelist.list(
        ListWhitelistParams(product=Product.STATIC_ISP, ip="10.10.10.1", lock=lock)
    )
    fields = parse_multipart(route.calls.last.request)
    assert fields["product"] == "5"
    assert fields["lock"] == "1"
    assert res.total == 1
    assert len(res.list) == 1
    assert res.list[0].mark_ip == "10.10.10.1"
    assert res.list[0].ip == 168430081


@respx.mock
def test_whitelist_list_lock_none_omitted(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/list").mock(
        return_value=httpx.Response(200, text=envelope({"list": [], "total": 0}))
    )
    client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))
    assert "lock" not in parse_multipart(route.calls.last.request)


@respx.mock
def test_whitelist_delete_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/del").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.whitelist.delete(
        DeleteWhitelistParams(product=Product.RESIDENTIAL, ips="1.1.1.1,2.2.2.2")
    )
    assert parse_multipart(route.calls.last.request) == {
        "product": "1",
        "ips": "1.1.1.1,2.2.2.2",
    }


@respx.mock
def test_whitelist_remark_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/remark").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.whitelist.remark(
        RemarkWhitelistParams(product=Product.RESIDENTIAL, id="101", remark="some mark")
    )
    assert parse_multipart(route.calls.last.request) == {
        "product": "1",
        "id": "101",
        "remark": "some mark",
    }


@respx.mock
def test_account_create_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy_account/create").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.account.create(
        CreateAccountParams(
            product=Product.RESIDENTIAL,
            account="account11",
            password="pass11",
            status=1,
        )
    )
    assert parse_multipart(route.calls.last.request) == {
        "product": "1",
        "account": "account11",
        "password": "pass11",
        "status": "1",
    }


@respx.mock
def test_account_list_defaults_and_unwrap(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy_account/list").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "list": [
                        {
                            "id": 2,
                            "account": "account11",
                            "status": 1,
                            "limit_residential_flow": 1100000000,
                        }
                    ],
                    "page": 1,
                    "total": 2,
                }
            ),
        )
    )
    res = client.proxy.account.list(ListAccountParams(product=Product.RESIDENTIAL))
    fields = parse_multipart(route.calls.last.request)
    assert fields["page"] == "1"
    assert fields["limit"] == "10"
    assert res.total == 2
    assert res.list[0].limit_residential_flow == 1100000000


@respx.mock
def test_account_consume_log_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy_account/consume_log").mock(
        return_value=httpx.Response(
            200, text=envelope({"list": [{"account_id": 2, "day": 1731340800}]})
        )
    )
    res = client.proxy.account.consume_log(
        ConsumeLogParams(account_id=2, start_time="2025-01-01 00:00:00", page=3)
    )
    fields = parse_multipart(route.calls.last.request)
    assert fields["account_id"] == "2"
    assert fields["page"] == "3"
    assert fields["limit"] == "10"
    assert fields["start_time"] == "2025-01-01 00:00:00"
    assert res.list[0].day == 1731340800


@respx.mock
def test_account_update_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy_account/update").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.account.update(
        UpdateAccountParams(
            id=2,
            account="account11",
            password="pass11",
            status=-3,
            remark="disabled",
            limit_flow="5",
        )
    )
    assert parse_multipart(route.calls.last.request) == {
        "id": "2",
        "account": "account11",
        "password": "pass11",
        "status": "-3",
        "remark": "disabled",
        "limit_flow": "5",
    }


def _add_invalid(c: Client) -> None:
    c.proxy.whitelist.add(AddWhitelistParams(product=0, ip=""))  # type: ignore[arg-type]


def _create_invalid(c: Client) -> None:
    c.proxy.account.create(
        CreateAccountParams(product=0, account="a", password="", status=0)  # type: ignore[arg-type]
    )


def _update_invalid(c: Client) -> None:
    c.proxy.account.update(UpdateAccountParams(id=0, account="", password=""))


@pytest.mark.parametrize(
    ("call", "fields"),
    [
        (_add_invalid, ["product", "ip"]),
        (_create_invalid, ["product", "password", "status"]),
        (_update_invalid, ["id", "account", "password"]),
    ],
)
def test_validation_missing_required(client: Client, call, fields) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValidationError) as exc:
        call(client)
    assert set(exc.value.fields) == set(fields)


@respx.mock
def test_validation_prevents_request(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/add").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    with pytest.raises(ValidationError):
        client.proxy.whitelist.add(AddWhitelistParams(product=0, ip=""))  # type: ignore[arg-type]
    assert route.call_count == 0


def test_validation_error_message() -> None:
    err = ValidationError("Whitelist.add", ["product", "ip"])
    assert str(err) == "Whitelist.add: missing required field(s): product, ip"
