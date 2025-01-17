from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.convert import ModelConverter as BaseModelConverter
from marshmallow_sqlalchemy.fields import Nested
from marshmallow import fields, ValidationError
import sqlalchemy
import base64

from searcch.importer.db.model import *

class Base64Field(fields.Field):
    """Field that serializes to a base64-encoded string and deserializes
    to bytes."""

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        return base64.b64encode(value).decode("utf-8")

    def _deserialize(self, value, attr, data, **kwargs):
        if value is None:
            return None
        if value == "":
            return b""
        try:
            return base64.b64decode(value)
        except Exception as error:
            raise ValidationError("Invalid base64 content") from error


class ModelConverter(BaseModelConverter):
    SQLA_TYPE_MAPPING = {
        **BaseModelConverter.SQLA_TYPE_MAPPING,
        sqlalchemy.LargeBinary: Base64Field,
        sqlalchemy.types.BINARY: Base64Field,
    }


class ArtifactFundingSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactFunding
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ArtifactMetadataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactMetadata
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True
        exclude = ('id', 'artifact_id',)


class ArtifactPublicationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactPublication
        exclude = ('artifact_id', 'publisher_id',)
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ExporterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Exporter
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ArtifactTagSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactTag
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True
        exclude = ('id', 'artifact_id',)


class FileContentSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = FileContent
        model_converter = ModelConverter
        include_fk = False
        include_relationships = False
        exclude = ()


class ArtifactFileMemberSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactFileMember
        exclude = ('id', 'parent_file_id', 'file_content_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    file_content = Nested(FileContentSchema, many=False)


class ArtifactFileSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactFile
        exclude = ('id', 'artifact_id', 'file_content_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    file_content = Nested(FileContentSchema, many=False)
    members = Nested(ArtifactFileMemberSchema, many=True)


class ArtifactRelationshipSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactRelationship
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ArtifactReleaseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactRelease
        exclude = ('id', 'artifact_id',)
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ImporterSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Importer
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class PersonSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Person
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class UserAuthorizationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = UserAuthorization
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class UserSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        exclude = ('id','person_id',)
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    person = Nested(PersonSchema)


class ArtifactCurationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactCuration
        exclude = ('id','artifact_id', 'curator_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    curator = Nested(UserSchema)


class LicenseSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = License
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class OrganizationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Organization
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class AffiliationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Affiliation
        exclude = ('id', 'person_id', 'org_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    person = Nested(PersonSchema)
    org = Nested(OrganizationSchema)


class ArtifactAffiliationSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactAffiliation
        exclude = ('id', 'artifact_id', 'affiliation_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    affiliation = Nested(AffiliationSchema, many=False)


class BadgeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Badge
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True


class ArtifactBadgeSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactBadge
        exclude = ('id', 'artifact_id', 'badge_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    badge = Nested(BadgeSchema, many=False)


class RecurringVenueShallowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RecurringVenue
        model_converter = ModelConverter
        include_fk = True
        include_relationships = False


class VenueShallowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Venue
        model_converter = ModelConverter
        include_fk = True
        include_relationships = False


class RecurringVenueSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = RecurringVenue
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    recurrences = Nested(VenueShallowSchema, many=True)


class VenueSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Venue
        exclude = ('recurring_venue_id',)
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    recurring_venue = Nested(RecurringVenueShallowSchema, many=False)


class ArtifactVenueSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactVenue
        exclude = ('id', 'artifact_id', 'venue_id')
        model_converter = ModelConverter
        include_fk = True
        include_relationships = True

    venue = Nested(VenueSchema, many=False)


class PersonMetadataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PersonMetadata
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class ArtifactShallowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Artifact
        model_converter = ModelConverter
        exclude = ('id','license_id', 'owner_id', 'importer_id')
        include_fk = True
        include_relationships = False


class ArtifactSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Artifact
        model_converter = ModelConverter
        exclude = ('id','license_id', 'owner_id', 'importer_id')
        include_fk = True
        include_relationships = True

    license = Nested(LicenseSchema, many=False)
    meta = Nested(ArtifactMetadataSchema, many=True)
    tags = Nested(ArtifactTagSchema, many=True)
    files = Nested(ArtifactFileSchema, many=True)
    owner = Nested(UserSchema)
    importer = Nested(ImporterSchema, many=False)
    # parent = Nested(ArtifactSchema, many=True)
    curations = Nested(ArtifactCurationSchema, many=True)
    publication = Nested(ArtifactPublicationSchema, many=False)
    releases = Nested(ArtifactReleaseSchema, many=True)
    affiliations = Nested(ArtifactAffiliationSchema, many=True)
    relationships = Nested(ArtifactRelationshipSchema, many=True)
    badges = Nested(ArtifactBadgeSchema, many=True)
    venues = Nested(ArtifactVenueSchema, many=True)
    candidate_relationships = Nested(
        "CandidateArtifactRelationshipShallowSchema", many=True)


class CandidateArtifactMetadataSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CandidateArtifactMetadata
        model_converter = ModelConverter
        exclude = ('id',)
        include_fk = True
        include_relationships = True


class CandidateArtifactShallowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CandidateArtifact
        model_converter = ModelConverter
        exclude = ('id','owner_id','owner','candidate_artifact_relationships',
                   'imported_artifact_id')
        include_fk = True
        include_relationships = True

    meta = Nested(CandidateArtifactMetadataSchema, many=True)


class CandidateArtifactSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CandidateArtifact
        model_converter = ModelConverter
        exclude = ('id','owner_id')
        include_fk = True
        include_relationships = True

    meta = Nested(CandidateArtifactMetadataSchema, many=True)
    owner = Nested(UserSchema)
    imported_artifact = Nested(ArtifactSchema)
    candidate_artifact_relationships = Nested(
        "CandidateArtifactRelationshipSchema", many=True)


class CandidateArtifactRelationshipSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CandidateArtifactRelationship
        model_converter = ModelConverter
        exclude = ('id','artifact_id','related_candidate_id')
        include_fk = True
        include_relationships = True

    artifact = Nested(ArtifactSchema)
    related_candidate = Nested(CandidateArtifactSchema)


class CandidateArtifactRelationshipShallowSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = CandidateArtifactRelationship
        model_converter = ModelConverter
        exclude = ('id','artifact_id','related_candidate_id','artifact')
        include_fk = True
        include_relationships = True

    related_candidate = Nested(CandidateArtifactShallowSchema)


class ArtifactImportSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = ArtifactImport
        model_converter = ModelConverter
        exclude = ()
        include_fk = True
        include_relationships = True

    owner = Nested(UserSchema, many=False)
    #parent = Nested(ArtifactSchema, many=False)
    artifact = Nested(ArtifactSchema, many=False)
