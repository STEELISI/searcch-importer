
from __future__ import print_function
import os
import sys
import logging
import json
import datetime
import alembic
import sqlalchemy
import fileinput

from searcch.importer.util.config import find_configfile,get_config_parser
from searcch.importer.util.log import configure_logging
from searcch.importer.util.sql import object_from_json
from searcch.importer.importer import (get_importer,get_importer_names,ImportSession)
from searcch.importer.exporter import get_exporter
from searcch.importer.db import (get_db_session,get_db_engine)
from searcch.importer.db.migration import (check_at_head,upgrade)
from searcch.importer.util.applicable import (
    Applicable,ApplicableClass,ApplicableMethod,
    ApplicableFormatter,
    DefaultSubcommandArgumentParser)
from searcch.importer.db.model import (
    Base,Artifact,Person,User,ArtifactTag,ArtifactMetadata,
    ArtifactPublication,ArtifactCuration,License,
    ArtifactRelationship,ExportedObject,
    CandidateArtifact,CandidateArtifactRelationship,
    ARTIFACT_RELATIONS)
from searcch.importer.exceptions import *


LOG = logging.getLogger("searcch.importer")

def get_default_maxwidth():
    try:
        return os.get_terminal_size()[0]
    except:
        return 80

@ApplicableFormatter(
    kwargs=[dict(name="recurse",help="Recursively print related records",
                 action="store_true",default=False),
            dict(name="maxwidth",help="Max char width to print (with exceptions: we will never truncate field names or record type titles; and we will never truncate values below 5 characters).  Defaults to the width of your terminal if we can extract it (>=Python 3.3), else 80 characters.",
                 type=int),
            dict(name="indent",help="Indentation level for recursive records",
                 type=int)],
    excluded=["cur_indent","parentstr","seen","root_class"])
def pretty_print_record(o,maxwidth=get_default_maxwidth(),
                        indent=2,recurse=False,
                        cur_indent=0,parentstr="",seen=[],
                        root_class=None):
    if not isinstance(o,Base):
        return
    is_root_class_instance = False
    if not root_class:
        root_class = o.__class__
    elif isinstance(o,root_class):
        is_root_class_instance = True
    if o in seen:
        return
    if maxwidth is None:
        maxwidth = 0
    title = o.__class__.__name__
    if parentstr:
        title = parentstr + "." + title
    title_width = len(title)
    field_width = len("Field")
    for k in o.__class__.__mapper__.column_attrs.keys():
        if len(k) > field_width:
            field_width = len(k)
    for k in o.__class__.__mapper__.relationships.keys():
        if len(k) > field_width:
            field_width = len(k)
    val_width = len("Value")
    for k in o.__class__.__mapper__.column_attrs.keys():
        l = len(repr(getattr(o,k,"")))
        if l > val_width:
            val_width = l
    relationship_values = {}
    todo = []
    for k in o.__class__.__mapper__.relationships.keys():
        v = getattr(o,k,None)
        if not v:
            val = "None"
        elif isinstance(v,Base):
            val = repr(v)
            todo.append(v)
        elif isinstance(v,list):
            val = str(len(v))
            todo.extend(v)
        else:
            val = str(v)
        l = len(val)
        if l > val_width:
            val_width = l
        relationship_values[k] = val
    # We do not truncate the object title nor its fields, and we assume a
    # minimum of 5 chars to display partial values.  maxwidth is about
    # truncating values if necessary.  Our goal with all this is to calculate
    # two values: total_width (the max width of chars per line that we will
    # print); and val_width (a subordinate value that governs how wide the
    # value chars will be).
    total_title_width = cur_indent + title_width + 4
    total_fv_width = cur_indent + field_width + 4 + 3 + val_width
    MIN_VAL_WIDTH = 5
    least_val_width = val_width
    if least_val_width > MIN_VAL_WIDTH:
        least_val_width = MIN_VAL_WIDTH
    total_least_fv_width = cur_indent + field_width + 4 + 3 + least_val_width
    if maxwidth > 0:
        # We may need to limit chars per line:
        minwidth = total_title_width
        wide = "t"
        if total_fv_width > minwidth:
            minwidth = total_fv_width
            wide = "kv"
        if minwidth > maxwidth:
            total_width = minwidth
            if wide == "t":
                val_width = total_width - (cur_indent + field_width + 4 + 3)
            else:
                # This is the complicated case.  We are willing to reduce
                # val_width to least_val_width, but we only want to reduce it
                # as necessary for the title_width -- because we are not
                # willing to reduce that.
                ourmaxwidth = maxwidth
                if total_title_width > maxwidth:
                    ourmaxwidth = total_title_width
                if total_least_fv_width > ourmaxwidth:
                    ourmaxwidth = total_least_fv_width
                    val_width = least_val_width
                else:
                    val_width = ourmaxwidth - (cur_indent + field_width + 4 + 3)
                total_width = ourmaxwidth
        else:
            if wide == "t":
                total_width = minwidth
                val_width = minwidth - (cur_indent + field_width + 4 + 3)
            else:
                total_width = cur_indent + field_width + 4 + 3 + val_width
    else:
        # We just want to print everything, no limits:
        total_width = field_width + val_width + 4 + 3 + cur_indent
        if total_title_width > total_width:
            total_width = total_title_width
            diff = total_width - (field_width + val_width + 4 + 3 + cur_indent)
            val_width += diff

    print(" " * cur_indent + "+" + "=" * (total_width - 2 - cur_indent) + "+")
    print(" " * cur_indent + "| {:<{}} |".format(
        title[:(total_width - 4 - cur_indent)],total_width - 4 - cur_indent))
    print(" " * cur_indent + "+" + "=" * (total_width - 2 - cur_indent) + "+")
    print("{:<{}}| {:<{}} | {:<{}} |".format(
        "",cur_indent,"Field",field_width,"Value",val_width))
    print(" " * cur_indent + "+" + "-" * (total_width - 2 - cur_indent) + "+")
    for k in o.__class__.__mapper__.column_attrs.keys():
        v = str(getattr(o,k,""))
        print("{li:<{cur_indent}}| {field:<{field_width}} | {val:<{val_width}} |".format(
            li="",cur_indent=cur_indent,
            field=k,field_width=field_width,
            val=str(v)[:val_width],val_width=val_width))
    for k in o.__class__.__mapper__.relationships.keys():
        v = relationship_values[k]
        print("{li:<{cur_indent}}| {field:<{field_width}} | {val:<{val_width}} |".format(
            li="",cur_indent=cur_indent,
            field=k,field_width=field_width,
            val=str(v)[:val_width],val_width=val_width))
    print(" " * cur_indent + "+" + "-" * (total_width - 2 - cur_indent) + "+")
    if hasattr(o,"id"):
        title += "(%s)" % (str(o.id))
    if recurse and todo and not is_root_class_instance:
        seen.append(o)
        for t in todo:
            pretty_print_record(
                t,maxwidth=maxwidth,cur_indent=cur_indent+indent,indent=indent,
                parentstr=title,recurse=recurse,seen=seen,root_class=root_class)

@ApplicableClass()
class Client(object):

    def __init__(self,options,config,session=None,logger=LOG):
        self.options = options
        self.config = config
        self._session = session
        self.logger = logger

    def get_user(self):
        person = self.session.query(Person).\
            filter(Person.name == self.config["DEFAULT"]["user_name"]).\
            filter(Person.email == self.config["DEFAULT"]["user_email"]).\
            first()
        if not person:
            person = Person(email=self.config["DEFAULT"]["user_email"],
                            name=self.config["DEFAULT"]["user_name"])
            user = User(person=person)
        else:
            user = self.session.query(User).\
                filter(User.person == person).\
                first()
            if not user:
                user = User(person=person)
        return user

    @property
    def session(self):
        if self._session:
            return self._session
        auto_upgrade = None
        if self.options.no_auto_upgrade is not None:
            auto_upgrade = not self.options.no_auto_upgrade
        error_db_unsync = None
        if self.options.no_error_db_unsync is not None:
            error_db_unsync = not self.options.no_error_db_unsync
        self._session = get_db_session(
            config=self.config,echo=self.options.debug,
            auto_upgrade=auto_upgrade,error_db_unsync=error_db_unsync)
        return self._session

    @ApplicableMethod(alias="db.check")
    def db_check(self):
        return check_at_head(
            engine=get_db_engine(self.config,echo=self.options.debug))

    @ApplicableMethod(alias="db.upgrade")
    def db_upgrade(self):
        return upgrade(
            engine=get_db_engine(self.config,echo=self.options.debug))

    @ApplicableMethod(alias="db.create_all")
    def db_create_all(self):
        self.config["db"]["force_create_all"] = "true"
        return get_db_session(
            config=self.config,echo=self.options.debug)

    def get_importer(self,candidate,importer=None):
        return get_importer(candidate.url,self.config,self.session,name=importer)

    def artifact_import_core(self,candidate,importer=None):
        imp = None
        try:
            imp = self.get_importer(candidate,importer=importer)
        except:
            raise ImporterInternalError("error while getting importer",exc_info=sys.exc_info())
        if not imp:
            raise ImporterNotFound("no importer can import %r" % (candidate.url,))
        return imp.import_artifact(candidate)

    def artifact_import_post(self,artifact,fetch=True,remove=True,extract=True):
        imp_session = ImportSession(self.config,self.session,artifact)
        if fetch:
            imp_session.retrieve_all()
        if extract:
            imp_session.extract_all()
        if remove:
            imp_session.remove_all()
        imp_session.finalize()
        artifact.set_import_session(artifact)

    def artifact_import_one(self,candidate,importer=None,fetch=True,remove=True,
                            extract=True):
        ret = self.artifact_import_core(candidate,importer=importer)
        if isinstance(ret,Artifact):
            self.artifact_import_post(
                ret,fetch=fetch,remove=remove,extract=extract)
        return ret

    def artifact_import_all(self,candidate,importer=None,fetch=True,remove=True,
                            follow=True,extract=True,candidates=[]):
        imported = dict()
        ret = self.artifact_import_one(
            candidate,importer=importer,fetch=fetch,remove=remove,
            extract=extract)
        if not ret:
            return None
        else:
            self.session.add(ret)
        imported[candidate.url] = ret
        pending = [ ret ]
        for (crelation,curl) in candidates:
            if curl in imported:
                self.logger.info("candidate %r already imported; not processing duplicate candidate relationship" % (curl))
                continue
            ca = CandidateArtifact(url=curl,ctime=datetime.datetime.now(),
                                   owner=ret.owner)
            ret.candidate_relationships.append(
                CandidateArtifactRelationship(relation=crelation,related_candidate=ca))
        while follow and len(pending) > 0:
            p = pending.pop(0)
            for car in p.candidate_relationships:
                if car.related_candidate.imported_artifact:
                    continue
                ca = car.related_candidate
                curl = ca.url
                if curl in imported:
                    ca.imported_artifact = imported[curl]
                    self.session.add(ca)
                    ar = ArtifactRelationship(
                        artifact=p,relation=car.relation,
                        related_artifact=ca.imported_artifact)
                    p.relationships.append(ar)
                    continue
                else:
                    ret = self.artifact_import_one(
                        ca,fetch=fetch,remove=remove,extract=extract)
                    if not ret:
                        self.logger.warn("failed to import candidate %r",ca)
                        continue
                    car.related_candidate.imported_artifact = ret
                    self.session.add(car.related_candidate)
                    ar = ArtifactRelationship(
                        relation=car.relation,related_artifact=ret)
                    p.relationships.append(ar)
                    self.session.add(ret)
                    imported[ret.url] = ret
                    pending.append(ret)
        # If other artifacts had possible relationships to this candidate,
        # recast them as real ArtifactRelationships at this point.
        for car in candidate.candidate_artifact_relationships:
            ar = ArtifactRelationship(
                artifact_id=car.artifact.id,relation=car.relation,
                related_artifact_id=ret.id)
            self.session.add(ar)
        # Update the candidate to reflect the new import.
        candidate.imported_artifact = ret
        candidate.mtime = datetime.datetime.now()
        self.session.commit()

        if len(imported) > 1:
            return list(imported.values())
        else:
            return list(imported.values())[0]

    def _parse_candidates(x):
        ret = []
        if not x:
            return ret
        l1 = x.split(";")
        for i in l1:
            l2 = i.split(",")
            if not len(l2) == 2:
                raise MalformedArgumentsError("malformed candidates list")
            if l2[0] not in ARTIFACT_RELATIONS:
                raise MalformedArgumentsError("invalid relation %r; must be one of %r" % (
                    l2[0],ARTIFACT_RELATIONS))
            ret.append((l2[0],l2[1]))
        return ret

    @ApplicableMethod(
        alias="artifact.import",
        kwargs=[dict(name="sessionid",type=int),
            dict(name="nofetch",action="store_true",default=False),
            dict(name="noremove",action="store_true",default=False),
            dict(name="nofollow",action="store_true",default=False),
            dict(name="noextract",action="store_true",default=False),
            dict(name="candidates",type=_parse_candidates,default=[])])
    def artifact_import(self,url,importer="",sessionid=None,
                        nofetch=False,noremove=False,nofollow=False,
                        noextract=False,candidates=[]):
        """
        Import an artifact from a URL.

        :param url: a URL pointing to an artifact
        :param importer: the name of a specific importer to use; or the empty string for automatic selection
        :param sessionid: an explicit import sessionid to begin or resume from
        :param nofetch: do not download artifact files
        :param noremove: do not remove downloaded artifact files
        :param nofollow: do not automatically follow suggested artifacts
        :param candidates: a semicolon-separated list of relation,url tuples that specifies a URL that is related to the main artifact
        """
        return self.artifact_import_all(
            CandidateArtifact(url=url),importer=importer,
            fetch=not nofetch,remove=not noremove,follow=not nofollow,
            extract=not noextract,candidates=candidates)

    @ApplicableMethod(
        alias="artifact.create",
        kwargs=[
            dict(name="nofetch",action="store_true",default=False),
            dict(name="noremove",action="store_true",default=False),
            dict(name="nofollow",action="store_true",default=False),
            dict(name="candidates",type=_parse_candidates,default=[])])
    def artifact_create(self,path,nofetch=False,noremove=False,
                        nofollow=False,candidates=[]):
        """
        Create an artifact from a JSON document.

        :param path: a pathname pointing to a json artifact blob; use '-' for stdin
        :param importer: the name of a specific importer to use; or the empty string for automatic selection
        :param sessionid: an explicit import sessionid to begin or resume from
        :param nofetch: do not download artifact files
        :param noremove: do not remove downloaded artifact files
        :param nofollow: do not automatically follow suggested artifacts
        :param candidates: a semicolon-separated list of relation,url tuples that specifies a URL that is related to the main artifact
        """
        content = ""
        files = (path,)
        with fileinput.input(files=files) as f:
            for line in f:
                content += line
        artifact = object_from_json(
            self.session,Artifact,json.loads(content))
        artifact.ctime = datetime.datetime.now()
        artifact.owner = self.get_user()
        self.session.add(artifact)
        self.logger.debug("created, starting post import: %r",artifact)
        self.artifact_import_post(artifact,fetch=not nofetch,remove=not noremove)
        self.logger.debug("post import: %r",artifact)
        self.session.commit()
        self.session.refresh(artifact)
        return artifact

    @ApplicableMethod(
        alias="artifact.list",
        kwargs=[dict(name="curated",action="store_true",default=False),
                dict(name="published",action="store_true",default=False)])
    def artifact_list(self,id=None,url=None,owner=None,curated=None,published=None):
        """
        List artifacts matching filter parameters.

        :param id: artifact id
        :param url: artifact URL
        :param owner: artifact owner
        :param curated: only show artifacts that have been curated
        :param published: only show artifacts that have been published
        """
        return self.session.query(Artifact).\
          join(User, Artifact.owner_id==User.id).\
          filter(Artifact.id == int(id) if id is not None else True).\
          filter(Artifact.url == url if url is not None else True).\
          filter(User.email == owner if owner is not None else True).\
          filter(Artifact.curations != None if curated else True).\
          filter(Artifact.publication != None if published else True).\
          all()

    @ApplicableMethod(alias="artifact.show",
                      formatter=pretty_print_record)
    def artifact_get(self,id):
        """
        Returns an artifact.

        :param id: artifact id
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        return artifact

    @ApplicableMethod(alias="artifact.delete")
    def artifact_delete(self,id):
        """
        Delete an artifact.

        :param id: artifact id
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == int(id)).first()
        if artifact:
            self.session.delete(artifact)
            self.session.commit()
            return
        else:
            raise ObjectNotFoundError("artifact",id=id)

    @ApplicableMethod(alias="artifact.modify")
    def artifact_modify(self,id,typ=None,title=None,name=None,description=None,
                        license_short_name=None):
        """
        Modify an artifact.

        :param id: artifact id
        :param typ: artifact type (cannot be "")
        :param title: artifact title (cannot be "")
        :param name: artifact name (set to "" to clear)
        :param description: artifact description (set to "" to clear)
        :param license_short_name: set a new license that references an existing license short name
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        if artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        if title == "":
            raise MalformedArgumentsError("artifact title cannot be null")
        if not title and description == None and license_short_name == None \
          and typ == None and name == None:
            raise MalformedArgumentsError("must supply at least one field to modify")
        curations = []
        if typ and artifact.type != typ:
            artifact.type = typ
            curations.append(ArtifactCuration(
                artifact_id=artifact.id,time=datetime.datetime.now(),
                opdata=json.dumps(
                    [ { "obj":"artifact","op":"set",
                        "data":{ "field":"type","type":typ } } ],
                    separators=(',',':')),
                curator=self.get_user()))
        if title and artifact.title != title:
            artifact.title = title
            curations.append(ArtifactCuration(
                artifact_id=artifact.id,time=datetime.datetime.now(),
                opdata=json.dumps(
                    [ { "obj":"artifact","op":"set",
                        "data":{ "field":"title","title":title } } ],
                    separators=(',',':')),
                curator=self.get_user()))
        if name != None and artifact.name != name:
            artifact.name = name
            curations.append(ArtifactCuration(
                artifact_id=artifact.id,time=datetime.datetime.now(),
                opdata=json.dumps(
                    [ { "obj":"artifact","op":"set",
                        "data":{ "field":"name","name":name } } ],
                    separators=(',',':')),
                curator=self.get_user()))
        if description != None and artifact.description != description:
            artifact.description = description
            curations.append(ArtifactCuration(
                artifact_id=artifact.id,time=datetime.datetime.now(),
                opdata=json.dumps(
                    [ { "obj":"artifact","op":"set",
                        "data":{ "field":"description","description":description } } ],
                    separators=(',',':')),
                curator=self.get_user()))
        if license_short_name != None:
            if license_short_name:
                license_obj = self.session.query(License).\
                  filter(License.short_name == license_short_name).first()
                if not license_obj:
                    raise ObjectNotFoundError("license",short_name=license_short_name)
                artifact.license_id = license_obj.id
                curations.append(ArtifactCuration(
                    artifact_id=artifact.id,time=datetime.datetime.now(),
                    opdata=json.dumps(
                        [ { "obj":"artifact","op":"set",
                            "data":{ "field":"license","short_name":license_short_name } } ],
                        separators=(',',':')),
                    curator=self.get_user()))
            else:
                artifact.license_id = None
                curations.append(ArtifactCuration(
                    artifact_id=artifact.id,time=datetime.datetime.now(),
                    opdata=json.dumps(
                        [ { "obj":"artifact","op":"clear",
                            "data":{ "field":"license" } } ],
                        separators=(',',':')),
                    curator=self.get_user()))
        self.session.add(artifact)
        self.session.add_all(curations)
        self.session.commit()
        return curations

    @ApplicableMethod(alias="tag.add")
    def tag_add(self,id,tag):
        """
        Add a tag to an unpublished artifact (adds a new curation).

        :param id: artifact id
        :param tag: tag name
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        elif artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        owner = self.get_user()
        t = ArtifactTag(artifact_id=artifact.id,tag=tag)
        opdata = [ { "obj":"tag","op":"add","data":{ "tag":tag } } ]
        opdata_str = json.dumps(opdata,separators=(',',':'))
        curation = ArtifactCuration(
            artifact_id=artifact.id,time=datetime.datetime.now(),
            opdata=opdata_str,curator=owner)
        self.session.add_all([t,curation])
        self.session.commit()
        return curation

    @ApplicableMethod(alias="tag.delete")
    def tag_delete(self,id,tag):
        """
        Deletes a tag from an unpublished artifact (adds a new curation).

        :param id: artifact id
        :param tag: tag name
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        elif artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        owner = self.get_user()
        t = self.session.query(ArtifactTag).\
          filter(ArtifactTag.artifact_id == id).\
          filter(ArtifactTag.tag == tag).\
          first()
        if not t:
            raise ObjectNotFoundError("tag",artifact_id=id,tag=tag)
        opdata = [ { "obj":"tag","op":"delete","data":{ "tag":tag } } ]
        opdata_str = json.dumps(opdata,separators=(',',':'))
        curation = ArtifactCuration(
            artifact_id=artifact.id,time=datetime.datetime.now(),
            opdata=opdata_str,curator=owner)
        self.session.delete(t)
        self.session.add(curation)
        self.session.commit()
        return curation

    @ApplicableMethod(alias="metadata.add")
    def metadata_add(self,id,name,value,type=None,source=None):
        """
        Add a metadata pair to an unpublished artifact (adds a new curation).

        :param id: artifact id
        :param name: metadata name
        :param value: metadata value
        :param type: metadata type
        :param source: metadata source
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        elif artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        owner = self.get_user()
        meta = ArtifactMetadata(artifact_id=artifact.id,name=name,value=value)
        mdd = { "name":name,"value":value }
        if type:
            mdd["type"] = type
        if source:
            mdd["source"] = source
        else:
            mdd["source"] = "manual"
        opdata = [ { "obj":"meta","op":"add","data":mdd } ]
        opdata_str = json.dumps(opdata,separators=(',',':'))
        curation = ArtifactCuration(
            artifact_id=artifact.id,time=datetime.datetime.now(),
            opdata=opdata_str,curator=owner)
        self.session.add_all([meta,curation])
        self.session.commit()
        return curation

    @ApplicableMethod(alias="metadata.delete")
    def metadata_delete(self,id,name):
        """
        Deletes a metadata pair from an unpublished artifact (adds a new curation).

        :param id: artifact id
        :param name: metadata name
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        elif artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        owner = self.get_user()
        meta = self.session.query(ArtifactMetadata).\
          filter(ArtifactMetadata.artifact_id == id).\
          filter(ArtifactMetadata.name == name).\
          first()
        if not meta:
            raise ObjectNotFoundError("metadata",artifact_id=id,name=name)
        opdata = [ { "obj":"meta","op":"delete","data":{ "name":name } } ]
        opdata_str = json.dumps(opdata,separators=(',',':'))
        curation = ArtifactCuration(
            artifact_id=artifact.id,time=datetime.datetime.now(),
            opdata=opdata_str,curator=owner)
        self.session.delete(meta)
        self.session.add(curation)
        self.session.commit()
        return curation

    @ApplicableMethod(
        alias="relationship.add",
        largs=[
            dict(name="id"),
            dict(name="relation",
                 help="One of " + ",".join(ArtifactRelationship.relation.property.columns[0].type._enums_argument)),
            dict(name="related_id")])
    def relationship_add(self,id,relation,related_id):
        """
        Add a relationship from id to related_id.

        :param id: artifact id
        :param relation: a relationship between artifacts
        :param related_id: the related artifact id
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        related_artifact = self.session.query(Artifact).filter(Artifact.id == related_id).first()
        if not related_artifact:
            raise ObjectNotFoundError("artifact",related_id=related_id)
        if artifact.publication:
            raise AlreadyPublishedError(id,"cannot modify")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        if relation not in ArtifactRelationship.relation.property.columns[0].type._enums_argument:
            raise MalformedArgumentsError("invalid relation %r" % (relation))
        if self.session.query(ArtifactRelationship).\
          filter(ArtifactRelationship.artifact_id == id).\
          filter(ArtifactRelationship.relation == relation).\
          filter(ArtifactRelationship.related_artifact_id == related_id).all():
            raise ObjectExistsError("relation %r from %r to %r already exists" % (
                relation,id,related_id))
        owner = self.get_user()
        relationship = ArtifactRelationship(
            artifact_id=artifact.id,relation=relation,
            related_artifact_id=related_artifact.id)
        opdata = [ { "obj":"relationship","op":"add",
                     "data":{ "artifact_id":artifact.id,"relation":relation,
                              "related_artifact_id":related_artifact.id } } ]
        opdata_str = json.dumps(opdata,separators=(',',':'))
        curation = ArtifactCuration(
            artifact_id=artifact.id,time=datetime.datetime.now(),
            opdata=opdata_str,curator=owner)
        self.session.add_all([relationship,curation])
        self.session.commit()
        return [relationship,curation]

    @ApplicableMethod(alias="artifact.publish")
    def artifact_publish(self,id):
        """
        Publish an artifact.

        :param id: artifact id
        """
        artifact = self.session.query(Artifact).filter(Artifact.id == id).first()
        if not artifact:
            raise ObjectNotFoundError("artifact",id=id)
        elif artifact.publication:
            raise AlreadyPublishedError(id,"cannot re-publish")
        exported = self.session.query(ExportedObject).\
          filter(ExportedObject.object_type == "artifact").\
          filter(ExportedObject.object_id == id).all()
        if exported:
            raise AlreadyExportedError("artifact",id=id)
        publisher = self.get_user()
        artifact.publication = ArtifactPublication(
            time=datetime.datetime.now(),publisher=publisher)
        self.session.add(artifact.publication)
        self.session.commit()
        return artifact.publication

    @ApplicableMethod(
        alias="artifact.export",
        kwargs=[dict(name="all",action="store_true",default=False)])
    def artifact_export(self,id=None,all=False,exporter="json"):
        """
        Export an artifact.

        :param id: artifact id
        :param all: if set, export all unexported artifacts
        :param exporter: the name of a specific exporter to use
        """
        artifacts = []
        if id:
            artifacts = [self.session.query(Artifact).filter(Artifact.id == id).first()]
        elif all:
            artifacts = self.session.query(Artifact).\
              join(ExportedObject, sqlalchemy.and_(ExportedObject.object_id == Artifact.id,ExportedObject.object_type == "artifact"), isouter=True).\
              filter(ExportedObject.id == None).\
              all()
        else:
            self.logger.error("must supply either a specific id or --all to export")
        if not artifacts:
            if id:
                raise ObjectNotFoundError("artifact",id=id)
            else:
                self.logger.warning("no artifacts to export")
                return
        exporter = get_exporter(exporter,self.config,self.session)
        if exporter.external:
            # If this artifact is to be exported outside our system, we want to
            # see if that's already been done to avoid a duplicate.  We also
            # want to check to ensure that any references to other artifacts
            # (currently only via relationships) are to artifacts that have
            # also been published to the same export destination.
            for artifact in artifacts:
                exported = self.session.query(ExportedObject).\
                  filter(ExportedObject.object_type == "artifact").\
                  filter(ExportedObject.object_id == id).\
                  filter(ExportedObject.exporter_id == exporter.exporter_obj.id).all()
                if exported:
                    raise AlreadyExportedError("artifact",id=id)
        exports = []
        for artifact in artifacts:
            self.logger.debug("exporting: %r",artifact)
            res = exporter.export_artifact(artifact)
            if isinstance(res,ExportedObject):
                res.exporter = exporter.exporter_obj
                self.session.add(res)
                self.session.commit()
                exports.append(res)
            elif res:
                exports.append(res)
            else:
                self.logger.error("failed to export %r (%r)",artifact,res)
        if all:
            return exports
        else:
            return exports[0]

    @ApplicableMethod(alias="export.list")
    def export_list(self):
        """
        List exported objects.
        """
        return self.session.query(ExportedObject).all()

    @ApplicableMethod(
        alias="candidate.list",
        kwargs=[dict(name="imported",action="store_true",default=False)])
    def candidate_list(self,id=None,url=None,owner=None,imported=None):
        """
        Returns a list of candidate artifacts matching filter parameters.

        :param id: candidate artifact id
        :param url: candidate artifact URL
        :param owner: candidate artifact owner
        :param imported: only show candidate artifacts that have been imported
        """
        return self.session.query(CandidateArtifact).\
          join(User, CandidateArtifact.owner_id==User.id).\
          filter(CandidateArtifact.id == int(id) if id is not None else True).\
          filter(CandidateArtifact.url == url if url is not None else True).\
          filter(User.email == owner if owner is not None else True).\
          filter(CandidateArtifact.imported_artifact != None if imported else True).\
          all()

    @ApplicableMethod(alias="candidate.show",
                      formatter=pretty_print_record)
    def candidate_get(self,id):
        """
        Returns a candidate artifact.

        :param id: candidate artifact id
        """
        candidate = self.session.query(CandidateArtifact).\
          filter(CandidateArtifact.id == id).first()
        if not candidate:
            raise ObjectNotFoundError("candidate artifact",id=id)
        return candidate

    @ApplicableMethod(
        alias="candidate.import",formatter=pretty_print_record,
        kwargs=[dict(name="nofetch",action="store_true",default=False),
                dict(name="noremove",action="store_true",default=False),
                dict(name="nofollow",action="store_true",default=False)])
    def candidate_import(self,id,importer="",sessionid=None,
                         nofetch=False,noremove=False,nofollow=False):
        """
        Import a candidate artifact that hasn't already been imported.

        :param id: candidate artifact id
        :param importer: the name of a specific importer to use; or the empty string for automatic selection
        :param sessionid: an explicit import sessionid to begin or resume from
        :param nofetch: do not download artifact files
        :param noremove: do not remove downloaded artifact files
        :param nofollow: do not automatically follow suggested artifacts
        """
        candidate = self.session.query(CandidateArtifact).\
          filter(CandidateArtifact.id == id).first()
        if not candidate:
            raise ObjectNotFoundError("candidate artifact",id=id)
        if candidate.imported_artifact:
            raise AlreadyImportedError("candidate artifact",id=id)
        return self.artifact_import_all(
            candidate,fetch=not nofetch,remove=not noremove,follow=not nofollow)
