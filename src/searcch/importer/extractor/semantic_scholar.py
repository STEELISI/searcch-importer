import requests
import logging
import json

from searcch.importer.extractor import BaseExtractor
from searcch.importer.db.model import (
    ArtifactMetadata )

LOG = logging.getLogger(__name__)

class SemanticScholarExtractor(BaseExtractor):
    api_restpoint = "https://api.semanticscholar.org/v1/"
    name = "semantic_scholar"
    version = "0.1"

    def __init__(self, config,session,**kwargs):
        self._config = config
        self._session = session
        self.doi_number = self.get_doi_number()
        self.paper_info = None

    def get_paper_info(self):
        paper_api_restpoint = self.api_restpoint + "paper/" + self.doi_number
        r = requests.get(paper_api_restpoint)
        if r.status_code == 200:
            self.paper_info = r.json()

    def get_citations(self):
        if self.paper_info:
            if "citations" in self.paper_info.keys():
                citations = self.paper_info["citations"]
                return citations

    def get_references(self):
        if self.paper_info:
            if "references" in self.paper_info.keys():
                references = self.paper_info["references"]
                return references

    def get_doi_number(self):
        for individual_meta in self.session.artifact.meta:
            if individual_meta.name == "doi":
                return individual_meta.value

    def extract(self):
        LOG.debug("Inside semantic_scholar extract...")

        if self.doi_number is not None:
            self.get_paper_info()
            citations = json.dumps(self.get_citations())
            references = json.dumps(self.get_references())

            # Enrich the artifact here.
            self.session.artifact.meta.append(
                ArtifactMetadata(
                    name="citations", value=citations, type="text/json", source="semantic_scholar"))

            self.session.artifact.meta.append(
                ArtifactMetadata(
                    name="references", value=references, type="text/json", source="semantic_scholar"))
