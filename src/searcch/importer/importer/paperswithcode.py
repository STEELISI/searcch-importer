import logging
import datetime
import requests
from urllib.parse import urlparse

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,ArtifactTag, CandidateArtifactRelationship, CandidateArtifact )

LOG = logging.getLogger(__name__)

class PapersWithCodeClient(object):

    def __init__(self, token=None):
        self.token = None
        self.session = requests.session()
        self.baseurl = "https://paperswithcode.com/api/v1"

    def paper_get(self, paper_id):
        ret = self.session.get(self.baseurl + "/papers/" + str(paper_id),
                               headers={"Accept":"application/json"})
        ret.raise_for_status()
        return ret.json()

    def paper_repository_list(self, paper_id):
        ret = self.session.get(self.baseurl + "/papers/" + str(paper_id) + "/repositories",
                               headers={"Accept":"application/json"})
        ret.raise_for_status()
        return ret.json()

    def paper_dataset_list(self, paper_id):
        ret = self.session.get(self.baseurl + "/papers/" + str(paper_id) + "/datasets",
                               headers={"Accept":"application/json"})
        ret.raise_for_status()
        return ret.json()

    def dataset_get(self, dataset_id):
        ret = self.session.get(self.baseurl + "/datasets/" + str(dataset_id),
                               headers={"Accept":"application/json"})
        ret.raise_for_status()
        return ret.json()

class PapersWithCodeImporter(BaseImporter):
    """Provides an PapersWithCode Importer."""

    name = "paperswithcode"
    version = "0.1"

    @classmethod
    def _extract_paper_id(self, url, session=None):
        try:
            if not session:
                session = requests.session()
            res = session.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc.endswith("paperswithcode.com") \
              and urlobj.path.startswith("/paper/"):
                paper_id = urlobj.path[len("/paper/"):].rstrip("/")
                return paper_id
        except BaseException:
            return None

    @classmethod
    def can_import(cls, url):
        """Checks to see if this URL is a paperswithcode.com URL"""
        if cls._extract_paper_id(url):
            return True
        return False

    def import_artifact(self,candidate):
        """Imports an artifact from paperswithcode and returns an Artifact, or throws an error"""
        url = candidate.url
        LOG.debug("Importing %s from paperswithcode" % (url,))

        client = PapersWithCodeClient()
        paper_id = self.__class__._extract_paper_id(url, session=client.session)
        if not paper_id:
            LOG.warning("unrecognizable paperswithcode URL (%r)", url)
            return None

        paper_info = client.paper_get(paper_id)
        LOG.debug("paperswithcode paper_info: %r", paper_info)
        title = paper_info.get("title", "")
        abstract = paper_info.get("abstract", "")

        affiliations = []
        for author in paper_info.get("authors", []):
            affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=Person(name=author)), roles="Author"))

        # Getting the repo links
        repo_list = map(lambda x: x.get("url", None), client.paper_repository_list(paper_id).get("results", []))

        # Getting the dataset objects
        dataset_list = map(lambda x: x.get("url", None), client.paper_dataset_list(paper_id).get("results", []))

        # Get paper URL and add as an ArtifactFile for keyword extraction
        files = []
        url_pdf = paper_info.get("url_pdf", "")
        url_pdf_name = None
        if url_pdf:
            url_pdf_parsing = urlparse(url_pdf)
            url_pdf_name = url_pdf_parsing.path[len("/pdf/"):].rstrip("/")
            files.append(ArtifactFile(
                url=url_pdf,
                filetype="application/pdf",
                name=url_pdf_name
            ))

        # Create candidate artifacts for repo_links and datasets
        ts = datetime.datetime.now()
        artifact_relationships = []
        for repo_url in repo_list:
            if not repo_url:
                continue
            candidate_artifact = CandidateArtifact(
                url=repo_url, type="software", ctime=ts, owner=self.owner_object)
            candidate_artifact_relationship = CandidateArtifactRelationship(
                relation="describes", related_candidate=candidate_artifact)
            artifact_relationships.append(candidate_artifact_relationship)

        for dataset_url in dataset_list:
            if not dataset_url:
                continue
            candidate_artifact = CandidateArtifact(
                url=dataset_url, type="dataset", ctime=ts, owner=self.owner_object)
            candidate_artifact_relationship = CandidateArtifactRelationship(
                relation="describes", related_candidate=candidate_artifact)
            artifact_relationships.append(candidate_artifact_relationship)

        artifact = Artifact(
            type="publication", url=url, title=title, description=abstract, ctime=ts,
            ext_id=url, affiliations=affiliations, files=files,
            candidate_relationships=artifact_relationships, owner=self.owner_object)

        return artifact

