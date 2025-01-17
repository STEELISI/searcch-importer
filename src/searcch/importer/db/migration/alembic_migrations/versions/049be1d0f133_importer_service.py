"""importer-service

Revision ID: 049be1d0f133
Revises: ac894ad4047b
Create Date: 2021-02-11 22:19:01.420764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '049be1d0f133'
down_revision = 'ac894ad4047b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('artifact_imports',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('remote_id', sa.Integer(), nullable=True),
    sa.Column('type', sa.Enum('dataset', 'executable', 'methodology', 'metrics', 'priorwork', 'publication', 'hypothesis', 'code', 'domain', 'supportinginfo', 'unknown', name='artifact_import_type_enum'), nullable=True),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('importer_module_name', sa.String(length=256), nullable=True),
    sa.Column('ctime', sa.DateTime(), nullable=False),
    sa.Column('mtime', sa.DateTime(), nullable=True),
    sa.Column('phase', sa.Enum('start', 'validate', 'import', 'retrieve', 'extract', 'done'), nullable=False),
    sa.Column('message', sa.Text(), nullable=True),
    sa.Column('progress', sa.Float(), nullable=True),
    sa.Column('bytes_retrieved', sa.Integer(), nullable=True),
    sa.Column('bytes_extracted', sa.Integer(), nullable=True),
    sa.Column('log', sa.Text(), nullable=True),
    sa.Column('artifact_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('remote_id', 'url')
    )
    convention = {
        "uq": "uq_%(table_name)s_%(column_0_name)s",
    }
    with op.batch_alter_table('artifacts', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq_artifacts_owner_id")


def downgrade():
    op.drop_table('artifact_imports')
    with op.batch_alter_table('artifacts', schema=None) as batch_op:
        batch_op.create_unique_constraint(
            "uq_artifacts_owner_id_url_version",
            ['owner_id', 'url', 'version'])

