"""affiliation org_id nullable

Revision ID: 1024dfc41010
Revises: 9d0ecc58a94e
Create Date: 2020-09-14 19:34:50.111694

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1024dfc41010'
down_revision = '9d0ecc58a94e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("affiliations") as batch_op:
        batch_op.alter_column(
            "org_id",existing_type=sa.INTEGER(),nullable=True)

def downgrade():
    with op.batch_alter_table("affiliations") as batch_op:
        batch_op.alter_column(
            "org_id",existing_type=sa.INTEGER(),nullable=False)
