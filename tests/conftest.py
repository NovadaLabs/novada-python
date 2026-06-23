"""Shared test fixtures and helpers."""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from novada import Client


@pytest.fixture
def client() -> Client:
    """A client pointed at deterministic test hosts with retries disabled."""
    return Client(
        "test-key",
        base_url="http://base.test",
        web_unblocker_url="http://unblock.test",
        scraper_url="http://scraper.test",
        max_retries=0,
    )


def envelope(data: Any, *, code: int = 0, msg: str = "success") -> str:
    """Build a uniform Novada response envelope as a JSON string."""
    return json.dumps({"code": code, "data": data, "msg": msg, "timestamp": 0})


def parse_multipart(request: httpx.Request) -> dict[str, str]:
    """Extract text fields from a multipart/form-data request body."""
    content_type = request.headers["content-type"]
    boundary = content_type.split("boundary=", 1)[1]
    body = request.content.decode("utf-8")
    fields: dict[str, str] = {}
    for part in body.split(f"--{boundary}"):
        part = part.strip("\r\n")
        if not part or part == "--":
            continue
        header, _, value = part.partition("\r\n\r\n")
        name = header.split('name="', 1)[1].split('"', 1)[0]
        fields[name] = value
    return fields
