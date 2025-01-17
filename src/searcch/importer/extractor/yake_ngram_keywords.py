
import six
import logging
import sys
import os.path
import os
import requests
import json

import yake

from searcch.importer.extractor import BaseKeywordExtractor
from searcch.importer.db.model import (
    ArtifactMetadata, ArtifactTag )

LOG = logging.getLogger(__name__)

class YakeNGramKeywordsExtractor(BaseKeywordExtractor):
    """Uses the Yet Another Keyword Extractor to extract keywords from text files."""
    name = "yake_ngram_keywords"
    version = "0.1"

    def __init__(self,config,session,**kwargs):
        self._config = config
        self._session = session

    def extract_keywords(self,text,source=None):
        LOG.debug("extracting keywords (%s) from %r",
                  getattr(self.__class__,"name",None),source)

        ext = yake.KeywordExtractor()
        top_keywords = ext.extract_keywords(text)
        if not len(top_keywords):
            LOG.debug("no top ngram keywords found in %r",source)
            return False

        for (kw,rank) in top_keywords:
            # Don't add duplicate tags.
            if not self.session.artifact.has_tag(kw,ignore_case=True):
                LOG.debug("yake found kw %s (%r)",kw,rank)
                self.session.artifact.tags.append(
                    ArtifactTag(tag=kw,source="yake_ngram_keywords"))

        top_keywords = json.dumps(top_keywords, separators=(',', ':'))
        self.session.artifact.meta.append(
            ArtifactMetadata(
                name="top_ngram_keywords",value=top_keywords,source="yake_ngram_keywords",type="json"))
        return True
