"""GEO-32 supplements existing free/paid, stale-menu and mutation rollback tests."""

from copy import deepcopy
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from test_cart_add import configured  # noqa: F401
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401

from app.models import (
    Cart,
    CartItem,
    CartItemModifierOption,
    MenuItemVariant,
    ModifierOptionPrice,
)
from app.services import cart as service


@pytest.fixture
def priced(configured):  # noqa: F811
    client, connection, cart, body, ids = configured
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        db.get(MenuItemVariant, ids["variant"]).price = Decimal("0.10")
        for pid, value in zip(ids["prices"], ["0.20", "0.30"]):
            db.get(ModifierOptionPrice, pid).price_adjustment = Decimal(value)
        other = MenuItemVariant(
            menu_item_id=ids["item"],
            name="Other",
            display_order=2,
            price=Decimal("1.05"),
        )
        db.add(other)
        db.flush()
        for oid, value in zip(ids["options"], ["0.05", "0.15"]):
            db.add(
                ModifierOptionPrice(
                    modifier_option_id=oid,
                    menu_item_id=ids["item"],
                    menu_item_variant_id=other.id,
                    price_adjustment=Decimal(value),
                )
            )
        other_id = other.id
        db.commit()
    return client, connection, cart, body, ids, other_id


def test_exact_totals_across_all_endpoints(priced):
    client, connection, cart, body, ids, other_id = priced
    url = f"/api/carts/{cart['id']}"
    assert cart["subtotal"] == "0.00" and cart["item_count"] == 0
    body["quantity"] = 3
    first = client.post(f"{url}/items", json=body)
    assert first.status_code == 201
    first = first.json()
    lid = first["items"][0]["id"]
    assert first["items"][0]["unit_price"] == "0.60"
    assert first["items"][0]["line_total"] == "1.80"
    second_body = deepcopy(body)
    second_body.update(menu_item_variant_id=other_id, quantity=2)
    second = client.post(f"{url}/items", json=second_body).json()
    other_line = next(line for line in second["items"] if line["id"] != lid)
    assert other_line["unit_price"] == "1.25"
    assert other_line["line_total"] == "2.50"
    assert second["subtotal"] == "4.30" and second["item_count"] == 5
    third = client.post(f"{url}/items", json=body).json()
    assert third["subtotal"] == "6.10" and third["item_count"] == 8
    assert len({line["id"] for line in third["items"]}) == 3
    assert client.get(url).json() == third
    with Session(connection) as db:
        response = service.get_cart(db, UUID(cart["id"]))
        assert isinstance(response.subtotal, Decimal)
        assert response.subtotal == Decimal("6.10")
        assert all(
            isinstance(line.unit_price, Decimal)
            and isinstance(line.line_total, Decimal)
            for line in response.items
        )
    patched = client.patch(f"{url}/items/{lid}", json={"quantity": 4}).json()
    assert patched["subtotal"] == "6.70" and patched["item_count"] == 9
    removed = client.delete(f"{url}/items/{other_line['id']}").json()
    assert removed["subtotal"] == "4.20" and removed["item_count"] == 7
    for line in removed["items"]:
        final = client.delete(f"{url}/items/{line['id']}")
        assert final.status_code == 200
    assert final.json()["subtotal"] == "0.00"
    assert final.json()["item_count"] == 0


@pytest.mark.parametrize("change,expected", [("base", "2.13"), ("adjustment", "2.43")])
def test_repricing_preserves_persisted_intent(priced, change, expected):
    client, connection, cart, body, ids, other_id = priced
    url = f"/api/carts/{cart['id']}"
    body["quantity"] = 3
    before = client.post(f"{url}/items", json=body).json()
    cid = UUID(cart["id"])

    def snapshot():
        lines = select(CartItem.id).where(CartItem.cart_id == cid)
        return (
            connection.execute(select(Cart.__table__).where(Cart.id == cid)).all(),
            connection.execute(
                select(CartItem.__table__).where(CartItem.cart_id == cid)
            ).all(),
            connection.execute(
                select(CartItemModifierOption.__table__).where(
                    CartItemModifierOption.cart_item_id.in_(lines)
                )
            ).all(),
        )

    stored = snapshot()
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        if change == "base":
            db.get(MenuItemVariant, ids["variant"]).price = Decimal("0.21")
        else:
            db.get(ModifierOptionPrice, ids["prices"][0]).price_adjustment = Decimal(
                "0.41"
            )
        db.commit()
    result = client.get(url)
    assert result.status_code == 200
    result = result.json()
    assert result["subtotal"] == expected
    assert result["expires_at"] == before["expires_at"]
    assert result["items"][0]["id"] == before["items"][0]["id"]
    assert snapshot() == stored


@pytest.mark.parametrize("line_count", [1, 6])
def test_pricing_read_has_one_select(priced, line_count):
    client, connection, cart, body, ids, other_id = priced
    url = f"/api/carts/{cart['id']}"
    for _ in range(line_count):
        assert client.post(f"{url}/items", json=body).status_code == 201
    statements = []

    def track(conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            statements.append(statement)

    event.listen(connection, "before_cursor_execute", track)
    try:
        response = client.get(url)
    finally:
        event.remove(connection, "before_cursor_execute", track)
    assert response.status_code == 200
    assert response.json()["item_count"] == 2 * line_count
    assert len(statements) == 1


@pytest.mark.parametrize(
    "field",
    ["price", "base_price", "price_adjustment", "unit_price", "line_total", "subtotal"],
)
def test_client_prices_rejected(priced, field):
    client, connection, cart, body, ids, other_id = priced
    url = f"/api/carts/{cart['id']}"
    original = client.post(f"{url}/items", json=body).json()
    lid = original["items"][0]["id"]
    body[field] = "0.01"
    for response in [
        client.post(f"{url}/items", json=body),
        client.patch(f"{url}/items/{lid}", json={"quantity": 3, field: "0.01"}),
    ]:
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
    assert client.get(url).json() == original
