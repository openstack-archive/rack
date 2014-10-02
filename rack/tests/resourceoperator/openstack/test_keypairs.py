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

from rack.resourceoperator import openstack as os_client
from rack.resourceoperator.openstack import keypairs
from rack import test

import uuid


CONF = cfg.CONF

CREDENTIALS = {
    "os_username": "fake",
    "os_password": "fake",
    "os_tenant_name": "fake",
    "os_auth_url": "fake"
}
cfg.set_defaults(os_client.openstack_client_opts, **CREDENTIALS)


class FakeKeypairModel(object):
    id = uuid.uuid4()
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

    def test_keypair_list(self):
        fake_keypar1 = FakeKeypairModel()
        fake_keypar2 = FakeKeypairModel()
        self.nova.keypairs.list().AndReturn([fake_keypar1,
                                            fake_keypar2])
        self.mox.ReplayAll()

        keypair_ids = self.keypair_client.keypair_list()
        self.assertEqual(keypair_ids[0], fake_keypar1.id)
        self.assertEqual(keypair_ids[1], fake_keypar2.id)

    def test_keypair_show(self):
        fake_keypar1 = FakeKeypairModel()
        self.nova.keypairs.get(fake_keypar1.id)\
            .AndReturn(fake_keypar1)
        self.mox.ReplayAll()

        keypair = self.keypair_client.keypair_show(fake_keypar1.id)
        self.assertEqual(keypair, fake_keypar1)

    def test_keypair_create(self):
        fake_keypar1 = FakeKeypairModel()
        self.nova.keypairs.create(fake_keypar1.name)\
            .AndReturn(fake_keypar1)
        self.mox.ReplayAll()

        keypair = self.keypair_client.keypair_create(fake_keypar1.name)
        self.assertEqual(keypair["nova_keypair_id"], fake_keypar1.name)
        self.assertEqual(keypair["private_key"], fake_keypar1.private_key)

    def test_keypair_delete(self):
        fake_keypar1 = FakeKeypairModel()
        self.nova.keypairs.delete(fake_keypar1.id)
        self.mox.ReplayAll()

        self.keypair_client.keypair_delete(fake_keypar1.id)
