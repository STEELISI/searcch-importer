"""venue

Revision ID: 9566bde09e38
Revises: 7d950af1f97a
Create Date: 2021-12-17 21:29:18.725830

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9566bde09e38'
down_revision = '7d950af1f97a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('venues',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('type', sa.Enum('conference', 'journal', 'magazine', 'newspaper', 'periodical', 'event', 'other', name='venue_enum'), nullable=False),
    sa.Column('title', sa.String(length=1024), nullable=False),
    sa.Column('abbrev', sa.String(length=64), nullable=True),
    sa.Column('url', sa.String(length=1024), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('location', sa.String(length=1024), nullable=True),
    sa.Column('year', sa.Integer(), nullable=True),
    sa.Column('month', sa.Integer(), nullable=True),
    sa.Column('start_day', sa.Integer(), nullable=True),
    sa.Column('end_day', sa.Integer(), nullable=True),
    sa.Column('publisher', sa.String(length=1024), nullable=True),
    sa.Column('publisher_location', sa.String(length=1024), nullable=True),
    sa.Column('publisher_url', sa.String(length=1024), nullable=True),
    sa.Column('isbn', sa.String(length=128), nullable=True),
    sa.Column('issn', sa.String(length=128), nullable=True),
    sa.Column('doi', sa.String(length=128), nullable=True),
    sa.Column('volume', sa.Integer(), nullable=True),
    sa.Column('issue', sa.Integer(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('artifact_venues',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('artifact_id', sa.Integer(), nullable=False),
    sa.Column('venue_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
    sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('artifact_id', 'venue_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('artifact_venues')
    op.drop_table('venues')
    # ### end Alembic commands ###
