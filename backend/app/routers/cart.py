from uuid import UUID

from fastapi import APIRouter, Body, Depends, Response
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.cart import (
    CartCreateRequest,
    CartItemCreateRequest,
    CartItemQuantityRequest,
    CartResponse,
)
from app.services import cart as service


class CartRoute(APIRoute):
    """Keep the cart error contract local without changing existing menu errors."""

    def get_route_handler(self):
        handler = super().get_route_handler()

        async def cart_handler(request):
            try:
                return await handler(request)
            except RequestValidationError as exc:
                return JSONResponse(
                    status_code=422,
                    content={
                        "error": {
                            "code": "validation_error",
                            "message": "Invalid cart request.",
                            "details": [
                                {
                                    "field": ".".join(
                                        str(part) for part in error["loc"][1:]
                                    ),
                                    "reason": error["type"],
                                }
                                for error in exc.errors()
                            ],
                        }
                    },
                )
            except service.CartError as exc:
                return JSONResponse(
                    status_code=exc.status_code, content=jsonable_encoder(exc.content)
                )

        return cart_handler


router = APIRouter(prefix="/api/carts", tags=["carts"], route_class=CartRoute)


@router.post("", response_model=CartResponse, status_code=201)
def create_cart(
    response: Response,
    body: CartCreateRequest | None = Body(default=None),
    db: Session = Depends(get_db),
) -> CartResponse:
    cart = service.create_cart(db)
    response.headers["Location"] = f"/api/carts/{cart.id}"
    return cart


@router.get("/{cart_id}", response_model=CartResponse)
def get_cart(cart_id: UUID, db: Session = Depends(get_db)) -> CartResponse:
    return service.get_cart(db, cart_id)


@router.post("/{cart_id}/items", response_model=CartResponse, status_code=201)
def add_item(
    cart_id: UUID, body: CartItemCreateRequest, db: Session = Depends(get_db)
) -> CartResponse:
    return service.add_item(db, cart_id, body)


@router.patch("/{cart_id}/items/{cart_item_id}", response_model=CartResponse)
def update_quantity(
    cart_id: UUID,
    cart_item_id: UUID,
    body: CartItemQuantityRequest,
    db: Session = Depends(get_db),
) -> CartResponse:
    return service.update_quantity(db, cart_id, cart_item_id, body)
