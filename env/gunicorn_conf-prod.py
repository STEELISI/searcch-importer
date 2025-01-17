import multiprocessing

import atexit
import datetime
from apscheduler.schedulers.background import BackgroundScheduler

bind = "0.0.0.0:80"
workers = multiprocessing.cpu_count() * 2 + 1
workers = 1
worker_class = "gevent"
threads = 2 * multiprocessing.cpu_count()
threads = 1
timeout = 6000
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "debug"
pidfile = "logs/process_id.pid"
capture_output = True
enable_stdio_inheritance = True
daemon = False

#
# NB: something in our import chain imports requests before the gevent worker
# monkey patches requests.  So make sure it's done immediately.
#
if worker_class == "gevent":
    import gevent
    import gevent.monkey
    gevent.monkey.patch_all()

#
# NB: early exceptions from the app may be lost when workers fail immediately.
# Set preload_app = True if workers fail with no apparent cause; then you'll
# see exceptions.
#
#preload_app = True

def on_starting(server):
    from searcch.importer.server.app import (app, db, config)
    from searcch.importer.server.tasks import RemoteBackendTask
    from searcch.importer.db import get_db_session

    with app.app_context():
        # Make sure our database has a schema, modulo config.
        session = get_db_session(config=config)
        session.connection().invalidate()

        if config["server"].getboolean("remote_register"):
            task = RemoteBackendTask(server.log, config, db)
            scheduler = BackgroundScheduler()
            scheduler.add_job(func=task.run_once, trigger="interval", next_run_time=datetime.datetime.now(),
                              seconds=config["server"].getint("remote_update_interval"), max_instances=1)

            scheduler.start()

            atexit.register(lambda: scheduler.shutdown())
            atexit.register(lambda: task.delete())
            #RemoteBackendTask(server.log, config, db)
