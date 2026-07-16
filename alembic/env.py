import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Permitir "import src...." sin importar desde dónde se invoque alembic
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importar TODOS los modelos (SQLModel + SQLAlchemy clásico) para que su
# metadata quede registrado antes de que Alembic compare el esquema.
# base.py hace que Base (SQLAlchemy) y SQLModel compartan el mismo metadata,
# así que un solo target_metadata cubre ambos estilos de modelo del proyecto.
from src.models.base import Base  # noqa: E402
import src.models.congress_model  # noqa: E402,F401
import src.models.sponsor_model  # noqa: E402,F401
import src.models.speaker_model  # noqa: E402,F401
import src.models.sesion_cronograma_model  # noqa: E402,F401
import src.models.congreso_sponsor_model  # noqa: E402,F401
import src.models.user  # noqa: E402,F401
import src.models.category  # noqa: E402,F401
import src.models.congress_category  # noqa: E402,F401
import src.models.course  # noqa: E402,F401
import src.models.post  # noqa: E402,F401
import src.models.enrollment  # noqa: E402,F401
import src.models.user_platform  # noqa: E402,F401

target_metadata = Base.metadata

# URL de conexión: reutiliza la misma configuración que la app (src/config/db.py),
# leída de las variables de entorno (.env). Se puede sobreescribir con
# ALEMBIC_DATABASE_URL para apuntar a otra base (ej. una BD vacía para generar
# la migración baseline sin tocar la base de desarrollo/producción).
override_url = os.getenv("ALEMBIC_DATABASE_URL")
if override_url:
    config.set_main_option("sqlalchemy.url", override_url)
else:
    from src.config.db import DATABASE_URL
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
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
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
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
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
