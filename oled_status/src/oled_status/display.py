# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/display.py
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

"""The physical screen, or an in-memory stand-in for previews and development."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from PIL import Image

from oled_status.pages.common import HEIGHT, WIDTH
from oled_status.settings import Settings


class Screen(Protocol):
    def show(self, image: Image.Image) -> None: ...
    def contrast(self, level: int) -> None: ...
    def off(self) -> None: ...


class Oled:
    """SSD1306 over I2C, driven by luma.oled."""

    def __init__(self, settings: Settings) -> None:
        from luma.core.interface.serial import i2c  # hardware-only import
        from luma.oled.device import ssd1306

        serial = i2c(port=settings.i2c_port, address=settings.i2c_address)
        self._device = ssd1306(serial, width=WIDTH, height=HEIGHT, rotate=settings.rotate)
        self._level: int | None = None
        self._on = True

    def show(self, image: Image.Image) -> None:
        if not self._on:
            self._device.show()
            self._on = True
        self._device.display(image)

    def contrast(self, level: int) -> None:
        if level != self._level:
            self._device.contrast(level)
            self._level = level

    def off(self) -> None:
        if self._on:
            self._device.hide()
            self._on = False


class FileScreen:
    """Writes each frame to a PNG, scaled up so it is easy to look at."""

    def __init__(self, path: Path, scale: int = 4) -> None:
        self._path = path
        self._scale = scale
        path.parent.mkdir(parents=True, exist_ok=True)

    def show(self, image: Image.Image) -> None:
        size = (WIDTH * self._scale, HEIGHT * self._scale)
        image.convert("L").resize(size, Image.Resampling.NEAREST).save(self._path)

    def contrast(self, level: int) -> None:
        return None

    def off(self) -> None:
        self.show(Image.new("1", (WIDTH, HEIGHT)))
