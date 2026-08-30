"""Startup configuration and the timestamp helper."""

import importlib
import sys
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest

from app.utils.time import utc_now


# ------------------------------------------------------------------ time --

def test_utc_now_is_timezone_aware():
    """The whole point of replacing datetime.utcnow(). A naive datetime
    cannot be compared to an aware one without raising, and nothing about
    it records that it was UTC."""
    now = utc_now()

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)


def test_utc_now_can_be_compared_to_other_aware_datetimes():
    assert utc_now() > datetime(2020, 1, 1, tzinfo=timezone.utc)


# ---------------------------------------------------------------- config --

def _reload_config(monkeypatch, **environment):
    """Re-imports app.config with a specific environment.

    `load_dotenv()` inside the module must not be allowed to refill a
    variable this test just removed, so it is stubbed out.
    """
    monkeypatch.setattr("dotenv.load_dotenv", lambda *args, **kwargs: False)

    for name in ("DATABASE_URL", "SECRET_KEY", "ALGORITHM"):
        monkeypatch.delenv(name, raising=False)

    for name, value in environment.items():
        monkeypatch.setenv(name, value)

    sys.modules.pop("app.config", None)
    return importlib.import_module("app.config")


@pytest.fixture(autouse=True)
def restore_config():
    """Whatever a test in this module does to app.config, put the real one
    back afterwards — every other module holds references into it."""
    yield
    sys.modules.pop("app.config", None)
    importlib.import_module("app.config")


def test_missing_database_url_fails_at_import(monkeypatch):
    with pytest.raises(Exception) as caught:
        _reload_config(monkeypatch, SECRET_KEY="x")

    assert "DATABASE_URL" in str(caught.value)


def test_missing_secret_key_fails_at_import(monkeypatch):
    """It used to start fine and then fail on the first login attempt,
    with an error from inside the JWT library."""
    with pytest.raises(Exception) as caught:
        _reload_config(monkeypatch, DATABASE_URL="postgresql://a/b")

    assert "SECRET_KEY" in str(caught.value)


def test_blank_secret_key_counts_as_missing(monkeypatch):
    with pytest.raises(Exception) as caught:
        _reload_config(
            monkeypatch,
            DATABASE_URL="postgresql://a/b",
            SECRET_KEY="   ",
        )

    assert "SECRET_KEY" in str(caught.value)


def test_algorithm_defaults_when_absent(monkeypatch):
    config = _reload_config(
        monkeypatch,
        DATABASE_URL="postgresql://a/b",
        SECRET_KEY="x",
    )

    assert config.ALGORITHM == "HS256"


def test_error_message_says_how_to_fix_it(monkeypatch):
    with pytest.raises(Exception) as caught:
        _reload_config(monkeypatch, SECRET_KEY="x")

    message = str(caught.value)
    assert ".env" in message
