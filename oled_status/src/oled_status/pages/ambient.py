# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/pages/ambient.py
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

"""Always-on and fun pages: clock, weather, now playing, starfield, alerts."""

from __future__ import annotations

import random

from PIL import ImageDraw

from oled_status.alerts import Level
from oled_status.icons import WEATHER_ICONS, draw_icon
from oled_status.pages.common import (
    HEIGHT,
    TICKS_PER_SECOND,
    WIDTH,
    Frame,
    Page,
    centred,
    degrees,
    fit,
    font,
    marquee,
)

STAR_COUNT = 60
STAR_DEPTH = 32
STAR_SPREAD = 4


def _clock(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """Large time with a blinking colon, the date, and a weather icon in the corner."""
    now = frame.snapshot.now
    colon = ":" if frame.tick // TICKS_PER_SECOND % 2 == 0 else " "
    centred(draw, 4, now.strftime(f"%H{colon}%M"), 34)
    centred(draw, 46, now.strftime("%a %d %b"), 13)
    if weather := frame.snapshot.weather:
        draw_icon(draw, WEATHER_ICONS.get(weather.condition, "cloud"), WIDTH - 12, 0)


def _weather(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """Big condition icon, temperature and a readable condition name."""
    weather = frame.snapshot.weather
    if weather is None:
        return
    draw_icon(draw, WEATHER_ICONS.get(weather.condition, "cloud"), 2, 8, 3)
    draw.text((48, 6), degrees(weather.temperature), font=font(28), fill="white")
    label = weather.condition.replace("partlycloudy", "partly cloudy").replace("-", " ")
    draw.text((48, 44), fit(label.capitalize(), 12, WIDTH - 48), font=font(12), fill="white")


def _media(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """Now playing: scrolling title with the artist underneath."""
    media = frame.snapshot.media
    if media is None:
        return
    draw_icon(draw, "note", 0, 0)
    draw.text((16, -1), "Now playing", font=font(12), fill="white")
    draw.line((0, 14, WIDTH - 1, 14), fill="white")
    marquee(draw, 20, media.title, 16, frame.tick)
    if media.artist:
        centred(draw, 44, media.artist, 12)


def star_positions(tick: int) -> list[tuple[int, int, int]]:
    """Screen (x, y, size) of each star at `tick`; a pure function of time."""
    rng = random.Random(1337)  # noqa: S311 - decoration, not security
    stars: list[tuple[int, int, int]] = []
    for _ in range(STAR_COUNT):
        sx, sy = rng.uniform(-1, 1), rng.uniform(-1, 1)
        depth = STAR_DEPTH - (rng.uniform(0, STAR_DEPTH) + tick * 0.5) % STAR_DEPTH + 1
        x = int(WIDTH / 2 + sx * WIDTH / 2 * STAR_SPREAD / depth)
        y = int(HEIGHT / 2 + sy * HEIGHT / 2 * STAR_SPREAD / depth)
        if 0 <= x < WIDTH and 0 <= y < HEIGHT:
            stars.append((x, y, 2 if depth < STAR_DEPTH / 4 else 1))
    return stars


def _starfield(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """Stars flying towards the viewer; also moves every pixel against burn-in."""
    for x, y, size in star_positions(frame.tick):
        draw.rectangle((x, y, x + size - 1, y + size - 1), fill="white")


def _alert(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """The most urgent alert, flashing inverted when it is critical."""
    alert = frame.alerts[0]
    flash = alert.level is Level.CRITICAL and frame.tick // 5 % 2 == 1
    if flash:
        draw.rectangle((0, 0, WIDTH - 1, HEIGHT - 1), fill="white")
    colour = "black" if flash else "white"
    draw_icon(draw, alert.icon, 2, 4, 2, fill=colour)
    draw.text((32, 4), fit(alert.title, 14, WIDTH - 32), font=font(14), fill=colour)
    extra = f" (+{len(frame.alerts) - 1} more)" if len(frame.alerts) > 1 else ""
    draw.text((2, 34), fit(alert.detail, 12, WIDTH - 2), font=font(12), fill=colour)
    if extra:
        draw.text((2, 50), extra.strip(), font=font(10), fill=colour)


PAGES: dict[str, Page] = {
    "clock": Page(_clock, animated=True),
    "weather": Page(_weather, lambda frame: frame.snapshot.weather is not None),
    "media": Page(_media, lambda frame: frame.snapshot.media is not None, animated=True),
    "starfield": Page(_starfield, animated=True),
    "alert": Page(_alert, lambda frame: bool(frame.alerts), animated=True),
}
