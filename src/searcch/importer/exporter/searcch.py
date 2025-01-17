from __future__ import print_function

import json
import requests
import datetime

from .json import JSONExporter
from searcch.importer.db.model import ExportedObject
from searcch.importer.exceptions import (
    NotExportedError )

class SearcchExporter(JSONExporter):
    """A simple SEARCCH exporter that recursively flattens an Artifact record into a JSON document and pushes it to the SEARCCH API."""

    name = "searcch"
    version = "1.0"
    external = True

    def export_artifact(self,artifact):
        """Exports an artifact in a flat JSON format."""
        # Check to see if this artifact has relationships with unexported
        # artifacts:
        new_relationships = []
        for relationship in artifact.relationships:
            exported_related_artifact = self.session.query(ExportedObject).\
              filter(ExportedObject.object_type == "artifact").\
              filter(ExportedObject.object_id == relationship.related_artifact_id).\
              filter(ExportedObject.exporter == self.exporter_obj).first()
            if not exported_related_artifact:
                raise NotExportedError(
                    "artifact",id=relationship.related_artifact_id,
                    msg="related artifact not yet exported via %r" % (self.exporter_obj,))
            # The backend has to fill in relationship.artifact_id for the
            # artifact we are exporting... but we have to reference the
            # already-exported artifacts.
            new_relationships.append(dict(
                related_artifact_id=exported_related_artifact.external_object_id,
                relation=relationship.relation))
        j = self._to_json(artifact)
        j["exporter"] = dict(name=SearcchExporter.name,version=SearcchExporter.version)
        j["relationships"] = new_relationships
        headers = dict()
        if self.config["searcch"]["api_key"]:
            headers["X-Api-Key"] = self.config["searcch"]["api_key"]
        r = requests.post(
            self.config["searcch"]["api_root"] + "/artifacts",
            headers=headers,json=j)
        if r.status_code != requests.codes.ok:
            r.raise_for_status()
        rj = r.json()
        rid = rj.get("id",None)
        if not rid and "artifact" in rj:
            rid = rj["artifact"].get("id",None)
        if rid:
            return ExportedObject(
                object_id=artifact.id,object_type="artifact",
                ctime=datetime.datetime.now(),
                external_object_id=rid)
        else:
            return r.json()
