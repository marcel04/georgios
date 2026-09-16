from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import (
    MenuCategory,
    MenuItem,
    MenuItemVariant,
    ModifierGroup,
    ModifierOption,
    ModifierOptionPrice,
)
from app.seeds.menu_data import MENU_DATA, MENU_MODIFIER_DATA


def seed_menu(db: Session) -> None:
    # The seed file is the canonical local-development menu snapshot.
    # Delete existing categories first; ON DELETE CASCADE removes their
    # associated items, variants, and modifier data.
    db.execute(delete(MenuCategory))
    db.flush()

    items_by_category = {}
    for category_data in MENU_DATA:
        category = MenuCategory(
            name=category_data["name"],
            description=category_data.get("description"),
            display_order=category_data["display_order"],
        )

        db.add(category)
        db.flush()

        items_by_category[category.name] = {}
        for item_data in category_data["items"]:
            item = MenuItem(
                category_id=category.id,
                name=item_data["name"],
                description=item_data.get("description"),
                image_url=item_data.get("image_url"),
                display_order=item_data["display_order"],
            )

            items_by_category[category.name][item.name] = item
            db.add(item)
            db.flush()

            for variant_data in item_data["variants"]:
                variant = MenuItemVariant(
                    menu_item=item,
                    name=variant_data["name"],
                    price=Decimal(variant_data["price"]),
                    display_order=variant_data["display_order"],
                )

                db.add(variant)

    db.flush()
    _seed_modifiers(db, items_by_category)
    db.commit()


def _seed_modifiers(db: Session, items_by_category: dict) -> None:
    """Build item-owned groups and explicit prices within the seed transaction."""
    for data in MENU_MODIFIER_DATA:
        # Missing targets fail loudly rather than silently omitting configuration.
        category_items = items_by_category[data["category_name"]]
        targets = (
            [category_items[data["item_name"]]]
            if "item_name" in data
            else category_items.values()
        )
        for item in targets:
            group = ModifierGroup(
                menu_item=item,
                name=data["name"],
                min_selections=data["min_selections"],
                max_selections=data["max_selections"],
                display_order=data["display_order"],
            )
            db.add(group)
            for option_data in data["options"]:
                option = ModifierOption(
                    modifier_group=group,
                    name=option_data["name"],
                    display_order=option_data["display_order"],
                )
                db.add(option)
                # Require an explicit price: absent data never means "free".
                adjustment = Decimal(option_data["price_adjustment"])
                for variant in item.variants:
                    db.add(
                        ModifierOptionPrice(
                            modifier_option=option,
                            menu_item_variant=variant,
                            price_adjustment=adjustment,
                        )
                    )


def main() -> None:
    with SessionLocal() as db:
        seed_menu(db)


if __name__ == "__main__":
    main()
