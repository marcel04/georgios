from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload

from app.models.cart import Cart, CartItem, CartItemModifierOption, CartStatus
from app.models.menu import MenuItem, MenuItemVariant, ModifierGroup, ModifierOption
from app.schemas.cart import (
    CartGroupResponse,
    CartItemCreateRequest,
    CartItemQuantityRequest,
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


def load_cart(db: Session, cart_id: UUID) -> Cart:
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
            .execution_options(populate_existing=True)
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
    return cart


def check_expiration(db: Session, cart: Cart, now: datetime) -> None:
    if cart.status == CartStatus.EXPIRED or now >= as_utc(cart.expires_at):
        # GET can race with a mutation. Never expire a newly refreshed deadline.
        if cart.status == CartStatus.ACTIVE:
            result = db.execute(
                update(Cart)
                .where(
                    Cart.id == cart.id,
                    Cart.status == CartStatus.ACTIVE,
                    Cart.expires_at <= now,
                )
                .values(status=CartStatus.EXPIRED)
                .execution_options(synchronize_session=False)
            )
            db.commit()
            cart = load_cart(db, cart.id)
            if (
                not result.rowcount
                and cart.status == CartStatus.ACTIVE
                and now < as_utc(cart.expires_at)
            ):
                return
        raise CartError(
            410, "cart_expired", "This cart has expired. Create a new cart.", cart=cart
        )


def get_cart(db: Session, cart_id: UUID) -> CartResponse:
    cart = load_cart(db, cart_id)
    check_expiration(db, cart, server_now())
    return render_cart(cart)


def render_cart(cart: Cart) -> CartResponse:
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


def validate_configuration(db: Session, request: CartItemCreateRequest) -> None:
    variant = (
        db.scalars(
            select(MenuItemVariant)
            .where(MenuItemVariant.id == request.menu_item_variant_id)
            .options(
                joinedload(MenuItemVariant.menu_item).joinedload(MenuItem.category),
                joinedload(MenuItemVariant.menu_item)
                .joinedload(MenuItem.modifier_groups)
                .joinedload(ModifierGroup.options)
                .joinedload(ModifierOption.prices),
            )
        )
        .unique()
        .one_or_none()
    )
    details = []

    def invalid(field, reason, **ids):
        details.append(dict(field=field, reason=reason, **ids))

    if variant is None:
        invalid("menu_item_variant_id", "variant_not_found")
    elif (
        not variant.is_available
        or not variant.menu_item.is_available
        or not variant.menu_item.category.is_active
    ):
        invalid("menu_item_variant_id", "item_unavailable")
    else:
        groups = {group.id: group for group in variant.menu_item.modifier_groups}
        supplied = set()
        for selection in request.modifier_groups:
            gid = selection.modifier_group_id
            ids = dict(modifier_group_id=gid)
            if gid in supplied:
                invalid("modifier_groups", "duplicate_group", **ids)
            supplied.add(gid)
            group = groups.get(gid)
            if group is None or not group.is_active:
                invalid("modifier_groups", "group_unavailable", **ids)
                continue
            if len(selection.option_ids) != len(set(selection.option_ids)):
                invalid("modifier_groups", "duplicate_option", **ids)
            count = len(set(selection.option_ids))
            if count < group.min_selections:
                invalid("modifier_groups", "missing_required_selections", **ids)
            if count > group.max_selections:
                invalid("modifier_groups", "too_many_selections", **ids)
            options = {option.id: option for option in group.options}
            for oid in selection.option_ids:
                option = options.get(oid)
                option_ids = dict(**ids, modifier_option_id=oid)
                if option is None:
                    invalid("modifier_groups", "option_wrong_group", **option_ids)
                elif not option.is_available:
                    invalid("modifier_groups", "option_unavailable", **option_ids)
                elif not any(
                    price.menu_item_variant_id == variant.id for price in option.prices
                ):
                    invalid(
                        "modifier_groups", "unsupported_variant_price", **option_ids
                    )
        for group in groups.values():
            if group.is_active and group.min_selections and group.id not in supplied:
                invalid(
                    "modifier_groups",
                    "missing_required_selections",
                    modifier_group_id=group.id,
                )
    if details:
        raise CartError(
            422, "validation_error", "Invalid cart configuration.", details=details
        )


@contextmanager
def cart_mutation(db: Session, cart_id: UUID):
    """Own the transaction and share the parent lock across all cart mutations."""
    try:
        cart = db.scalars(
            select(Cart).where(Cart.id == cart_id).with_for_update()
        ).one_or_none()
        now = server_now()
        if cart is None:
            raise CartError(404, "cart_not_found", "Cart not found.")
        check_expiration(db, cart, now)
        yield cart, now
        db.commit()
    except Exception:
        db.rollback()
        raise


def mutation_response(db: Session, cart: Cart, now: datetime) -> CartResponse:
    db.flush()
    # Validate the entire resulting cart before accepting or refreshing the deadline.
    response = render_cart(load_cart(db, cart.id))
    cart.expires_at = now + timedelta(minutes=10)
    response.expires_at = cart.expires_at
    return response


def add_item(
    db: Session, cart_id: UUID, request: CartItemCreateRequest
) -> CartResponse:
    with cart_mutation(db, cart_id) as (cart, now):
        validate_configuration(db, request)
        line = CartItem(
            cart_id=cart_id,
            menu_item_variant_id=request.menu_item_variant_id,
            quantity=request.quantity,
            special_instructions=request.special_instructions,
            created_at=now,
        )
        line.modifier_options = [
            CartItemModifierOption(modifier_option_id=oid)
            for group in request.modifier_groups
            for oid in group.option_ids
        ]
        db.add(line)
        response = mutation_response(db, cart, now)
    return response


def update_quantity(
    db: Session, cart_id: UUID, cart_item_id: UUID, request: CartItemQuantityRequest
) -> CartResponse:
    with cart_mutation(db, cart_id) as (cart, now):
        line = db.scalars(
            select(CartItem).where(
                CartItem.cart_id == cart_id, CartItem.id == cart_item_id
            )
        ).one_or_none()
        if line is None:
            raise CartError(404, "cart_item_not_found", "Cart item not found.")
        line.quantity = request.quantity
        response = mutation_response(db, cart, now)
    return response
