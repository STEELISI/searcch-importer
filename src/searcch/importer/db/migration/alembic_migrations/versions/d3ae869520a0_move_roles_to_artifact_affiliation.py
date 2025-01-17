"""move-roles-to-artifact-affiliation

Revision ID: d3ae869520a0
Revises: 9a1314b315e7
Create Date: 2021-07-15 06:05:03.845547

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3ae869520a0'
down_revision = '9a1314b315e7'
branch_labels = None
depends_on = None


def upgrade():
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s__%(column_2_name)s",
    }
    with op.batch_alter_table('affiliations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint(
            "uq__affiliations__person_id__org_id__roles")
        batch_op.create_unique_constraint(
            "uq__affiliations__person_id__org_id",
            ['person_id', 'org_id'])
        batch_op.drop_column('roles')

    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s",
    }
    with op.batch_alter_table('artifact_affiliations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint(
            "uq__artifact_affiliations__artifact_id__affiliation_id")
        batch_op.add_column(sa.Column('roles',
            sa.Enum('Author', 'ContactPerson', 'Other', name='artifact_affiliation_enum'),
            nullable=False, default="Author"))
        batch_op.create_unique_constraint(
            "uq__artifact_affiliations__artifact_id__affiliation_id__roles",
            ['artifact_id', 'affiliation_id', 'roles'])


def downgrade():
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s__%(column_2_name)s",
    }
    with op.batch_alter_table('artifact_affiliations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint(
            "uq__artifact_affiliations__artifact_id__affiliation_id__roles")
        batch_op.drop_column('roles')
        batch_op.create_unique_constraint(
            "uq__artifact_affiliations__artifact_id__affiliation_id",
            ['artifact_id', 'affiliation_id'])

    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s",
    }
    with op.batch_alter_table('affiliations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint("uq__affiliations__person_id__org_id")
        batch_op.add_column(sa.Column(
            'roles',
            sa.Enum("Author","ProjectManager","Researcher","ContactPerson",
                    "PrincipalInvestigator","CoPrincipalInvestigator","Other",
                    name='affiliation_enum'),
            nullable=False, default="Author"))
        batch_op.create_unique_constraint(
            "uq__affiliations__artifact_id__affiliation_id__roles",
            ['artifact_id', 'affiliation_id', 'roles'])
