"""artifact_file_restructure

Revision ID: 16b45f41cabc
Revises: cf685d729cc8
Create Date: 2020-12-07 15:44:26.867115

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '16b45f41cabc'
down_revision = 'cf685d729cc8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'artifact_file_members',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('parent_file_id', sa.Integer(), nullable=False),
        sa.Column('pathname', sa.String(length=512), nullable=False),
        sa.Column('html_url', sa.String(length=512), nullable=True),
        sa.Column('download_url', sa.String(length=512), nullable=True),
        sa.Column('name', sa.String(length=512), nullable=True),
        sa.Column('filetype', sa.String(length=128), nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('mtime', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['parent_file_id'], ['artifact_files.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('parent_file_id', 'pathname')
    )
    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(length=512), nullable=True))
        batch_op.create_unique_constraint(
            "uq_artifact_files_artifact_id_url", ['artifact_id', 'url'])
        #batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_column('parent_file_id')


def downgrade():
    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_file_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key(None, 'artifact_files', ['parent_file_id'], ['id'])
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('name')

    op.drop_table('artifact_file_members')
