# Copyright (c) 2014 ITOCHU Techno-Solutions Corporation.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
from migrate import ForeignKeyConstraint

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy import Column, MetaData, Table

LOG = logging.getLogger(__name__)

meta = MetaData()

keypairs = Table('keypairs', meta,
                 Column('created_at', DateTime),
                 Column('updated_at', DateTime),
                 Column('deleted_at', DateTime),
                 Column('deleted', Integer),
                 Column('keypair_id', String(length=36),
                        primary_key=True, nullable=False),
                 Column('gid', String(length=36), nullable=False),
                 Column('nova_keypair_id', String(length=255)),
                 Column('private_key', Text),
                 Column('display_name', String(length=255)),
                 Column('is_default', Boolean),
                 Column('user_id', String(length=255)),
                 Column('project_id', String(length=255)),
                 Column('status', String(length=255)),
                 mysql_engine='InnoDB',
                 mysql_charset='utf8'
                 )


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        keypairs.create()
        groups = Table("groups", meta, autoload=True)
        ForeignKeyConstraint([keypairs.c.gid], [groups.c.gid]).create()
    except Exception:
        LOG.info(repr(keypairs))
        LOG.exception(_('Exception while creating keypairs table.'))
        raise


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        keypairs.drop()
    except Exception:
        LOG.info(repr(keypairs))
        LOG.exception(_('Exception while dropping keypairs table.'))
        raise
