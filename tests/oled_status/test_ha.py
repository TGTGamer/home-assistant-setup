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

import pytest

from oled_status.ha import SUPERVISOR_URL, HomeAssistant, safe_for_token


@pytest.mark.parametrize(
    ("url", "safe"),
    [
        ("https://ha.example.org", True),
        ("https://192.168.1.10:8123", True),
        ("http://localhost:8123", True),
        ("http://127.0.0.1:8123", True),
        ("http://[::1]:8123", True),
        ("http://homeassistant.local:8123", False),
        ("http://192.168.1.10:8123", False),
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
