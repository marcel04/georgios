from decimal import Decimal

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import MenuCategory, MenuItem, MenuItemVariant
from app.seeds.menu_data import MENU_DATA


def seed_menu(db: Session) -> None:
    # The seed file is the canonical local-development menu snapshot.
    # Delete existing categories first; ON DELETE CASCADE removes their
    # associated items, variants, and modifier data.
    db.execute(delete(MenuCategory))
    db.flush()

    for category_data in MENU_DATA:
        category = MenuCategory(
            name=category_data["name"],
            description=category_data.get("description"),
            display_order=category_data["display_order"],
        )

        db.add(category)
        db.flush()

        for item_data in category_data["items"]:
            item = MenuItem(
                category_id=category.id,
                name=item_data["name"],
                description=item_data.get("description"),
                image_url=item_data.get("image_url"),
                display_order=item_data["display_order"],
            )

            db.add(item)
            db.flush()

            for variant_data in item_data["variants"]:
                variant = MenuItemVariant(
                    menu_item_id=item.id,
                    name=variant_data["name"],
                    price=Decimal(variant_data["price"]),
                    display_order=variant_data["display_order"],
                )

                db.add(variant)

    db.commit()


def main() -> None:
    with SessionLocal() as db:
        seed_menu(db)


if __name__ == "__main__":
    main()
