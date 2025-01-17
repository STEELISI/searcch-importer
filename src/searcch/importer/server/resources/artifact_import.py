import datetime
import dateutil.parser
import logging
import json
import threading
import requests
import traceback
import sys

from flask import abort, jsonify, request, make_response, Blueprint
from flask_restful import reqparse, Resource, fields, marshal

from searcch.importer.db.model import (
    ArtifactImport, ExportedObject, ARTIFACT_IMPORT_TYPES,
    CandidateArtifact )
from searcch.importer.db.schema import (
    ArtifactSchema )
from searcch.importer.server.util import verify_api_key
from searcch.importer.server.app import ( app,db,config )
from searcch.importer.importer import (
    get_importer,ImportSession )
from searcch.importer.exporter import (
    get_exporter )


LOG = logging.getLogger(__name__)

class ThreadedArtifactImport(threading.Thread):
    """
    A simple thread to handle an artifact import (and status updates
    and final push to the server, if applicable).
    """
    def __init__(self,artifact_import_id,**kwargs):
        super(ThreadedArtifactImport,self).__init__(**kwargs)
        self.artifact_import_id = artifact_import_id
        self._stop_flag = False
        self._log = ""

    def log(self,msg):
        self._log += str(msg)

    def notify_backend(self,artifact_import,status=None,phase=None,message=None,
                       progress=0.0,bytes_retrieved=0,bytes_extracted=0,
                       artifact=None):
        api_root = config["searcch"].get("api_root")
        api_key = config["searcch"].get("api_key")
        data = dict(mtime=artifact_import.mtime.isoformat())
        if status:
            data["status"] = status
        if phase:
            data["phase"] = phase
        if message != None:
            data["message"] = message
        if progress:
            data["progress"] = progress
        if bytes_retrieved:
            data["bytes_retrieved"] = bytes_retrieved
        if bytes_extracted:
            data["bytes_extracted"] = bytes_extracted
        if self._log:
            data["log"] = self._log
        if artifact:
            data["artifact"] = artifact
        r = requests.put(
            api_root + "/artifact/import/%d" % (artifact_import.remote_id),
            headers={ "Content-type":"application/json",
                      "X-Api-Key":api_key },
            data=json.dumps(data))
        if r.status_code != requests.codes.ok:
            LOG.error("failed to notify the backend (%d) (%r)" % (r.status_code,r.content))
            return (False,r)
        return (True,r)

    def run(self,*args,**kwargs):
        with app.app_context():
            return self._run(*args,**kwargs)

    def _run(self,*args,**kwargs):
        artifact_import = db.session.query(ArtifactImport)\
          .filter(ArtifactImport.id == self.artifact_import_id).first()
        if not artifact_import:
            LOG.error("no such artifact_import_id %r; bug?" % (
                self.artifact_import_id))
            return
        nofetch = artifact_import.nofetch
        noextract = artifact_import.noextract
        noremove = artifact_import.noremove

        artifact_import.phase = "validate"
        artifact_import.mtime = datetime.datetime.now()
        #self.log("Validating URL: %r" % (artifact_import.url))
        db.session.commit()
        db.session.refresh(artifact_import)
        self.notify_backend(
            artifact_import,status="running",
            phase=artifact_import.phase,progress=1.0)

        imp = None
        try:
            imp = get_importer(artifact_import.url,config,db.session,
                               name=artifact_import.importer_module_name)
        except:
            #self.log("\nerror:\n" + traceback.format_exc())
            artifact_import.mtime = datetime.datetime.now()
            self.notify_backend(
                artifact_import,status="failed",
                message="Error while choosing importer module; please manually import this artifact (%r)." % (
                    sys.exc_info()[1]))
            return
        if not imp:
            #self.log("No importer module can handle %r; please manually import this artifact."
            #         % (artifact_import.url))
            artifact_import.mtime = datetime.datetime.now()
            self.notify_backend(
                artifact_import,status="failed",
                message="No importer module can handle this URL; please manually import this artifact.")
            return
        self.log("done.\n")

        self.log("Importing artifact: ")
        artifact_import.phase = "import"
        artifact_import.mtime = datetime.datetime.now()
        db.session.commit()
        db.session.refresh(artifact_import)
        self.notify_backend(
            artifact_import,phase=artifact_import.phase,message="",
            progress=10.0)

        artifact = None
        try:
            artifact = imp.import_artifact(CandidateArtifact(url=artifact_import.url))
        except:
            self.log("error:\n" + traceback.format_exc())
            artifact_import.mtime = datetime.datetime.now()
            self.notify_backend(
                artifact_import,status="failed",
                message="error importing artifact (%r)" % sys.exc_info()[1])
            return
        if not artifact:
            self.log("error\n")
            artifact_import.mtime = datetime.datetime.now()
            self.notify_backend(
                artifact_import,status="failed",
                message="import failed to produce an artifact")
            return
        self.log("done (%r)\n" % (artifact))
        LOG.debug("imported: %r",artifact)

        self.log("Retrieving artifact sources: ")
        artifact_import.phase = "retrieve"
        artifact_import.mtime = datetime.datetime.now()
        db.session.commit()
        self.notify_backend(
            artifact_import,phase=artifact_import.phase,message="",
            progress=40.0)

        imp_session = ImportSession(config,db.session,artifact)
        if not nofetch:
            try:
                imp_session.retrieve_all()
            except:
                self.log("error:\n" + traceback.format_exc())
                artifact_import.mtime = datetime.datetime.now()
                self.notify_backend(
                    artifact_import,status="failed",
                    message="error importing artifact")
                return
        self.log("done.\n")

        self.log("Extracting artifact sources: ")
        artifact_import.phase = "extract"
        artifact_import.mtime = datetime.datetime.now()
        db.session.commit()
        self.notify_backend(
            artifact_import,phase=artifact_import.phase,message="",
            progress=70.0)

        try:
            if not noextract:
                imp_session.extract_all()
            if not noremove:
                imp_session.remove_all()
        except:
            self.log("error:\n" + traceback.format_exc())
            artifact_import.mtime = datetime.datetime.now()
            self.notify_backend(
                artifact_import,status="failed",
                message="error importing artifact")
            return
        self.log("done.\n")

        imp_session.finalize()

        artifact_import.artifact = artifact
        db.session.add(artifact)
        try:
            db.session.commit()
            db.session.refresh(artifact_import)
        except:
            db.session.rollback()
            db.session.refresh(artifact_import)
            artifact_import.artifact = None
            self.log("Incorrect artifact content (%r):\n" % (artifact))
            self.log("error:\n" + traceback.format_exc())
            artifact_import.mtime = datetime.datetime.now()
            db.session.commit()
            self.notify_backend(
                artifact_import,status="failed",
                message="error importing artifact (%r)" % sys.exc_info()[1])
            return

        self.log("Finished import:\n\n")
        try:
            self.log(json.dumps(ArtifactSchema().dump(artifact)) + "\n")
        except:
            pass
        artifact_import.phase = "done"
        artifact_import.mtime = datetime.datetime.now()
        db.session.commit()
        (success,response) = self.notify_backend(
            artifact_import,status="completed",phase=artifact_import.phase,
            message="",progress=100.0,artifact=ArtifactSchema().dump(artifact))

        if success:
            if "id" in response.json():
                exporter = get_exporter("searcch",config,db.session)
                exp = ExportedObject(
                    object_id=artifact.id,object_type="artifact",
                    ctime=datetime.datetime.now(),
                    external_object_id=response.json()["id"],
                    exporter=exporter.exporter_obj)
                db.session.add(exp)
                db.session.commit()
            else:
                LOG.warning("server claimed success, but returned no id")
        else:
            LOG.error("server returned error (%r)" % (response.status_code,))
        return

    def stop(self):
        self._stop_flag = True

    def cleanup(self):
        self.stop()
        LOG.debug("stopped import thread")
        self.join()
        LOG.debug("joined import thread")


class ArtifactImportResourceRoot(Resource):

    def __init__(self):
        super(ArtifactImportResourceRoot,self).__init__()
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument(
            name="id",type=int,required=True,
            help="Artifact import remote id (required for status updates or final artifact push)")
        self.reqparse.add_argument(
            name="url",type=str,required=True,
            help="Artifact source URL")
        self.reqparse.add_argument(
            name="type",type=str,required=False,
            help="Artifact type")
        self.reqparse.add_argument(
            name="importer_module_name",type=str,required=False,
            help="A specific importer module name to use")
        self.reqparse.add_argument(
            name="nofetch",type=bool,required=False,default=False,
            help="If True, do not fetch artifact files.")
        self.reqparse.add_argument(
            name="noextract",type=bool,required=False,default=False,
            help="If True, do not extract additional metadata (e.g. keywords) from artifact content and files.")
        self.reqparse.add_argument(
            name="noremove",type=bool,required=False,default=False,
            help="If True, do not removed fetched artifact content.")
        self.reqparse.add_argument(
            name="ctime",type=str,required=False,
            help="The creation time of this artifact import")
        super(ArtifactImportResourceRoot,self).__init__()

    def post(self):
        """
        Start a new artifact import.
        """
        api_key = request.headers.get('X-Api-Key')
        verify_api_key(api_key)

        args = self.reqparse.parse_args()
        if "type" not in args or not args["type"]:
            args["type"] = "other"
        if args["type"] not in ARTIFACT_IMPORT_TYPES:
            abort(401,description="invalid type argument (must be one of %s)" % (
                ",".join(ARTIFACT_IMPORT_TYPES)))
        if "ctime" not in args:
            args["ctime"] = datetime.datetime.now()
        else:
            args["ctime"] = dateutil.parser.parse(args["ctime"])
        args["remote_id"] = args["id"]
        del args["id"]
        artifact_import = ArtifactImport(
            mtime=datetime.datetime.now(),phase="start",
            **args)
        res = db.session.query(ArtifactImport)\
          .filter(ArtifactImport.remote_id == args["remote_id"]).first()
        if res:
            abort(403,description="already importing this artifact")
        db.session.add(artifact_import)
        db.session.commit()
        db.session.refresh(artifact_import)

        ThreadedArtifactImport(artifact_import.id).start()
        
        response = jsonify({ "status":"up" })
        response.status_code = 200
        return response


class ArtifactImportResource(Resource):

    def __init__(self,artifact_import_id):
        super(ArtifactImporterResource,self).__init__()

        self.artifact_import = db.session.query(ArtifactImport).filter(
            ArtifactImport.id == artifact_import_id).all()
        if not self.artifact_import:
            abort(404,description="invalid artifact import id")

    def get(self,artifact_import_id):
        api_key = request.headers.get('X-Api-Key')
        verify_api_key(api_key)

        response = jsonify(self.artifact_import)
        response.status_code = 200
        return response
