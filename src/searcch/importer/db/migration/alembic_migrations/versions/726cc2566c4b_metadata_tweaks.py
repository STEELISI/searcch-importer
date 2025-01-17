"""metadata_tweaks

Revision ID: 726cc2566c4b
Revises: 6856092ff104
Create Date: 2020-12-05 23:17:30.513785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '726cc2566c4b'
down_revision = '6856092ff104'
branch_labels = None
depends_on = None


def upgrade():
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s",
    }
    with op.batch_alter_table('artifact_metadata', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(length=256), nullable=True))
        batch_op.drop_constraint("uq__artifact_metadata__name")
        batch_op.create_unique_constraint(
            "uq_artifact_metadata_name_artifact_id_value_type",
            ['name', 'artifact_id', 'value', 'type'])


def downgrade():
    with op.batch_alter_table('artifact_metadata', schema=None) as batch_op:
        batch_op.drop_constraint("uq_artifact_metadata_name_artifact_id_value_type")
        batch_op.drop_column('type')
        batch_op.create_unique_constraint(
            "uq_artifact_metadata_name",
            ['name', 'artifact_id'])
