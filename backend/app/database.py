from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    # Future ORM models inherit this class to share metadata with Alembic.
    pass


# Share one engine and connection pool; connections open when first needed.
engine = create_engine(settings.database_url)

# A factory for independent sessions, not a shared session instance.
SessionLocal = sessionmaker(
    bind=engine,
    # Disable automatic flushing before queries; commit still flushes changes.
    autoflush=False,
    # Callers manage transaction commits explicitly.
    autocommit=False,
)


def get_db():
    # Intended for FastAPI Depends(get_db); no route uses it yet.
    db = SessionLocal()

    try:
        # Give the caller a session and resume here during cleanup.
        yield db
    finally:
        # Release session resources even if the caller raises an exception.
        db.close()
