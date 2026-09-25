# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/preview.py
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

"""Renders every page from made-up data, for docs and eyeballing changes."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PIL import Image

from oled_status import alerts
from oled_status.pages import PAGES, Frame
from oled_status.pages.common import HEIGHT, WIDTH
from oled_status.render import render
from oled_status.snapshot import Bin, Heating, Lock, Media, Person, Snapshot, Ups, Weather

SCALE = 3
GAP = 6


def sample() -> Snapshot:
    """A plausible evening at home, with something worth alerting on."""
    return Snapshot(
        now=datetime(2026, 9, 25, 21, 42),
        night=False,
        people=(Person("Me", home=True), Person("Partner", home=True)),
        locks=(Lock("Front door", "locked"), Lock("Back door", "unlocked"), Lock("Gate", "locked")),
        heating=Heating(current=19.5, target=21.0, active=True),
        bins=(Bin("Recycling", 1), Bin("General waste", 8), Bin("Garden", 15)),
        media=Media("Everybody Wants to Rule the World", "Tears for Fears"),
        weather=Weather("partlycloudy", 14.0, "°C"),
        ups=Ups(87.0, charging=True),
        lights_on=("Kitchen", "Lounge"),
    )


def frames() -> dict[str, Frame]:
    """One sample frame per page, plus a night alert and a flashing critical alert."""
    snapshot = sample()
    night = replace(snapshot, night=True)
    leak = replace(snapshot, leaks=("Kitchen sink",))
    return {
        **{name: Frame(snapshot, tuple(alerts.current(snapshot))) for name in PAGES},
        "alert": Frame(night, tuple(alerts.current(night))),
        "alert-critical": Frame(leak, tuple(alerts.current(leak)), tick=5),
    }


def write(out: Path) -> list[Path]:
    """Write one PNG per page plus `all.png`, a contact sheet of them all."""
    out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    images: list[Image.Image] = []
    for name, frame in frames().items():
        page = "alert" if name.startswith("alert") else name
        image = render(page, frame).convert("L")
        image = image.resize((WIDTH * SCALE, HEIGHT * SCALE), Image.Resampling.NEAREST)
        path = out / f"{name}.png"
        image.save(path)
        written.append(path)
        images.append(image)
    columns = 3
    rows = -(-len(images) // columns)
    tile_w, tile_h = WIDTH * SCALE + GAP, HEIGHT * SCALE + GAP
    sheet = Image.new("L", (columns * tile_w + GAP, rows * tile_h + GAP), color=60)
    for index, image in enumerate(images):
        sheet.paste(image, (GAP + index % columns * tile_w, GAP + index // columns * tile_h))
    sheet.save(out / "all.png")
    written.append(out / "all.png")
    return written
