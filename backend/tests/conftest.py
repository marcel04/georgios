"""Allow ordinary API tests to import the app without local credentials."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

# Opt-in PostgreSQL tests intentionally use the configured development database.
if os.environ.get("GEO20_DB_TESTS") != "1":
    # conftest loads before test modules import the app and validate settings.
    # setdefault preserves explicitly supplied environment values.
    os.environ.setdefault("FRONTEND_URL", "http://localhost:3000")
    os.environ.setdefault("DATABASE_URL", "sqlite://")


@pytest.fixture
def menu_engine():
    """Create an isolated database with real foreign-key cascade enforcement."""
    from app.models import MenuCategory, MenuItem, MenuItemVariant

    engine = create_engine(
        "sqlite://",
        # TestClient handles requests on another thread.
        connect_args={"check_same_thread": False},
        # Share one connection so both threads see the same in-memory database.
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # API contract tests need the core menu tables, not PostgreSQL triggers.
    for model in (MenuCategory, MenuItem, MenuItemVariant):
        model.__table__.create(engine)

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def menu_api(menu_engine):
    """Exercise the real API with the isolated menu database."""
    from app.database import get_db
    from app.main import app

    engine = menu_engine

    def override_db():
        # Each request gets its own session, closed by the context manager.
        with Session(engine) as session:
            yield session

    # Replace only the database dependency; exercise the real route and schema.
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            yield client, engine
    finally:
        # Restore global app state even after a failing assertion.
        app.dependency_overrides.clear()
        app.dependency_overrides.update(previous_overrides)
