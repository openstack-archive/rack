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
Unit Tests for rack.resourceoperator.openstack.securitygroups
"""
from oslo.config import cfg

from rack import exception
from rack.resourceoperator import openstack as os_client
from rack.resourceoperator.openstack import securitygroups
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


def fake_securitygroup():
    return {"security_group": fake_securitygroup_list()[0]}


def fake_securitygroup_list():
    return [{"id": "neutron_securitygroup_id"},
            {"id": "neutron_securitygroup_id"}]


class SecuritygroupTestCase(test.NoDBTestCase):

    def setUp(self):
        super(SecuritygroupTestCase, self).setUp()
        self.securitygroup_client = securitygroups.SecuritygroupAPI()
        self.neutron = os_client.get_neutron_client()
        self.mox.StubOutWithMock(self.neutron, "list_security_groups")
        self.mox.StubOutWithMock(self.neutron, "show_security_group")
        self.mox.StubOutWithMock(self.neutron, "create_security_group")
        self.mox.StubOutWithMock(self.neutron, "create_security_group_rule")
        self.mox.StubOutWithMock(self.neutron, "delete_security_group")
        self.mox.StubOutWithMock(os_client, "get_neutron_client")
        os_client.get_neutron_client().AndReturn(self.neutron)

    def test_securitygroup_list(self):
        fake_securitygroups = {"security_groups": fake_securitygroup_list()}
        self.neutron.list_security_groups()\
            .AndReturn(fake_securitygroups)
        self.mox.ReplayAll()

        neutron_securitygroup_ids = self.securitygroup_client.\
            securitygroup_list()
        for neutron_securitygroup_id in neutron_securitygroup_ids:
            self.assertEqual(neutron_securitygroup_id,
                             "neutron_securitygroup_id")

    def test_securitygroup_get(self):
        fake_security_group = fake_securitygroup()
        fake_security_group_id = fake_security_group["security_group"]["id"]
        self.neutron.show_security_group(fake_security_group_id)\
            .AndReturn(fake_security_group)
        self.mox.ReplayAll()

        security_group_id = self.securitygroup_client.securitygroup_get(
            fake_security_group_id)
        self.assertEqual(security_group_id, fake_security_group_id)

    def test_securitygroup_create(self):
        fake_name = "fake_name"
        fake_securitygroup_id = "neutron_securitygroup_id"
        fake_sec_body = {'security_group': {'name': fake_name}}
        fake_sec_rule_body = {"security_group_rule": {
            "direction": "ingress",
            "ethertype": "IPv4",
            "security_group_id": fake_securitygroup_id,
            "protocol": "tcp",
            "port_range_min": "80",
            "port_range_max": "80"}}
        self.neutron.create_security_group(
            fake_sec_body).AndReturn(fake_securitygroup())
        self.neutron.create_security_group_rule(fake_sec_rule_body)
        self.mox.ReplayAll()

        fake_rules = [{"protocol": "tcp",
                       "port_range_max": "80"}]
        sec_group_dict = self.securitygroup_client.securitygroup_create(
            fake_name, fake_rules)
        self.assertEqual(
            sec_group_dict, {"neutron_securitygroup_id":
                             fake_securitygroup_id})

    def test_securitygroup_create_all_arguments(self):
        fake_name = "fake_name"
        fake_securitygroup_id = "neutron_securitygroup_id"
        fake_sec_body = {'security_group': {'name': fake_name}}
        fake_sec_rule_body1 = {
            "security_group_rule": {
                "direction": "ingress",
                "ethertype": "IPv4",
                "security_group_id": fake_securitygroup_id,
                "protocol": "tcp",
                "port_range_min": "80",
                "port_range_max": "80",
                "remote_group_id": "remote_neutron_securitygroup_id"}}
        fake_sec_rule_body2 = {"security_group_rule": {
            "direction": "ingress",
            "ethertype": "IPv4",
            "security_group_id": fake_securitygroup_id,
            "protocol": "tcp",
            "port_range_min": "80",
            "port_range_max": "80",
            "remote_ip_prefix": "remote_ip_prefix"}}
        self.neutron.create_security_group(
            fake_sec_body).AndReturn(fake_securitygroup())
        self.neutron.create_security_group_rule(fake_sec_rule_body1)
        self.neutron.create_security_group_rule(fake_sec_rule_body2)
        self.mox.ReplayAll()

        fake_rules = [
            {"protocol": "tcp",
             "port_range_max": "80",
             "remote_neutron_securitygroup_id":
             "remote_neutron_securitygroup_id"},
            {"protocol": "tcp",
             "port_range_max": "80",
             "remote_ip_prefix": "remote_ip_prefix"}]
        sec_group_dict = self.securitygroup_client.securitygroup_create(
            fake_name, fake_rules)
        self.assertEqual(
            sec_group_dict, {"neutron_securitygroup_id":
                             fake_securitygroup_id})

    def test_securitygroup_create_exception_securitygroup_rule_create_faild(
            self):
        fake_name = "fake_name"
        fake_securitygroup_id = "neutron_securitygroup_id"
        fake_sec_body = {'security_group': {'name': fake_name}}
        fake_sec_rule_body = {
            "security_group_rule": {"direction": "ingress",
                                    "ethertype": "IPv4",
                                    "security_group_id": fake_securitygroup_id,
                                    "protocol": "tcp",
                                    "port_range_min": "80",
                                    "port_range_max": "80"}}
        self.neutron.create_security_group(
            fake_sec_body).AndReturn(fake_securitygroup())
        self.neutron.create_security_group_rule(fake_sec_rule_body)\
            .AndRaise(exception.OpenStackException(400, "fake_msg"))
        self.neutron.delete_security_group(fake_securitygroup_id)
        self.mox.ReplayAll()

        fake_rules = [{"protocol": "tcp",
                       "port_range_max": "80"}]
        try:
            self.securitygroup_client.securitygroup_create(
                fake_name, fake_rules)
        except Exception as e:
            self.assertEqual(e.code, 400)
            self.assertEqual(e.message, "fake_msg")

    def test_securitygroup_delete(self):
        fake_security_group = fake_securitygroup()
        fake_security_group_id = fake_security_group["security_group"]["id"]
        self.neutron.delete_security_group(fake_security_group_id)
        self.mox.ReplayAll()

        self.securitygroup_client.securitygroup_delete(fake_security_group_id)
