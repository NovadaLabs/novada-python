"""Proxy management example.

Set NOVADA_API_KEY in the environment and run:

    python examples/proxy.py
"""

from __future__ import annotations

from novada import APIError, Client, Product
from novada.proxy.types import AddWhitelistParams, ListWhitelistParams


def main() -> None:
    with Client() as client:  # reads NOVADA_API_KEY
        try:
            client.proxy.whitelist.add(
                AddWhitelistParams(product=Product.RESIDENTIAL, ip="10.10.10.1", remark="example")
            )
            result = client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))
            print(f"whitelist total = {result.total}")
            for entry in result.list:
                print(f"  {entry.mark_ip} (id={entry.id}, locked={entry.lock})")
        except APIError as err:
            print(f"api error: {err}")


if __name__ == "__main__":
    main()
