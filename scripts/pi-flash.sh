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
#   scripts/pi-flash.sh list                     show removable disks
#   scripts/pi-flash.sh backup DEVICE IMAGE      copy the whole card to IMAGE
#   scripts/pi-flash.sh flash DEVICE [BOARD]     download and write HA OS (default rpi4-64)
#
# DEVICE is the whole card, for example /dev/sdd or /dev/mmcblk0; find it with
# `list`. It must be a removable disk no bigger than MAX_CARD_GB (default 256);
# set ALLOW_LARGE_DISK=DEVICE to accept a bigger one. Flashing asks you to type
# DEVICE again; without a terminal, set CONFIRM_ERASE to the same path instead.
# Backup never replaces an existing IMAGE unless OVERWRITE_BACKUP=IMAGE is set.
# Uses sudo in a terminal and pkexec (a desktop password prompt) otherwise.
set -euo pipefail

CACHE="${XDG_CACHE_HOME:-$HOME/.cache}/home-assistant-setup"
MAX_CARD_GB=${MAX_CARD_GB:-256}
if [ -t 0 ]; then AS_ROOT=sudo; else AS_ROOT=pkexec; fi

usage() {
  echo "usage: $0 list | backup DEVICE IMAGE | flash DEVICE [BOARD]" >&2
  exit 1
}

list_disks() {
  lsblk -dpo NAME,SIZE,RM,TRAN,MODEL | awk 'NR==1 || $3=="1"'
}

# Check DEVICE is a whole, removable disk and print what it is.
check_device() {
  local dev=$1
  [ -b "$dev" ] || { echo "$dev is not a block device" >&2; exit 1; }
  [ "$(lsblk -dno TYPE "$dev")" = disk ] || { echo "$dev is a partition; give the whole disk" >&2; exit 1; }
  [ "$(lsblk -dno RM "$dev" | tr -d ' ')" = 1 ] || {
    echo "$dev is not a removable disk; refusing. Removable disks:" >&2
    list_disks >&2
    exit 1
  }
  local size_gb=$(( $(lsblk -dnbo SIZE "$dev") / 1000000000 ))
  if [ "$size_gb" -gt "$MAX_CARD_GB" ] && [ "${ALLOW_LARGE_DISK:-}" != "$dev" ]; then
    echo "$dev is ${size_gb} GB, bigger than an SD card (limit ${MAX_CARD_GB} GB); refusing." >&2
    echo "If it really is the card, rerun with ALLOW_LARGE_DISK=$dev." >&2
    exit 1
  fi
  echo "Card: $dev ($(lsblk -dno SIZE "$dev" | xargs), $(lsblk -dno MODEL "$dev" | xargs))"
}

# Refuse to write the backup over a device or an existing image.
check_backup_target() {
  local out=$1
  if [ -b "$out" ] || [ -c "$out" ]; then
    echo "$out is a device, not an image file; refusing." >&2
    exit 1
  fi
  if [ -e "$out" ] && [ "${OVERWRITE_BACKUP:-}" != "$out" ]; then
    echo "$out already exists; refusing to replace a backup." >&2
    echo "Choose another name, or rerun with OVERWRITE_BACKUP=$out." >&2
    exit 1
  fi
  [ -d "$(dirname "$out")" ] || { echo "$(dirname "$out") does not exist" >&2; exit 1; }
}

# Unmount every mounted partition of DEVICE, then prove none is still mounted.
# Mount points are read one per line, so paths with spaces are handled.
unmount_all() {
  local dev=$1 part
  while IFS= read -r part; do
    if [ -n "$(lsblk -nro MOUNTPOINTS "$part" | tr -d '\n')" ]; then
      udisksctl unmount -b "$part"
    fi
  done < <(lsblk -lnpo NAME "$dev" | tail -n +2)
  if [ -n "$(lsblk -nro MOUNTPOINTS "$dev" | tr -d '\n')" ]; then
    echo "Something on $dev is still mounted; not touching it:" >&2
    lsblk -po NAME,MOUNTPOINTS "$dev" >&2
    exit 1
  fi
}

confirm_erase() {
  local dev=$1 what=$2 typed
  if [ -t 0 ]; then
    read -rp "ERASE everything on $dev and write $what? Type $dev to confirm: " typed
    [ "$typed" = "$dev" ] || { echo "Not confirmed; nothing written." >&2; exit 1; }
  elif [ "${CONFIRM_ERASE:-}" != "$dev" ]; then
    echo "Not a terminal: set CONFIRM_ERASE=$dev to confirm erasing this disk." >&2
    exit 1
  fi
}

case "${1:-}" in
  list)
    list_disks ;;
  backup)
    dev=${2:-}; out=${3:-}
    [ -n "$dev" ] && [ -n "$out" ] || usage
    check_device "$dev"
    check_backup_target "$out"
    unmount_all "$dev"
    $AS_ROOT dd if="$dev" of="$out" bs=4M status=progress conv=fsync
    $AS_ROOT chown "$(id -u):$(id -g)" "$out"
    echo "Backup saved to $out" ;;
  flash)
    dev=${2:-}; board=${3:-rpi4-64}
    [ -n "$dev" ] || usage
    check_device "$dev"
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
    confirm_erase "$dev" "HA OS ${tag}"
    unmount_all "$dev"
    xz -dc "$image" | $AS_ROOT dd of="$dev" bs=4M status=progress conv=fsync
    $AS_ROOT partprobe "$dev" || true
    sync
    echo "HA OS ${tag} written to $dev. Next: scripts/prepare-boot.sh" ;;
  *) usage ;;
esac
