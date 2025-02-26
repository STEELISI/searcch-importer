import os
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name,disable_existing_loggers=False)

LOG = logging.getLogger(__name__)

# add your model's MetaData object here
# for 'autogenerate' support
import searcch.importer.db.model
target_metadata = searcch.importer.db.model.Base.metadata

# NB: this stuff only runs when running alembic standalone, from the CLI.  When
# run from searcch.importer.(db|client), those handle this stuff.
#
# Accept a variety of methods to get the sqlalchemy db URL if one is not
# already set:
#   * SEARCCH_IMPORTER_DB_URL env var
#   * SEARCCH_IMPORTER_CONFIG_FILE env var
#   * default config file search
# Use the searcch importer config file to set the alembic sqlalchemy URL.
if not config.get_main_option("sqlalchemy.url"):
    from searcch.importer.util.config import find_configfile,get_config_parser
    searcch_url = os.getenv("SEARCCH_IMPORTER_DB_URL")
    if not searcch_url:
        cf = os.getenv("SEARCCH_IMPORTER_CONFIG_FILE")
        if not cf:
            cf = find_configfile()
        if cf:
            searcch_config = get_config_parser()
            searcch_config.read(cf)
            searcch_url = searcch_config["db"]["url"]
        else:
            LOG.error("cannot find searcch importer sqlalchemy db URL!")
            exit(1)
    if not searcch_url:
        LOG.error("searcch importer sqlalchemy db URL is null; aborting!")
        exit(1)
    config.set_main_option("sqlalchemy.url",searcch_url)

def run_migrations_offline():
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


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata,
            # We want batch-oriented autogenerated migrations for sqlalchemy.
            render_as_batch=True
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
