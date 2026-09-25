# ------------------------------------------------------------------------------
# File: scripts/house_checks.py
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

"""House checks: FCL-1.0-MIT file headers and ASCII-only dashes.

`python scripts/house_checks.py` reports problems and exits non-zero.
`python scripts/house_checks.py --fix` adds missing headers.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = "home-assistant-setup"
HASH_COMMENT_SUFFIXES = {".py", ".sh", ".ps1", ".yaml", ".yml", ".toml", ".conf"}
HASH_COMMENT_NAMES = {"Dockerfile"}
SKIP_PARTS = {"externals", ".venv", "previews", "node_modules"}
SKIP_NAMES = {"uv.lock", "pnpm-lock.yaml"}
# en dash, em dash, horizontal bar, minus sign
DASHES = {chr(0x2013), chr(0x2014), chr(0x2015), chr(0x2212)}
BANNER = "# " + "-" * 78

HEADER_BODY = """#
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
"""


def header(relative: str, modified: str) -> str:
    """The canonical licence header for the file at `relative`."""
    return (
        f"{BANNER}\n# File: {relative}\n# Project: {PROJECT}\n"
        f"# Last modified: {modified}\n{HEADER_BODY}{BANNER}\n"
    )


def tracked_files() -> list[Path]:
    """Files git knows about, including new untracked ones not ignored."""
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return [
        ROOT / line
        for line in output.splitlines()
        if line
        and (ROOT / line).is_file()
        and not SKIP_PARTS.intersection(Path(line).parts)
        and Path(line).name not in SKIP_NAMES
    ]


def needs_header(path: Path) -> bool:
    """True for file types that take `#` comments and must carry a header."""
    return path.suffix in HASH_COMMENT_SUFFIXES or path.name in HASH_COMMENT_NAMES


def has_header(text: str, relative: str) -> bool:
    """True when the canonical header for `relative` opens the file (after any shebang)."""
    body = text.split("\n", 1)[1] if text.startswith("#!") else text
    return body.startswith(f"{BANNER}\n# File: {relative}\n") and HEADER_BODY in body[:2000]


def add_header(text: str, relative: str) -> str:
    """Prepend the header, keeping a shebang on the first line."""
    block = header(relative, date.today().isoformat())
    if text.startswith("#!"):
        shebang, rest = text.split("\n", 1)
        return f"{shebang}\n{block}\n{rest}"
    return f"{block}\n{text}"


APP_LOCK = "oled_status/requirements.lock"
APP_LOCK_COMMAND = [
    "uv",
    "export",
    "--package",
    "oled-status",
    "--no-dev",
    "--no-emit-workspace",
    "--frozen",
    "--quiet",
]


def _requirements(text: str) -> list[str]:
    """Requirement lines of a lock file, without comments or blanks."""
    return [line for line in text.splitlines() if line and not line.startswith("#")]


def app_lock_problems() -> list[str]:
    """The app image installs APP_LOCK; it must match what uv.lock resolves."""
    # Fixed argument list defined above; no user input reaches it.
    expected = subprocess.run(  # noqa: S603
        APP_LOCK_COMMAND, cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout
    committed = (ROOT / APP_LOCK).read_text(encoding="utf-8")
    if _requirements(expected) != _requirements(committed):
        return [f"{APP_LOCK}: out of date with uv.lock (run pnpm lock:app)"]
    return []


def main() -> int:
    """Run every check; with --fix, add missing headers instead of reporting them."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fix", action="store_true", help="add missing headers")
    args = parser.parse_args()
    problems: list[str] = []
    for path in tracked_files():
        relative = path.relative_to(ROOT).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), start=1):
            if DASHES.intersection(line):
                problems.append(f"{relative}:{number}: use an ASCII hyphen, not an en or em dash")
        if needs_header(path) and not has_header(text, relative):
            if args.fix:
                path.write_text(add_header(text, relative), encoding="utf-8")
                print(f"added header: {relative}")
            else:
                problems.append(f"{relative}: missing FCL-1.0-MIT header (run with --fix)")
    problems.extend(app_lock_problems())
    for problem in problems:
        print(problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
