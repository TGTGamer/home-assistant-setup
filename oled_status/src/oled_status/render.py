# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/render.py
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

"""Draws one page into a 1-bit image."""

from __future__ import annotations

from PIL import Image, ImageDraw

from oled_status.pages import PAGES, Frame
from oled_status.pages.common import HEIGHT, WIDTH


def render(page: str, frame: Frame) -> Image.Image:
    """A 128x64 1-bit image of `page` for this frame."""
    image = Image.new("1", (WIDTH, HEIGHT))
    PAGES[page].draw(ImageDraw.Draw(image), frame)
    return image
