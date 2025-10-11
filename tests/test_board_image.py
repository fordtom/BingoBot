"""Tests for `bingo.utils.board_image`."""

from __future__ import annotations

import asyncio

import pytest


def run(coro):
    return asyncio.run(coro)


def _sample_grid(grid_size, status="OPEN"):
    return [
        [
            {
                "description": f"Row {row} Col {col}",
                "status": status,
            }
            for col in range(grid_size)
        ]
        for row in range(grid_size)
    ]


def test_generate_bingo_board_image_basic(tmp_path):
    from bingo.utils import board_image

    grid_size = 2
    grid = _sample_grid(grid_size)

    result = run(board_image.generate_bingo_board_image(grid, grid_size))
    assert result.read(4) == b"\x89PNG"


def test_generate_bingo_board_image_closed_colours(tmp_path):
    from bingo.utils import board_image

    grid_size = 2
    grid = _sample_grid(grid_size, status="CLOSED")

    result = run(board_image.generate_bingo_board_image(grid, grid_size))
    assert result.read(4) == b"\x89PNG"
