# ------------------------------------------------------------------------------
# File: oled_status/src/oled_status/pages/dino.py
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

"""Dinosaur pages: a mood dinosaur, and one running away across the screen."""

from __future__ import annotations

import math
import random
from typing import Final

from PIL import ImageDraw

from oled_status.icons import draw_icon, draw_rows
from oled_status.pages.common import HEIGHT, WIDTH, Frame, Page, font

# A small T-rex facing right, built from a head, a body and a pair of legs.
_HEAD_HAPPY: Final = (
    "..........#########.",
    ".........##.#######.",
    ".........##########.",
    ".........##########.",
    ".........#####......",
    ".........########...",
)
_HEAD_WORRIED: Final = (
    "..........#########.",
    ".........##.#######.",
    ".........##########.",
    ".........##########.",
    ".........##.........",
    ".........#######....",
)
_BODY: Final = (
    "#.......#######.....",
    "#......########.....",
    "##....#########.....",
    "###..############...",
    "####.##########.##..",
    ".##############.....",
    "..############......",
    "...##########.......",
    "....#########.......",
    ".....#######........",
)
_LEGS_STANDING: Final = (
    "......##...##.......",
    "......##...##.......",
    "......##...##.......",
    "......###..###......",
)
_LEGS_LEFT: Final = (
    "......##...##.......",
    "......##...###......",
    "......##............",
    "......###...........",
)
_LEGS_RIGHT: Final = (
    "......##...##.......",
    "......###..##.......",
    "...........##.......",
    "...........###......",
)
_CACTUS: Final = (
    "...##...",
    "...##...",
    "#..##...",
    "#..##.##",
    "#..##.##",
    "#..##.##",
    "####..##",
    "...####.",
    "...##...",
    "...##...",
    "...##...",
    "...##...",
)

DINO_WIDTH = 20
DINO_HEIGHT = 20
EYE_ROW = 1
EYE_COLUMN = 11

RUN_SPEED = 2  # world pixels per tick
RUN_DINO_X = 12
GROUND_Y = 57
JUMP_HEIGHT = 18
JUMP_PIXELS = 56  # ground covered during one jump
CACTUS_WIDTH = 8
CACTUS_HEIGHT = 12
STRIDE_TICKS = 3


def sprite(
    head: tuple[str, ...], legs: tuple[str, ...], *, eyes_shut: bool = False
) -> tuple[str, ...]:
    """Assemble a dinosaur from its parts, optionally with the eye closed."""
    if eyes_shut:
        line = head[EYE_ROW]
        head = (
            *head[:EYE_ROW],
            line[:EYE_COLUMN] + "#" + line[EYE_COLUMN + 1 :],
            *head[EYE_ROW + 1 :],
        )
    return (*head, *_BODY, *legs)


def _dino(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """A dinosaur that bounces when all is well and sweats when there are alerts."""
    worried = bool(frame.alerts)
    scale = 2
    x = (WIDTH - DINO_WIDTH * scale) // 2
    y = HEIGHT - 14 - DINO_HEIGHT * scale
    if worried:
        x += 2 if frame.tick // 2 % 2 else -2
        rows = sprite(_HEAD_WORRIED, _LEGS_STANDING)
        for index in range(2):
            drop_y = y + (frame.tick * 2 + index * 8) % 16
            drop_x = x + DINO_WIDTH * scale + 4 + index * 5
            draw.rectangle((drop_x, drop_y, drop_x + 1, drop_y + 3), fill="white")
    else:
        blink = frame.tick % 40 >= 38
        if frame.tick // 5 % 2:
            y -= 2
        rows = sprite(_HEAD_HAPPY, _LEGS_STANDING, eyes_shut=blink)
    draw_rows(draw, rows, x, y, scale)
    ground = HEIGHT - 13
    draw.line((x - 12, ground, x + DINO_WIDTH * scale + 12, ground), fill="white")


def _cactus_cycle() -> tuple[tuple[int, ...], int]:
    """World x of each cactus in one loop of the course, and the loop length."""
    rng = random.Random(2024)  # noqa: S311 - decoration, not security
    positions: list[int] = []
    cursor = 0
    for _ in range(12):
        cursor += rng.randrange(80, 160)
        positions.append(cursor)
    return tuple(positions), cursor + 80


_CACTI, _COURSE_LENGTH = _cactus_cycle()


def cactus_positions(tick: int) -> list[int]:
    """Screen x of every cactus near or on the screen at `tick`."""
    offset = tick * RUN_SPEED
    return sorted(
        x for position in _CACTI if (x := (position - offset + 64) % _COURSE_LENGTH - 64) < WIDTH
    )


def jump_height(tick: int) -> int:
    """How far above the ground the runner is at `tick`, clearing the next cactus."""
    feet = RUN_DINO_X + DINO_WIDTH // 2
    for x in cactus_positions(tick):
        distance = x + CACTUS_WIDTH // 2 - feet
        if -JUMP_PIXELS // 2 <= distance < JUMP_PIXELS // 2:
            progress = (JUMP_PIXELS // 2 - distance) / JUMP_PIXELS
            return round(JUMP_HEIGHT * math.sin(math.pi * progress))
    return 0


def _dino_run(draw: ImageDraw.ImageDraw, frame: Frame) -> None:
    """The dinosaur runs away across a scrolling desert, hopping over cacti."""
    tick = frame.tick
    for index, cloud_y in enumerate((8, 16)):
        cloud_x = WIDTH - (tick // 4 + index * 70) % (WIDTH + 24)
        draw_icon(draw, "cloud", cloud_x, cloud_y)
    draw.line((0, GROUND_Y, WIDTH - 1, GROUND_Y), fill="white")
    rng = random.Random(7)  # noqa: S311 - decoration, not security
    for _ in range(10):
        pebble = (rng.randrange(WIDTH) - tick * RUN_SPEED) % WIDTH
        draw.point((pebble, GROUND_Y + 2 + rng.randrange(4)), fill="white")
    for x in cactus_positions(tick):
        draw_rows(draw, _CACTUS, x, GROUND_Y - CACTUS_HEIGHT)
    height = jump_height(tick)
    stride = _LEGS_LEFT if tick // STRIDE_TICKS % 2 else _LEGS_RIGHT
    legs = _LEGS_STANDING if height else stride
    draw_rows(draw, sprite(_HEAD_HAPPY, legs), RUN_DINO_X, GROUND_Y - DINO_HEIGHT - height)
    score = f"{tick // 5 % 100000:05d}"
    draw.text((WIDTH - 32, -1), score, font=font(10), fill="white")


PAGES: dict[str, Page] = {
    "dino": Page(_dino, animated=True),
    "dino_run": Page(_dino_run, animated=True),
}
