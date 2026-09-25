# ------------------------------------------------------------------------------
# File: scripts/license_check.py
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

"""Fail when an installed dependency uses a licence outside the allow list."""

from __future__ import annotations

import json
import subprocess
import sys

ALLOWED = (
    "MIT",
    "BSD",
    "Apache",
    "ISC",
    "MPL",
    "PSF",
    "Python Software Foundation",
    "HPND",
    "Unlicense",
    "LicenseRef-FCL-1.0-MIT",
)
# Our own packages carry the FCL, which pip-licenses reports as UNKNOWN.
OWN = {"home-assistant-setup", "oled-status"}


def main() -> int:
    output = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--from=mixed"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    denied = [
        f"{item['Name']} {item['Version']}: {item['License']}"
        for item in json.loads(output)
        if item["Name"] not in OWN and not any(key in item["License"] for key in ALLOWED)
    ]
    for line in denied:
        print(f"licence not allowed: {line}", file=sys.stderr)
    return 1 if denied else 0


if __name__ == "__main__":
    sys.exit(main())
