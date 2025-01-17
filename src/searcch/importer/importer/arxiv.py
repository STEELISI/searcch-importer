import logging
import datetime
import atoma, requests
from urllib.parse import urlparse
import urllib, urllib.request
import arxiv

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,ArtifactTag )

LOG = logging.getLogger(__name__)

class ArxivImporter(BaseImporter):
    """Provides an Arxiv Importer"""

    name = "arxiv"
    version = "0.1"

    @classmethod
    def _extract_record_id(self, url):
        try:
            #session = requests.session()
            res = requests.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc == "arxiv.org" \
              and (urlobj.path.startswith("/abs/") or urlobj.path.startswith("/pdf/")): # check for pdf file as well
                paper_id = urlobj.path[len("/abs/"):].rstrip("/")
                return paper_id
        except BaseException:
            return None

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a arxiv.org URL."""
        if cls._extract_record_id(url):
            return True
        return False

    def import_artifact(self, candidate):
        """Imports an artifact from Arxiv and returns an Artifact"""
        url = candidate.url.replace('/pdf/','/abs/').replace(".pdf","")
        LOG.debug("importing '%s' from Arxiv" % (url,))
        arxiv_url = "http://export.arxiv.org/api/query?"

        session = requests.session()
        res = requests.get(url)
        urlobj = urlparse(res.url)

        if urlobj.netloc == "arxiv.org" and urlobj.path.startswith("/abs/"):
            paper_id = urlobj.path[len("/abs/"):].rstrip("/")
            arxiv_url = arxiv_url + "id_list=" + paper_id
            arxiv_url_response = urllib.request.urlopen(arxiv_url)
            article_content = arxiv_url_response.read()
            feed = atoma.parse_atom_bytes(article_content)

            artifacts = []
            metadata = []
            metadata.append(ArtifactMetadata(name="arxiv_id", value=paper_id, source="arxiv"))

            for entry in feed.entries:
                title = entry.title.value
                url = entry.id_
                abstract = entry.summary.value

                affiliations = []

                for person in entry.authors:
                    LOG.debug("adding author %r", person)
                    affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=Person(name=person.name)), roles="Author"))

                files = []

                for link in entry.links:
                    if link.type_ == "application/pdf":
                        files.append(ArtifactFile(
                            url=link.href,
                            filetype="application/pdf",
                            name=paper_id + ".pdf"
                        ))

                artifacts.append(Artifact(type="software", url=url, title=title, description=abstract, ctime=datetime.datetime.now(),
                         ext_id=paper_id, affiliations=affiliations, files=files, meta=metadata, owner=self.owner_object))
            return artifacts[0]
