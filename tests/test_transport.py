"""M0 acceptance: transport encoding, Bearer injection, envelope decoding,
error mapping and retry behaviour."""

from __future__ import annotations

import httpx
import pytest
import respx

from novada import (
    APIError,
    AuthError,
    Client,
    NovadaError,
    RateLimitError,
)

from .conftest import envelope, parse_multipart


@respx.mock
def test_multipart_bearer_and_envelope_unwrap(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/list").mock(
        return_value=httpx.Response(200, text=envelope({"list": [], "total": 3}))
    )
    data = client._transport.do_multipart(
        "http://base.test", "/v1/white_list/list", {"product": "1"}
    )

    assert data == {"list": [], "total": 3}
    request = route.calls.last.request
    assert request.headers["authorization"] == "Bearer test-key"
    assert request.headers["accept"] == "application/json"
    assert request.headers["user-agent"].startswith("novada-python/")
    assert request.headers["content-type"].startswith("multipart/form-data; boundary=")
    assert parse_multipart(request) == {"product": "1"}


@respx.mock
def test_multipart_omits_empty_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/white_list/add").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client._transport.do_multipart(
        "http://base.test",
        "/v1/white_list/add",
        {"product": "1", "ip": "1.2.3.4", "remark": ""},
    )
    assert parse_multipart(route.calls.last.request) == {"product": "1", "ip": "1.2.3.4"}


@respx.mock
def test_business_code_nonzero_raises_apierror(client: Client) -> None:
    respx.post("http://base.test/v1/white_list/list").mock(
        return_value=httpx.Response(200, text=envelope(None, code=1001, msg="boom"))
    )
    with pytest.raises(APIError) as exc:
        client._transport.do_multipart("http://base.test", "/v1/white_list/list", {})
    assert exc.value.code == 1001
    assert exc.value.http_status == 200
    assert exc.value.message == "boom"
    # A business failure is not an auth/rate-limit error.
    assert not isinstance(exc.value, (AuthError, RateLimitError))


@respx.mock
@pytest.mark.parametrize(
    ("status", "exc_type"),
    [
        (401, AuthError),
        (403, AuthError),
        (429, RateLimitError),
        (500, APIError),
    ],
)
def test_http_status_maps_to_error(client: Client, status: int, exc_type: type[APIError]) -> None:
    respx.post("http://base.test/v1/x").mock(
        return_value=httpx.Response(status, text=envelope(None, code=9, msg="nope"))
    )
    with pytest.raises(exc_type) as exc:
        client._transport.do_multipart("http://base.test", "/v1/x", {})
    assert exc.value.http_status == status
    # The message prefers the envelope "msg".
    assert exc.value.message == "nope"


@respx.mock
def test_retry_on_429_then_success() -> None:
    client = Client("k", base_url="http://base.test", max_retries=2)
    route = respx.post("http://base.test/v1/x").mock(
        side_effect=[
            httpx.Response(429, text="rate"),
            httpx.Response(200, text=envelope({"ok": 1})),
        ]
    )
    data = client._transport.do_multipart("http://base.test", "/v1/x", {})
    assert data == {"ok": 1}
    assert route.call_count == 2


@respx.mock
def test_business_code_never_retried() -> None:
    client = Client("k", base_url="http://base.test", max_retries=3)
    route = respx.post("http://base.test/v1/x").mock(
        return_value=httpx.Response(200, text=envelope(None, code=7, msg="biz"))
    )
    with pytest.raises(APIError):
        client._transport.do_multipart("http://base.test", "/v1/x", {})
    assert route.call_count == 1


@respx.mock
def test_network_error_retried_then_raises() -> None:
    client = Client("k", base_url="http://base.test", max_retries=1)
    route = respx.post("http://base.test/v1/x").mock(side_effect=httpx.ConnectError("down"))
    with pytest.raises(NovadaError):
        client._transport.do_multipart("http://base.test", "/v1/x", {})
    assert route.call_count == 2


def test_missing_api_key_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NOVADA_API_KEY", raising=False)
    with pytest.raises(NovadaError):
        Client("")


def test_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NOVADA_API_KEY", "env-key")
    client = Client("")
    assert client.base_url == "https://api-m.novada.com"
