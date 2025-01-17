
import logging
import os
import os.path

import sqlalchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from searcch.importer.util.config import (
    config_section,ConfigSection )
from searcch.importer.db.model import Base
from searcch.importer.db import migration

LOG = logging.getLogger(__name__)

class DbNotInSync(BaseException):
    pass

@config_section
class DbConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "db"

    @classmethod
    def section_defaults(cls):
        return dict(url="",auto_upgrade="true",
                    error_db_unsync="true",
                    force_create_all="false")

def ensure_db_file(config=None,url=None):
    if url:
        if url.startswith("sqlite:///"):
            path = url[len("sqlite:///"):]
    elif config and config["db"]["url"]:
        url = config["db"]["url"]
        if url.startswith("sqlite:///"):
            path = url[len("sqlite:///"):]
    elif os.getuid() == 0:
        ourpath = None
        dirs = [ "/var/db/","/var/tmp","/tmp" ]
        for d in dirs:
            if os.path.exists(d):
                ourpath = d
                break
        if not ourpath:
            os.makedirs(dirs[0])
            ourpath = dirs[0]
        path = ourpath + "/searcch-importer.db"
        url = "sqlite:///" + path
    else:
        home = os.getenv("HOME")
        if not home or not os.path.exists(home):
            raise FileNotFoundError("cannot find $HOME dir")
        path = home + os.sep + ".local" + os.sep + "var"
        if not os.path.exists(path):
            os.makedirs(path,exist_ok=True)
        path += os.sep + "searcch-importer.db"
        url = "sqlite:///" + path
    LOG.debug("ensure_db_file: url = %s, path = %s",url,path)
    if path and path != ":memory:" and not os.path.exists(path):
        f = open(path,'w')
        f.close()
    return url

def get_db_engine(config=None,url=None,echo=False):
    url = ensure_db_file(config=config,url=url)
    LOG.debug("connecting to '%s'",url)
    return create_engine(url,echo=echo)

def get_db_session(config=None,url=None,auto_upgrade=None,
                   error_db_unsync=None,echo=False):
    # Function args, if specified, override config; else, config.  If config or
    # config opts unset, then default to what the config would have been above.
    if auto_upgrade is None:
        if config:
            auto_upgrade = config["db"].getboolean("auto_upgrade")
        if auto_upgrade is None:
            auto_upgrade = True
    if error_db_unsync is None:
        if config:
            error_db_unsync = config["db"].getboolean("error_db_unsync")
        if error_db_unsync is None:
            error_db_unsync = True

    engine = get_db_engine(config=config,url=url,echo=echo)
    at_head = migration.check_at_head(engine)
    if config and config["db"].getboolean("force_create_all"):
        Base.metadata.create_all(engine,checkfirst=True)
    elif not at_head and auto_upgrade:
        migration.upgrade(engine)
    elif not at_head and error_db_unsync:
        raise DbNotInSync("database not at current migration head and db.auto_upgrade false")
    return sessionmaker(bind=engine)()
