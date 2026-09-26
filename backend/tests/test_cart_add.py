from datetime import timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session
from test_cart_api import cart_api as cart_api_fixture  # noqa: F401
from test_cart_api import utc

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
from app.services import cart as service


@pytest.fixture
def configured(cart_api_fixture):  # noqa: F811
    client, connection = cart_api_fixture
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        order = (
            db.scalar(
                select(MenuCategory.display_order)
                .order_by(MenuCategory.display_order.desc())
                .limit(1)
            )
            or 0
        ) + 1
        category = MenuCategory(name="GEO29", display_order=order)
        item = MenuItem(name="Meal", category=category, display_order=1)
        variant = MenuItemVariant(
            name="Regular", menu_item=item, price=Decimal("10.00"), display_order=1
        )
        groups = [
            ModifierGroup(
                name=str(i),
                menu_item=item,
                min_selections=1,
                max_selections=1,
                display_order=i,
            )
            for i in [1, 2]
        ]
        options = [
            ModifierOption(name=str(i), modifier_group=g, display_order=1)
            for i, g in enumerate(groups)
        ]
        prices = [
            ModifierOptionPrice(
                modifier_option=o,
                menu_item_variant=variant,
                price_adjustment=Decimal(p),
            )
            for o, p in zip(options, ["0.00", "2.50"])
        ]
        db.add_all(prices)
        db.commit()
        ids = dict(
            variant=variant.id,
            item=item.id,
            category=category.id,
            groups=[g.id for g in groups],
            options=[o.id for o in options],
            prices=[p.id for p in prices],
        )
    cart = client.post("/api/carts").json()
    body = dict(
        menu_item_variant_id=ids["variant"],
        quantity=2,
        special_instructions="Well done",
        modifier_groups=[
            dict(modifier_group_id=g, option_ids=[o])
            for g, o in zip(ids["groups"], ids["options"])
        ],
    )
    return client, connection, cart, body, ids


def test_configured_add(configured, monkeypatch):
    client, connection, cart, body, ids = configured
    now = utc(cart["expires_at"]) - timedelta(minutes=5)
    monkeypatch.setattr(service, "server_now", lambda: now)
    url = f"/api/carts/{cart['id']}/items"
    first = client.post(url, json=body)
    assert first.status_code == 201
    result = first.json()
    assert result["subtotal"] == "25.00"
    assert result["item_count"] == 2
    assert utc(result["expires_at"]) == now + timedelta(minutes=10)
    line = result["items"][0]
    assert line["special_instructions"] == "Well done"
    assert [g["modifier_group_id"] for g in line["modifier_groups"]] == ids["groups"]
    assert [g["options"][0]["price_adjustment"] for g in line["modifier_groups"]] == [
        "0.00",
        "2.50",
    ]
    second = client.post(url, json=body).json()
    assert second["subtotal"] == "50.00" and second["item_count"] == 4
    assert len({line["id"] for line in second["items"]}) == 2
    with Session(connection) as db:
        assert set(
            db.scalars(
                select(CartItemModifierOption.modifier_option_id).where(
                    CartItemModifierOption.cart_item_id == UUID(line["id"])
                )
            )
        ) == set(ids["options"])


@pytest.mark.parametrize(
    "case",
    [
        "missing_variant",
        "variant",
        "item",
        "category",
        "wrong_group",
        "inactive_group",
        "wrong_option",
        "option",
        "omitted",
        "below",
        "above",
        "duplicate_group",
        "duplicate_option",
        "price",
        "q0",
        "qnegative",
        "q21",
        "qfraction",
        "qfloat",
        "qbool",
        "instructions",
        "client_price",
        "nested_price",
    ],
)
def test_rejected_add_atomic(configured, case):
    client, connection, cart, body, ids = configured
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        if case in ["variant", "item", "category", "inactive_group", "option"]:
            model, key, field = {
                "variant": (MenuItemVariant, "variant", "is_available"),
                "item": (MenuItem, "item", "is_available"),
                "category": (MenuCategory, "category", "is_active"),
                "inactive_group": (ModifierGroup, "groups", "is_active"),
                "option": (ModifierOption, "options", "is_available"),
            }[case]
            value = ids[key]
            value = value[0] if isinstance(value, list) else value
            setattr(db.get(model, value), field, False)
        elif case == "wrong_group":
            other = MenuItem(
                name="Other meal", category_id=ids["category"], display_order=2
            )
            group = ModifierGroup(
                name="Other group",
                menu_item=other,
                min_selections=0,
                max_selections=1,
                display_order=1,
            )
            db.add(group)
            db.flush()
            body["modifier_groups"][0]["modifier_group_id"] = group.id
        elif case == "price":
            db.delete(db.get(ModifierOptionPrice, ids["prices"][0]))
        db.commit()
    if case == "missing_variant":
        body["menu_item_variant_id"] = 2147483647
    if case == "wrong_option":
        body["modifier_groups"][0]["option_ids"] = [ids["options"][1]]
    if case == "omitted":
        body.pop("modifier_groups")
    if case == "below":
        body["modifier_groups"][0]["option_ids"] = []
    if case == "above":
        body["modifier_groups"][0]["option_ids"].append(ids["options"][1])
    if case == "duplicate_group":
        body["modifier_groups"].append(body["modifier_groups"][0])
    if case == "duplicate_option":
        body["modifier_groups"][0]["option_ids"] *= 2
    if case.startswith("q"):
        body["quantity"] = {
            "q0": 0,
            "qnegative": -1,
            "q21": 21,
            "qfraction": 1.5,
            "qfloat": 1.0,
            "qbool": True,
        }[case]
    if case == "instructions":
        body["special_instructions"] = "é" * 251
    if case == "client_price":
        body["unit_price"] = "0.01"
    if case == "nested_price":
        body["modifier_groups"][0]["price"] = "0.01"
    response = client.post(f"/api/carts/{cart['id']}/items", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
    assert response.json()["error"]["details"]
    with Session(connection) as db:
        assert utc(db.get(Cart, UUID(cart["id"])).expires_at) == utc(cart["expires_at"])
        assert (
            list(
                db.scalars(select(CartItem).where(CartItem.cart_id == UUID(cart["id"])))
            )
            == []
        )


def test_simple_and_stale(configured):
    client, connection, cart, body, ids = configured
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        for gid in ids["groups"]:
            db.get(ModifierGroup, gid).min_selections = 0
        db.commit()
    body.pop("modifier_groups")
    body.pop("special_instructions")
    url = f"/api/carts/{cart['id']}/items"
    response = client.post(url, json=body)
    assert response.status_code == 201
    first = response.json()
    assert first["subtotal"] == "20.00"
    with Session(connection, join_transaction_mode="create_savepoint") as db:
        db.get(ModifierGroup, ids["groups"][0]).min_selections = 1
        db.commit()
    body["modifier_groups"] = [
        dict(modifier_group_id=ids["groups"][0], option_ids=[ids["options"][0]])
    ]
    response = client.post(url, json=body)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "cart_menu_conflict"
    with Session(connection) as db:
        assert (
            len(
                list(
                    db.scalars(
                        select(CartItem).where(CartItem.cart_id == UUID(cart["id"]))
                    )
                )
            )
            == 1
        )
        assert utc(db.get(Cart, UUID(cart["id"])).expires_at) == utc(
            first["expires_at"]
        )


@pytest.mark.parametrize(
    "kind,status", [("missing", 404), ("malformed", 422), ("expired", 410)]
)
def test_cart_errors(configured, monkeypatch, kind, status):
    client, connection, cart, body, ids = configured
    cid = cart["id"]
    if kind == "missing":
        cid = str(uuid4())
    if kind == "malformed":
        cid = "bad"
    if kind == "expired":
        monkeypatch.setattr(service, "server_now", lambda: utc(cart["expires_at"]))
    response = client.post(f"/api/carts/{cid}/items", json=body)
    assert response.status_code == status
    assert (
        response.json()["error"]["code"]
        == {404: "cart_not_found", 422: "validation_error", 410: "cart_expired"}[status]
    )


def test_postgres_lock_checks_time_after_wait(monkeypatch):
    """A real blocked writer samples time only after acquiring the cart lock."""
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from sqlalchemy import delete, text

    from app.database import engine
    from app.schemas.cart import CartItemCreateRequest

    if os.environ.get("GEO27_DB_TESTS") != "1":
        pytest.skip("Requires PostgreSQL; SQLite cannot verify row locks")
    deadline = service.server_now() + timedelta(minutes=1)
    with Session(engine) as db:
        cart = Cart(expires_at=deadline)
        db.add(cart)
        db.commit()
        cid = cart.id
    started = Event()
    sampled = Event()
    pid = []

    def clock():
        sampled.set()
        return deadline

    monkeypatch.setattr(service, "server_now", clock)

    def writer():
        with Session(engine) as db:
            pid.append(db.scalar(text("select pg_backend_pid()")))
            started.set()
            try:
                service.add_item(
                    db,
                    cid,
                    CartItemCreateRequest(menu_item_variant_id=2147483647, quantity=1),
                )
            except service.CartError as exc:
                return exc.status_code

    try:
        with Session(engine) as locker, ThreadPoolExecutor(max_workers=1) as pool:
            locker.execute(select(Cart).where(Cart.id == cid).with_for_update())
            future = pool.submit(writer)
            try:
                assert started.wait(5)
                import time

                limit = time.monotonic() + 5
                blocked = False
                with engine.connect() as observer:
                    while time.monotonic() < limit:
                        blocked = observer.scalar(
                            text(
                                "select wait_event_type = 'Lock' from pg_stat_activity where pid=:pid"
                            ),
                            dict(pid=pid[0]),
                        )
                        if blocked:
                            break
                        time.sleep(0.01)
                assert blocked
                assert not sampled.is_set()
            finally:
                locker.rollback()
            assert future.result(timeout=5) == 410
            assert sampled.is_set()
        with Session(engine) as db:
            row = db.get(Cart, cid)
            assert row.status.value == "EXPIRED"
            assert row.expires_at == deadline
            assert row.items == []
    finally:
        with Session(engine) as db:
            db.execute(delete(Cart).where(Cart.id == cid))
            db.commit()


@pytest.mark.parametrize("operation", ["add", "quantity"])
def test_postgres_concurrent_mutations_preserve_both_lines(operation):
    import os
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    from sqlalchemy import delete

    from app.database import engine
    from app.schemas.cart import CartItemCreateRequest, CartItemQuantityRequest

    if os.environ.get("GEO27_DB_TESTS") != "1":
        pytest.skip("Requires PostgreSQL; SQLite cannot verify row locks")
    with Session(engine) as db:
        order = (
            db.scalar(
                select(MenuCategory.display_order)
                .order_by(MenuCategory.display_order.desc())
                .limit(1)
            )
            or 0
        ) + 1
        category = MenuCategory(
            name=f"GEO29 concurrency {uuid4()}", display_order=order
        )
        item = MenuItem(name="Meal", category=category, display_order=1)
        variant = MenuItemVariant(
            name="Regular", menu_item=item, price=Decimal("10.00"), display_order=1
        )
        cart = Cart(expires_at=service.server_now() + timedelta(minutes=5))
        db.add_all([variant, cart])
        if operation == "quantity":
            cart.items = [
                CartItem(menu_item_variant=variant, quantity=1) for _ in range(2)
            ]
        db.commit()
        line_ids = [line.id for line in cart.items]
        cid, category_id, variant_id = cart.id, category.id, variant.id
    barrier = Barrier(2)

    def writer(index):
        with Session(engine) as db:
            barrier.wait(timeout=5)
            if operation == "quantity":
                return service.update_quantity(
                    db,
                    cid,
                    line_ids[index],
                    CartItemQuantityRequest(quantity=index + 3),
                )
            return service.add_item(
                db,
                cid,
                CartItemCreateRequest(menu_item_variant_id=variant_id, quantity=1),
            )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(writer, index) for index in range(2)]
            results = [future.result(timeout=10) for future in futures]
        counts = sorted(result.item_count for result in results)
        assert counts == [1, 2] if operation == "add" else counts in ([4, 7], [5, 7])
        with Session(engine) as db:
            cart = db.get(Cart, cid)
            assert len(cart.items) == 2
            assert len({line.id for line in cart.items}) == 2
            assert service.get_cart(db, cid).subtotal == Decimal(
                "20.00" if operation == "add" else "70.00"
            )
            if operation == "quantity":
                assert sorted(line.quantity for line in cart.items) == [3, 4]
    finally:
        with Session(engine) as db:
            db.execute(delete(Cart).where(Cart.id == cid))
            db.execute(delete(MenuCategory).where(MenuCategory.id == category_id))
            db.commit()
