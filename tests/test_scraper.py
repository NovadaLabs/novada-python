"""M3/M4 acceptance: scraper generic driver, typed scrapers, query endpoints."""

from __future__ import annotations

import json
from urllib.parse import parse_qs

import httpx
import pytest
import respx

from novada import Client, ValidationError
from novada.scraper import Request, Target
from novada.scraper.types import (
    GoogleSearchParams,
    UnblockerParams,
    YouTubeVideoParams,
)

from .conftest import envelope


def form_of(request: httpx.Request) -> dict[str, str]:
    """Parse an x-www-form-urlencoded request body into a flat dict."""
    parsed = parse_qs(request.content.decode("utf-8"))
    return {k: v[0] for k, v in parsed.items()}


@respx.mock
def test_do_encodes_and_routes_to_scraper_api(client: Client) -> None:
    route = respx.post("http://scraper.test/request").mock(
        return_value=httpx.Response(200, text='{"ok":true}')
    )
    res = client.scraper.do(
        Request(
            target=Target.SCRAPER_API,
            scraper_name="youtube.com",
            scraper_id="youtube_video-post_explore",
            params=[{"url": "https://youtu.be/x"}],
            return_errors=True,
        )
    )
    assert res.raw == '{"ok":true}'
    form = form_of(route.calls.last.request)
    assert form["scraper_name"] == "youtube.com"
    assert form["scraper_id"] == "youtube_video-post_explore"
    assert form["scraper_errors"] == "true"
    # scraper_params must be the JSON-marshaled array.
    parsed = json.loads(form["scraper_params"])
    assert parsed == [{"url": "https://youtu.be/x"}]
    # Compact JSON, matching Go's encoding/json (no spaces).
    assert form["scraper_params"] == '[{"url":"https://youtu.be/x"}]'


@respx.mock
def test_do_routes_to_web_unblocker(client: Client) -> None:
    route = respx.post("http://unblock.test/request").mock(
        return_value=httpx.Response(200, text="ok")
    )
    client.scraper.do(
        Request(
            target=Target.WEB_UNBLOCKER,
            scraper_name="example.com",
            scraper_id="web-unlocker",
            params=[{"url": "https://example.com"}],
        )
    )
    assert "scraper_errors" not in form_of(route.calls.last.request)


def test_do_validation(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.scraper.do(Request(scraper_name="", scraper_id="", params=[]))
    assert set(exc.value.fields) == {"scraper_name", "scraper_id", "scraper_params"}


@respx.mock
def test_youtube_video_post(client: Client) -> None:
    route = respx.post("http://scraper.test/request").mock(
        return_value=httpx.Response(200, text='{"title":"t"}')
    )
    res = client.scraper.api.youtube.video_post(
        YouTubeVideoParams(url="https://www.youtube.com/watch?v=HAwTwmzgNc4")
    )
    assert res.raw == '{"title":"t"}'
    form = form_of(route.calls.last.request)
    assert form["scraper_id"] == "youtube_video-post_explore"
    params = json.loads(form["scraper_params"])
    assert params[0]["url"] == "https://www.youtube.com/watch?v=HAwTwmzgNc4"


@respx.mock
def test_google_search_flat_form_and_decode(client: Client) -> None:
    route = respx.post("http://scraper.test/request").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "code": 200,
                    "cost_time": 1103,
                    "msg": "success",
                    "data": {
                        "filename": "",
                        "html": None,
                        "json": [{"spider_code": 200}],
                        "task_id": "abc123",
                    },
                }
            ),
        )
    )
    res = client.scraper.api.google.search(
        GoogleSearchParams(query="apple", country="us", device="desktop")
    )
    form = form_of(route.calls.last.request)
    assert form["scraper_id"] == "google_search"
    assert form["q"] == "apple"
    assert form["json"] == "1"  # defaulted to JSON output
    assert form["country"] == "us"
    assert form["device"] == "desktop"
    assert res.code == 200
    assert res.cost_time == 1103
    assert res.data.task_id == "abc123"
    # The raw result array is preserved verbatim (Any / json.RawMessage parity).
    assert res.data.json == [{"spider_code": 200}]


@respx.mock
def test_google_search_html_mode(client: Client) -> None:
    route = respx.post("http://scraper.test/request").mock(
        return_value=httpx.Response(200, text=envelope({"code": 200}))
    )
    client.scraper.api.google.search(GoogleSearchParams(query="x", html=True))
    assert form_of(route.calls.last.request)["json"] == "0"


def test_google_search_validation(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.scraper.api.google.search(GoogleSearchParams(query=""))
    assert exc.value.fields == ["q"]


@respx.mock
def test_unblocker_scrape_fields_and_decode(client: Client) -> None:
    route = respx.post("http://unblock.test/request").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "code": 200,
                    "html": "<html></html>",
                    "msg_detail": "",
                    "use_balance": 0.0013,
                }
            ),
        )
    )
    res = client.scraper.unblocker.scrape(
        UnblockerParams(
            target_url="https://www.google.com",
            country="us",
            js_render=True,
            wait_ms=5000,
        )
    )
    form = form_of(route.calls.last.request)
    assert form["target_url"] == "https://www.google.com"
    assert form["response_format"] == "html"  # defaulted
    assert form["js_render"] == "true"
    assert form["country"] == "us"
    assert form["wait_ms"] == "5000"
    assert res.code == 200
    assert res.html == "<html></html>"
    assert res.use_balance == 0.0013


def test_unblocker_scrape_validation(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.scraper.unblocker.scrape(UnblockerParams(target_url=""))
    assert exc.value.fields == ["target_url"]


@respx.mock
def test_universal_balance_bare_number(client: Client) -> None:
    route = respx.post("http://base.test/v1/capture/get_balance").mock(
        return_value=httpx.Response(200, text=envelope(998909.179853))
    )
    res = client.scraper.universal.balance()
    assert route.called
    assert res.scraper_balance == 998909.179853


@respx.mock
def test_universal_unit_decode(client: Client) -> None:
    respx.post("http://base.test/v1/capture/unit").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "scraper": [{"package": "scraper", "level": 1, "price": 1.6}],
                    "unblocker": [{"package": "web_unlocker", "level": 1, "price": 1.3}],
                }
            ),
        )
    )
    res = client.scraper.universal.unit()
    assert res.scraper[0].price == 1.6
    assert res.unblocker[0].price == 1.3


@respx.mock
def test_unblocker_countries_general_host(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy/unblocker_area").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "continent": {"1": "Asia"},
                    "country": [
                        {
                            "continent": "Asia",
                            "continent_code": 1,
                            "list": [{"code": "jp", "name_en": "Japan"}],
                        }
                    ],
                }
            ),
        )
    )
    res = client.scraper.unblocker.countries()
    assert route.called
    assert res.country[0].list[0].code == "jp"


@respx.mock
def test_unblocker_cities_validation(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.scraper.unblocker.cities("", "")
    assert set(exc.value.fields) == {"code", "region"}


@respx.mock
def test_browser_countries_raw_and_flow_use(client: Client) -> None:
    respx.post("http://base.test/v1/proxy/browser_area").mock(
        return_value=httpx.Response(200, text=envelope({"x": 1}))
    )
    assert client.scraper.browser.countries() == {"x": 1}

    respx.post("http://base.test/v1/browser_flow/browser_flow_use").mock(
        return_value=httpx.Response(200, text=envelope({"list": [{"id": 1, "use": 92295}]}))
    )
    fl = client.scraper.browser.flow_use("2025-01-01 00:00:00", "2025-01-02 00:00:00")
    assert fl.list[0].use == 92295

    with pytest.raises(ValidationError):
        client.scraper.browser.flow_use("", "")
