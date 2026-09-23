"""PostgreSQL persistence: GEO27_DB_TESTS=1 uv run pytest tests/test_carts.py.

Run migrations first. All test writes roll back; existing menu data is not reseeded.
"""

import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, insert, inspect, select, text, update
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.models import (
    Cart,
    CartItem,
    CartItemModifierOption,
    CartStatus,
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    ModifierGroup,
    ModifierOption,
)


def test_cart_mappers_configure():
    configure_mappers()
    assert set(CartItemModifierOption.__table__.columns.keys()) == {
        "cart_item_id",
        "modifier_option_id",
    }


@pytest.fixture
def cart_db():
    if os.environ.get("GEO27_DB_TESTS") != "1":
        pytest.skip("Requires local PostgreSQL at migration head; GEO27_DB_TESTS=1")
    from app.database import engine

    assert engine.dialect.name == "postgresql"
    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            with Session(
                bind=connection, join_transaction_mode="create_savepoint"
            ) as db:
                yield db
        finally:
            transaction.rollback()


@pytest.fixture
def cart_graph(cart_db):
    db = cart_db
    order = (
        db.scalar(
            select(MenuCategory.display_order)
            .order_by(MenuCategory.display_order.desc())
            .limit(1)
        )
        or 0
    )
    category = MenuCategory(name=f"geo27-{uuid4().hex}", display_order=order + 1)
    item = MenuItem(name="Test meal", category=category, display_order=1)
    variant = MenuItemVariant(
        name="Regular", price=Decimal("10.00"), display_order=1, menu_item=item
    )
    group = ModifierGroup(
        name="Choices",
        min_selections=0,
        max_selections=1,
        display_order=1,
        menu_item=item,
    )
    option = ModifierOption(name="Choice", display_order=1, modifier_group=group)
    cart = Cart(expires_at=datetime.now(timezone.utc) + timedelta(minutes=10))
    line = CartItem(cart=cart, menu_item_variant=variant, quantity=1)
    selection = CartItemModifierOption(cart_item=line, modifier_option=option)
    db.add(selection)
    db.flush()
    return cart, line, selection


def test_tables_and_relationships(cart_db, cart_graph):
    cart, line, selection = cart_graph
    inspector = inspect(cart_db.connection())
    assert {"carts", "cart_items", "cart_item_modifier_options"} <= set(
        inspector.get_table_names()
    )
    assert inspector.get_pk_constraint("cart_item_modifier_options")[
        "constrained_columns"
    ] == ["cart_item_id", "modifier_option_id"]
    cart_db.expire_all()
    assert cart.items == [line]
    assert line.cart is cart
    assert line.modifier_options == [selection]
    assert selection.cart_item is line
    assert line.menu_item_variant.name == "Regular"
    assert selection.modifier_option.name == "Choice"
    assert isinstance(cart.id, UUID) and cart.id.version == 4
    assert isinstance(line.id, UUID) and line.id.version == 4
    assert cart.id != line.id
    assert cart.status is CartStatus.ACTIVE
    assert line.special_instructions is None


@pytest.mark.parametrize("status", list(CartStatus))
def test_valid_statuses(cart_db, status):
    cart = Cart(status=status, expires_at=datetime.now(timezone.utc))
    cart_db.add(cart)
    cart_db.flush()
    cart_db.refresh(cart)
    assert cart.status is status


def test_database_rejects_invalid_status(cart_db):
    with pytest.raises(DataError):
        with cart_db.begin_nested():
            cart_db.execute(
                text("INSERT INTO carts (status, expires_at) VALUES ('INVALID', now())")
            )


@pytest.mark.parametrize("quantity", [1, 20, 0, 21])
def test_quantity_boundaries(cart_db, cart_graph, quantity):
    _, line, _ = cart_graph
    statement = update(CartItem).where(CartItem.id == line.id).values(quantity=quantity)
    if quantity in (0, 21):
        with pytest.raises(IntegrityError, match="ck_cart_items_quantity_range"):
            with cart_db.begin_nested():
                cart_db.execute(statement)
    else:
        cart_db.execute(statement)
        cart_db.refresh(line)
        assert line.quantity == quantity


@pytest.mark.parametrize("instructions", [None, "", "é" * 250, "é" * 251])
def test_instruction_length(cart_db, cart_graph, instructions):
    _, line, _ = cart_graph
    statement = (
        update(CartItem)
        .where(CartItem.id == line.id)
        .values(special_instructions=instructions)
    )
    if instructions is not None and len(instructions) > 250:
        with pytest.raises(DataError):
            with cart_db.begin_nested():
                cart_db.execute(statement)
    else:
        cart_db.execute(statement)
        cart_db.refresh(line)
        assert line.special_instructions == instructions


def test_duplicate_selection_rejected_but_identical_lines_allowed(cart_db, cart_graph):
    cart, line, selection = cart_graph
    with pytest.raises(IntegrityError):
        with cart_db.begin_nested():
            cart_db.execute(
                insert(CartItemModifierOption).values(
                    cart_item_id=line.id,
                    modifier_option_id=selection.modifier_option_id,
                )
            )
    other = CartItem(cart=cart, menu_item_variant=line.menu_item_variant, quantity=1)
    cart_db.add(
        CartItemModifierOption(
            cart_item=other, modifier_option=selection.modifier_option
        )
    )
    cart_db.flush()
    cart_db.expire_all()
    assert len(cart.items) == 2
    assert line.id != other.id
    assert other.modifier_options[0].modifier_option_id == selection.modifier_option_id


@pytest.mark.parametrize("owner", [Cart, CartItem])
@pytest.mark.parametrize("orm", [False, True])
def test_owned_records_cascade(cart_db, cart_graph, owner, orm):
    cart, line, _ = cart_graph
    cart_id, line_id = cart.id, line.id
    target = cart if owner is Cart else line
    if orm:
        # Loaded collections exercise SQLAlchemy's ownership cascade too.
        assert cart.items and line.modifier_options
        cart_db.delete(target)
        cart_db.flush()
    else:
        cart_db.execute(delete(owner).where(owner.id == target.id))
    assert cart_db.scalar(select(CartItem.id).where(CartItem.id == line_id)) is None
    assert (
        cart_db.scalar(
            select(CartItemModifierOption.cart_item_id).where(
                CartItemModifierOption.cart_item_id == line_id
            )
        )
        is None
    )
    assert (cart_db.scalar(select(Cart.id).where(Cart.id == cart_id)) is None) == (
        owner is Cart
    )


@pytest.mark.parametrize("target", ["variant", "option", "item", "category", "group"])
def test_menu_references_block_deletion(cart_db, cart_graph, target):
    _, line, selection = cart_graph
    variant = line.menu_item_variant
    option = selection.modifier_option
    record = {
        "variant": variant,
        "option": option,
        "item": variant.menu_item,
        "category": variant.menu_item.category,
        "group": option.modifier_group,
    }[target]
    with pytest.raises(IntegrityError):
        with cart_db.begin_nested():
            cart_db.execute(delete(type(record)).where(type(record).id == record.id))


def test_timestamps_and_expiration_are_row_local(cart_db, cart_graph):
    cart, line, _ = cart_graph
    for record in (cart, line):
        assert record.created_at.tzinfo is not None
        assert record.updated_at == record.created_at
    assert cart.expires_at.tzinfo is not None
    old = datetime(2000, 1, 1, tzinfo=timezone.utc)
    # CURRENT_TIMESTAMP is transaction-stable; insert old values to prove triggers
    # replace even explicitly supplied updated_at without sleep or committed data.
    clock_cart = Cart(expires_at=old, created_at=old, updated_at=old)
    clock_line = CartItem(
        cart=clock_cart,
        menu_item_variant=line.menu_item_variant,
        quantity=1,
        created_at=old,
        updated_at=old,
    )
    cart_db.add(clock_line)
    cart_db.flush()
    cart_db.execute(
        update(CartItem)
        .where(CartItem.id == clock_line.id)
        .values(quantity=2, updated_at=old)
    )
    cart_db.refresh(clock_line)
    cart_db.refresh(clock_cart)
    assert clock_line.updated_at > old
    assert clock_line.created_at == old
    assert clock_cart.updated_at == old  # Child writes do not touch parents.
    cart_db.execute(
        update(Cart)
        .where(Cart.id == clock_cart.id)
        .values(status=CartStatus.EXPIRED, updated_at=old)
    )
    cart_db.refresh(clock_cart)
    assert clock_cart.updated_at > old
    assert clock_cart.created_at == old
    assert clock_cart.expires_at == old
    assert clock_cart.updated_at == cart_db.scalar(select(text("CURRENT_TIMESTAMP")))
