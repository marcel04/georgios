"""Category API tests use real SQLAlchemy queries against isolated SQLite data.

PostgreSQL-specific migrations and triggers are outside these API contract tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import get_db
from app.main import app
from app.models import MenuCategory


@pytest.fixture
def category_api():
    """Create a fresh database and dependency override for each test case."""
    engine = create_engine(
        "sqlite://",
        # TestClient handles requests on another thread.
        connect_args={"check_same_thread": False},
        # Share one connection so both threads see the same in-memory database.
        poolclass=StaticPool,
    )
    # Only the table this endpoint queries is needed; no PostgreSQL triggers.
    MenuCategory.__table__.create(engine)

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
        engine.dispose()


def seed(engine, *categories):
    """Commit fixture rows so the request session can query them."""
    with Session(engine) as session:
        session.add_all(categories)
        session.commit()


def test_returns_active_categories(category_api):
    # Omitted is_active uses the model's true server default.
    client, engine = category_api
    seed(
        engine,
        MenuCategory(name="Pizza", description="Fresh pizza", display_order=1),
        MenuCategory(name="Drinks", description=None, display_order=2),
    )

    response = client.get("/api/menu/categories")

    assert response.status_code == 200
    assert [row["name"] for row in response.json()] == ["Pizza", "Drinks"]


def test_excludes_inactive_categories(category_api):
    # Mix visible and hidden records to verify filtering, not just an empty result.
    client, engine = category_api
    seed(
        engine,
        MenuCategory(name="Hidden", display_order=1, is_active=False),
        MenuCategory(name="Visible", display_order=2, is_active=True),
    )

    response = client.get("/api/menu/categories")

    assert response.status_code == 200
    assert [row["name"] for row in response.json()] == ["Visible"]


def test_orders_by_display_order_not_id_or_insertion(category_api):
    # Deliberately disagree with ID/insertion order to catch a missing ORDER BY.
    client, engine = category_api
    seed(
        engine,
        MenuCategory(id=1, name="Last", display_order=30),
        MenuCategory(id=2, name="First", display_order=10),
        MenuCategory(id=3, name="Middle", display_order=20),
    )

    response = client.get("/api/menu/categories")

    assert response.status_code == 200
    assert [row["id"] for row in response.json()] == [2, 3, 1]
    assert [row["display_order"] for row in response.json()] == [10, 20, 30]


# Cover both a genuinely empty table and a table containing only hidden rows.
@pytest.mark.parametrize("inactive_only", [False, True])
def test_no_active_categories_returns_empty_list(category_api, inactive_only):
    client, engine = category_api
    if inactive_only:
        seed(engine, MenuCategory(name="Hidden", display_order=1, is_active=False))

    response = client.get("/api/menu/categories")

    assert response.status_code == 200
    assert response.json() == []


def test_response_contains_only_public_fields(category_api):
    client, engine = category_api
    seed(
        engine,
        MenuCategory(id=10, name="Pizza", description="Fresh pizza", display_order=1),
        MenuCategory(id=20, name="Drinks", description=None, display_order=2),
    )

    response = client.get("/api/menu/categories")

    assert response.status_code == 200
    # Exact equality rejects leaked internal fields and verifies nullable descriptions.
    assert response.json() == [
        {"id": 10, "name": "Pizza", "description": "Fresh pizza", "display_order": 1},
        {"id": 20, "name": "Drinks", "description": None, "display_order": 2},
    ]
