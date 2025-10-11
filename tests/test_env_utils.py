"""Tests for `utils.env_utils`."""

from __future__ import annotations

import os


def test_get_discord_token(monkeypatch):
    from utils import env_utils

    monkeypatch.setenv("DISCORD_TOKEN", "token123")
    assert env_utils.get_discord_token() == "token123"


def test_get_discord_token_missing(monkeypatch):
    from utils import env_utils

    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    try:
        env_utils.get_discord_token()
    except ValueError as exc:
        assert "DISCORD_TOKEN" in str(exc)
    else:  # pragma: no cover - ensure exception path exercised
        assert False, "Expected ValueError"


def test_get_allowed_channel_id(monkeypatch):
    from utils import env_utils

    monkeypatch.setenv("CHANNEL", "12345")
    assert env_utils.get_allowed_channel_id() == 12345


def test_get_allowed_channel_id_invalid(monkeypatch):
    from utils import env_utils

    monkeypatch.setenv("CHANNEL", "notint")
    assert env_utils.get_allowed_channel_id() is None


def test_get_allowed_channel_id_missing(monkeypatch):
    from utils import env_utils

    monkeypatch.delenv("CHANNEL", raising=False)
    assert env_utils.get_allowed_channel_id() is None
