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

from rack import context
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack.resourceoperator import manager
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
        },
        {
            "securitygroup_id": SECURITYGROUP_ID2,
            "neutron_securitygroup_id": "fake_key2",
            "gid": GID,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": "fake_key2",
            "is_default": False,
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
        "securitygroup_id": kwargs.get("securitygroup_id"),
        "neutron_securitygroup_id": kwargs.get("neutron_securitygroup_id"),
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": kwargs.get("display_name"),
        "is_default": kwargs.get("is_default")
    }


def fake_update(context, gid, securitygroup_id, kwargs):
    return {
        "securitygroup_id": securitygroup_id,
        "neutron_securitygroup_id": "test_securitygroup",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test_securitygroup",
        "is_default": kwargs.get("is_default")
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
    return {"neutron_securitygroup_id": "fake_id"}


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
        self.app = fakes.wsgi_app()

    def test_index(self):
        self.stubs.Set(db, "securitygroup_get_all", fake_securitygroup_get_all)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_list")
        securitygroup_list = [
            {
                "securitygroup_id": SECURITYGROUP_ID1,
                "neutron_securitygroup_id": "fake_key1",
                "user_id": "fake",
                "project_id": "fake",
                "gid": GID,
                "display_name": "fake_key1",
                "is_default": False,
                "status": "Exist"
            },
            {
                "securitygroup_id": SECURITYGROUP_ID2,
                "neutron_securitygroup_id": "fake_key2",
                "user_id": "fake",
                "project_id": "fake",
                "gid": GID,
                "display_name": "fake_key2",
                "is_default": False,
                "status": "Exist"
            },
        ]
        manager.ResourceOperator.securitygroup_list(
            IsA(context.RequestContext),
            IsA(list)
        ).AndReturn(securitygroup_list)
        self.mox.ReplayAll()
        expected = [
            {
                "securitygroup_id": SECURITYGROUP_ID1,
                "neutron_securitygroup_id": "fake_key1",
                "user_id": "fake",
                "project_id": "fake",
                "gid": GID,
                "name": "fake_key1",
                "is_default": False,
                "status": "Exist"
            },
            {
                "securitygroup_id": SECURITYGROUP_ID2,
                "neutron_securitygroup_id": "fake_key2",
                "user_id": "fake",
                "project_id": "fake",
                "gid": GID,
                "name": "fake_key2",
                "is_default": False,
                "status": "Exist"
            },
        ]
        url = get_base_url(GID)
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 200)
        self.assertEqual(body["securitygroups"], expected)

    def test_index_securitygroup_not_found_exception(self):
        url = get_base_url(GID + "a")
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_index_raise_exception_by_manager(self):
        self.stubs.Set(db, "securitygroup_get_all", fake_securitygroup_get_all)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_list")

        manager.ResourceOperator.securitygroup_list(
            IsA(context.RequestContext),
            IsA(list)
        ).AndRaise(exception.RackException())
        self.mox.ReplayAll()
        url = get_base_url(GID)
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    def test_show(self):
        self.stubs.Set(db, "securitygroup_get_by_securitygroup_id",
                       fake_securitygroup_get_by_securitygroup_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_show")
        securitygroup = {
            "securitygroup_id": SECURITYGROUP_ID1,
            "neutron_securitygroup_id": "fake_key1",
            "gid": GID,
            "user_id": "fake",
            "project_id": "fake",
            "display_name": "fake_key1",
            "is_default": False,
            "status": "Exist"
        }
        manager.ResourceOperator.securitygroup_show(
            IsA(context.RequestContext),
            IsA(object)
        ).AndReturn(securitygroup)
        self.mox.ReplayAll()
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
            "status": "Exist"
        }
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body["securitygroup"], expected)

    def test_show_uuidcheck_gid_not_found_exception(self):
        url = get_base_url(GID + "aaa") + "/" + SECURITYGROUP_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_show_uuidcheck_securitygroup_not_found_exception(self):
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID1 + "aaaa"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_show_db_securitygroup_not_found_exception(self):
        self.mox.StubOutWithMock(
            db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID1
        ).AndRaise(exception.SecuritygroupNotFound(
            securitygroup_id=SECURITYGROUP_ID1))
        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_show_manager_exception(self):
        self.mox.StubOutWithMock(
            db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID1
        ).AndRaise(exception.SecuritygroupNotFound(
            securitygroup_id=SECURITYGROUP_ID1))
        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_create_with_no_rules(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_create")
        name = "test_securitygroup"
        securty_group = {"neutron_securitygroup_id": "fake_id"}
        manager.ResourceOperator.securitygroup_create(
            IsA(context.RequestContext),
            name,
            IsA(list)
        ).AndReturn(securty_group)
        self.mox.StubOutWithMock(db, "securitygroup_create")
        db.securitygroup_create(IsA(context.RequestContext),
                                IsA(dict))\
            .AndReturn({"securitygroup_id": SECURITYGROUP_ID,
                        "neutron_securitygroup_id": "fake_id",
                        "gid": GID,
                        "user_id": "noauth",
                        "project_id": "noauth",
                        "display_name": name,
                        "is_default": True})
        self.mox.ReplayAll()

        request_body = {"securitygroup": {"name": name,
                                          "is_default": "true"}}

        expected = {"securitygroup": {"securitygroup_id": SECURITYGROUP_ID,
                                      "neutron_securitygroup_id": "fake_id",
                                      "gid": GID,
                                      "user_id": "noauth",
                                      "project_id": "noauth",
                                      "name": name,
                                      "is_default": True}}

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)

        for key in body["securitygroup"]:
            self.assertEqual(
                body["securitygroup"][key], expected["securitygroup"][key])

    def test_create_with_no_name(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_create")
        result_value = {"neutron_securitygroup_id": "fake_id"}
        manager.ResourceOperator.securitygroup_create(
            IsA(context.RequestContext),
            IsA(unicode),
            IsA(list)
        ).AndReturn(result_value)
        self.mox.StubOutWithMock(db, "securitygroup_create")
        name = "securitygroup-" + SECURITYGROUP_ID
        db.securitygroup_create(IsA(context.RequestContext),
                                IsA(dict))\
            .AndReturn({"securitygroup_id": SECURITYGROUP_ID,
                        "neutron_securitygroup_id": "fake_id",
                        "gid": GID,
                        "user_id": "noauth",
                        "project_id": "noauth",
                        "display_name": name,
                        "is_default": False})
        self.mox.ReplayAll()

        request_body = {
            "securitygroup": {
                "is_default": "false",
            }
        }

        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "neutron_securitygroup_id": "fake_id",
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "name": name,
                "is_default": False,
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in body["securitygroup"]:
            self.assertEqual(
                body["securitygroup"][key], expected["securitygroup"][key])

    def test_create_with_rules(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.stubs.Set(db, "securitygroup_get_by_securitygroup_id",
                       fake_securitygroup_get_by_securitygroup_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_create")
        name = "test_securitygroup"
        security_group = {"neutron_securitygroup_id": "fake_id"}
        manager.ResourceOperator.securitygroup_create(
            IsA(context.RequestContext),
            name,
            [{"protocol": "icmp",
              "port_range_max": None,
              "port_range_min": None,
              "remote_neutron_securitygroup_id": "fake_key1",
              "remote_ip_prefix": None},
             {"protocol": "tcp",
              "port_range_max": "80",
              "port_range_min": "80",
              "remote_neutron_securitygroup_id": "fake_key1",
              "remote_ip_prefix": None}]
        ).AndReturn(security_group)
        self.mox.StubOutWithMock(db, "securitygroup_create")
        db.securitygroup_create(IsA(context.RequestContext),
                                IsA(dict))\
            .AndReturn({"securitygroup_id": SECURITYGROUP_ID,
                        "neutron_securitygroup_id": "fake_id",
                        "gid": GID,
                        "user_id": "noauth",
                        "project_id": "noauth",
                        "display_name": name,
                        "is_default": True})
        self.mox.ReplayAll()

        request_body = {
            "securitygroup": {
            "name": name,
            "is_default": "true",
            "securitygrouprules": [
                {
                    "protocol": "icmp",
                    "remote_securitygroup_id": SECURITYGROUP_ID1
                },
                {
                    "port_range_max": "80",
                    "port_range_min": "80",
                    "protocol": "tcp",
                    "remote_securitygroup_id": SECURITYGROUP_ID1}
            ]
            }
        }

        expected = {"securitygroup": {"securitygroup_id": SECURITYGROUP_ID,
                                      "neutron_securitygroup_id": "fake_id",
                                      "gid": GID,
                                      "user_id": "noauth",
                                      "project_id": "noauth",
                                      "name": name,
                                      "is_default": True}}

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in body["securitygroup"]:
            self.assertEqual(
                body["securitygroup"][key], expected["securitygroup"][key])

    def test_create_exception_InvalidInput_invalid_request_body(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        request_body = {}

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_create_exception_InvalidInput_rule_is_not_list(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
            "name": name,
            "is_default": "true",
            "securitygrouprules": "fake_rules"
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_create_exception_InvalidInput_is_default_is_not_boolean(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
            "name": name,
            "is_default": "fake"
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_create_exception_HTTPNotFound_gid_not_found(self):
        self.mox.StubOutWithMock(db, "group_get_by_gid")
        db.group_get_by_gid(IsA(context.RequestContext),
                            GID)\
            .AndRaise(exception.GroupNotFound(gid=GID))
        self.mox.ReplayAll()
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
            "name": name,
            "is_default": "true"
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_create_exception_HTTPNotFound_gid_is_not_uuid(self):
        name = "test_securitygroup"
        request_body = {
            "securitygroup": {
            "name": name,
            "is_default": "true"
            }
        }

        url = get_base_url(GID + "aaa")
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_create_exception_manager_securitygroup_create(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_create")
        name = "test_securitygroup"
        manager.ResourceOperator.securitygroup_create(
            IsA(context.RequestContext),
            name,
            IsA(list)
        ).AndRaise(exception.RackException())
        self.mox.ReplayAll()

        request_body = {
            "securitygroup": {
                "name": name,
                "is_default": "true",
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_create_exception_db_securitygroup_create(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_create")
        name = "test_securitygroup"
        securty_group = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "neutron_securitygroup_id": "fake_id",
                "gid": GID,
                "display_name": name,
                "is_default": True,
            }
        }
        manager.ResourceOperator.securitygroup_create(
            IsA(context.RequestContext),
            name,
            IsA(list)
        ).AndReturn(securty_group)
        self.mox.StubOutWithMock(db, "securitygroup_create")
        db.securitygroup_create(IsA(context.RequestContext),
                                IsA(dict))\
            .AndRaise(exception.RackException())
        self.mox.ReplayAll()

        request_body = {
            "securitygroup": {
                "name": name,
                "is_default": "true",
            }
        }

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    def test_update(self):
        self.stubs.Set(db, "securitygroup_update", fake_update)
        request_body = {
            "securitygroup": {
                "is_default": "true"
            }
        }
        expected = {
            "securitygroup": {
                "securitygroup_id": SECURITYGROUP_ID,
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "neutron_securitygroup_id": "test_securitygroup",
                "name": "test_securitygroup",
                "is_default": True,
            }
        }

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 200)
        for key in body["securitygroup"]:
            self.assertEqual(
                body["securitygroup"][key], expected["securitygroup"][key])

    def test_update_exception_InValidInput_invalid_request_body(self):
        request_body = {}

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_update_exception_InValidInput_is_default_is_not_boolean(self):
        request_body = {
            "securitygroup": {
                "is_default": "fake"
            }
        }

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_update_exception_InValidInput_is_default_is_required(self):
        request_body = {
            "securitygroup": {}
        }

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 400)

    def test_update_exception_NotFound_gid_is_not_uuid(self):
        request_body = {
            "securitygroup": {
                "is_default": "true"
            }
        }

        url = get_base_url(GID + "aaa") + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_update_exception_NotFound_securitygroup_id_is_not_uuid(self):
        request_body = {
            "securitygroup": {
                "is_default": "true"
            }
        }

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID + "aaa"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_update_NotFound_db_securitygroup_create(self):
        self.mox.StubOutWithMock(db, "securitygroup_update")
        db.securitygroup_update(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID,
            IsA(dict))\
            .AndRaise(exception.SecuritygroupNotFound(
                      securitygroup_id=SECURITYGROUP_ID))
        self.mox.ReplayAll()
        request_body = {
            "securitygroup": {
                "is_default": "true"
            }
        }

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    def test_delete(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID)\
            .AndReturn({"processes": [],
                        "neutron_securitygroup_id": "fake_id"})

        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_delete")
        manager.ResourceOperator.securitygroup_delete(
            IsA(context.RequestContext),
            "fake_id")

        self.mox.StubOutWithMock(db, "securitygroup_delete")
        db.securitygroup_delete(IsA(context.RequestContext),
                                GID,
                                SECURITYGROUP_ID)
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_exception_HTTPNotFound_gid_is_not_uuid(self):
        url = get_base_url(GID + "aaa") + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exception_HTTPNotFound_securitygroup_id_is_not_uuid(self):
        url = get_base_url(GID) + "/" + SECURITYGROUP_ID + "aaa"
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exeption_HTTPNotFound_securitygroup_not_found(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID)\
            .AndRaise(exception.SecuritygroupNotFound(
                securitygroup_id=SECURITYGROUP_ID))
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exeption_manager_securitygroup_delete(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID)\
            .AndReturn({"processes": [],
                        "neutron_securitygroup_id": "fake_id"})

        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_delete")
        manager.ResourceOperator.securitygroup_delete(
            IsA(context.RequestContext),
            "fake_id")\
            .AndRaise(exception.RackException())
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_delete_exeption_HTTPNotFound_db_securitygroup_id_not_found(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID)\
            .AndReturn({"processes": [],
                        "neutron_securitygroup_id": "fake_id"})

        self.mox.StubOutWithMock(
            manager.ResourceOperator, "securitygroup_delete")
        manager.ResourceOperator.securitygroup_delete(
            IsA(context.RequestContext),
            "fake_id")

        self.mox.StubOutWithMock(db, "securitygroup_delete")
        db.securitygroup_delete(IsA(context.RequestContext),
                                GID,
                                SECURITYGROUP_ID)\
            .AndRaise(exception.SecuritygroupNotFound(
                securitygroup_id=SECURITYGROUP_ID))
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exeption_SecuritygroupInUse(self):
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext),
            GID,
            SECURITYGROUP_ID)\
            .AndReturn({"processes": [{"gid": "gid"}],
                        "neutron_securitygroup_id": "fake_id"})

        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + SECURITYGROUP_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)
