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
Unit Tests for rack.resourceoperator.openstack.networks
"""

import mox

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
    "os_auth_url": "fake"
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

    def _setup_test_network_create(self, gateway=None, dns_nameservers=None,
                                   ext_router=None):
        network_id = "fake_network_id"
        create_network_response = {"network": {"id": "fake_network_id"}}
        self.neutron_mock.create_network(
            mox.IsA(dict)).AndReturn(create_network_response)
        expected_body = {
            "subnet": {
                "network_id": network_id,
                "ip_version": 4,
                "cidr": CIDR
            }
        }
        if gateway:
            expected_body["subnet"].update(gateway_ip=gateway)
        if dns_nameservers:
            expected_body["subnet"].update(dns_nameservers=dns_nameservers)
        create_subnet_response = {"subnet": {"id": "fake_subnet_id"}}
        self.neutron_mock.create_subnet(
            expected_body).AndReturn(create_subnet_response)
        if ext_router:
            self.neutron_mock.add_interface_router(mox.IsA(str),
                                                   mox.IsA(dict))

    def test_network_create(self):
        self._setup_test_network_create()
        self.mox.ReplayAll()

        self.network_client.network_create("fake_name", CIDR)

    def test_network_create_with_parameters(self):
        parameters = {
            "gateway": "10.0.0.254",
            "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
            "ext_router": "fake_router"
        }
        self._setup_test_network_create(**parameters)
        self.mox.ReplayAll()

        self.network_client.network_create("fake_name", CIDR, **parameters)

    def test_network_raise_exception(self):
        self.neutron_mock.create_network(mox.IsA(dict)).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(exception.NetworkCreateFailed,
                          self.network_client.network_create, "fake_name",
                          CIDR)

    def test_network_delete(self):
        neutron_network_id = "fake_network_id"
        ext_router = "fake_router"
        show_network_response = {
            "network": {"subnets": ["fake_subnet1", "fake_subnet2"]}}
        self.neutron_mock.show_network(
            neutron_network_id).AndReturn(show_network_response)
        self.neutron_mock.remove_interface_router(
            ext_router, mox.IsA(dict)).MultipleTimes()
        self.neutron_mock.delete_network(neutron_network_id)
        self.mox.ReplayAll()

        self.network_client.network_delete(neutron_network_id, ext_router)

    def test_network_delete_raise_exception(self):
        neutron_network_id = "fake_network_id"
        self.neutron_mock.delete_network(
            neutron_network_id).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(exception.NetworkDeleteFailed,
                          self.network_client.network_delete,
                          neutron_network_id)
