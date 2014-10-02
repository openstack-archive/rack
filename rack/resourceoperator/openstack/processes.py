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


class ProcessesAPI(object):

    def process_list(self):
        nova = os_client.get_nova_client()
        servers = nova.servers.list()
        server_status_list = []
        for server in servers:
            networks = []
            for key in server.addresses.keys():
                for address in server.addresses[key]:
                    networks.append({
                        "display_name": key,
                        address["OS-EXT-IPS:type"]: address["addr"]})
            d = {
                "nova_instance_id": server.id,
                "status": server.status,
                "networks": networks
            }
            server_status_list.append(d)
        return server_status_list

    def process_show(self, nova_instance_id):
        nova = os_client.get_nova_client()
        server = nova.servers.get(nova_instance_id)
        networks = []
        for key in server.addresses.keys():
            for address in server.addresses[key]:
                networks.append({
                    "display_name": key,
                    address["OS-EXT-IPS:type"]: address["addr"]})
        return {"status": server.status, "networks": networks}

    def process_create(self, name, key_name,
                       security_groups, image, flavor,
                       userdata, meta, nics):
        nova = os_client.get_nova_client()
        server = nova.servers.create(name=name, key_name=key_name,
                                     security_groups=security_groups,
                                     image=image, flavor=flavor,
                                     userdata=userdata, meta=meta,
                                     nics=nics)
        return (server.id, server.status)

    def process_delete(self, nova_instance_id):
        nova = os_client.get_nova_client()
        nova.servers.delete(nova_instance_id)

    def get_process_address(self, nova_instance_id):
        nova = os_client.get_nova_client()
        server = nova.servers.get(nova_instance_id)
        addresses = server.addresses
        addrs = []
        for k in addresses.keys():
            ips = addresses.get(k)
            for ip in ips:
                if ip["OS-EXT-IPS:type"] == "fixed":
                    addrs.append(ip["addr"])
        return ",".join(addrs)
