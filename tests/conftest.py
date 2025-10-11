"""Shared pytest configuration and stubs for external dependencies."""

from __future__ import annotations

import sys
import types
from pathlib import Path

# Ensure the project root is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _ensure_dotenv_stub() -> None:
    """Provide a minimal dotenv stub that no-ops on load."""
    if "dotenv" in sys.modules:
        return

    dotenv_stub = types.ModuleType("dotenv")

    def load_dotenv(*_args, **_kwargs):  # type: ignore[unused-argument]
        return None

    dotenv_stub.load_dotenv = load_dotenv  # type: ignore[attr-defined]
    sys.modules["dotenv"] = dotenv_stub


def _ensure_discord_stub() -> None:
    """Provide a lightweight discord module stub for tests."""
    if "discord" in sys.modules:
        return

    discord_stub = types.ModuleType("discord")

    class DummyColor:
        def __init__(self, value: int):
            self.value = value

        @classmethod
        def gold(cls) -> "DummyColor":
            return cls(0xFFD700)

        @classmethod
        def red(cls) -> "DummyColor":
            return cls(0xFF0000)

    class DummyEmbed:
        def __init__(self, title=None, description=None, color=None):
            self.title = title
            self.description = description
            self.color = color
            self.fields: list[dict[str, object]] = []

        def add_field(self, *, name, value, inline=False):
            self.fields.append({"name": name, "value": value, "inline": inline})

    class DummyUser:
        def __init__(self, user_id: int, mention: str | None = None):
            self.id = user_id
            self.mention = mention or f"<@{user_id}>"

    class DummyClient:
        def __init__(self, *, users=None, channels=None):
            self._users = users or {}
            self._channels = channels or {}

        async def fetch_user(self, user_id: int):  # pragma: no cover - simple stub
            if user_id in self._users:
                return self._users[user_id]
            raise DummyNotFound(f"User {user_id} not found")

        def get_channel(self, channel_id: int):  # pragma: no cover - simple stub
            return self._channels.get(channel_id)

    class DummyNotFound(Exception):
        """Exception raised when a Discord resource is not found."""

    discord_stub.Embed = DummyEmbed  # type: ignore[attr-defined]
    discord_stub.Color = DummyColor  # type: ignore[attr-defined]
    discord_stub.User = DummyUser  # type: ignore[attr-defined]
    discord_stub.NotFound = DummyNotFound  # type: ignore[attr-defined]
    discord_stub.abc = types.SimpleNamespace(User=DummyUser)
    discord_stub.Interaction = object  # type: ignore[attr-defined]
    discord_stub.Client = DummyClient  # type: ignore[attr-defined]

    sys.modules["discord"] = discord_stub
    sys.modules["discord.abc"] = discord_stub.abc  # type: ignore[assignment]


_ensure_dotenv_stub()
_ensure_discord_stub()
