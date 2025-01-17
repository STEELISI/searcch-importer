"""text title desc

Revision ID: 9d0ecc58a94e
Revises: ba81de6110c7
Create Date: 2020-09-10 21:50:26.227543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9d0ecc58a94e'
down_revision = 'ba81de6110c7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("artifacts") as batch_op:
        batch_op.alter_column(
            "title",type_=sa.Text,nullable=False)
        batch_op.alter_column(
            "description",type_=sa.Text,nullable=True)

def downgrade():
    with op.batch_alter_table("artifacts") as batch_op:
        batch_op.alter_column(
            "title",type_=sa.String(1024),nullable=False)
        batch_op.alter_column(
            "description",type_=sa.String(65535),nullable=True)
