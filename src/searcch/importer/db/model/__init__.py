
import six
from future.utils import iteritems
import abc
import time
import hashlib
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,Integer,String,Enum,DateTime,LargeBinary,ForeignKey,UniqueConstraint,
    Float,BigInteger,Text,Boolean)
import sqlalchemy.types
from sqlalchemy.types import BINARY
from sqlalchemy.orm import relationship
import sqlalchemy.event

Base = declarative_base()

ARTIFACT_TYPES = (
    "publication", "presentation", "dataset", "software",
    "other"
)
ARTIFACT_IMPORT_TYPES = (
    "publication", "presentation", "dataset", "software",
    "other", "unknown"
)

ARTIFACT_RELATIONS = (
    "cites", "supplements", "extends", "uses", "describes",
    "requires", "processes", "produces", "indexes"
)

class FileContent(Base):
    __tablename__ = "file_content"

    id = Column(Integer, primary_key=True, autoincrement=True)
    content = Column(LargeBinary(), nullable=False)
    hash = Column(BINARY(length=32), nullable=False)
    size = Column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint("hash"),
    )

    @classmethod
    def find_existing(kls,session,content):
        d = FileContent.make_hash(content)
        return session.query(FileContent).filter(FileContent.hash == d).first()

    @classmethod
    def make_hash(kls,content):
        m = hashlib.sha256()
        m.update(content)
        d = m.digest()
        return d

    def __repr__(self):
        return "<FileContent(id=%r,hash=0x%s,size=%r)>" % (
            self.id, self.hash.hex(), self.size )

#
# Both our primary key and hash are UNIQUE.  The migration that added this
# table IGNOREs conflicts on updates.  But that means that to make inserts of
# "new" content seamless, we have to update any objects without their primary
# keys set, if there is an existing hash match.  We also calculate the hash and
# size fields if they are missing.
#
@sqlalchemy.event.listens_for(FileContent, 'before_insert')
def file_content_fixups(mapper, connection, target):
    if not target.hash:
        target.hash = FileContent.make_hash(target.content)
    if target.size is None:
        target.size = len(target.content)
    if target.id is None:
        res = connection.execute("select id from file_content where hash=:hashval",
                                 { "hashval": target.hash })
        row = res.first()
        if row:
            target.id = row["id"]

class ArtifactMetadata(Base):
    __tablename__ = "artifact_metadata"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey('artifacts.id'))
    name = Column(String(64),nullable=False)
    value = Column(String(16384),nullable=False)
    type = Column(String(256),nullable=True)
    source = Column(String(256),nullable=True)

    def __repr__(self):
        return "<ArtifactMetadata(artifact_id=%r,name=%r,type=%r,source=%r)>" % (
            self.artifact_id,self.name,self.type,self.source)

class ArtifactTag(Base):
    __tablename__ = "artifact_tags"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey('artifacts.id'))
    tag = Column(String(256),nullable=False)
    source = Column(String(256),nullable=False,default="")

    __table_args__ = (
        UniqueConstraint("tag","artifact_id","source"),)

    def __repr__(self):
        return "<ArtifactTag(artifact_id=%r,tag=%r,source=%r)>" % (
            self.artifact_id,self.tag,self.source)

class ArtifactFile(Base):
    __tablename__ = "artifact_files"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    url = Column(String(512),nullable=False)
    name = Column(String(512),nullable=True)
    filetype = Column(String(128),nullable=False)
    file_content_id = Column(Integer, ForeignKey("file_content.id"))
    size = Column(BigInteger())
    mtime = Column(DateTime)

    file_content = relationship("FileContent",uselist=False)
    members = relationship("ArtifactFileMember",uselist=True)

    __table_args__ = (
        UniqueConstraint("artifact_id","url"),)

    def __repr__(self):
        return "<ArtifactFile(id=%r,artifact_id=%r,file_content_id=%r,url=%r,name=%r,size=%r,mtime=%r)>" % (
            self.id,self.artifact_id,self.file_content_id,self.url,self.name,self.size,
            self.mtime.isoformat() if self.mtime else "")

class ArtifactFileMember(Base):
    __tablename__ = "artifact_file_members"

    id = Column(Integer,primary_key=True,autoincrement=True)
    parent_file_id = Column(Integer,ForeignKey("artifact_files.id"),nullable=False)
    pathname = Column(String(512),nullable=False)
    html_url = Column(String(512))
    download_url = Column(String(512))
    name = Column(String(512))
    filetype = Column(String(128),nullable=False)
    file_content_id = Column(Integer, ForeignKey("file_content.id"))
    size = Column(BigInteger())
    mtime = Column(DateTime)
    file_content = relationship("FileContent",uselist=False)
    parent_file = relationship("ArtifactFile",uselist=False,viewonly=True)

    __table_args__ = (
        UniqueConstraint("parent_file_id","pathname"),)

    def __repr__(self):
        return "<ArtifactFileMember(id=%r,file_content_id=%r,pathname=%r,name=%r,html_url=%r,size=%r,mtime=%r)>" % (
            self.id,self.file_content_id,self.pathname,self.name,self.html_url,self.size,
            self.mtime.isoformat() if self.mtime else "")

class Importer(Base):
    __tablename__ = "importers"

    id = Column(Integer,primary_key=True)
    name = Column(String(32),nullable=False)
    version = Column(String(32))

    __table_args__ = (
        UniqueConstraint("name","version"),)

    def __repr__(self):
        return "<Importer(id=%r,name=%r,version=%r)>" % (self.id,self.name,self.version)

class Exporter(Base):
    __tablename__ = "exporters"

    id = Column(Integer,primary_key=True)
    name = Column(String(32),nullable=False)
    version = Column(String(32))

    __table_args__ = (
        UniqueConstraint("name","version"),)

    def __repr__(self):
        return "<Exporter(id=%r,name=%r,version=%r)>" % (self.id,self.name,self.version)

class Extractor(Base):
    __tablename__ = "extractors"

    id = Column(Integer,primary_key=True)
    name = Column(String(32),nullable=False)
    version = Column(String(32))

    __table_args__ = (
        UniqueConstraint("name","version"),)

    def __repr__(self):
        return "<Extractor(id=%r,name=%r,version=%r)>" % (self.id,self.name,self.version)

class License(Base):
    __tablename__ = "licenses"

    id = Column(Integer,primary_key=True,autoincrement=True)
    short_name = Column(String(64))
    long_name = Column(String(512), nullable=False)
    url = Column(String(1024), nullable=False)
    verified = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("long_name", "url", "verified"),)

    def __repr__(self):
        return "<License(id=%r,long_name=%r,short_name=%r,url=%r,verified=%r)>" % (
            self.id, self.long_name, self.short_name, self.url, self.verified)

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer,primary_key=True,autoincrement=True)
    name = Column(String(1024),nullable=True)
    email = Column(String(256),nullable=True)
    meta = relationship("PersonMetadata",uselist=True)

    def __repr__(self):
        return "<Person(id=%r,name=%r,email=%r)>" % (
            self.id,self.name,self.email)

class PersonMetadata(Base):
    __tablename__ = "person_metadata"

    id = Column(Integer,primary_key=True,autoincrement=True)
    person_id = Column(Integer,ForeignKey("persons.id"),nullable=False)
    name = Column(String(64),nullable=False)
    value = Column(String(1024),nullable=False)
    source = Column(String(256),nullable=True)

    __table_args__ = (
        UniqueConstraint("person_id","name"),)

    def __repr__(self):
        return "<PersonMetadata(person_id=%r,name=%r)>" % (
            self.id,self.name)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer,primary_key=True,autoincrement=True)
    person_id = Column(Integer,ForeignKey("persons.id"),nullable=False)
    person = relationship("Person",uselist=False)

    __table_args__ = (
        UniqueConstraint("person_id"),)

    def __repr__(self):
        return "<User(id=%r,person_id=%r)>" % (
            self.id,self.person_id)

class UserAuthorization(Base):
    __tablename__ = "user_authorizations"

    user_id = Column(Integer,ForeignKey("users.id"),primary_key=True)
    roles = Column(
        Enum("Uploader","Editor","Curator",
             name="user_authorization_role_enum"),
        nullable=False)
    scope = Column(
        Enum("Org","Artifact",
             name="user_authorization_scope_enum"),
        nullable=False)
    # A NULL scoped_id is a wildcard, meaning everything.
    scoped_id = Column(Integer,nullable=True)

    __table_args__ = (
        UniqueConstraint("user_id","roles","scope","scoped_id"),)

    def __repr__(self):
        return "<UserAuthorization(user_id=%r,roles=%r,scope=%r,scoped_id=%r)>" % (
            self.user_id,self.roles,self.scope,str(self.scoped_id))

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer,primary_key=True,autoincrement=True)
    name = Column(String(1024),nullable=False)
    type = Column(
        Enum("Institution","Company","Institute","ResearchGroup","Sponsor","Other",
             name="organization_enum"),
        nullable=False)
    url = Column(String(512),nullable=True)
    state = Column(String(64),nullable=True)
    country = Column(String(64),nullable=True)
    latitude = Column(Float(),nullable=True)
    longitude = Column(Float(),nullable=True)
    address = Column(String(512),nullable=True)
    verified = Column(Boolean,nullable=False,default=False)

    def __repr__(self):
        return "<Organization(name=%r,type=%r,url=%r,verified=%r)>" % (
            self.name,self.type,self.url,self.verified)

class Affiliation(Base):
    __tablename__ = "affiliations"

    id = Column(Integer,primary_key=True,autoincrement=True)
    person_id = Column(Integer,ForeignKey("persons.id"),nullable=False)
    org_id = Column(Integer,ForeignKey("organizations.id"),nullable=True)

    person = relationship("Person",uselist=False)
    org = relationship("Organization",uselist=False)

    __table_args__ = (
        UniqueConstraint("person_id","org_id"),)

    def __repr__(self):
        return "<Affiliation(person_id=%r,org_id=%r)>" % (
            self.person_id,self.org_id)

class ArtifactAffiliation(Base):
    __tablename__ = "artifact_affiliations"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"),nullable=False)
    affiliation_id = Column(Integer,ForeignKey("affiliations.id"),nullable=False)
    roles = Column(
        Enum("Author","ContactPerson","Other",
             name="artifact_affiliation_enum"),
        nullable=False,default="Author")

    #artifact = relationship("Artifact",uselist=False)
    affiliation = relationship("Affiliation",uselist=False)

    __table_args__ = (
        UniqueConstraint("artifact_id","affiliation_id","roles"),)

    def __repr__(self):
        return "<ArtifactAffiliation(artifact_id=%r,affiliation_id=%r,roles=%r)>" % (
            self.artifact_id,self.affiliation_id,self.roles)

class RecurringVenue(Base):
    __tablename__ = "recurring_venues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(
        Enum("conference", "journal", "magazine", "newspaper", "periodical",
             "event", "other",
             name="recurring_venue_enum"),
        nullable=False)
    title = Column(String(1024), nullable=False)
    abbrev = Column(String(64))
    url = Column(String(1024), nullable=False)
    description = Column(Text)
    publisher_url = Column(String(1024), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)

    recurrences = relationship("Venue", uselist=True, viewonly=True)

    def __repr__(self):
        return "<RecurringVenue(type=%r,title=%r,url=%r,verified=%r)>" % (
            self.type, self.title, self.url, self.verified)

class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(
        Enum("conference", "journal", "magazine", "newspaper", "periodical",
             "event", "other",
             name="venue_enum"),
        nullable=False)
    title = Column(String(1024), nullable=False)
    abbrev = Column(String(64))
    url = Column(String(1024), nullable=False)
    description = Column(Text)
    location = Column(String(1024))
    year = Column(Integer)
    month = Column(Integer)
    start_day = Column(Integer)
    end_day = Column(Integer)
    publisher = Column(String(1024))
    publisher_location = Column(String(1024))
    publisher_url = Column(String(1024))
    isbn = Column(String(128))
    issn = Column(String(128))
    doi = Column(String(128))
    volume = Column(Integer)
    issue = Column(Integer)
    verified = Column(Boolean, nullable=False, default=False)
    recurring_venue_id = Column(Integer,ForeignKey("recurring_venues.id"),nullable=True)

    recurring_venue = relationship("RecurringVenue",uselist=False)

    def __repr__(self):
        return "<Venue(type=%r,title=%r,url=%r,verified=%r)>" % (
            self.type, self.title, self.url, self.verified)

class ArtifactVenue(Base):
    __tablename__ = "artifact_venues"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"),nullable=False)
    venue_id = Column(Integer,ForeignKey("venues.id"),nullable=False)
    venue = relationship("Venue", uselist=False)
    __table_args__ = (
        UniqueConstraint("artifact_id","venue_id"),)
        
    def __repr__(self):
        return "<ArtifactVenue(artifact_id=%r,venue_id=%r)>" % (
            self.artifact_id, self.venue_id)

class Badge(Base):
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1024), nullable=False)
    url = Column(String(1024), nullable=False)
    image_url = Column(String(1024))
    description = Column(Text)
    version = Column(String(256), nullable=False, default="")
    organization = Column(String(1024), nullable=False)
    venue = Column(String(1024))
    issue_time = Column(DateTime)
    doi = Column(String(128))
    verified = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("title", "url", "version", "organization"),)

    def __repr__(self):
        return "<Badge(title=%r,url=%r,version=%r,organization=%r,venue=%r,verified=%r)>" % (
            self.title, self.url, self.version, self.organization, self.venue, self.verified)

class ArtifactBadge(Base):
    __tablename__ = "artifact_badges"

    id = Column(Integer, primary_key=True, autoincrement=True)
    artifact_id = Column(Integer, ForeignKey(
        "artifacts.id"), nullable=False)
    badge_id = Column(Integer, ForeignKey(
        "badges.id"), nullable=False)

    badge = relationship("Badge", uselist=False)

    __table_args__ = (
        UniqueConstraint("artifact_id", "badge_id"),)

    def __repr__(self):
        return "<ArtifactBadge(artifact_id=%r,badge_id=%r)>" % (
            self.artifact_id, self.badge_id)

class ArtifactFunding(Base):
    __tablename__ = "artifact_funding"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"),nullable=False)
    funding_org_id = Column(Integer,ForeignKey("organizations.id"),nullable=False)
    grant_number = Column(String(128),nullable=False)
    grant_url = Column(String(256),nullable=True)
    grant_title = Column(String(1024),nullable=True)

    organization = relationship("Organization",uselist=False)

    __table_args__ = (
        UniqueConstraint("artifact_id","funding_org_id","grant_number"),)

class ArtifactCuration(Base):
    __tablename__ = "artifact_curations"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    time = Column(DateTime,nullable=False)
    notes = Column(Text)
    opdata = Column(Text,nullable=False)
    curator_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    curator = relationship("User",uselist=False)

    def __repr__(self):
        return "<ArtifactCuration(id=%r,artifact_id=%r,time=%r,curator=%r)>" % (
            self.id,self.artifact_id,self.time.isoformat(),
            self.curator)

class ArtifactRelease(Base):
    __tablename__ = "artifact_releases"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    url = Column(String(512))
    author_login = Column(String(128))
    author_email = Column(String(128))
    author_name = Column(String(128))
    tag = Column(String(256))
    title = Column(String(1024))
    time = Column(DateTime)
    notes = Column(Text)

    def __repr__(self):
        return "<ArtifactRelease(id=%r,artifact_id=%r,url=%r,title=%r,author_email=%r,time=%r)>" % (
            self.id,self.artifact_id,self.url,self.title,self.author_email,
            self.time.isoformat() if self.time else "")

class ArtifactPublication(Base):
    __tablename__ = "artifact_publications"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    time = Column(DateTime,nullable=False)
    notes = Column(Text)
    publisher_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    publisher = relationship("User",uselist=False)

    def __repr__(self):
        return "<ArtifactPublication(id=%r,artifact_id=%r,time=%r,publisher=%r)>" % (
            self.id,self.artifact_id,self.time.isoformat(),self.publisher)

class ArtifactRelationship(Base):
    """The ArtifactRelationship class declares a relationship between two SEARCCH artifacts."""

    __tablename__ = "artifact_relationships"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    relation = Column(Enum(
        *ARTIFACT_RELATIONS,
        name="artifact_relationship_enum"))
    related_artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    related_artifact = relationship("Artifact",uselist=False,
                                    foreign_keys=[related_artifact_id])

    __table_args__ = (
        UniqueConstraint("artifact_id","relation","related_artifact_id"),)

    def __repr__(self):
        return "<ArtifactRelationship(id=%r,artifact_id=%r,relation=%r,related_artifact_id=%r)>" % (
            self.id,self.artifact_id,self.relation,self.related_artifact_id)

class Artifact(Base):
    """The Artifact class provides an internal model of a SEARCCH artifact.  An artifact is an entity that may be added to or edited within the SEARCCH Hub."""

    __tablename__ = "artifacts"

    id = Column(Integer,primary_key=True,autoincrement=True)
    #uuid = Column(String(64),primary_key=True)
    type = Column(Enum(*ARTIFACT_TYPES,name="artifact_enum"))
    url = Column(String(1024),nullable=False)
    ext_id = Column(String(512),nullable=True)
    title = Column(Text(),nullable=False)
    name = Column(String(1024),nullable=True)
    ctime = Column(DateTime,nullable=False)
    mtime = Column(DateTime,nullable=True)
    description = Column(Text())
    meta = relationship("ArtifactMetadata")
    tags = relationship("ArtifactTag")
    files = relationship("ArtifactFile")
    license_id = Column(Integer,ForeignKey("licenses.id"),nullable=True)
    license = relationship("License",uselist=False)
    owner_id = Column(Integer,ForeignKey("users.id"),nullable=True)
    owner = relationship("User",uselist=False)
    importer_id = Column(Integer,ForeignKey("importers.id"),nullable=True)
    importer = relationship("Importer",uselist=False)
    curations = relationship("ArtifactCuration")
    publication = relationship("ArtifactPublication",uselist=False)
    releases = relationship("ArtifactRelease",uselist=True)
    affiliations = relationship("ArtifactAffiliation",uselist=True)
    relationships = relationship("ArtifactRelationship",uselist=True,
                                 foreign_keys=[ArtifactRelationship.artifact_id])
    badges = relationship("ArtifactBadge",uselist=True)
    venues = relationship("ArtifactVenue",uselist=True)
    fundings = relationship("ArtifactFunding",uselist=True)
    candidate_relationships = relationship(
        "CandidateArtifactRelationship",uselist=True)

    def __repr__(self):
        return "<Artifact(id=%r,type=%r,url=%r,ctime=%r,owner=%r)>" % (
            self.id,self.type,self.url,
            self.ctime.isoformat(),self.owner)

    def has_author(self,name=None,email=None,allow_none_match=True):
        if name == None and email == None:
            return False
        for a in self.affiliations:
            if not a.affiliation or not a.affiliation.person:
                continue
            p = a.affiliation.person
            match_name = True if (name == None and allow_none) or name == p.name else False
            match_email = True if (email == None and allow_none) or email == p.email else False
            if match_name and match_email:
                return True
        return False

    def has_tag(self,tag,source=None,ignore_case=False,allow_none_match=True):
        if not self.tags:
            return False
        for t in self.tags:
            match_tag = True if (tag == t.tag or (ignore_case and tag.lower() == t.tag.lower())) else False
            match_source = True if (source == None and allow_none_match) or source == t.source else False
            if match_tag and match_source:
                return True
        return False

    @property
    def import_session(self):
        return self.__import_session

    def set_import_session(self, import_session):
        self.__import_session = import_session

class CandidateArtifactMetadata(Base):
    __tablename__ = "candidate_artifact_metadata"

    id = Column(Integer,primary_key=True,autoincrement=True)
    candidate_artifact_id = Column(Integer,ForeignKey('candidate_artifacts.id'))
    name = Column(String(64),nullable=False)
    value = Column(String(16384),nullable=False)
    type = Column(String(256),nullable=True)
    source = Column(String(256),nullable=True)

    __table_args__ = (
        UniqueConstraint("name","candidate_artifact_id","value","type"),)

    def __repr__(self):
        return "<CandidateArtifactMetadata(candidate_artifact_id=%r,name=%r)>" % (
            self.candidate_artifact_id,self.name)

class CandidateArtifact(Base):
    """The CandidateArtifact class allows possible/recommended ("candidate"), yet-to-be-imported Artifacts to be declared.  These have not been imported, so cannot be placed in the main Artifacts table.  We also need to model possible relationships between both candidates and existing artifacts."""
    __tablename__ = "candidate_artifacts"

    id = Column(Integer,primary_key=True,autoincrement=True)
    url = Column(String(1024),nullable=False)
    ctime = Column(DateTime,nullable=False)
    mtime = Column(DateTime)
    type = Column(Enum(*ARTIFACT_TYPES,name="candidate_artifact_enum"))
    title = Column(Text())
    name = Column(Text())
    description = Column(Text())
    owner_id = Column(Integer,ForeignKey("users.id"),nullable=False)
    imported_artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    meta = relationship("CandidateArtifactMetadata")
    owner = relationship("User",uselist=False)
    imported_artifact = relationship("Artifact",uselist=False,
                                     foreign_keys=[imported_artifact_id])
    candidate_artifact_relationships = relationship(
        "CandidateArtifactRelationship",uselist=True,viewonly=True)

    def __repr__(self):
        return "<CandidateArtifact(id=%r,type=%r,url=%r,ctime=%r,owner=%r,imported_artifact_id=%r)>" % (
            self.id,self.type,self.url,
            self.ctime.isoformat(),self.owner,self.imported_artifact_id)

class CandidateArtifactRelationship(Base):
    """The CandidateArtifactRelationship class declares a relationship between an artifact and a candidate."""

    __tablename__ = "candidate_artifact_relationships"

    id = Column(Integer,primary_key=True,autoincrement=True)
    artifact_id = Column(Integer,ForeignKey("artifacts.id"))
    relation = Column(Enum(
        *ARTIFACT_RELATIONS,
        name="candidate_artifact_relationship_enum"))
    related_candidate_id = Column(Integer,ForeignKey("candidate_artifacts.id"))
    artifact = relationship("Artifact",uselist=False,viewonly=True)
    related_candidate = relationship("CandidateArtifact",uselist=False,
                                     foreign_keys=[related_candidate_id])

    __table_args__ = (
        UniqueConstraint("artifact_id","relation","related_candidate_id"),)

    def __repr__(self):
        return "<ArtifactCandidateRelationship(id=%r,artifact_id=%r,relation=%r,related_candidate_id=%r)>" % (
            self.id,self.artifact_id,self.relation,self.related_candidate_id)

class CandidateRelationship(Base):
    """The CandidateRelationship class declares a relationship between two candidate artifacts."""

    __tablename__ = "candidate_relationships"

    id = Column(Integer,primary_key=True,autoincrement=True)
    candidate_artifact_id = Column(Integer,ForeignKey("candidate_artifacts.id"))
    relation = Column(Enum(
        *ARTIFACT_RELATIONS,
        name="candidate_relationship_enum"))
    related_candidate_id = Column(Integer,ForeignKey("candidate_artifacts.id"))
    related_candidate = relationship("CandidateArtifact",uselist=False,
                                     foreign_keys=[related_candidate_id])

    __table_args__ = (
        UniqueConstraint("candidate_artifact_id","relation","related_candidate_id"),)

    def __repr__(self):
        return "<CandidateRelationship(id=%r,candidate_id=%r,relation=%r,related_candidate_id=%r)>" % (
            self.id,self.candidate_id,self.relation,self.related_candidate_id)

class ExportedObject(Base):
    """The ExportedObject class tracks system objects that have been exported.  The idea is that each object can only be exported to a single destination once without clearing its presence in this table."""

    __tablename__ = "exported_objects"

    id = Column(Integer,primary_key=True,autoincrement=True)
    object_id = Column(Integer,nullable=False)
    object_type = Column(String(256))
    ctime = Column(DateTime,nullable=False)
    exporter_id = Column(Integer,ForeignKey("exporters.id"),nullable=False)
    external_object_id = Column(Integer,nullable=False)

    exporter = relationship("Exporter",uselist=False)

    __table_args__ = (
        UniqueConstraint("object_id","object_type","exporter_id"),)

    def __repr__(self):
        return "<ExportedArtifact(id=%r,object_id=%r,ctime=%r,exporter=%r,external_object_id=%r)>" % (
            self.id,self.object_id,self.ctime.isoformat(),
            self.exporter,self.external_object_id)

class ArtifactImport(Base):
    """
    ArtifactImport represents an ongoing or completed artifact import
    session, for server-triggered imports.
    """

    __tablename__ = "artifact_imports"

    id = Column(Integer,primary_key=True,autoincrement=True)
    # NB: this is the remote ID of the artifact import; necessary if the remote
    # caller wants asynch status updates and completed artifact push instead of
    # polling.
    remote_id = Column(Integer,nullable=True)
    #remote_url = Column(String(1024),nullable=True)
    type = Column(Enum(*ARTIFACT_IMPORT_TYPES,name="artifact_import_type_enum"))
    url = Column(String(1024), nullable=False)
    importer_module_name = Column(String(256), nullable=True)
    nofetch = Column(Boolean, default=False)
    noextract = Column(Boolean, default=False)
    noremove = Column(Boolean, default=False)
    ctime = Column(DateTime, nullable=False)
    mtime = Column(DateTime, nullable=True)
    # Importer phase
    phase = Column(Enum(
        "start","validate","import","retrieve","extract","done"),
        default="start", nullable=False)
    message = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)
    bytes_retrieved = Column(Integer, default=0)
    bytes_extracted = Column(Integer, default=0)
    log = Column(Text, nullable=True)
    # Only set once status=complete and phase=done
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=True)

    artifact = relationship("Artifact", uselist=False)

    __table_args__ = (
        UniqueConstraint("remote_id","url"),)

    def __repr__(self):
        return "<ArtifactImport(id=%r,remote_id=%r,type='%r',url='%r',importer_module_name='%r')>" % (
            self.id, self.remote_id, self.type, self.url, self.importer_module_name)
