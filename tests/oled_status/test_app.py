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

import threading
from datetime import datetime

from PIL import Image

from conftest import state, states
from oled_status import app
from oled_status.ha import HomeAssistant, States
from oled_status.settings import Settings


class FakeHome(HomeAssistant):
    """A Home Assistant client that replays scripted results or errors."""

    def __init__(self, results: list[States | Exception]) -> None:
        """Replay `results` in order, repeating the last one."""
        super().__init__("http://test", "token")
        self.results = results

    def states(self) -> States:
        """Return or raise the next scripted result."""
        result = self.results.pop(0) if len(self.results) > 1 else self.results[0]
        if isinstance(result, Exception):
            raise result
        return result


class FakeScreen:
    """Records what the loop draws instead of driving hardware."""

    def __init__(self) -> None:
        """Start with nothing drawn."""
        self.images: list[Image.Image] = []
        self.levels: list[int] = []
        self.offs = 0

    def show(self, image: Image.Image) -> None:
        """Record the frame."""
        self.images.append(image)

    def contrast(self, level: int) -> None:
        """Record the brightness."""
        self.levels.append(level)

    def off(self) -> None:
        """Count blanking calls."""
        self.offs += 1


def run(settings: Settings, home: FakeHome, moment: datetime, frames: int) -> FakeScreen:
    """Run the loop for `frames` iterations with a one-second-per-frame fake clock."""
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
    """A failed first fetch shows the waiting screen, then pages once states arrive."""
    home = FakeHome([OSError("down"), states(state("sun.sun", "above_horizon"))])
    settings = Settings(refresh_seconds=1)
    screen = run(settings, home, datetime(2026, 9, 25, 12, 0), frames=3)
    assert len(screen.images) == 3
    assert screen.levels == [settings.contrast, settings.contrast]
    assert screen.offs == 1  # the finally block blanks the screen


def test_night_dims_the_screen() -> None:
    """Night uses the night brightness."""
    home = FakeHome([states()])
    settings = Settings(night_contrast=3)
    screen = run(settings, home, datetime(2026, 9, 25, 23, 30), frames=2)
    assert screen.levels == [3, 3]


def test_screen_off_at_night_when_quiet() -> None:
    """With screen_off_at_night and no alerts, nothing is drawn overnight."""
    home = FakeHome([states()])
    settings = Settings(screen_off_at_night=True)
    screen = run(settings, home, datetime(2026, 9, 25, 2, 0), frames=2)
    assert screen.images == []
    assert screen.offs == 3


def test_drops_stale_states_after_a_long_outage() -> None:
    """A lock seen before the outage must not keep showing once the data is stale."""
    ok = states(state("lock.front", "locked"))
    home = FakeHome([ok, *[OSError("down")] * 200])
    settings = Settings(refresh_seconds=1, locks=("lock.front",))
    screen = run(settings, home, datetime(2026, 9, 25, 12, 0), frames=80)
    waiting = app.waiting_image("connection lost").tobytes()
    assert app.stale_after(settings) == app.MIN_STALE_SECONDS
    assert screen.images[1].tobytes() != waiting  # still fresh just after the fetch
    assert screen.images[-1].tobytes() == waiting


def test_stale_limit_scales_with_refresh_interval() -> None:
    """Slow refresh intervals get three missed refreshes before data is dropped."""
    assert app.stale_after(Settings(refresh_seconds=40)) == 120


def test_runs_outside_the_main_thread() -> None:
    """The loop works from a worker thread, where signal handlers cannot be set."""
    errors: list[BaseException] = []

    def work() -> None:
        """Run a couple of frames, keeping any exception for the assertion."""
        try:
            run(Settings(), FakeHome([states()]), datetime(2026, 9, 25, 12, 0), frames=2)
        except BaseException as error:
            errors.append(error)

    worker = threading.Thread(target=work)
    worker.start()
    worker.join()
    assert errors == []


def test_slow_failures_count_towards_staleness() -> None:
    """A failed request that itself takes past the limit drops the states at once."""
    # start, frame 1 (fetch ok, then success time), frame 2 (fetch starts at 2 s,
    # fails, and it is 200 s by the time the failure is seen)
    times = iter([0.0, 1.0, 1.0, 2.0, 200.0])
    home = FakeHome([states(state("lock.front", "locked")), OSError("timed out")])
    screen = FakeScreen()
    app.run(
        Settings(refresh_seconds=1, locks=("lock.front",)),
        home,
        screen,
        clock=lambda: next(times),
        now=lambda: datetime(2026, 9, 25, 12, 0),
        sleep=lambda _s: None,
        frames=2,
    )
    assert screen.images[-1].tobytes() == app.waiting_image("connection lost").tobytes()
