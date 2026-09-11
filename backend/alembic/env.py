"""Entorno de Alembic. La URL sale de la configuracion de la aplicacion.

GAN_URL_BASE_DATOS_ALEMBIC permite apuntar a otra base sin tocar el .env,
que es lo que hacen los tests.
"""

import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

import app.modelos  # noqa: F401  deja todas las tablas registradas en Base.metadata
from alembic import context
from app.nucleo.base_datos import Base
from app.nucleo.configuracion import configuracion

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

url = os.environ.get("GAN_URL_BASE_DATOS_ALEMBIC") or configuracion.url_base_datos
config.set_main_option("sqlalchemy.url", url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
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
