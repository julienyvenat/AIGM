"""Small, environment-driven configuration helpers shared across the app.

Kept separate from src/main.py (and unit-testable on its own, see
src/__tests__/test_config.py) since main.py already does a lot at import
time (route registration, DB init lifespan, etc.).
"""
import os

# Permissive-but-not-wildcard default for local dev: the Vite dev server
# (5173) and CRA-style (3000) ports on localhost. Production sets
# CORS_ORIGINS explicitly (e.g. "https://jdr.yvenat.eu") -- see
# .env.production.example / docker-compose.prod.yml.
DEFAULT_DEV_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def get_cors_origins() -> list[str]:
    """Return the list of allowed CORS origins.

    Reads the comma-separated CORS_ORIGINS environment variable (e.g.
    "https://jdr.yvenat.eu,https://other.example.com"). Falls back to a
    localhost-only allowlist for dev when unset. Never returns a wildcard.
    """
    raw = os.getenv("CORS_ORIGINS")
    if not raw:
        return list(DEFAULT_DEV_CORS_ORIGINS)

    origins = [origin.strip() for origin in raw.split(",")]
    origins = [origin for origin in origins if origin]
    return origins or list(DEFAULT_DEV_CORS_ORIGINS)
