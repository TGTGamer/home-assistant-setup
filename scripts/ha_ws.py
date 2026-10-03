# ------------------------------------------------------------------------------
# File: scripts/ha_ws.py
# Project: home-assistant-setup
# Last modified: 2026-10-03
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

"""Send websocket commands to Home Assistant with nothing but the standard library.

Reads one JSON command per line on stdin, sends each with a fresh `id`, and
prints the matching result as one JSON line. Needs HA_WS_URL (for example
ws://172.30.32.1/api/websocket from inside the hub) and HA_TOKEN in the
environment. Meant to run on the hub over SSH, for the parts of the API that
REST does not cover: labels, the entity registry, traces and to-do lists.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import sys
from urllib.parse import urlparse


class Socket:
    """A minimal client for unfragmented text frames."""

    def __init__(self, url: str) -> None:
        parts = urlparse(url)
        host, port = parts.hostname or "localhost", parts.port or 80
        self.sock = socket.create_connection((host, port), timeout=30)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET {parts.path} HTTP/1.1\r\nHost: {host}:{port}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(request.encode())
        self.buffer = b""
        while b"\r\n\r\n" not in self.buffer:
            self.buffer += self.sock.recv(4096)
        head, self.buffer = self.buffer.split(b"\r\n\r\n", 1)
        if b" 101 " not in head.split(b"\r\n", 1)[0]:
            raise ConnectionError(head.decode(errors="replace"))

    def send(self, message: object) -> None:
        """Send one masked text frame."""
        data = json.dumps(message).encode()
        mask = os.urandom(4)
        header = bytes([0x81])
        if len(data) < 126:
            header += bytes([0x80 | len(data)])
        elif len(data) < 65536:
            header += bytes([0x80 | 126]) + struct.pack(">H", len(data))
        else:
            header += bytes([0x80 | 127]) + struct.pack(">Q", len(data))
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(header + mask + masked)

    def _need(self, length: int) -> None:
        while len(self.buffer) < length:
            chunk = self.sock.recv(65536)
            if not chunk:
                raise EOFError("connection closed")
            self.buffer += chunk

    def receive(self) -> dict[str, object]:
        """Read one frame and decode its JSON."""
        self._need(2)
        length, offset = self.buffer[1] & 0x7F, 2
        if length == 126:
            self._need(4)
            length, offset = struct.unpack(">H", self.buffer[2:4])[0], 4
        elif length == 127:
            self._need(10)
            length, offset = struct.unpack(">Q", self.buffer[2:10])[0], 10
        self._need(offset + length)
        payload, self.buffer = self.buffer[offset : offset + length], self.buffer[offset + length :]
        result: dict[str, object] = json.loads(payload)
        return result


def main() -> int:
    """Authenticate, then relay stdin commands to stdout results."""
    url = os.environ.get("HA_WS_URL", "ws://172.30.32.1/api/websocket")
    token = os.environ["HA_TOKEN"]
    ws = Socket(url)
    if ws.receive().get("type") != "auth_required":
        raise ConnectionError("expected auth_required")
    ws.send({"type": "auth", "access_token": token})
    if ws.receive().get("type") != "auth_ok":
        raise PermissionError("authentication failed")
    for index, line in enumerate(sys.stdin, start=1):
        if not line.strip():
            continue
        command = json.loads(line)
        command["id"] = index
        ws.send(command)
        while True:
            reply = ws.receive()
            if reply.get("id") == index and reply.get("type") == "result":
                print(json.dumps(reply))
                break
    return 0


if __name__ == "__main__":
    sys.exit(main())
