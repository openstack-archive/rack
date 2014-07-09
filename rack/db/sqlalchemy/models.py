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
from rack.openstack.common.db.sqlalchemy import models

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, schema
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Group(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):
    
    __tablename__ = 'groups'
    securitygroups = relationship("Securitygroup")
    processes = relationship("Process")

    gid = Column(String(36), primary_key=True)
    user_id = Column(String(255))
    project_id = Column(String(255))
    display_name = Column(String(255))
    display_description = Column(String(255))
    status = Column(String(255))


class Service(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):
    """Represents a running service on a host."""

    __tablename__ = 'services'
    __table_args__ = (
        schema.UniqueConstraint("host", "topic", "deleted",
                                name="uniq_services0host0topic0deleted"),
        schema.UniqueConstraint("host", "binary", "deleted",
                                name="uniq_services0host0binary0deleted")
    )

    id = Column(Integer, primary_key=True)
    host = Column(String(255))
    binary = Column(String(255))
    topic = Column(String(255))
    report_count = Column(Integer, nullable=False, default=0)
    disabled = Column(Boolean, default=False)
    disabled_reason = Column(String(255))


class Network(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):
    
    __tablename__ = 'networks'
    
    network_id = Column(String(255), primary_key=True)
    gid = Column(String(255))
    neutron_network_id = Column(String(255))
    is_admin = Column(Boolean, default=False)
    subnet = Column(String(255))
    ext_router = Column(String(255))
    user_id = Column(String(255))
    project_id = Column(String(255))
    display_name = Column(String(255))
    status = Column(String(255))


class Keypair(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):

    __tablename__ = 'keypairs'

    keypair_id = Column(String(36), primary_key=True)
    gid = Column(String(36), ForeignKey('groups.gid'), nullable=False)
    user_id = Column(String(255))
    project_id = Column(String(255))
    nova_keypair_id = Column(String(255))
    private_key = Column(Text)
    display_name = Column(String(255))
    is_default = Column(Boolean, default=False)
    status = Column(String(255))


class Securitygroup(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):

    __tablename__ = 'securitygroups'

    deleted = Column(Integer, nullable=False, default=0)
    securitygroup_id = Column(String(36), primary_key=True)
    gid = Column(String(36), ForeignKey('groups.gid'))
    neutron_securitygroup_id = Column(String(36))
    is_default = Column(Boolean, default=False)
    user_id = Column(String(255))
    project_id = Column(String(255))
    display_name = Column(String(255))
    status = Column(String(255))

    group = relationship("Group",
                            foreign_keys=gid,
                            primaryjoin='and_('
                                'Securitygroup.gid == Group.gid,'
                                'Securitygroup.deleted == 0,'
                                'Group.deleted == 0)')


class Process(models.SoftDeleteMixin,
              models.TimestampMixin,
              models.ModelBase,
              Base):

    __tablename__ = 'processes'


    deleted = Column(Integer, nullable=False, default=0)
    gid = Column(String(36), ForeignKey('groups.gid'), nullable=False)
    keypair_id = Column(String(36), ForeignKey('keypairs.keypair_id'))
    pid = Column(String(36), primary_key=True)
    ppid = Column(String(36), ForeignKey('processes.pid'))
    nova_instance_id = Column(String(36))
    glance_image_id = Column(String(36), nullable=False)
    nova_flavor_id = Column(Integer, nullable=False)
    user_id = Column(String(255), nullable=False)
    project_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=False)
    status = Column(String(255), nullable=False)

    group = relationship("Group",
                            foreign_keys=gid,
                            primaryjoin='and_('
                                'Process.gid == Group.gid,'
                                'Process.deleted == 0,'
                                'Group.deleted == 0)')

    securitygroups = relationship("Securitygroup",
                    secondary="processes_securitygroups",
                    primaryjoin='and_('
                                'Process.pid == ProcessSecuritygroup.pid,'
                                'Process.deleted == 0)',
                    secondaryjoin='and_('
                                'Securitygroup.securitygroup_id == ProcessSecuritygroup.securitygroup_id,'
                                'Securitygroup.deleted == 0)',
                    backref="processes")

    networks = relationship("Network",
                    secondary="processes_networks",
                    primaryjoin='and_('
                                'Process.pid == ProcessNetwork.pid,'
                                'Process.deleted == 0)',
                    secondaryjoin='and_('
                                'Network.network_id == ProcessNetwork.network_id,'
                                'Network.deleted == 0)',
                    backref="processes")

class ProcessSecuritygroup(models.ModelBase,Base):

    __tablename__ = 'processes_securitygroups'

    pid = Column(String(36), ForeignKey('processes.pid'), nullable=False, primary_key=True)
    securitygroup_id = Column(String(36), ForeignKey('securitygroups.securitygroup_id'), nullable=False, primary_key=True)

class ProcessNetwork(models.ModelBase,Base):

    __tablename__ = 'processes_networks'

    pid = Column(String(36), ForeignKey('processes.pid'), nullable=False, primary_key=True)
    network_id = Column(String(36), ForeignKey('networks.network_id'), nullable=False, primary_key=True)
