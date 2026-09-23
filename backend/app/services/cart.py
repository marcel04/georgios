from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart, CartItem, CartItemModifierOption, CartStatus
from app.models.menu import MenuItem, MenuItemVariant, ModifierOption
from app.schemas.cart import (
    CartGroupResponse,
    CartItemResponse,
    CartOptionResponse,
    CartResponse,
)


def server_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    # SQLite test storage drops offsets; production TIMESTAMPTZ is aware.
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class CartError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        *,
        cart: Cart | None = None,
        details: list[dict] | None = None,
    ):
        self.status_code = status_code
        self.content = {
            "error": {"code": code, "message": message, "details": details or []}
        }
        if cart is not None:
            self.content.update(
                cart_id=str(cart.id),
                status=cart.status.value,
                expires_at=as_utc(cart.expires_at),
            )


def create_cart(db: Session) -> CartResponse:
    cart = Cart(expires_at=server_now() + timedelta(minutes=10))
    db.add(cart)
    db.flush()  # Let the existing database defaults assign UUID and status.
    response = CartResponse(
        id=cart.id,
        status="ACTIVE",
        expires_at=as_utc(cart.expires_at),
        item_count=0,
        subtotal=Decimal("0.00"),
        items=[],
    )
    db.commit()
    return response


def get_cart(db: Session, cart_id: UUID) -> CartResponse:
    # One statement gives validation and pricing a consistent menu snapshot.
    variant = joinedload(Cart.items).joinedload(CartItem.menu_item_variant)
    option = (
        joinedload(Cart.items)
        .joinedload(CartItem.modifier_options)
        .joinedload(CartItemModifierOption.modifier_option)
    )
    cart = (
        db.scalars(
            select(Cart)
            .where(Cart.id == cart_id)
            .options(
                variant.joinedload(MenuItemVariant.menu_item).joinedload(
                    MenuItem.category
                ),
                variant.joinedload(MenuItemVariant.menu_item).joinedload(
                    MenuItem.modifier_groups
                ),
                option.joinedload(ModifierOption.modifier_group),
                option.joinedload(ModifierOption.prices),
            )
        )
        .unique()
        .one_or_none()
    )
    if cart is None:
        raise CartError(404, "cart_not_found", "Cart not found.")
    if cart.status == CartStatus.EXPIRED or server_now() >= as_utc(cart.expires_at):
        transition = cart.status == CartStatus.ACTIVE
        if transition:
            cart.status = CartStatus.EXPIRED
        error = CartError(
            410, "cart_expired", "This cart has expired. Create a new cart.", cart=cart
        )
        if transition:
            db.commit()  # Persist the transition before returning the domain error.
        raise error

    items = []
    conflicts = []
    for line in sorted(cart.items, key=lambda line: (line.created_at, line.id)):
        variant = line.menu_item_variant
        item = variant.menu_item

        def conflict(field, reason, **ids):
            conflicts.append(
                dict(cart_item_id=str(line.id), field=field, reason=reason, **ids)
            )

        if (
            not variant.is_available
            or not item.is_available
            or not item.category.is_active
        ):
            conflict("menu_item_variant_id", "item_unavailable")
        selections = {}
        for selection in line.modifier_options:
            option = selection.modifier_option
            group = option.modifier_group
            selections.setdefault(group.id, (group, []))[1].append(option)
        for group in item.modifier_groups:
            count = len(selections.get(group.id, (None, []))[1])
            if (
                group.is_active
                and not group.min_selections <= count <= group.max_selections
            ):
                conflict(
                    "modifier_groups", "selection_bounds", modifier_group_id=group.id
                )
        groups = []
        unit_price = variant.price
        for group, options in sorted(
            selections.values(), key=lambda pair: pair[0].display_order
        ):
            if not group.is_active or group.menu_item_id != item.id:
                conflict(
                    "modifier_groups", "group_unavailable", modifier_group_id=group.id
                )
            responses = []
            for option in sorted(options, key=lambda option: option.display_order):
                ids = dict(modifier_group_id=group.id, modifier_option_id=option.id)
                price = next(
                    (
                        price
                        for price in option.prices
                        if price.menu_item_variant_id == variant.id
                    ),
                    None,
                )
                if not option.is_available:
                    conflict("modifier_groups", "option_unavailable", **ids)
                if price is None:
                    conflict("modifier_groups", "price_unavailable", **ids)
                    continue
                unit_price += price.price_adjustment
                responses.append(
                    CartOptionResponse(
                        modifier_option_id=option.id,
                        modifier_option_name=option.name,
                        price_adjustment=price.price_adjustment,
                    )
                )
            groups.append(
                CartGroupResponse(
                    modifier_group_id=group.id,
                    modifier_group_name=group.name,
                    options=responses,
                )
            )
        items.append(
            CartItemResponse(
                id=line.id,
                menu_item_id=item.id,
                menu_item_name=item.name,
                menu_item_variant_id=variant.id,
                menu_item_variant_name=variant.name,
                quantity=line.quantity,
                special_instructions=line.special_instructions,
                modifier_groups=groups,
                unit_price=unit_price,
                line_total=unit_price * line.quantity,
            )
        )
    if conflicts:
        raise CartError(
            409,
            "cart_menu_conflict",
            "A cart selection is no longer available.",
            cart=cart,
            details=conflicts,
        )
    return CartResponse(
        id=cart.id,
        status=cart.status,
        expires_at=as_utc(cart.expires_at),
        items=items,
        item_count=sum(line.quantity for line in items),
        subtotal=sum((line.line_total for line in items), Decimal("0.00")),
    )
