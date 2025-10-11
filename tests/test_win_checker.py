"""Tests for `bingo.utils.win_checker`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List

import pytest


class DummyDB:
    def __init__(self, boards: List[Dict[str, Any]], winners: Dict[int, int]):
        self._boards = boards
        self._winners = winners
        self.fetchall_calls: list = []
        self.fetchone_calls: list = []

    async def fetchall(self, query, params=None):
        self.fetchall_calls.append((query, params))
        return self._boards

    async def fetchone(self, query, params=None):
        self.fetchone_calls.append((query, params))
        board_id = params[1]
        closed = self._winners.get(board_id, 0)
        return {"closed_count": closed}


class DummyChannel:
    def __init__(self):
        self.messages: list = []

    async def send(self, embed=None):
        self.messages.append(embed)


class DummyBot:
    def __init__(self, fetch_map):
        self.fetch_map = fetch_map

    async def fetch_user(self, user_id):
        value = self.fetch_map.get(user_id)
        if isinstance(value, Exception):
            raise value
        return value


class DummyUser:
    def __init__(self, user_id):
        self.id = user_id
        self.mention = f"<@{user_id}>"

    def __str__(self):  # pragma: no cover - simple helper
        return self.mention


def run(coro):
    return asyncio.run(coro)


def test_check_for_winners_identifies_closed_board():
    from bingo.utils import win_checker

    grid_size = 2
    total = grid_size * grid_size
    boards = [
        {"board_id": 1, "user_id": 101},
        {"board_id": 2, "user_id": 102},
    ]
    winners = {1: total, 2: total - 1}
    dummy_db = DummyDB(boards, winners)

    result = run(
        win_checker.check_for_winners(dummy_db, game_id=5, grid_size=grid_size)
    )
    assert result == [101]
    assert len(dummy_db.fetchall_calls) == 1
    assert len(dummy_db.fetchone_calls) == 2


def test_check_for_winners_no_closed_boards():
    from bingo.utils import win_checker

    boards = [{"board_id": 1, "user_id": 101}]
    winners = {1: 3}
    dummy_db = DummyDB(boards, winners)

    result = run(win_checker.check_for_winners(dummy_db, game_id=5, grid_size=2))
    assert result == []


@pytest.mark.asyncio
async def test_announce_winners_sends_embed():
    from bingo.utils import win_checker

    channel = DummyChannel()
    user = DummyUser(200)
    bot = DummyBot({200: user})

    await win_checker.announce_winners(channel, [200], "Test Game", bot)
    assert channel.messages
    embed = channel.messages[0]
    assert "Test Game" in embed.description
    assert "<@200>" in embed.fields[0]["value"]


@pytest.mark.asyncio
async def test_announce_winners_handles_fetch_failure():
    from bingo.utils import win_checker
    import discord

    channel = DummyChannel()
    bot = DummyBot({300: discord.NotFound(None, None)})

    await win_checker.announce_winners(channel, [300], "Oops", bot)
    embed = channel.messages[0]
    assert "User ID: 300" in embed.fields[0]["value"]
