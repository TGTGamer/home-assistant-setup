# ------------------------------------------------------------------------------
# File: tests/test_eventiva_supervisor.py
# Project: home-assistant-setup
# Last modified: 2026-11-16
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

"""Exercise installation and activation boundaries without a gateway or secrets."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts/setup-eventiva-supervisor.sh"

FAKE_CLI = r"""
import json, os, sys
from pathlib import Path
p = Path(os.environ["FAKE_STATE"])
s = json.loads(p.read_text()) if p.exists() else {"agents": [], "jobs": []}
a = sys.argv[1:]
def flag(name): return a[a.index(name) + 1]
if a[:2] == ["config", "validate"]: pass
elif a[:2] == ["config", "get"]:
    if not s.get("mcp"): sys.exit(1)
    print("https://ampcode.com/mcp")
elif a[:2] == ["agents", "list"]: print(json.dumps(s["agents"]))
elif a[:2] == ["agents", "add"]:
    w = flag("--workspace")
    Path(w).mkdir()
    s["agents"].append({"id": a[2], "workspace": w})
elif a[:2] == ["mcp", "add"]: s["mcp"] = True
elif a[:2] == ["mcp", "doctor"]: pass
elif a[:2] == ["cron", "list"]: print(json.dumps({"jobs": s["jobs"]}))
elif a[:2] == ["cron", "add"]:
    s["jobs"].append({"id": "managed", "name": flag("--name"), "enabled": False})
elif a[:2] == ["cron", "edit"]: pass
elif a[:2] == ["cron", "enable"]:
    if os.environ.get("FAIL_ENABLE"): sys.exit(1)
    s["jobs"][0]["enabled"] = True
elif a[:2] == ["cron", "disable"]: s["jobs"][0]["enabled"] = False
elif a[:2] == ["cron", "run"]: s["ran"] = True
else: raise RuntimeError("Unexpected CLI invocation: " + repr(a))
p.write_text(json.dumps(s))
"""


@pytest.fixture
def install_env(tmp_path: Path) -> dict[str, str]:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    cli = bin_dir / "openclaw"
    cli.write_text(f"#!{sys.executable}\n{FAKE_CLI}", encoding="utf-8")
    cli.chmod(0o700)
    return {
        **os.environ,
        "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
        "EVENTIVA_WORKSPACE": str(tmp_path / "workspace"),
        "FAKE_STATE": str(tmp_path / "cli-state.json"),
    }


def run(action: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # noqa: S603
        ["bash", str(INSTALLER), action],  # noqa: S607
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def write_proof(env: dict[str, str], age: timedelta = timedelta()) -> None:
    proof = {
        "ok": True,
        "checkedAt": (datetime.now(UTC) - age).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "project": "resnovas/Eventiva",
        "repository": "Resnovas/Eventiva",
        "issue": "EVE-test",
        "thread": "test-thread",
    }
    (Path(env["EVENTIVA_WORKSPACE"]) / "smoke-test.json").write_text(json.dumps(proof))


def test_prepare_is_repeatable_and_preserves_ledger(install_env: dict[str, str]) -> None:
    result = run("prepare", install_env)
    assert result.returncode == 0, result.stderr
    workspace = Path(install_env["EVENTIVA_WORKSPACE"])
    ledger = workspace / "state.json"
    ledger.write_text('{"version":1,"jobs":{"existing":{"thread":"retained"}}}')
    original = ledger.read_text()
    result = run("prepare", install_env)
    assert result.returncode == 0, result.stderr
    state = json.loads(Path(install_env["FAKE_STATE"]).read_text())
    assert len(state["jobs"]) == 1
    assert state["jobs"][0]["enabled"] is False
    assert ledger.read_text() == original
    assert json.loads((workspace / "control.json").read_text())["dryRun"] is True


def test_refuses_to_adopt_existing_workspace(install_env: dict[str, str]) -> None:
    Path(install_env["EVENTIVA_WORKSPACE"]).mkdir()
    assert run("prepare", install_env).returncode != 0


def test_refuses_to_reset_lost_state(install_env: dict[str, str]) -> None:
    assert run("prepare", install_env).returncode == 0
    ledger = Path(install_env["EVENTIVA_WORKSPACE"]) / "state.json"
    ledger.unlink()
    assert run("prepare", install_env).returncode != 0
    assert not ledger.exists()


def test_requires_fresh_smoke_test(install_env: dict[str, str]) -> None:
    assert run("prepare", install_env).returncode == 0
    assert run("enable", install_env).returncode != 0
    write_proof(install_env, timedelta(hours=2))
    assert run("enable", install_env).returncode != 0
    write_proof(install_env)
    assert run("enable", install_env).returncode == 0
    assert run("prepare", install_env).returncode != 0
    assert run("smoke", install_env).returncode != 0


def test_failed_activation_restores_dry_run(install_env: dict[str, str]) -> None:
    assert run("prepare", install_env).returncode == 0
    write_proof(install_env)
    assert run("enable", {**install_env, "FAIL_ENABLE": "1"}).returncode != 0
    control = Path(install_env["EVENTIVA_WORKSPACE"]) / "control.json"
    assert json.loads(control.read_text())["dryRun"] is True


def test_smoke_only_queues_a_disabled_dry_run(install_env: dict[str, str]) -> None:
    assert run("prepare", install_env).returncode == 0
    assert run("smoke", install_env).returncode == 0
    state = json.loads(Path(install_env["FAKE_STATE"]).read_text())
    assert state["ran"] is True
    assert state["jobs"][0]["enabled"] is False
