"""Scraper example.

Set NOVADA_API_KEY in the environment and run:

    python examples/scraper.py
"""

from __future__ import annotations

from novada import APIError, Client
from novada.scraper.types import GoogleSearchParams, UnblockerParams


def main() -> None:
    with Client() as client:  # reads NOVADA_API_KEY
        try:
            # Google Search (SerpApi) — structured result.
            gs = client.scraper.api.google.search(GoogleSearchParams(query="apple", country="us"))
            print(f"google: code={gs.code} cost_time={gs.cost_time}ms")

            # Web Unblocker — typed scrape.
            unb = client.scraper.unblocker.scrape(
                UnblockerParams(target_url="https://www.google.com", country="us")
            )
            print(f"unblocker: code={unb.code} html_len={len(unb.html)} cost={unb.use_balance}")

            # Query endpoint on the general host.
            balance = client.scraper.universal.balance()
            print(f"scraper balance = {balance.scraper_balance}")
        except APIError as err:
            print(f"api error: {err}")


if __name__ == "__main__":
    main()
