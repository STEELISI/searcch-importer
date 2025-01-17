import sys
import six
import os
import logging
import dateutil.parser
import datetime
import urllib
import requests
from future.utils import raise_from
from urllib.parse import urlparse
import bs4
import re
import bibtexparser
import json

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact, ArtifactFile, ArtifactMetadata, ArtifactRelease, User, Person,
    Importer, Affiliation, ArtifactAffiliation, ArtifactTag, Organization,
    Badge, ArtifactBadge, RecurringVenue, Venue, ArtifactVenue)
from searcch.importer.exceptions import MissingMetadataError

LOG = logging.getLogger(__name__)

class NDSSImporter(BaseImporter):
    """Provides an NDSS Importer."""

    name = "ndss"
    version = "0.1"

    @classmethod
    def _extract_record_id(self, url):
        try:
            session = requests.session()
            res = requests.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc.endswith("ndss-symposium.org") \
              and urlobj.path.startswith("/ndss"):
                return (urlobj.path[len("/ndss-paper/"):].rstrip("/"), res.url, session)
        except BaseException:
            return None

    @classmethod
    def can_import(cls, url):
        """Checks to see if this URL is a doi.org or ndss-symposium.org/ndss-paper URL."""
        if cls._extract_record_id(url):
            return True
        return False

    def parse_author_str(self, authors):
        # We split on ), assuming that institution names are within () pairs.
        # Then we extract the institution and split the string that preceded
        # the ( on , -- this allows multiple authors from the same institution.
        ret = []
        for x in authors.split(")"):
            xa = x
            fp = x.find("(")
            inst = None
            if fp > 0:
                xa = x[:fp]
                inst = x[fp+1:].strip()
            org = None
            if inst:
                org = Organization(name=inst, type="Institution")
            for n in xa.split(","):
                n = n.strip()
                if not n:
                    continue
                p = Person(name=n)
                aff = Affiliation(person=p,org=org)
                aaff = ArtifactAffiliation(
                    affiliation=aff,roles="Author")
                ret.append(aaff)
        return ret

    def import_artifact(self, candidate):
        """Imports an artifact from NDSS and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from NDSS " % (url,))
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, 'html.parser')
        page_header_elm = soup.find('div',class_="page-header")

        # Two ways to find the title: entry-title or meta og:title.
        title = None
        title_elm = soup.find('h1',class_='entry-title')
        if title_elm:
            title = title_elm.text
        if not title:
            title_elm = soup.find("meta", {"property": "og:title"})
            if title_elm:
                title = title_elm.get("content").replace(" - NDSS Symposium", "")
        if not title:
            raise MissingMetadataError("no title")

        # Find author/affiliation info.
        affiliations = []
        auth = soup.find('p',class_="ndss_authors")
        if not auth:
            auth = soup.find('strong',text=lambda x: x.text.startswith("Author(s):"))
            if auth:
                auth = auth.parent.text
            else:
                auth = soup.find("div", {"class":"page-header"})
                if auth:
                    auth = auth.find("p")
                if auth:
                    auth = auth.text.strip()
        if auth:
            auth = auth.replace("Author(s):" , "")
            LOG.debug("parsing author string: %r", auth)
            affiliations = self.parse_author_str(auth)
        if not affiliations:
            LOG.warn("no author data")

        # Find associated artifact files.  Two overall possibilities: the old
        # ndss_* classes; Paper/Slides href text; and the new aria button
        # classes.
        artifact_files = []
        try:
            ppfd = soup.find('p',class_="ndss_downloads")
            if ppfd:
                paperurl = "https://www.ndss-symposium.org/"
                url_route = ppfd.find('a')['href']
                path = urlparse(url_route).path
                ext = os.path.splitext(path)
                typ = ext[1][1:]
                name = ext[0].split('/')[-1]+ext[1]
                paperurl = paperurl + url_route
                artifact_files.append(ArtifactFile(
                    name=name, url=paperurl, filetype="application/"+typ))
            ppfd = soup.find('p',class_="ndss_additional")
            if ppfd:
                paperurl = "https://www.ndss-symposium.org/"
                url_route = ppfd.find('a')['href']
                path = urlparse(url_route).path
                ext = os.path.splitext(path)
                typ = ext[1][1:]
                pdfurl = paperurl + url_route
                artifact_files.append(ArtifactFile(
                    name=name, url=pdfurl, filetype="application/"+typ))
        except:
            LOG.warning("failed to parse artifact files") 
            LOG.exception(sys.exc_info()[1])
        presentation_pdf_det = soup.find('a', class_='pdf-button')
        if presentation_pdf_det:
            presentation_pdf_link = presentation_pdf_det.get('href')
            path = urlparse(presentation_pdf_link).path
            ext = os.path.splitext(path)
            typ = ext[1][1:]
            name = ext[0].split('/')[-1]+ext[1]
            artifact_files.append(ArtifactFile(
                name=name, url=presentation_pdf_link, filetype="application/"+typ))
        presentation_slides_det = soup.find('a', class_='button-slides')
        if presentation_slides_det:
            presentation_slides_link = presentation_slides_det.get('href')
            path = urlparse(presentation_slides_link).path
            ext = os.path.splitext(path)
            typ = ext[1][1:]
            name = ext[0].split('/')[-1]+ext[1]
            artifact_files.append(ArtifactFile(
                name=name, url=presentation_slides_link, filetype="application/"+typ))
        # Extreme a.text strategy for old editions.
        if not artifact_files:
            section = soup.find("section", {"class": "new-wrapper"})
            if section:
                paper_link = section.find('a',text=lambda x: x.startswith("Paper"))
                if paper_link:
                    paperurl = "https://www.ndss-symposium.org/"
                    url_route = paper_link.get('href')
                    path = urlparse(url_route).path
                    ext = os.path.splitext(path)
                    typ = ext[1][1:]
                    name = ext[0].split('/')[-1]+ext[1]
                    paperurl = paperurl + url_route
                    artifact_files.append(ArtifactFile(
                        name=name, url=paperurl, filetype="application/"+typ))
                slides_link = section.find('a',text=lambda x: x.startswith("Slides"))
                if slides_link:
                    paperurl = "https://www.ndss-symposium.org/"
                    url_route = slides_link.get('href')
                    path = urlparse(url_route).path
                    ext = os.path.splitext(path)
                    typ = ext[1][1:]
                    name = ext[0].split('/')[-1]+ext[1]
                    pdfurl = paperurl + url_route
                    artifact_files.append(ArtifactFile(
                        name=name, url=pdfurl, filetype="application/"+typ))

        # Find the description (abstract).
        abstract = ""
        abs_elm = soup.find("div",{"class": "paper-data"})
        if abs_elm:
            abstract = "".join(
                map(lambda x: x.text.strip(), abs_elm.findAll("p")))
        else:
            abs_elm = soup.find("section",{"class":"new-wrapper"})
            if abs_elm:
                abs_elm = abs_elm.find(
                    "h2",text=lambda x: x.startswith("Abstract:"))
            if abs_elm:
                abs_elm = abs_elm.findNextSibling("p")
            if abs_elm:
                abstract = abs_elm.text

        # The only metadata we extract is a link to the presentation video.
        metadata = []
        presentation_video_det = soup.find('a', class_='button-video')
        if presentation_video_det:
            presentation_video_link = presentation_video_det.get('href')
            parsed_url = urlparse(presentation_video_link)
            if not parsed_url.scheme:
                presentation_video_link = "https:" + presentation_video_link
            metadata.append(ArtifactMetadata(
                name="presentation_video",
                value=str(presentation_video_link), type="text/json",
                source="ndss"))

        # Extract Venue.  Two possibilities: the old ndss_associated class, or
        # extracting year from ArtifactFile URLs.
        vvalues = dict(type="conference")
        artifact_venue = []
        venue_object = None
        venue_link = soup.find('p',class_='ndss_associated')
        if venue_link:
            venue_url = venue_link.find('a')['href']
            venue_title = venue_link.find('a').text
            venue_object = self.session.query(Venue).\
                filter(Venue.url  == venue_url).\
                filter(Venue.verified == True).first()
            if not venue_object:
                vvalues["url"] = venue_url
                vvalues["title"] = venue_title
                venue_object = Venue(**vvalues)
            artifact_venue.append(ArtifactVenue(venue=venue_object))
        if not venue_object:
            aevent = soup.find('strong',text=lambda x: x.text.startswith("Associated Event:"))
            if aevent:
                aevent = aevent.parent.find("a")
            if aevent:
                venue_url = aevent.get("href")
                venue_title = aevent.text.strip()
                venue_object = self.session.query(Venue).\
                    filter(Venue.url  == venue_url).\
                    filter(Venue.verified == True).first()
                if not venue_object:
                    vvalues["url"] = venue_url
                    vvalues["title"] = venue_title
                    venue_object = Venue(**vvalues)
                artifact_venue.append(ArtifactVenue(venue=venue_object))
        if not venue_object:
            year = None
            for af in artifact_files:
                match = re.search("[^\d]+((20|19)\d\d)[^\d]+", af.url)
                if match:
                    year = match.group(1)
                    break
            if year:
                venue_url = "https://www.ndss-symposium.org/ndss" + year + "/"
                venue_title = "NDSS Symposium "+year
                venue_object = self.session.query(Venue).\
                  filter(Venue.url == venue_url).\
                  filter(Venue.verified == True).first()
                if not venue_object:
                    vvalues["url"] = venue_url
                    vvalues["title"] = venue_title
                    venue_object = Venue(**vvalues)
                artifact_venue.append(ArtifactVenue(venue=venue_object))

        if venue_object and not venue_object.recurring_venue:
            venue_object.recurring_venue = RecurringVenue(
                url="https://www.ndss-symposium.org/",
                title="Network and Distributed System Security Symposium",
                abbrev="NDSS", type="conference",
                description="The NDSS Symposium is a leading security forum that fosters information exchange among researchers and practitioners of network and distributed system security.")

        return Artifact(
            type="publication",url=url,title=title,description=abstract,
            ctime=datetime.datetime.now(),
            owner=self.owner_object,importer=self.importer_object,
            tags=[],meta=metadata,files=artifact_files,affiliations=affiliations,venues=artifact_venue)
