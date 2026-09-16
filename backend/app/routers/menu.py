from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.menu import MenuCategory, MenuItem, ModifierGroup, ModifierOption
from app.schemas.menu import (
    MenuCategoryResponse,
    MenuItemDetailResponse,
    MenuItemResponse,
)

# All routes in this router share the /api/menu prefix.
router = APIRouter(
    prefix="/api/menu",
    tags=["menu"],
)


@router.get("/categories", response_model=list[MenuCategoryResponse])
# FastAPI obtains a session and runs get_db cleanup after use.
def get_menu_categories(db: Session = Depends(get_db)) -> list[MenuCategory]:
    # Filter and sort in the database rather than after loading all categories.
    statement = (
        select(MenuCategory)
        .where(MenuCategory.is_active.is_(True))
        .order_by(MenuCategory.display_order)
    )

    # scalars() yields model objects rather than SQLAlchemy Row wrappers.
    # No matches naturally produces [], with HTTP 200.
    return list(db.scalars(statement).all())


@router.get("/categories/{category_id}/items", response_model=list[MenuItemResponse])
def get_menu_items_by_category(
    category_id: int, db: Session = Depends(get_db)
) -> list[MenuItem]:
    category = db.get(MenuCategory, category_id)

    if category is None or not category.is_active:
        raise HTTPException(
            status_code=404,
            detail="Menu category not found",
        )

    statement = (
        select(MenuItem)
        .options(selectinload(MenuItem.variants))
        .where(
            MenuItem.category_id == category_id,
            MenuItem.is_available.is_(True),
        )
        .order_by(MenuItem.display_order)
    )

    items = list(db.scalars(statement).all())

    for item in items:
        item.variants = sorted(
            [variant for variant in item.variants if variant.is_available],
            key=lambda variant: variant.display_order,
        )

    return items


@router.get("/items/{item_id}", response_model=MenuItemDetailResponse)
def get_menu_item(item_id: int, db: Session = Depends(get_db)) -> MenuItem:
    statement = (
        select(MenuItem)
        .options(
            selectinload(MenuItem.variants),
            selectinload(MenuItem.modifier_groups)
            .selectinload(ModifierGroup.options)
            .selectinload(ModifierOption.prices),
        )
        .where(
            MenuItem.id == item_id,
            MenuItem.is_available.is_(True),
        )
    )

    item = db.scalars(statement).one_or_none()

    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Menu item not found",
        )

    item.variants = sorted(
        [variant for variant in item.variants if variant.is_available],
        key=lambda variant: variant.display_order,
    )

    variant_order = {variant.id: variant.display_order for variant in item.variants}

    item.modifier_groups = sorted(
        [group for group in item.modifier_groups if group.is_active],
        key=lambda group: group.display_order,
    )

    for group in item.modifier_groups:
        group.options = sorted(
            [option for option in group.options if option.is_available],
            key=lambda option: option.display_order,
        )

        for option in group.options:
            option.prices = sorted(
                option.prices,
                key=lambda price: variant_order[price.menu_item_variant_id],
            )

    return item
