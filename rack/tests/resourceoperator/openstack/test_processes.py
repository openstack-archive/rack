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
from mox import IsA
from oslo.config import cfg
from rack.resourceoperator import openstack as os_client
from rack import test

import uuid

from rack.resourceoperator.openstack import processes


class fake_process(object):
    pass


class ProcessesTest(test.NoDBTestCase):

    def setUp(self):
        super(ProcessesTest, self).setUp()
        cfg.CONF.os_username = "os_username"
        cfg.CONF.os_password = "os_password"
        cfg.CONF.os_tenant_name = "os_tenant_name"
        cfg.CONF.os_auth_url = "os_auth_url"

        self.process_client = processes.ProcessesAPI()
        self.nova = os_client.get_nova_client()
        self.mox.StubOutWithMock(self.nova, "servers")
        self.mox.StubOutWithMock(os_client, "get_nova_client")
        os_client.get_nova_client().AndReturn(self.nova)
        self.process_id = unicode(uuid.uuid4())

    def test_process_list(self):

        class _dummy(object):

            def __init__(self, id, status, addresses):
                self.id = id
                self.status = status
                self.addresses = addresses

        mock_list = []
        address1 = [
            {"OS-EXT-IPS:type": "fixed", "addr": "0.0.0.0"},
            {"OS-EXT-IPS:type": "floating", "addr": "0.0.0.1"}]
        address2 = [
            {"OS-EXT-IPS:type": "fixed", "addr": "0.0.0.3"}]
        addresses = {}
        addresses.update(network_id_1=address1)
        addresses.update(network_id_2=address2)
        mock_list.append(_dummy("1", "ACTIVE1", addresses))
        mock_list.append(_dummy("2", "ACTIVE2", addresses))
        self.nova.servers.list().AndReturn(mock_list)
        self.mox.ReplayAll()

        expect_net = [
            {"display_name": "network_id_2",
             "fixed": "0.0.0.3"},
            {"display_name": "network_id_1",
             "fixed": "0.0.0.0"},
            {"display_name": "network_id_1",
             "floating": "0.0.0.1"}]

        expect = [
            {"nova_instance_id": "1", "status": "ACTIVE1",
                "networks": expect_net},
            {"nova_instance_id": "2", "status": "ACTIVE2",
                "networks": expect_net}]
        actual = self.process_client.process_list()

        expect.sort()
        [x["networks"].sort() for x in expect]
        actual.sort()
        [x["networks"].sort() for x in actual]
        self.assertEqual(expect, actual)

    def test_process_show(self):

        class _dummy(object):

            def __init__(self, id, status, addresses):
                self.id = id
                self.status = status
                self.addresses = addresses

        address1 = [
            {"OS-EXT-IPS:type": "fixed", "addr": "0.0.0.0"},
            {"OS-EXT-IPS:type": "floating", "addr": "0.0.0.1"}]
        address2 = [
            {"OS-EXT-IPS:type": "fixed", "addr": "0.0.0.3"}]
        addresses = {}
        addresses.update(network_id_1=address1)
        addresses.update(network_id_2=address2)
        self.nova.servers.get(IsA(str)).AndReturn(
            _dummy("1", "ACTIVE1", addresses))
        self.mox.ReplayAll()

        expect_net = [
            {"display_name": "network_id_2",
             "fixed": "0.0.0.3"},
            {"display_name": "network_id_1",
             "fixed": "0.0.0.0"},
            {"display_name": "network_id_1",
             "floating": "0.0.0.1"}]

        expect = {
            "status": "ACTIVE1",
            "networks": expect_net}
        actual = self.process_client.process_show("id")
        expect["networks"].sort()
        actual["networks"].sort()
        self.assertEqual(expect, actual)

    def test_process_create(self):
        display_name = "display_name"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        nova_flavor_id = "3"
        nova_keypair_id = "test"
        neutron_securitygroup_ids = [
            "947dc616-e737-4cb9-b816-52ad80cb9e37",
            "1892987f-3874-46ef-a487-fb8e925210ce"]
        neutron_network_ids = [
            "a3c6488a-a236-46f7-aab6-8f1fe91ad9ef",
            "43015163-babe-4bee-8fe8-38470d28b2a2"]
        metadata = {"metadata": "metadata"}
        userdata = "userdata"
        process_build = fake_process()
        process_build.status = "BUILD"
        process_build.id = self.process_id
        nics = []
        for network_id in neutron_network_ids:
            nics.append(network_id)

        self.nova.servers.create(name=display_name,
                                 image=glance_image_id,
                                 flavor=nova_flavor_id,
                                 meta=metadata,
                                 userdata=userdata,
                                 nics=nics,
                                 key_name=nova_keypair_id,
                                 security_groups=neutron_securitygroup_ids)\
            .AndReturn(process_build)
        process_active = fake_process()
        process_active.status = "ACTIVE"
        process_active.id = self.process_id
        self.mox.ReplayAll()

        process_id = self.process_client.process_create(
            display_name,
            nova_keypair_id,
            neutron_securitygroup_ids,
            glance_image_id,
            nova_flavor_id,
            userdata,
            metadata,
            neutron_network_ids)
        self.assertEqual(process_id, (self.process_id, "BUILD"))

    def test_process_delete(self):
        self.nova.servers.delete(self.process_id)
        self.mox.ReplayAll()
        self.process_client.process_delete(self.process_id)

    def test_get_process_address(self):

        class _dummy(object):

            def __init__(self):
                self.addresses = {"key": [
                    {"OS-EXT-IPS:type": "fixed", "addr": "ip_data1"},
                    {"OS-EXT-IPS:type": "fixed", "addr": "ip_data2"}]}

        self.nova.servers.get(self.process_id).AndReturn(_dummy())
        self.mox.ReplayAll()
        expect = "ip_data1,ip_data2"
        actual = self.process_client.get_process_address(self.process_id)
        self.assertEqual(actual, expect)

