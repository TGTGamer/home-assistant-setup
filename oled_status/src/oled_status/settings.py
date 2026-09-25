# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/settings.py
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

"""App options, read from the Supervisor's options file or a local JSON file."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import time
from pathlib import Path
from typing import Final

OPTIONS_PATH: Final = Path("/data/options.json")
DEFAULT_PAGES: Final = (
    "clock",
    "weather",
    "people",
    "locks",
    "heating",
    "bins",
    "media",
    "ups",
    "mood",
    "starfield",
)
_TIME = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class SettingsError(ValueError):
    """Raised when an option is missing or malformed."""


@dataclass(frozen=True)
class Settings:
    """Everything the display loop needs to know about its setup.

    Entity lists are Home Assistant entity IDs. An empty list or blank string
    turns the matching page or alert off, so the app runs before any entity
    is configured.
    """

    i2c_port: int = 1
    i2c_address: int = 0x3C
    rotate: int = 0
    contrast: int = 255
    night_contrast: int = 8
    night_start: time = time(23, 0)
    night_end: time = time(7, 0)
    screen_off_at_night: bool = False
    page_seconds: int = 8
    refresh_seconds: int = 5
    pages: tuple[str, ...] = DEFAULT_PAGES
    weather: str = ""
    climate: str = ""
    media_player: str = ""
    ups_battery: str = ""
    ups_charging: str = ""
    persons: tuple[str, ...] = ()
    locks: tuple[str, ...] = ()
    bins: tuple[str, ...] = ()
    leak_sensors: tuple[str, ...] = ()
    ignored_lights: tuple[str, ...] = field(default=())


def _time(raw: object, key: str) -> time:
    """Parse `HH:MM` into a time, naming `key` in the error."""
    if not isinstance(raw, str) or not (match := _TIME.match(raw)):
        raise SettingsError(f"{key} must be HH:MM, got {raw!r}")
    return time(int(match.group(1)), int(match.group(2)))


def _int(raw: object, key: str, low: int, high: int) -> int:
    """Accept a whole number in `low..high`; booleans are rejected."""
    if isinstance(raw, bool) or not isinstance(raw, int) or not low <= raw <= high:
        raise SettingsError(f"{key} must be a whole number from {low} to {high}, got {raw!r}")
    return raw


def _bool(raw: object, key: str) -> bool:
    """Accept only a real JSON boolean; the string "false" is an error, not True."""
    if not isinstance(raw, bool):
        raise SettingsError(f"{key} must be true or false, got {raw!r}")
    return raw


def _str(raw: object, key: str) -> str:
    """Accept text (or nothing), trimmed."""
    if raw is None:
        return ""
    if not isinstance(raw, str):
        raise SettingsError(f"{key} must be text, got {raw!r}")
    return raw.strip()


def _list(raw: object, key: str) -> tuple[str, ...]:
    """Accept a list of text, trimmed, with blank entries dropped."""
    if raw is None:
        return ()
    if not isinstance(raw, list) or not all(isinstance(item, str) for item in raw):
        raise SettingsError(f"{key} must be a list of text, got {raw!r}")
    return tuple(item.strip() for item in raw if item.strip())


def parse(raw: dict[str, object]) -> Settings:
    """Validate raw options into Settings, using defaults for anything absent."""
    base = Settings()
    address = raw.get("i2c_address", "0x3C")
    if not isinstance(address, str) or not re.fullmatch(r"0x[0-9a-fA-F]{2}", address):
        raise SettingsError(f"i2c_address must look like 0x3C, got {address!r}")
    pages = _list(raw.get("pages"), "pages") or base.pages
    from oled_status.pages import PAGES  # local import: pages import settings

    unknown = [name for name in pages if name not in PAGES]
    if unknown:
        raise SettingsError(f"unknown pages {unknown}; choose from {sorted(PAGES)}")
    return Settings(
        i2c_port=_int(raw.get("i2c_port", base.i2c_port), "i2c_port", 0, 20),
        i2c_address=int(address, 16),
        rotate=_int(raw.get("rotate", base.rotate), "rotate", 0, 3),
        contrast=_int(raw.get("contrast", base.contrast), "contrast", 0, 255),
        night_contrast=_int(
            raw.get("night_contrast", base.night_contrast), "night_contrast", 0, 255
        ),
        night_start=_time(raw.get("night_start", "23:00"), "night_start"),
        night_end=_time(raw.get("night_end", "07:00"), "night_end"),
        screen_off_at_night=_bool(raw.get("screen_off_at_night", False), "screen_off_at_night"),
        page_seconds=_int(raw.get("page_seconds", base.page_seconds), "page_seconds", 2, 120),
        refresh_seconds=_int(
            raw.get("refresh_seconds", base.refresh_seconds), "refresh_seconds", 1, 300
        ),
        pages=pages,
        weather=_str(raw.get("weather"), "weather"),
        climate=_str(raw.get("climate"), "climate"),
        media_player=_str(raw.get("media_player"), "media_player"),
        ups_battery=_str(raw.get("ups_battery"), "ups_battery"),
        ups_charging=_str(raw.get("ups_charging"), "ups_charging"),
        persons=_list(raw.get("persons"), "persons"),
        locks=_list(raw.get("locks"), "locks"),
        bins=_list(raw.get("bins"), "bins"),
        leak_sensors=_list(raw.get("leak_sensors"), "leak_sensors"),
        ignored_lights=_list(raw.get("ignored_lights"), "ignored_lights"),
    )


def load(path: Path = OPTIONS_PATH) -> Settings:
    """Read and validate the options file; a missing file means all defaults."""
    if not path.exists():
        return parse({})
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise SettingsError(f"{path} must hold a JSON object")
    return parse(data)
