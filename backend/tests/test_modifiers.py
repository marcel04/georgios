"""Opt-in PostgreSQL checks: GEO20_DB_TESTS=1 uv run pytest tests/test_modifiers.py.

Uses the configured development database at migration head; test rows roll back.
"""

import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, configure_mappers

from app.models import (
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    ModifierGroup,
    ModifierOption,
    ModifierOptionPrice,
)


def test_modifier_mappers_configure_without_warnings():
    configure_mappers()


@pytest.mark.skipif(
    os.environ.get("GEO20_DB_TESTS") != "1",
    reason="Requires local PostgreSQL at migration head",
)
def test_modifier_database_invariants():
    from app.database import engine

    with engine.connect() as connection:
        transaction = connection.begin()
        try:
            session = Session(bind=connection, join_transaction_mode="create_savepoint")
            suffix = uuid4().hex
            order = (
                connection.scalar(
                    select(MenuCategory.display_order)
                    .order_by(MenuCategory.display_order.desc())
                    .limit(1)
                )
                or 0
            )
            category = MenuCategory(name=f"geo20-{suffix}", display_order=order + 1)
            pizza = MenuItem(name="Pizza", category=category, display_order=1)
            sub = MenuItem(name="Sub", category=category, display_order=2)
            small = MenuItemVariant(
                name="Small", price=Decimal("10.00"), display_order=1, menu_item=pizza
            )
            large = MenuItemVariant(
                name="Large", price=Decimal("15.00"), display_order=2, menu_item=pizza
            )
            other = MenuItemVariant(
                name="Regular", price=Decimal("8.00"), display_order=1, menu_item=sub
            )
            group = ModifierGroup(
                name="Toppings",
                min_selections=0,
                max_selections=3,
                display_order=1,
                menu_item=pizza,
            )
            option = ModifierOption(
                name="Pepperoni", display_order=1, modifier_group=group
            )
            free = ModifierOptionPrice(
                modifier_option=option,
                menu_item_variant=small,
                price_adjustment=Decimal("0.00"),
            )
            session.add_all([category, small, large, other, group, option, free])
            session.flush()
            assert option.menu_item_id == pizza.id == free.menu_item_id
            assert free.price_adjustment == Decimal("0.00")
            assert group.is_active and option.is_available
            assert group.created_at.tzinfo is not None
            session.expire_all()
            assert free.menu_item_variant == small
            assert free in small.modifier_option_prices
            assert option in group.options

            def rejected(statement):
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(statement)

            prices = ModifierOptionPrice.__table__
            options = ModifierOption.__table__
            groups = ModifierGroup.__table__
            # Direct SQL bypasses ORM validation: every ownership edge is enforced.
            rejected(
                insert(options).values(
                    modifier_group_id=group.id,
                    menu_item_id=sub.id,
                    name="Wrong",
                    display_order=2,
                )
            )
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=pizza.id,
                    menu_item_variant_id=other.id,
                    price_adjustment=1,
                )
            )
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=sub.id,
                    menu_item_variant_id=other.id,
                    price_adjustment=1,
                )
            )
            rejected(
                update(groups)
                .where(groups.c.id == group.id)
                .values(menu_item_id=sub.id)
            )
            rejected(
                update(MenuItemVariant)
                .where(MenuItemVariant.id == small.id)
                .values(menu_item_id=sub.id, display_order=3)
            )
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=pizza.id,
                    menu_item_variant_id=large.id,
                    price_adjustment=-1,
                )
            )
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=pizza.id,
                    menu_item_variant_id=small.id,
                    price_adjustment=0,
                )
            )
            for minimum, maximum in [(-1, 2), (0, -1), (3, 2)]:
                rejected(
                    insert(groups).values(
                        menu_item_id=pizza.id,
                        name="Invalid",
                        display_order=2,
                        min_selections=minimum,
                        max_selections=maximum,
                    )
                )
            for name, position in [("Toppings", 2), ("Other", 1)]:
                rejected(
                    insert(groups).values(
                        menu_item_id=pizza.id,
                        name=name,
                        display_order=position,
                        min_selections=0,
                        max_selections=1,
                    )
                )
            for name, position in [("Pepperoni", 2), ("Other", 1)]:
                rejected(
                    insert(options).values(
                        modifier_group_id=group.id,
                        menu_item_id=pizza.id,
                        name=name,
                        display_order=position,
                    )
                )
            # Force an old timestamp in the inserted row to test UPDATE triggers.
            for table, values in [
                (
                    groups,
                    dict(
                        menu_item_id=pizza.id,
                        name="Clock",
                        display_order=3,
                        min_selections=0,
                        max_selections=0,
                    ),
                ),
                (
                    options,
                    dict(
                        modifier_group_id=group.id,
                        menu_item_id=pizza.id,
                        name="Clock",
                        display_order=3,
                    ),
                ),
            ]:
                row_id = connection.scalar(
                    insert(table)
                    .values(**values, updated_at=text("'2000-01-01'::timestamptz"))
                    .returning(table.c.id)
                )
                result = connection.execute(
                    update(table)
                    .where(table.c.id == row_id)
                    .values(name="Clock updated")
                    .returning(table.c.updated_at)
                ).scalar_one()
                assert result.year > 2000
            connection.execute(
                delete(MenuItemVariant).where(MenuItemVariant.id == small.id)
            )
            assert (
                connection.scalar(select(prices.c.id).where(prices.c.id == free.id))
                is None
            )
            connection.execute(delete(MenuItem).where(MenuItem.id == pizza.id))
            assert (
                connection.scalar(
                    select(groups.c.id).where(groups.c.menu_item_id == pizza.id)
                )
                is None
            )
            assert (
                connection.scalar(
                    select(options.c.id).where(options.c.menu_item_id == pizza.id)
                )
                is None
            )
            session.close()
        finally:
            transaction.rollback()
