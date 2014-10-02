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
from rack.openstack.common import log as logging
from rack.resourceoperator import openstack as os_client


LOG = logging.getLogger(__name__)


class NetworkAPI(object):

    def network_list(self):
        neutron = os_client.get_neutron_client()
        networks = neutron.list_networks().get("networks")
        neutron_network_ids = []
        for network in networks:
            neutron_network_ids.append(network.get("id"))
        return neutron_network_ids

    def network_show(self, neutron_network_id):
        neutron = os_client.get_neutron_client()
        return neutron.show_network(neutron_network_id)

    def network_create(self, name, cidr, gateway=None, ext_router=None,
                       dns_nameservers=None):
        neutron = os_client.get_neutron_client()
        network_body = {"network": {"name": name}}
        network = neutron.create_network(network_body)["network"]

        try:
            subnet_body = {
                "subnet": {
                    "network_id": network["id"],
                    "ip_version": 4,
                    "cidr": cidr
                }
            }
            if gateway:
                subnet_body["subnet"]["gateway_ip"] = gateway
            if dns_nameservers:
                subnet_body["subnet"]["dns_nameservers"] = dns_nameservers
            subnet = neutron.create_subnet(subnet_body)["subnet"]

            if ext_router:
                router_body = {"subnet_id": subnet["id"]}
                neutron.add_interface_router(ext_router, router_body)
        except Exception as e:
            neutron.delete_network(network['id'])
            raise e

        return dict(neutron_network_id=network["id"])

    def network_delete(self, neutron_network_id, ext_router=None):
        neutron = os_client.get_neutron_client()

        if ext_router:
            network = neutron.show_network(neutron_network_id)["network"]
            subnets = network["subnets"]
            for subnet in subnets:
                neutron.remove_interface_router(
                    ext_router, {"subnet_id": subnet})

        neutron.delete_network(neutron_network_id)
