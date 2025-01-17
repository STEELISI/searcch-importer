"""zenodo-tweaks

Revision ID: f799323c9ee8
Revises: 049be1d0f133
Create Date: 2021-02-14 21:49:35.460295

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f799323c9ee8'
down_revision = '049be1d0f133'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('person_metadata', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source', sa.String(length=256), nullable=True))


def downgrade():
    with op.batch_alter_table('person_metadata', schema=None) as batch_op:
        batch_op.drop_column('source')
