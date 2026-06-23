"""M2 acceptance: the remaining proxy sub-services — encoding, decoding,
raw export streams, and shared helpers."""

from __future__ import annotations

import httpx
import pytest
import respx

from novada import Client, ValidationError
from novada.proxy.types import (
    CityParams,
    DeleteProhibitParams,
    ExportStaticParams,
    ListStaticParams,
    MobileUseParams,
    OpenDedicatedDCParams,
    OpenStaticISPParams,
    RenewSettingParams,
    RenewStaticParams,
    TimeRange,
)

from .conftest import envelope, parse_multipart


@respx.mock
def test_residential_countries_decode(client: Client) -> None:
    respx.post("http://base.test/v1/proxy/domestic_dynamic_area").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {
                    "continent": {"1": "Asia"},
                    "country": [
                        {
                            "continent": "Asia",
                            "continent_code": 1,
                            "list": [{"code": "jp", "name_en": "Japan", "ip_num": 5}],
                        }
                    ],
                }
            ),
        )
    )
    res = client.proxy.residential.countries()
    assert res.continent == {"1": "Asia"}
    assert res.country[0].list[0].code == "jp"
    assert res.country[0].list[0].ip_num == 5


@respx.mock
def test_residential_cities_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/proxy/region_by_city").mock(
        return_value=httpx.Response(200, text=envelope({"data": [{"code": "x"}]}))
    )
    res = client.proxy.residential.cities(CityParams(code="us", region="alabama"))
    assert parse_multipart(route.calls.last.request) == {"code": "us", "region": "alabama"}
    assert res.data[0].code == "x"


@respx.mock
def test_residential_consume_log_validation(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.proxy.residential.consume_log(TimeRange(start="", end=""))
    assert set(exc.value.fields) == {"start_time", "end_time"}


@respx.mock
def test_residential_consume_log_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/residential_flow/consume_log").mock(
        return_value=httpx.Response(200, text=envelope({"list": [{"id": 1, "use": 99}]}))
    )
    res = client.proxy.residential.consume_log(
        TimeRange(start="2025-01-01 00:00:00", end="2025-01-31 23:59:59")
    )
    fields = parse_multipart(route.calls.last.request)
    assert fields["start_time"] == "2025-01-01 00:00:00"
    assert res.list[0].use == 99


@respx.mock
def test_mobile_consume_log_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/mobile_flow/mobile_flow_use").mock(
        return_value=httpx.Response(200, text=envelope({"list": []}))
    )
    client.proxy.mobile.consume_log(
        MobileUseParams(start="2025-01-01 00:00:00", end="2025-01-02 00:00:00", granularity="2")
    )
    fields = parse_multipart(route.calls.last.request)
    assert fields["day_or_hour"] == "2"


@respx.mock
def test_mobile_countries_returns_raw(client: Client) -> None:
    respx.post("http://base.test/v1/proxy/mobile_area").mock(
        return_value=httpx.Response(200, text=envelope({"any": [1, 2]}))
    )
    assert client.proxy.mobile.countries() == {"any": [1, 2]}


@respx.mock
def test_rotating_isp_countries(client: Client) -> None:
    respx.post("http://base.test/v1/proxy/isp_data_area").mock(
        return_value=httpx.Response(200, text=envelope({"country": [{"code": "us", "node": "n1"}]}))
    )
    res = client.proxy.rotating_isp.countries()
    assert res.country[0].node == "n1"


@respx.mock
def test_rotating_dc_countries_nested_city(client: Client) -> None:
    respx.post("http://base.test/v1/proxy/dynamic_data_area").mock(
        return_value=httpx.Response(
            200,
            text=envelope({"country": [{"id": 3, "code": "hk", "city": {"code": "hk-1"}}]}),
        )
    )
    res = client.proxy.rotating_dc.countries()
    assert res.country[0].city.code == "hk-1"


@respx.mock
def test_rotating_dc_consume_log_path(client: Client) -> None:
    route = respx.post("http://base.test/v1/dc_flow/consume_log").mock(
        return_value=httpx.Response(200, text=envelope({"list": []}))
    )
    client.proxy.rotating_dc.consume_log(
        TimeRange(start="2025-01-01 00:00:00", end="2025-01-02 00:00:00")
    )
    assert route.called


@respx.mock
def test_static_isp_open_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/static_house/open").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.static_isp.open(
        OpenStaticISPParams(ip_type="normal", region="hk:1|us-va:2", duration="week", num=3)
    )
    assert parse_multipart(route.calls.last.request) == {
        "ip_type": "normal",
        "region": "hk:1|us-va:2",
        "duration": "week",
        "num": "3",
    }


@respx.mock
def test_static_isp_list_defaults_and_decode(client: Client) -> None:
    route = respx.post("http://base.test/v1/static_house/list").mock(
        return_value=httpx.Response(
            200,
            text=envelope(
                {"list": [{"id": 1, "ip": "1.1.1.1", "port": "8000"}], "page": 1, "total": 1}
            ),
        )
    )
    res = client.proxy.static_isp.list(ListStaticParams())
    fields = parse_multipart(route.calls.last.request)
    assert fields["page"] == "1"
    assert fields["limit"] == "10"
    assert res.list[0].ip == "1.1.1.1"


@respx.mock
def test_static_isp_export_returns_raw_bytes(client: Client) -> None:
    # The export endpoint returns a CSV file stream, not the JSON envelope.
    respx.post("http://base.test/v1/static_house/export").mock(
        return_value=httpx.Response(200, text="ip,port\n1.1.1.1,8000\n")
    )
    raw = client.proxy.static_isp.export(ExportStaticParams(status="1"))
    assert raw == b"ip,port\n1.1.1.1,8000\n"


@respx.mock
def test_static_isp_region_decode(client: Client) -> None:
    respx.post("http://base.test/v1/static_house/region").mock(
        return_value=httpx.Response(
            200,
            text=envelope({"list": {"Asia-Pacific": [{"node": "HK", "param": 1}]}}),
        )
    )
    res = client.proxy.static_isp.region("isp-resi")
    assert res.list["Asia-Pacific"][0].node == "HK"


@respx.mock
def test_static_isp_renew_setting_fields(client: Client) -> None:
    route = respx.post("http://base.test/v1/static_house/renew_setting").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.static_isp.renew_setting(
        RenewSettingParams(ids="100,111", package_type="week", status=1, renew_type=2)
    )
    fields = parse_multipart(route.calls.last.request)
    assert fields["type"] == "static_house"
    assert fields["ids"] == "100,111"
    assert fields["status"] == "1"
    assert fields["renew_type"] == "2"


@respx.mock
def test_dedicated_dc_open_and_renew(client: Client) -> None:
    open_route = respx.post("http://base.test/v1/static/open").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.dedicated_dc.open(
        OpenDedicatedDCParams(region="hk:1|tw:2", duration="month", num=2)
    )
    assert parse_multipart(open_route.calls.last.request) == {
        "region": "hk:1|tw:2",
        "duration": "month",
        "num": "2",
    }

    renew_route = respx.post("http://base.test/v1/static/renew").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.dedicated_dc.renew(RenewStaticParams(ips="1.1.1.1", duration="week"))
    fields = parse_multipart(renew_route.calls.last.request)
    assert fields["renew_ip_list"] == "1.1.1.1"


@respx.mock
def test_dedicated_dc_renew_setting_type(client: Client) -> None:
    route = respx.post("http://base.test/v1/static/renew_setting").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.dedicated_dc.renew_setting(
        RenewSettingParams(ids="1", package_type="week", status=1, renew_type=1)
    )
    assert parse_multipart(route.calls.last.request)["type"] == "static"


@respx.mock
def test_unlimited_hosts_defaults(client: Client) -> None:
    route = respx.post("http://base.test/v1/unlimited/host_list").mock(
        return_value=httpx.Response(
            200, text=envelope({"list": [{"id": 7, "host": "h1"}], "page": 1, "total": 1})
        )
    )
    res = client.proxy.unlimited.hosts()
    fields = parse_multipart(route.calls.last.request)
    assert fields == {"page": "1", "limit": "10"}
    assert res.list[0].host == "h1"


@respx.mock
def test_prohibit_domain_add_list_delete(client: Client) -> None:
    add_route = respx.post("http://base.test/v1/prohibit_domain/add").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.prohibit_domain.add("example.com")
    assert parse_multipart(add_route.calls.last.request) == {"address": "example.com"}

    list_route = respx.post("http://base.test/v1/prohibit_domain/list").mock(
        return_value=httpx.Response(
            200, text=envelope({"list": [{"id": 1, "address": "x.com"}], "total": 1})
        )
    )
    res = client.proxy.prohibit_domain.list()
    assert list_route.called
    assert res.list[0].address == "x.com"

    del_route = respx.post("http://base.test/v1/prohibit_domain/del").mock(
        return_value=httpx.Response(200, text=envelope(None))
    )
    client.proxy.prohibit_domain.delete(DeleteProhibitParams(all=True))
    assert parse_multipart(del_route.calls.last.request) == {"is_all": "1"}


def test_prohibit_domain_delete_requires_id_when_not_all(client: Client) -> None:
    with pytest.raises(ValidationError) as exc:
        client.proxy.prohibit_domain.delete(DeleteProhibitParams())
    assert exc.value.fields == ["id"]


@pytest.mark.parametrize(
    "call",
    [
        lambda c: c.proxy.static_isp.open(
            OpenStaticISPParams(ip_type="", region="", duration="", num=0)
        ),
        lambda c: c.proxy.dedicated_dc.open(OpenDedicatedDCParams(region="", duration="", num=0)),
        lambda c: c.proxy.mobile.consume_log(MobileUseParams(start="", end="", granularity="")),
    ],
)
def test_proxy_validation_prevents_request(client: Client, call) -> None:  # type: ignore[no-untyped-def]
    with pytest.raises(ValidationError):
        call(client)
