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
Unit Tests for rack.resourceoperator.manager
"""

import mox
from oslo.config import cfg
import uuid

from rack import context
from rack import db
from rack import exception
from rack.resourceoperator import manager as operator_manager
from rack import test
from __builtin__ import Exception

CONF = cfg.CONF

GID = unicode(uuid.uuid4())
KEYPAIR_ID = unicode(uuid.uuid4())
NETWORK_ID = unicode(uuid.uuid4())
NEUTRON_NETWORK_ID = unicode(uuid.uuid4())

NOVA_INSTANCE_ID = unicode(uuid.uuid4())



def fake_keypair_create(name):
    return {
        "nova_keypair_id": name,
        "name": name
    }
    
def fake_securitygroup_create(name):
    return "neutron_securitygroup_id"


def fake_securitygrouprule_create(neutron_securitygroup_id, protocol,
               port_range_min=None, port_range_max=None, 
               remote_neutron_securitygroup_id=None, remote_ip_prefix=None, 
               direction="ingress", ethertype="IPv4"):
    pass


def fake_network_create():
    return NEUTRON_NETWORK_ID


class ResourceOperatorManagerKeypairTestCase(test.NoDBTestCase):
    def setUp(self):
        super(ResourceOperatorManagerKeypairTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperatorManager()
        self.context = context.RequestContext('fake_user', 'fake_project')

    def test_keypair_create(self):
        self.stubs.Set(self.manager.keypair_client, "keypair_create", fake_keypair_create)
        self.mox.StubOutWithMock(db, "keypair_update")
        db.keypair_update(self.context, GID, KEYPAIR_ID, mox.IsA(dict))
        self.mox.ReplayAll()

        self.manager.keypair_create(self.context, GID, KEYPAIR_ID, "fake_keypair")

    def test_keypair_create_raise_keypair_create_failed(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_create")
        self.manager.keypair_client.keypair_create(mox.IsA(str))\
                .AndRaise(exception.KeypairCreateFailed())
        self.mox.StubOutWithMock(db, "keypair_update")
        db.keypair_update(self.context, GID, KEYPAIR_ID, {"status": "ERROR"})
        self.mox.ReplayAll()

        self.manager.keypair_create(self.context, GID, KEYPAIR_ID, "fake_keypair")

    def test_keypair_create_keypair_not_found(self):
        self.stubs.Set(self.manager.keypair_client, "keypair_create", fake_keypair_create)
        self.mox.StubOutWithMock(db, "keypair_update")
        db.keypair_update(self.context, GID, KEYPAIR_ID, mox.IsA(dict))\
                .AndRaise(exception.KeypairNotFound(keypair_id=KEYPAIR_ID))
        self.mox.ReplayAll()

        self.manager.keypair_create(self.context, GID, KEYPAIR_ID, "fake_keypair")

    def test_keypair_delete(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_delete")
        self.manager.keypair_client.keypair_delete(mox.IsA(str))
        self.mox.ReplayAll()

        self.manager.keypair_delete(self.context, "fake_keypair")

    def test_keypair_delete_raise_keypair_delete_failed(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_delete")
        self.manager.keypair_client.keypair_delete(mox.IsA(str))\
                .AndRaise(exception.KeypairDeleteFailed())
        self.mox.ReplayAll()

        self.manager.keypair_delete(self.context, "fake_keypair")


class ResourceOperatorManagerNetworkTestCase(test.NoDBTestCase):
    def setUp(self):
        super(ResourceOperatorManagerNetworkTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperatorManager()
        self.context = context.RequestContext('fake_user', 'fake_project')

    def test_create_network(self):
        self.stubs.Set(self.manager.network_client, "network_create", fake_network_create)
        self.mox.StubOutWithMock(db, "network_update")
        expected_values = {"neutron_network_id": NEUTRON_NETWORK_ID, 
                           "status": "ACTIVE"}
        db.network_update(self.context, NETWORK_ID, expected_values)
        self.mox.ReplayAll()

        network = {}
        network["network_id"] = NETWORK_ID
        self.manager.network_create(self.context, network)

    def test_create_network_exception_create_faild(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_create")
        self.manager.network_client.network_create(
                    mox.IsA(str), mox.IsA(str), mox.IsA(str), mox.IsA(str), mox.IsA(str),)\
                .AndRaise(Exception())
        self.mox.StubOutWithMock(db, "network_update")
        expected_values = {"status": "ERROR"}
        db.network_update(self.context, NETWORK_ID, expected_values)
        self.mox.ReplayAll()

        network = {
            "network_id": NETWORK_ID,
            "display_name": "fake_name",
            "subnet": "10.0.0.0/24",
            "gateway": "fake_gateway",
            "dns_nameservers": "fake_dns_nameservers",
            "ext_router": "fake_router"}
        self.manager.network_create(self.context, network)

    def test_create_network_exception_db_update_faild(self):
        self.stubs.Set(self.manager.network_client, "network_create", fake_network_create)
        self.mox.StubOutWithMock(db, "network_update")
        expected_values = {"neutron_network_id": NEUTRON_NETWORK_ID, 
                           "status": "ACTIVE"}
        db.network_update(self.context, NETWORK_ID, expected_values)\
                                                        .AndRaise(Exception())
        self.mox.ReplayAll()

        network = {}
        network["network_id"] = NETWORK_ID
        self.manager.network_create(self.context, network)

    def test_delete_network(self):
        ext_router = "fake_ext_router"
        self.mox.StubOutWithMock(self.manager.network_client, "network_delete")
        self.manager.network_client.network_delete(NEUTRON_NETWORK_ID, ext_router)
        self.mox.ReplayAll()

        self.manager.network_delete(self.context, NEUTRON_NETWORK_ID, ext_router)

    def test_delete_network_exception_delete_faild(self):
        ext_router = "fake_ext_router"
        self.mox.StubOutWithMock(self.manager.network_client, "network_delete")
        self.manager.network_client.network_delete(NEUTRON_NETWORK_ID, ext_router)\
                                                .AndRaise(Exception())
        self.mox.ReplayAll()

        self.manager.network_delete(self.context, NEUTRON_NETWORK_ID, ext_router)


class ResourceOperatorManagerSecuritygroupTestCase(test.NoDBTestCase):
    def setUp(self):
        super(ResourceOperatorManagerSecuritygroupTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperatorManager()
        self.context = context.RequestContext('fake_user', 'fake_project')
        self.securitygroup_id = "securitygroup_id"
        self.name = "securitygroup_name"
        securitygrouprule = {}
        securitygrouprule["protocol"] = ""

    def _securitygroups(self):
        return [
                {
                 "protocol": "tcp",
                 "port_range_min": None,
                 "port_range_max": "80",
                 "remote_neutron_securitygroup_id": None,
                 "remote_ip_prefix": "192.168.1.1/32",
                 },
                {
                 "protocol": "tcp",
                 "port_range_min": "1",
                 "port_range_max": "80",
                 "remote_neutron_securitygroup_id": "fake",
                 "remote_ip_prefix": None,
                 },                
                ]
        
        
    def test_securitygroup_create(self):
        self.stubs.Set(self.manager.securitygroup_client, "securitygroup_create", fake_securitygroup_create)
        self.stubs.Set(self.manager.securitygrouprule_client, "securitygrouprule_create", fake_securitygrouprule_create)
        self.mox.StubOutWithMock(db, "securitygroup_update")
        values = {}
        values["status"] = "ACTIVE"
        values["neutron_securitygroup_id"] = fake_securitygroup_create(self.name)
        db.securitygroup_update(self.context, GID, self.securitygroup_id, values)
        self.mox.ReplayAll()

        self.manager.securitygroup_create(self.context, GID, self.securitygroup_id, self.name, self._securitygroups())

    def test_securitygroup_create_no_securityrules(self):
        self.stubs.Set(self.manager.securitygroup_client, "securitygroup_create", fake_securitygroup_create)
        self.mox.StubOutWithMock(db, "securitygroup_update")
        values = {}
        values["status"] = "ACTIVE"
        values["neutron_securitygroup_id"] = fake_securitygroup_create(self.name)
        db.securitygroup_update(self.context, GID, self.securitygroup_id, values)
        self.mox.ReplayAll()

        self.manager.securitygroup_create(self.context, GID, self.securitygroup_id, self.name, [])

    def test_securitygroup_create_raise_securitygroup_create_failed(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client, "securitygroup_create")
        self.manager.securitygroup_client.securitygroup_create(mox.IsA(str))\
                .AndRaise(exception.SecuritygroupCreateFailed())
        self.mox.StubOutWithMock(db, "securitygroup_update")
        db.securitygroup_update(self.context, GID, self.securitygroup_id, {"status": "ERROR"})
        self.mox.ReplayAll()
 
        self.manager.securitygroup_create(self.context, GID, self.securitygroup_id, self.name, [])
 
    def test_securitygroup_create_raise_securitygrouprule_create_failed(self):
        self.stubs.Set(self.manager.securitygroup_client, "securitygroup_create", fake_securitygroup_create)
        self.mox.StubOutWithMock(self.manager.securitygrouprule_client, "securitygrouprule_create")
        self.manager.securitygrouprule_client.securitygrouprule_create(
                    mox.IgnoreArg(),
                    mox.IgnoreArg(),
                    mox.IgnoreArg(),
                    mox.IgnoreArg(),
                    mox.IgnoreArg(),
                    mox.IgnoreArg())\
                .AndRaise(exception.SecuritygroupCreateFailed())
        self.mox.StubOutWithMock(db, "securitygroup_update")
        values = {}
        values["status"] = "ERROR"
        values["neutron_securitygroup_id"] = fake_securitygroup_create(self.name)
        db.securitygroup_update(self.context, GID, self.securitygroup_id, values)
        self.mox.ReplayAll()
 
        self.manager.securitygroup_create(self.context, GID, self.securitygroup_id, self.name, self._securitygroups())
 
    def test_securitygroup_create_securitygroup_not_found(self):
        self.stubs.Set(self.manager.securitygroup_client, "securitygroup_create", fake_securitygroup_create)
        self.mox.StubOutWithMock(db, "securitygroup_update")
        values = {}
        values["status"] = "ACTIVE"
        values["neutron_securitygroup_id"] = fake_securitygroup_create(self.name)
        db.securitygroup_update(self.context, GID, self.securitygroup_id, values)\
                .AndRaise(exception.SecuritygroupNotFound(securitygroup_id=self.securitygroup_id))
        values["status"] = "ERROR"
        db.securitygroup_update(self.context, GID, self.securitygroup_id, values)
        self.mox.ReplayAll()
  
        self.manager.securitygroup_create(self.context, GID, self.securitygroup_id, self.name, [])
  
    def test_securitygroup_delete(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client, "securitygroup_delete")
        self.manager.securitygroup_client.securitygroup_delete(mox.IsA(str))
        self.mox.ReplayAll()
 
        self.manager.securitygroup_delete(self.context, self.securitygroup_id)

    def test_securitygroup_delete_raise_securitygroup_delete_failed(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client, "securitygroup_delete")
        self.manager.securitygroup_client.securitygroup_delete(mox.IsA(str))\
                .AndRaise(exception.SecuritygroupDeleteFailed())
        self.mox.ReplayAll()
 
        self.manager.securitygroup_delete(self.context, self.securitygroup_id)


class ResourceOperatorManagerProcessesTestCase(test.NoDBTestCase):
    def setUp(self):
        super(ResourceOperatorManagerProcessesTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperatorManager()
        self.context = context.RequestContext('fake_user', 'fake_project')
        self.nova_instance_id = unicode(uuid.uuid4())

    def test_processes_create(self):
        self.mox.StubOutWithMock(self.manager.process_client, "process_create")
        pid = "pida309f-9638-44de-827d-5125ff7e9865"
        ppid = "ppid309f-9638-44de-827d-5125ff7e1968"
        gid = "gida309f-9638-44de-827d-5125ff7e1246"
        display_name = "display_name"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        nova_flavor_id = "3"
        nova_keypair_id = "test"
        neutron_securitygroup_ids = ["947dc616-e737-4cb9-b816-52ad80cb9e37", "1892987f-3874-46ef-a487-fb8e925210ce"]
        neutron_network_ids = ["a3c6488a-a236-46f7-aab6-8f1fe91ad9ef","43015163-babe-4bee-8fe8-38470d28b2a2"]
        metadata = {"metadata": "metadata"}
        self.manager.process_client.process_create(display_name,
                                                   glance_image_id,
                                                   nova_flavor_id,
                                                   nova_keypair_id,
                                                   neutron_securitygroup_ids,
                                                   neutron_network_ids,
                                                   metadata)\
                                                   .AndReturn(self.nova_instance_id)

        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(self.context, 
                          gid, 
                          pid, 
                          {"nova_instance_id": self.nova_instance_id,
                           "status": "ACTIVE"})
        self.mox.ReplayAll()

        self.manager.process_create(self.context, 
                                     pid,
                                     ppid,
                                     gid,
                                     display_name,
                                     glance_image_id,
                                     nova_flavor_id,
                                     nova_keypair_id,
                                     neutron_securitygroup_ids,
                                     neutron_network_ids,
                                     metadata)

    def test_processes_create_catch_exception(self):
        self.mox.StubOutWithMock(self.manager.process_client, "process_create")
        pid = "pida309f-9638-44de-827d-5125ff7e9865"
        ppid = "ppid309f-9638-44de-827d-5125ff7e1968"
        gid = "gida309f-9638-44de-827d-5125ff7e1246"
        display_name = "display_name"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        nova_flavor_id = "3"
        nova_keypair_id = "test"
        neutron_securitygroup_ids = ["947dc616-e737-4cb9-b816-52ad80cb9e37", "1892987f-3874-46ef-a487-fb8e925210ce"]
        neutron_network_ids = ["a3c6488a-a236-46f7-aab6-8f1fe91ad9ef","43015163-babe-4bee-8fe8-38470d28b2a2"]
        metadata = {"metadata": "metadata"}
        self.manager.process_client.process_create(display_name,
                                                   glance_image_id,
                                                   nova_flavor_id,
                                                   nova_keypair_id,
                                                   neutron_securitygroup_ids,
                                                   neutron_network_ids,
                                                   metadata)\
                                                   .AndRaise(exception.ProcessCreateFailed())

        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(self.context, 
                          gid, 
                          pid, 
                          {"status": "ERROR"})
        self.mox.ReplayAll()

        self.manager.process_create(self.context, 
                                     pid,
                                     ppid,
                                     gid,
                                     display_name,
                                     glance_image_id,
                                     nova_flavor_id,
                                     nova_keypair_id,
                                     neutron_securitygroup_ids,
                                     neutron_network_ids,
                                     metadata)

    def test_process_delete(self):
        self.mox.StubOutWithMock(self.manager.process_client, "process_delete")
        self.manager.process_client.process_delete(self.nova_instance_id)
        self.mox.ReplayAll()
        
        self.manager.process_delete(self.context, self.nova_instance_id)

    def test_process_delete_catch_exception(self):
        self.mox.StubOutWithMock(self.manager.process_client, "process_delete")
        self.manager.process_client.process_delete(self.nova_instance_id)\
                                            .AndRaise(exception.ProcessDeleteFailed())
        self.mox.ReplayAll()
        
        self.manager.process_delete(self.context, self.nova_instance_id)