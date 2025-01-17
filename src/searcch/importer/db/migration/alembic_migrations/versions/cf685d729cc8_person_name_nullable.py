"""person_name_nullable

Revision ID: cf685d729cc8
Revises: 726cc2566c4b
Create Date: 2020-12-06 23:36:03.593653

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cf685d729cc8'
down_revision = '726cc2566c4b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=1024),
               nullable=True)


def downgrade():
    with op.batch_alter_table('persons', schema=None) as batch_op:
        batch_op.alter_column('name',
               existing_type=sa.VARCHAR(length=1024),
               nullable=False)
