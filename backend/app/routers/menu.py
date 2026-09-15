from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models.menu import MenuCategory, MenuItem
from app.schemas.menu import MenuCategoryResponse, MenuItemResponse

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
def get_menu_items_by_category(category_id: int, db: Session = Depends(get_db)) -> list[MenuItem]:
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
            [
                variant
                for variant in item.variants
                if variant.is_available
            ],
            key=lambda variant: variant.display_order,
        )

    return items

