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

Licences are parsed as SPDX-style expressions: parentheses group, AND binds
tighter than OR, and pip-licenses' "; " between classifiers counts as OR. A
licence term passes only if it is exactly one of the allowed names or
aliases below, so `MIT-Commercial` fails and `(MIT OR GPL-3.0-only) AND
GPL-3.0-only` fails because the GPL term is required. `WITH` exceptions pass
only when the exception is listed too.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys

# Exact licence names, compared case-insensitively: SPDX IDs plus the
# classifier names pip-licenses reports for them.
_ALLOWED_NAMES = (
    "MIT",
    "MIT License",
    "MIT-CMU",
    "0BSD",
    "BSD",
    "BSD License",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "Apache-2.0",
    "Apache License 2.0",
    "Apache Software License",
    "ISC",
    "ISC License (ISCL)",
    "MPL-2.0",
    "Mozilla Public License 2.0 (MPL 2.0)",
    "PSF-2.0",
    "Python Software Foundation License",
    "HPND",
    "Historical Permission Notice and Disclaimer (HPND)",
    "Unlicense",
    "The Unlicense (Unlicense)",
    "LicenseRef-FCL-1.0-MIT",
)
ALLOWED = frozenset(name.casefold() for name in _ALLOWED_NAMES)
# Names that contain parentheses must be read as one token, not as a group.
_PARENTHESISED = tuple(name for name in _ALLOWED_NAMES if "(" in name)
ALLOWED_EXCEPTIONS = frozenset({"llvm-exception"})
# Our own packages carry the FCL, which pip-licenses reports as UNKNOWN.
OWN = {"home-assistant-setup", "oled-status"}

# Operators are upper case, as in SPDX, so names such as "Historical Permission
# Notice and Disclaimer" are not split on their "and".
_SPLIT = re.compile(r"(\(|\)|;|\s+(?:AND|OR|WITH)\s+)")


class LicenceSyntaxError(ValueError):
    """The expression could not be parsed; the check treats it as not allowed."""


def _tokens(expression: str) -> list[str]:
    """Split an expression into names, parentheses, `;` and AND/OR/WITH."""
    protected: dict[str, str] = {}
    for index, name in enumerate(_PARENTHESISED):
        placeholder = f"\x00{index}\x00"
        pattern = re.compile(re.escape(name), re.IGNORECASE)
        if pattern.search(expression):
            expression = pattern.sub(placeholder, expression)
            protected[placeholder] = name
    tokens = []
    for raw in _SPLIT.split(expression):
        token = raw.strip()
        if token:
            tokens.append(protected.get(token, token))
    return tokens


class _Parser:
    """Recursive descent: or := and (OR|; and)*, and := with (AND with)*."""

    def __init__(self, tokens: list[str]) -> None:
        """Parse `tokens` from the start."""
        self._tokens = tokens
        self._index = 0

    def _peek(self) -> str | None:
        """The next symbol, or None at the end."""
        return self._tokens[self._index] if self._index < len(self._tokens) else None

    def _take(self) -> str:
        """Consume and return the next symbol."""
        symbol = self._peek()
        if symbol is None:
            raise LicenceSyntaxError("unexpected end of expression")
        self._index += 1
        return symbol

    def parse(self) -> bool:
        """Evaluate the whole expression; trailing tokens are a syntax error."""
        result = self._or()
        if self._peek() is not None:
            raise LicenceSyntaxError(f"unexpected {self._peek()!r}")
        return result

    def _or(self) -> bool:
        """At least one alternative must pass (evaluate all, to check syntax)."""
        results = [self._and()]
        while self._peek() in ("OR", ";"):
            self._take()
            results.append(self._and())
        return any(results)

    def _and(self) -> bool:
        """Every conjoined term must pass."""
        results = [self._with()]
        while self._peek() == "AND":
            self._take()
            results.append(self._with())
        return all(results)

    def _with(self) -> bool:
        """A term, optionally with an exception that must itself be allowed."""
        allowed = self._term()
        if self._peek() == "WITH":
            self._take()
            allowed = self._take().casefold() in ALLOWED_EXCEPTIONS and allowed
        return allowed

    def _term(self) -> bool:
        """A licence name or a parenthesised expression."""
        symbol = self._take()
        if symbol == "(":
            result = self._or()
            if self._take() != ")":
                raise LicenceSyntaxError("missing )")
            return result
        if symbol in (")", ";", "AND", "OR", "WITH"):
            raise LicenceSyntaxError(f"unexpected {symbol!r}")
        return symbol.casefold() in ALLOWED


def expression_allowed(expression: str) -> bool:
    """True when the licence expression is satisfied by allowed licences only."""
    try:
        return _Parser(_tokens(expression)).parse()
    except LicenceSyntaxError:
        return False


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
