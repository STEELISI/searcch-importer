"""artifact-types-mods

Revision ID: 60b014113895
Revises: 07e9470e1875
Create Date: 2021-08-15 19:31:39.655747

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '60b014113895'
down_revision = '07e9470e1875'
branch_labels = None
depends_on = None


def upgrade():
    #
    # We first add values to the Enum; then migrate data; then remove values
    # from the Enum.
    #
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo'))
    # And back to transactional mode.
    op.execute(
        "update artifacts set type='software'"
        " where type in ('code','executable')")
    op.execute(
        "update artifacts set type='other'"
        " where type in ('methodology', 'metrics', 'priorwork', 'hypothesis',"
        "                'domain', 'supportinginfo')")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'))

    with op.batch_alter_table('artifact_imports') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'unknown', 'presentation', 'software', 'other'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'unknown'))
    # And back to transactional mode.
    op.execute(
        "update artifact_imports set type='software'"
        " where type in ('code','executable')")
    op.execute(
        "update artifact_imports set type='other'"
        " where type in ('methodology', 'metrics', 'priorwork', 'hypothesis',"
        "                'domain', 'supportinginfo')")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifact_imports') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other',
                'unknown'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                 'unknown', 'presentation', 'software', 'other'))

    with op.batch_alter_table('candidate_artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo'))
    # And back to transactional mode.
    op.execute(
        "update candidate_artifacts set type='software'"
        " where type in ('code','executable')")
    op.execute(
        "update candidate_artifacts set type='other'"
        " where type in ('methodology', 'metrics', 'priorwork', 'hypothesis',"
        "                'domain', 'supportinginfo')")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            type_=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other'),
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'))



def downgrade():
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'))
    # And back to transactional mode; no going back from 'other' conversion!
    op.execute(
        "update artifacts set type='code' where type='software'")
    op.execute(
        "update artifacts set type='other' where type='presentation'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo'))

    with op.batch_alter_table('artifact_imports') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other',
                'unknown'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                 'unknown', 'presentation', 'software', 'other'))
    # And back to transactional mode; no going back from 'other' conversion!
    op.execute(
        "update artifact_imports set type='code' where type='software'")
    op.execute(
        "update artifact_imports set type='other' where type='presentation'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('artifact_imports') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'unknown', 'presentation', 'software', 'other'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'unknown'))

    with op.batch_alter_table('candidate_artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'publication', 'presentation', 'dataset', 'software', 'other'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'))
    # And back to transactional mode; no going back from 'other' conversion!
    op.execute(
        "update candidate_artifacts set type='code' where type='software'")
    op.execute(
        "update candidate_artifacts set type='other' where type='presentation'")
    # Alter the Enum to the final state:
    with op.batch_alter_table('candidate_artifacts') as batch_op:
        batch_op.alter_column(
            "type",
            existing_type=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo',
                'presentation', 'software', 'other'),
            type_=sa.Enum(
                'dataset', 'executable', 'methodology', 'metrics', 'priorwork',
                'publication', 'hypothesis', 'code', 'domain', 'supportinginfo'))
