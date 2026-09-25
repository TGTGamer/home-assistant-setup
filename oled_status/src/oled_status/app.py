# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/app.py
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

"""The display loop: fetch states, pick a page, draw it, repeat."""

from __future__ import annotations

import logging
import signal
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from types import FrameType

from PIL import Image, ImageDraw

from oled_status import alerts, rotation
from oled_status.display import Screen
from oled_status.ha import HomeAssistant
from oled_status.pages import PAGES, Frame
from oled_status.pages.common import HEIGHT, TICKS_PER_SECOND, WIDTH, centred
from oled_status.render import render
from oled_status.settings import Settings
from oled_status.snapshot import Snapshot, build, is_night

log = logging.getLogger(__name__)

MIN_STALE_SECONDS = 60


def stale_after(settings: Settings) -> float:
    """Seconds without a successful fetch before the last states are dropped.

    Three missed refreshes, but never less than a minute, so a single slow
    request does not blank the screen.
    """
    return float(max(MIN_STALE_SECONDS, settings.refresh_seconds * 3))


def waiting_image(message: str) -> Image.Image:
    """A plain screen explaining why no home status is shown."""
    image = Image.new("1", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(image)
    centred(draw, 18, "Home Assistant", 12)
    centred(draw, 36, message, 11)
    return image


def _stop(_signum: int, _frame: FrameType | None) -> None:
    """SIGTERM handler: unwind through `run`'s finally block so the screen blanks."""
    raise SystemExit(0)


def run(
    settings: Settings,
    home: HomeAssistant,
    screen: Screen,
    *,
    clock: Callable[[], float] = time.monotonic,
    now: Callable[[], datetime] = datetime.now,
    sleep: Callable[[float], None] = time.sleep,
    frames: int | None = None,
) -> None:
    """Run until stopped (or for `frames` iterations, for tests).

    If Home Assistant cannot be read for longer than `stale_after`, the last
    states are dropped and a "connection lost" screen replaces them, so an old
    snapshot never passes for the current state of locks, leaks or power.
    """
    # Signal handlers can only be installed from the main thread; elsewhere
    # (tests, embedding) the caller owns shutdown.
    if threading.current_thread() is threading.main_thread():
        signal.signal(signal.SIGTERM, _stop)
    started = clock()
    last_fetch = float("-inf")
    last_success = float("-inf")
    snapshot: Snapshot | None = None
    waiting = "connecting..."
    drawn = 0
    try:
        while frames is None or drawn < frames:
            moment = clock()
            if moment - last_fetch >= settings.refresh_seconds:
                last_fetch = moment
                try:
                    snapshot = build(home.states(), settings, now())
                    # Measured after the request, which may take up to its timeout.
                    last_success = clock()
                except (OSError, ValueError) as error:
                    log.warning("could not read states: %s", error)
                    # Measured now, after the failed request, which may have taken its full timeout.
                    if snapshot is not None and clock() - last_success > stale_after(settings):
                        log.warning("dropping states older than %.0fs", stale_after(settings))
                        snapshot = None
                        waiting = "connection lost"
            drawn += 1
            if snapshot is None:
                screen.show(waiting_image(waiting))
                sleep(1.0)
                continue

            current = now()
            snapshot = replace(
                snapshot,
                now=current,
                night=is_night(current.time(), settings.night_start, settings.night_end),
            )
            frame = Frame(
                snapshot,
                tuple(alerts.current(snapshot)),
                int((moment - started) * TICKS_PER_SECOND),
            )
            page = rotation.choose(settings, frame, moment - started)
            if page is None:
                screen.off()
                sleep(1.0)
                continue
            screen.contrast(settings.night_contrast if snapshot.night else settings.contrast)
            screen.show(render(page, frame))
            sleep(1 / TICKS_PER_SECOND if PAGES[page].animated else 0.5)
    finally:
        screen.off()
