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
from oslo.config import cfg
import uuid

from neutronclient.common import exceptions as neutron_exceptions

from __builtin__ import Exception
from rack import context
from rack import exception
from rack.resourceoperator import manager as operator_manager
from rack import test

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


def fake_keypair_list():
    return ["nova_keypair_ids1", "nova_keypair_ids2"]


def fake_securitygrouprule_create(neutron_securitygroup_id, protocol,
                                  port_range_min=None, port_range_max=None,
                                  remote_neutron_securitygroup_id=None,
                                  remote_ip_prefix=None,
                                  direction="ingress", ethertype="IPv4"):
    pass


def fake_network_create():
    return NEUTRON_NETWORK_ID


class ResourceOperatorManagerKeypairTestCase(test.NoDBTestCase):

    def setUp(self):
        super(ResourceOperatorManagerKeypairTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperator()
        self.context = context.RequestContext('fake_user', 'fake_project')

    def test_keypair_list(self):
        self.stubs.Set(
            self.manager.keypair_client, "keypair_list", fake_keypair_list)
        self.mox.ReplayAll()

        test_keypairs = [{"nova_keypair_id": "nova_keypair_ids1"},
                         {"nova_keypair_id": "nova_keypair_ids2"}]
        keypairs = self.manager.keypair_list(self.context, test_keypairs)
        for keypair in keypairs:
            self.assertEqual("Exist", keypair["status"])

    def test_keypair_list_not_exist(self):
        self.stubs.Set(
            self.manager.keypair_client, "keypair_list", fake_keypair_list)
        self.mox.ReplayAll()

        test_keypairs = [{"nova_keypair_id": "fake"},
                         {"nova_keypair_id": "fake"}]
        keypairs = self.manager.keypair_list(self.context, test_keypairs)
        for keypair in keypairs:
            self.assertEqual("NotExist", keypair["status"])

    def test_keypair_list_exception_OpenStackException(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_list")
        self.manager.keypair_client.keypair_list()\
            .AndRaise(exception.OpenStackException(400, "fake"))
        self.mox.ReplayAll()

        test_keypairs = [{"nova_keypair_id": "nova_keypair_ids1"},
                         {"nova_keypair_id": "nova_keypair_ids2"}]
        try:
            self.manager.keypair_list(self.context, test_keypairs)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake", e.message)

    def test_keypair_show(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_show")
        self.manager.keypair_client.keypair_show("fake")
        self.mox.ReplayAll()

        test_keypair = {"nova_keypair_id": "fake"}
        self.manager.keypair_show(self.context, test_keypair)
        self.assertEqual("Exist", test_keypair["status"])

    def test_keypair_show_status_not_exist(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_show")
        self.manager.keypair_client.keypair_show("fake")\
            .AndRaise(exception.OpenStackException(404, ""))
        self.mox.ReplayAll()

        test_keypair = {"nova_keypair_id": "fake"}
        self.manager.keypair_show(self.context, test_keypair)
        self.assertEqual("NotExist", test_keypair["status"])

    def test_keypair_show_exception(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_show")
        self.manager.keypair_client.keypair_show("fake")\
            .AndRaise(exception.OpenStackException(405, "fake_msg"))
        self.mox.ReplayAll()

        test_keypair = {"nova_keypair_id": "fake"}
        try:
            self.manager.keypair_show(self.context, test_keypair)
        except Exception as e:
            self.assertEqual(405, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_keypair_create(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_create")
        self.manager.keypair_client.keypair_create("fake_keypair")\
            .AndReturn({})
        self.mox.ReplayAll()

        self.manager.keypair_create(
            self.context, "fake_keypair")

    def test_keypair_create_exception(self):
        self.mox.StubOutWithMock(
            self.manager.keypair_client, "keypair_create")
        self.manager.keypair_client.keypair_create("fake_keypair")\
            .AndRaise(exception.OpenStackException(405, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.keypair_create(self.context,
                                        "fake_keypair")
        except Exception as e:
            self.assertEqual(405, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_keypair_delete(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_delete")
        self.manager.keypair_client.keypair_delete("fake_keypair")
        self.mox.ReplayAll()

        self.manager.keypair_delete(self.context, "fake_keypair")

    def test_keypair_delete_exception_404(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_delete")
        self.manager.keypair_client.keypair_delete("fake_keypair")\
            .AndRaise(exception.OpenStackException(404, "fake_msg"))
        self.mox.ReplayAll()

        self.manager.keypair_delete(self.context, "fake_keypair")

    def test_keypair_delete_exception_not_404(self):
        self.mox.StubOutWithMock(self.manager.keypair_client, "keypair_delete")
        self.manager.keypair_client.keypair_delete("fake_keypair")\
            .AndRaise(exception.OpenStackException(405, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.keypair_delete(self.context, "fake_keypair")
        except Exception as e:
            self.assertEqual(405, e.code)
            self.assertEqual("fake_msg", e.message)


class ResourceOperatorManagerNetworkTestCase(test.NoDBTestCase):

    def setUp(self):
        super(ResourceOperatorManagerNetworkTestCase, self).setUp()
        self.exception = neutron_exceptions.\
            NeutronClientException(status_code=400, message="fake_msg")
        self.manager = operator_manager.ResourceOperator()
        self.context = context.RequestContext('fake_user', 'fake_project')

    def test_network_list_exist(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_list")
        self.manager.network_client.network_list()\
            .AndReturn(["fake_neutron_network_id1",
                        "fake_neutron_network_id2"])
        self.mox.ReplayAll()

        fake_networks = [{"neutron_network_id": "fake_neutron_network_id1"},
                         {"neutron_network_id": "fake_neutron_network_id2"}]
        networks = self.manager.network_list(self.context,
                                             fake_networks)
        for network in networks:
            self.assertEqual("Exist", network["status"])

    def test_network_list_not_exist(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_list")
        self.manager.network_client.network_list()\
            .AndReturn(["fake_neutron_network_id3"])
        self.mox.ReplayAll()
        fake_networks = [
            {"neutron_network_id": "fake_neutron_network_id1"},
            {"neutron_network_id": "fake_neutron_network_id2"}]
        networks = self.manager.network_list(self.context,
                                             fake_networks)
        for network in networks:
            self.assertEqual("NotExist", network["status"])

    def test_network_list_exception_network_list_faild(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_list")
        self.manager.network_client.network_list()\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_networks = [{"neutron_network_id": "fake_neutron_network_id1"},
                         {"neutron_network_id": "fake_neutron_network_id2"}]
        try:
            self.manager.network_list(self.context, fake_networks)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_network_show_exist(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_show")
        self.manager.network_client.network_show(NEUTRON_NETWORK_ID)
        self.mox.ReplayAll()

        fake_network = {"neutron_network_id": NEUTRON_NETWORK_ID}
        self.manager.network_show(self.context,
                                  fake_network)
        self.assertEqual("Exist", fake_network["status"])

    def test_network_show_not_exist(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_show")
        self.exception.status_code = 404
        self.manager.network_client.network_show(NEUTRON_NETWORK_ID)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_network = {"neutron_network_id": NEUTRON_NETWORK_ID}
        self.manager.network_show(self.context,
                                  fake_network)
        self.assertEqual("NotExist", fake_network["status"])

    def test_network_show_exception_network_show_faild(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_show")
        self.manager.network_client.network_show(NEUTRON_NETWORK_ID)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_network = {"neutron_network_id": NEUTRON_NETWORK_ID}
        try:
            self.manager.network_show(self.context,
                                      fake_network)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_network_create(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_create")
        name = "fake_nat"
        cidr = "10.0.0.0/24"
        gateway = "10.0.0.1"
        ext_router = uuid.uuid4()
        dns_nameservers = ["8.8.8.8"]
        expected_values = {"neutron_network_id": NEUTRON_NETWORK_ID}
        self.manager.network_client.network_create(name,
                                                   cidr,
                                                   gateway,
                                                   ext_router,
                                                   dns_nameservers)\
            .AndReturn(expected_values)
        self.mox.ReplayAll()

        network = self.manager.network_create(self.context,
                                              name,
                                              cidr,
                                              gateway,
                                              ext_router,
                                              dns_nameservers)
        self.assertEqual(expected_values, network)

    def test_network_create_exception_create_faild(self):
        self.mox.StubOutWithMock(self.manager.network_client, "network_create")
        name = "fake_nat"
        cidr = "10.0.0.0/24"
        gateway = "10.0.0.1"
        ext_router = "fake_ext_router"
        dns_nameservers = ["8.8.8.8"]
        self.manager.network_client.network_create(name,
                                                   cidr,
                                                   gateway,
                                                   ext_router,
                                                   dns_nameservers)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        try:
            self.manager.network_create(self.context,
                                        name,
                                        cidr,
                                        gateway,
                                        ext_router,
                                        dns_nameservers)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_network_delete(self):
        ext_router = "fake_ext_router"
        self.mox.StubOutWithMock(self.manager.network_client,
                                 "network_delete")
        self.manager.network_client.network_delete(NEUTRON_NETWORK_ID,
                                                   ext_router)
        self.mox.ReplayAll()

        self.manager.network_delete(self.context,
                                    NEUTRON_NETWORK_ID,
                                    ext_router)

    def test_delete_network_exception_is_not404(self):
        ext_router = "fake_ext_router"
        self.mox.StubOutWithMock(self.manager.network_client,
                                 "network_delete")
        self.manager.network_client.\
            network_delete(NEUTRON_NETWORK_ID,
                           ext_router)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        try:
            self.manager.network_delete(self.context,
                                        NEUTRON_NETWORK_ID,
                                        ext_router)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_delete_network_exception_404(self):
        ext_router = "fake_ext_router"
        self.mox.StubOutWithMock(self.manager.network_client,
                                 "network_delete")
        self.exception.status_code = 404
        self.manager.network_client.\
            network_delete(NEUTRON_NETWORK_ID,
                           ext_router)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        self.manager.network_delete(self.context,
                                    NEUTRON_NETWORK_ID,
                                    ext_router)


class ResourceOperatorManagerSecuritygroupTestCase(test.NoDBTestCase):

    def setUp(self):
        super(ResourceOperatorManagerSecuritygroupTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperator()
        self.exception = neutron_exceptions.\
            NeutronClientException(status_code=400, message="fake_msg")
        self.context = context.RequestContext('fake_user', 'fake_project')
        self.name = "securitygroup_name"

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
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_create")
        self.manager.securitygroup_client.\
            securitygroup_create(self.name,
                                 self._securitygroups())\
            .AndReturn("neutron_securitygroup_id")
        self.mox.ReplayAll()

        securitygroup = self.manager.securitygroup_create(
            self.context,
            self.name,
            self._securitygroups())
        self.assertEqual("neutron_securitygroup_id", securitygroup)

    def test_securitygroup_create_exception_securitygroup_create_faild(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_create")
        self.manager.securitygroup_client.\
            securitygroup_create(self.name,
                                 self._securitygroups())\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        try:
            self.manager.securitygroup_create(
                self.context,
                self.name,
                self ._securitygroups())
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_securitygroup_list_exist(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_list")
        self.manager.securitygroup_client.\
            securitygroup_list().AndReturn(["neutron_securitygroup_id1",
                                            "neutron_securitygroup_id2"])
        self.mox.ReplayAll()

        fake_securitygroups = [
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"},
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"}]
        securitygroups = self.manager.securitygroup_list(self.context,
                                                         fake_securitygroups)
        for securitygroup in securitygroups:
            self.assertEqual("Exist", securitygroup["status"])

    def test_securitygroup_list_not_exist(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_list")
        self.manager.securitygroup_client.\
            securitygroup_list().AndReturn([])
        self.mox.ReplayAll()

        fake_securitygroups = [
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"},
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"}]
        securitygroups = self.manager.securitygroup_list(self.context,
                                                         fake_securitygroups)
        for securitygroup in securitygroups:
            self.assertEqual("NotExist", securitygroup["status"])

    def test_securitygroup_list_not_exception(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_list")
        self.manager.securitygroup_client.\
            securitygroup_list().AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_securitygroups = [
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"},
            {"neutron_securitygroup_id": "neutron_securitygroup_id1"}]
        try:
            self.manager.securitygroup_list(
                self.context,
                fake_securitygroups)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_securitygroup_show_exist(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_get")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.manager.securitygroup_client.\
            securitygroup_get(fake_neutron_securitygroup_id)
        self.mox.ReplayAll()

        fake_securitygroup = {
            "neutron_securitygroup_id": fake_neutron_securitygroup_id}
        self.manager.securitygroup_show(self.context,
                                        fake_securitygroup)
        self.assertEqual("Exist", fake_securitygroup["status"])

    def test_securitygroup_show_not_exist(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_get")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.exception.status_code = 404
        self.manager.securitygroup_client.\
            securitygroup_get("neutron_securitygroup_id1")\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_securitygroup = {
            "neutron_securitygroup_id": fake_neutron_securitygroup_id}
        self.manager.securitygroup_show(self.context,
                                        fake_securitygroup)
        self.assertEqual("NotExist", fake_securitygroup["status"])

    def test_securitygroup_show_exception_securitygroup_show_failed(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_get")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.manager.securitygroup_client.\
            securitygroup_get("neutron_securitygroup_id1")\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        fake_securitygroup = {
            "neutron_securitygroup_id": fake_neutron_securitygroup_id}
        try:
            self.manager.securitygroup_show(self.context,
                                            fake_securitygroup)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_securitygroup_delete(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_delete")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.manager.securitygroup_client.\
            securitygroup_delete(fake_neutron_securitygroup_id)
        self.mox.ReplayAll()

        self.manager.securitygroup_delete(
            self.context,
            fake_neutron_securitygroup_id)

    def test_securitygroup_delete_exception_404(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_delete")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.exception.status_code = 404
        self.manager.securitygroup_client.\
            securitygroup_delete(fake_neutron_securitygroup_id)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        self.manager.securitygroup_delete(
            self.context,
            fake_neutron_securitygroup_id)

    def test_securitygroup_delete_exception_securitygroup_delete_faild(self):
        self.mox.StubOutWithMock(self.manager.securitygroup_client,
                                 "securitygroup_delete")
        fake_neutron_securitygroup_id = "neutron_securitygroup_id1"
        self.manager.securitygroup_client.\
            securitygroup_delete(fake_neutron_securitygroup_id)\
            .AndRaise(self.exception)
        self.mox.ReplayAll()

        try:
            self.manager.securitygroup_delete(
                self.context,
                fake_neutron_securitygroup_id)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)


class ResourceOperatorManagerProcessesTestCase(test.NoDBTestCase):

    def setUp(self):
        super(ResourceOperatorManagerProcessesTestCase, self).setUp()
        self.manager = operator_manager.ResourceOperator()
        self.context = context.RequestContext('fake_user', 'fake_project')

    def test_processes_list(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_list")
        fake_processes = [{"nova_instance_id": "nova_instance_id1",
                           "status": "Active",
                           "networks": [{
                               "display_name": "00",
                               "network_id": "1",
                               "fixed": "0.0.0.1"}]},
                          {"nova_instance_id": "nova_instance_id2",
                           "status": "Active",
                           "networks": [{
                               "display_name": "01",
                               "network_id": "2",
                               "fixed": "0.0.0.2"}]}]
        self.manager.process_client.process_list().AndReturn(fake_processes)
        self.mox.ReplayAll()

        processes = self.manager.process_list(self.context,
                                              fake_processes)
        for i, process in enumerate(processes):
            self.assertEqual(fake_processes[i], process)

    def test_processes_list_not_exist(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_list")
        fake_processes = [{"nova_instance_id": "nova_instance_id1",
                           "status": "Active",
                           "networks": [{
                               "display_name": "00",
                               "network_id": "1",
                               "fixed": "0.0.0.1"}]},
                          {"nova_instance_id": "nova_instance_id2",
                           "status": "Active",
                           "networks": [{
                               "display_name": "01",
                               "network_id": "2",
                               "fixed": "0.0.0.2"}]}]

        expect = [{"nova_instance_id": "nova_instance_id",
                   "status": "NotExist",
                   "networks": [{
                       "display_name": "00",
                       "network_id": "1",
                       "fixed": "0.0.0.1"}]},
                  {"nova_instance_id": "nova_instance_id2",
                   "status": "Active",
                   "networks": [{
                       "display_name": "01",
                       "network_id": "2",
                       "fixed": "0.0.0.2"}]}]

        self.manager.process_client.process_list().AndReturn(fake_processes)
        self.mox.ReplayAll()
        actual = self.manager.process_list(self.context, expect)
        self.assertEqual(actual, expect)

    def test_processes_list_exception(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_list")
        fake_processes = [{"nova_instance_id": "nova_instance_id1",
                           "status": "Active"},
                          {"nova_instance_id": "nova_instance_id2",
                           "status": "Active"}]
        self.manager.process_client.process_list()\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.process_list(self.context, fake_processes)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_process_show(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_show")
        fake_processes = {"nova_instance_id": "nova_instance_id1",
                          "status": "Active",
                          "networks": [{
                              "display_name": "00",
                              "network_id": "1",
                              "fixed": "0.0.0.1"}]}

        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_show(
            fake_nova_instance_id).AndReturn(fake_processes)
        self.mox.ReplayAll()

        input = {"nova_instance_id": fake_nova_instance_id,
                 "networks": [{
                     "display_name": "00",
                     "network_id": "1",
                     "fixed": "0.0.0.1"}]}
        self.manager.process_show(self.context, input)
        self.assertEqual(fake_processes, input)

    def test_process_show_exception_404(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_show")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_show(fake_nova_instance_id)\
            .AndRaise(exception.OpenStackException(404, "fake_msg"))
        self.mox.ReplayAll()

        process = {"nova_instance_id": fake_nova_instance_id}
        self.manager.process_show(self.context, process)
        self.assertEqual("NotExist", process["status"])

    def test_process_show_exception_not_404(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_show")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_show(fake_nova_instance_id)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.mox.ReplayAll()

        process = {"nova_instance_id": fake_nova_instance_id}
        try:
            self.manager.process_show(self.context, process)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_process_create(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_create")
        fake_name = "fake_name"
        fake_key_name = "fake_key_name"
        face_security_groups = ["security_group_id1"]
        fake_image = "fake_image"
        fake_flavor = "fake_flavor"
        fake_userdata = "fake_userdata"
        fake_meta = "fake_meta"
        fake_nics = "fake_nics"
        fake_process = {"pid": "fake_pid"}
        self.manager.process_client.process_create(fake_name,
                                                   fake_key_name,
                                                   face_security_groups,
                                                   fake_image,
                                                   fake_flavor,
                                                   fake_userdata,
                                                   fake_meta,
                                                   fake_nics)\
            .AndReturn(fake_process)
        self.mox.ReplayAll()

        process = self.manager.process_create(self.context,
                                              fake_name,
                                              fake_key_name,
                                              face_security_groups,
                                              fake_image,
                                              fake_flavor,
                                              fake_userdata,
                                              fake_meta,
                                              fake_nics)
        self.assertEqual("fake_pid", process["pid"])

    def test_process_create_exception_process_create_faild(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_create")
        fake_name = "fake_name"
        fake_key_name = "fake_key_name"
        face_security_groups = ["security_group_id1"]
        fake_image = "fake_image"
        fake_flavor = "fake_flavor"
        fake_userdata = "fake_userdata"
        fake_meta = "fake_meta"
        fake_nics = "fake_nics"
        self.manager.process_client.process_create(fake_name,
                                                   fake_key_name,
                                                   face_security_groups,
                                                   fake_image,
                                                   fake_flavor,
                                                   fake_userdata,
                                                   fake_meta,
                                                   fake_nics)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.process_create(self.context,
                                        fake_name,
                                        fake_key_name,
                                        face_security_groups,
                                        fake_image,
                                        fake_flavor,
                                        fake_userdata,
                                        fake_meta,
                                        fake_nics)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_process_delete(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_delete")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_delete(fake_nova_instance_id)
        self.mox.ReplayAll()

        self.manager.process_delete(self.context, fake_nova_instance_id)

    def test_process_delete_exception_404(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_delete")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_delete(fake_nova_instance_id)\
            .AndRaise(exception.OpenStackException(404, "fake_msg"))
        self.mox.ReplayAll()

        self.manager.process_delete(self.context, fake_nova_instance_id)

    def test_process_delete_exception_not_404(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "process_delete")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.process_delete(fake_nova_instance_id)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.process_delete(self.context, fake_nova_instance_id)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)

    def test_get_process_address(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "get_process_address")
        fake_nova_instance_id = "nova_instance_id1"
        fake_process_address = "address1,adress2"
        self.manager.process_client.get_process_address(fake_nova_instance_id)\
            .AndReturn(fake_process_address)
        self.mox.ReplayAll()

        process_address = self.manager\
            .get_process_address(self.context, fake_nova_instance_id)
        self.assertEqual(fake_process_address, process_address)

    def test_get_process_address_exception_get_process_address_faild(self):
        self.mox.StubOutWithMock(self.manager.process_client,
                                 "get_process_address")
        fake_nova_instance_id = "nova_instance_id1"
        self.manager.process_client.get_process_address(fake_nova_instance_id)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.mox.ReplayAll()

        try:
            self.manager.get_process_address(self.context,
                                             fake_nova_instance_id)
        except Exception as e:
            self.assertEqual(400, e.code)
            self.assertEqual("fake_msg", e.message)
