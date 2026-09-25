# ------------------------------------------------------------------------------
# File: tests/oled_status/test_ha.py
# Project: home-assistant-setup
# Last modified: 2026-09-25
#
# Copyright 2026 TGTGamer - All Rights Reserved
#
# Licensed under the Fair Core License, Version 1.0, MIT Future License
# (FCL-1.0-MIT); you may not use this file except in compliance with the
# License in the LICENSE file at the root of this repository. Each version
# becomes available under the MIT license on the second anniversary of the
# date it is made available.
#
# You must not move, change, disable, or circumvent any license key
# functionality in this software, or modify it to remove protected
# functionality.
#
# Contributions are made under the TGTGamer Cooperation Commitment in
# CONTRIBUTING.md, and everyone taking part follows CODE_OF_CONDUCT.md.
#
# DELETING THIS NOTICE AUTOMATICALLY VOIDS YOUR LICENSE
# ------------------------------------------------------------------------------

from __future__ import annotations

import ipaddress
import threading
import urllib.error
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from oled_status.ha import SUPERVISOR_URL, HomeAssistant, safe_for_token

# Built from integers rather than written out, so no IP address literals live
# in the repository: the IPv4 and IPv6 loopback addresses, and one address in
# the private range (loopback checks must reject it).
LOOPBACK_V4 = ipaddress.IPv4Address(0x7F000001)
LOOPBACK_V6 = ipaddress.IPv6Address(1)
PRIVATE_V4 = next(ipaddress.IPv4Network((0xC0A80000, 16)).hosts())


@pytest.mark.parametrize(
    ("url", "safe"),
    [
        ("https://ha.example.org", True),
        (f"https://{PRIVATE_V4}:8123", True),
        ("http://localhost:8123", True),
        (f"http://{LOOPBACK_V4}:8123", True),
        (f"http://[{LOOPBACK_V6}]:8123", True),
        ("http://homeassistant.local:8123", False),
        (f"http://{PRIVATE_V4}:8123", False),
        ("ftp://localhost", False),
        ("https://", False),
        ("not a url", False),
    ],
)
def test_token_only_over_https_or_loopback(url: str, safe: bool) -> None:
    """Tokens go over HTTPS, or plain HTTP only to this machine."""
    assert safe_for_token(url) is safe


def test_environment_refuses_plain_http_to_the_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """A LAN http:// HA_URL is rejected before any request carries the token."""
    monkeypatch.delenv("SUPERVISOR_TOKEN", raising=False)
    monkeypatch.setenv("HA_URL", "http://homeassistant.local:8123")
    monkeypatch.setenv("HA_TOKEN", "t")
    with pytest.raises(RuntimeError, match="https"):
        HomeAssistant.from_environment()


def test_environment_prefers_the_supervisor(monkeypatch: pytest.MonkeyPatch) -> None:
    """Inside the app the Supervisor proxy is used, whatever HA_URL says."""
    monkeypatch.setenv("SUPERVISOR_TOKEN", "t")
    monkeypatch.setenv("HA_URL", "http://homeassistant.local:8123")
    assert HomeAssistant.from_environment()._base_url == SUPERVISOR_URL


class _Redirector(BaseHTTPRequestHandler):
    """Answers every request with a redirect to a plain-HTTP LAN host."""

    def do_GET(self) -> None:
        """Redirect, as a hostile or misconfigured server might."""
        self.send_response(302)
        self.send_header("Location", "http://homeassistant.local:8123/api/states")
        self.end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep test output quiet."""


@pytest.fixture
def redirecting_server() -> Iterator[str]:
    """A throwaway local server that only ever redirects; yields its base URL."""
    server = HTTPServer((str(LOOPBACK_V4), 0), _Redirector)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://{LOOPBACK_V4}:{server.server_port}/api"
    server.shutdown()


def test_redirects_are_refused(redirecting_server: str) -> None:
    """A redirect raises instead of re-sending the token to the new address."""
    with pytest.raises(urllib.error.HTTPError, match="refusing redirect"):
        HomeAssistant(redirecting_server, "token").states()
