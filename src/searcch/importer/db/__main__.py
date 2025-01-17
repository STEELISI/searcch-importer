
from __future__ import print_function
import logging
import os
import argparse
from searcch.importer.db import get_db_session

LOG = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create the importer database via CLI.")
    parser.add_argument("--url",help="The full database URL; overrides other compositional arguments.")
    parser.add_argument("--driver",help="The dialect+driver string to be used in a URL.")
    parser.add_argument("--file",help="The filename string to be used in a URL; takes precedence over host/port/database args.")
    parser.add_argument("--host",help="The hostname/address to be used in a URL.")
    parser.add_argument("--port",help="The port to be used in a URL.")
    parser.add_argument("--database",help="The database to be used in a URL.")
    parser.add_argument("--username",help="The username to be used in a URL.")
    parser.add_argument("--password",help="The password to be used in a URL; use SEARCCH_IMPORTER_DBPASS instead.")

    args = parser.parse_args()

    if not args.url \
      and (not args.host or not args.driver or not args.database) \
      and (not args.file or not args.driver):
        print("ERROR: must supply either `url` or `driver`,`host`,`database`, or `driver`,`file` parameter values.")
        exit(-1)

    if args.url:
        url = args.url
    else:
        creds = ""
        if args.username:
            creds = args.username
            if args.password:
                creds += ":" + args.password
            elif os.getenv("SEARCCH_IMPORTER_DBPASS"):
                creds += ":" + os.getenv("SEARCCH_IMPORTER_DBPASS")
            creds += "@"
        if args.file:
            fp = args.file
            if fp[0] == "/" and fp[1] != "/":
                fp = "/" + fp
            url = "%s://%s%s" % (args.driver,creds,fp)
        else:
            server = args.host
            if args.port:
                server += ":" + args.port
            url = "%s://%s%s/%s" % (args.driver,creds,server,database)

    get_db_session(url=url,auto_upgrade=True)
    exit(0)
