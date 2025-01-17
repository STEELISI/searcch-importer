"""publishes_relationship

Revision ID: 8b2452c9291a
Revises: 810f17f0d2dc
Create Date: 2020-11-23 21:01:43.027224

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.orm.session import Session
from searcch.importer.db.model import ArtifactRelationship

# revision identifiers, used by Alembic.
revision = '8b2452c9291a'
down_revision = '810f17f0d2dc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("artifact_relationships",recreate="always") as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                "cites","supplements","continues","references","documents",
                "compiles","publishes"),
            existing_type=sa.Enum(
                "cites","supplements","continues","references","documents",
                "compiles"))


def downgrade():
    with op.batch_alter_table("artifact_relationships",recreate="always") as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                "cites","supplements","continues","references","documents",
                "compiles"),
            existing_type=sa.Enum(
                "cites","supplements","continues","references","documents",
                "compiles","publishes"))
