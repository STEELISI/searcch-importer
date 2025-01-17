"""refactor_org

Revision ID: 6b76c3bd985c
Revises: d3ae869520a0
Create Date: 2021-07-15 07:23:32.316613

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6b76c3bd985c'
down_revision = 'd3ae869520a0'
branch_labels = None
depends_on = None


def upgrade():
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s__%(column_2_name)s",
    }
    with op.batch_alter_table('organizations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_constraint(
            "uq__organizations__name__type__parent_org_id")
        #batch_op.drop_constraint("parent_org_id_fkey", type_='foreignkey')
        batch_op.drop_column('parent_org_id')
        batch_op.add_column(sa.Column(
            'verified', sa.Boolean, nullable=True, default=False))
        batch_op.alter_column(
            'type',existing_type=sa.Enum(
                "Institution","Institute","ResearchGroup","Sponsor","Other",
                name="organization_enum"),
            type=sa.Enum(
                "Institution","Company","Institute","ResearchGroup","Sponsor","Other",
                name="organization_enum"))
    op.execute("update organizations set verified=False where verified is NULL")
    with op.batch_alter_table('organizations', schema=None) as batch_op:
        batch_op.alter_column(
            'verified',existing_type=sa.Boolean, nullable=False)


def downgrade():
    convention = {
        "uq": "uq__%(table_name)s__%(column_0_name)s__%(column_1_name)s__%(column_2_name)s",
    }
    with op.batch_alter_table('organizations', schema=None,
                              naming_convention=convention) as batch_op:
        batch_op.drop_column('verified')
        batch_op.add_column(sa.Column('parent_org_id', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key("parent_org_id_fkey", 'organizations', ['parent_org_id'], ['id'])
        batch_op.create_unique_constraint(
            "uq__organizations__name__type__parent_org_id",
            ['name', 'type', 'parent_org_id'])
