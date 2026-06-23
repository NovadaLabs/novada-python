"""Wallet example.

Set NOVADA_API_KEY in the environment and run:

    python examples/wallet.py
"""

from __future__ import annotations

from novada import APIError, Client
from novada.wallet.types import UsageRecordParams


def main() -> None:
    with Client() as client:  # reads NOVADA_API_KEY
        try:
            balance = client.wallet.balance()
            print(f"wallet balance = {balance.balance}")

            records = client.wallet.usage_record(UsageRecordParams(page=1, limit=10))
            print(f"usage records (count={records.count}):")
            for rec in records.list:
                print(f"  {rec.order_id}: {rec.description} ({rec.money})")
        except APIError as err:
            print(f"api error: {err}")


if __name__ == "__main__":
    main()
