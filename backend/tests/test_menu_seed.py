"""Verify the canonical seed against an isolated database, never development data."""

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import MenuCategory, MenuItem, MenuItemVariant
from app.seeds.menu import seed_menu


def menu_counts(db) -> tuple[int, int, int]:
    return tuple(
        db.scalar(select(func.count()).select_from(model))
        for model in (MenuCategory, MenuItem, MenuItemVariant)
    )


def test_seed_creates_expected_totals(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)

    # A new session verifies that seed_menu persisted its work.
    with Session(menu_engine) as db:
        assert menu_counts(db) == (21, 292, 515)


def test_seed_creates_cheese_pizza_with_ordered_exact_prices(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)
        category = db.scalars(
            select(MenuCategory).where(MenuCategory.name == "Pizzas")
        ).one()
        cheese = db.scalars(
            select(MenuItem).where(
                MenuItem.category_id == category.id, MenuItem.name == "Cheese"
            )
        ).one()
        variants = db.scalars(
            select(MenuItemVariant)
            .where(MenuItemVariant.menu_item_id == cheese.id)
            .order_by(MenuItemVariant.display_order)
        ).all()

        assert [(v.name, v.price) for v in variants] == [
            ("Small", Decimal("10.85")),
            ("Large", Decimal("14.95")),
            ("X-Large (Sicilian)", Decimal("20.75")),
        ]


def test_seed_twice_preserves_totals(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)
        assert menu_counts(db) == (21, 292, 515)
        seed_menu(db)

    with Session(menu_engine) as db:
        assert menu_counts(db) == (21, 292, 515)


def test_seed_preserves_representative_category_and_item_display_order(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)
        categories = db.scalars(
            select(MenuCategory)
            .where(MenuCategory.name.in_(["Salads", "Pizzas", "Specialty Pizzas"]))
            .order_by(MenuCategory.display_order)
        ).all()

        # Fixed expectations verify stored positions, not just sorted output.
        assert [(category.name, category.display_order) for category in categories] == [
            ("Pizzas", 13),
            ("Specialty Pizzas", 14),
            ("Salads", 15),
        ]
        items = db.scalars(
            select(MenuItem)
            .where(MenuItem.category_id == categories[0].id)
            .order_by(MenuItem.display_order)
        ).all()
        assert [(item.name, item.display_order) for item in items] == [
            ("Cheese", 1),
            ("1 Topping", 2),
            ("2 Toppings", 3),
            ("3 Toppings", 4),
            ("4 Toppings", 5),
        ]


def test_seed_replaces_existing_menu_and_cascades_children(menu_engine):
    with Session(menu_engine) as db:
        db.add(
            MenuCategory(
                name="Obsolete category",
                display_order=1,
                items=[
                    MenuItem(
                        name="Obsolete item",
                        display_order=1,
                        variants=[
                            MenuItemVariant(
                                name="Obsolete variant",
                                price=Decimal("1.00"),
                                display_order=1,
                            )
                        ],
                    )
                ],
            )
        )
        db.commit()
        seed_menu(db)

    with Session(menu_engine) as db:
        assert menu_counts(db) == (21, 292, 515)
        for model, name in (
            (MenuCategory, "Obsolete category"),
            (MenuItem, "Obsolete item"),
            (MenuItemVariant, "Obsolete variant"),
        ):
            assert db.scalar(select(model).where(model.name == name)) is None


def test_seed_excludes_market_price_items(menu_engine):
    with Session(menu_engine) as db:
        seed_menu(db)

        seafood = db.scalars(
            select(MenuCategory).where(MenuCategory.name == "Seafood")
        ).one()
        seafood_items = db.scalars(
            select(MenuItem).where(MenuItem.category_id == seafood.id)
        ).all()

        salads = db.scalars(
            select(MenuCategory).where(MenuCategory.name == "Salads")
        ).one()
        salad_items = db.scalars(
            select(MenuItem).where(MenuItem.category_id == salads.id)
        ).all()

        # Exclusions must hold within populated categories.
        assert seafood_items
        assert salad_items
        assert "Lobster Roll (seasonal)" not in {item.name for item in seafood_items}
        assert "Lobster Salad" not in {item.name for item in salad_items}
