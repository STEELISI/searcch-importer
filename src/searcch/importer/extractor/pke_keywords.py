import six
import logging
import sys
import os.path
import os
import requests
import json
import spacy
import nltk
import pke

from searcch.importer.extractor import BaseKeywordExtractor
from searcch.importer.db.model import (
    ArtifactMetadata, ArtifactTag )

LOG = logging.getLogger(__name__)

class PKEExtractor(BaseKeywordExtractor):
    """Uses the PKE toolkit to extract keywords from text files."""
    name = "pke_keywords"
    version = "0.1"

    def __init__(self,config,session,**kwargs):
        self._config = config
        self._session = session
        try:
            sp = spacy.load("en_core_web_sm")
        except:
            spacy.cli.download("en_core_web_sm")
            sp = spacy.load("en_core_web_sm")
        try:
            if not nltk.corpus.stopwords.fileids:
                nltk.download('stopwords')
        except:
            nltk.download('stopwords')

    def extract_keywords(self,text,source=None):
        LOG.debug("extracting keywords (%s) from %r",
            getattr(self.__class__,"name",None),source)

        keywords = []
        extractor = pke.unsupervised.TopicRank()
        extractor.load_document(input=text, language="en")
        extractor.candidate_selection()
        extractor.candidate_weighting()
        keyphrases = extractor.get_n_best(n=10)
        maxi=-float('inf')
        for i in keyphrases:
            maxi = max(maxi,i[1])
        normalized = []
        for i in keyphrases:
            normalized.append((i[0],i[1]/maxi))
        keywords.extend(normalized)
        extractor = pke.unsupervised.YAKE()
        extractor.load_document(input=text, language="en")
        extractor.candidate_selection()
        extractor.candidate_weighting()
        keyphrases = extractor.get_n_best(n=10)
        maxi=-float('inf')
        for i in keyphrases:
            maxi = max(maxi,i[1])
        normalized = []
        for i in keyphrases:
            normalized.append((i[0],i[1]/maxi))
        keywords.extend(normalized)
        extractor = pke.unsupervised.MultipartiteRank()
        extractor.load_document(input=text, language="en")
        extractor.candidate_selection()
        extractor.candidate_weighting()
        keyphrases = extractor.get_n_best(n=10)
        maxi=-float('inf')
        for i in keyphrases:
            maxi = max(maxi,i[1])
        normalized = []
        for i in keyphrases:
            normalized.append((i[0],i[1]/maxi))
        keywords.extend(normalized)

        keywords.sort(key = lambda x:x[1],reverse=True)
        seen=set()
        filtered_keywords = []
        for i in keywords:
            if(i[0] not in seen):
                filtered_keywords.append(i)
                seen.add(i[0])

        if not len(filtered_keywords):
            LOG.debug("no pke keywords found in %r",source)
            return False

        # Add in ArtifacTags, but don't duplicate.
        for (kw,rank) in filtered_keywords:
            if not self.session.artifact.has_tag(kw,ignore_case=True):
                LOG.debug("pke_keywords found kw %s (%r)",kw,rank)
                self.session.artifact.tags.append(
                    ArtifactTag(tag=kw,source="pke_keywords"))

        pke_keywords = json.dumps(filtered_keywords, separators=(',', ':'))
        self.session.artifact.meta.append(
            ArtifactMetadata(
                name="pke_keywords",value=pke_keywords,source="pke_keywords",type="json"))
        return True;
