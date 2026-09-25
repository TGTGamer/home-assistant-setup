# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/rotation.py
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

"""Chooses which page is on screen."""

from __future__ import annotations

from oled_status.pages import PAGES, Frame
from oled_status.settings import Settings

FALLBACK = "clock"


def sequence(settings: Settings, frame: Frame) -> list[str]:
    """Pages to cycle through now. Alerts get every other slot."""
    pages = [
        name
        for name in settings.pages
        if name != "alert" and name in PAGES and PAGES[name].relevant(frame)
    ] or [FALLBACK]
    if not frame.alerts:
        return pages
    return [slot for name in pages for slot in ("alert", name)]


def choose(settings: Settings, frame: Frame, elapsed_seconds: float) -> str | None:
    """Page name for this moment, or None when the screen should be dark.

    `elapsed_seconds` is time since the app started, so the rotation keeps
    moving even when the page list changes length.
    """
    if settings.screen_off_at_night and frame.snapshot.night and not frame.alerts:
        return None
    pages = sequence(settings, frame)
    return pages[int(elapsed_seconds // settings.page_seconds) % len(pages)]
