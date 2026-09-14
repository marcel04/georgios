from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.menu import MenuCategory
from app.schemas.menu import MenuCategoryResponse

# All routes in this router share the /api/menu prefix.
router = APIRouter(
    prefix="/api/menu",
    tags=["menu"],
)


@router.get(
    "/categories",
    # Serialize ORM objects using only the public category fields.
    response_model=list[MenuCategoryResponse],
)
def get_menu_categories(
    # FastAPI obtains a session and runs get_db cleanup after use.
    db: Session = Depends(get_db),
) -> list[MenuCategory]:
    # Filter and sort in the database rather than after loading all categories.
    statement = (
        select(MenuCategory)
        .where(MenuCategory.is_active.is_(True))
        .order_by(MenuCategory.display_order)
    )

    # scalars() yields model objects rather than SQLAlchemy Row wrappers.
    # No matches naturally produces [], with HTTP 200.
    return list(db.scalars(statement).all())
