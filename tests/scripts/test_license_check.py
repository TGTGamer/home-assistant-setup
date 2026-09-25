# ------------------------------------------------------------------------------
# File: tests/scripts/test_license_check.py
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

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest


def _load() -> ModuleType:
    """Import scripts/license_check.py, which is a script rather than a package."""
    path = Path(__file__).resolve().parents[2] / "scripts" / "license_check.py"
    spec = importlib.util.spec_from_file_location("license_check", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


license_check = _load()


@pytest.mark.parametrize(
    "expression",
    [
        "MIT",
        "MIT License",
        "MIT-CMU",
        "BSD-2-Clause",
        "0BSD",
        "Apache-2.0 OR BSD-2-Clause",
        "Mozilla Public License 2.0 (MPL 2.0)",
        "PSF-2.0",
        "BSD License; MIT License",
        "Apache-2.0 WITH LLVM-exception",
        "(MIT OR GPL-3.0-only) AND Apache-2.0",
        "LicenseRef-FCL-1.0-MIT",
    ],
)
def test_allowed(expression: str) -> None:
    """Permissive licences, and OR choices with a permissive side, pass."""
    assert license_check.expression_allowed(expression)


@pytest.mark.parametrize(
    "expression",
    [
        "GPL-3.0-or-later AND MIT",
        "MIT AND LGPL-2.1",
        "GPL-2.0",
        "AGPL-3.0",
        "SSPL-1.0",
        "UNKNOWN",
        "",
        "Some Custom Licence",
        "MIT with Commons Clause",
    ],
)
def test_denied(expression: str) -> None:
    """Any denied or unrecognised term under AND fails the whole expression."""
    assert not license_check.expression_allowed(expression)
