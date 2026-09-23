from fastapi import FastAPI

from app.routers.cart import router as cart_router
from app.routers.menu import router as menu_router

# Uvicorn serves this application; automatic API documentation is disabled.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

# Register the menu endpoints on the application served by Uvicorn.
app.include_router(menu_router)
app.include_router(cart_router)


@app.get("/health")
def health() -> dict[str, str]:
    # Confirms the API responds; this does not check the database connection.
    return {"status": "ok"}
