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
from neutronclient.v2_0 import client as neutron_client
from oslo.config import cfg

from rack import exception
from rack.resourceoperator import openstack as os_client
from rack.resourceoperator.openstack import networks
from rack import test

CONF = cfg.CONF

CREDENTIALS = {
    "os_username": "fake",
    "os_password": "fake",
    "os_tenant_name": "fake",
    "os_auth_url": "fake",
    "os_region_name": "fake"
}
cfg.set_defaults(os_client.openstack_client_opts, **CREDENTIALS)


CIDR = "10.0.0.0/24"


class NetworkTestCase(test.NoDBTestCase):

    def setUp(self):
        super(NetworkTestCase, self).setUp()
        self.network_client = networks.NetworkAPI()
        self.neutron_mock = self.mox.CreateMock(neutron_client.Client)
        self.mox.StubOutWithMock(os_client, "get_neutron_client")
        os_client.get_neutron_client().AndReturn(self.neutron_mock)

    def test_network_list(self):
        network_list = [{"id": "fake_id1"},
                        {"id": "fake_id2"}]
        self.neutron_mock.list_networks()\
            .AndReturn({"networks": network_list})
        self.mox.ReplayAll()

        network_ids = self.network_client.network_list()
        self.assertEqual(network_ids[0], network_list[0].get("id"))
        self.assertEqual(network_ids[1], network_list[1].get("id"))

    def test_network_show(self):
        fake_neutron_network_id = "neutron_network_id"
        fake_network = {"id": "fake_id"}
        self.neutron_mock.show_network(fake_neutron_network_id)\
            .AndReturn(fake_network)
        self.mox.ReplayAll()

        network = self.network_client.network_show(fake_neutron_network_id)
        self.assertEqual(network, fake_network)

    def test_network_create_only_essential_items(self):
        fake_neutron_network_id = "fake_neutron_network_id"
        fake_subunet_id = "fake_subnet_id"
        fake_name = "fake_name"
        fake_cidr = "fake_cidr"
        fake_network = {"network": {"id": fake_neutron_network_id}}
        self.neutron_mock.create_network({"network": {"name": fake_name}})\
            .AndReturn(fake_network)
        fake_subnet_body = {"subnet": {"network_id": fake_neutron_network_id,
                                       "ip_version": 4,
                                       "cidr": fake_cidr}}
        fake_subnet = {"subnet": {"id": fake_subunet_id}}
        self.neutron_mock.create_subnet(fake_subnet_body)\
            .AndReturn(fake_subnet)
        self.mox.ReplayAll()

        network = self.network_client.network_create(fake_name,
                                                     fake_cidr)
        self.assertEqual(
            network["neutron_network_id"], fake_neutron_network_id)

    def test_network_create_all_arguments(self):
        fake_neutron_network_id = "fake_neutron_network_id"
        fake_subunet_id = "fake_subnet_id"
        fake_name = "fake_name"
        fake_cidr = "fake_cidr"
        fake_gateway = "fake_gateway"
        fake_ext_router = "fake_ext_router"
        fake_dns_nameservers = "fake_dns_nameservers"
        fake_network = {"network": {"id": fake_neutron_network_id}}

        self.neutron_mock.create_network({"network": {"name": fake_name}})\
            .AndReturn(fake_network)

        fake_subnet_body = {"subnet": {
            "network_id": fake_neutron_network_id,
            "ip_version": 4,
            "cidr": fake_cidr,
            "gateway_ip": fake_gateway,
            "dns_nameservers": fake_dns_nameservers}}
        fake_subnet = {"subnet": {"id": fake_subunet_id}}
        self.neutron_mock.create_subnet(fake_subnet_body)\
            .AndReturn(fake_subnet)

        fake_router_body = {"subnet_id": fake_subunet_id}
        self.neutron_mock.add_interface_router(fake_ext_router,
                                               fake_router_body)
        self.mox.ReplayAll()

        network = self.network_client.network_create(fake_name,
                                                     fake_cidr,
                                                     fake_gateway,
                                                     fake_ext_router,
                                                     fake_dns_nameservers)
        self.assertEqual(
            network["neutron_network_id"], fake_neutron_network_id)

    def test_network_create_exception_create_subnet_faild(self):
        fake_neutron_network_id = "fake_neutron_network_id"
        fake_subunet_id = "fake_subnet_id"
        fake_name = "fake_name"
        fake_cidr = "fake_cidr"
        fake_gateway = "fake_gateway"
        fake_ext_router = "fake_ext_router"
        fake_dns_nameservers = "fake_dns_nameservers"
        fake_network = {"network": {"id": fake_neutron_network_id}}

        self.neutron_mock.create_network({"network": {"name": fake_name}})\
            .AndReturn(fake_network)

        fake_subnet_body = {"subnet": {
            "network_id": fake_neutron_network_id,
            "ip_version": 4,
            "cidr": fake_cidr,
            "gateway_ip": fake_gateway,
            "dns_nameservers": fake_dns_nameservers}}
        fake_subnet = {"subnet": {"id": fake_subunet_id}}
        self.neutron_mock.create_subnet(fake_subnet_body)\
            .AndReturn(fake_subnet)

        fake_router_body = {"subnet_id": fake_subunet_id}
        self.neutron_mock.add_interface_router(fake_ext_router,
                                               fake_router_body)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))

        self.neutron_mock.delete_network(fake_neutron_network_id)
        self.mox.ReplayAll()

        try:
            self.network_client.network_create(fake_name,
                                               fake_cidr,
                                               fake_gateway,
                                               fake_ext_router,
                                               fake_dns_nameservers)
        except Exception as e:
            self.assertEqual(e.code, 400)
            self.assertEqual(e.message, "fake_msg")

    def test_network_create_exception_add_interface_router_faild(self):
        fake_neutron_network_id = "fake_neutron_network_id"
        fake_name = "fake_name"
        fake_cidr = "fake_cidr"
        fake_gateway = "fake_gateway"
        fake_ext_router = "fake_ext_router"
        fake_dns_nameservers = "fake_dns_nameservers"
        fake_network = {"network": {"id": fake_neutron_network_id}}

        self.neutron_mock.create_network({"network": {"name": fake_name}})\
            .AndReturn(fake_network)

        fake_subnet_body = {"subnet": {
            "network_id": fake_neutron_network_id,
            "ip_version": 4,
            "cidr": fake_cidr,
            "gateway_ip": fake_gateway,
            "dns_nameservers": fake_dns_nameservers}}
        self.neutron_mock.create_subnet(fake_subnet_body)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))

        self.neutron_mock.delete_network(fake_neutron_network_id)
        self.mox.ReplayAll()

        try:
            self.network_client.network_create(fake_name,
                                               fake_cidr,
                                               fake_gateway,
                                               fake_ext_router,
                                               fake_dns_nameservers)
        except Exception as e:
            self.assertEqual(e.code, 400)
            self.assertEqual(e.message, "fake_msg")

    def test_network_delete_ext_router_none(self):
        fake_neutron_network_id = "neutron_network_id"
        fake_subnets = ["subnet1", "subnet2"]
        fake_network = {"network": {"subnets": fake_subnets}}
        fake_ext_router = "fake_ext_router"
        self.neutron_mock.show_network(fake_neutron_network_id)\
            .AndReturn(fake_network)
        self.neutron_mock.remove_interface_router(
            fake_ext_router, {"subnet_id": fake_subnets[0]})
        self.neutron_mock.remove_interface_router(
            fake_ext_router, {"subnet_id": fake_subnets[1]})
        self.neutron_mock.delete_network(fake_neutron_network_id)
        self.mox.ReplayAll()
        self.network_client.network_delete(fake_neutron_network_id,
                                           fake_ext_router)
