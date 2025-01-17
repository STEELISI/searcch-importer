
import six
from future.utils import iteritems
import abc
import logging
import os.path

from searcch.importer.db.model import (
    Extractor, License)
from searcch.importer.util.pdf import pdf_file_to_text

LOG = logging.getLogger(__name__)

@six.add_metaclass(abc.ABCMeta)
class BaseExtractor(object):
    """An abstract base class that any Extractor must subclass."""
    name = None
    version = None

    def __init__(self,config,session,**kwargs):
        self._config = config
        self._session = session

    @property
    def config(self):
        return self._config

    @property
    def session(self):
        return self._session

    @abc.abstractmethod
    def extract(self):
        """Extracts all possible metadata from an artifact import session; return value ignored."""

    def get_license_object(self,short_name):
        license = self.session.session.query(License).\
            filter(License.short_name == short_name).\
            first()
        if not license:
            license = License(short_name=short_name)
        return license

@six.add_metaclass(abc.ABCMeta)
class BaseKeywordExtractor(BaseExtractor):

    @abc.abstractmethod
    def extract_keywords(self,text,source=None):
        """Extracts keywords from the text supplied by source."""

    def extract(self):
        """Extracts keywords from retrieved ArtifactFiles with mime type application/pdf or text and saves the top N as ArtifactMetadata."""

        LOG.debug("extracting keywords (%r) in %r",
                  getattr(self.__class__,"name",None),self.session.artifact)

        self.extract_keywords(self.session.general_text,source="general text")

        for rf in self.session.retrieved_files:
            if os.path.isfile(rf.path):
                if self.session.general_text_indexed(artifact_file=rf.artifact_file):
                    continue
                text = None
                if rf.mime_type in ("application/pdf","pdf"):
                    text = pdf_file_to_text(rf.path)
                elif rf.mime_type in ("text","txt","application/text","",None):
                    with open(rf.path,"rb") as f:
                        text = f.read().decode()
                else:
                    continue
                if text:
                    self.extract_keywords(text,source=rf)
            elif os.path.isdir(rf.path) and rf.artifact_file.members:
                for rfm in rf.artifact_file.members:
                    if rfm.pathname.startswith("LICENSE") or rfm.pathname.startswith("COPYING"):
                        continue
                    if self.session.general_text_indexed(
                      artifact_file=rf.artifact_file,artifact_file_member=rfm):
                        continue
                    text = None
                    path = os.path.join(rf.path,rfm.pathname)
                    if rfm.filetype in ("application/pdf","pdf"):
                        text = pdf_file_to_text(path)
                    elif rfm.filetype in ("text","txt","application/text","",None):
                        with open(path,"rb") as f:
                            text = f.read().decode()
                    else:
                        continue
                    if text:
                        self.extract_keywords(text,source=rfm)

__extractors__ = dict()

def load_extractors():
    global __extractors__

    if __extractors__:
        return

    from .basic import BasicFileExtractor
    from .git import GitExtractor
    from .top_keywords import TopKeywordsExtractor
    from .yake_ngram_keywords import YakeNGramKeywordsExtractor
    from .semantic_scholar import SemanticScholarExtractor
    from .markdown_extractor import MarkdownExtractor
    from .pke_keywords import PKEExtractor
    from .license import LicenseExtractor

    __extractors__[BasicFileExtractor.name] = BasicFileExtractor
    __extractors__[GitExtractor.name] = GitExtractor
    __extractors__[MarkdownExtractor.name] = MarkdownExtractor
    __extractors__[LicenseExtractor.name] = LicenseExtractor
    __extractors__[SemanticScholarExtractor.name] = SemanticScholarExtractor
    __extractors__[TopKeywordsExtractor.name] = TopKeywordsExtractor
    __extractors__[YakeNGramKeywordsExtractor.name] = YakeNGramKeywordsExtractor
    __extractors__[PKEExtractor.name] = PKEExtractor

    return

def get_extractor_names():
    load_extractors()
    return __extractors__.keys()

def get_extractors(config,session,**kwargs):
    load_extractors()
    return [cls(config,session,**kwargs) for cls in __extractors__.values()]

def get_extractor(name,config,session,**kwargs):
    load_extractors()
    if name:
        if not name in __extractors__:
            raise NotImplementedError("no such extractor '%s'" % (str(name),))
        return __extractors__[name]()
    else:
        for name in __extractors__:
            try:
                cls = __extractors__[name]
                return cls(config,session)
            except Exception:
                pass
        return None
