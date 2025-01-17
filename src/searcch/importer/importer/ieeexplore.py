
import sys
import six
import logging
import time
import dateutil.parser
import datetime
import requests
from future.utils import raise_from
from urllib.parse import urlparse
import rispy
import json
import bs4
import re

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,Organization,
    Importer,Affiliation,ArtifactAffiliation,ArtifactTag,Venue,ArtifactVenue,
    RecurringVenue)
from searcch.importer.exceptions import MissingMetadataError

LOG = logging.getLogger(__name__)

class IeeeXploreImporter(BaseImporter):
    """Provides an IeeeXplore DOI Importer."""

    name = "ieeexplore"
    version = "0.1"

    @classmethod
    def _extract_record_id(self,url):
        try:
            urlobj = urlparse(url)
            if urlobj.netloc == "doi.ieeecomputersociety.org":
                doi = urlobj.path[1:].rstrip("/")
                url = "https://doi.org/" + doi
            session = requests.session()
            res = requests.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc == "ieeexplore.ieee.org" \
              and urlobj.path.startswith("/document/"):
                return (urlobj.path[len("/document/"):].rstrip("/"),res.url,session)
        except BaseException:
            return None

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a doi.org or ieeexplore.ieee.org/document URL."""
        if cls._extract_record_id(url):
            return True
        return False

    def import_artifact(self,candidate):
        """Imports an artifact from IEEE Xplore and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from IEEE Xplore" % (url,))
        (record_id,newurl,session) = self.__class__._extract_record_id(url)
        headers = { "Referer": newurl, "User-Agent": "" }
        res = session.get(newurl,headers=headers)
        res.raise_for_status()
        risres = session.get(
            "https://ieeexplore.ieee.org/rest/search/citation/format?recordIds=%s&download-format=download-ris" % (record_id),
            headers=headers)
        risres.raise_for_status()

        LOG.debug("record: %r",risres.json())

        soup = bs4.BeautifulSoup(res.content, 'html.parser')
        risdata = rispy.loads(risres.json()["data"])[0]
        jsondata = dict()
        match = re.search("xplGlobal\.document\.metadata=(.*);",
                          res.content.decode("utf-8"))
        if match:
            try:
                jsondata = json.loads(match.group(1))
            except:
                LOG.error("failed to decode matched JSON content")
                LOG.exception(sys.exc_info()[1])
        title = risdata.get("title") or jsondata.get("title")
        if not title:
            title_elm = soup.find("meta", {"property": "og:title"})
            if title_elm:
                title = title_elm.get("content")
        if not title:
            raise Exception("unable to extract title")
        doi = risdata.get("doi","") or jsondata.get("doi","")
        if not doi:
            raise Exception("no DOI in metadata")
        description = risdata.get("abstract") or jsondata.get("abstract")
        if not description:
            description_elm = soup.find("meta", {"property": "og:description"})
            if description_elm:
                description = description_elm.get("content")
        if not description:
            LOG.warning("%s (%s) missing abstract",newurl,url)

        # Two paths to the author list: embedded json data structure; or RIS.
        affiliations = []
        for a in jsondata.get("authors",[]):
            org = None
            aaff = a.get("affiliation",[])
            if len(aaff) > 0:
                org = Organization(type="Institution",name=aaff[0])
            person = Person(name=a["name"])
            LOG.debug("adding JSON author %r",person)
            affiliations.append(ArtifactAffiliation(
                affiliation=Affiliation(person=person,org=org),roles="Author"))
        if not affiliations:
            authors = []
            for a in risdata.get("authors",[]):
                authors.append(Person(name=a))
            for person in authors:
                LOG.debug("adding RIS author %r",person)
                affiliations.append(ArtifactAffiliation(
                    affiliation=Affiliation(person=person),roles="Author"))

        tags = list()
        seentags = dict()
        for kw in risdata.get("keywords",[]):
            if kw in seentags:
                continue
            tags.append(ArtifactTag(tag=kw,source="ieeexplore"))
            seentags[kw] = True
        for kwi in jsondata.get("keywords",[]):
            kwl = kwi.get("kwd")
            kwt = kwi.get("type")
            for kw in kwl:
                if kw in seentags:
                    continue
                tags.append(ArtifactTag(tag=kw,source=kwt))
                seentags[kw] = True

        metadata = list()
        verbatim_metadata_names = [
            "doi","start_page","end_page","secondary_title","type_of_reference",
            "year","journal_name","number","issn","publication_year" ]
        for vmn in verbatim_metadata_names:
            if not vmn in risdata:
                continue
            metadata.append(ArtifactMetadata(name=vmn,value=str(risdata[vmn])))

        record_url = "https://doi.org/%s" % (doi,)

        files = []
        LOG.debug("attempting PDF fetch via %r from IEEE Xplore",url)
        try:
            href = "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=" + record_id
            res = session.head(href)
            if res.status_code == requests.codes.ok:
                filename = record_id + ".pdf"
                files.append(
                    ArtifactFile(url=href,name=filename,filetype="application/pdf"))
                LOG.debug("found PDF file at %r",href)
            else:
                LOG.warning("failed to HEAD the pdf link (%r,%r); cannot download",
                            href,res.status_code)
        except:
            LOG.warning("failed PDF fetch via %r from IEEE Xplore",url)

        # Extracting the Venue Information from IEEE.
        artifact_venue = []
        try:
            venue_type="other"
            venue_title = None
            venue_url = jsondata.get("pubLink")
            if not venue_url:
                venue_url_elm = soup.find(
                    "div",{"class":"stats-document-abstract-publishedIn"})
                if venue_url_elm:
                    venue_url_elm = venue_url_elm.find(
                        "strong",text=lambda x: x.startswith("Published in:"))
                if venue_url_elm:
                    venue_url_elm = venue_url_elm.findNextSibling("a")
                if venue_url_elm:
                    venue_url = venue_url_elm.get("href")
            if not venue_url:
                raise MissingMetadataError("failed to extract venue URL")
            elif venue_url[0] == "/":
                venue_url = "https://ieeexplore.ieee.org" + venue_url
            if "type_of_reference" in risdata: 
                if risdata["type_of_reference"]  == "CONF":
                    venue_type  = "conference"
                elif risdata["type_of_reference"]  == "JOUR":
                    venue_type = "journal"
                elif risdata["type_of_reference"] == "MAG":
                        venue_type = "magazine"
            if "journal_name" in risdata:
                venue_title = risdata["journal_name"]
            venue_object = self.session.query(Venue).\
                filter(Venue.title  == title).\
                filter(Venue.verified == True).first()
            if not venue_object:
                value = dict(
                    type=venue_type,title=venue_title,url=venue_url)
                if "isbn" in risdata:
                    value["isbn"] = risdata["isbn"]
                if "issn" in risdata:
                    value["issn"] = risdata["issn"]
                if "volume" in risdata:
                    value["volume"] = risdata["volume"]
                if "doi" in risdata:
                    value["doi"] = risdata["doi"]
                venue_object = Venue(**value)

                vheaders = { "Referer": venue_url, "User-Agent": "" }
                jsonmetares = session.get(
                    "https://ieeexplore.ieee.org/rest/publication/home/metadata?pubid=%s" % (venue_url.split("/")[-2],),
                    headers=vheaders)
                jsonmetares.raise_for_status()
                jm = jsonmetares.json()
                if jm.get("hasParentConference", False) \
                  and jm.get("parentPublicationNumber"):
                    ppn = jm.get("parentPublicationNumber")
                    pt = jm.get("parentTitle")
                    purl = "https://ieeexplore.ieee.org/xpl/conhome/%s/all-proceedings" % (ppn,)
                    recurring_venue_object = RecurringVenue(
                        url=purl,title=pt,type="conference")
                    venue_object.recurring_venue = recurring_venue_object

            artifact_venue.append(ArtifactVenue(venue=venue_object))
        except:
            LOG.warn("failed to scrape existing venue info")
            LOG.exception(sys.exc_info()[1])

        return Artifact(
            type="publication",url=record_url,title=title,description=description,
            ctime=datetime.datetime.now(),ext_id=record_id,
            owner=self.owner_object,importer=self.importer_object,
            tags=tags,meta=metadata,affiliations=affiliations,files=files,venues=artifact_venue)
