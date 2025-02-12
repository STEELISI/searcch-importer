from future.utils import raise_from
import sys
import six
import logging
import time
import dateutil.parser
import datetime
from urllib.parse import urlparse
import bs4
import json
import requests
import ast

from searcch.importer.importer import BaseImporter
from searcch.importer.db.model import (
    Artifact,ArtifactFile,ArtifactMetadata,ArtifactRelease,User,Person,
    Importer,Affiliation,ArtifactAffiliation,Badge,ArtifactBadge,
    RecurringVenue,Venue,ArtifactVenue)

LOG = logging.getLogger(__name__)

def jsonify(data):
    my_dict = ast.literal_eval(data)
    first = my_dict['items'][0]
    doi=""
    for k in first.keys():
        doi=k
        break
    json_string = json.dumps(first[doi])
    return json_string

class AcmDigitalLibraryImporter(BaseImporter):
    """Provides an ACM DL DOI Importer."""

    name = "acm_dl"
    version = "0.1"

    @classmethod
    def _extract_doi(cls,url,session=None):
        try:
            if not session:
                session = requests.session()
            urlobj = urlparse(url)
            #
            # The ACM DL has added a nasty chain of redirects through
            # Cloudflare to get cookies set correctly.  None of the python
            # urllibs (urllib, urllib3, requests) can handle it.  The chain is
            # doi.org -> dl.acm.org -> dl.acm.org?cookieSet=1 -> dl.acm.org,
            # and all urllibs hang until some kind of timeout or 403.
            #
            # So instead of actually following the redirects, we just glue the
            # doi.org path onto a dl.acm.org URL.  Don't know if this will work
            # in all cases, but any other solution involves custom redirect
            # handling in one of the urllib libraries, and I'm not even sure
            # what they are all getting goofed up on.  In the 403 case, you
            # would perhaps guess that they are dropping the cloudflare cookie,
            # or maybe that redirect #4 after the cookieSet redirect (#3)
            # (which identical location was already sent in #2) is causing a
            # loop detection (but that should result in exception).
            #
            if urlobj.netloc == "doi.org":
                res = None
                try:
                    res = session.get("https://dl.acm.org/doi" + urlobj.path)
                    if res.status_code == requests.codes.ok:
                        return (res,urlobj.path[1:])
                except:
                    pass
            res = session.get(url,timeout=30)
            urlobj = urlparse(res.url)
            if urlobj.netloc == "dl.acm.org":
                if urlobj.path.startswith("/doi/abs/"):
                    return (res,urlobj.path[9:])
                if urlobj.path.startswith("/doi/"):
                    return (res,urlobj.path[5:])
        except BaseException:
            LOG.exception(sys.exc_info()[1])
        return (None,None)

    @classmethod
    def can_import(cls,url):
        """Checks to see if this URL is a doi.org or dl.acm.org/doi URL."""
        (res,doi) = cls._extract_doi(url)
        if res and doi:
            return True
        return False

    def import_artifact(self,candidate):
        """Imports an artifact from the ACM Digital Library and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from ACM Digital Library" % (url,))
        session = requests.session()
        (res,doi) = self.__class__._extract_doi(url,session=session)

        firstpage = res.content
        newurl = res.url
        res = session.post(
            "https://dl.acm.org/action/exportCiteProcCitation",
            data={"dois":doi,
                  "targetFile":"custom-bibtex","format":"bibTex"})
        res.raise_for_status()
        LOG.debug("ACM record: %r",res.json())
        j = res.json()["items"][0][doi]
        if "DOI" in j and j["DOI"] != doi:
            doi = j["DOI"]

        title = name = j.get("title")
        containerTitle = j.get("container-title")
        print("Title ", title, " container Title ", containerTitle)
        
        if not title:
            raise Exception("no title ACM metadata")
        
        description = j.get("abstract")
        if not description:
            LOG.warning("%s (%s) missing abstract",newurl,url)

        authors = []
        for a in j.get("author",[]):
            aname = "%s %s" % (a.get("given",""),a.get("family",""))
            aname = aname.strip() or None
            email = a.get("email",None)
            if not aname and not email:
                raise Exception("missing author name and email address")
            authors.append(Person(email=email,name=aname))
        affiliations = []
        for person in authors:
            LOG.debug("adding author %r",person)
            affiliations.append(ArtifactAffiliation(affiliation=Affiliation(person=person),roles="Author"))

        metadata = list()
        metadata.append(ArtifactMetadata(
            name="doi",value=doi,source="acm_dl"))
        if "original-date" in j \
          and "date-parts" in j["original-date"] \
          and isinstance(j["original-date"]["date-parts"],list) \
          and len(j["original-date"]["date-parts"]) == 3:
            [year,month,day] = j["original-date"]["date-parts"]
            metadata.append(ArtifactMetadata(
                name="ctime",value="%(d)-%(02d)-%(02d)T00:00:00" % (year,month,day),
                source="acm_dl"))
        verbatim_metadata_names = [
            "collection-title","container-title","call-number","event-place",
            "ISBN","number-of-pages","page","publisher","publisher-place" ]
        for vmn in verbatim_metadata_names:
            if not vmn in j:
                continue
            metadata.append(ArtifactMetadata(
                name=vmn,value=str(j[vmn]),source="acm_dl"))
        metadata.append(ArtifactMetadata(
            name="acm_full_citation",value=json.dumps(j),
            source="acm_dl",type="text/json"))

        soup = bs4.BeautifulSoup(firstpage,"lxml")

        # See if we can extract badge metadata.
        elm = None
        try:
            elm = soup.find(name="span",attrs={"class":"badges"})
        except:
            LOG.debug("no identifiable badge info")
            LOG.exception(sys.exc_info()[1])
        artifact_badges = []
        if elm:
            try:
                badges = elm.findAll(
                    name="a",attrs={"class":"img-badget"})
                for b in badges:
                    badge_url = b.get("href")
                    badge_object = self.session.query(Badge).\
                      filter(Badge.url == badge_url).\
                      filter(Badge.verified == True).first()
                    if badge_object:
                        artifact_badges.append(ArtifactBadge(badge=badge_object))
                    value = dict(
                        title=b.get("data-title"),
                        url=badge_url)
                    u = urlparse(badge_url)
                    if u and u.fragment:
                        value["shortname"] = u.fragment
                    value = json.dumps(value)
                    metadata.append(ArtifactMetadata(
                        name="badge",value=value,type="text/json",
                        source="acm_dl"))
            except:
                LOG.warn("failed to scrape existing badge info")
                LOG.exception(sys.exc_info()[1])

        record_url = j.get("URL",newurl)

        # Extract venue metadata.  First, extract just enough to match an
        # existing Venue.  If necessary, continue to scrape to construct
        # Venue and RecurringVenue.
        venue_url = None
        recurring_venue_url = None
        artifact_venue = []
        venue_type = "other"
        try:
            nav = soup.find('nav',attrs={"class":"article__breadcrumbs separator"})
            if nav:
                tmp  = nav.findAll('a')
                typ = tmp[1]["href"]
                if typ == "/conferences":
                    venue_type = "conference"
                elif typ == "/journals":
                    venue_type = "journal"
                elif typ == "/magazines":
                    venue_type = "magazine"
                if len(tmp) > 4:
                    loc = tmp[4]["href"]
                    venue_url = "https://dl.acm.org" + loc
                if len(tmp) > 2:
                    loc = tmp[2]["href"]
                    recurring_venue_url = "https://dl.acm.org" + loc
        except:
            LOG.warn("failed to extract initial venue metadata")
            LOG.exception(sys.exc_info()[1])

        if venue_url:
            venue_object = self.session.query(Venue).\
                filter(Venue.url  == venue_url).\
                filter(Venue.verified == True).first()
            if venue_object:
                print("Appended existing venue object")
                artifact_venue.append(ArtifactVenue(venue=venue_object))
            else:
                vvalues = dict(url=venue_url,type=venue_type,verified=False,
                               title=containerTitle,
                               publisher_url=venue_url)
                print("Created new venue object with ", containerTitle)
                if "ISBN" in j:
                    vvalues["isbn"] = j["ISBN"]
                if "ISSN" in j:
                    vvalues["issn"] = j["ISSN"]
                if "collection-title" in j:
                    vvalues["abbrev"]  = j["collection-title"]
                if "issue" in j:
                    vvalues["issue"] = j["issue"]
                if "publisher-place" in j:
                    vvalues["publisher_location"] = j["publisher-place"]
                if "publisher" in j:
                    vvalues["publisher"] = j["publisher"]
                if "volume" in j:
                    vvalues["volume"] = j["volume"]
                venue_object = Venue(**vvalues)
                artifact_venue.append(ArtifactVenue(venue=venue_object))

                # Also try to extract a RecurringVenue object.
                if recurring_venue_url:
                    print("Recurring venue url ", recurring_venue_url)
                    rvalues = dict(
                        type=venue_object.type, verified=False,
                        url=recurring_venue_url)
                    rpage = session.get(recurring_venue_url)
                    rsoup = bs4.BeautifulSoup(rpage.content, 'html.parser')
                    telm = rsoup.find("h1", {"class": "title lines-1"})
                    selm = rsoup.find("p", {"class": "banner__text"})
                    if telm:
                        rvalues["abbrev"] = telm.text
                    if selm:
                        rvalues["title"] = selm.text
                    recurring_venue = RecurringVenue(**rvalues)
                    venue_object.recurring_venue = recurring_venue

        # Check to see if a PDF is available.  Note that this will fail if the
        # source IP address running this process does not have full access to
        # the DL.
        pdf_url = "https://dl.acm.org/doi/pdf/%s" % (doi,)
        res = session.head(pdf_url)
        files = []
        if res.status_code == requests.codes.ok:
            filename = "%s.pdf" % (doi,)
            idx = doi.rfind("/")
            if idx > 0:
                filename = "%s.pdf" % (doi[idx+1:],)
            files.append(
                ArtifactFile(url=pdf_url,name=filename,filetype="application/pdf"))
        else:
            LOG.info("failed to HEAD the pdf (%r)",res.status_code)

        return Artifact(
            type="publication",url=record_url,title=title,description=description,
            name=name,ctime=datetime.datetime.now(),ext_id=doi,
            owner=self.owner_object,importer=self.importer_object,
            meta=metadata,affiliations=affiliations,
            files=files,badges=artifact_badges,venues=artifact_venue)
