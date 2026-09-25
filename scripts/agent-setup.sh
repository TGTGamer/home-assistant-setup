#!/usr/bin/env sh
# ------------------------------------------------------------------------------
# File: scripts/agent-setup.sh
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

# Idempotent setup for people and agents: installs a pinned, checksum-verified
# uv if needed, syncs the locked Python environment, then runs the fast
# checks. See AGENT-SETUP.md.
set -eu
cd "$(dirname "$0")/.."

UV_VERSION=0.11.26

# SHA-256 of each uv release archive, from the release's .sha256 files.
uv_sha256() {
  case "$1" in
    x86_64-unknown-linux-gnu) echo 6426a73c3837e6e2483ee344cbc00f36394d179afcba6183cb77437e67db4af0 ;;
    aarch64-unknown-linux-gnu) echo befa1a59c91e96eb601b0fd9a97c03dd666f17baba644b2b4db9c59a767e387e ;;
    x86_64-apple-darwin) echo 922b460202707dd5f4ccacbadbe7f6a546cc46e82a99bf50ca99a7977a78eddd ;;
    aarch64-apple-darwin) echo 8f7fbf1708399b921857bce71e1d60f0d3ccf52a30caebc1c1a2f175dce13ab6 ;;
    *) return 1 ;;
  esac
}

install_uv() {
  case "$(uname -s)-$(uname -m)" in
    Linux-x86_64) target=x86_64-unknown-linux-gnu ;;
    Linux-aarch64 | Linux-arm64) target=aarch64-unknown-linux-gnu ;;
    Darwin-x86_64) target=x86_64-apple-darwin ;;
    Darwin-arm64) target=aarch64-apple-darwin ;;
    *) echo "agent-setup: no pinned uv for $(uname -s)-$(uname -m); install uv $UV_VERSION yourself" >&2; exit 1 ;;
  esac
  expected=$(uv_sha256 "$target")
  archive="uv-$target.tar.gz"
  tmp=$(mktemp -d)
  trap 'rm -rf "$tmp"' EXIT
  curl -fsSL -o "$tmp/$archive" \
    "https://github.com/astral-sh/uv/releases/download/$UV_VERSION/$archive"
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$tmp/$archive" | cut -d' ' -f1)
  else
    actual=$(shasum -a 256 "$tmp/$archive" | cut -d' ' -f1)
  fi
  if [ "$actual" != "$expected" ]; then
    echo "agent-setup: uv archive checksum mismatch ($actual); not installing" >&2
    exit 1
  fi
  tar -xzf "$tmp/$archive" -C "$tmp"
  mkdir -p "$HOME/.local/bin"
  cp "$tmp/uv-$target/uv" "$tmp/uv-$target/uvx" "$HOME/.local/bin/"
}

if ! command -v uv >/dev/null 2>&1; then
  install_uv
  PATH="$HOME/.local/bin:$PATH"
  export PATH
fi
uv sync --locked
uv run pytest -q
echo "agent-setup: ok"
