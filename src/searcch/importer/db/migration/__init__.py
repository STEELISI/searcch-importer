import os
import alembic
import alembic.config
import alembic.script
import alembic.migration
import alembic.command

from searcch.importer.util.config import find_configfile,get_config_parser

our_alembic_ini = os.path.join(os.path.dirname(__file__),"alembic.ini")

def get_alembic_config():
    return alembic.config.Config(our_alembic_ini)

def check_at_head(engine,config=get_alembic_config()):
    config.set_main_option("sqlalchemy.url",str(engine.url))
    directory = alembic.script.ScriptDirectory.from_config(config)
    with engine.begin() as connection:
        context = alembic.migration.MigrationContext.configure(connection)
        return set(context.get_current_heads()) == set(directory.get_heads())

def upgrade(engine,revision="head",config=get_alembic_config()):
    config.set_main_option("sqlalchemy.url",str(engine.url))
    with engine.begin() as connection:
        config.attributes["connection"] = engine
        return alembic.command.upgrade(config,revision)
    
