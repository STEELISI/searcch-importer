"""file-content

Revision ID: 3393727c0583
Revises: 9566bde09e38
Create Date: 2022-05-02 19:41:49.554303

"""
from alembic import op
import sqlalchemy as sa
import hashlib


# revision identifiers, used by Alembic.
revision = '3393727c0583'
down_revision = '9566bde09e38'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    
    op.create_table('file_content',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('content', sa.LargeBinary(), nullable=False),
        sa.Column('hash', sa.BINARY(length=32), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.PrimaryKeyConstraint('id', sqlite_on_conflict='IGNORE'),
        sa.UniqueConstraint('hash', sqlite_on_conflict='IGNORE')
    )
    with op.batch_alter_table('artifact_file_members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_content_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key("file_content_id_fkey", 'file_content', ['file_content_id'], ['id'])

    # We will just manage the file_content inserts and deduplication.
    fid = 1
    hashes = dict()

    session = sa.orm.Session(bind=bind)
    res = session.execute("select id, content from artifact_file_members")
    for row in res:
        if row["content"] is None:
            continue
        m = hashlib.sha256()
        m.update(row["content"])
        d = m.digest()
        ds = d.hex()
        if not ds in hashes:
            session.execute(
                "insert into file_content (id, content, hash, size) values (:fid, :content, :hash, :size)",
                { "fid": fid, "content": row["content"], "hash": d, "size": len(row["content"]) })
            print("inserted fc: %s" % (ds,))
            hashes[ds] = fid
            fid += 1
        session.execute("update artifact_file_members set file_content_id=:fid where id=:id",
                        { "id": row["id"], "fid": hashes[ds] })
        print("updated artifact_file_members.id=%d to point to file_content_id.id=%d"
              % (row["id"],hashes[ds]))

    with op.batch_alter_table('artifact_file_members', schema=None) as batch_op:
        batch_op.drop_column('content')

    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('file_content_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key("file_content_id_fkey", 'file_content', ['file_content_id'], ['id'])

    session = sa.orm.Session(bind=bind)
    res = session.execute("select id, content from artifact_files")
    for row in res:
        if row["content"] is None:
            continue
        m = hashlib.sha256()
        m.update(row["content"])
        d = m.digest()
        ds = d.hex()
        if not ds in hashes:
            session.execute(
                "insert into file_content (id, content, hash, size) values (:fid, :content, :hash, :size)",
                { "fid": fid, "content": row["content"], "hash": d, "size": len(row["content"]) })
            print("inserted fc: %s" % (ds,))
            hashes[ds] = fid
            fid += 1
        session.execute("update artifact_files set file_content_id=:fid where id=:id",
                        { "id": row["id"], "fid": hashes[ds] })
        print("updated artifact_files.id=%d to point to file_content_id.id=%d"
              % (row["id"],hashes[ds]))

    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.drop_column('content')

    with op.batch_alter_table('artifacts', schema=None) as batch_op:
        batch_op.drop_column('version')
        batch_op.drop_column('parent_id')


def downgrade():
    bind = op.get_bind()

    with op.batch_alter_table('artifacts', schema=None) as batch_op:
        batch_op.add_column(sa.Column('parent_id', sa.INTEGER(), nullable=True))
        batch_op.add_column(sa.Column('version', sa.INTEGER(), nullable=True))
        batch_op.create_foreign_key("parent_id_fkey", 'artifacts', ['parent_id'], ['id'])

    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.BLOB(), nullable=True))

    session = sa.orm.Session(bind=bind)
    res = session.execute("select id, file_content_id from artifact_files where file_content_id is not NULL")
    for row in res:
        res2 = session.execute("select content from file_content where id=:id", { "id": row["file_content_id"] })
        row2 = res2.first()
        session.execute("update artifact_files set content=:content where id=:id",
                        { "id": row["id"], "content": res2[0]["content"] })

    with op.batch_alter_table('artifact_files', schema=None) as batch_op:
        batch_op.drop_column('file_content_id')

    with op.batch_alter_table('artifact_file_members', schema=None) as batch_op:
        batch_op.add_column(sa.Column('content', sa.BLOB(), nullable=True))

    session = sa.orm.Session(bind=bind)
    res = session.execute("select id, file_content_id from artifact_file_members where file_content_id is not NULL")
    for row in res:
        res2 = session.execute("select content from file_content where id=:id", { "id": row["file_content_id"] })
        row2 = res2.first()
        session.execute("update artifact_file_members set content=:content where id=:id",
                        { "id": row["id"], "content": row2["content"] })

    with op.batch_alter_table('artifact_file_members', schema=None) as batch_op:
        batch_op.drop_column('file_content_id')

    op.drop_table('file_content')
