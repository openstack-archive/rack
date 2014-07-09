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
 
from rack.api.v1 import securitygroups
from rack import context
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi
from rack import test
from rack.tests.api import fakes
 
import uuid
import webob
 
GID = unicode(uuid.uuid4())
SECURITYGROUP_ID = unicode(uuid.uuid4())
 
SECURITYGROUP_ID1 = unicode(uuid.uuid4())
SECURITYGROUP_ID2 = unicode(uuid.uuid4())

def _base_securitygroup_get_response(context):
    return [
        {
        "securitygroup_id": SECURITYGROUP_ID1,
        "neutron_securitygroup_id": "fake_key1",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "fake_key1",
        "is_default": False,
        "status": "ACTIVE"
        },
        {
        "securitygroup_id": SECURITYGROUP_ID2,
        "neutron_securitygroup_id": "fake_key2",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "fake_key2",
        "is_default": False,
        "status": "ACTIVE"
        },
    ]

 
def fake_group_get_by_id(context, gid):
    pass


def fake_securitygroup_get_all(context, gid, filters=None):
    return _base_securitygroup_get_response(context)
 
 
def fake_securitygroup_get_by_securitygroup_id(context, gid, securitygroup_id):
    securitygroup_list = _base_securitygroup_get_response(context)
    for securitygroup in securitygroup_list:
        if securitygroup["securitygroup_id"] == securitygroup_id:
            return securitygroup
    raise exception.SecuritygroupNotFound(securitygroup_id=securitygroup_id)
 
 
def fake_create(context, kwargs):
    return {
        "securitygroup_id": SECURITYGROUP_ID,
        "neutron_securitygroup_id": kwargs.get("neutron_securitygroup_id"),
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": kwargs.get("display_name"),
        "is_default": kwargs.get("is_default"),
        "status": "BUILDING"
    }
 
 
def fake_update(context, gid, securitygroup_id, kwargs):
    return {
        "securitygroup_id": securitygroup_id,
        "neutron_securitygroup_id": "test_securitygroup",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test_securitygroup",
        "is_default": kwargs.get("is_default"),
        "status": "ACTIVE"
    }
 

def fake_delete(context, gid, securitygroup_id):
    return {
        "securitygroup_id": securitygroup_id,
        "neutron_securitygroup_id": "test_securitygroup",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test_securitygrouppair",
        "is_default": False,
        "status": "DELETING"
    }


def fake_neutron_securitygroup_id(context, gid, securitygroup_id):
    return {"neutron_securitygroup_id":"fake_id"}


def get_request(url, method, body=None):
    req = webob.Request.blank(url)
    req.headers['Content-Type'] = 'application/json'
    req.method = method
    if body is not None:
        req.body = jsonutils.dumps(body)
    return req

def get_base_url(gid):
    return "/v1/groups/" + gid + "/securitygroups"
 
class SecuritygroupsTest(test.NoDBTestCase):
 
    def setUp(self):
        super(SecuritygroupsTest, self).setUp()
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.stubs.Set(db, "securitygroup_get_all", fake_securitygroup_get_all)
        self.stubs.Set(db, "securitygroup_get_by_securitygroup_id", fake_securitygroup_get_by_securitygroup_id)
        self.stubs.Set(db, "securitygroup_create", fake_create)
        self.stubs.Set(db, "securitygroup_update", fake_update)
        self.stubs.Set(db, "securitygroup_delete", fake_delete)
        self.mox.StubOutWithMock(scheduler_rpcapi.SchedulerAPI, "select_destinations")
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "securitygroup_create")
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "securitygroup_delete")
        self.app = fakes.wsgi_app()
 
    def test_index(self):
        url = get_base_url(GID)
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected = [
            {
            "securitygroup_id": SECURITYGROUP_ID1,
            "neutron_securitygroup_id": "fake_key1",
            "gid": GID,
            "user_id": "fake",
            "project_id": "fake",
            "name": "fake_key1",
            "is_default": False,
            "status": "ACTIVE"
            },
            {
            "securitygroup_id": SECURITYGROUP_ID2,
            "neutron_securitygroup_id": "fake_key2",
            "gid": GID,
            "user_id": "fake",
            "project_id": "fake",
            "name": "fake_key2",
            "is_default": False,
            "status": "ACTIVE"
            },
        ]
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body["securitygroups"], expected)
 
    def test_index_with_param(self):
        param = \
          "?securitygroup_id=df1c7053-ddd8-49d8-bd27-913f37f08238" + \
          "&name=sec-df1c7053-ddd8-49d8-bd27-913f37f08238" + \
          "&is_default=t&status=ACTIVE"
        url = get_base_url(GID) + param
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 200)

    def test_index_invalid_format_gid(self):
        url = get_base_url("aaaaa")
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

 
    def test_show(self):
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected = {
            "securitygroup_id": SECURITYGROUP_ID1,
            "neutron_securitygroup_id": "fake_key1",
            "gid": GID,
            "user_id": "fake",
            "project_id": "fake",
            "name": "fake_key1",
            "is_default": False,
            "status": "ACTIVE"
        }
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body["securitygroup"], expected)
 
    def test_show_invalid_format_gid(self):
        url = get_base_url("aaaaa") + "/" + SECURITYGROUP_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
  
    def test_show_invalid_format_securitygroup_id(self):
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_show_securitygroup_not_found(self):
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_create(self):
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
                "name": name,
                "is_default": "true",
            }
        }

        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=name,
                securitygrouprules=[])
        self.mox.ReplayAll()

        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": name,
                "is_default": True,
                "status": "BUILDING"
            }
        }
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in expected["securitygroup"]:
            self.assertEqual(body["securitygroup"][key], expected["securitygroup"][key])
 
    def test_create_raise_exception_by_scheduler_rpcapi(self):
        self.mox.StubOutWithMock(db, "securitygroup_update")
        db.securitygroup_update(IsA(context.RequestContext), IsA(unicode), IsA(unicode),
                          IsA(dict))
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndRaise(Exception())
        self.mox.ReplayAll()

        request_body = {
            "securitygroup": {
                "name": "test_securitygroup",
            }
        }
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)


    def test_create_raise_exception_by_operator_rpcapi(self):
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
                "name": name,
            }
        }
        
        self.mox.StubOutWithMock(db, "securitygroup_update")
        db.securitygroup_update(IsA(context.RequestContext), GID, IsA(unicode), {"status": "ERROR"})
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=name,
                securitygrouprules=[])\
            .AndRaise(Exception())
        self.mox.ReplayAll()

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_create_invalid_format_gid(self):
        request_body = {
            "securitygroup": {
                "name": "test_securitygroup",
            }
        }

        url = get_base_url('aaaaaaaa')
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_securitygroup_name_is_whitespace(self):
        request_body = {
            "securitygroup": {
                "name": " ",
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_create_securitygroup_name_with_leading_trailing_whitespace(self):
        request_body = {
            "securitygroup": {
                "name": " test_securitygroup ",
            }
        }

        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name="test_securitygroup",
                securitygrouprules=[])
        self.mox.ReplayAll()

        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test_securitygroup",
                "is_default": False,
                "status": "BUILDING"
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in expected["securitygroup"]:
            self.assertEqual(body["securitygroup"][key], expected["securitygroup"][key])
  
    def test_create_without_securitygroup_name(self):
        request_body = {
            "securitygroup": {
                "is_default": "true",
            }
        }

        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=IsA(unicode),
                securitygrouprules=[])
        self.mox.ReplayAll()

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 202)
 
    def test_create_without_is_default(self):
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
                "name": name,
            }
        }

        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=name,
                securitygrouprules=[])
        self.mox.ReplayAll()

        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test_securitygroup",
                "is_default": False,
                "status": "BUILDING"
            }
        }
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in expected["securitygroup"]:
            self.assertEqual(body["securitygroup"][key], expected["securitygroup"][key])
 
    def test_create_empty_body(self):
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=IsA(unicode),
                securitygrouprules=[])
        self.mox.ReplayAll()

        request_body = {"securitygroup": {}}
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 202)
 
    def test_create_no_body(self):
        request_body = {}
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_create_invalid_format_body(self):
        request_body = []
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_create_check_securitygroup_name_length(self):
        MAX_LENGTH = 255
        request_body = {
            "securitygroup": {
                "name": "a" * (MAX_LENGTH + 1),
            }
        }
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_create_invalid_is_default(self):
        request_body = {
            "securitygroup": {
                "name": "test_securitygroup",
                "is_default": "aaa"
            }
        }
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    
    def test_create_with_rules(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
                "name": name,
                "is_default": "true",
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmp",
                      "remote_securitygroup_id": remote_securitygroup_id
                      },
                     {
                      "port_range_max": "80",
                      "port_range_min": "80",
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id
                      },
                  {"protocol": "icmp","remote_ip_prefix": "192.168.0.0/16"},
                  {"port_range_max": "80","port_range_min": "80","protocol": "tcp","remote_ip_prefix": "192.168.0.0/16"},
                  {"port_range_max": "5000","port_range_min": "5000","protocol": "udp","remote_ip_prefix": "192.168.0.0/16"},
                     ]
 
            }
        }

        self.stubs.Set(db, "securitygroup_get_by_securitygroup_id", fake_neutron_securitygroup_id)
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_create(
                IsA(context.RequestContext), "fake_host", gid=GID, securitygroup_id=IsA(unicode), name=IsA(unicode),
                securitygrouprules=[
                    {"protocol": "icmp", "port_range_max": None, "port_range_min": None,
                     "remote_securitygroup_id": remote_securitygroup_id,
                     "remote_neutron_securitygroup_id": "fake_id",
                     "remote_ip_prefix": None},
                    {"protocol": "tcp", "port_range_max": "80", "port_range_min": "80",
                     "remote_securitygroup_id": remote_securitygroup_id,
                     "remote_neutron_securitygroup_id": "fake_id",
                     "remote_ip_prefix": None},
                    {"protocol": "icmp", "port_range_max": None, "port_range_min": None,
                     "remote_securitygroup_id": None,
                     "remote_ip_prefix": "192.168.0.0/16"},
                    {"protocol": "tcp", "port_range_max": "80", "port_range_min": "80",
                     "remote_securitygroup_id": None,
                     "remote_ip_prefix": "192.168.0.0/16"},
                    {"protocol": "udp", "port_range_max": "5000", "port_range_min": "5000",
                     "remote_securitygroup_id": None,
                     "remote_ip_prefix": "192.168.0.0/16"}
                ])
        self.mox.ReplayAll()

        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": name,
                "is_default": True,
                "status": "BUILDING",
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in expected["securitygroup"]:
            self.assertEqual(body["securitygroup"][key], expected["securitygroup"][key])

    def test_create_with_rules_not_protocol(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "remote_securitygroup_id": remote_securitygroup_id
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
    
    def test_create_with_rules_invalid_protocol(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmpp",
                      "remote_securitygroup_id": remote_securitygroup_id
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_rules_invalid_remote_securitygroup_id(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmp",
                      "remote_securitygroup_id": remote_securitygroup_id + "error"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_with_rules_invalid_remote_ip_prefix(self):
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmp",
                      "remote_ip_prefix": "error"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_rules_no_remote_securitygroup_id_and_no_remote_ip_prefix(self):
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmp",
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_rules_remote_securitygroup_id_and_remote_ip_prefix(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "icmp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_max_is_none(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_max_is_over_65535(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16",
                      "port_range_max": "65536"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_max_is_zero(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16",
                      "port_range_max": "0"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_min_is_over_65535(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16",
                      "port_range_max": "1",
                      "port_range_min": "65536"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_min_is_higher_than_port_range_max(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16",
                      "port_range_max": "1",
                      "port_range_min": "2"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_tcp_or_udp_rules_port_range_min_is_zero(self):
        remote_securitygroup_id = "b755595b-3bdf-4152-8fb0-456d5e72eb01"
        request_body = {
            "securitygroup": {
                "securitygrouprules": 
                    [
                     {
                      "protocol": "tcp",
                      "remote_securitygroup_id": remote_securitygroup_id,
                      "remote_ip_prefix": "192.168.0.0/16",
                      "port_range_max": "1",
                      "port_range_min": "0"
                      },
                     ] 
            }
        }
  
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update(self):
        request_body = {
            "securitygroup": {
                "is_default": "true"
            }
        }
        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "neutron_securitygroup_id": "test_securitygroup",
                "name": "test_securitygroup",
                "is_default": True,
                "status": "ACTIVE"
            }
        }
  
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in request_body["securitygroup"]:
            self.assertEqual(body["securitygroup"][key], expected["securitygroup"][key])
 
    def test_update_invalid_format_gid(self):
        request_body = {
            "securitygroup": {
                "is_default": "true",
            }
        }
 
        url = get_base_url("aaaaaaa") + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update_invalid_format_securitygroup_id(self):
        request_body = {
            "securitygroup": {
                "is_default": "true",
            }
        }
 
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_update_invalid_format_is_default(self):
        request_body = {
            "securitygroup": {
                "is_default": "aaa",
            }
        }
 
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_update_without_is_default(self):
        request_body = {
            "securitygroup": {
                "name": "aaa",
            }
        }
 
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_update_empty_body(self):
        request_body = {"securitygroup": {}}
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_update_no_body(self):
        request_body = {}
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_update_invalid_body(self):
        request_body = []
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
 
    def test_delete(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(IsA(context.RequestContext), 
                                                 GID, 
                                                 SECURITYGROUP_ID)\
                                                 .AndReturn({"processes":[]})
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_delete(
                IsA(context.RequestContext), "fake_host", neutron_securitygroup_id="test_securitygroup")
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)
 
    def test_delete_invalid_format_gid(self):
        url = get_base_url("aaaaaaa") + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_delete_invalid_format_securitygroup_id(self):
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_delete_securitygroup_not_found(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(IsA(context.RequestContext), 
                                                 GID, 
                                                 SECURITYGROUP_ID)\
                                                 .AndReturn({"processes":[]})
        self.mox.StubOutWithMock(db, "securitygroup_delete")
        db.securitygroup_delete(IsA(context.RequestContext), GID, SECURITYGROUP_ID)\
                .AndRaise(exception.SecuritygroupNotFound(securitygroup_id=SECURITYGROUP_ID))
        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_delete_raise_exception_by_scheduler_rpcapi(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(IsA(context.RequestContext), 
                                                 GID, 
                                                 SECURITYGROUP_ID)\
                                                 .AndReturn({"processes":[]})
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndRaise(Exception())
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_delete_raise_exception_by_operator_rpcapi(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(IsA(context.RequestContext), 
                                                 GID, 
                                                 SECURITYGROUP_ID)\
                                                 .AndReturn({"processes":[]})
        scheduler_rpcapi.SchedulerAPI.select_destinations(
                IsA(context.RequestContext), request_spec={}, filter_properties={})\
            .AndReturn({"host": "fake_host"})
        operator_rpcapi.ResourceOperatorAPI.securitygroup_delete(
                IsA(context.RequestContext), "fake_host", neutron_securitygroup_id="test_securitygroup")\
            .AndRaise(Exception())
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_delete_raise_exception_securitygroup_inuse(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(IsA(context.RequestContext), 
                                                 GID, 
                                                 SECURITYGROUP_ID)\
                                                 .AndReturn({"processes":[{"pid":"pid"}]})
        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)
