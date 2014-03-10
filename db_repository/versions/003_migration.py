from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
post = Table('post', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('body', String),
    Column('timestamp', DateTime),
    Column('user_id', Integer),
)

user = Table('user', pre_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('nickname', String),
    Column('email', String),
    Column('role', SmallInteger),
    Column('pwdhash', String),
    Column('created', DateTime),
)

user = Table('user', post_meta,
    Column('cust_id', Integer, primary_key=True, nullable=False),
    Column('cust_username', String(length=64)),
    Column('cust_mail', String(length=120)),
    Column('role', SmallInteger, default=ColumnDefault(0)),
    Column('pwdhash', String(length=120)),
    Column('created', DateTime),
    Column('cust_fname', String(length=30)),
    Column('cust_lname', String(length=30)),
    Column('cust_phone', String(length=12)),
    Column('cust_notes', Text),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].drop()
    pre_meta.tables['user'].columns['email'].drop()
    pre_meta.tables['user'].columns['id'].drop()
    pre_meta.tables['user'].columns['nickname'].drop()
    post_meta.tables['user'].columns['cust_fname'].create()
    post_meta.tables['user'].columns['cust_id'].create()
    post_meta.tables['user'].columns['cust_lname'].create()
    post_meta.tables['user'].columns['cust_mail'].create()
    post_meta.tables['user'].columns['cust_notes'].create()
    post_meta.tables['user'].columns['cust_phone'].create()
    post_meta.tables['user'].columns['cust_username'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].create()
    pre_meta.tables['user'].columns['email'].create()
    pre_meta.tables['user'].columns['id'].create()
    pre_meta.tables['user'].columns['nickname'].create()
    post_meta.tables['user'].columns['cust_fname'].drop()
    post_meta.tables['user'].columns['cust_id'].drop()
    post_meta.tables['user'].columns['cust_lname'].drop()
    post_meta.tables['user'].columns['cust_mail'].drop()
    post_meta.tables['user'].columns['cust_notes'].drop()
    post_meta.tables['user'].columns['cust_phone'].drop()
    post_meta.tables['user'].columns['cust_username'].drop()
