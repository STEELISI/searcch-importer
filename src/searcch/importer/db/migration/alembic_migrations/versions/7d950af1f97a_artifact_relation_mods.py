"""artifact-relation-mods

Revision ID: 7d950af1f97a
Revises: 60b014113895
Create Date: 2021-08-15 19:31:39.655747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d950af1f97a'
down_revision = '60b014113895'
branch_labels = None
depends_on = None


def upgrade():
    #
    # We first add values to the Enum; then migrate data; then remove values
    # from the Enum.
    #
    with op.batch_alter_table('artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))
    # And back to transactional mode.
    op.execute(
        "update artifact_relationships set relation='extends' where relation='continues'")
    op.execute(
        "update artifact_relationships set relation='cites' where relation='references'")
    op.execute(
        "update artifact_relationships set relation='describes' where relation='documents'")
    op.execute(
        "update artifact_relationships set relation='produces' where relation='compiles'")
    op.execute(
        "update artifact_relationships set relation='describes' where relation='publishes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))

    with op.batch_alter_table('candidate_artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))
    # And back to transactional mode.
    op.execute(
        "update candidate_artifact_relationships set relation='extends' where relation='continues'")
    op.execute(
        "update candidate_artifact_relationships set relation='cites' where relation='references'")
    op.execute(
        "update candidate_artifact_relationships set relation='describes' where relation='documents'")
    op.execute(
        "update candidate_artifact_relationships set relation='produces' where relation='compiles'")
    op.execute(
        "update candidate_artifact_relationships set relation='describes' where relation='publishes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))

    with op.batch_alter_table('candidate_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))
    # And back to transactional mode.
    op.execute(
        "update candidate_relationships set relation='extends' where relation='continues'")
    op.execute(
        "update candidate_relationships set relation='cites' where relation='references'")
    op.execute(
        "update candidate_relationships set relation='describes' where relation='documents'")
    op.execute(
        "update candidate_relationships set relation='produces' where relation='compiles'")
    op.execute(
        "update candidate_relationships set relation='describes' where relation='publishes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            type_=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))


def downgrade():
    with op.batch_alter_table('artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))
    # And back to transactional mode.
    # XXX: note that there is no going back from several of the new types!
    op.execute(
        "update artifact_relationships set relation='continues' where relation='extends'")
    op.execute(
        "update artifact_relationships set relation='compiles' where relation='produces'")
    op.execute(
        "update artifact_relationships set relation='publishes' where relation='describes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))

    with op.batch_alter_table('candidate_artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))
    # And back to transactional mode.
    # XXX: note that there is no going back from several of the new types!
    op.execute(
        "update candidate_artifact_relationships set relation='continues' where relation='extends'")
    op.execute(
        "update candidate_artifact_relationships set relation='compiles' where relation='produces'")
    op.execute(
        "update candidate_artifact_relationships set relation='publishes' where relation='describes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_artifact_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))

    with op.batch_alter_table('candidate_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'extends', 'uses', 'describes',
                'requires', 'processes', 'produces', 'indexes'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'))
    # And back to transactional mode.
    # XXX: note that there is no going back from several of the new types!
    op.execute(
        "update candidate_relationships set relation='continues' where relation='extends'")
    op.execute(
        "update candidate_relationships set relation='compiles' where relation='produces'")
    op.execute(
        "update candidate_relationships set relation='publishes' where relation='describes'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_relationships') as batch_op:
        batch_op.alter_column(
            "relation",
            existing_type=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses',
                'describes', 'requires', 'processes', 'produces'),
            type_=sa.Enum(
                'cites', 'supplements', 'continues', 'references', 'documents',
                'compiles', 'publishes', 'indexes', 'extends', 'uses'))
