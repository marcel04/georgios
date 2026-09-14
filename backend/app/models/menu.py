from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    and_,
    func,
    text,
)
from sqlalchemy.orm import Mapped, foreign, mapped_column, relationship

from app.database import Base


class MenuCategory(Base):
    __tablename__ = "menu_categories"

    __table_args__ = (
        UniqueConstraint(
            "display_order",
            name="uq_menu_categories_display_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    display_order: Mapped[int] = mapped_column(
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    items: Mapped[list[MenuItem]] = relationship(
        back_populates="category",
        cascade="all, delete",
        passive_deletes=True,
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    __table_args__ = (
        UniqueConstraint(
            "category_id",
            "display_order",
            name="uq_menu_items_category_display_order",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    category_id: Mapped[int] = mapped_column(
        ForeignKey(
            "menu_categories.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    display_order: Mapped[int] = mapped_column(
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    category: Mapped[MenuCategory] = relationship(
        back_populates="items",
    )

    variants: Mapped[list[MenuItemVariant]] = relationship(
        back_populates="menu_item",
        cascade="all, delete",
        passive_deletes=True,
    )

    modifier_groups: Mapped[list[ModifierGroup]] = relationship(
        back_populates="menu_item",
        cascade="all, delete",
        passive_deletes=True,
    )


class MenuItemVariant(Base):
    __tablename__ = "menu_item_variants"

    __table_args__ = (
        UniqueConstraint("id", "menu_item_id", name="uq_menu_item_variants_id_item"),
        UniqueConstraint(
            "menu_item_id",
            "name",
            name="uq_menu_item_variants_item_name",
        ),
        UniqueConstraint(
            "menu_item_id",
            "display_order",
            name="uq_menu_item_variants_display_order",
        ),
        CheckConstraint(
            "price > 0",
            name="ck_menu_item_variants_price_positive",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey(
            "menu_items.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )

    display_order: Mapped[int] = mapped_column(
        nullable=False,
    )

    is_available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    menu_item: Mapped[MenuItem] = relationship(
        back_populates="variants",
    )

    modifier_option_prices: Mapped[list[ModifierOptionPrice]] = relationship(
        back_populates="menu_item_variant",
        primaryjoin=lambda: and_(
            MenuItemVariant.id == foreign(ModifierOptionPrice.menu_item_variant_id),
            MenuItemVariant.menu_item_id == ModifierOptionPrice.menu_item_id,
        ),
        cascade="all, delete",
        passive_deletes=True,
    )


class ModifierGroup(Base):
    __tablename__ = "modifier_groups"
    __table_args__ = (
        UniqueConstraint("id", "menu_item_id", name="uq_modifier_groups_id_item"),
        UniqueConstraint("menu_item_id", "name", name="uq_modifier_groups_item_name"),
        UniqueConstraint(
            "menu_item_id", "display_order", name="uq_modifier_groups_item_order"
        ),
        CheckConstraint(
            "min_selections >= 0", name="ck_modifier_groups_min_nonnegative"
        ),
        CheckConstraint(
            "max_selections >= 0", name="ck_modifier_groups_max_nonnegative"
        ),
        CheckConstraint(
            "max_selections >= min_selections",
            name="ck_modifier_groups_selection_range",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    menu_item_id: Mapped[int] = mapped_column(
        ForeignKey("menu_items.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    min_selections: Mapped[int] = mapped_column(nullable=False)
    max_selections: Mapped[int] = mapped_column(nullable=False)
    display_order: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    menu_item: Mapped[MenuItem] = relationship(back_populates="modifier_groups")
    options: Mapped[list[ModifierOption]] = relationship(
        back_populates="modifier_group", cascade="all, delete", passive_deletes=True
    )


class ModifierOption(Base):
    __tablename__ = "modifier_options"
    __table_args__ = (
        UniqueConstraint("id", "menu_item_id", name="uq_modifier_options_id_item"),
        UniqueConstraint(
            "modifier_group_id", "name", name="uq_modifier_options_group_name"
        ),
        UniqueConstraint(
            "modifier_group_id", "display_order", name="uq_modifier_options_group_order"
        ),
        ForeignKeyConstraint(
            ["modifier_group_id", "menu_item_id"],
            ["modifier_groups.id", "modifier_groups.menu_item_id"],
            name="fk_modifier_options_group_item",
            ondelete="CASCADE",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modifier_group_id: Mapped[int] = mapped_column(nullable=False)
    menu_item_id: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int] = mapped_column(nullable=False)
    is_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("true")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    modifier_group: Mapped[ModifierGroup] = relationship(back_populates="options")
    prices: Mapped[list[ModifierOptionPrice]] = relationship(
        back_populates="modifier_option", cascade="all, delete", passive_deletes=True
    )


class ModifierOptionPrice(Base):
    __tablename__ = "modifier_option_prices"
    __table_args__ = (
        UniqueConstraint(
            "modifier_option_id",
            "menu_item_variant_id",
            name="uq_modifier_option_prices_option_variant",
        ),
        CheckConstraint(
            "price_adjustment >= 0", name="ck_modifier_option_prices_nonnegative"
        ),
        ForeignKeyConstraint(
            ["modifier_option_id", "menu_item_id"],
            ["modifier_options.id", "modifier_options.menu_item_id"],
            name="fk_modifier_option_prices_option_item",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["menu_item_variant_id", "menu_item_id"],
            ["menu_item_variants.id", "menu_item_variants.menu_item_id"],
            name="fk_modifier_option_prices_variant_item",
            ondelete="CASCADE",
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    modifier_option_id: Mapped[int] = mapped_column(nullable=False)
    menu_item_variant_id: Mapped[int] = mapped_column(nullable=False)
    menu_item_id: Mapped[int] = mapped_column(nullable=False)
    price_adjustment: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    # The option relationship supplies ownership; the variant writes only its ID.
    # Both columns still participate in the join and PostgreSQL foreign key.
    modifier_option: Mapped[ModifierOption] = relationship(back_populates="prices")
    menu_item_variant: Mapped[MenuItemVariant] = relationship(
        back_populates="modifier_option_prices",
        primaryjoin=lambda: and_(
            foreign(ModifierOptionPrice.menu_item_variant_id) == MenuItemVariant.id,
            ModifierOptionPrice.menu_item_id == MenuItemVariant.menu_item_id,
        ),
    )
