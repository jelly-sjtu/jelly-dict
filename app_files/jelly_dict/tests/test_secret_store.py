from __future__ import annotations

import json

import pytest

from app.storage import secret_store


@pytest.fixture(autouse=True)
def _isolated_keyring(monkeypatch):
    """In-memory backend so tests never touch the real macOS Keychain."""
    pytest.importorskip("keyring")
    import keyring
    from keyring.backend import KeyringBackend

    class _MemBackend(KeyringBackend):
        priority = 1

        def __init__(self):
            self._store = {}

        def get_password(self, service, username):
            return self._store.get((service, username))

        def set_password(self, service, username, password):
            self._store[(service, username)] = password

        def delete_password(self, service, username):
            self._store.pop((service, username), None)

    keyring.set_keyring(_MemBackend())
    monkeypatch.delenv("JELLY_DICT_GOOGLE_VISION_API_KEY", raising=False)


def test_set_get_delete_round_trip():
    secret_store.set("google_vision_api_key", "secret-abc-123")
    assert secret_store.get("google_vision_api_key") == "secret-abc-123"
    assert secret_store.is_set("google_vision_api_key")
    secret_store.delete("google_vision_api_key")
    assert secret_store.get("google_vision_api_key") is None
    assert not secret_store.is_set("google_vision_api_key")


def test_empty_value_deletes_existing():
    secret_store.set("google_vision_api_key", "x")
    secret_store.set("google_vision_api_key", "")
    assert secret_store.get("google_vision_api_key") is None


def test_env_var_fallback(monkeypatch):
    monkeypatch.setenv("JELLY_DICT_GOOGLE_VISION_API_KEY", "from-env")
    assert secret_store.get("google_vision_api_key") == "from-env"


def test_settings_json_never_contains_secret(tmp_path, monkeypatch):
    monkeypatch.setenv("JELLY_DICT_HOME", str(tmp_path))
    from app.storage.settings_store import Settings, SettingsStore

    secret_store.set("google_vision_api_key", "MY-SECRET-KEY-ABCDEFG")
    store = SettingsStore(path=tmp_path / "settings.json")
    s = Settings()
    store.save(s)
    raw = (tmp_path / "settings.json").read_text(encoding="utf-8")
    assert "MY-SECRET-KEY-ABCDEFG" not in raw
    # Also verify the dataclass itself does not surface the key.
    serialized = json.dumps(s.to_dict())
    assert "MY-SECRET-KEY-ABCDEFG" not in serialized


def test_mask_helper():
    assert secret_store.mask("") == ""
    assert secret_store.mask("abcd") == "••••"
    masked = secret_store.mask("abcdefghijklmnop")
    assert "abcd" in masked and "…" in masked
