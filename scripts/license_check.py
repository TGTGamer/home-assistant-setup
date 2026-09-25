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

"""Fail when an installed dependency uses a licence outside the allow list.

Licences are checked as expressions, not substrings: every term joined by AND
must be allowed, and at least one alternative joined by OR (or by the "; "
pip-licenses uses between classifiers) must pass. So `GPL-3.0 AND MIT` fails
even though it mentions MIT, while `Apache-2.0 OR BSD-2-Clause` passes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

ALLOWED = (
    "MIT",
    "BSD",
    "0BSD",
    "Apache",
    "ISC",
    "MPL",
    "Mozilla Public License",
    "PSF",
    "Python Software Foundation",
    "HPND",
    "Unlicense",
    "LicenseRef-FCL-1.0-MIT",
)
# Copyleft, source-available and unknown terms never pass, whatever else they say.
DENIED = ("GPL", "SSPL", "BUSL", "Commons Clause", "NonCommercial", "UNKNOWN", "Proprietary")
# Our own packages carry the FCL, which pip-licenses reports as UNKNOWN.
OWN = {"home-assistant-setup", "oled-status"}

_OR = re.compile(r"\s+OR\s+|\s*;\s*", re.IGNORECASE)
_AND = re.compile(r"\s+AND\s+", re.IGNORECASE)
_WITH = re.compile(r"\s+WITH\s+.*$", re.IGNORECASE)


def _mentions(term: str, names: tuple[str, ...]) -> bool:
    """True when `term` names any of `names`, case-insensitively and not mid-word."""
    return any(re.search(rf"(?<![A-Za-z]){re.escape(name)}", term, re.IGNORECASE) for name in names)


def term_allowed(term: str) -> bool:
    """One licence, such as `MIT` or `Mozilla Public License 2.0 (MPL 2.0)`."""
    base = _WITH.sub("", term).strip(" ()")
    # Deny on the whole term, so an exception clause cannot hide a restriction.
    return bool(base) and not _mentions(term, DENIED) and _mentions(base, ALLOWED)


def expression_allowed(expression: str) -> bool:
    """True when some OR alternative has every one of its AND terms allowed."""
    flat = expression.replace("(", " ").replace(")", " ")
    return any(
        all(term_allowed(term) for term in _AND.split(alternative))
        for alternative in _OR.split(flat)
        if alternative.strip()
    )


def main() -> int:
    """Check every installed distribution; print the ones that fail."""
    output = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--from=mixed"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    denied = [
        f"{item['Name']} {item['Version']}: {item['License']}"
        for item in json.loads(output)
        if item["Name"] not in OWN and not expression_allowed(item["License"])
    ]
    for line in denied:
        print(f"licence not allowed: {line}", file=sys.stderr)
    return 1 if denied else 0


if __name__ == "__main__":
    sys.exit(main())
