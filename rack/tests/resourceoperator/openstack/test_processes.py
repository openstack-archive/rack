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
from rack import test, exception
from rack.resourceoperator import openstack as os_client
import uuid

from rack.resourceoperator.openstack import processes


class fake_process(object):
    pass

class ProcessesTest(test.NoDBTestCase):
    def setUp(self):
        super(ProcessesTest, self).setUp()
        self.process_client = processes.ProcessesAPI()
        self.nova = os_client.get_nova_client()
        self.mox.StubOutWithMock(self.nova, "servers")
        self.mox.StubOutWithMock(os_client, "get_nova_client")
        os_client.get_nova_client().AndReturn(self.nova)
        self.process_id  = unicode(uuid.uuid4())

    def test_process_create(self):
        display_name = "display_name"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        nova_flavor_id = "3"
        nova_keypair_id = "test"
        neutron_securitygroup_ids = ["947dc616-e737-4cb9-b816-52ad80cb9e37", "1892987f-3874-46ef-a487-fb8e925210ce"]
        neutron_network_ids = ["a3c6488a-a236-46f7-aab6-8f1fe91ad9ef","43015163-babe-4bee-8fe8-38470d28b2a2"]
        metadata = {"metadata": "metadata"}
        userdata = "userdata"
        process_build = fake_process()
        process_build.status = "BUILD"
        process_build.id = self.process_id
        nics = []
        for network_id in neutron_network_ids:
                nics.append({"net-id": network_id})

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
        self.nova.servers.get(self.process_id)\
                                .AndReturn(process_active)
        self.mox.ReplayAll()

        process_id = self.process_client.process_create(display_name, 
                                           glance_image_id, 
                                           nova_flavor_id, 
                                           nova_keypair_id, 
                                           neutron_securitygroup_ids, 
                                           neutron_network_ids, 
                                           metadata,
                                           userdata)
        self.assertEqual(process_id, self.process_id)

    def test_process_create_raise_exception(self):
        display_name = "display_name"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        nova_flavor_id = "3"
        nova_keypair_id = "test"
        neutron_securitygroup_ids = ["947dc616-e737-4cb9-b816-52ad80cb9e37", "1892987f-3874-46ef-a487-fb8e925210ce"]
        neutron_network_ids = ["a3c6488a-a236-46f7-aab6-8f1fe91ad9ef","43015163-babe-4bee-8fe8-38470d28b2a2"]
        metadata = {"metadata": "metadata"}
        userdata = "userdata"
        process_build = fake_process()
        process_build.status = "BUILD"
        process_build.id = self.process_id
        nics = []
        for network_id in neutron_network_ids:
                nics.append({"net-id": network_id})

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
        process_active.status = "ERROR"
        process_active.id = self.process_id
        self.nova.servers.get(self.process_id)\
                                .AndReturn(process_active)
        self.mox.ReplayAll()
        self.assertRaises(
                exception.ProcessCreateFailed,
                self.process_client.process_create, 
                display_name,
                glance_image_id,
                nova_flavor_id,
                nova_keypair_id, 
                neutron_securitygroup_ids, 
                neutron_network_ids, 
                metadata,
                userdata)

    def test_process_delete(self):
        self.nova.servers.delete(self.process_id)
        self.mox.ReplayAll()

        self.process_client.process_delete(self.process_id)

    def test_process_delete_raise_exception(self):
        self.nova.servers.delete(self.process_id).AndRaise(Exception)
        self.mox.ReplayAll()

        self.assertRaises(exception.ProcessDeleteFailed,
                          self.process_client.process_delete,
                          self.process_id)
