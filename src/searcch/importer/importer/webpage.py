import re
import sys
import six
import logging
import time
import dateutil.parser
import datetime
from future.utils import raise_from
import giturlparse
import requests
import re
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
    """Provides a Github Importer."""

    name = "webage"
    version = "0.1"

    @classmethod
    def can_import(cls,url):
        print("Checking ", url)
        if (url.endswith(".web")):
            return True
        else:
            return False


    def import_artifact(self,candidate):
        """Imports an artifact from Github and returns an Artifact, or throws an error."""
        url = candidate.url
        print("Importing artifact from", url)
        LOG.warn("importing '%s' from github" % (url,))
        
        with open(url) as f:                                                   
            lines = f.readlines()
            items = lines[0].split('|')
            authors = items[0].split(',')
            papertitle = items[1].strip()
            webpage = items[3].strip()
            affiliations = []
            for i in authors:
                if i.strip() != "":
                    person = Person(name=i.strip())
                    affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=person,org=None),roles="Author"))

            LOG.warn("importing '%s' from webpage" % (webpage,))               

            page = requests.get(webpage)
            description = page.text
            soup = BeautifulSoup(page.text, features="html.parser")            
            title = soup.find('title')

            if title is None or title.get_text() == "":
                title = soup.find('h1')
            if title is None or title.get_text() == "":
                title = soup.find('h2')
            if title is None or title.get_text() == "":
                title = soup.find('h3')
            if title is None or title.get_text() == "":
                title = soup.find('p')
            if title is not None:
                title=title.get_text()
                title = re.sub(r'[^a-zA-Z0-9\-\_\s]', '', title)
            else:
                title = papertitle                
            
            print("Title ", title)
            
            alllinks = soup.find_all('a')
            arttype = "software"
            
            for a in alllinks:                                                 
                link = a.get('href')                                           
                parent_element = a.parent
                surrounding_text = ""
                if parent_element:                                             
                    surrounding_text = parent_element.get_text(separator=' ', strip=True)
                    
                if link is not None:
                    if (link.endswith(".gz") or link.endswith(".zip") or "github.com" in link):
                        arttype = "software"
                    if "dataset" in surrounding_text:
                        arttype = "dataset"
                    
            releases = list()                                                  
            files = list()

            name = title
            path = None
            license = None
            tags = list()
            metadata = list()
            
            return Artifact(type=arttype,url=webpage,title=title,description=description,
                            name=name,ctime=datetime.datetime.now(),ext_id=path,
                            owner=self.owner_object,importer=self.importer_object,
                            tags=tags,meta=metadata,files=files,license=license,releases=releases,
                            affiliations=affiliations)

        return None
