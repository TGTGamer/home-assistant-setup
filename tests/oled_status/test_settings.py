# ------------------------------------------------------------------------------
# File: tests/oled_status/test_settings.py
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

import json
from datetime import time
from pathlib import Path

import pytest

from oled_status.settings import DEFAULT_PAGES, Settings, SettingsError, load, parse


def test_defaults_when_options_missing(tmp_path: Path) -> None:
    assert load(tmp_path / "missing.json") == Settings()


def test_parses_full_options(tmp_path: Path) -> None:
    path = tmp_path / "options.json"
    path.write_text(
        json.dumps(
            {
                "i2c_address": "0x3d",
                "rotate": 2,
                "night_start": "22:30",
                "night_end": "06:15",
                "pages": ["clock", "locks"],
                "locks": ["lock.front_door", " ", "lock.gate "],
                "climate": " climate.hall ",
            }
        )
    )
    settings = load(path)
    assert settings.i2c_address == 0x3D
    assert settings.rotate == 2
    assert settings.night_start == time(22, 30)
    assert settings.night_end == time(6, 15)
    assert settings.pages == ("clock", "locks")
    assert settings.locks == ("lock.front_door", "lock.gate")
    assert settings.climate == "climate.hall"


def test_empty_page_list_uses_defaults() -> None:
    assert parse({"pages": []}).pages == DEFAULT_PAGES


@pytest.mark.parametrize(
    ("options", "message"),
    [
        ({"i2c_address": "60"}, "i2c_address"),
        ({"rotate": 4}, "rotate"),
        ({"rotate": True}, "rotate"),
        ({"night_start": "7am"}, "night_start"),
        ({"pages": ["clock", "disco"]}, "unknown pages"),
        ({"locks": "lock.front"}, "locks"),
        ({"weather": 3}, "weather"),
    ],
)
def test_rejects_bad_options(options: dict[str, object], message: str) -> None:
    with pytest.raises(SettingsError, match=message):
        parse(options)


def test_rejects_non_object_file(tmp_path: Path) -> None:
    path = tmp_path / "options.json"
    path.write_text("[]")
    with pytest.raises(SettingsError):
        load(path)
