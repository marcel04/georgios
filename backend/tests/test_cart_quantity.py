from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy.orm import Session
from test_cart_add import configured  # noqa: F401
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401
from test_cart_api import utc

from app.models import Cart, CartItem, MenuItemVariant
from app.services import cart as service


@pytest.fixture
def populated(configured):  # noqa: F811
    client, connection, cart, body, ids = configured
    body["quantity"] = 1
    first = client.post(f"/api/carts/{cart['id']}/items", json=body).json()
    first_id = first["items"][0]["id"]
    second = client.post(f"/api/carts/{cart['id']}/items", json=body).json()
    return client, connection, second, first_id, ids


@pytest.mark.parametrize("quantity", [1, 3, 20])
def test_quantity_success(populated, monkeypatch, quantity):
    client, connection, before, lid, ids = populated
    now = utc(before["expires_at"]) - timedelta(minutes=5)
    monkeypatch.setattr(service, "server_now", lambda: now)
    response = client.patch(
        f"/api/carts/{before['id']}/items/{lid}", json={"quantity": quantity}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["item_count"] == quantity + 1
    assert result["subtotal"] == format(Decimal("12.50") * (quantity + 1), ".2f")
    assert utc(result["expires_at"]) == now + timedelta(minutes=10)
    original = {line["id"]: line for line in before["items"]}
    for line in result["items"]:
        expected = dict(original[line["id"]])
        if line["id"] == lid:
            expected.update(
                quantity=quantity, line_total=format(Decimal("12.50") * quantity, ".2f")
            )
        assert line == expected
    assert client.get(f"/api/carts/{before['id']}").json() == result
    with Session(connection) as db:
        assert db.get(CartItem, UUID(lid)).quantity == quantity


@pytest.mark.parametrize(
    "payload",
    [
        {"quantity": 0},
        {"quantity": -1},
        {"quantity": 21},
        {"quantity": 1.5},
        {"quantity": True},
        {"quantity": 1.0},
        {},
        {"quantity": 2, "special_instructions": "edit"},
        {"quantity": 2, "price": "0.01"},
        None,
    ],
)
def test_invalid_quantity_atomic(populated, payload):
    client, connection, before, lid, ids = populated
    response = client.patch(
        f"/api/carts/{before['id']}/items/{lid}",
        **({"json": payload} if payload is not None else {}),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert client.get(f"/api/carts/{before['id']}").json() == before


@pytest.mark.parametrize(
    "case,status,code",
    [
        ("bad_cart", 422, "validation_error"),
        ("bad_item", 422, "validation_error"),
        ("missing_cart", 404, "cart_not_found"),
        ("expired", 410, "cart_expired"),
        ("missing_item", 404, "cart_item_not_found"),
        ("other_cart", 404, "cart_item_not_found"),
    ],
)
def test_lookup_precedence(populated, monkeypatch, case, status, code):
    client, connection, before, lid, ids = populated
    cid = before["id"]
    if case == "bad_cart":
        cid = "bad"
    if case == "bad_item":
        lid = "bad"
    if case == "missing_cart":
        cid = str(uuid4())
    if case == "missing_item":
        lid = str(uuid4())
    if case == "other_cart":
        cid = client.post("/api/carts").json()["id"]
    if case == "expired":
        monkeypatch.setattr(service, "server_now", lambda: utc(before["expires_at"]))
        lid = str(uuid4())
    response = client.patch(f"/api/carts/{cid}/items/{lid}", json={"quantity": 3})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    with Session(connection) as db:
        assert utc(db.get(Cart, UUID(before["id"])).expires_at) == utc(
            before["expires_at"]
        )
        assert all(
            line.quantity == 1 for line in db.get(Cart, UUID(before["id"])).items
        )


@pytest.mark.parametrize("stale", [False, True])
def test_current_menu(populated, stale):
    client, connection, before, lid, ids = populated
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        variant = db.get(MenuItemVariant, ids["variant"])
        variant.price = Decimal("20.00")
        variant.is_available = not stale
        db.commit()
    response = client.patch(
        f"/api/carts/{before['id']}/items/{lid}", json={"quantity": 3}
    )
    assert response.status_code == (409 if stale else 200)
    with Session(connection) as db:
        if stale:
            assert response.json()["error"]["code"] == "cart_menu_conflict"
            assert db.get(CartItem, UUID(lid)).quantity == 1
            assert utc(db.get(Cart, UUID(before["id"])).expires_at) == utc(
                before["expires_at"]
            )
        else:
            assert response.json()["subtotal"] == "90.00"
            assert all(
                line["unit_price"] == "22.50" for line in response.json()["items"]
            )
