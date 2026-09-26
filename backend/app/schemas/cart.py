from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer

Money = Annotated[
    Decimal, PlainSerializer(lambda value: format(value, ".2f"), return_type=str)
]


class CartCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CartOptionResponse(BaseModel):
    modifier_option_id: int
    modifier_option_name: str
    price_adjustment: Money


class CartGroupResponse(BaseModel):
    modifier_group_id: int
    modifier_group_name: str
    options: list[CartOptionResponse]


class CartItemResponse(BaseModel):
    id: UUID
    menu_item_id: int
    menu_item_name: str
    menu_item_variant_id: int
    menu_item_variant_name: str
    quantity: int
    special_instructions: str | None
    modifier_groups: list[CartGroupResponse]
    unit_price: Money
    line_total: Money


class CartResponse(BaseModel):
    id: UUID
    status: Literal["ACTIVE"]
    expires_at: datetime
    item_count: int
    subtotal: Money
    items: list[CartItemResponse]


class CartGroupSelection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    modifier_group_id: int
    option_ids: list[int]


class CartItemCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    menu_item_variant_id: int
    quantity: Annotated[int, Field(strict=True, ge=1, le=20)]
    special_instructions: Annotated[str, Field(max_length=250)] | None = None
    modifier_groups: list[CartGroupSelection] = Field(default_factory=list)


class CartItemQuantityRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    quantity: Annotated[int, Field(strict=True, ge=1, le=20)]
