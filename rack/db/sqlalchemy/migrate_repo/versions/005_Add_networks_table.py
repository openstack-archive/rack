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
from sqlalchemy import MetaData, Table, Column, Integer
from sqlalchemy import String, DateTime, Boolean


LOG = logging.getLogger(__name__)

meta = MetaData()

networks = Table('networks', meta,
                 Column('created_at', DateTime),
                 Column('updated_at', DateTime),
                 Column('deleted_at', DateTime),
                 Column('network_id', String(length=255),
                        primary_key=True, nullable=False),
                 Column('gid', String(length=255), nullable=False),
                 Column('neutron_network_id', String(length=255)),
                 Column('is_admin', Boolean),
                 Column('cidr', String(length=255)),
                 Column('ext_router', String(length=255)),
                 Column('user_id', String(length=255)),
                 Column('project_id', String(length=255)),
                 Column('display_name', String(length=255)),
                 Column('deleted', Integer),
                 mysql_engine='InnoDB',
                 mysql_charset='utf8'
                 )


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        networks.create()
        groups = Table("groups", meta, autoload=True)
        ForeignKeyConstraint([networks.c.gid], [groups.c.gid]).create()
    except Exception:
        LOG.info(repr(networks))
        LOG.exception(_('Exception while creating networks table.'))
        raise


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        networks.drop()
    except Exception:
        LOG.info(repr(networks))
        LOG.exception(_('Exception while dropping networks table.'))
        raise
