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
from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean, DateTime, Integer, String, Text

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging

LOG = logging.getLogger(__name__)

meta = MetaData()


processes = Table('processes', meta,
                  Column('created_at', DateTime),
                  Column('updated_at', DateTime),
                  Column('deleted_at', DateTime),
                  Column('deleted', Integer, nullable=False),
                  Column('gid', String(length=36), nullable=False),
                  Column('keypair_id', String(length=36)),
                  Column(
                      'pid', String(length=36), primary_key=True,
                      nullable=False),
                  Column('ppid', String(length=36)),
                  Column('nova_instance_id', String(length=36)),
                  Column('glance_image_id', String(length=36)),
                  Column('nova_flavor_id', Integer),
                  Column('user_id', String(length=255)),
                  Column('project_id', String(length=255)),
                  Column('display_name', String(length=255)),
                  Column('app_status', Integer),
                  Column('is_proxy', Boolean),
                  Column('shm_endpoint', Text),
                  Column('ipc_endpoint', Text),
                  Column('fs_endpoint', Text),
                  Column('args', Text),
                  Column('userdata', Text),
                  mysql_engine='InnoDB',
                  mysql_charset='utf8'
                  )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    groups = Table("groups", meta, autoload=True)
    keypairs = Table("keypairs", meta, autoload=True)

    try:
        processes.create()
    except Exception:
        LOG.info(repr(processes))
        LOG.exception(_('Exception while creating processes table.'))
        raise

    ForeignKeyConstraint(columns=[processes.c.gid],
                         refcolumns=[groups.c.gid]).create()

    ForeignKeyConstraint(columns=[processes.c.keypair_id],
                         refcolumns=[keypairs.c.keypair_id]).create()

    ForeignKeyConstraint(columns=[processes.c.ppid],
                         refcolumns=[processes.c.pid]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        processes.drop()
    except Exception:
        LOG.info(repr(processes))
        LOG.exception(_('Exception while dropping processes table.'))
        raise
