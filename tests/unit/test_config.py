"""Tests for application configuration."""
from __future__ import annotations

import pytest


class TestSettings:
    def test_settings_loads_from_env(self, monkeypatch):
        monkeypatch.setenv("SECRET_KEY", "test-secret")
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
        # Re-import to pick up patched env
        import importlib

        import config
        importlib.reload(config)
        # Basic sanity: module imports without error

    def test_missing_secret_key_raises(self, monkeypatch):
        monkeypatch.delenv("SECRET_KEY", raising=False)
        monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost/db")
        import importlib

        from pydantic import ValidationError

        import config
        with pytest.raises(ValidationError):
            importlib.reload(config)
            # Force a fresh settings instantiation
            config.Settings()
