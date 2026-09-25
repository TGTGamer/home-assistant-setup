# ------------------------------------------------------------------------------
# File: tests/oled_status/test_pages.py
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

from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from oled_status import icons, preview, rotation
from oled_status.pages import PAGES, Frame
from oled_status.pages.ambient import star_positions
from oled_status.pages.common import HEIGHT, WIDTH, fit, text_width
from oled_status.render import render
from oled_status.settings import Settings


@pytest.mark.parametrize("name", sorted(preview.frames()))
def test_every_sample_page_draws_something(name: str) -> None:
    frame = preview.frames()[name]
    page = "alert" if name.startswith("alert") else name
    image = render(page, frame)
    assert image.size == (WIDTH, HEIGHT)
    assert image.getbbox() is not None, f"{name} drew nothing"


@pytest.mark.parametrize("name", sorted(PAGES))
def test_pages_survive_an_empty_house(name: str) -> None:
    empty = replace(
        preview.sample(),
        people=(),
        locks=(),
        heating=None,
        bins=(),
        media=None,
        weather=None,
        ups=None,
        lights_on=(),
    )
    frame = Frame(empty)
    if PAGES[name].relevant(frame):
        render(name, frame)


def test_icons_are_square_and_draw() -> None:
    for name in icons.names():
        image = Image.new("1", (icons.SIZE, icons.SIZE))
        icons.draw_icon(ImageDraw.Draw(image), name, 0, 0)
        assert image.getbbox() is not None, name
    assert set(icons.WEATHER_ICONS.values()) <= set(icons.names())


def test_fit_shortens_to_width() -> None:
    text = fit("A very long front door name indeed", 11, 60)
    assert text.endswith("...")
    assert text_width(text, 11) <= 60
    assert fit("Gate", 11, 60) == "Gate"


def test_starfield_moves_and_stays_on_screen() -> None:
    first, later = star_positions(0), star_positions(10)
    assert first != later
    assert all(0 <= x < WIDTH and 0 <= y < HEIGHT for x, y, _ in first + later)


def test_rotation_skips_irrelevant_pages_and_interleaves_alerts() -> None:
    settings = Settings(pages=("clock", "media", "locks"), page_seconds=5)
    snapshot = replace(preview.sample(), media=None)
    quiet = Frame(snapshot)
    assert rotation.sequence(settings, quiet) == ["clock", "locks"]
    assert rotation.choose(settings, quiet, 0) == "clock"
    assert rotation.choose(settings, quiet, 5) == "locks"
    assert rotation.choose(settings, quiet, 10) == "clock"
    frames = preview.frames()
    assert rotation.sequence(settings, frames["alert"]) == [
        "alert",
        "clock",
        "alert",
        "media",
        "alert",
        "locks",
    ]


def test_rotation_falls_back_to_clock_and_can_go_dark() -> None:
    settings = Settings(pages=("media",), screen_off_at_night=True)
    snapshot = replace(preview.sample(), media=None)
    assert rotation.choose(settings, Frame(snapshot), 0) == "clock"
    assert rotation.choose(settings, Frame(replace(snapshot, night=True)), 0) is None


def test_preview_writes_contact_sheet(tmp_path: Path) -> None:
    written = preview.write(tmp_path)
    assert tmp_path / "all.png" in written
    assert all(path.exists() for path in written)
