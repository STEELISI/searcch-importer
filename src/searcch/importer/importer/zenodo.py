
import sys
import six
import logging
import time
import dateutil.parser
import datetime
from future.utils import raise_from
from urllib.parse import urlparse
import requests

from searcch.importer.exceptions import (
    ConfigError,ImporterError,HttpError )
from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,
    Importer,License,Person,ArtifactAffiliation,Affiliation,
    Organization,ArtifactFunding,PersonMetadata,ArtifactTag,
    ARTIFACT_TYPES )
from searcch.importer.db.model.license import recognize_license

LOG = logging.getLogger(__name__)

class ZenodoResource(object):

    def __init__(self,api,json):
        self._api = api
        self._json = json

class ZenodoDeposition(ZenodoResource):
    pass

class ZenodoDepositionFile(ZenodoResource):
    pass

class ZenodoRecord(ZenodoResource):
    pass

class ZenodoLicense(ZenodoResource):
    pass

class ZenodoError(ImporterError):
    pass

class MalformedZenodoRecordError(ZenodoError):

    def __init__(self,message,record=None):
        super(ZenodoApiError,self).__init__(message)
        self.record = record
        if record:
            self.message = message + "(record %r)" % (record,)
        else:
            self.message = message

    def __repr__(self):
        return "<MalformedZenodoRecordError('{message}',{record}>".format(
            message=self.message,record=self.record)

class ZenodoApiError(ZenodoError):

    def __init__(self,message,status,errors={}):
        super(ZenodoApiError,self).__init__(message,status,errors)
        self.message = message
        self.status = status
        self.errors = errors

    def __repr__(self):
        return "<ZenodoApiError('{message}',{code}>".format(
            message=message,code=code)

class ZenodoApi(object):
    """A class providing access to the Zenodo API."""

    APIROOT = "https://zenodo.org/api/"

    def __init__(self,token,apiroot=APIROOT,verify=True):
        self._token = token
        self._apiroot = apiroot
        self._verify = verify
        self._session = requests.Session()

    def _send(self,req,stream=False,timeout=None):
        req = self._session.prepare_request(req)
        return self._session.send(req,verify=self._verify,
                                  stream=stream,timeout=timeout)

    def _request(self,method,suburl,headers={},params={},data=None,
                 stream=False,timeout=None):
        url = self._apiroot + suburl
        LOG.debug("%s %s: headers=%s" % (method.upper(),url,str(headers)))
        new_headers = dict(**headers)
        new_headers["Authorization"] = "Bearer " + self._token
        if method in [ "POST","PUT" ] and not "Content-Type" in new_headers:
            new_headers["Content-Type"] = "application/json"
        req = requests.Request(method,url,data=data,headers=headers,
                               params=params)
        resp = self._send(req,stream=stream,timeout=timeout)
        if resp.status_code not in [ 200,201,202,204 ]:
            j = resp.json()
            raise ZenodoApiError(j["message"],j["status"],getattr(j,"errors",None))
        return resp

    def get(self,suburl,**kwargs):
        return self._request("get",suburl,**kwargs)

    def head(self,suburl,**kwargs):
        return self._request("head",suburl,**kwargs)

    def put(self,suburl,**kwargs):
        return self._request("put",suburl,**kwargs)

    def post(self,suburl,**kwargs):
        return self._request("post",suburl,**kwargs)

    def delete(self,suburl,**kwargs):
        return self._request("delete",suburl,**kwargs)

    def ping(self):
        resp = self.get("/deposit/depositions")
        if resp.status_code in [200,401]:
            return True
        else:
            return False

    def get_record(self,id,raw=False):
        j = self.get("/records/%s" % (str(id),)).json()
        if raw:
            return j
        else:
            return ZenodoRecord(self,j)

    def get_license(self,id,raw=False):
        j = self.get("/licenses/%s" % (str(id),)).json()
        if raw:
            return j
        else:
            return ZenodoLicense(self,j)

class ZenodoImporter(BaseImporter):
    """Provides a Zenodo Importer."""

    name = "zenodo"
    version = "0.1"

    def __init__(self,config,session):
        super(ZenodoImporter,self).__init__(config,session)
        if not self.config["zenodo"]["token"]:
            raise ConfigError("zenodo importer requires a token, and zenodo.token must be set to that token")
        self.api = ZenodoApi(self.config["zenodo"]["token"])

    def _extract_record_id(self,url):
        ret = urlparse(url)
        if (ret.netloc.find("zenodo.org:") > -1 \
            or ret.netloc.endswith("zenodo.org")) \
          and ret.path.startswith("/record/"):
            return ret.path.split("/")[-1]
        elif ret.netloc.endswith("doi.org") \
          and (ret.path.startswith("10.5281/zenodo.")
               or ret.path.startswith("/10.5281/zenodo.")):
            return ret.path.split(".")[-1]
        else:
            return False

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a Zenodo URL or Zenodo DOI."""
        try:
            ret = urlparse(url)
            if ret.netloc.find("zenodo.org:") > -1 \
              or ret.netloc.endswith("zenodo.org"):
                return True
            elif ret.netloc.endswith("doi.org") \
              and (ret.path.startswith("10.5281/zenodo.")
                   or ret.path.startswith("/10.5281/zenodo.")):
                return True
        except BaseException:
            pass
        return False

    def _parse_time(self,timestr):
        return dateutil.parser.parse(timestr)

    def _map_type(self,ztype):
        if ztype == "software":
            return "software"
        elif ztype not in ARTIFACT_TYPES:
            return "other"
        return ztype

    def import_artifact(self,candidate):
        """Imports an artifact from Zenodo and returns an Artifact, or throws an error."""
        url = candidate.url
        record_id = self._extract_record_id(url)
        LOG.debug("importing '%s' from zenodo via record_id %s" % (url,str(record_id)))
        try:
            rj = self.api.get_record(record_id,raw=True)
        except ZenodoError:
            ex = sys.exc_info()[1]
            raise_from(HttpError(ex.status,ex.message),ex)

        if not "metadata" in rj:
            raise MalformedZenodoRecordError("no metadata",record=record_id)

        ztype = "other"
        if "resource_type" in rj["metadata"] and "type" in rj["metadata"]["resource_type"]:
            ztype = self._map_type(rj["metadata"]["resource_type"]["type"])
        else:
            LOG.warn("missing resource_type.type in zenodo metadata")
        title = rj["metadata"].get("title")
        description = rj["metadata"].get("description")
        metadata = list()
        tags = list()
        if "created" in rj:
            ts = dateutil.parser.parse(rj["created"]).isoformat()
            metadata.append(ArtifactMetadata(name="ctime",value=ts))
        if "updated" in rj:
            ts = dateutil.parser.parse(rj["updated"]).isoformat()
            metadata.append(ArtifactMetadata(name="mtime",value=ts))
        if "keywords" in rj["metadata"]:
            for kw in rj["metadata"]["keywords"]:
                tags.append(ArtifactTag(tag=kw,source="zenodo"))
        if "language" in rj["metadata"]:
            metadata.append(ArtifactMetadata(
                name="language",value=rj["metadata"]["language"],source="zenodo"))

        metadata_imports = [
            "publication_type","publication_date","revision"
        ]
        for mi in metadata_imports:
            if mi in rj["metadata"]:
                metadata.append(ArtifactMetadata(
                    name=mi,value=rj["metadata"][mi],source="zenodo"))

        affiliations = []
        org_map = dict()
        if "creators" in rj["metadata"]:
            for cr in rj["metadata"]["creators"]:
                if not "name" in cr:
                    continue
                name = cr["name"]
                if name.find(",") > 0:
                    name = " ".join(map(lambda x: x.strip(),reversed(name.split(",",1))))
                organization = None
                if "affiliation" in cr:
                    if cr["affiliation"] in org_map:
                        organization = org_map[cr["affiliation"]]
                    else:
                        organization = Organization(
                            name=cr["affiliation"],type="Institution")
                        org_map[cr["affiliation"]] = organization
                person = Person(name=name)
                if "orcid" in cr:
                    person.meta = [ PersonMetadata(
                        name="orcid",value=cr["orcid"],source="zenodo") ]
                affiliation = Affiliation(
                    person=person,org=organization)
                affiliations.append(ArtifactAffiliation(affiliation=affiliation,roles="Author"))

        files = []
        if "files" in rj and rj["files"]:
            for f in rj["files"]:
                if "key" not in f \
                  or "links" not in f \
                  or "self" not in f["links"]:
                    continue
                files.append(ArtifactFile(
                    url=f["links"]["self"],
                    name=f["key"],
                    filetype=f.get("type"),
                    size=f.get("size")))

        fundings = []
        if "grants" in rj["metadata"] and rj["metadata"]["grants"]:
            for g in rj["metadata"]["grants"]:
                if "code" not in g \
                  or "funder" not in g \
                  or "name" not in g["funder"]:
                    continue
                grant_url = None
                if "links" in g and "self" in g["links"]:
                    grant_url = g["links"]["self"]
                org = Organization(
                    name=g["funder"]["name"],type="Sponsor")
                fundings.append(ArtifactFunding(
                    grant_number=str(g["code"]),grant_url=grant_url,
                    grant_title=g.get("title"),organization=org))

        license = None
        if "license" in rj["metadata"]:
            try:
                lj = self.api.get_license(rj["metadata"]["license"]["id"],raw=True)
                LOG.debug("zenodo license: %r",lj)
                short_name = lj["id"]
                long_name = lj["metadata"]["title"]
                license_url = lj["metadata"]["url"]
                if short_name:
                    license = self._session.query(License).\
                      filter(License.short_name == short_name).\
                      first()
                if not license and long_name:
                    license = self._session.query(License).\
                      filter(License.long_name == long_name).\
                      first()
                if not license:
                    license = License(short_name=short_name,
                                      long_name=long_name,url=license_url)
            except:
                LOG.exception("license")

        return Artifact(
            type=ztype,url=url,ext_id=str(record_id),
            title=title,description=description,license=license,
            ctime=datetime.datetime.now(),
            owner=self.owner_object,importer=self.importer_object,
            affiliations=affiliations,files=files,fundings=fundings,
            tags=tags,meta=metadata)
