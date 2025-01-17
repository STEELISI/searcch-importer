"""importer-remote-options

Revision ID: 71cc3aa3e0c9
Revises: 6864e7d5b11b
Create Date: 2022-12-19 14:15:56.234423

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '71cc3aa3e0c9'
down_revision = '6864e7d5b11b'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artifact_imports', schema=None) as batch_op:
        batch_op.add_column(sa.Column('nofetch', sa.Boolean()))
        batch_op.add_column(sa.Column('noextract', sa.Boolean()))
        batch_op.add_column(sa.Column('noremove', sa.Boolean()))


def downgrade():
    with op.batch_alter_table('artifact_imports', schema=None) as batch_op:
        batch_op.drop_column('noremove')
        batch_op.drop_column('noextract')
        batch_op.drop_column('nofetch')
