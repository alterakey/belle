import sqlalchemy as sa
import sqlalchemy.dialects.mysql as sa_mysql

metadata = sa.MetaData()

asset_table = sa.Table(
    'asset', metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('user_id', sa.Integer, nullable=True),
    sa.Column('name', sa.Unicode(255), nullable=False),
    sa.Column('type', sa.Unicode(255), nullable=False),
    sa.Column('hash', sa.String(255), nullable=False, unique=True),
    sa.Column('blob', sa_mysql.LONGBLOB),
    sa.Column('thumbnail', sa_mysql.LONGBLOB)
)
