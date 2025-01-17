"""recurring-venue

Revision ID: 6864e7d5b11b
Revises: 3393727c0583
Create Date: 2022-12-12 06:00:35.423302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6864e7d5b11b'
down_revision = '3393727c0583'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recurring_venues',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('type', sa.Enum('conference', 'journal', 'magazine', 'newspaper', 'periodical', 'event', 'other', name='recurring_venue_enum'), nullable=False),
    sa.Column('title', sa.String(length=1024), nullable=False),
    sa.Column('abbrev', sa.String(length=64), nullable=True),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('publisher_url', sa.String(length=1024), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recurring_venue_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key("recurring_venues_id_fkey", 'recurring_venues', ['recurring_venue_id'], ['id'])


def downgrade():
    with op.batch_alter_table('venues', schema=None) as batch_op:
        batch_op.drop_constraint("recurring_venues_id_fkey", type_='foreignkey')
        batch_op.drop_column('recurring_venue_id')

    op.drop_table('recurring_venues')
