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
    # Resolve relationship joins without opening a database connection.
    # Run pytest with -W error to make mapper warnings fail the test.
    configure_mappers()


# Ordinary CI runs skip this test because it requires migrated PostgreSQL.
@pytest.mark.skipif(
    os.environ.get("GEO20_DB_TESTS") != "1",
    reason="Requires local PostgreSQL at migration head",
)
def test_modifier_database_invariants():
    from app.database import engine

    with engine.connect() as connection:
        # All ORM and direct SQL operations share this rollback boundary.
        transaction = connection.begin()
        try:
            # Give the session a savepoint inside the outer transaction, so
            # session cleanup cannot commit the test data permanently.
            session = Session(bind=connection, join_transaction_mode="create_savepoint")
            # Avoid collisions with existing category names and display positions.
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
            # This second item supplies a deliberately incompatible variant.
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
            # Zero is valid for a free choice; Decimal avoids float imprecision.
            free = ModifierOptionPrice(
                modifier_option=option,
                menu_item_variant=small,
                price_adjustment=Decimal("0.00"),
            )
            session.add_all([category, small, large, other, group, option, free])
            # INSERT the object graph and obtain IDs/defaults without committing.
            session.flush()
            # Relationship assignment should propagate the item ownership key.
            assert option.menu_item_id == pizza.id == free.menu_item_id
            assert free.price_adjustment == Decimal("0.00")
            assert group.is_active and option.is_available
            assert group.created_at.tzinfo is not None
            # Reload relationships from SQL instead of trusting in-memory links.
            session.expire_all()
            assert free.menu_item_variant == small
            assert free in small.modifier_option_prices
            assert option in group.options

            # Each invalid write gets its own savepoint: PostgreSQL rejects it,
            # then rollback restores a usable transaction for the next check.
            def rejected(statement):
                with pytest.raises(IntegrityError):
                    with connection.begin_nested():
                        connection.execute(statement)

            prices = ModifierOptionPrice.__table__
            options = ModifierOption.__table__
            groups = ModifierGroup.__table__
            # Direct SQL bypasses ORM validation: every ownership edge is enforced.
            # An option cannot claim a different item from its owning group.
            rejected(
                insert(options).values(
                    modifier_group_id=group.id,
                    menu_item_id=sub.id,
                    name="Wrong",
                    display_order=2,
                )
            )
            # Correct option ownership, but the variant belongs to the sub.
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=pizza.id,
                    menu_item_variant_id=other.id,
                    price_adjustment=1,
                )
            )
            # Changing the shared owner to match the variant must also fail:
            # it no longer matches the option. Both foreign keys are necessary.
            rejected(
                insert(prices).values(
                    modifier_option_id=option.id,
                    menu_item_id=sub.id,
                    menu_item_variant_id=other.id,
                    price_adjustment=1,
                )
            )
            # Existing children also prevent moving their parents to another item.
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
            # Reject negative bounds and a maximum smaller than the minimum.
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
            # Test duplicate names and positions separately within one item.
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
            # Apply the same uniqueness checks within one modifier group.
            for name, position in [("Pepperoni", 2), ("Other", 1)]:
                rejected(
                    insert(options).values(
                        modifier_group_id=group.id,
                        menu_item_id=pizza.id,
                        name=name,
                        display_order=position,
                    )
                )
            # CURRENT_TIMESTAMP is stable within a PostgreSQL transaction;
            # an old value proves the trigger fired without adding sleeps.
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
            # Direct SQL deletion verifies database cascades, not ORM cascades.
            # Deleting the variant must remove its modifier price.
            connection.execute(
                delete(MenuItemVariant).where(MenuItemVariant.id == small.id)
            )
            assert (
                connection.scalar(select(prices.c.id).where(prices.c.id == free.id))
                is None
            )
            # Deleting the pizza must remove its modifier groups and options.
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
            # Remove test rows even if an assertion fails. PostgreSQL sequences
            # may still advance; rolling back does not reset generated IDs.
            transaction.rollback()
