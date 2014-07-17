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
from migrate.changeset import UniqueConstraint
from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean, DateTime, Integer, String

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging


LOG = logging.getLogger(__name__)

meta = MetaData()


services = Table('services', meta,
                 Column('created_at', DateTime),
                 Column('updated_at', DateTime),
                 Column('deleted_at', DateTime),
                 Column('id', Integer, primary_key=True, nullable=False),
                 Column('host', String(length=255)),
                 Column('binary', String(length=255)),
                 Column('topic', String(length=255)),
                 Column('report_count', Integer, nullable=False),
                 Column('disabled', Boolean),
                 Column('deleted', Integer),
                 Column('disabled_reason', String(length=255)),
                 mysql_engine='InnoDB',
                 mysql_charset='utf8'
                 )


def upgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        services.create()
    except Exception:
        LOG.info(repr(services))
        LOG.exception(_('Exception while creating services table.'))
        raise

    UniqueConstraint('host', 'topic', 'deleted',
                     table=services,
                     name='uniq_services0host0topic0deleted').create()
    UniqueConstraint('host', 'binary', 'deleted',
                     table=services,
                     name='uniq_services0host0binary0deleted').create()


def downgrade(migrate_engine):
    meta.bind = migrate_engine

    try:
        services.drop()
    except Exception:
        LOG.info(repr(services))
        LOG.exception(_('Exception while dropping services table.'))
        raise
