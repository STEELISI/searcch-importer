"""lengthen_fields

Revision ID: 1b9ee67c1d04
Revises: 8b2452c9291a
Create Date: 2020-12-01 22:07:00.739276

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1b9ee67c1d04'
down_revision = '8b2452c9291a'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artifact_curations', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.Text(), existing_type=sa.String(1024), nullable=True)
        batch_op.alter_column(
            'opdata', type_=sa.Text(), existing_type=sa.String(4096), nullable=False)
    with op.batch_alter_table('artifact_publications', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.Text(), existing_type=sa.String(1024), nullable=True)
    with op.batch_alter_table('artifact_releases', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.Text(), existing_type=sa.String(1024), nullable=True)


def downgrade():
    with op.batch_alter_table('artifact_curations', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.String(1024), existing_type=sa.Text(), nullable=True)
        batch_op.alter_column(
            'opdata', type_=sa.String(4096), existing_type=sa.Text(), nullable=False)
    with op.batch_alter_table('artifact_publications', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.String(1024), existing_type=sa.Text(), nullable=True)
    with op.batch_alter_table('artifact_releases', recreate='always') as batch_op:
        batch_op.alter_column(
            'notes', type_=sa.String(1024), existing_type=sa.Text(), nullable=True)
