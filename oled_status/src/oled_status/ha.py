# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/ha.py
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

"""Minimal read-only Home Assistant REST client."""

from __future__ import annotations

import ipaddress
import json
import os
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Final

SUPERVISOR_URL: Final = "http://supervisor/core/api"


def safe_for_token(url: str) -> bool:
    """True when a bearer token may be sent to `url` without crossing a network in clear.

    HTTPS is always fine. Plain HTTP is only allowed to this machine (localhost
    or a loopback address), for example through an SSH tunnel. The Supervisor's
    internal `http://supervisor` URL is handled separately and never comes
    from user input.
    """
    parts = urllib.parse.urlsplit(url)
    if parts.scheme == "https":
        return bool(parts.hostname)
    if parts.scheme != "http" or not parts.hostname:
        return False
    if parts.hostname == "localhost":
        return True
    try:
        return ipaddress.ip_address(parts.hostname).is_loopback
    except ValueError:
        return False


@dataclass(frozen=True)
class State:
    """One entity's state as returned by `GET /api/states`."""

    entity_id: str
    state: str
    attributes: dict[str, object]

    @property
    def name(self) -> str:
        """Friendly name, falling back to the object ID made readable."""
        friendly = self.attributes.get("friendly_name")
        if isinstance(friendly, str) and friendly:
            return friendly
        return self.entity_id.split(".", 1)[-1].replace("_", " ").title()

    def number(self, attribute: str | None = None) -> float | None:
        """The state (or an attribute) as a float, or None if it isn't numeric."""
        raw = self.state if attribute is None else self.attributes.get(attribute)
        if isinstance(raw, bool):
            return None
        if isinstance(raw, int | float):
            return float(raw)
        if isinstance(raw, str):
            try:
                return float(raw)
            except ValueError:
                return None
        return None


States = dict[str, State]


def parse_states(payload: object) -> States:
    """Turn the JSON list from `/api/states` into a lookup by entity ID."""
    if not isinstance(payload, list):
        raise ValueError("expected a JSON list of states")
    states: States = {}
    for item in payload:
        if not isinstance(item, dict):
            continue
        entity_id, state = item.get("entity_id"), item.get("state")
        attributes = item.get("attributes")
        if isinstance(entity_id, str) and isinstance(state, str):
            states[entity_id] = State(
                entity_id, state, attributes if isinstance(attributes, dict) else {}
            )
    return states


class HomeAssistant:
    """Fetches every entity state in one request.

    Inside the app it uses the Supervisor proxy and `SUPERVISOR_TOKEN`. For
    local development set `HA_URL` (an `https://` URL, or `http://localhost`
    through an SSH tunnel) and `HA_TOKEN` (a long-lived access token).
    """

    def __init__(self, base_url: str, token: str, timeout: float = 10.0) -> None:
        """Target `base_url` (ending in `/api`) with a bearer `token`."""
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout

    @classmethod
    def from_environment(cls) -> HomeAssistant:
        """Build a client from the app or development environment variables."""
        if token := os.environ.get("SUPERVISOR_TOKEN"):
            return cls(SUPERVISOR_URL, token)
        url, token = os.environ.get("HA_URL"), os.environ.get("HA_TOKEN")
        if not url or not token:
            raise RuntimeError("set SUPERVISOR_TOKEN (inside HA) or HA_URL and HA_TOKEN")
        if not safe_for_token(url):
            raise RuntimeError(
                "HA_URL must be https://, or http:// to localhost through a tunnel, "
                "so the token is never sent in clear text"
            )
        return cls(f"{url.rstrip('/')}/api", token)

    def states(self) -> States:
        """Return all entity states."""
        # The URL is always http(s): it comes from SUPERVISOR_URL or HA_URL.
        request = urllib.request.Request(  # noqa: S310
            f"{self._base_url}/states",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        with urllib.request.urlopen(request, timeout=self._timeout) as response:  # noqa: S310
            return parse_states(json.load(response))
