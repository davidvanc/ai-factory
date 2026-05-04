"""
Alembic helper - genereert per-service migration setup.
Builder roept generate_alembic_setup() aan voor services met database_enabled.
"""
from pathlib import Path


ALEMBIC_INI_TEMPLATE = """[alembic]
script_location = alembic
prepend_sys_path = .
sqlalchemy.url =
file_template = %%(year)d_%%(month).2d_%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
"""

ALEMBIC_ENV_TEMPLATE = '''"""Alembic environment - reads DATABASE_URL from env, sync mode for migrations."""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import models hier zodat Alembic ze ziet:
from src.service_template.database import Base
# from src.models import *  # uncomment in je service om je eigen models te registreren

config = context.config

# Lees DATABASE_URL uit environment
db_url = os.getenv("DATABASE_URL", "")
if db_url:
    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
'''

ALEMBIC_SCRIPT_MAKO = '''"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
'''


def generate_alembic_setup(project_path: Path) -> list[str]:
    """Genereer alembic config voor een service. Returns lijst van geschreven files."""
    written = []

    alembic_ini = project_path / "alembic.ini"
    alembic_ini.write_text(ALEMBIC_INI_TEMPLATE)
    written.append(str(alembic_ini))

    alembic_dir = project_path / "alembic"
    alembic_dir.mkdir(parents=True, exist_ok=True)

    env_py = alembic_dir / "env.py"
    env_py.write_text(ALEMBIC_ENV_TEMPLATE)
    written.append(str(env_py))

    script_mako = alembic_dir / "script.py.mako"
    script_mako.write_text(ALEMBIC_SCRIPT_MAKO)
    written.append(str(script_mako))

    versions_dir = alembic_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    keep = versions_dir / ".gitkeep"
    keep.write_text("")
    written.append(str(keep))

    return written
