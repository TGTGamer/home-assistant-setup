#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# File: scripts/setup-eventiva-supervisor.sh
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

set -euo pipefail

# Run in the OpenClaw app's terminal, not the separate Home Assistant SSH app.
action="${1:-status}"
workspace="${EVENTIVA_WORKSPACE:?Set EVENTIVA_WORKSPACE to an absolute persistent directory}"
case "$workspace" in /*) ;; *) echo 'EVENTIVA_WORKSPACE must be absolute' >&2; exit 1 ;; esac
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
agent=eventiva-supervisor
server=eventiva-puck
job_name=eventiva-supervisor-watchdog
for executable in openclaw jq; do command -v "$executable" >/dev/null; done

job_id() {
  openclaw cron list --agent "$agent" --all --json |
    jq -er --arg name "$job_name" '
      [.jobs[] | select(.name == $name)] |
      if length == 1 then .[0].id else error("Expected exactly one managed job") end'
}

case "$action" in
  prepare)
    openclaw config validate
    agents="$(openclaw agents list --json)"
    if jq -e --arg id "$agent" '.[] | select(.id == $id)' <<<"$agents" >/dev/null; then
      actual="$(jq -r --arg id "$agent" '.[] | select(.id == $id) | .workspace' <<<"$agents")"
      [[ "$actual" == "$workspace" ]] || { echo 'Existing agent has a different workspace' >&2; exit 1; }
    else
      [[ ! -e "$workspace" ]] || { echo 'Refusing to adopt an existing directory' >&2; exit 1; }
      openclaw agents add "$agent" --workspace "$workspace" --non-interactive --json >/dev/null
    fi
    jobs="$(openclaw cron list --agent "$agent" --all --json)"
    matches="$(jq --arg name "$job_name" '[.jobs[] | select(.name == $name)] | length' <<<"$jobs")"
    [[ "$matches" -le 1 ]] || { echo 'Duplicate managed jobs; inspect before proceeding' >&2; exit 1; }
    if [[ "$matches" != 0 && ( ! -f "$workspace/state.json" || ! -f "$workspace/control.json" ) ]]; then
      echo 'Managed job has lost its state; restore it before preparing again' >&2
      exit 1
    fi
    if jq -e --arg name "$job_name" '.jobs[] | select(.name == $name and .enabled)' <<<"$jobs" >/dev/null; then
      echo 'Disable the managed job before updating its instructions' >&2
      exit 1
    fi
    mkdir -p -- "$workspace"
    chmod 700 -- "$workspace"
    for file in AGENTS.md WATCHDOG.md; do
      if [[ -f "$workspace/$file" ]]; then cp -p -- "$workspace/$file" "$workspace/$file.previous"; fi
      cp -- "$repo_root/openclaw/eventiva/$file" "$workspace/$file"
    done
    if [[ ! -f "$workspace/control.json" ]]; then
      printf '%s\n' '{"dryRun":true}' > "$workspace/control.json"
    fi
    if [[ ! -f "$workspace/state.json" ]]; then
      printf '%s\n' '{"version":1,"activationAt":null,"lastReconciledAt":null,"jobs":{}}' > "$workspace/state.json"
    fi
    jq -e '.version == 1 and (.jobs | type == "object")' "$workspace/state.json" >/dev/null
    jq -e '.dryRun | type == "boolean"' "$workspace/control.json" >/dev/null
    # A missing key is expected on first installation; invalid config was
    # rejected above. Never print a config subtree that may contain credentials.
    if existing="$(openclaw config get "mcp.servers.$server.url" 2>/dev/null)"; then
      [[ "$existing" == 'https://ampcode.com/mcp' ]] || { echo 'MCP server name is already in use' >&2; exit 1; }
    else
      openclaw mcp add "$server" --url https://ampcode.com/mcp \
        --transport streamable-http --auth oauth --no-probe
    fi
    message='Read AGENTS.md, control.json, state.json and WATCHDOG.md in your workspace. Perform one watchdog pass, strictly honoring dryRun. Persist observations and report actions or blockers.'
    if [[ "$matches" == 0 ]]; then
      openclaw cron add --name "$job_name" --agent "$agent" --every 5m \
        --session isolated --message "$message" --timeout-seconds 240 \
        --no-deliver --disabled --json
    else
      openclaw cron edit "$(job_id)" --message "$message" --every 5m \
        --timeout-seconds 240 --json
    fi
    echo 'Prepared with schedule disabled. Sign in to eventiva-puck in OpenClaw Settings > MCP, then run smoke.'
    ;;
  smoke)
    jq -e '.dryRun == true' "$workspace/control.json" >/dev/null
    openclaw mcp doctor "$server" --probe
    openclaw cron run "$(job_id)" --json
    echo 'Smoke run queued. Inspect its result and smoke-test.json before enabling.'
    ;;
  enable)
    jq -e '.version == 1 and (.jobs | type == "object")' "$workspace/state.json" >/dev/null
    jq -e '.ok == true and .project == "resnovas/Eventiva" and
      .repository == "Resnovas/Eventiva" and (.issue | type == "string") and
      (.thread | type == "string") and
      ((now - (.checkedAt | fromdateiso8601)) >= 0) and
      ((now - (.checkedAt | fromdateiso8601)) < 3600)' "$workspace/smoke-test.json" >/dev/null
    id="$(job_id)"
    openclaw mcp doctor "$server" --probe
    tmp="$(mktemp "$workspace/.control.XXXXXX")"
    jq '.dryRun = false' "$workspace/control.json" > "$tmp"
    mv -- "$tmp" "$workspace/control.json"
    if ! openclaw cron enable "$id" --json; then
      tmp="$(mktemp "$workspace/.control.XXXXXX")"
      jq '.dryRun = true' "$workspace/control.json" > "$tmp"
      mv -- "$tmp" "$workspace/control.json"
      exit 1
    fi
    ;;
  disable)
    openclaw cron disable "$(job_id)" --json
    ;;
  status)
    openclaw cron list --agent "$agent" --all --json
    openclaw mcp doctor "$server"
    ;;
  *) echo 'Usage: setup-eventiva-supervisor.sh prepare|smoke|enable|disable|status' >&2; exit 2 ;;
esac
