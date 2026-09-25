# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/snapshot.py
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

"""Turns raw entity states into the few facts the pages draw."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime, time

from oled_status.ha import State, States
from oled_status.settings import Settings

_DAYS = re.compile(r"(\d+)")


@dataclass(frozen=True)
class Person:
    """Someone the people page and away alerts track."""

    name: str
    home: bool


@dataclass(frozen=True)
class Lock:
    """A lock and its raw Home Assistant state."""

    name: str
    state: str

    @property
    def secure(self) -> bool:
        """Only `locked` counts; unlocked, jammed or open do not."""
        return self.state == "locked"


@dataclass(frozen=True)
class Heating:
    """Thermostat readings; `active` while the boiler is calling for heat."""

    current: float | None
    target: float | None
    active: bool


@dataclass(frozen=True)
class Bin:
    """A waste collection and the days until it."""

    name: str
    days: int


@dataclass(frozen=True)
class Media:
    """What a media player is currently playing."""

    title: str
    artist: str


@dataclass(frozen=True)
class Weather:
    """Current condition and temperature from a weather entity."""

    condition: str
    temperature: float | None
    unit: str


@dataclass(frozen=True)
class Ups:
    """UPS battery level; `charging` is None when no charging entity is set."""

    percent: float
    charging: bool | None


@dataclass(frozen=True)
class Snapshot:
    """What the house looks like right now, already filtered by the settings."""

    now: datetime
    night: bool
    people: tuple[Person, ...] = ()
    locks: tuple[Lock, ...] = ()
    heating: Heating | None = None
    bins: tuple[Bin, ...] = ()
    media: Media | None = None
    weather: Weather | None = None
    ups: Ups | None = None
    lights_on: tuple[str, ...] = ()
    leaks: tuple[str, ...] = ()

    @property
    def anyone_home(self) -> bool:
        """True when at least one tracked person is home."""
        return any(person.home for person in self.people)


def is_night(now: time, start: time, end: time) -> bool:
    """True between start and end, handling windows that cross midnight."""
    if start <= end:
        return start <= now < end
    return now >= start or now < end


def bin_days(state: State, today: date) -> int | None:
    """Days until a collection, from the common waste-collection sensor formats.

    Accepts a number of days, an ISO date, `today` / `tomorrow`, text such as
    `in 3 days`, or a `daysTo` attribute.
    """
    days_to = state.number("daysTo")
    if days_to is not None:
        return int(days_to)
    text = state.state.strip().lower()
    if text in ("unknown", "unavailable", ""):
        return None
    if text == "today":
        return 0
    if text == "tomorrow":
        return 1
    try:
        return (date.fromisoformat(text[:10]) - today).days
    except ValueError:
        pass
    match = _DAYS.search(text)
    return int(match.group(1)) if match else None


def _usable(state: State | None) -> State | None:
    """The state, or None when missing, unknown or unavailable."""
    if state is None or state.state in ("unknown", "unavailable"):
        return None
    return state


def build(states: States, settings: Settings, now: datetime) -> Snapshot:
    """Build a Snapshot from the current states."""

    def get(entity_id: str) -> State | None:
        """State for a configured entity ID, or None when unset or unusable."""
        return _usable(states.get(entity_id)) if entity_id else None

    people = tuple(
        Person(state.name, state.state == "home")
        for entity_id in settings.persons
        if (state := get(entity_id))
    )
    locks = tuple(
        Lock(state.name, state.state) for entity_id in settings.locks if (state := get(entity_id))
    )

    heating = None
    if climate := get(settings.climate):
        heating = Heating(
            current=climate.number("current_temperature"),
            target=climate.number("temperature"),
            active=climate.attributes.get("hvac_action") == "heating",
        )

    bins = sorted(
        (
            Bin(state.name, days)
            for entity_id in settings.bins
            if (state := get(entity_id)) and (days := bin_days(state, now.date())) is not None
            if days >= 0
        ),
        key=lambda item: item.days,
    )

    media = None
    if (player := get(settings.media_player)) and player.state == "playing":
        title = player.attributes.get("media_title")
        artist = player.attributes.get("media_artist")
        media = Media(
            title if isinstance(title, str) else "Playing",
            artist if isinstance(artist, str) else "",
        )

    weather = None
    if forecast := get(settings.weather):
        unit = forecast.attributes.get("temperature_unit")
        weather = Weather(
            forecast.state, forecast.number("temperature"), unit if isinstance(unit, str) else ""
        )

    ups = None
    if (battery := get(settings.ups_battery)) and (percent := battery.number()) is not None:
        charging_state = get(settings.ups_charging)
        charging = None if charging_state is None else charging_state.state in ("on", "charging")
        ups = Ups(percent, charging)

    lights_on = tuple(
        sorted(
            state.name
            for entity_id, state in states.items()
            if entity_id.startswith("light.")
            and state.state == "on"
            and entity_id not in settings.ignored_lights
            and not state.attributes.get("entity_id")  # skip light groups
        )
    )
    leaks = tuple(
        state.name
        for entity_id in settings.leak_sensors
        if (state := get(entity_id)) and state.state == "on"
    )

    return Snapshot(
        now=now,
        night=is_night(now.time(), settings.night_start, settings.night_end),
        people=people,
        locks=locks,
        heating=heating,
        bins=tuple(bins),
        media=media,
        weather=weather,
        ups=ups,
        lights_on=lights_on,
        leaks=leaks,
    )
