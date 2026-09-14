"""Allow ordinary API tests to import the app without local credentials."""

import os

# Opt-in PostgreSQL tests intentionally use the configured development database.
if os.environ.get("GEO20_DB_TESTS") != "1":
    # conftest loads before test modules import the app and validate settings.
    # setdefault preserves explicitly supplied environment values.
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("DATABASE_URL", "sqlite://")
