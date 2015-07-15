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

from rack import exception

from rack.openstack.common import log as logging

from rack.resourceoperator.openstack import keypairs
from rack.resourceoperator.openstack import networks
from rack.resourceoperator.openstack import processes
from rack.resourceoperator.openstack import securitygroups


LOG = logging.getLogger(__name__)


class ResourceOperator(object):

    def __init__(self):
        self.keypair_client = keypairs.KeypairAPI()
        self.securitygroup_client = securitygroups.SecuritygroupAPI()
        self.network_client = networks.NetworkAPI()
        self.process_client = processes.ProcessesAPI()

    def keypair_list(self, context, keypairs):
        try:
            ids = self.keypair_client.keypair_list()
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.code, e.message)

        for keypair in keypairs:
            if keypair["nova_keypair_id"] in ids:
                keypair["status"] = "Exist"
            else:
                keypair["status"] = "NotExist"
        return keypairs

    def keypair_show(self, context, keypair):
        try:
            self.keypair_client.keypair_show(keypair["nova_keypair_id"])
            keypair["status"] = "Exist"
        except Exception as e:
            LOG.exception(e)
            if e.code == 404:
                keypair["status"] = "NotExist"
                return
            raise exception.OpenStackException(e.code, e.message)

    def keypair_create(self, context, name):
        try:
            return self.keypair_client.keypair_create(name)
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.code, e.message)

    def keypair_delete(self, context, nova_keypair_id):
        try:
            self.keypair_client.keypair_delete(nova_keypair_id)
        except Exception as e:
            LOG.exception(e)
            if e.code == 404:
                return
            raise exception.OpenStackException(e.code, e.message)

    def securitygroup_list(self, context, securitygroups):
        try:
            neutron_securitygroup_ids = self.securitygroup_client.\
                securitygroup_list()
        except Exception as e:
            raise exception.OpenStackException(e.status_code, e.message)
        for securitygroup in securitygroups:
            if securitygroup["neutron_securitygroup_id"] in\
                    neutron_securitygroup_ids:
                securitygroup["status"] = "Exist"
            else:
                securitygroup["status"] = "NotExist"
        return securitygroups

    def securitygroup_show(self, context, securitygroup):
        try:
            self.securitygroup_client.securitygroup_get(
                securitygroup['neutron_securitygroup_id'])
            securitygroup["status"] = "Exist"
        except Exception as e:
            if e.status_code == 404:
                securitygroup["status"] = "NotExist"
            else:
                raise exception.OpenStackException(e.status_code, e.message)
        return securitygroup

    def securitygroup_create(self, context, name, securitygrouprules):
        try:
            return self.securitygroup_client.securitygroup_create(
                name, securitygrouprules)
        except Exception as e:
            raise exception.OpenStackException(e.status_code, e.message)

    def securitygroup_delete(self, context, neutron_securitygroup_id):
        try:
            self.securitygroup_client.securitygroup_delete(
                neutron_securitygroup_id)
        except Exception as e:
            if e.status_code == 404:
                pass
            else:
                LOG.exception(e)
                raise exception.OpenStackException(e.status_code, e.message)

    def network_list(self, context, networks):
        try:
            ids = self.network_client.network_list()
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.status_code, e.message)

        for network in networks:
            if network["neutron_network_id"] in ids:
                network["status"] = "Exist"
            else:
                network["status"] = "NotExist"
        return networks

    def network_show(self, context, network):
        try:
            self.network_client.network_show(network["neutron_network_id"])
            network["status"] = "Exist"
        except Exception as e:
            LOG.exception(e)
            if e.status_code == 404:
                network["status"] = "NotExist"
                return
            raise exception.OpenStackException(e.status_code, e.message)

    def network_create(self, context, name, cidr, gateway, ext_router,
                       dns_nameservers):
        try:
            return self.network_client.network_create(
                name, cidr, gateway, ext_router, dns_nameservers)
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.status_code, e.message)

    def network_delete(self, context, neutron_network_id, ext_router):
        try:
            self.network_client.network_delete(neutron_network_id, ext_router)
        except Exception as e:
            LOG.exception(e)
            if e.status_code == 404:
                return
            raise exception.OpenStackException(e.status_code, e.message)

    def process_list(self, context, processes):
        try:
            nova_process_list = self.process_client.process_list()
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.code, e.message)

        for process in processes:
            is_exist = False
            for nova_process in nova_process_list:
                if process["nova_instance_id"] ==\
                        nova_process["nova_instance_id"]:
                    is_exist = True
                    process["status"] = nova_process["status"]
                    for nova_network in nova_process["networks"]:
                        for network in process["networks"]:
                            if(nova_network["display_name"] ==
                                    network["display_name"]):
                                network.update(nova_network)
                    break
            if not is_exist:
                process["status"] = "NotExist"

        return processes

    def process_show(self, context, process):
        try:
            nova_process = self.process_client.process_show(
                process["nova_instance_id"])
            process["status"] = nova_process["status"]
            for nova_network in nova_process["networks"]:
                for network in process["networks"]:
                    if(nova_network["display_name"] ==
                            network["display_name"]):
                        network.update(nova_network)

        except Exception as e:
            LOG.exception(e)
            if e.code == 404:
                process["status"] = "NotExist"
                return
            raise exception.OpenStackException(e.code, e.message)

    def process_create(self, context, name, key_name,
                       security_groups, image, flavor,
                       userdata, meta, networks):
        try:
            nics = []
            for network in networks:
                nics.append({"net-id": network["neutron_network_id"]})

            nova_instance_id, status = self.process_client.process_create(
                            name, key_name, security_groups, image, flavor,
                            userdata, meta, nics)

            for network in networks:
                if network.get("is_floating"):
                    try:
                        self.network_client.add_floatingip(
                            nova_instance_id, network["neutron_network_id"],
                            network["ext_router"])
                    except:
                        pass

            return nova_instance_id, status

        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.code, e.message)

    def process_delete(self, context, nova_instance_id):
        try:
            self.process_client.process_delete(nova_instance_id)
        except Exception as e:
            LOG.exception(e)
            if e.code == 404:
                return
            raise exception.OpenStackException(e.code, e.message)

    def get_process_address(self, context, nova_instance_id):
        try:
            return self.process_client.get_process_address(nova_instance_id)
        except Exception as e:
            LOG.exception(e)
            raise exception.OpenStackException(e.code, e.message)
