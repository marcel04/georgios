from fastapi import FastAPI

# Uvicorn serves this application; automatic API documentation is disabled.
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
def health() -> dict[str, str]:
    # Confirms the API responds; this does not check the database connection.
    return {"status": "ok"}
