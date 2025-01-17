
import configparser
import six
import abc
import os
from future.utils import iteritems

CONFIG_DEFAULTS = dict()

def config_section(cls):
    global CONFIG_DEFAULTS
    CONFIG_DEFAULTS[cls.section_name()] = cls.section_defaults()

@six.add_metaclass(abc.ABCMeta)
class ConfigSection(object):

    @abc.abstractclassmethod
    def section_name(cls):
        pass

    @abc.abstractclassmethod
    def section_defaults(cls):
        pass

class MyConfigParser(configparser.ConfigParser):

    def __init__(self,*args,**kwargs):
        super(MyConfigParser,self).__init__(*args,**kwargs)
        for (name,defaults) in iteritems(CONFIG_DEFAULTS):
            if not name in self:
                self.add_section(name)
            for (k,v) in iteritems(defaults):
                self.set(name,k,v)

    def read_env(self):
        for (name,defaults) in iteritems(CONFIG_DEFAULTS):
            for (k,v) in iteritems(defaults):
                var = "%s_%s" % (str(name).upper(),str(k).upper())
                val = os.getenv(var)
                if val is not None:
                    self.set(name,k,val)

def get_config_parser(*args,**kwargs):
    return MyConfigParser(*args,**kwargs)

DEFAULT_CONFIGFILE_PATHS = [ "/etc/searcch-importer.ini" ]
if os.getenv("HOME"):
    DEFAULT_CONFIGFILE_PATHS.insert(
        0,"%s/.config/searcch-importer.ini" % (os.getenv("HOME")))
    DEFAULT_CONFIGFILE_PATHS.insert(
        0,"%s/.local/etc/searcch-importer.ini" % (os.getenv("HOME")))
if os.getenv("SEARCCH_IMPORTER_CONFIGFILE"):
    DEFAULT_CONFIGFILE_PATHS = [ os.getenv("SEARCCH_IMPORTER_CONFIGFILE") ]

def find_configfile():
    for fp in DEFAULT_CONFIGFILE_PATHS:
        if os.path.exists(fp) and os.access(fp,os.R_OK):
            return fp
    return None

def add_default_configfile(fp):
    global DEFAULT_CONFIGFILE_PATHS
    if not fp in DEFAULT_CONFIGFILE_PATHS:
        DEFAULT_CONFIGFILE_PATHS.insert(0,fp)
    return None

@config_section
class DefaultConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "DEFAULT"

    @classmethod
    def section_defaults(cls):
        return dict(
            user_email=os.getenv("USER","nobody") + "@localhost",
            user_name=os.getenv("USER","nobody"),
            tmpdir="/var/tmp/searcch-importer")

@config_section
class RetrieverConfigSection(ConfigSection):

    @classmethod
    def section_name(cls):
        return "retrieve"

    @classmethod
    def section_defaults(cls):
        return dict(
            git="/usr/bin/git",
            max_file_size="134217728")
