"""metadata_value_size_increase

Revision ID: ac894ad4047b
Revises: 16b45f41cabc
Create Date: 2020-12-07 17:56:09.910246

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac894ad4047b'
down_revision = '16b45f41cabc'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artifact_metadata', recreate='always') as batch_op:
        batch_op.alter_column(
            'value', type_=sa.String(16384), existing_type=sa.String(1024), nullable=False)


def downgrade():
    with op.batch_alter_table('artifact_metadata', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.String(1024), existing_type=sa.String(16384), nullable=True)
