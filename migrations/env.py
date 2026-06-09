"""
ASIMNEXUS Alembic Database Migration Environment
=================================================
Configures Alembic to run migrations against both SQLite (dev) and PostgreSQL (prod).
"""

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, create_engine

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Alembic Config object
config = context.config

# Set up logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Import all models for autogenerate support
try:
    from core.database import Base
    target_metadata = Base.metadata
except ImportError:
    target_metadata = None

# Determine database URL
DATABASE_URL = os.getenv(
    "ASIM_DATABASE_URL",
    os.getenv(
        "DATABASE_URL",
        "sqlite:///data/asimnexus.db"
    )
)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without connecting)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to live DB)."""
    # For SQLite, use create_engine directly
    if DATABASE_URL.startswith("sqlite"):
        connectable = create_engine(DATABASE_URL)
    else:
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
