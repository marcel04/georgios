from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class MenuCategoryResponse(BaseModel):
    """Public category contract; availability and timestamps stay internal."""

    id: int
    name: str
    description: str | None
    display_order: int

    # Read values from SQLAlchemy object attributes instead of requiring a dict.
    model_config = ConfigDict(from_attributes=True)


class MenuItemVariantResponse(BaseModel):
    id: int
    name: str
    price: Decimal
    display_order: int

    model_config = ConfigDict(from_attributes=True)


class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    image_url: str | None
    display_order: int
    variants: list[MenuItemVariantResponse]

    model_config = ConfigDict(from_attributes=True)
