"""GEO-22 API contracts, using a fresh SQLAlchemy database for every test."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.models import MenuCategory, MenuItem, MenuItemVariant


@pytest.fixture
def item_api(menu_api):
    client, engine = menu_api
    # IDs/insertion order deliberately differ from display order at both levels.
    with Session(engine) as session:
        session.add_all(
            [
                MenuCategory(id=1, name="Pizza", display_order=1),
                MenuCategory(id=2, name="Subs", display_order=2),
                MenuCategory(id=3, name="Hidden", display_order=3, is_active=False),
            ]
        )
        session.flush()
        session.add_all(
            [
                MenuItem(id=10, category_id=1, name="Last", display_order=30),
                MenuItem(
                    id=20,
                    category_id=1,
                    name="First",
                    display_order=10,
                    description="Cheese pizza",
                    image_url="/images/cheese.jpg",
                ),
                MenuItem(id=30, category_id=1, name="Middle", display_order=20),
                MenuItem(
                    id=40,
                    category_id=1,
                    name="Unavailable",
                    display_order=5,
                    is_available=False,
                ),
                MenuItem(id=50, category_id=2, name="Italian Sub", display_order=1),
                MenuItem(id=60, category_id=3, name="Hidden item", display_order=1),
            ]
        )
        session.flush()
        session.add_all(
            [
                MenuItemVariant(
                    id=100,
                    menu_item_id=20,
                    name="Large",
                    price=Decimal("18.50"),
                    display_order=30,
                ),
                MenuItemVariant(
                    id=200,
                    menu_item_id=20,
                    name="Small",
                    price=Decimal("10.25"),
                    display_order=10,
                ),
                MenuItemVariant(
                    id=300,
                    menu_item_id=20,
                    name="Medium",
                    price=Decimal("14.00"),
                    display_order=20,
                ),
                MenuItemVariant(
                    id=400,
                    menu_item_id=20,
                    name="Unavailable",
                    price=Decimal("9.00"),
                    display_order=5,
                    is_available=False,
                ),
            ]
        )
        session.commit()
    return client


def test_returns_available_items_only_from_requested_category(item_api):
    response = item_api.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    assert {item["id"] for item in response.json()} == {10, 20, 30}


def test_items_are_ordered_by_display_order(item_api):
    response = item_api.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    assert [item["id"] for item in response.json()] == [20, 30, 10]
    assert [item["display_order"] for item in response.json()] == [10, 20, 30]


def test_includes_only_available_variants(item_api):
    response = item_api.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    item = next(item for item in response.json() if item["id"] == 20)
    assert {variant["id"] for variant in item["variants"]} == {100, 200, 300}


def test_variants_are_ordered_by_display_order(item_api):
    response = item_api.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    item = next(item for item in response.json() if item["id"] == 20)
    assert [variant["id"] for variant in item["variants"]] == [200, 300, 100]
    assert [variant["display_order"] for variant in item["variants"]] == [10, 20, 30]


@pytest.mark.parametrize("category_id", [999, 3], ids=["missing", "inactive"])
def test_missing_or_inactive_category_returns_404(item_api, category_id):
    response = item_api.get(f"/api/menu/categories/{category_id}/items")

    assert response.status_code == 404
    assert response.json() == {"detail": "Menu category not found"}


@pytest.mark.parametrize("unavailable_only", [False, True])
def test_no_available_items_returns_empty_list(menu_api, unavailable_only):
    client, engine = menu_api
    with Session(engine) as session:
        category = MenuCategory(id=1, name="Pizza", display_order=1)
        if unavailable_only:
            category.items = [
                MenuItem(name="Unavailable", display_order=1, is_available=False)
            ]
        session.add(category)
        session.commit()

    response = client.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    assert response.json() == []


def test_response_contains_only_public_item_and_variant_fields(item_api):
    response = item_api.get("/api/menu/categories/1/items")

    assert response.status_code == 200
    items = response.json()
    for item in items:
        assert set(item) == {
            "id",
            "name",
            "description",
            "image_url",
            "display_order",
            "variants",
        }
        for variant in item["variants"]:
            assert set(variant) == {"id", "name", "price", "display_order"}

    # Decimal prices serialize as strings, preserving the monetary precision.
    assert items[0] == {
        "id": 20,
        "name": "First",
        "description": "Cheese pizza",
        "image_url": "/images/cheese.jpg",
        "display_order": 10,
        "variants": [
            {"id": 200, "name": "Small", "price": "10.25", "display_order": 10},
            {"id": 300, "name": "Medium", "price": "14.00", "display_order": 20},
            {"id": 100, "name": "Large", "price": "18.50", "display_order": 30},
        ],
    }
    assert items[1]["description"] is None
    assert items[1]["image_url"] is None
    assert items[1]["variants"] == []
