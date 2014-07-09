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
import rack_client
import testtools
import time
import logging
from novaclient.v1_1 import client as nova_client
from neutronclient.v2_0 import client as neutron_client

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.DEBUG)
shandler = logging.StreamHandler()
shandler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)s %(message)s %(filename)s:%(lineno)s")
shandler.setFormatter(formatter)
LOG.addHandler(shandler)

class RackTestCase(testtools.TestCase):
    RETRY = 30
    test_user = "integrationtest"
    keystone_endpoint = "http://localhost:5000/v2.0"

    def setUp(self):
        super(RackTestCase, self).setUp()

    def tearDown(self):
        super(RackTestCase, self).tearDown()
        LOG.debug("Cleanup OpenStack resources")
        nova = self.get_nova_client()
        neutron = self.get_neutron_client()
        #clean servers
        servers = nova.servers.list()
        for server in servers:
            LOG.debug("Delete nova instance: %s", server.id)
            nova.servers.delete(server.id)
        retry = 0
        while retry < self.RETRY:
            servers = nova.servers.list()
            if len(servers) == 0:
                break
            retry += 1
        #clean networks
        ports = neutron.list_ports()
        networks = neutron.list_networks()
        for port in ports["ports"]:
            router_id = None
            if port["device_owner"] == "network:router_interface":
                router_id = port["device_id"]
            if router_id:
                neutron.remove_interface_router(router_id, {"port_id": port["id"]})
        for network in networks["networks"]:
            if network["name"] != "public":
                LOG.debug("Delete network: %s", network["id"])
                neutron.delete_network(network["id"])
        #clean securitygroups
        securitygroups = neutron.list_security_groups()["security_groups"]
        for i in securitygroups:
            if i["name"] != "default":
                LOG.debug("Delete security group: %s", i["id"])
                neutron.delete_security_group(i["id"])
        #clean keypairs
        keypairs =  nova.keypairs.list()
        for i in keypairs:
            LOG.debug("Delete keypair: %s", i.id)
            nova.keypairs.delete(i.id)

    def get_nova_client(self):
        credentials = {
            "username": self.test_user,
            "api_key": self.test_user,
            "project_id": self.test_user,
            "auth_url": self.keystone_endpoint
        }
        return nova_client.Client(**credentials)

    def get_neutron_client(self):
        credentials = {
            "username": self.test_user,
            "password": self.test_user,
            "tenant_name": self.test_user,
            "auth_url": self.keystone_endpoint
        }
        return neutron_client.Client(**credentials)

    def _do_request(self, arg_list, func_name):
        headers = {
            "content-type": "application/json",
            "accept": "application/json",
            "X-Auth-Token": ":".join([self.test_user, self.test_user])
        }
        parser = rack_client.get_parser()

        LOG.debug(" ".join(arg_list))
        args = parser.parse_args(arg_list)
        func = getattr(rack_client, func_name)
        res = func(args, headers)
        if func_name.split("_")[1] != "delete":
            LOG.debug(res.json())

        return res

    def _wait_for_active(self, arg_list, show_func_name):
        retry = 0
        while retry < self.RETRY:
            res = self._do_request(arg_list, show_func_name)
            self.assertEquals(200, res.status_code)
            ref = res.json().values()[0]
            if ref["status"] == "ACTIVE":
                break
            elif ref["status"] == "ERROR":
                self.fail("status ERROR")
            time.sleep(2)
            retry += 1
        if retry == self.RETRY:
            self.fail("Timeout for waiting")

    def _group_list(self):
        arg_list = ["group-list"]
        return self._do_request(arg_list, "group_list")

    def _group_create(self, name, description=None):
        group_create = ["group-create", "--name", name]
        if description:
            group_create.extend(["--description", description])
        return self._do_request(group_create, "group_create")

    def _group_delete(self, gid):
        arg_list = ["group-delete", "--gid", gid]
        return self._do_request(arg_list, "group_delete")

    def _keypair_list(self, gid):
        arg_list = ["keypair-list", "--gid", gid]
        return self._do_request(arg_list, "keypair_list")

    def _keypair_create(self, gid, name=None, is_default=None):
        arg_list = ["keypair-create", "--gid", gid]
        if name:
            arg_list.extend(["--name", name])
        if is_default:
            arg_list.extend(["--is_default", is_default])
        return self._do_request(arg_list, "keypair_create")

    def _keypair_delete(self, gid, keypair_id):
        arg_list = ["keypair-delete", "--gid", gid, "--keypair_id", keypair_id]
        return self._do_request(arg_list, "keypair_delete")

    def _securitygroup_list(self, gid):
        arg_list = ["securitygroup-list", "--gid", gid]
        return self._do_request(arg_list, "securitygroup_list")

    def _securitygroup_create(self, gid, name=None, is_default=None, rules=None):
        arg_list = ["securitygroup-create", "--gid", gid]
        if name:
            arg_list.extend(["--name", name])
        if is_default:
            arg_list.extend(["--is_default", is_default])
        if rules:
            arg_list.append("--securitygrouprules")
            arg_list.extend(rules)
        return self._do_request(arg_list, "securitygroup_create")

    def _securitygroup_delete(self, gid, securitygroup_id):
        arg_list = ["securitygroup-delete", "--gid", gid, "--securitygroup_id", securitygroup_id]
        return self._do_request(arg_list, "securitygroup_delete")

    def _network_list(self, gid):
        arg_list = ["network-list", "--gid", gid]
        return self._do_request(arg_list, "network_list")

    def _network_create(self, gid, cidr, name=None, gateway=None, dns_nameservers=[], ext_router_id=None):
        arg_list = ["network-create", "--gid", gid, "--cidr", cidr]
        if name:
            arg_list.extend(["--name", name])
        if gateway:
            arg_list.extend(["--gateway", gateway])
        if dns_nameservers:
            arg_list.append("--dns_nameservers")
            arg_list.extend(dns_nameservers)
        if ext_router_id:
            arg_list.extend(["--ext_router_id", ext_router_id])
        return self._do_request(arg_list, "network_create")

    def _network_delete(self, gid, network_id):
        arg_list = ["network-delete", "--gid", gid, "--network_id", network_id]
        return self._do_request(arg_list, "network_delete")

    def _process_list(self, gid):
        arg_list = ["process-list", "--gid", gid]
        return self._do_request(arg_list, "process_list")

    def _process_create(self, gid, nova_flavor_id=None, glance_image_id=None, securitygroup_ids=None, ppid=None, name=None, keypair_id=None, metadata=None):
        arg_list = ["process-create", "--gid", gid]
        if securitygroup_ids:
            arg_list.append("--securitygroup_ids")
            arg_list.extend(securitygroup_ids)
        if nova_flavor_id:
            arg_list.extend(["--nova_flavor_id", nova_flavor_id])
        if glance_image_id:
            arg_list.extend(["--glance_image_id", glance_image_id])
        if ppid:
            arg_list.extend(["--ppid", ppid])
        if name:
            arg_list.extend(["--name", name])
        if keypair_id:
            arg_list.extend(["--keypair_id", keypair_id])
        if metadata:
            arg_list.extend(["--metadata", metadata])
        return self._do_request(arg_list, "process_create")

    def _process_delete(self, gid, pid):
        arg_list = ["process-delete", "--gid", gid, "--pid", pid]
        return self._do_request(arg_list, "process_delete")

#### test cases ####

    def test_group(self):
        name = "group1"
        description = "This is group1"

        #create
        res = self._group_create(name, description)
        self.assertEqual(201, res.status_code)
        group_ref1 = res.json()["group"]
        self.assertEquals(name, group_ref1["name"])
        self.assertEquals(description, group_ref1["description"])

        res = self._group_create("group2")
        group_ref2 = res.json()["group"]
        self.assertEqual(201, res.status_code)

        #list
        res = self._group_list()
        self.assertEquals(200, res.status_code)
        group_refs = res.json()["groups"]
        self.assertEquals(2, len(group_refs))

        #show
        arg_list = ["group-show", "--gid", group_ref1["gid"]]
        res = self._do_request(arg_list, "group_show")
        self.assertEquals(200, res.status_code)
        group_ref = res.json()["group"]
        self.assertEquals(group_ref1, group_ref)

        #update
        arg_list = ["group-update", "--gid", group_ref1["gid"], "--name", "group1-2", "--description", "Group name changed"]
        res = self._do_request(arg_list, "group_update")
        self.assertEquals(200, res.status_code)
        group_ref = res.json()["group"]
        self.assertEquals("group1-2", group_ref["name"])
        self.assertEquals("Group name changed", group_ref["description"])

        #delete
        res = self._group_delete(group_ref1["gid"])
        self.assertEquals(204, res.status_code)
        res = self._group_delete(group_ref2["gid"])
        self.assertEquals(204, res.status_code)
        res = self._group_delete(group_ref1["gid"])
        self.assertEquals(404, res.status_code)

    def test_keypair(self):
        res = self._group_create("group")
        group_ref = res.json()["group"]
        gid = group_ref["gid"]

        #create
        name = "keypair1"
        is_default = "true"
        res = self._keypair_create(gid=gid, name=name, is_default=is_default)
        self.assertEqual(202, res.status_code)
        keypair_ref1 = res.json()["keypair"]
        self.assertEqual(name, keypair_ref1["name"])
        self.assertEqual(True, keypair_ref1["is_default"])
        arg_list = ["keypair-show", "--gid", gid, "--keypair_id", keypair_ref1["keypair_id"]]
        self._wait_for_active(arg_list, "keypair_show")

        res = self._keypair_create(gid)
        self.assertEqual(202, res.status_code)
        keypair_ref2 = res.json()["keypair"]
        arg_list = ["keypair-show", "--gid", gid, "--keypair_id", keypair_ref2["keypair_id"]]
        self._wait_for_active(arg_list, "keypair_show")

        #list
        res = self._keypair_list(gid)
        self.assertEqual(200, res.status_code)
        keypair_refs = res.json()["keypairs"]
        self.assertEquals(2, len(keypair_refs))

        #update
        arg_list = ["keypair-update", "--gid", gid, "--keypair_id", keypair_ref2["keypair_id"], "--is_default", "true"]
        res = self._do_request(arg_list, "keypair_update")
        self.assertEquals(200, res.status_code)
        keypair_ref = res.json()["keypair"]
        self.assertEquals(True, keypair_ref["is_default"])

        #delete
        res = self._keypair_delete(gid, keypair_ref1["keypair_id"])
        self.assertEquals(204, res.status_code)
        res = self._keypair_delete(gid, keypair_ref2["keypair_id"])
        self.assertEquals(204, res.status_code)
        res = self._keypair_delete(gid, keypair_ref1["keypair_id"])
        self.assertEquals(404, res.status_code)

        res = self._keypair_list(gid)
        self.assertEquals(200, res.status_code)
        keypair_refs = res.json()["keypairs"]
        self.assertEquals(0, len(keypair_refs))

        res = self._group_delete(gid)
        self.assertEquals(204, res.status_code)

    def test_securitygroup(self):
        res = self._group_create("group")
        group_ref = res.json()["group"]
        gid = group_ref["gid"]

        #create
        name = "securitygroup1"
        is_default = "true"
        rules = []
        rules.append("protocol=icmp,remote_ip_prefix=10.0.0.0/24")
        rules.append("protocol=tcp,port_range_max=1023,port_range_min=1,remote_ip_prefix=10.0.0.0/24")
        rules.append("protocol=udp,port_range_max=1023,port_range_min=1,remote_ip_prefix=10.0.0.0/24")
        res = self._securitygroup_create(gid, name=name, is_default=is_default, rules=rules)
        self.assertEqual(202, res.status_code)
        securitygroup_ref1 = res.json()["securitygroup"]
        self.assertEqual(name, securitygroup_ref1["name"])
        self.assertEqual(True, securitygroup_ref1["is_default"])
        arg_list = ["securitygroup-show", "--gid", gid, "--securitygroup_id", securitygroup_ref1["securitygroup_id"]]
        self._wait_for_active(arg_list, "securitygroup_show")

        res = self._securitygroup_create(gid)
        self.assertEqual(202, res.status_code)
        securitygroup_ref2 = res.json()["securitygroup"]
        arg_list = ["securitygroup-show", "--gid", gid, "--securitygroup_id", securitygroup_ref2["securitygroup_id"]]
        self._wait_for_active(arg_list, "securitygroup_show")

        #list
        res = self._securitygroup_list(gid)
        self.assertEqual(200, res.status_code)
        securitygroup_refs = res.json()["securitygroups"]
        self.assertEquals(2, len(securitygroup_refs))

        #update
        arg_list = ["securitygroup-update", "--gid", gid, "--securitygroup_id", securitygroup_ref2["securitygroup_id"], "--is_default", "true"]
        res = self._do_request(arg_list, "securitygroup_update")
        self.assertEquals(200, res.status_code)
        securitygroup_ref = res.json()["securitygroup"]
        self.assertEquals(True, securitygroup_ref["is_default"])

        #delete
        res = self._securitygroup_delete(gid, securitygroup_ref1["securitygroup_id"])
        self.assertEquals(204, res.status_code)
        res = self._securitygroup_delete(gid, securitygroup_ref2["securitygroup_id"])
        self.assertEquals(204, res.status_code)
        res = self._securitygroup_delete(gid, securitygroup_ref1["securitygroup_id"])
        self.assertEquals(404, res.status_code)

        res = self._securitygroup_list(gid)
        self.assertEquals(200, res.status_code)
        securitygroup_refs = res.json()["securitygroups"]
        self.assertEquals(0, len(securitygroup_refs))

        res = self._group_delete(gid)
        self.assertEquals(204, res.status_code)

    def test_network(self):
        res = self._group_create("group")
        group_ref = res.json()["group"]
        gid = group_ref["gid"]

        #create
        cidr1 = "10.0.0.0/24"
        name = "network1"
        ext_router_id="50c915ab-c128-46bc-b3d0-a464bcdf1acc"
        res = self._network_create(gid, cidr1, name=name, gateway="10.0.0.254", dns_nameservers=["8.8.8.8", "8.8.4.4"], ext_router_id=ext_router_id)
        self.assertEqual(202, res.status_code)
        network_ref1 = res.json()["network"]
        self.assertEqual(cidr1, network_ref1["cidr"])
        self.assertEqual(name, network_ref1["name"])
        self.assertEqual(ext_router_id, network_ref1["ext_router_id"])
        arg_list = ["network-show", "--gid", gid, "--network_id", network_ref1["network_id"]]
        self._wait_for_active(arg_list, "network_show")

        cidr2 = "10.0.1.0/24"
        res = self._network_create(gid, cidr2)
        self.assertEqual(202, res.status_code)
        network_ref2 = res.json()["network"]
        arg_list = ["network-show", "--gid", gid, "--network_id", network_ref2["network_id"]]
        self._wait_for_active(arg_list, "network_show")

        #list
        res = self._network_list(gid)
        self.assertEqual(200, res.status_code)
        network_refs = res.json()["networks"]
        self.assertEquals(2, len(network_refs))

        """
        arg_list = ["network-update", "--gid", gid, "--network_id", network_ref1["network_id"], "--is_admin", "true"]
        res = self._do_request(arg_list, "network_update")
        self.assertEquals(200, res.status_code)
        network_ref = res.json()["network"]
        self.assertEquals(True, network_ref["is_admin"])
        """

        #delete
        res = self._network_delete(gid, network_ref1["network_id"])
        self.assertEquals(204, res.status_code)
        res = self._network_delete(gid, network_ref2["network_id"])
        self.assertEquals(204, res.status_code)
        res = self._network_delete(gid, network_ref1["network_id"])
        self.assertEquals(404, res.status_code)

        res = self._network_list(gid)
        self.assertEquals(200, res.status_code)
        network_refs = res.json()["networks"]
        self.assertEquals(0, len(network_refs))

        res = self._group_delete(gid)
        self.assertEquals(204, res.status_code)

    def test_process(self):
        #create group
        res = self._group_create("group")
        group_ref = res.json()["group"]
        gid = group_ref["gid"]

        #create keypair
        res = self._keypair_create(gid)
        self.assertEquals(202, res.status_code)
        keypair_ref1 = res.json()["keypair"]
        arg_list = ["keypair-show", "--gid", gid, "--keypair_id", keypair_ref1["keypair_id"]]
        self._wait_for_active(arg_list, "keypair_show")

        res = self._keypair_create(gid)
        self.assertEquals(202, res.status_code)
        keypair_ref2 = res.json()["keypair"]
        arg_list = ["keypair-show", "--gid", gid, "--keypair_id", keypair_ref2["keypair_id"]]
        self._wait_for_active(arg_list, "keypair_show")

        #create securitygroups
        rules = ["protocol=icmp,remote_ip_prefix=10.0.0.0/24"]
        res = self._securitygroup_create(gid, rules=rules)
        self.assertEquals(202, res.status_code)
        securitygroup_ref1 = res.json()["securitygroup"]
        arg_list = ["securitygroup-show", "--gid", gid, "--securitygroup_id", securitygroup_ref1["securitygroup_id"]]
        self._wait_for_active(arg_list, "securitygroup_show")

        rules = ["protocol=tcp,port_range_max=1023,port_range_min=1,remote_ip_prefix=10.0.0.0/24"]
        res = self._securitygroup_create(gid, rules=rules)
        self.assertEquals(202, res.status_code)
        securitygroup_ref2 = res.json()["securitygroup"]
        arg_list = ["securitygroup-show", "--gid", gid, "--securitygroup_id", securitygroup_ref2["securitygroup_id"]]
        self._wait_for_active(arg_list, "securitygroup_show")

        rules = ["protocol=udp,port_range_max=1023,port_range_min=1,remote_ip_prefix=10.0.0.0/24"]
        res = self._securitygroup_create(gid, rules=rules)
        self.assertEquals(202, res.status_code)
        securitygroup_ref3 = res.json()["securitygroup"]
        arg_list = ["securitygroup-show", "--gid", gid, "--securitygroup_id", securitygroup_ref3["securitygroup_id"]]
        self._wait_for_active(arg_list, "securitygroup_show")

        #create networks
        cidr1 = "10.0.0.0/24"
        ext_router_id="50c915ab-c128-46bc-b3d0-a464bcdf1acc"
        res = self._network_create(gid, cidr1, gateway="10.0.0.254", dns_nameservers=["8.8.8.8", "8.8.4.4"], ext_router_id=ext_router_id)
        self.assertEquals(202, res.status_code)
        network_ref1 = res.json()["network"]
        arg_list = ["network-show", "--gid", gid, "--network_id", network_ref1["network_id"]]
        self._wait_for_active(arg_list, "network_show")

        cidr2 = "10.0.1.0/24"
        res = self._network_create(gid, cidr2, dns_nameservers=["8.8.8.8", "8.8.4.4"])
        self.assertEquals(202, res.status_code)
        network_ref2 = res.json()["network"]
        arg_list = ["network-show", "--gid", gid, "--network_id", network_ref2["network_id"]]
        self._wait_for_active(arg_list, "network_show")

        #create process
        nova_flavor_id = "2"
        glance_image_id = "5aea309f-9638-44de-827d-5125ff7e4689"
        name = "process1"
        keypair_id = keypair_ref1["keypair_id"]
        securitygroup_ids = [securitygroup_ref1["securitygroup_id"], securitygroup_ref2["securitygroup_id"]]
        metadata = "key1=value1,key2=value2"
        res = self._process_create(gid, nova_flavor_id, glance_image_id, securitygroup_ids, name=name, keypair_id=keypair_id, metadata=metadata)
        self.assertEqual(202, res.status_code)
        process_ref1 = res.json()["process"]
        self.assertEqual(nova_flavor_id, process_ref1["nova_flavor_id"])
        self.assertEqual(glance_image_id, process_ref1["glance_image_id"])
        self.assertEqual(name, process_ref1["name"])
        self.assertEqual(keypair_id, process_ref1["keypair_id"])
        self.assertEqual(sorted(securitygroup_ids), sorted(process_ref1["securitygroup_ids"]))
        arg_list = ["process-show", "--gid", gid, "--pid", process_ref1["pid"]]
        self._wait_for_active(arg_list, "process_show")

        res = self._process_create(gid, ppid=process_ref1["pid"])
        self.assertEqual(202, res.status_code)
        process_ref2 = res.json()["process"]
        self.assertEqual(process_ref1["pid"], process_ref2["ppid"])
        arg_list = ["process-show", "--gid", gid, "--pid", process_ref2["pid"]]
        self._wait_for_active(arg_list, "process_show")

        #list processes
        res = self._process_list(gid)
        self.assertEqual(200, res.status_code)
        process_refs = res.json()["processes"]
        self.assertEquals(2, len(process_refs))

        #create unused network
        cidr3 = "10.0.2.0/24"
        res = self._network_create(gid, cidr3, dns_nameservers=["8.8.8.8", "8.8.4.4"])
        self.assertEquals(202, res.status_code)
        network_ref3 = res.json()["network"]
        arg_list = ["network-show", "--gid", gid, "--network_id", network_ref3["network_id"]]
        self._wait_for_active(arg_list, "network_show")

        #delete unused keypair
        res = self._keypair_delete(gid, keypair_ref2["keypair_id"])
        self.assertEquals(204, res.status_code)

        #delete used keypair
        res = self._keypair_delete(gid, keypair_ref1["keypair_id"])
        self.assertEqual(409, res.status_code)

        #delete unused securitygroup
        res = self._securitygroup_delete(gid, securitygroup_ref3["securitygroup_id"])
        self.assertEquals(204, res.status_code)

        #delete used securitygroup
        res = self._securitygroup_delete(gid, securitygroup_ref1["securitygroup_id"])
        self.assertEqual(409, res.status_code)

        #delete unused network
        res = self._network_delete(gid, network_ref3["network_id"])
        self.assertEquals(204, res.status_code)

        #delete used network
        res = self._network_delete(gid, network_ref1["network_id"])
        self.assertEqual(409, res.status_code)

        #delete used group
        res = self._group_delete(gid)
        self.assertEqual(409, res.status_code)

        #delete process
        res = self._process_delete(gid, process_ref1["pid"])
        self.assertEquals(204, res.status_code)
        res = self._process_delete(gid, process_ref2["pid"])
        self.assertEquals(404, res.status_code)
        res = self._process_delete(gid, process_ref1["pid"])
        self.assertEquals(404, res.status_code)

        res = self._process_list(gid)
        self.assertEquals(200, res.status_code)
        process_refs = res.json()["processes"]
        self.assertEquals(0, len(process_refs))

        #delete used group
        res = self._group_delete(gid)
        self.assertEqual(409, res.status_code)

        #cleanup network
        res = self._network_delete(gid, network_ref1["network_id"])
        self.assertEqual(204, res.status_code)
        res = self._network_delete(gid, network_ref2["network_id"])
        self.assertEqual(204, res.status_code)

        #delete used group
        res = self._group_delete(gid)
        self.assertEqual(409, res.status_code)

        #cleanup securitygroup
        res = self._securitygroup_delete(gid, securitygroup_ref1["securitygroup_id"])
        self.assertEqual(204, res.status_code)
        res = self._securitygroup_delete(gid, securitygroup_ref2["securitygroup_id"])
        self.assertEqual(204, res.status_code)

        #delete used group
        res = self._group_delete(gid)
        self.assertEqual(409, res.status_code)

        #cleanup keypair
        res = self._keypair_delete(gid, keypair_ref1["keypair_id"])
        self.assertEquals(204, res.status_code)

        #delete group
        res = self._group_delete(gid)
        self.assertEquals(204, res.status_code)
