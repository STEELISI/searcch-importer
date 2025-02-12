import re
import sys
import six
import logging
import time
import dateutil.parser
import datetime
from future.utils import raise_from
import requests
from bs4 import BeautifulSoup, SoupStrainer
from urllib.parse import urlparse

from searcch.importer.importer import BaseImporter
from searcch.importer.exceptions import HttpError
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,ArtifactFileMember,
    ArtifactTag,FileContent)
from searcch.importer.db.model.license import recognize_license

LOG = logging.getLogger(__name__)

class WebpageImporter(BaseImporter):
    """Provides a generic importer from a URL."""

    name = "webpage"
    version = "0.1"

    @classmethod
    def can_import(cls,url):
        print("Checking if webpage can be imported ", url)
        try:
            response = requests.get(url)
            print("Got status code", response.status_code)
            if response.status_code != 200:
                return False
            else:
                return True
        except HttpError:
            return False

    def import_artifact(self,candidate):
        """Imports an artifact from Github and returns an Artifact, or throws an error."""
        url = candidate.url
        
        print("Importing artifact from", url)
        LOG.warn("importing '%s' from webpage" % (url,))

        page = requests.get(url)
        soup = BeautifulSoup(page.text, features="html.parser")
        title = soup.find('title').get_text()
        print("Title ", title)
        alllinks = soup.find_all('a')
        for a in alllinks:
            link = a.get('href')
            parent_element = a.parent
            if parent_element:
                surrounding_text = parent_element.get_text(separator=' ', strip=True)
                print("text ", surrounding_text)
            print("link ", link)
            
        releases = list()
        files = list()
        
        return Artifact(type="software",url=url,title="fake", description="fake",
                        name="fake",ctime=datetime.datetime.now(),ext_id="",
                        owner=self.owner_object,importer=self.importer_object,
                        tags=None,meta=None,files=files,license=None,releases=releases,
                        affiliations=None)
