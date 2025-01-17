"""exporter_fixes

Revision ID: 810f17f0d2dc
Revises: 1024dfc41010
Create Date: 2020-11-19 09:59:49.436594

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '810f17f0d2dc'
down_revision = '1024dfc41010'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.add_column(sa.Column('exporter_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_artifacts_exporter_id_exporters',
            'exporters', ['exporter_id'], ['id'])
    convention = {
        "uq": "uq_%(table_name)s_%(column_0_name)s",
    }
    with op.batch_alter_table(
        'exporters',naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq_exporters_name")
        batch_op.create_unique_constraint(
            "uq_exporters_name_version",["name","version"])


def downgrade():
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.drop_column('exporter_id')
    convention = {
        "uq": "uq_%(table_name)s_%(column_0_name)s_%(column_1_name)s",
    }
    with op.batch_alter_table(
        'exporters',naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq_exporters_name_version")
        batch_op.create_unique_constraint(
            "uq_exporters_name",["name"])
