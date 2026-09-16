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


class ModifierOptionPriceResponse(BaseModel):
    menu_item_variant_id: int
    price_adjustment: Decimal

    model_config = ConfigDict(from_attributes=True)


class ModifierOptionResponse(BaseModel):
    id: int
    name: str
    display_order: int
    prices: list[ModifierOptionPriceResponse]

    model_config = ConfigDict(from_attributes=True)


class ModifierGroupResponse(BaseModel):
    id: int
    name: str
    min_selections: int
    max_selections: int
    display_order: int
    options: list[ModifierOptionResponse]

    model_config = ConfigDict(from_attributes=True)


class MenuItemDetailResponse(BaseModel):
    id: int
    name: str
    description: str | None
    image_url: str | None
    display_order: int
    variants: list[MenuItemVariantResponse]
    modifier_groups: list[ModifierGroupResponse]

    model_config = ConfigDict(from_attributes=True)
