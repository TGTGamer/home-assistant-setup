# ------------------------------------------------------------------------------
# File: tests/oled_status/test_app.py
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

from datetime import datetime

from PIL import Image

from conftest import state, states
from oled_status import app
from oled_status.ha import HomeAssistant, States
from oled_status.settings import Settings


class FakeHome(HomeAssistant):
    def __init__(self, results: list[States | Exception]) -> None:
        super().__init__("http://test", "token")
        self.results = results

    def states(self) -> States:
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result


class FakeScreen:
    def __init__(self) -> None:
        self.images: list[Image.Image] = []
        self.levels: list[int] = []
        self.offs = 0

    def show(self, image: Image.Image) -> None:
        self.images.append(image)

    def contrast(self, level: int) -> None:
        self.levels.append(level)

    def off(self) -> None:
        self.offs += 1


def run(settings: Settings, home: FakeHome, moment: datetime, frames: int) -> FakeScreen:
    screen = FakeScreen()
    ticks = iter(float(n) for n in range(10_000))
    app.run(
        settings,
        home,
        screen,
        clock=lambda: next(ticks),
        now=lambda: moment,
        sleep=lambda _s: None,
        frames=frames,
    )
    return screen


def test_shows_waiting_screen_until_states_arrive_then_recovers() -> None:
    home = FakeHome([OSError("down"), states(state("sun.sun", "above_horizon"))])
    settings = Settings(refresh_seconds=1)
    screen = run(settings, home, datetime(2026, 9, 25, 12, 0), frames=3)
    assert len(screen.images) == 3
    assert screen.levels == [settings.contrast, settings.contrast]
    assert screen.offs == 1  # the finally block blanks the screen


def test_night_dims_the_screen() -> None:
    home = FakeHome([states()])
    settings = Settings(night_contrast=3)
    screen = run(settings, home, datetime(2026, 9, 25, 23, 30), frames=2)
    assert screen.levels == [3, 3]


def test_screen_off_at_night_when_quiet() -> None:
    home = FakeHome([states()])
    settings = Settings(screen_off_at_night=True)
    screen = run(settings, home, datetime(2026, 9, 25, 2, 0), frames=2)
    assert screen.images == []
    assert screen.offs == 3
