# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/alerts.py
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

"""Things worth interrupting the page rotation for, most urgent first."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from oled_status.snapshot import Snapshot

BIN_REMINDER_FROM_HOUR = 17


class Level(IntEnum):
    """How urgent an alert is; higher sorts first and CRITICAL flashes."""

    INFO = 1
    WARNING = 2
    CRITICAL = 3


@dataclass(frozen=True)
class Alert:
    """One thing needing attention: an icon, a short title and the names involved."""

    level: Level
    icon: str
    title: str
    detail: str


def _names(names: tuple[str, ...], limit: int = 3) -> str:
    """Join names for a one-line detail, collapsing the tail into `+N`."""
    shown = ", ".join(names[:limit])
    return shown if len(names) <= limit else f"{shown} +{len(names) - limit}"


def current(snapshot: Snapshot) -> list[Alert]:
    """Every active alert, sorted most urgent first."""
    alerts: list[Alert] = []
    if snapshot.leaks:
        alerts.append(Alert(Level.CRITICAL, "drop", "Water leak!", _names(snapshot.leaks)))

    if snapshot.ups and snapshot.ups.charging is False:
        alerts.append(
            Alert(Level.CRITICAL, "battery", "On battery", f"{snapshot.ups.percent:.0f}% left")
        )

    open_locks = tuple(lock.name for lock in snapshot.locks if not lock.secure)
    if open_locks and (snapshot.night or (snapshot.people and not snapshot.anyone_home)):
        alerts.append(Alert(Level.WARNING, "unlocked", "Unlocked", _names(open_locks)))

    if snapshot.lights_on and (snapshot.night or (snapshot.people and not snapshot.anyone_home)):
        alerts.append(Alert(Level.WARNING, "bulb", "Lights on", _names(snapshot.lights_on)))

    due_tomorrow = tuple(item.name for item in snapshot.bins if item.days == 1)
    if due_tomorrow and snapshot.now.hour >= BIN_REMINDER_FROM_HOUR:
        alerts.append(Alert(Level.INFO, "bin", "Bins out tonight", _names(due_tomorrow)))

    return sorted(alerts, key=lambda alert: alert.level, reverse=True)
