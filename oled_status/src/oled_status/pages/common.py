# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/pages/common.py
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

"""Shared drawing helpers and the page contract."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from functools import cache

from PIL import ImageDraw, ImageFont

from oled_status.alerts import Alert
from oled_status.icons import draw_icon
from oled_status.snapshot import Snapshot

WIDTH = 128
HEIGHT = 64
TICKS_PER_SECOND = 10

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


@dataclass(frozen=True)
class Frame:
    """Everything a page may draw from. `tick` counts tenths of a second."""

    snapshot: Snapshot
    alerts: tuple[Alert, ...] = ()
    tick: int = 0


@dataclass(frozen=True)
class Page:
    """A named screen. `relevant` hides it when it has nothing to show."""

    draw: Callable[[ImageDraw.ImageDraw, Frame], None]
    relevant: Callable[[Frame], bool] = field(default=lambda _frame: True)
    animated: bool = False


@cache
def font(size: int) -> Font:
    """Pillow's bundled scalable font at `size` pixels."""
    return ImageFont.load_default(size=size)


def text_width(text: str, size: int) -> int:
    """Rendered width in pixels of `text` at `size`."""
    left, _top, right, _bottom = font(size).getbbox(text)
    return int(right - left)


def fit(text: str, size: int, width: int) -> str:
    """Shorten `text` with an ellipsis until it fits in `width` pixels."""
    if text_width(text, size) <= width:
        return text
    while text and text_width(f"{text}...", size) > width:
        text = text[:-1]
    return f"{text.rstrip()}..."


def centred(draw: ImageDraw.ImageDraw, y: int, text: str, size: int) -> None:
    """Draw `text` horizontally centred at height `y`, shortened to fit."""
    text = fit(text, size, WIDTH)
    draw.text(((WIDTH - text_width(text, size)) // 2, y), text, font=font(size), fill="white")


def header(draw: ImageDraw.ImageDraw, icon: str, title: str) -> None:
    """Icon and title across the top, with a rule underneath."""
    draw_icon(draw, icon, 0, 0)
    draw.text((16, -1), fit(title, 12, WIDTH - 16), font=font(12), fill="white")
    draw.line((0, 14, WIDTH - 1, 14), fill="white")


def marquee(draw: ImageDraw.ImageDraw, y: int, text: str, size: int, tick: int) -> None:
    """Draw text centred if it fits, otherwise scrolling right to left."""
    width = text_width(text, size)
    if width <= WIDTH:
        centred(draw, y, text, size)
        return
    gap = 32
    offset = (tick * 3) % (width + gap)
    for x in (-offset, width + gap - offset):
        draw.text((x, y), text, font=font(size), fill="white")


def days_label(days: int, short: bool = False) -> str:
    """Human label for days until a collection; `short` fits a table column."""
    if short:
        return {0: "Today", 1: "Tmrw"}.get(days, f"{days} days")
    return {0: "Today", 1: "Tomorrow"}.get(days, f"In {days} days")


def degrees(value: float | None) -> str:
    """Temperature with a degree sign, dropping a trailing `.0`; `--` if unknown."""
    return "--" if value is None else f"{value:.1f}".removesuffix(".0") + "°"
