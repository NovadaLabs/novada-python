"""Integration tests that hit the live Novada API.

These are skipped unless NOVADA_API_KEY is set, and are marked ``integration``
so they can be selected/deselected explicitly:

    pytest -m integration      # run only these
    pytest -m "not integration"  # skip these (also skipped automatically
                                 # when NOVADA_API_KEY is unset)
"""

from __future__ import annotations

import os

import pytest

from novada import Client, Product
from novada.proxy.types import ListWhitelistParams

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not os.environ.get("NOVADA_API_KEY"),
        reason="NOVADA_API_KEY not set",
    ),
]


def test_whitelist_list_live() -> None:
    with Client() as client:
        result = client.proxy.whitelist.list(ListWhitelistParams(product=Product.RESIDENTIAL))
        assert result.total >= 0


def test_wallet_balance_live() -> None:
    with Client() as client:
        balance = client.wallet.balance()
        assert balance.balance >= 0
