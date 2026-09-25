#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# File: scripts/prepare-boot.sh
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

# Add this repo's boot settings to a freshly flashed HA OS card. Safe to rerun.
#
# Mounts the card's hassos-boot partition, appends ha-os/boot/config.txt.append
# to config.txt once, and copies ha-os/boot/CONFIG onto it (HA OS imports the
# CONFIG folder on boot).
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
PART=$(lsblk -lnpo NAME,LABEL | awk '$2=="hassos-boot"{print $1}')
[ -n "$PART" ] || { echo "No partition labelled hassos-boot; is the card inserted?" >&2; exit 1; }
[ "$(wc -l <<<"$PART")" -eq 1 ] || { echo "More than one hassos-boot partition found" >&2; exit 1; }

MOUNT=$(lsblk -no MOUNTPOINT "$PART" | head -1)
if [ -z "$MOUNT" ]; then
  udisksctl mount -b "$PART" >/dev/null
  MOUNT=$(lsblk -no MOUNTPOINT "$PART" | head -1)
fi
# Never fall back to an empty path: "$MOUNT/config.txt" would become /config.txt.
if [ -z "$MOUNT" ] || [ "$MOUNT" = / ] || [ ! -f "$MOUNT/config.txt" ]; then
  echo "Could not find $PART mounted with a config.txt (mount point: '${MOUNT}')." >&2
  exit 1
fi
echo "Boot partition: $PART at $MOUNT"

if grep -q "home-assistant-setup: begin" "$MOUNT/config.txt"; then
  echo "config.txt already has the settings"
else
  printf '\n[all]\n' >>"$MOUNT/config.txt"
  cat "$ROOT/ha-os/boot/config.txt.append" >>"$MOUNT/config.txt"
  echo "config.txt updated"
fi
cp -r "$ROOT/ha-os/boot/CONFIG" "$MOUNT/"
sync
echo "CONFIG copied. Eject the card, put it in the Pi and power on."
