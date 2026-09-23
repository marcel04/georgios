from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.menu import MenuItemVariant, ModifierOption


class CartStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CONVERTED = "CONVERTED"  # Reserved for future ordering work.


class Cart(Base):
    __tablename__ = "carts"
    __table_args__ = (Index("ix_carts_status_expires_at", "status", "expires_at"),)

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    status: Mapped[CartStatus] = mapped_column(
        SAEnum(CartStatus, name="cart_status"),
        nullable=False,
        server_default=text("'ACTIVE'"),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    items: Mapped[list[CartItem]] = relationship(
        back_populates="cart", cascade="all, delete", passive_deletes=True
    )


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        CheckConstraint(
            "quantity BETWEEN 1 AND 20", name="ck_cart_items_quantity_range"
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True, server_default=text("gen_random_uuid()")
    )
    cart_id: Mapped[UUID] = mapped_column(
        ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    menu_item_variant_id: Mapped[int] = mapped_column(
        ForeignKey("menu_item_variants.id", ondelete="NO ACTION"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(nullable=False)
    special_instructions: Mapped[str | None] = mapped_column(String(250), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    cart: Mapped[Cart] = relationship(back_populates="items")
    menu_item_variant: Mapped[MenuItemVariant] = relationship()
    modifier_options: Mapped[list[CartItemModifierOption]] = relationship(
        back_populates="cart_item", cascade="all, delete", passive_deletes=True
    )


class CartItemModifierOption(Base):
    __tablename__ = "cart_item_modifier_options"

    cart_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("cart_items.id", ondelete="CASCADE"), primary_key=True
    )
    modifier_option_id: Mapped[int] = mapped_column(
        ForeignKey("modifier_options.id", ondelete="NO ACTION"),
        primary_key=True,
        index=True,
    )
    cart_item: Mapped[CartItem] = relationship(back_populates="modifier_options")
    modifier_option: Mapped[ModifierOption] = relationship()
