"""Real API/ORM tests; GEO27_DB_TESTS=1 also exercises PostgreSQL defaults."""

import os
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.main import app
from app.models import Cart, CartStatus, MenuCategory
from app.services import cart as service


@pytest.fixture(params=["sqlite", "postgresql"])
def cart_api(request, menu_engine):
    if request.param == "postgresql":
        if os.environ.get("GEO27_DB_TESTS") != "1":
            pytest.skip("Requires GEO27_DB_TESTS=1")
        from app.database import engine
    else:
        engine = menu_engine
        with engine.connect() as connection:
            connection.connection.driver_connection.create_function(
                "gen_random_uuid", 0, lambda: uuid4().hex
            )
    with engine.connect() as connection:
        transaction = connection.begin()

        def override_db():
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as db:
                yield db

        previous = app.dependency_overrides.copy()
        app.dependency_overrides[get_db] = override_db
        try:
            with TestClient(app) as client:
                yield client, connection
        finally:
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous)
            transaction.rollback()


def utc(value):
    if isinstance(value, str):
        value = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return (
        value.replace(tzinfo=timezone.utc)
        if value.tzinfo is None
        else value.astimezone(timezone.utc)
    )


@pytest.mark.parametrize("body", [None, {}])
def test_create_and_read(cart_api, body, monkeypatch):
    client, connection = cart_api
    before = service.server_now()
    response = client.post("/api/carts", **({"json": body} if body is not None else {}))
    after = service.server_now()
    assert response.status_code == 201
    data = response.json()
    assert UUID(data["id"]).version == 4
    location = f"/api/carts/{data['id']}"
    assert response.headers["location"] == location
    assert data == dict(
        id=data["id"],
        status="ACTIVE",
        expires_at=data["expires_at"],
        item_count=0,
        subtotal="0.00",
        items=[],
    )
    assert (
        before + timedelta(minutes=10)
        <= utc(data["expires_at"])
        <= after + timedelta(minutes=10)
    )
    with Session(connection) as db:
        row = db.get(Cart, UUID(data["id"]))
        assert row.status == CartStatus.ACTIVE
        deadline, updated = row.expires_at, row.updated_at
    monkeypatch.setattr(service, "server_now", lambda: before + timedelta(minutes=5))
    for _ in range(2):
        fetched = client.get(location)
        assert fetched.status_code == 200
        assert fetched.json() == data
    with Session(connection) as db:
        row = db.get(Cart, UUID(data["id"]))
        assert row.expires_at == deadline
        assert row.updated_at == updated


@pytest.mark.parametrize(
    "payload",
    [
        {"status": "EXPIRED"},
        {"expires_at": "2099-01-01"},
        {"id": str(uuid4())},
        {"price": "0.01"},
        [],
    ],
)
def test_rejects_client_fields(cart_api, payload):
    client, _ = cart_api
    response = client.post("/api/carts", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize(
    "cart_id,status,code",
    [(str(uuid4()), 404, "cart_not_found"), ("invalid-uuid", 422, "validation_error")],
)
def test_lookup_errors(cart_api, cart_id, status, code):
    client, _ = cart_api
    response = client.get(f"/api/carts/{cart_id}")
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert isinstance(response.json()["error"]["details"], list)


@pytest.mark.parametrize("offset,status", [(-1, 200), (0, 410), (1, 410)])
def test_expiration_boundary(cart_api, monkeypatch, offset, status):
    client, connection = cart_api
    data = client.post("/api/carts").json()
    deadline = utc(data["expires_at"])
    monkeypatch.setattr(
        service, "server_now", lambda: deadline + timedelta(microseconds=offset)
    )
    response = client.get(f"/api/carts/{data['id']}")
    assert response.status_code == status
    if status == 410:
        assert response.json()["error"] == dict(
            code="cart_expired",
            message="This cart has expired. Create a new cart.",
            details=[],
        )
        assert response.json()["cart_id"] == data["id"]
        assert response.json()["status"] == "EXPIRED"
        assert utc(response.json()["expires_at"]) == deadline
        assert client.get(f"/api/carts/{data['id']}").status_code == 410
    with Session(connection) as db:
        row = db.get(Cart, UUID(data["id"]))
        assert row.status == (
            CartStatus.EXPIRED if status == 410 else CartStatus.ACTIVE
        )
        assert utc(row.expires_at) == deadline


def test_stored_expired_cannot_revive(cart_api):
    client, connection = cart_api
    data = client.post("/api/carts").json()
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        db.get(Cart, UUID(data["id"])).status = CartStatus.EXPIRED
        db.commit()
    assert client.get(f"/api/carts/{data['id']}").status_code == 410


def test_menu_unchanged(cart_api, monkeypatch):
    client, connection = cart_api
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        order = (
            db.scalar(
                select(MenuCategory.display_order)
                .order_by(MenuCategory.display_order.desc())
                .limit(1)
            )
            or 0
        ) + 1
        db.add(MenuCategory(name="GEO28 fixture", display_order=order))
        db.commit()
    tables = [
        table
        for table in Base.metadata.sorted_tables
        if not table.name.startswith("cart")
    ]

    def snapshot():
        return {
            table.name: connection.execute(
                select(table).order_by(*table.primary_key.columns)
            ).all()
            for table in tables
        }

    before = snapshot()
    data = client.post("/api/carts").json()
    assert client.get(f"/api/carts/{data['id']}").status_code == 200
    monkeypatch.setattr(service, "server_now", lambda: utc(data["expires_at"]))
    assert client.get(f"/api/carts/{data['id']}").status_code == 410
    assert snapshot() == before


@pytest.mark.parametrize(
    "change",
    ["price", "option", "group", "bounds", "missing_price", "variant", "category"],
)
def test_persisted_items(cart_api, change):
    from decimal import Decimal

    from app.models import (
        CartItem,
        CartItemModifierOption,
        MenuItem,
        MenuItemVariant,
        ModifierGroup,
        ModifierOption,
        ModifierOptionPrice,
    )

    client, connection = cart_api
    data = client.post("/api/carts").json()
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        order = (
            db.scalar(
                select(MenuCategory.display_order)
                .order_by(MenuCategory.display_order.desc())
                .limit(1)
            )
            or 0
        ) + 1
        category = MenuCategory(name="GEO28 meal", display_order=order)
        item = MenuItem(name="Meal", category=category, display_order=1)
        variant = MenuItemVariant(
            name="Regular", menu_item=item, price=Decimal("10.00"), display_order=1
        )
        group = ModifierGroup(
            name="Extras",
            menu_item=item,
            min_selections=0,
            max_selections=2,
            display_order=1,
        )
        option = ModifierOption(name="Extra", modifier_group=group, display_order=1)
        price = ModifierOptionPrice(
            modifier_option=option,
            menu_item_variant=variant,
            price_adjustment=Decimal("2.50"),
        )
        line = CartItem(
            id=uuid4(), cart_id=UUID(data["id"]), menu_item_variant=variant, quantity=2
        )
        db.add_all(
            [price, CartItemModifierOption(cart_item=line, modifier_option=option)]
        )
        db.commit()
        response = client.get(f"/api/carts/{data['id']}")
        assert response.status_code == 200
        result = response.json()
        assert result["subtotal"] == "25.00"
        assert result["item_count"] == 2
        assert result["items"] == [
            {
                "id": str(line.id),
                "menu_item_id": item.id,
                "menu_item_name": "Meal",
                "menu_item_variant_id": variant.id,
                "menu_item_variant_name": "Regular",
                "quantity": 2,
                "special_instructions": None,
                "modifier_groups": [
                    {
                        "modifier_group_id": group.id,
                        "modifier_group_name": "Extras",
                        "options": [
                            {
                                "modifier_option_id": option.id,
                                "modifier_option_name": "Extra",
                                "price_adjustment": "2.50",
                            }
                        ],
                    }
                ],
                "unit_price": "12.50",
                "line_total": "25.00",
            }
        ]
        if change == "price":
            price.price_adjustment = Decimal("3.00")
        elif change == "option":
            option.is_available = False
        elif change == "group":
            group.is_active = False
        elif change == "bounds":
            group.min_selections = 2
        elif change == "missing_price":
            db.delete(price)
        elif change == "variant":
            variant.is_available = False
        else:
            category.is_active = False
        db.commit()
    response = client.get(f"/api/carts/{data['id']}")
    assert response.status_code == (200 if change == "price" else 409)
    assert utc(response.json()["expires_at"]) == utc(data["expires_at"])
    if change == "price":
        assert response.json()["subtotal"] == "26.00"
    else:
        assert response.json()["error"]["code"] == "cart_menu_conflict"
        assert (
            response.json()["error"]["details"][0]["cart_item_id"]
            == result["items"][0]["id"]
        )
