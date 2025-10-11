"""Tests for `bingo.utils.channel_check`."""

from __future__ import annotations

import asyncio


def run(coro):
    return asyncio.run(coro)


class DummyResponse:
    def __init__(self):
        self.sent = None
        self.ephemeral = None
        self._done = False

    async def send_message(self, message, ephemeral=False):
        self.sent = message
        self.ephemeral = ephemeral
        self._done = True

    def is_done(self):
        return self._done


class DummyInteraction:
    def __init__(self, channel_id, allowed_channel=None):
        channel = None if allowed_channel is None else f"Channel {allowed_channel}"
        self.channel_id = channel_id
        from discord import Client

        self.client = Client(
            channels={allowed_channel: channel} if allowed_channel else {}
        )
        self.response = DummyResponse()
        self.followup = self.response


def test_is_allowed_channel_no_env(monkeypatch):
    from bingo.utils import channel_check

    monkeypatch.delenv("CHANNEL", raising=False)
    channel_check.ALLOWED_CHANNEL_ID = None
    interaction = DummyInteraction(channel_id=123)
    assert run(channel_check.is_allowed_channel(interaction)) is True


def test_is_allowed_channel_match(monkeypatch):
    from bingo.utils import channel_check

    monkeypatch.setenv("CHANNEL", "123")
    channel_check.ALLOWED_CHANNEL_ID = 123
    interaction = DummyInteraction(channel_id=123)
    assert run(channel_check.is_allowed_channel(interaction)) is True
    assert interaction.response.sent is None


def test_is_allowed_channel_mismatch(monkeypatch):
    from bingo.utils import channel_check

    monkeypatch.setenv("CHANNEL", "999")
    channel_check.ALLOWED_CHANNEL_ID = 999
    interaction = DummyInteraction(channel_id=123)
    result = run(channel_check.is_allowed_channel(interaction))
    assert result is False
    assert "This command can only be used" in interaction.response.sent


def test_require_allowed_channel_blocks(monkeypatch):
    from bingo.utils import channel_check

    monkeypatch.setenv("CHANNEL", "321")
    channel_check.ALLOWED_CHANNEL_ID = 321
    interaction = DummyInteraction(channel_id=123)

    called = {}

    @channel_check.require_allowed_channel
    async def dummy_handler(inter):
        called["ran"] = True
        return "ok"

    result = run(dummy_handler(interaction))
    assert result is None
    assert "ran" not in called
    assert "This command can only be used" in interaction.response.sent
