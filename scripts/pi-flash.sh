#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# File: scripts/pi-flash.sh
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

# Back up an SD card to an image, or write Home Assistant OS to one.
#
#   scripts/pi-flash.sh backup IMAGE     copy the whole card to IMAGE
#   scripts/pi-flash.sh flash [BOARD]    download and write HA OS (default rpi4-64)
#
# Exactly one USB disk (the card reader) must be attached. Uses sudo in a
# terminal and pkexec (a desktop password prompt) otherwise.
set -euo pipefail

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/home-assistant-setup"
if [ -t 0 ]; then AS_ROOT=sudo; else AS_ROOT=pkexec; fi

mapfile -t DEVS < <(lsblk -dnpo NAME,TRAN | awk '$2=="usb"{print $1}')
[ "${#DEVS[@]}" -eq 1 ] || { echo "Expected exactly one USB disk, found: ${DEVS[*]:-none}" >&2; exit 1; }
DEV=${DEVS[0]}
SIZE_GB=$(( $(lsblk -dnbo SIZE "$DEV") / 1000000000 ))
echo "Card: $DEV (${SIZE_GB} GB, $(lsblk -dno MODEL "$DEV" | xargs))"

unmount_all() {
  for part in $(lsblk -lnpo NAME,MOUNTPOINT "$DEV" | awk 'NF==2{print $1}'); do
    udisksctl unmount -b "$part"
  done
}

case "${1:-}" in
  backup)
    out=${2:?usage: $0 backup IMAGE}
    unmount_all
    $AS_ROOT dd if="$DEV" of="$out" bs=4M status=progress conv=fsync
    $AS_ROOT chown "$(id -u):$(id -g)" "$out"
    echo "Backup saved to $out" ;;
  flash)
    board=${2:-rpi4-64}
    mkdir -p "$CACHE"
    tag=$(curl -fsSL https://api.github.com/repos/home-assistant/operating-system/releases/latest \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])')
    image="$CACHE/haos_${board}-${tag}.img.xz"
    if [ ! -s "$image" ]; then
      curl -fL -o "$image.part" \
        "https://github.com/home-assistant/operating-system/releases/download/${tag}/haos_${board}-${tag}.img.xz"
      xz -t "$image.part" && mv "$image.part" "$image"
    fi
    echo "Image: $image"
    if [ -t 0 ]; then
      read -rp "ERASE everything on $DEV and write HA OS ${tag}? Type yes: " ok
      [ "$ok" = yes ] || exit 1
    elif [ "${CONFIRM_ERASE:-}" != "$DEV" ]; then
      echo "Not a terminal: set CONFIRM_ERASE=$DEV to confirm erasing this disk." >&2
      exit 1
    fi
    unmount_all
    xz -dc "$image" | $AS_ROOT dd of="$DEV" bs=4M status=progress conv=fsync
    $AS_ROOT partprobe "$DEV" || true
    sync
    echo "HA OS ${tag} written to $DEV. Next: scripts/prepare-boot.sh" ;;
  *) echo "usage: $0 backup IMAGE | flash [BOARD]" >&2; exit 1 ;;
esac
