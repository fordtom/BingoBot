import asyncio
import importlib.util
import os
import sys
import types
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHANNEL_CHECK_PATH = os.path.join(BASE_DIR, "bingo", "utils", "channel_check.py")
ENV_UTILS_PATH = os.path.join(BASE_DIR, "bingo", "utils", "env_utils.py")


def load_channel_check(env_value=None):
    if env_value is not None:
        os.environ['CHANNEL'] = str(env_value)
    elif 'CHANNEL' in os.environ:
        del os.environ['CHANNEL']
    # Provide a minimal stub for the discord module so the util can import it
    if 'discord' not in sys.modules:
        stub = types.ModuleType('discord')
        class DummyUser: pass
        stub.Interaction = object
        stub.User = DummyUser
        stub.Embed = object
        stub.Color = types.SimpleNamespace(gold=lambda: None, red=lambda: None)
        app_commands_stub = types.SimpleNamespace(Group=lambda *a, **k: None)
        stub.app_commands = app_commands_stub
        sys.modules['discord'] = stub
    # Stub out dotenv.load_dotenv to avoid dependency on python-dotenv
    if 'dotenv' not in sys.modules:
        dotenv_stub = types.ModuleType('dotenv')
        def load_dotenv():
            return None
        dotenv_stub.load_dotenv = load_dotenv
        sys.modules['dotenv'] = dotenv_stub
    # Provide stub bingo package with env_utils
    if 'bingo' not in sys.modules:
        bingo_pkg = types.ModuleType('bingo')
        utils_pkg = types.ModuleType('bingo.utils')
        bingo_pkg.utils = utils_pkg
        sys.modules['bingo'] = bingo_pkg
        sys.modules['bingo.utils'] = utils_pkg
    if 'bingo.utils.env_utils' not in sys.modules:
        env_spec = importlib.util.spec_from_file_location('bingo.utils.env_utils', ENV_UTILS_PATH)
        env_module = importlib.util.module_from_spec(env_spec)
        sys.modules['bingo.utils.env_utils'] = env_module
        env_spec.loader.exec_module(env_module)
    if BASE_DIR not in sys.path:
        sys.path.insert(0, BASE_DIR)
    spec = importlib.util.spec_from_file_location("bingo.utils.channel_check", CHANNEL_CHECK_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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


class DummyClient:
    def __init__(self, channel=None):
        self._channel = channel

    def get_channel(self, channel_id):
        return self._channel


class DummyInteraction:
    def __init__(self, channel_id, client):
        self.channel_id = channel_id
        self.client = client
        self.response = DummyResponse()
        self.followup = self.response


def test_is_allowed_channel_no_env():
    module = load_channel_check(None)
    interaction = DummyInteraction(channel_id=123, client=DummyClient())
    assert asyncio.run(module.is_allowed_channel(interaction)) is True


def test_is_allowed_channel_match():
    module = load_channel_check(123)
    interaction = DummyInteraction(channel_id=123, client=DummyClient())
    assert asyncio.run(module.is_allowed_channel(interaction)) is True
    assert interaction.response.sent is None


def test_is_allowed_channel_mismatch():
    module = load_channel_check(999)
    interaction = DummyInteraction(channel_id=123, client=DummyClient(channel="chan"))
    result = asyncio.run(module.is_allowed_channel(interaction))
    assert result is False
    assert "This command can only be used" in interaction.response.sent


