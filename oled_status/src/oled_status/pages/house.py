# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/pages/house.py
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

"""Pages about the home: people, locks, heating, bins and the UPS."""

from __future__ import annotations

from PIL import ImageDraw

from oled_status.icons import draw_icon
from oled_status.pages.common import (
    WIDTH,
    Frame,
    Page,
    days_label,
    degrees,
    fit,
    font,
    header,
    text_width,
)


def _people(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    people = frame.snapshot.people
    home = sum(person.home for person in people)
    header(draw, "person", f"Home: {home} of {len(people)}")
    column_width = WIDTH // max(1, min(len(people), 4))
    for index, person in enumerate(people[:4]):
        left = index * column_width
        draw_icon(draw, "person" if person.home else "away", left + column_width // 2 - 12, 18, 2)
        name = fit(person.name, 11, column_width - 2)
        draw.text((left + 1, 46), name, font=font(11), fill="white")


def _locks(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    locks = frame.snapshot.locks
    open_count = sum(not lock.secure for lock in locks)
    header(
        draw,
        "unlocked" if open_count else "locked",
        "All locked" if not open_count else f"{open_count} unlocked",
    )
    for row, lock in enumerate(locks[:3]):
        y = 17 + row * 16
        draw_icon(draw, "locked" if lock.secure else "unlocked", 0, y)
        state = lock.state.replace("_", " ").title()
        state_width = text_width(state, 11)
        draw.text((WIDTH - state_width, y - 1), state, font=font(11), fill="white")
        name = fit(lock.name, 11, WIDTH - 16 - state_width - 4)
        draw.text((16, y - 1), name, font=font(11), fill="white")


def _heating(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    heating = frame.snapshot.heating
    if heating is None:
        return
    header(draw, "flame", "Heating on" if heating.active else "Heating idle")
    if heating.active and frame.tick // 5 % 2:
        draw_icon(draw, "flame", 2, 22, 3)
    elif heating.active:
        draw_icon(draw, "flame", 2, 20, 3)
    draw.text((44, 16), degrees(heating.current), font=font(28), fill="white")
    draw.text((46, 49), f"Set to {degrees(heating.target)}", font=font(11), fill="white")


def _bins(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    bins = frame.snapshot.bins
    header(draw, "bin", f"Bins: {days_label(bins[0].days)}")
    for row, item in enumerate(bins[:3]):
        y = 17 + row * 15
        draw.text((0, y), fit(item.name, 11, 74), font=font(11), fill="white")
        label = days_label(item.days, short=True)
        draw.text((WIDTH - 50, y), fit(label, 11, 50), font=font(11), fill="white")


def _ups(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    ups = frame.snapshot.ups
    if ups is None:
        return
    source = {True: "Mains, charging", False: "On battery", None: "Power"}[ups.charging]
    header(draw, "plug" if ups.charging is not False else "battery", source)
    left, top, right, bottom = 4, 22, 84, 50
    draw.rectangle((left, top, right, bottom), outline="white")
    draw.rectangle((right + 1, top + 8, right + 4, bottom - 8), fill="white")
    filled = left + 2 + int((right - left - 4) * max(0.0, min(ups.percent, 100.0)) / 100)
    draw.rectangle((left + 2, top + 2, filled, bottom - 2), fill="white")
    draw.text((92, 26), f"{ups.percent:.0f}%", font=font(14), fill="white")


def _mood(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    worried = bool(frame.alerts)
    blink = frame.tick % 40 >= 38
    draw.ellipse((34, 2, 94, 62), outline="white", width=2)
    for eye_x in (52, 76):
        if blink:
            draw.line((eye_x - 4, 24, eye_x + 4, 24), fill="white", width=2)
        else:
            draw.ellipse((eye_x - 4, 19, eye_x + 4, 29), fill="white")
    if worried:
        draw.arc((48, 42, 80, 62), 200, 340, fill="white", width=2)
    else:
        draw.arc((46, 26, 82, 52), 20, 160, fill="white", width=2)


PAGES: dict[str, Page] = {
    "people": Page(_people, lambda frame: bool(frame.snapshot.people)),
    "locks": Page(_locks, lambda frame: bool(frame.snapshot.locks)),
    "heating": Page(_heating, lambda frame: frame.snapshot.heating is not None, animated=True),
    "bins": Page(_bins, lambda frame: bool(frame.snapshot.bins)),
    "ups": Page(_ups, lambda frame: frame.snapshot.ups is not None),
    "mood": Page(_mood, animated=True),
}
