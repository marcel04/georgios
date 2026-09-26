from datetime import timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_cart_add import configured  # noqa: F401
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401
from test_cart_api import utc
from test_cart_quantity import populated  # noqa: F401

from app.models import Cart, CartItem, CartItemModifierOption, MenuItemVariant
from app.services import cart as service


def test_remove_and_empty_cart(populated, monkeypatch):  # noqa: F811
    client, connection, before, lid, ids = populated
    remaining_id = next(line["id"] for line in before["items"] if line["id"] != lid)
    patched = client.patch(
        f"/api/carts/{before['id']}/items/{remaining_id}", json={"quantity": 3}
    )
    assert patched.status_code == 200
    before = patched.json()
    now = utc(before["expires_at"]) - timedelta(minutes=5)
    monkeypatch.setattr(service, "server_now", lambda: now)
    url = f"/api/carts/{before['id']}"
    response = client.delete(f"{url}/items/{lid}")
    assert response.status_code == 200
    result = response.json()
    assert result["items"] == [line for line in before["items"] if line["id"] != lid]
    assert result["item_count"] == 3
    assert result["subtotal"] == "37.50"
    assert utc(result["expires_at"]) == now + timedelta(minutes=10)
    assert client.get(url).json() == result
    with Session(connection) as db:
        assert db.get(CartItem, UUID(lid)) is None
        assert (
            list(
                db.scalars(
                    select(CartItemModifierOption).where(
                        CartItemModifierOption.cart_item_id == UUID(lid)
                    )
                )
            )
            == []
        )
    repeated = client.delete(f"{url}/items/{lid}")
    assert repeated.status_code == 404
    assert repeated.json()["error"]["code"] == "cart_item_not_found"
    assert client.get(url).json() == result
    remaining = result["items"][0]["id"]
    response = client.delete(f"{url}/items/{remaining}")
    assert response.status_code == 200
    empty = response.json()
    assert empty == dict(
        id=before["id"],
        status="ACTIVE",
        expires_at=empty["expires_at"],
        item_count=0,
        subtotal="0.00",
        items=[],
    )
    assert client.get(url).json() == empty
    with Session(connection) as db:
        assert db.get(Cart, UUID(before["id"])) is not None
        assert db.get(CartItem, UUID(remaining)) is None
        assert (
            list(
                db.scalars(
                    select(CartItemModifierOption).where(
                        CartItemModifierOption.cart_item_id == UUID(remaining)
                    )
                )
            )
            == []
        )
    assert (
        client.post(
            f"{url}/items",
            json=dict(
                menu_item_variant_id=ids["variant"],
                quantity=1,
                modifier_groups=[
                    dict(modifier_group_id=g, option_ids=[o])
                    for g, o in zip(ids["groups"], ids["options"])
                ],
            ),
        ).status_code
        == 201
    )


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
def test_remove_errors(populated, monkeypatch, case, status, code):  # noqa: F811
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
    response = client.delete(f"/api/carts/{cid}/items/{lid}")
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    with Session(connection) as db:
        row = db.get(Cart, UUID(before["id"]))
        assert utc(row.expires_at) == utc(before["expires_at"])
        assert {str(line.id) for line in row.items} == {
            line["id"] for line in before["items"]
        }
        assert all(len(line.modifier_options) == 2 for line in row.items)


@pytest.mark.parametrize("other_stale", [False, True])
def test_stale_recovery_or_rollback(populated, other_stale):  # noqa: F811
    client, connection, before, lid, ids = populated
    url = f"/api/carts/{before['id']}"
    if not other_stale:
        other = next(line["id"] for line in before["items"] if line["id"] != lid)
        assert client.delete(f"{url}/items/{other}").status_code == 200
        before = client.get(url).json()
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        db.get(MenuItemVariant, ids["variant"]).is_available = False
        db.commit()
    response = client.delete(f"{url}/items/{lid}")
    assert response.status_code == (409 if other_stale else 200)
    with Session(connection) as db:
        row = db.get(Cart, UUID(before["id"]))
        if other_stale:
            assert response.json()["error"]["code"] == "cart_menu_conflict"
            assert utc(row.expires_at) == utc(before["expires_at"])
            assert len(row.items) == 2
            assert all(len(line.modifier_options) == 2 for line in row.items)
        else:
            assert response.json()["items"] == []
            assert response.json()["subtotal"] == "0.00"
            assert row.items == []
