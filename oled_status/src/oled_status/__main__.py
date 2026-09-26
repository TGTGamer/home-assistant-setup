# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/__main__.py
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

"""Command line: `python -m oled_status [--preview DIR | --file PNG] [--options JSON]`."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from oled_status import app, preview, settings
from oled_status.display import FileScreen, Oled, Screen
from oled_status.ha import HomeAssistant


def main() -> None:
    """Parse arguments, then render previews or run the display loop."""
    parser = argparse.ArgumentParser(prog="oled_status", description=__doc__)
    parser.add_argument("--options", type=Path, default=settings.OPTIONS_PATH)
    parser.add_argument("--preview", type=Path, help="render sample pages to this folder and exit")
    parser.add_argument("--file", type=Path, help="draw to this PNG instead of the OLED")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.preview:
        for path in preview.write(args.preview):
            print(path)
        return

    options = settings.load(args.options)
    # Connect before opening the display, so a missing token fails first and
    # clearly, rather than hiding behind a display error.
    home = HomeAssistant.from_environment()
    screen: Screen = FileScreen(args.file) if args.file else Oled(options)
    app.run(options, home, screen)


if __name__ == "__main__":
    main()
