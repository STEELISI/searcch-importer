
import six
from future.utils import iteritems
import abc
import os
import os.path
import shutil
import sys
import logging

from searcch.importer.db.model import (
    Importer,Person,User,License)
from searcch.importer.util.retrieve import Retriever
from searcch.importer.extractor import get_extractors
from searcch.importer.util import bytes2str
import searcch.importer.importer.config

LOG = logging.getLogger(__name__)

@six.add_metaclass(abc.ABCMeta)
class BaseImporter(object):
    """An abstract base class that any Importer must subclass."""
    name = None
    version = None

    def __init__(self,config,session):
        self._config = config
        self._session = session

    @property
    def importer_object(self):
        imp = self._session.query(Importer).\
            filter(Importer.name == self.__class__.name).\
            filter(Importer.version == self.__class__.version).\
            first()
        if not imp:
            imp = Importer(name=self.__class__.name,
                           version=self.__class__.version)
        return imp

    @property
    def owner_object(self):
        person = self._session.query(Person).\
            filter(Person.name == self.config["DEFAULT"]["user_name"]).\
            filter(Person.email == self.config["DEFAULT"]["user_email"]).\
            first()
        if not person:
            person = Person(email=self.config["DEFAULT"]["user_email"],
                            name=self.config["DEFAULT"]["user_name"])
            owner = User(person=person)
        else:
            owner = self._session.query(User).\
                filter(User.person == person).\
                first()
            if not owner:
                owner = User(person=person)
        return owner

    def get_license_object(self,short_name):
        license = self._session.query(License).\
            filter(License.short_name == short_name).\
            first()
        if not license:
            license = License(short_name=short_name)
        return license

    @property
    def config(self):
        return self._config

    @property
    def session(self):
        return self._session

    @abc.abstractclassmethod
    def can_import(cls,url):
        """Checks to see if this URL can be imported by this Importer."""

    @abc.abstractmethod
    def import_artifact(self,candidate):
        """Imports an artifact from the given CandidateArtifact and returns an Artifact."""

__importers__ = dict()

def load_importers():
    global __importers__

    if __importers__:
        return

    from .github import GithubImporter
    from .zenodo import ZenodoImporter
    from .acm_dl import AcmDigitalLibraryImporter
    from .ieeexplore import IeeeXploreImporter
    from .usenix import USENIXImporter
    from .gitrepo import GitRepoImporter
    from .arxiv import ArxivImporter
    from .paperswithcode import PapersWithCodeImporter
    from .ndss import NDSSImporter
    from .acsac import ACSACImporter

    __importers__[GithubImporter.name] = GithubImporter
    __importers__[ZenodoImporter.name] = ZenodoImporter
    __importers__[AcmDigitalLibraryImporter.name] = AcmDigitalLibraryImporter
    __importers__[IeeeXploreImporter.name] = IeeeXploreImporter
    __importers__[USENIXImporter.name] = USENIXImporter
    __importers__[NDSSImporter.name] = NDSSImporter
    __importers__[ACSACImporter.name] = ACSACImporter
    __importers__[PapersWithCodeImporter.name] = PapersWithCodeImporter
    __importers__[ArxivImporter.name] = ArxivImporter
    __importers__[GitRepoImporter.name] = GitRepoImporter

    return

def get_importer_names():
    load_importers()
    return __importers__.keys()

def validate_url(url,retries=0,interval=None):
    import requests
    errors = []
    while retries >= 0:
        retries -= 1
        try:
            requests.head(url)
        except requests.exceptions.RequestException:
            if retries < 0:
                six.reraise(*sys.exc_info())
        except:
            LOG.exception(sys.exc_info()[1])
            if retries < 0:
                six.reraise(*sys.exc_info())

def get_importer(url,config,session,name=None,retries=0,interval=None):
    load_importers()
    validate_url(url,retries=retries,interval=interval)
    if name:
        if not name in __importers__:
            raise NotImplementedError("no such importer %r" % (name,))
        return __importers__[name]()
    else:
        for name in __importers__:
            try:
                cls = __importers__[name]
                i = cls(config,session)
                if i.can_import(url):
                    return i
            except Exception:
                LOG.debug("unexpected error in %s.can_import:",
                          name,exc_info=sys.exc_info())
        return None

class ImportSession(object):
    """A helper class that contains and manages state (e.g. temporary filesystem content) accumulated during an import session -- retrieval, unpacking, extraction(s)."""

    def __init__(self,config,session,artifact,sessionid=None):
        self._config = config
        self._session = session
        self._artifact = artifact
        self._retrieved_files = []
        self._sessionid_journal_path = os.path.join(
            config["DEFAULT"]["tmpdir"],".last_sessionid")
        self._sessionid = sessionid or self._get_next_sessionid()
        self._session_destdir = os.path.join(
            config["DEFAULT"]["tmpdir"],str(self._sessionid))
        self._artifact_destdir = os.path.join(
            config["DEFAULT"]["tmpdir"],str(self._sessionid))
        self._general_text = ""
        self._general_text_source_map = dict()
        if self.artifact.title:
            self.add_general_text(self.artifact.title,artifact_field="title")
        if self.artifact.description:
            self.add_general_text(self.artifact.description,artifact_field="description")

    def _get_next_sessionid(self):
        n = 0
        if os.path.exists(self._sessionid_journal_path):
            f = open(self._sessionid_journal_path,'r')
            try:
                n = int(f.read()) + 1
            except:
                pass
            f.close()
        sd = os.path.join(self.config["DEFAULT"]["tmpdir"],str(n))
        while os.path.exists(sd):
            n += 1
            sd = os.path.join(self.config["DEFAULT"]["tmpdir"],str(n))
        os.makedirs(sd)
        f = open(self._sessionid_journal_path,'w')
        f.write(str(n))
        f.close()
        return n

    @property
    def id(self):
        return self._sessionid

    @property
    def config(self):
        return self._config

    @property
    def session(self):
        return self._session

    @property
    def artifact(self):
        return self._artifact

    @property
    def retrieved_files(self):
        return self._retrieved_files

    @property
    def general_text(self):
        """
        A collection of all general descriptive text from the Artifact (e.g., Artifact.description, Artifact.title, or a README.md ArtifactFileMember).
        """
        return self._general_text

    def general_text_indexed(self,artifact_field=None,artifact_file=None,
                             artifact_file_member=None):
        st = (artifact_field,artifact_file,artifact_file_member)
        if st in self._general_text_source_map:
            return True
        return False

    def add_general_text(self,text,artifact_field=None,artifact_file=None,
                         artifact_file_member=None):
        st = (artifact_field,artifact_file,artifact_file_member)
        if st in self._general_text_source_map:
            return False
        self._general_text_source_map[st] = text
        self._general_text += "\n\n" + text
        return True

    def add_general_text_from_file(self,retrieved_artifact_file,artifact_file_member):
        st = (None,retrieved_artifact_file.artifact_file,artifact_file_member)
        if st in self._general_text_source_map:
            return False
        text = None
        path = None
        if artifact_file_member:
            file_content = artifact_file_member.file_content
            if file_content and file_content.content:
                text = file_content.content.decode()
            path = os.path.join(retrieved_artifact_file.path,artifact_file_member.pathname)
        else:
            if retrieved_artifact_file.artifact_file.file_content \
              and retrieved_artifact_file.artifact_file.file_content.content:
                text = retrieved_artifact_file.artifact_file.file_content.content.decode()
            if os.path.isfile(retrieved_artifact_file.path):
                path = retrieved_artifact_file.path
        if not text and path:
            f = open(path,"rb")
            text = bytes2str(f.read())
            f.close()
        if not text:
            return False
        self._general_text_source_map[st] = text
        self._general_text += "\n\n" + text
        return True

    def retrieve_all(self):
        r = Retriever(self.config)
        i = 0
        for af in self.artifact.files:
            destdir = os.path.join(self._artifact_destdir,str(i))
            rf = r.retrieve(af,self.artifact,destdir=destdir)
            if rf:
                self._retrieved_files.append(rf)
                LOG.debug("retrieved file: %r" % (rf,))
            i += 1

    def extract_all(self,skip=[]):
        """Runs all extractors (except those identified in the `skip` arg) across the artifact and its content."""
        for ext in get_extractors(self.config,self):
            if skip and ext.name in skip:
                continue
            ext.extract()

    def remove_retrieved_files(self):
        """Removes all temporary filesystem content for each retrieved file."""
        for rf in self.retrieved_files:
            #os.removedirs(rf.destdir)
            if os.path.exists(rf.destdir):
                shutil.rmtree(rf.destdir)

    def remove_all(self):
        """Removes all temporary filesystem content."""
        self.remove_retrieved_files()
        #os.removedirs(self._artifact_destdir)
        if os.path.exists(self._artifact_destdir):
            shutil.rmtree(self._artifact_destdir)
        if os.path.exists(self._session_destdir):
            shutil.rmtree(self._session_destdir)

    def finalize(self):
        """Automatically fills in as many unset fields in the main Artifact object as possible, as necessary to be in compliance with the schema; although there are no good choices."""
        if not self.artifact.title:
            if self.artifact.name:
                self.artifact.title = self.artifact.name
            else:
                self.artifact.title = self.artifact.url

    def __repr__(self):
        return "<ImportSession(id=%r,artifact=%r)>" % (
            self.id,self.artifact)
