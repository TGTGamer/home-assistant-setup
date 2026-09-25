# ------------------------------------------------------------------------------
# File: tests/oled_status/test_snapshot.py
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

from datetime import date, datetime, time

import pytest

from conftest import state, states
from oled_status.ha import parse_states
from oled_status.settings import Settings
from oled_status.snapshot import bin_days, build, is_night

NOW = datetime(2026, 9, 25, 21, 0)


@pytest.mark.parametrize(
    ("moment", "expected"),
    [(time(22, 59), False), (time(23, 0), True), (time(3, 0), True), (time(7, 0), False)],
)
def test_night_window_crosses_midnight(moment: time, expected: bool) -> None:
    assert is_night(moment, time(23, 0), time(7, 0)) is expected


def test_night_window_same_day() -> None:
    assert is_night(time(14, 0), time(13, 0), time(15, 0))
    assert not is_night(time(16, 0), time(13, 0), time(15, 0))


@pytest.mark.parametrize(
    ("value", "attributes", "expected"),
    [
        ("3", {}, 3),
        ("today", {}, 0),
        ("Tomorrow", {}, 1),
        ("in 5 days", {}, 5),
        ("2026-09-28", {}, 3),
        ("2026-09-28T00:00:00+00:00", {}, 3),
        ("Recycling", {"daysTo": 2}, 2),
        ("unknown", {}, None),
        ("no idea", {}, None),
    ],
)
def test_bin_days_formats(value: str, attributes: dict[str, object], expected: int | None) -> None:
    assert bin_days(state("sensor.bin", value, **attributes), date(2026, 9, 25)) == expected


def test_build_reads_configured_entities_only() -> None:
    settings = Settings(
        persons=("person.a", "person.b"),
        locks=("lock.front", "lock.missing"),
        climate="climate.hall",
        bins=("sensor.recycling", "sensor.garden", "sensor.past"),
        media_player="media_player.lounge",
        weather="weather.home",
        ups_battery="sensor.ups",
        ups_charging="binary_sensor.ups_charging",
        leak_sensors=("binary_sensor.sink",),
        ignored_lights=("light.porch",),
    )
    snapshot = build(
        states(
            state("person.a", "home", friendly_name="A"),
            state("person.b", "not_home", friendly_name="B"),
            state("lock.front", "unlocked", friendly_name="Front"),
            state(
                "climate.hall",
                "heat",
                current_temperature=19.5,
                temperature=21,
                hvac_action="heating",
            ),
            state("sensor.recycling", "in 8 days", friendly_name="Recycling"),
            state("sensor.garden", "tomorrow", friendly_name="Garden"),
            state("sensor.past", "2026-09-20"),
            state("media_player.lounge", "playing", media_title="Song", media_artist="Band"),
            state("weather.home", "rainy", temperature=12.5, temperature_unit="°C"),
            state("sensor.ups", "64"),
            state("binary_sensor.ups_charging", "off"),
            state("binary_sensor.sink", "on", friendly_name="Sink"),
            state("light.kitchen", "on", friendly_name="Kitchen"),
            state("light.porch", "on"),
            state("light.all", "on", entity_id=["light.kitchen"]),
            state("light.hall", "off"),
        ),
        settings,
        NOW,
    )
    assert [(p.name, p.home) for p in snapshot.people] == [("A", True), ("B", False)]
    assert [lock.name for lock in snapshot.locks] == ["Front"]
    assert snapshot.heating is not None and snapshot.heating.active
    assert snapshot.heating.current == 19.5
    assert [(b.name, b.days) for b in snapshot.bins] == [("Garden", 1), ("Recycling", 8)]
    assert snapshot.media is not None and snapshot.media.title == "Song"
    assert snapshot.weather is not None and snapshot.weather.temperature == 12.5
    assert snapshot.ups is not None and snapshot.ups.charging is False
    assert snapshot.lights_on == ("Kitchen",)
    assert snapshot.leaks == ("Sink",)
    assert snapshot.anyone_home


def test_build_ignores_unavailable_and_paused_player() -> None:
    settings = Settings(climate="climate.hall", media_player="media_player.tv")
    snapshot = build(
        states(state("climate.hall", "unavailable"), state("media_player.tv", "paused")),
        settings,
        NOW,
    )
    assert snapshot.heating is None
    assert snapshot.media is None


def test_parse_states_skips_malformed_items() -> None:
    parsed = parse_states(
        [
            {"entity_id": "light.a", "state": "on", "attributes": {"friendly_name": "A"}},
            {"entity_id": "light.b"},
            "nonsense",
            {"entity_id": "sensor.c", "state": "1", "attributes": None},
        ]
    )
    assert sorted(parsed) == ["light.a", "sensor.c"]
    assert parsed["sensor.c"].name == "C"
    with pytest.raises(ValueError, match="list"):
        parse_states({"states": []})
