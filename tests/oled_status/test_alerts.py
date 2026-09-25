# ------------------------------------------------------------------------------
# File: tests/oled_status/test_alerts.py
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
from datetime import datetime

from oled_status.alerts import Level, current
from oled_status.snapshot import Bin, Lock, Person, Snapshot, Ups

EVENING = datetime(2026, 9, 25, 18, 0)


def base() -> Snapshot:
    return Snapshot(
        now=EVENING,
        night=False,
        people=(Person("A", home=True),),
        locks=(Lock("Front", "locked"), Lock("Back", "unlocked")),
        lights_on=("Kitchen",),
    )


def titles(snapshot: Snapshot) -> list[str]:
    return [alert.title for alert in current(snapshot)]


def test_nothing_to_say_when_home_in_the_evening() -> None:
    assert titles(base()) == []


def test_night_flags_unlocked_doors_and_lights() -> None:
    assert titles(replace(base(), night=True)) == ["Unlocked", "Lights on"]


def test_everyone_out_flags_unlocked_doors_and_lights() -> None:
    snapshot = replace(base(), people=(Person("A", home=False),))
    assert titles(snapshot) == ["Unlocked", "Lights on"]


def test_no_people_configured_means_no_away_alerts() -> None:
    assert titles(replace(base(), people=())) == []


def test_critical_alerts_come_first() -> None:
    snapshot = replace(base(), night=True, leaks=("Sink",), ups=Ups(40, charging=False))
    alerts = current(snapshot)
    assert [alert.level for alert in alerts][:2] == [Level.CRITICAL, Level.CRITICAL]
    assert alerts[0].detail == "Sink"
    assert alerts[1].detail == "40% left"


def test_bin_reminder_only_the_evening_before() -> None:
    snapshot = replace(base(), locks=(), lights_on=(), bins=(Bin("Recycling", 1),))
    assert titles(snapshot) == ["Bins out tonight"]
    assert titles(replace(snapshot, now=datetime(2026, 9, 25, 12, 0))) == []
    assert titles(replace(snapshot, bins=(Bin("Recycling", 2),))) == []


def test_long_name_lists_are_shortened() -> None:
    snapshot = replace(base(), night=True, locks=(), lights_on=("A", "B", "C", "D", "E"))
    assert current(snapshot)[0].detail == "A, B, C +2"
