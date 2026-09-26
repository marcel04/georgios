"""GEO-33: current rules, conflict details, and atomic stale-cart recovery.

Existing pricing/add/removal suites cover price changes, tampering and row locks.
"""

from uuid import UUID

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_cart_add import configured  # noqa: F401
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401

from app.models import (
    Cart,
    CartItem,
    CartItemModifierOption,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    ModifierGroup,
    ModifierOption,
    ModifierOptionPrice,
)


@pytest.fixture
def stored(configured):  # noqa: F811
    client, connection, cart, body, ids = configured
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        omitted = ModifierGroup(
            menu_item_id=ids["item"],
            name="Optional",
            min_selections=0,
            max_selections=2,
            display_order=3,
        )
        db.add(omitted)
        db.commit()
        ids["omitted"] = omitted.id
    for _ in range(2):
        response = client.post(f"/api/carts/{cart['id']}/items", json=body)
        assert response.status_code == 201
    return client, connection, response.json(), body, ids


def snapshot(connection, cid):
    cid = UUID(cid)
    line_ids = select(CartItem.id).where(CartItem.cart_id == cid)
    return [
        connection.execute(statement).all()
        for statement in [
            select(Cart.__table__).where(Cart.id == cid),
            select(CartItem.__table__)
            .where(CartItem.cart_id == cid)
            .order_by(CartItem.id),
            select(CartItemModifierOption.__table__)
            .where(CartItemModifierOption.cart_item_id.in_(line_ids))
            .order_by(
                CartItemModifierOption.cart_item_id,
                CartItemModifierOption.modifier_option_id,
            ),
        ]
    ]


@pytest.mark.parametrize(
    "change",
    [
        "category",
        "item",
        "variant",
        "group",
        "option",
        "new_required",
        "min",
        "max",
        "price",
    ],
)
def test_all_stale_lines_reported_without_writes(stored, change):
    client, connection, cart, body, ids = stored
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        if change == "category":
            db.get(MenuCategory, ids["category"]).is_active = False
        elif change == "item":
            db.get(MenuItem, ids["item"]).is_available = False
        elif change == "variant":
            db.get(MenuItemVariant, ids["variant"]).is_available = False
        elif change == "group":
            db.get(ModifierGroup, ids["groups"][0]).is_active = False
        elif change == "option":
            db.get(ModifierOption, ids["options"][0]).is_available = False
        elif change == "new_required":
            db.get(ModifierGroup, ids["omitted"]).min_selections = 1
        elif change == "min":
            group = db.get(ModifierGroup, ids["groups"][0])
            group.min_selections = 2
            group.max_selections = 2
        elif change == "max":
            group = db.get(ModifierGroup, ids["groups"][0])
            group.min_selections = 0
            group.max_selections = 0
        else:
            db.delete(db.get(ModifierOptionPrice, ids["prices"][0]))
        db.commit()
    before = snapshot(connection, cart["id"])
    response = client.get(f"/api/carts/{cart['id']}")
    assert response.status_code == 409
    result = response.json()
    assert result["error"]["code"] == "cart_menu_conflict"
    assert "subtotal" not in result and "items" not in result
    details = result["error"]["details"]
    assert {d["cart_item_id"] for d in details} == {
        line["id"] for line in cart["items"]
    }
    assert all(d["field"] and d["reason"] for d in details)
    if change in ["new_required", "min", "max"]:
        expected_gid = ids["omitted"] if change == "new_required" else ids["groups"][0]
        assert all(
            d["modifier_group_id"] == expected_gid and d["reason"] == "selection_bounds"
            for d in details
        )
        assert all(
            d["selection_count"] == (0 if change == "new_required" else 1)
            for d in details
        )
    if change in ["option", "price"]:
        assert all(
            d["modifier_group_id"] == ids["groups"][0]
            and d["modifier_option_id"] == ids["options"][0]
            for d in details
        )
    assert snapshot(connection, cart["id"]) == before


@pytest.mark.parametrize("operation", ["add", "patch", "delete"])
def test_missing_price_rollback_and_new_request_distinction(stored, operation):
    client, connection, cart, body, ids = stored
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        db.delete(db.get(ModifierOptionPrice, ids["prices"][0]))
        # Permit a valid new unconfigured line while old selections remain stale.
        for gid in ids["groups"]:
            db.get(ModifierGroup, gid).min_selections = 0
        db.commit()
    url = f"/api/carts/{cart['id']}"
    before = snapshot(connection, cart["id"])
    invalid = client.post(f"{url}/items", json=body)
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "validation_error"
    lid = cart["items"][0]["id"]
    if operation == "add":
        response = client.post(
            f"{url}/items", json=dict(menu_item_variant_id=ids["variant"], quantity=1)
        )
    elif operation == "patch":
        response = client.patch(f"{url}/items/{lid}", json={"quantity": 3})
    else:
        response = client.delete(f"{url}/items/{lid}")
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cart_menu_conflict"
    assert snapshot(connection, cart["id"]) == before


def test_option_regrouping_revalidates_current_bounds(stored):
    client, connection, cart, body, ids = stored
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        option = db.get(ModifierOption, ids["options"][0])
        option.modifier_group_id = ids["groups"][1]
        option.display_order = 2
        db.commit()
    before = snapshot(connection, cart["id"])
    response = client.get(f"/api/carts/{cart['id']}")
    assert response.status_code == 409
    details = response.json()["error"]["details"]
    assert {detail["modifier_group_id"] for detail in details} == set(ids["groups"])
    assert {detail["selection_count"] for detail in details} == {0, 2}
    assert snapshot(connection, cart["id"]) == before


def test_persisted_foreign_item_options_conflict(stored):
    client, connection, cart, body, ids = stored
    # Independent cart FKs ensure existence, not option/variant item ownership.
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        item = MenuItem(name="Other", category_id=ids["category"], display_order=2)
        variant = MenuItemVariant(
            name="Other",
            menu_item=item,
            price=db.get(MenuItemVariant, ids["variant"]).price,
            display_order=1,
        )
        db.add(variant)
        db.flush()
        db.get(CartItem, UUID(cart["items"][0]["id"])).menu_item_variant_id = variant.id
        db.commit()
    before = snapshot(connection, cart["id"])
    response = client.get(f"/api/carts/{cart['id']}")
    assert response.status_code == 409
    details = response.json()["error"]["details"]
    assert any(detail["reason"] == "group_unavailable" for detail in details)
    assert {detail["cart_item_id"] for detail in details} == {cart["items"][0]["id"]}
    assert snapshot(connection, cart["id"]) == before
