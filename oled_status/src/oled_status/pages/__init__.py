# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/pages/__init__.py
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

"""Page registry. Add a page by defining it in a module and listing it here."""

from __future__ import annotations

from oled_status.pages import ambient, house
from oled_status.pages.common import Frame, Page

PAGES: dict[str, Page] = {**ambient.PAGES, **house.PAGES}

__all__ = ["PAGES", "Frame", "Page"]
