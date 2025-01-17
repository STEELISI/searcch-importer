from __future__ import print_function

import json
import base64

from searcch.importer.exporter import BaseExporter
from searcch.importer.db.model import Base

class JSONExporter(BaseExporter):
    """A simple JSON exporter that recursively flattens an Artifact record into a JSON document."""

    name = "json"
    version = "1.0"
    external = False
    jsontypes = (dict,list,tuple,str,int,float,bool,type(None))

    def _to_json(self,o,recurse=True,skip_ids=True):
        if not isinstance(o,Base):
            return

        j = {}

        for k in o.__class__.__mapper__.column_attrs.keys():
            colprop = getattr(o.__class__,k).property.columns[0]
            if skip_ids and (colprop.primary_key or colprop.foreign_keys):
                continue
            v = getattr(o,k,"")
            if v is None:
                continue
            elif isinstance(v,bytes):
                v = base64.b64encode(v).decode('utf-8')
            elif not isinstance(v,self.jsontypes):
                v = str(v)
            j[k] = v
        if not recurse:
            return j

        for k in o.__class__.__mapper__.relationships.keys():
            relprop = getattr(o.__class__,k).property
            if k.startswith("parent_") or relprop.backref or relprop.viewonly:
                continue
            #print("%r.%r" %(o.__class__,k))
            v = getattr(o,k,None)
            if v is None:
                continue
            if isinstance(v,list):
                nl = []
                for x in v:
                    if isinstance(x,Base):
                        nl.append(self._to_json(x,recurse=recurse,skip_ids=skip_ids))
                    else:
                        nl.append(x)
                v = nl
            elif isinstance(v,Base):
                v = self._to_json(v,recurse=recurse,skip_ids=skip_ids)
            elif isinstance(v,bytes):
                v = base64.b64encode(v).decode('utf-8')
            elif not isinstance(v,self.jsontypes):
                v = str(v)
            j[k] = v
        return j

    def export_artifact(self,artifact):
        """Exports an artifact in a flat JSON format."""
        return json.dumps(self._to_json(artifact))
