import os
#import requests
import json
#import atexit
#import datetime
#from apscheduler.schedulers.gevent import GeventScheduler


class RemoteBackendTask(object):
    """
    A simple task wrapper that (re)connects to the backend as necessary
    and sends it status updates so it knows we're alive.
    """
    def __init__(self, logger, config, db, **kwargs):
        self.logger = logger
        self.config = config
        self.db = db
        self.api_root = self.config["searcch"].get("api_root")
        self.api_key = self.config["searcch"].get("api_key")
        self.myurl = self.config["server"].get("myurl")
        self.mykey = self.config["server"].get("secret_key")
        self.max_tasks = self.config["server"].getint("max_tasks")
        self.remote_update = self.config["server"].getboolean("remote_update")
        self.remote_update_interval = self.config["server"].getint("remote_update_interval")
        self.remote_delete_on_exit = self.config["server"].getboolean("remote_delete_on_exit")

        self._importer_instance_id = None
        self._registered = False
        self._session = None
        #self._scheduler = GeventScheduler()
        #self._scheduler.add_job(func=self.run_once, trigger="interval", next_run_time=datetime.datetime.now(),
        #                        seconds=self.remote_update_interval, max_instances=1)

        #self._scheduler.start()

        #atexit.register(lambda: self._scheduler.shutdown())
        #atexit.register(lambda: self.delete())

    @property
    def session(self):
        if not self._session:
            import requests
            self._session = requests.session()
        return self._session

    def run_once(self):
        # Try a remote update to see if we're already registered.
        if not self._registered:
            self.logger.debug("remote backend thread registering at backend (pid %d)",os.getpid())
            r = self.session.post(
                self.api_root + "/importers",
                data=json.dumps(dict(url=self.myurl,key=self.mykey,max_tasks=self.max_tasks)),
                headers={ "Content-type":"application/json",
                          "X-Api-Key":self.api_key })
            if r.status_code == 200:
                self._importer_instance_id = r.json()["id"]
                self._registered = True
                self.logger.debug("registered at backend (%d)",os.getpid())
                return True
            else:
                self.logger.error("failed to register at backend (%d)",os.getpid())
                return False

        if self._registered and self.remote_update:
            r = self.session.put(
                self.api_root + "/importer/%d" % (self._importer_instance_id,),
                data=json.dumps(dict(status="up")),
                headers={ "Content-type":"application/json",
                          "X-Api-Key":self.api_key })
            if r.status_code != 200:
                self.logger.error("failed to update status at backend %r" % (
                    r.status_code,))
                if r.status_code == 404:
                    self._registered = False
                    self._importer_instance_id = None
            else:
                self.logger.debug("updated status at backend (%d)",os.getpid())

    def delete(self):
        if not self.remote_delete_on_exit or not self._registered:
            return
        r = self.session.delete(
            self.api_root + "/importer/%d" % (self._importer_instance_id,),
            headers={ "Content-type":"application/json",
                      "X-Api-Key":self.api_key })
        if r.status_code != 200:
            self.logger.error("failed to delete our instance at backend")
        else:
            self.logger.debug("deleted remote instance at backend")
            self._importer_instance_id = None
            self._registered = False
