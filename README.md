# novada-python

[![CI](https://github.com/NovadaLabs/novada-python/actions/workflows/ci.yml/badge.svg)](https://github.com/NovadaLabs/novada-python/actions/workflows/ci.yml)

Python SDK for the [Novada](https://novada.com) API — proxy management, scraping, and wallet endpoints. Single runtime dependency (`httpx`), fully typed, Python 3.9+.

## Install

```sh
pip install novada
```

## Quick start

```python
from novada import Client, Product
from novada.proxy.types import ListWhitelistParams

client = Client("YOUR_API_KEY")  # or "" to read NOVADA_API_KEY

result = client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))
print("whitelist total =", result.total)
```

`Client` is a context manager and owns an `httpx.Client`; use `with Client(...) as client:` (or call `client.close()`) to release the connection pool when you are done.

## The three base URLs

Novada serves requests from **three** hosts. All are configurable and default to production:

| Purpose       | Default                          | Used by |
|---------------|----------------------------------|---------|
| General       | `https://api-m.novada.com`       | Every `/v1/*` endpoint (proxy, wallet, and the scraper area/balance/unit queries) |
| Web Unblocker | `https://webunlocker.novada.com` | `scraper.unblocker.scrape` (typed), or `scraper.do` with `target=Target.WEB_UNBLOCKER` |
| Scraper API   | `https://scraper.novada.com`     | `scraper.do` / `scraper.api.*` with `target=Target.SCRAPER_API` |

Only the scrape `POST /request` calls go to the Web Unblocker / Scraper API hosts; everything else (`/v1/*`) uses the general host.

```python
client = Client(
    "API_KEY",
    base_url="https://api-m.novada.com",
    web_unblocker_url="https://webunlocker.novada.com",
    scraper_url="https://scraper.novada.com",
    timeout=30.0,
    max_retries=2,
)
```

The Bearer API key is injected on every request. Retries apply only to network errors and HTTP 429/5xx — **never** to a non-zero business code.

## Proxy

```python
from novada.proxy.types import (
    AddWhitelistParams, CreateAccountParams, ListAccountParams,
    ListWhitelistParams, OpenStaticISPParams, ListStaticParams, TimeRange,
)

# Sub-accounts
client.proxy.account.create(CreateAccountParams(
    product=Product.RESIDENTIAL, account="account11", password="pass11", status=1,
))
client.proxy.account.list(ListAccountParams(product=Product.RESIDENTIAL))

# Whitelist
client.proxy.whitelist.add(AddWhitelistParams(product=Product.RESIDENTIAL, ip="10.10.10.1", remark="test"))
client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))

# Residential areas & traffic
client.proxy.residential.countries()
client.proxy.residential.balance()
client.proxy.residential.consume_log(TimeRange(start="2025-01-01 00:00:00", end="2025-01-31 23:59:59"))

# Static ISP / dedicated datacenter
client.proxy.static_isp.open(OpenStaticISPParams(ip_type="normal", region="hk:1|us-va:2", duration="week", num=3))
client.proxy.dedicated_dc.list(ListStaticParams())
```

Sub-services: `account`, `whitelist`, `residential`, `mobile`, `rotating_isp`, `rotating_dc`, `static_isp`, `dedicated_dc`, `unlimited`, `prohibit_domain`. Required parameters are validated client-side and raised as a `ValidationError` before any request is sent.

## Scraper

```python
from novada import Target
from novada.scraper import Request
from novada.scraper.types import GoogleSearchParams, UnblockerParams, YouTubeVideoParams

# Strongly typed (auto-selects the Scraper API host)
res = client.scraper.api.youtube.video_post(
    YouTubeVideoParams(url="https://www.youtube.com/watch?v=HAwTwmzgNc4")
)

# Google Search (SerpApi) — typed params, structured result (data.json is the raw result array)
gs = client.scraper.api.google.search(GoogleSearchParams(query="apple", country="us"))
print(gs.code, gs.cost_time, gs.data.json)

# Generic driver — any scraper_id, choose the host explicitly
res = client.scraper.do(Request(
    target=Target.SCRAPER_API,  # or Target.WEB_UNBLOCKER
    scraper_name="youtube.com",
    scraper_id="youtube_video-post_explore",
    params=[{"url": "https://www.youtube.com/watch?v=HAwTwmzgNc4"}],
    return_errors=True,
))
print(res.raw)  # raw scrape result (JSON/CSV/XLSX, depending on scraper)

# Web Unblocker — typed scrape; returns a structured result, not raw text
unb = client.scraper.unblocker.scrape(UnblockerParams(
    target_url="https://www.google.com",  # required
    country="us",                          # response_format defaults to "html"
))
print(unb.code, len(unb.html), unb.use_balance)

# Query endpoints on the general host
client.scraper.universal.balance()    # /v1/capture/get_balance
client.scraper.universal.unit()       # /v1/capture/unit
client.scraper.unblocker.countries()  # /v1/proxy/unblocker_area
client.scraper.browser.countries()    # /v1/proxy/browser_area
```

`scraper.do` marshals `params` to JSON, places it in the `scraper_params` form field, URL-encodes the body, and routes to the host selected by `target`. Scrape responses are returned raw because their format varies by scraper. `scraper.unblocker.scrape` is the dedicated Web Unblocker call: it sends the endpoint's own fields (`target_url`, `response_format`, `js_render`, `country`, `wait_ms`, …) and decodes the JSON envelope into an `UnblockerResult` (`html`, `code`, `msg`, `msg_detail`, `use_balance`).

## Wallet

```python
from novada.wallet.types import UsageRecordParams

client.wallet.balance()
client.wallet.usage_record(UsageRecordParams(page=1, limit=20))
```

## Error handling

Management endpoints return a uniform envelope `{code, data, msg, timestamp}`; **only `code == 0` is success**. A non-zero code or a non-2xx HTTP status is raised as an `APIError` (with `AuthError` / `RateLimitError` subclasses).

```python
from novada import APIError, AuthError, RateLimitError, ValidationError

try:
    client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))
except AuthError:        # HTTP 401/403
    print("invalid API key")
except RateLimitError:   # HTTP 429
    print("rate limited")
except APIError as err:  # business code != 0, or other HTTP error
    print(f"api error code={err.code} http={err.http_status}: {err.message}")
except ValidationError as err:  # missing required params (raised before the request)
    print(f"missing fields: {err.fields}")
```

The Go-style helpers `is_auth_error(err)`, `is_rate_limited(err)` and `code_of(err)` are also available for callers that prefer predicate checks over `except` clauses.

## Examples

Runnable examples live in [`examples/`](examples/): [`proxy.py`](examples/proxy.py), [`scraper.py`](examples/scraper.py), [`wallet.py`](examples/wallet.py). Set `NOVADA_API_KEY` and run e.g. `python examples/proxy.py`.

## License

[MIT](LICENSE)
