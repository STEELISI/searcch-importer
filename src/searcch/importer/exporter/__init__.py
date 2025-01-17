
import six
from future.utils import iteritems
import abc
from searcch.importer.db.model import (Exporter,ExportedObject)

@six.add_metaclass(abc.ABCMeta)
class BaseExporter(object):
    """An abstract base class that any Exporter must subclass."""

    def __init__(self,config,session,exporter_obj):
        self._config = config
        self._session = session
        self._exporter_obj = exporter_obj

    @property
    def config(self):
        return self._config

    @property
    def session(self):
        return self._session

    @property
    def exporter_obj(self):
        return self._exporter_obj

    @abc.abstractmethod
    def export_artifact(self,artifact):
        """Exports an artifact to the repository designated by an instance of this class."""

__exporters__ = dict()

def load_exporters():
    global __exporters__

    if __exporters__:
        return

    from .json import JSONExporter
    from .searcch import SearcchExporter

    __exporters__[JSONExporter.name] = JSONExporter
    __exporters__[SearcchExporter.name] = SearcchExporter

    return

def get_exporter(name,config,session):
    load_exporters()

    if not name:
        raise ValueError("must specify valid exporter name")
    elif not name in __exporters__:
        raise NotImplementedError("no such exporter '%s'" % (str(name),))

    exporter_obj = session.query(Exporter).\
        filter(Exporter.name == name).\
        filter(Exporter.version == __exporters__[name].version).first()
    if not exporter_obj:
        exporter_obj = Exporter(name=name,version=__exporters__[name].version)
        session.add(exporter_obj)
        session.commit()
    exporter = __exporters__[name](config,session,exporter_obj)
    return exporter
