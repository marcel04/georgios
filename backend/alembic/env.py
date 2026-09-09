from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.core.config import settings
from app.database import Base

# Access the settings loaded from alembic.ini.
config = context.config

# Use the application's DATABASE_URL instead of the ini placeholder.
# Escape percent signs for ConfigParser, including URL-encoded password characters.
config.set_main_option(
    "sqlalchemy.url",
    settings.database_url.replace("%", "%%"),
)

# Configure migration logging from alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate compares this model metadata with the database schema.
# Future model modules must be imported here so their tables register on Base.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate migration SQL without connecting to the database (--sql)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    # Use a separate migration engine without retaining pooled connections.
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


# Alembic selects SQL output mode or live execution from the CLI options.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
