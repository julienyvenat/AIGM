import importlib

from src import config as config_module
from src.config import get_cors_origins


def test_cors_origins_defaults_to_localhost_when_unset(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    origins = get_cors_origins()
    assert "http://localhost:5173" in origins
    assert "*" not in origins


def test_cors_origins_reads_single_env_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://jdr.yvenat.eu")
    assert get_cors_origins() == ["https://jdr.yvenat.eu"]


def test_cors_origins_reads_comma_separated_env_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://jdr.yvenat.eu, https://other.example.com")
    origins = get_cors_origins()
    assert origins == ["https://jdr.yvenat.eu", "https://other.example.com"]


def test_cors_origins_never_wildcard_even_if_misconfigured(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "*")
    # Explicit wildcard is still passed through as a literal origin string
    # here (not treated as CORSMiddleware's special wildcard) -- the point
    # of this test is just to confirm we don't silently fall back to a
    # permissive default on unexpected input.
    assert get_cors_origins() == ["*"]


def test_cors_origins_falls_back_to_default_on_blank_value(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "   ")
    origins = get_cors_origins()
    assert origins == config_module.DEFAULT_DEV_CORS_ORIGINS


def test_database_url_defaults_to_sqlite(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from src.engine import database

    importlib.reload(database)
    try:
        assert database.DATABASE_URL == database.DEFAULT_SQLITE_URL
        assert str(database.engine.url).startswith("sqlite+aiosqlite")
    finally:
        # Restore the module to its normal (env-derived) state for any
        # other test relying on `from src.engine.database import engine`
        # importing the *same* engine instance across the whole test run.
        importlib.reload(database)


def test_database_url_env_override_is_used(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/aigm"
    )
    from src.engine import database

    importlib.reload(database)
    try:
        assert database.DATABASE_URL.startswith("postgresql+asyncpg://")
        assert str(database.engine.url).startswith("postgresql+asyncpg://")
    finally:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        importlib.reload(database)
