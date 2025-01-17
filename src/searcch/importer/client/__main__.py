
from __future__ import print_function
import argparse
import sys
import logging

from searcch.importer.util.config import find_configfile,get_config_parser
from searcch.importer.util.log import configure_logging
from searcch.importer.util.applicable import Applicable
from searcch.importer.exceptions import ImporterError
from searcch.importer.db.model import Base
from . import Client


LOG = logging.getLogger("searcch.importer")

def parse_args():

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug",dest="debug",action='store_true',
                        help="Enable debugging log level")
    parser.add_argument("-c","--config-file",type=argparse.FileType(),
                        help="Path to config file")
    parser.add_argument("--no-auto-upgrade",default=None,action='store_true',
                        help="Do not automatically upgrade the database; overrides config file.")
    parser.add_argument("--no-error-db-unsync",default=None,action='store_true',
                        help="Do not abort if the database is out of synch with the schema.")

    # Add in subparsers.
    subparsers = parser.add_subparsers(help="Subcommands",dest='subcommand')
    Applicable.add_subparsers(subparsers)

    (options, args) = parser.parse_known_args(sys.argv[1:])
    return (options,args,parser)

def client_main():
    configure_logging()

    (options,args,parser) = parse_args()
    if not options.subcommand:
        parser.error("Error: must specify a subcommand")
        exit(1)
    if options.debug:
        configure_logging(level=logging.DEBUG)
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
        logging.getLogger('sqlalchemy').setLevel(logging.INFO)
    config = get_config_parser()
    if options.config_file:
        config.read_file(options.config_file)
    else:
        cf = find_configfile()
        if cf:
            config.read(cf)
    config.read_env()

    Applicable.register_object(Client(options,config))
    try:
        retval = Applicable.apply(options.subcommand,options)
        if retval is None or retval == "":
            pass
        elif isinstance(retval,Base):
            pretty_print_record(retval)
        else:
            sys.stdout.write(str(retval))
            sys.stdout.write("\n")
    except ImporterError:
        if options.debug:
            LOG.exception("error while running %s",options.subcommand)
        else:
            print("%s: %s" % (sys.exc_info()[0].__name__,sys.exc_info()[1]))
        return 1
    except BaseException:
        LOG.exception("error while running %s",options.subcommand)
        return 1

if __name__ == "__main__":
    exit(client_main())
