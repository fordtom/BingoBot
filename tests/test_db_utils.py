"""Tests for `bingo.utils.db_utils`."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, List, Optional

import pytest


def _maybe_await(value):
    if asyncio.iscoroutine(value) or isinstance(value, Awaitable):
        return value
    fut = asyncio.Future()
    fut.set_result(value)
    return fut


class DummyResponse:
    def __init__(self):
        self._done = False
        self.messages: list[tuple[Any, dict[str, Any]]] = []

    def is_done(self) -> bool:  # pragma: no cover - simple property
        return self._done

    async def send_message(self, content=None, **kwargs):
        self._done = True
        self.messages.append((content, kwargs))


class DummyFollowup:
    def __init__(self, response: DummyResponse):
        self._response = response

    async def send(self, content=None, **kwargs):
        self._response.messages.append((content, kwargs))


class DummyInteraction:
    def __init__(self):
        self.response = DummyResponse()
        self.followup = DummyFollowup(self.response)


@dataclass
class DummyDB:
    fetchone_result: Any = None
    fetchall_result: Optional[List[Any]] = None
    fetchone_handler: Optional[Callable[[str, tuple[Any, ...]], Any]] = None
    fetchall_handler: Optional[Callable[[str, tuple[Any, ...]], Any]] = None
    fetchone_calls: list = field(default_factory=list)
    fetchall_calls: list = field(default_factory=list)

    async def fetchone(self, query, params=None):
        params = tuple(params or ())
        self.fetchone_calls.append((query, params))
        if self.fetchone_handler is not None:
            return await _maybe_await(self.fetchone_handler(query, params))
        return self.fetchone_result

    async def fetchall(self, query, params=None):
        params = tuple(params or ())
        self.fetchall_calls.append((query, params))
        if self.fetchall_handler is not None:
            return await _maybe_await(self.fetchall_handler(query, params))
        return self.fetchall_result or []


def run(coro):
    return asyncio.run(coro)


def test_get_active_game_uses_provided_db():
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"game_id": 42})
    result = run(db_utils.get_active_game(dummy))
    assert result == {"game_id": 42}
    assert len(dummy.fetchone_calls) == 1
    query, params = dummy.fetchone_calls[0]
    assert "FROM games" in query
    assert params == ()


def test_get_active_game_fetches_handler(monkeypatch):
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"game_id": 7})
    calls: list[int] = []

    async def fake_get_db_handler():
        calls.append(1)
        return dummy

    monkeypatch.setattr("db.get_db_handler", fake_get_db_handler)

    result = run(db_utils.get_active_game())
    assert result == {"game_id": 7}
    assert calls == [1]


def test_get_game_by_id(monkeypatch):
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"game_id": 5})

    async def fake_get_db_handler():
        return dummy

    monkeypatch.setattr("db.get_db_handler", fake_get_db_handler)

    result = run(db_utils.get_game_by_id(5))
    assert result == {"game_id": 5}
    assert dummy.fetchone_calls[0][1] == (5,)


def test_get_or_validate_game_with_id_found():
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"game_id": 9})
    interaction = DummyInteraction()

    result = run(db_utils.get_or_validate_game(interaction, game_id=9, db=dummy))
    assert result == {"game_id": 9}
    assert interaction.response.messages == []


def test_get_or_validate_game_with_id_missing_sends_error():
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result=None)
    interaction = DummyInteraction()

    result = run(db_utils.get_or_validate_game(interaction, game_id=11, db=dummy))
    assert result is None
    assert interaction.response.messages
    message, kwargs = interaction.response.messages[0]
    assert "Game with ID 11" in message
    assert kwargs.get("ephemeral") is True


def test_get_or_validate_game_uses_active_game(monkeypatch):
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"game_id": 2})
    interaction = DummyInteraction()

    result = run(db_utils.get_or_validate_game(interaction, db=dummy))
    assert result == {"game_id": 2}
    assert interaction.response.messages == []


def test_get_or_validate_game_no_active_game(monkeypatch):
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result=None)
    interaction = DummyInteraction()

    result = run(db_utils.get_or_validate_game(interaction, db=dummy))
    assert result is None
    assert interaction.response.messages
    message, kwargs = interaction.response.messages[0]
    assert "No active game" in message
    assert kwargs.get("ephemeral") is True


def test_check_user_in_game_true():
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result={"exists": 1})
    result = run(db_utils.check_user_in_game(3, 99, db=dummy))
    assert result is True
    assert dummy.fetchone_calls[0][1] == (3, 99)


def test_check_user_in_game_false():
    from bingo.utils import db_utils

    dummy = DummyDB(fetchone_result=None)
    result = run(db_utils.check_user_in_game(4, 88, db=dummy))
    assert result is False


def test_fetch_events_for_game():
    from bingo.utils import db_utils

    events = [{"event_id": 1}, {"event_id": 2}]
    dummy = DummyDB(fetchall_result=events)

    result = run(db_utils.fetch_events_for_game(5, db=dummy))
    assert result == events
    assert dummy.fetchall_calls[0][1] == (5,)


def test_send_error_message_uses_response():
    from bingo.utils import db_utils

    interaction = DummyInteraction()

    run(db_utils.send_error_message(interaction, "Oops"))
    assert interaction.response.messages
    message, kwargs = interaction.response.messages[0]
    embed = kwargs["embed"]
    assert embed.title == "Error"
    assert "Oops" in embed.description
    assert kwargs.get("ephemeral") is True


def test_send_error_message_uses_followup_when_done():
    from bingo.utils import db_utils

    interaction = DummyInteraction()
    run(interaction.response.send_message("already"))

    run(db_utils.send_error_message(interaction, "Second"))
    # First message from initial send, second from followup
    assert len(interaction.response.messages) == 2
    message, kwargs = interaction.response.messages[1]
    embed = kwargs["embed"]
    assert embed.description == "Second"
    assert kwargs.get("ephemeral") is True
