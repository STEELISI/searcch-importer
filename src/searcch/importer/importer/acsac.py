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
import json

from searcch.importer.importer import BaseImporter
from searcch.importer.importer.acm_dl import AcmDigitalLibraryImporter
from searcch.importer.db.model import (
    Artifact, ArtifactFile, ArtifactMetadata, ArtifactRelease, User, Person,
    Importer, Affiliation, ArtifactAffiliation, ArtifactTag, Organization,
    Badge, ArtifactBadge, RecurringVenue, Venue, ArtifactVenue,
    CandidateArtifact, CandidateArtifactRelationship)
from searcch.importer.exceptions import MissingMetadataError

LOG = logging.getLogger(__name__)

class ACSACImporter(BaseImporter):
    """Provides an ACSAC Importer."""

    name = "acsac"
    version = "0.1"
    acsac_default_desc = "The Annual Computer Security Applications Conference (ACSAC) brings together cutting-edge researchers, with a broad cross-section of security professionals drawn from academia, industry, and government, gathered to present and discuss the latest security results and topics. With peer reviewed technical papers, invited talks, panels, national interest discussions, and workshops, ACSAC continues its core mission of investigating practical solutions for computer and network security technology."

    @classmethod
    def can_import(cls, url, session=None):
        """Checks to see if this URL is an acsac.org or openconf.org/acsac* URL."""
        try:
            if not session:
                session = requests.session()
            res = requests.get(url)
            urlobj = urlparse(res.url)
            if urlobj.netloc.endswith("acsac.org") \
              or (urlobj.netloc.endswith("openconf.org") \
                  and urlobj.path.startswith("/acsac")):
                return (res.url, urlobj, session)
        except BaseException:
            return None

    def import_artifact(self, candidate):
        """Imports an artifact from ACSAC and returns an Artifact, or throws an error."""
        url = candidate.url
        LOG.debug("importing '%s' from ACSAC " % (url,))
        urlobj = urlparse(url)
        year = None
        umatch = re.match("^\/((20\d\d)|acsac(20\d\d))\/.*$", urlobj.path)
        if umatch:
            year = umatch.group(1).replace("acsac","")
        page = requests.get(url)
        soup = bs4.BeautifulSoup(page.content, 'html.parser')

        elm = soup.find('div',id="oc_program_summary_main")
        if not elm:
            raise MissingMetadataError("cannot extract title")
        title_elm = elm.find('h1')
        if not title_elm:
            raise MissingMetadataError("cannot extract title")
        title = title_elm.text
        LOG.debug("importing '%s' from ACSAC " % (url,))

        desc = None
        desc_elm = title_elm.findNextSibling('p')
        if desc_elm:
            desc = desc_elm.text

        affiliations = []
        authors_elm = elm.find('div',id="oc_program_summary_authors")
        if authors_elm:
            for p in authors_elm.findAll('p'):
                pname = p.find('strong').text
                orgname = p.text.replace(pname,"").strip() or None
                org = None
                if orgname:
                    org = Organization(type="Institution", name=orgname)
                p = Person(name=pname)
                aff = Affiliation(person=p,org=org)
                aaff = ArtifactAffiliation(
                    affiliation=aff,roles="Author")
                affiliations.append(aaff)

        files = []
        paper_url = None
        for p in elm.findAll('p'):
            p_a = p.find('a')
            if not p_a:
                continue
            # XXX: need to call in the acm_dl importer to annotate this
            # artifact with this URL.
            if p_a.text.startswith("Paper"):
                paper_url = p_a.get("href")
            elif p_a.text.startswith("Slides"):
                furl = p_a.get("href")
                path = urlparse(furl).path
                ext = os.path.splitext(path)
                typ = ext[1][1:]
                name = ext[0].split('/')[-1]+ext[1]
                files.append(ArtifactFile(
                    name=name, url=furl, filetype="application/"+typ))
            elif p_a.text.startswith("Video"):
                files.append(ArtifactFile(
                    url=p_a.get("href"), filetype="application/video"))

        venues = []
        if year:
            vurl = "https://www.acsac.org/%s" % (year,)
            vpage = requests.get(vurl)
            vsoup = bs4.BeautifulSoup(vpage.content, 'html.parser')
            vdesc = None
            vdesc_elm = vsoup.find("div", class_="acsac-prose")
            if vdesc_elm:
                vdp_elm = vdesc_elm.find("p")
                if vdp_elm:
                    vdesc = vdp_elm.text.strip()
            if not vdesc:
                vdesc = self.__class__.acsac_default_desc

            vvalues = dict(
                type="conference", url=vurl, abbrev="ACSAC %s" % (year,),
                title="Annual Computer Security Applications Conference (ACSAC) %s" % (year,),
                description=vdesc, year=int(year))

            vloc_elm = vsoup.find("div", class_="acsac-logo")
            if vloc_elm:
                vloc_elm = vloc_elm.find("span")
            if vloc_elm:
                vdl_match = re.match("(\w+)\s+(\d+)\s*-\s*(\d+),\s+(20\d\d)\s+•\s+(.+)", vloc_elm.text)
                if vdl_match:
                    vvalues["start_day"] = int(vdl_match.group(2))
                    vvalues["end_day"] = int(vdl_match.group(3))
                    vvalues["location"] = vdl_match.group(5)
                    vvalues["month"] = dateutil.parser.parse(vdl_match.group(1)).month
                
            v = Venue(**vvalues)
            rv = RecurringVenue(
                url="https://www.acsac.org/", abbrev="ACSAC", type="conference",
                title="Annual Computer Security Applications Conference (ACSAC)",
                description=self.__class__.acsac_default_desc, verified=True)
            v.recurring_venue = rv
            venues.append(ArtifactVenue(venue=v))

        a = Artifact(
            type="publication",url=url,title=title,description=desc,
            ctime=datetime.datetime.now(),
            owner=self.owner_object,importer=self.importer_object,
            tags=[],meta=[],files=files,affiliations=affiliations,venues=venues)

        # Try to supplement our metadata with that from the ACM.
        aa = None
        if paper_url:
            try:
                ai = AcmDigitalLibraryImporter(self.config, self.session)
                aa = ai.import_artifact(
                    CandidateArtifact(url=paper_url,owner=self.owner_object))
            except:
                LOG.exception(sys.exc_info()[1])
        if aa:
            # Update title and description.
            if aa.title and not a.title:
                a.title = aa.title
            if aa.description and not a.description:
                a.description = aa.description

            # Update authors.
            for x in a.affiliations:
                for y in aa.affiliations:
                    if x.affiliation.person.name \
                      and x.affiliation.person.name == y.affiliation.person.name \
                      and not x.affiliation.person.email \
                      and y.affiliation.person.email:
                        x.affiliation.person.email = y.affiliation.person.email

            # Suck in metadata.
            for x in aa.meta:
                a.meta.append(x)

            # Suck in badges.
            for x in aa.badges:
                for y in a.badges:
                    if y.url == x.url:
                        continue
                    else:
                        a.badges.append(x)

            # Suck in files.
            for x in aa.files:
                a.files.append(x)

            # Update our venues.
            if aa.venues and a.venues:
                av = a.venues[0].venue
                aav = aa.venues[0].venue
                for k in ( "isbn", "issn", "issue", "volume",
                           "publisher_url", "publisher_location" ):
                    setattr(av, k, getattr(aav, k, None))

        if year:
            aurl = None
            if year in [ "2017", "2018" ]:
                aurl = "https://www.acsac.org/%s/artifacts" % (year,)
            else:
                aurl = "https://www.acsac.org/%s/program/artifacts" % (year,)
            apage = requests.get(aurl)
            if apage.ok:
                # Must use html5lib because ACSAC pages use unclosed <img>
                # tags, and that screws up the hierarchy of <li> tags for
                # pedantic parsers.
                asoup = bs4.BeautifulSoup(apage.content, 'html5lib')
                ap_elm = asoup.find("div", class_="acsac-prose")
                if not ap_elm:
                    # Hack for 2017/2018 years.
                    ap_elm = asoup.find("div", id="content")
                al_elms = []
                if ap_elm:
                    al_elms = ap_elm.findAll("li")
                al_elm = None
                for al_elm in al_elms:
                    if not al_elm.text.strip().startswith(a.title):
                        continue
                    print("text = %r" % (al_elm.text,))
                    i = 0
                    for ala_elm in al_elm.findChildren("a"):
                        i += 1
                        # Hack for 2017/2018: first <a> is to the paper.
                        if i == 1 and year in [ "2017", "2018" ]:
                            continue
                        ca = CandidateArtifact(
                            url=ala_elm.get("href"), ctime=a.ctime,
                            owner=a.owner)
                        car = CandidateArtifactRelationship(
                            artifact=a, related_candidate=ca,
                            relation="describes")
                        a.candidate_relationships.append(car)
                    break
                # Also, discover badging info.  No badges for 2017/2018.
                badge_url = None
                if al_elm:
                    ul_elm = al_elm.findParent("ul")
                    if ul_elm:
                        img_elm = ul_elm.findPrevious("img")
                        if "unctional" in img_elm.get("src") \
                          or "unctional" in img_elm.get("alt"):
                            badge_url = "https://www.acm.org/publications/policies/artifact-review-and-badging-current#functional"
                        elif "eusable" in img_elm.get("src") \
                          or "eusable" in img_elm.get("alt"):
                            badge_url = "https://www.acm.org/publications/policies/artifact-review-and-badging-current#reusable"
                if badge_url:
                    badge_object = self.session.query(Badge).\
                      filter(Badge.url  == badge_url).\
                      filter(Badge.verified == True).first()
                    if badge_object:
                        a.badges.append(ArtifactBadge(badge=badge_object))

        return a
