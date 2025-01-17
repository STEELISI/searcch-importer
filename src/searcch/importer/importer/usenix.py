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
import bibtexparser

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact, ArtifactFile, ArtifactMetadata, ArtifactRelease, User, Person,
    Importer, Affiliation, ArtifactAffiliation, ArtifactTag, Organization,
    Badge, ArtifactBadge, RecurringVenue, Venue, ArtifactVenue)

LOG = logging.getLogger(__name__)

class USENIXImporter(BaseImporter):
    """Provides an USENIX DOI Importer."""

    name = "usenix"
    version = "0.1"

    @classmethod
    def _extract_record_id(self, url):
        try:
            session = requests.session()
            res = requests.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc.endswith("usenix.org") \
              and urlobj.path.startswith("/conference/") and "/presentation/" in urlobj.path:
                return (urlobj.path[len("/conference/"):].rstrip("/"), res.url, session)
        except BaseException:
            return None

    @classmethod
    def can_import(cls, url):
        """Checks to see if this URL is a doi.org or usenix.org/conference URL."""
        if cls._extract_record_id(url):
            return True
        return False

    def import_artifact(self, candidate):
        """Imports an artifact from USENIX and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from USENIX " % (url,))
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, 'html.parser')

        title = soup.find('h1',id='page-title')
        if not title:
            LOG.warn("no title in data")
            title = soup.head.title.text.split(" | ")[0]
        else:
            title = title.text
        
        abstract=""
        abst = soup.find('div',class_='field-name-field-paper-description')
        if not abst:
            LOG.warn("no abstract in data")
        else:
            abstract = abst.find('div' , class_='field-item odd').text

        bib_text = soup.find('div', class_='bibtex-text-entry')
        if bib_text:
            bib_text = bib_text.text

        bib_dict={}
        if not bib_text:
            LOG.warn("no bibtext in metadata")
        else:
            bib_database = bibtexparser.loads(bib_text)
            bib_dict = bib_database.entries[0]
            
        affiliations = []
        org_dict = {}

        try:
            author_list = soup.find('div', class_='field-name-field-paper-people-text').\
              find('div' , class_='field-item odd').\
              find('p').text.split(';')
            for i in author_list:
                author = i.split(',')
                (org_name,country) = (None,None)
                offset = None
                if len(author) == 3:
                    (org_name,country) = (author[1].strip(),author[2].strip())
                    offset = 2
                else:
                    org_name = author[-1].strip()
                    offset = 1
                # Sometimes USENIX stuffs extra stuff after the author list,
                # like distinguished paper winner.
                newline_idx = org_name.find("\n")
                if newline_idx > 0:
                    org_name = org_name[:newline_idx]
                if org_name in org_dict:
                    org = org_dict[org_name]
                else:
                    org = Organization(name=org_name, type="Institution",
                                       country=country)
                    org_dict[org_name] = org
                    for a in range(len(author) - offset):
                        if author[a].startswith(" and "):
                            names = author[a].split()
                            person = Person(name=names[1].strip())
                            affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=person,org=org),roles="Author"))
                        else:
                            person = Person(name=author[a].strip())
                            affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=person,org=org),roles="Author"))
        except:
            LOG.warning("failed to parse author list")
            LOG.exception(sys.exc_info()[1])
        if not affiliations:
            if('author' in bib_dict):
                authors = bib_dict['author'].split('and')
                for a in authors:
                    affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=Person(name=a.strip())),roles="Author"))
            else:
                LOG.warn("no authors in metadata")

        meta_data = {}
        if 'isbn' in bib_dict:
            meta_data['ISBN'] = bib_dict['isbn']
        if 'year' in bib_dict:
            meta_data['year'] = bib_dict['year']
        if 'publisher' in bib_dict:
            meta_data['publisher'] = bib_dict['publisher']
        if 'pages' in bib_dict:
            meta_data['page'] = bib_dict['pages']

        verbatim_metadata_names = [
            "collection-title", "container-title", "call-number", "event-place",
            "ISBN", "number-of-pages", "page", "publisher", "publisher-place", 'year' ]
        metadata = list()
        for vmn in verbatim_metadata_names:
            if not vmn in meta_data:
                continue
            metadata.append(ArtifactMetadata(name=vmn, value=str(meta_data[vmn])))

        artifact_badges = []
        evaluation_badge = soup.find('div', class_='field-name-field-artifact-evaluated')
        if evaluation_badge:
            evaluation_badge_link = evaluation_badge.find('img')['src']
            metadata.append(ArtifactMetadata(
                        name="badge",value=str(evaluation_badge_link), type="text/json",
                        source="usenix"))
            badge_object = self.session.query(Badge).\
              filter(Badge.image_url == evaluation_badge_link).\
              filter(Badge.verified == True).first()
            if badge_object:
                artifact_badges.append(ArtifactBadge(badge=badge_object))

        presentation_video= soup.find('div', class_='embedded-video')
        if presentation_video:
            presentation_video_link = presentation_video.find('iframe')['src']
            parsed_url = urlparse(presentation_video_link)
            if not parsed_url.scheme:
                presentation_video_link = "https:" + presentation_video_link
            metadata.append(ArtifactMetadata(
                        name="presentation_video", value=str(presentation_video_link), type="text/json",
                        source="usenix"))

        artifact_files = []
        presentation_pdf = soup.find('div', class_='field-name-field-presentation-pdf')
        if presentation_pdf:
            presentation_pdf_link = presentation_pdf.find('a')['href']
            path = urlparse(presentation_pdf_link).path
            ext = os.path.splitext(path)
            typ = ext[1][1:]
            name = ext[0].split('/')[-1]+ext[1]
            artifact_files.append(ArtifactFile(
                        name=name, url=presentation_pdf_link, filetype="application/"+typ))
   
        presentation_slides= soup.find('div', class_ = 'field-name-field-paper-slides-file')
        if presentation_slides:
            presentation_slides_link = presentation_slides.find('a')['href']
            path = urlparse(presentation_slides_link).path
            ext = os.path.splitext(path)
            typ = ext[1][1:]
            name = ext[0].split('/')[-1]+ext[1]
            artifact_files.append(ArtifactFile(
                        name=name, url=presentation_slides_link, filetype="application/"+typ))

        #  Adding venue support
        artifact_venues = []
        s = 1
        for i in range(len(url)-1,-1,-1):
            if(url[i] == "/"):
                s+=1
            if(s == 2):
                tmp = url[:i]
        LOG.debug("candidate venue URL: %r", tmp)

        recurring_venue_object = None
        venue_object = self.session.query(Venue).\
            filter(Venue.url == tmp).\
            filter(Venue.verified == True).first()
        if venue_object:
            artifact_venues.append(ArtifactVenue(venue=venue_object))
        else:
            venue_page = requests.get(tmp)
            venue_soup = bs4.BeautifulSoup(venue_page.content, 'html.parser')

            value = dict(url=tmp, type="conference", verified=False)
            
            if 'ISBN' in meta_data:
                value['isbn'] = meta_data['ISBN']
            try:
                venue_title = venue_soup.find('div' , class_="field-pseudo-field field-pseudo-field--pseudo-host-title")
                value['title'] = venue_title.find('h2').text
            except:
                LOG.warn("failed to extract venue title")
                LOG.exception(sys.exc_info()[1])
            try:
                venue_abbrev = venue_soup.find("meta", {"property": "og:title"})
                venue_abbrev = venue_abbrev.get("content")
                value["abbrev"] = venue_abbrev
            except:
                LOG.warn("failed to extract venue abbreviated title")
                LOG.exception(sys.exc_info()[1])
            try:
                venue_desc = venue_soup.find("meta", {"property": "og:description"})
                venue_desc = venue_desc.get("content")
                value["description"] = venue_desc
            except:
                LOG.warn("failed to extract venue description")
                LOG.exception(sys.exc_info()[1])
            try:
                date = venue_soup.find('div' , class_="field field-name-field-date-text field-type-text field-label-hidden")
                date = date.find('div',class_="field-item odd").text
                if date:
                    value['year'] = date.split(',')[1].strip()
                    value['month'] = date.split(' ')[0].strip()
                    days = date.split(',')[0].split(' ')[1].split("-")
                    value['start_day'] = days[0][0:2]
                    value['end_day'] = days[0][3:5]
            except:
                LOG.warn("failed to extract venue date")
                LOG.exception(sys.exc_info()[1])

            try:
                loc = venue_soup.find('div' , class_="field field-name-field-address-text field-type-text field-label-hidden")
                if loc:
                    loc = loc.find('div',class_="field-item odd").text
                    value['location'] = loc
            except:
                LOG.warn("failed to extract venue location")
                LOG.exception(sys.exc_info()[1])

            venue_index_url = venue_soup.find(
                "a", {"href" : lambda x: x and x.startswith("https://www.usenix.org/conferences/byname/")})
            if venue_index_url:
                venue_index_url = venue_index_url.get("href")
                venue_index_page = requests.get(venue_index_url)

                recurring_venue_object = self.session.query(RecurringVenue).\
                    filter(RecurringVenue.url == venue_index_url).\
                    filter(RecurringVenue.verified == True).first()

                if recurring_venue_object:
                    LOG.debug("using existing RecurringVenue %r",
                              recurring_venue_object)
                else:
                    rvalues = dict(type="conference",url=venue_index_url)

                    venue_index_soup = bs4.BeautifulSoup(
                        venue_index_page.content, 'html.parser')

                    rabbrev = None
                    try:
                        rabbrev = venue_index_soup.find(
                            "h1", {"id": "page-title"}).text
                    except:
                        LOG.warn("failed to extract short name, try 1")
                        LOG.exception(sys.exc_info()[1])
                        try:
                            rabbrev = venue_index_soup.head.title.text.split(" | ")[0]
                        except:
                            LOG.warn("failed to extract short name, try 2")
                            LOG.exception(sys.exc_info()[1])
                    if rabbrev:
                        # We don't like slapping Symposia on all the short
                        # names.
                        rabbrev = rabbrev.replace(" Symposia","")
                        rvalues["abbrev"] = rabbrev

                    # Use the Venue long title and assume USENIX title style
                    # (NN(th|rd|nd|...) ) to extract a more pleasing long
                    # RecurringVenue name than USENIX really gives.
                    rtitle = value["title"]
                    if rtitle[0].isdigit() and rtitle.find(" ") > 0:
                        rtitle = " ".join(rtitle.split(" ")[1:])
                        rvalues["title"] = rtitle

                    recurring_venue_object = RecurringVenue(**rvalues)

            venue_object = Venue(
                **value, recurring_venue=recurring_venue_object)
            artifact_venues.append(ArtifactVenue(venue=venue_object))

        return Artifact(
            type="publication",url=url,title=title,description=abstract,
            name=title,ctime=datetime.datetime.now(),ext_id=url,
            owner=self.owner_object,importer=self.importer_object,
            tags=[],meta=metadata,files=artifact_files,affiliations=affiliations,
            badges=artifact_badges,venues=artifact_venues)
