
import six
import logging
import sys
import os.path
import os
import requests
import json

import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter

from searcch.importer.extractor import BaseKeywordExtractor
from searcch.importer.db.model import (
    ArtifactMetadata, ArtifactTag )

LOG = logging.getLogger(__name__)

def requests_download(url,destpath,retries=2,interval=2):
    while retries >= 0:
        try:
            session = requests.session()
            response = session.get(url,stream=True,timeout=4)
            response.raise_for_status()
            fd = open(destpath,'wb')
            for buf in response.iter_content(4096):
                fd.write(buf)
            fd.close()
            return response
        except:
            if retries == 0:
                six.reraise(*sys.exc_info())
        retries -= 1
    return None

class TopKeywordsExtractor(BaseKeywordExtractor):
    """A simple extractor that grabs the top N keywords from an ArtifactFile that is a PDF."""
    name = "top_keywords"
    version = "0.1"

    def __init__(self,config,session,**kwargs):
        self._config = config
        self._session = session
        self._common_words = []
        self._stop_words = set()
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        LOG.debug("loading nltk and token data")
        tmpdir = self.config["DEFAULT"]["tmpdir"]
        try:
            if not nltk.corpus.stopwords.fileids:
                nltk.download('stopwords')
        except:
            nltk.download('stopwords')
        self._stop_words = set(stopwords.words("english"))
        nltk.download("punkt")
        cw_url = "https://github.com/first20hours/google-10000-english/raw/master/google-10000-english-no-swears.txt"
        top_file = os.path.join(tmpdir,"google-10000-english-no-swears.txt")
        try:
            if not os.path.exists(top_file):
                requests_download(cw_url,top_file)
            with open(top_file,"rb") as f:
                self._common_words = set(f.read().decode().split())
            self._loaded = True
        except:
            LOG.warning("failed to download google-10000-english-no-swears.txt")
            LOG.exception(sys.exc_info()[1])

    def clean(self,line):
        # tokenize, ignore non-alpha's and stop or common words
        stripped = [w for w in word_tokenize(line) if w.isalpha() and not (
            w in self._stop_words or w in self._common_words)]
        return(list(filter(None, stripped)))

    def extract_keywords(self,text,source=None):
        LOG.debug("extracting keywords (%s) from %s",
                  getattr(self.__class__,"name",None),source)

        self.load()

        counts = Counter(self.clean(text.lower()))
        if not len(counts):
            LOG.debug("no keywords found in %r" % (source,))
            return False

        top = counts.most_common(10)
        for (kw,count) in top:
            # Don't add duplicate tags.
            if not self.session.artifact.has_tag(kw,ignore_case=True):
                LOG.debug("top_keywords found kw %s (%r)",kw,count)
                self.session.artifact.tags.append(
                    ArtifactTag(tag=kw,source="top_keywords"))

        top_keywords = json.dumps(top, separators=(',', ':'))
        self.session.artifact.meta.append(
            ArtifactMetadata(
                name="top_keywords",value=top_keywords,source="top_keywords",type="json"))
        return True
