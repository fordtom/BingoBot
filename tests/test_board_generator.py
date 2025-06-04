import pytest
import asyncio
import importlib.util
import os
import sys
import random

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BOARD_GENERATOR_PATH = os.path.join(BASE_DIR, "bingo", "utils", "board_generator.py")

spec = importlib.util.spec_from_file_location("board_generator", BOARD_GENERATOR_PATH)
board_generator = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = board_generator
spec.loader.exec_module(board_generator)

generate_board = board_generator.generate_board


def test_generate_board_success_deterministic():
    random.seed(0)
    events = [{"event_id": i} for i in range(1, 9)]
    result = asyncio.run(generate_board(events, grid_size=2))
    assert len(result) == 4
    # Expected order from random.seed(0)
    expected_ids = [7, 8, 4, 1]
    assert [sq["event_id"] for sq in result] == expected_ids
    # Validate positions
    assert result[0]["row"] == 0 and result[0]["column"] == 0
    assert result[-1]["row"] == 1 and result[-1]["column"] == 1


def test_generate_board_not_enough_events():
    events = [{"event_id": 1}, {"event_id": 2}]
    with pytest.raises(ValueError):
        asyncio.run(generate_board(events, grid_size=2))


