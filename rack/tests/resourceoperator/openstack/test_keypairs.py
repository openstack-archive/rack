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
Unit Tests for rack.resourceoperator.openstack.keypairs
"""

from oslo.config import cfg

from rack import exception
from rack.resourceoperator import openstack as os_client
from rack.resourceoperator.openstack import keypairs
from rack import test

CONF = cfg.CONF

CREDENTIALS = {
    "os_username": "fake",
    "os_password": "fake",
    "os_tenant_name": "fake",
    "os_auth_url": "fake"
}
cfg.set_defaults(os_client.openstack_client_opts, **CREDENTIALS)


class FakeKeypairModel(object):
    name = "fake_keypair"
    private_key = "fake_private_key"


class KeypairTestCase(test.NoDBTestCase):
    def setUp(self):
        super(KeypairTestCase, self).setUp()
        self.keypair_client = keypairs.KeypairAPI()
        self.nova = os_client.get_nova_client()
        self.mox.StubOutWithMock(self.nova, "keypairs")
        self.mox.StubOutWithMock(os_client, "get_nova_client")
        os_client.get_nova_client().AndReturn(self.nova)

    def test_keypair_create(self):
        name = "fake_keypair"
        self.nova.keypairs.create(name).AndReturn(FakeKeypairModel())
        self.mox.ReplayAll()

        expected = {
              "nova_keypair_id": name,
              "private_key": "fake_private_key"
        }
        values = self.keypair_client.keypair_create(name)
        self.assertEquals(expected, values)

    def test_keypair_create_raise_exception(self):
        name = "fake_keypair"
        self.nova.keypairs.create(name).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(
                exception.KeypairCreateFailed,
                self.keypair_client.keypair_create, name)

    def test_keypair_delete(self):
        nova_keypair_id = "fake_keypair"
        self.nova.keypairs.delete(nova_keypair_id)
        self.mox.ReplayAll()

        self.keypair_client.keypair_delete(nova_keypair_id)

    def test_keypair_delete_raise_exception(self):
        nova_keypair_id = "fake_keypair"
        self.nova.keypairs.delete(nova_keypair_id).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(
                exception.KeypairDeleteFailed,
                self.keypair_client.keypair_delete, nova_keypair_id)
