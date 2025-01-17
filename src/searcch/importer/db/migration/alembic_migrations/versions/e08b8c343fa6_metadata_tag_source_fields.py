"""metadata_tag_source_fields

Revision ID: e08b8c343fa6
Revises: 1b9ee67c1d04
Create Date: 2020-12-01 23:17:32.361601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e08b8c343fa6'
down_revision = '1b9ee67c1d04'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artifact_metadata') as batch_op:
        batch_op.add_column(sa.Column(
            'source',sa.String(length=256),nullable=True))
    with op.batch_alter_table('artifact_tags') as batch_op:
        batch_op.add_column(sa.Column(
            'source',sa.String(length=256),nullable=True))


def downgrade():
    with op.batch_alter_table('artifact_tags') as batch_op:
        batch_op.drop_column('source')
    with op.batch_alter_table('artifact_metadata') as batch_op:
        batch_op.drop_column('source')
