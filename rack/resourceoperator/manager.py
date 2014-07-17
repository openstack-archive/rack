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
"""
ResourceOperator Service
"""

from rack import db
from oslo import messaging

from rack import exception
from rack import manager
from rack.openstack.common import log as logging

from rack.resourceoperator.openstack import networks
from rack.resourceoperator.openstack import keypairs
from rack.resourceoperator.openstack import securitygroups
from rack.resourceoperator.openstack import processes


LOG = logging.getLogger(__name__)


class ResourceOperatorManager(manager.Manager):

    target = messaging.Target(version='1.0')

    def __init__(self, scheduler_driver=None, *args, **kwargs):
        super(ResourceOperatorManager, self).__init__(
            service_name='resourceoperator',
            *args, **kwargs)
        self.network_client = networks.NetworkAPI()
        self.keypair_client = keypairs.KeypairAPI()
        self.securitygroup_client = securitygroups.SecuritygroupAPI()
        self.securitygrouprule_client = securitygroups.SecuritygroupruleAPI()
        self.process_client = processes.ProcessesAPI()

    def network_create(self, context, network):
        update_values = {}
        try:
            neutron_network_id = self.network_client.network_create(
                                    network.get("display_name"),
                                    network.get("subnet"),
                                    network.get("gateway"),
                                    network.get("dns_nameservers"),
                                    network.get("ext_router"))
            update_values["neutron_network_id"] = neutron_network_id
            update_values["status"] = "ACTIVE"
        except Exception as e:
            LOG.exception(e)
            update_values["status"] = "ERROR"
        try:
            db.network_update(context, network["network_id"], update_values)
        except Exception as e:
            LOG.exception(e)

    def network_delete(self, context, neutron_network_id, ext_router):
        try:
            self.network_client.network_delete(neutron_network_id, ext_router)
        except Exception as e:
            LOG.exception(e)

    def keypair_create(self, context, gid, keypair_id, name):
        try:
            values = self.keypair_client.keypair_create(name)
            values["status"] = "ACTIVE"
        except Exception as e:
            LOG.exception(e)
            values = {"status": "ERROR"}
        try:
            db.keypair_update(context, gid, keypair_id, values)
        except Exception as e:
            LOG.exception(e)

    def keypair_delete(self, context, nova_keypair_id):
        try:
            self.keypair_client.keypair_delete(nova_keypair_id)
        except (exception.KeypairDeleteFailed,
                exception.InvalidOpenStackCredential) as e:
            LOG.exception(e)
        except Exception as e:
            LOG.exception(e)


    def securitygroup_create(self, context, gid, securitygroup_id, name, securitygrouprules):
        values = {}
        try:
            values["neutron_securitygroup_id"] =\
             self.securitygroup_client.securitygroup_create(name)
            for securitygrouprule in securitygrouprules:                
                self.securitygrouprule_client.securitygrouprule_create(
                                     neutron_securitygroup_id=values["neutron_securitygroup_id"],
                                     protocol=securitygrouprule.get("protocol"),
                                     port_range_min=securitygrouprule.get("port_range_min"),
                                     port_range_max=securitygrouprule.get("port_range_max"),
                                     remote_neutron_securitygroup_id=securitygrouprule.get("remote_neutron_securitygroup_id"),
                                     remote_ip_prefix=securitygrouprule.get("remote_ip_prefix")
                                         )
            values["status"] = "ACTIVE"
            db.securitygroup_update(context, gid, securitygroup_id, values)
        except Exception as e:
            values["status"] = "ERROR"
            db.securitygroup_update(context, gid, securitygroup_id, values)
            LOG.exception(e)

    def securitygroup_delete(self, context, neutron_securitygroup_id):
        try:
            self.securitygroup_client.securitygroup_delete(neutron_securitygroup_id)
        except Exception as e:
            LOG.exception(e)

    def process_create(self, 
                        context, 
                        pid, 
                        ppid, 
                        gid, 
                        name, 
                        glance_image_id, 
                        nova_flavor_id, 
                        nova_keypair_id, 
                        neutron_securitygroup_ids, 
                        neutron_network_ids, 
                        metadata,
                        userdata
                        ):
        update_values = {}
        try:
            metadata["pid"] = pid
            metadata["ppid"] = ppid
            metadata["gid"] = gid
            nova_instance_id = self.process_client.process_create(name, 
                                                                  glance_image_id, 
                                                                  nova_flavor_id, 
                                                                  nova_keypair_id, 
                                                                  neutron_securitygroup_ids, 
                                                                  neutron_network_ids, 
                                                                  metadata,
                                                                  userdata)
            update_values["nova_instance_id"] = nova_instance_id
            update_values["status"] = "ACTIVE"
            db.process_update(context, gid, pid, update_values)
        except Exception as e:
            update_values["status"] = "ERROR"
            db.process_update(context, gid, pid, update_values)
            LOG.exception(e)

    def process_delete(self, context, nova_instance_id):
        try:
            self.process_client.process_delete(nova_instance_id)
        except Exception as e:
            LOG.exception(e)

