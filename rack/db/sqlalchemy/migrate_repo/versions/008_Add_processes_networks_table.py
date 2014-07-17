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
from sqlalchemy import String

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging

LOG = logging.getLogger(__name__)

meta = MetaData()


processes_networks = Table('processes_networks', meta,
                           Column(
                               'pid', String(length=36), nullable=False,
                               primary_key=True),
                           Column(
                               'network_id', String(length=36),
                               nullable=False, primary_key=True),
                           mysql_engine='InnoDB',
                           mysql_charset='utf8'
                           )


def upgrade(migrate_engine):
    meta.bind = migrate_engine
    processes = Table("processes", meta, autoload=True)
    networks = Table("networks", meta, autoload=True)

    try:
        processes_networks.create()
    except Exception:
        LOG.info(repr(processes_networks))
        LOG.exception(_('Exception while creating processes_networks table.'))
        raise

    ForeignKeyConstraint(columns=[processes_networks.c.pid],
                         refcolumns=[processes.c.pid]).create()
    ForeignKeyConstraint(columns=[processes_networks.c.network_id],
                         refcolumns=[networks.c.network_id]).create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        processes_networks.drop()
    except Exception:
        LOG.info(repr(processes_networks))
        LOG.exception(_('Exception while dropping processes_networks table.'))
        raise
