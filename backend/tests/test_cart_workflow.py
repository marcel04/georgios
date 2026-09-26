"""Complete configured workflows supplement focused contract/unit scenarios."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session
from test_cart_add import configured  # noqa: F401
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401

from app.models import (
    MenuItem,
    MenuItemVariant,
    ModifierGroup,
    ModifierOption,
    ModifierOptionPrice,
)


@pytest.fixture
def two_meals(configured):  # noqa: F811
    client, connection, cart, body, ids = configured
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        item = MenuItem(name="Dinner", category_id=ids["category"], display_order=2)
        variant = MenuItemVariant(
            name="Regular", menu_item=item, price=Decimal("18.95"), display_order=1
        )
        group = ModifierGroup(
            name="Side",
            menu_item=item,
            min_selections=1,
            max_selections=1,
            display_order=1,
        )
        option = ModifierOption(name="Rice", modifier_group=group, display_order=1)
        db.add(
            ModifierOptionPrice(
                modifier_option=option,
                menu_item_variant=variant,
                price_adjustment=Decimal("0.00"),
            )
        )
        db.commit()
        dinner = dict(
            menu_item_variant_id=variant.id,
            quantity=1,
            modifier_groups=[dict(modifier_group_id=group.id, option_ids=[option.id])],
        )
        option_id = option.id
    return client, connection, cart, body, dinner, option_id


@pytest.mark.parametrize("stale_recovery", [False, True])
def test_complete_guest_workflow(two_meals, stale_recovery):
    client, connection, cart, meal, dinner, option_id = two_meals
    url = f"/api/carts/{cart['id']}"
    first = client.post(f"{url}/items", json=meal)
    assert first.status_code == 201
    meal_id = first.json()["items"][0]["id"]
    second = client.post(f"{url}/items", json=dinner)
    assert second.status_code == 201
    result = second.json()
    dinner_id = next(line["id"] for line in result["items"] if line["id"] != meal_id)
    assert result["subtotal"] == "43.95" and result["item_count"] == 3
    assert client.get(url).json() == result
    patched = client.patch(f"{url}/items/{meal_id}", json={"quantity": 3})
    assert patched.status_code == 200
    result = patched.json()
    assert result["subtotal"] == "56.45" and result["item_count"] == 4
    meal_line = next(line for line in result["items"] if line["id"] == meal_id)
    assert meal_line["line_total"] == "37.50"
    if stale_recovery:
        with Session(connection, join_transaction_mode="create_savepoint") as db:
            db.get(ModifierOption, option_id).is_available = False
            db.commit()
        conflict = client.get(url)
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "cart_menu_conflict"
        assert {d["cart_item_id"] for d in conflict.json()["error"]["details"]} == {
            dinner_id
        }
    removed = client.delete(f"{url}/items/{dinner_id}")
    assert removed.status_code == 200
    result = removed.json()
    assert result["items"] == [meal_line]
    assert result["subtotal"] == "37.50" and result["item_count"] == 3
    assert client.get(url).json() == result
    empty = client.delete(f"{url}/items/{meal_id}")
    assert empty.status_code == 200
    assert empty.json() == dict(
        id=cart["id"],
        status="ACTIVE",
        expires_at=empty.json()["expires_at"],
        subtotal="0.00",
        item_count=0,
        items=[],
    )
    assert client.get(url).json() == empty.json()
