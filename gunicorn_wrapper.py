#!/usr/bin/python

import gevent
import gevent.monkey

gevent.monkey.patch_all()

from  searcch.importer.server.app import app

if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=80)

