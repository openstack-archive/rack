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

import mox

CONF = cfg.CONF

CREDENTIALS = {
    "os_username": "fake",
    "os_password": "fake",
    "os_tenant_name": "fake",
    "os_auth_url": "fake"
}
cfg.set_defaults(os_client.openstack_client_opts, **CREDENTIALS)


def fake_securitygroup():
    return {"security_group": {"id": "neutron_securitygroup_id"}}


def fake_securitygrouprule():
    return {"direction": "ingress",
            "ethertype": "IPv4",
            "security_group_id": "neutron_securitygroup_id",
            "protocol": "tcp",
            "port_range_min": None,
            "port_range_max": "80"
            }


class SecuritygroupTestCase(test.NoDBTestCase):

    def setUp(self):
        super(SecuritygroupTestCase, self).setUp()
        self.securitygroup_client = securitygroups.SecuritygroupAPI()
        self.neutron = os_client.get_neutron_client()
        self.mox.StubOutWithMock(self.neutron, "create_security_group")
        self.mox.StubOutWithMock(self.neutron, "delete_security_group")
        self.mox.StubOutWithMock(os_client, "get_neutron_client")
        os_client.get_neutron_client().AndReturn(self.neutron)

    def test_securitygroup_create(self):
        name = "securitygroup"
        self.neutron.create_security_group(
            {"security_group": {"name": name}}).AndReturn(fake_securitygroup())
        self.mox.ReplayAll()

        expected = "neutron_securitygroup_id"

        values = self.securitygroup_client.securitygroup_create(name)
        self.assertEqual(expected, values)

    def test_securitygroup_create_raise_exception(self):
        name = "securitygroup"
        self.neutron.create_security_group(
            {"security_group": {"name": name}}).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(
            exception.SecuritygroupCreateFailed,
            self.securitygroup_client.securitygroup_create, name)

    def test_securitygroup_delete(self):
        neutron_securitygroup_id = "fake_securitygroup"
        self.neutron.delete_security_group(neutron_securitygroup_id)
        self.mox.ReplayAll()

        self.assertIsNone(
            self.securitygroup_client.securitygroup_delete(
                neutron_securitygroup_id))

    def test_securitygroup_delete_raise_exception(self):
        neutron_securitygroup_id = "fake_securitygroup"
        self.neutron.delete_security_group(
            neutron_securitygroup_id).AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(
            exception.SecuritygroupDeleteFailed,
            self.securitygroup_client.securitygroup_delete,
            neutron_securitygroup_id)


class SecuritygroupruleTestCase(test.NoDBTestCase):

    def setUp(self):
        super(SecuritygroupruleTestCase, self).setUp()
        self.securitygrouprule_client = securitygroups.SecuritygroupruleAPI()
        self.neutron = os_client.get_neutron_client()
        self.mox.StubOutWithMock(self.neutron, "create_security_group_rule")
        self.mox.StubOutWithMock(os_client, "get_neutron_client")
        os_client.get_neutron_client().AndReturn(self.neutron)

    def test_securitygrouprule_create_remote_ip_prefix(self):
        rule = fake_securitygrouprule()
        self.neutron.create_security_group_rule(
            {"security_group_rule":
             {"direction": rule["direction"],
              "ethertype": rule["ethertype"],
              "security_group_id": rule["security_group_id"],
              "protocol": rule["protocol"],
              "port_range_min": rule["port_range_max"],
              "port_range_max": rule["port_range_max"],
              "remote_ip_prefix": "192.168.1.1/32"
              }})
        self.mox.ReplayAll()

        self.assertIsNone(
            self.securitygrouprule_client.securitygrouprule_create(
                rule["security_group_id"],
                rule["protocol"],
                port_range_min=rule["port_range_min"],
                port_range_max=rule["port_range_max"],
                remote_ip_prefix="192.168.1.1/32",
            ))

    def test_securitygrouprule_create_remote_group_id(self):
        rule = fake_securitygrouprule()
        self.neutron.create_security_group_rule(
            {"security_group_rule":
             {"direction": rule["direction"],
              "ethertype": rule["ethertype"],
              "security_group_id": rule["security_group_id"],
              "protocol": rule["protocol"],
              "port_range_min": rule["port_range_max"],
              "port_range_max": rule["port_range_max"],
              "remote_group_id": "remote_neutron_securitygroup_id"
              }})
        self.mox.ReplayAll()

        self.assertIsNone(
            self.securitygrouprule_client.securitygrouprule_create(
                rule["security_group_id"],
                rule["protocol"],
                port_range_min=rule["port_range_min"],
                port_range_max=rule["port_range_max"],
                remote_neutron_securitygroup_id="remote_neutron_securitygroup"
                "_id",
            ))

    def test_securitygrouprule_create_raise_exception(self):
        rule = fake_securitygrouprule()
        self.neutron.create_security_group_rule(mox.IgnoreArg()).\
            AndRaise(Exception())
        self.mox.ReplayAll()

        self.assertRaises(
            exception.SecuritygroupCreateFailed,
            self.securitygrouprule_client.securitygrouprule_create,
            rule["security_group_id"],
            rule["protocol"],
            port_range_min=rule["port_range_min"],
            port_range_max=rule["port_range_max"],
            remote_neutron_securitygroup_id="remote_neutron_securitygroup_id"
        )
