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
from exceptions import Exception
import mox

from rack import context
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack.resourceoperator import rpcapi as resourceoperator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi
from rack import test
from rack.tests.api import fakes

import uuid
import webob

GID = unicode(uuid.uuid4())
NETWORK_ID1 = unicode(uuid.uuid4())
NETWORK_ID2 = unicode(uuid.uuid4())
RO_HOST_NAME = "host_resource_operator"
NEUTRON_NW_ID = "neutron_network_id"


def fake_create_db(context, values):
    values["network_id"] = NETWORK_ID1
    return values


def fake_group_get_by_gid(context, gid):
    return {"gid": gid,
            "status": "ACTIVE"
            }


def fake_select_destinations(context, request_spec, filter_properties):
    return {"host": RO_HOST_NAME}


def fake_network_get_all(context, gid, filters=None):
    return _return_base_network_list(context, gid, filters=None)


def fake_network_get_all_empty_list(contextm, gid):
    return []


def fake_raise_exception():
    raise Exception()


def _return_base_network_list(context, gid, filters=None):
    return [
        {
            "network_id": NETWORK_ID1,
            "neutron_network_id": None,
            "gid": gid,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": "net-45212048-abc3-43cc-89b3-377341426ac",
            "is_admin": "True",
            "subnet": "10.0.0.0/24",
            "ext_router": "91212048-abc3-43cc-89b3-377341426aca",
            "status": "BUILDING"
        },
        {
            "network_id": NETWORK_ID2,
            "neutron_network_id": None,
            "gid": gid,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": "net-13092048-abc3-43cc-89b3-377341426ac",
            "is_admin": "True",
            "subnet": "10.0.1.0/24",
            "ext_router": "91212048-abc3-43cc-89b3-377341426aca",
            "status": "BUILDING"
        }
    ]


def fake_network_get_by_network_id(context, gid, network_id):
    network_dict = _return_base_network_list(context, gid)[0]
    network_dict["processes"] = []
    return network_dict


def fake_network_delete(context, gid, network_id):
    return {
        "neutron_network_id": NEUTRON_NW_ID,
        "ext_router": "fake_ext_router"}


def get_request(url, method, body=None):
    req = webob.Request.blank(url)
    req.headers['Content-Type'] = 'application/json'
    req.method = method
    if body is not None:
        req.body = jsonutils.dumps(body)
    return req


class FakeContext(context.RequestContext):

    def elevated(self):
        """Return a consistent elevated context so we can detect it."""
        if not hasattr(self, '_elevated'):
            self._elevated = super(FakeContext, self).elevated()
        return self._elevated


class NetworksTest(test.NoDBTestCase):

    def setUp(self):
        super(NetworksTest, self).setUp()
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        self.app = fakes.wsgi_app()
        # fake context
        self.user_id = 'fake'
        self.project_id = 'fake'
        self.context = FakeContext(self.user_id, self.project_id)

    # Tests for create ###
    def test_create(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.StubOutWithMock(
            resourceoperator_rpcapi.ResourceOperatorAPI, "network_create")
        resourceoperator_rpcapi.ResourceOperatorAPI.network_create(
            mox.IsA(context.RequestContext),
            RO_HOST_NAME,
            mox.IsA(dict))
        self.mox.ReplayAll()

        request_body = {
            "network": {
                "is_admin": "True",
                "name": "network-test",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        expected_body = {
            "network": {
                "network_id": NETWORK_ID1,
                "neutron_network_id": None,
                "name": "network-test",
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "is_admin": True,
                "cidr": "10.0.0.0/24",
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca",
                "status": "BUILDING"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in expected_body["network"]:
            self.assertEqual(
                body["network"][key], expected_body["network"][key])
        self.assertEqual(res.status_code, 202)

    def test_create_validate_exception_by_gid_notfound_format(self):
        request_body = {
            "network": {
                "name": "test_network",
                "is_admin": "True",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + "a" + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_validate_exception_by_gid_notfound(self):
        self.mox.StubOutWithMock(
            db, "group_get_by_gid")
        db.group_get_by_gid(
            mox.IsA(context.RequestContext),
            GID)\
            .AndRaise(exception.GroupNotFound(gid=GID))
        self.mox.ReplayAll()
        request_body = {
            "network": {
                "name": "test_network",
                "is_admin": "True",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_validate_exception_no_body(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_body_format(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "name": "test_network",
            "is_admin": "True",
            "cidr": "10.0.0.0/24",
            "gateway": "10.0.0.254",
            "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
            "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_by_cidr_required_none(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "is_admin": "True",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_by_cidr_required_format(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "is_admin": "True",
                "cidr": "10.0.",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_by_required_item(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.StubOutWithMock(
            resourceoperator_rpcapi.ResourceOperatorAPI, "network_create")
        resourceoperator_rpcapi.ResourceOperatorAPI.network_create(
            mox.IsA(context.RequestContext),
            RO_HOST_NAME,
            mox.IsA(dict))
        self.mox.ReplayAll()

        request_body = {
            "network": {
                "cidr": "10.0.0.0/24",
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 202)

    def test_create_by_name_blank(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.StubOutWithMock(
            resourceoperator_rpcapi.ResourceOperatorAPI, "network_create")
        resourceoperator_rpcapi.ResourceOperatorAPI.network_create(
            mox.IsA(context.RequestContext),
            RO_HOST_NAME,
            mox.IsA(dict))
        self.mox.ReplayAll()

        request_body = {
            "network": {
                "name": "",
                "is_admin": "True",
                "cidr": "10.0.0.0/24"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 202)

    def test_create_validate_exception_by_name_max_length(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        name_max_length = 255
        request_body = {
            "network": {
                "name": "a" * (name_max_length + 1),
                "is_admin": "True",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_by_is_admin_not_boolean(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "cidr": "10.0.0.0/24",
                "is_admin": "admin",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_by_gateway_format(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "cidr": "10.0.0.0/24",
                "is_admin": "True",
                "gateway": "adfad",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_validate_exception_by_dns_format(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "cidr": "10.0.0.0/24",
                "is_admin": "True",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8258", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_with_empty_string_in_dns_nameservers(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "cidr": "10.0.0.0/24",
                "is_admin": "True",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["", ""],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_exception_scheduler_rpcapi(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndRaise(Exception)

        self.mox.StubOutWithMock(db, "network_update")
        error_values = {"status": "ERROR"}
        db.network_update(mox.IsA(context.RequestContext),
                          NETWORK_ID1,
                          error_values)

        self.mox.ReplayAll()

        request_body = {
            "network": {
                "is_admin": "True",
                "name": "network-test",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    def test_create_exception_resorceoperator_rpcapi(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        self.stubs.Set(resourceoperator_rpcapi.ResourceOperatorAPI,
                       "network_create",
                       fake_raise_exception)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.StubOutWithMock(db, "network_update")
        error_values = {"status": "ERROR"}
        db.network_update(mox.IsA(context.RequestContext),
                          NETWORK_ID1,
                          error_values)
        self.mox.ReplayAll()

        request_body = {
            "network": {
                "is_admin": "True",
                "name": "network-test",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }
        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    # Tests for index ###
    def test_index(self):
        self.stubs.Set(
            db, "network_get_all", fake_network_get_all)

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected_body = {"networks":
                         [
                             {
                                 "network_id": NETWORK_ID1,
                                 "neutron_network_id": None,
                                 "gid": GID,
                                 "user_id": "fake",
                                 "project_id": "fake",
                                 "name": "net-45212048-abc3-43cc-89b3-3773414"
                                 "26ac",
                                 "is_admin": "True",
                                 "cidr": "10.0.0.0/24",
                                 "ext_router_id": "91212048-abc3-43cc-89b3-37"
                                 "7341426aca",
                                 "status": "BUILDING"
                             },
                             {
                                 "network_id": NETWORK_ID2,
                                 "neutron_network_id": None,
                                 "gid": GID,
                                 "user_id": "fake",
                                 "project_id": "fake",
                                 "name": "net-13092048-abc3-43cc-89b3-3773414"
                                 "26ac",
                                 "is_admin": "True",
                                 "cidr": "10.0.1.0/24",
                                 "ext_router_id": "91212048-abc3-43cc-89b3-37"
                                 "7341426aca",
                                 "status": "BUILDING"
                             }
                         ]
                         }

        self.assertEqual(body, expected_body)
        self.assertEqual(res.status_code, 200)

    def test_index_with_param(self):
        self.stubs.Set(
            db, "network_get_all", fake_network_get_all)
        param = \
            "?network_id=" + NETWORK_ID1 + \
            "?neutron_network_id=" + NETWORK_ID1 + \
            "?status=" + NETWORK_ID1 + \
            "?is_admin=" + NETWORK_ID1 + \
            "?subnet=" + NETWORK_ID1 + \
            "?ext_router=" + NETWORK_ID1 + \
            "&name=test"
        url = "/v1/groups/" + GID + "/networks" + param
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 200)

    def test_index_return_empty_list(self):
        self.stubs.Set(
            db, "network_get_all", fake_network_get_all_empty_list)

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected_body = {"networks": []}

        self.assertEqual(body, expected_body)
        self.assertEqual(res.status_code, 200)

    def test_index_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    # Tests for show ###
    def test_show(self):
        self.stubs.Set(
            db, "network_get_by_network_id", fake_network_get_by_network_id)

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url + "/" + NETWORK_ID1, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        expected_body = {"network":
                         {
                             "network_id": NETWORK_ID1,
                             "neutron_network_id": None,
                             "gid": GID,
                             "user_id": "fake",
                             "project_id": "fake",
                             "name": "net-45212048-abc3-43cc-89b3-377341426ac",
                             "is_admin": "True",
                             "cidr": "10.0.0.0/24",
                             "ext_router_id": "91212048-abc3-43cc-89b3-377341"
                             "426aca",
                             "status": "BUILDING"
                         }
                         }
        self.assertEqual(body, expected_body)
        self.assertEqual(res.status_code, 200)

    def test_show_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks/' + NETWORK_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_validate_exception_by_network_id_format(self):
        not_uuid_network_id = "aaaaa"
        url = '/v1/groups/' + GID + '/networks/' + not_uuid_network_id
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_exception_networknotfound(self):
        self.mox.StubOutWithMock(
            db, "network_get_by_network_id")
        db.network_get_by_network_id(
            mox.IsA(context.RequestContext),
            GID,
            NETWORK_ID1)\
            .AndRaise(exception.NetworkNotFound(network_id=NETWORK_ID1))
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url + "/" + NETWORK_ID1, 'GET')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 404)

    # Tests for delete ###
    def test_delete(self):
        self.stubs.Set(
            db, "network_get_by_network_id", fake_network_get_by_network_id)
        self.stubs.Set(
            db, "network_delete", fake_network_delete)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(
                context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.StubOutWithMock(
            resourceoperator_rpcapi.ResourceOperatorAPI, "network_delete")
        resourceoperator_rpcapi.ResourceOperatorAPI.network_delete(
            mox.IsA(
                context.RequestContext),
            RO_HOST_NAME,
            neutron_network_id=NEUTRON_NW_ID,
            ext_router="fake_ext_router")
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 204)

    def test_delete_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_validate_exception_by_network_id_format(self):
        not_uuid_network_id = "aaaaa"
        url = '/v1/groups/' + GID + '/networks/' + not_uuid_network_id
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exception_scheduler_rpcapi(self):
        self.stubs.Set(
            db, "network_get_by_network_id", fake_network_get_by_network_id)
        self.stubs.Set(db, "network_delete", fake_network_delete)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndRaise(Exception)

        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    def test_delete_exception_resorceoperator_rpcapi(self):
        self.stubs.Set(
            db, "network_get_by_network_id", fake_network_get_by_network_id)
        self.stubs.Set(db, "network_delete", fake_network_delete)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        self.stubs.Set(resourceoperator_rpcapi.ResourceOperatorAPI,
                       "network_delete", fake_raise_exception)
        request_spec = {}
        filter_properties = {}
        self.mox.StubOutWithMock(
            scheduler_rpcapi.SchedulerAPI, "select_destinations")
        scheduler_rpcapi.SchedulerAPI.select_destinations(
            mox.IsA(context.RequestContext),
            request_spec,
            filter_properties)\
            .AndReturn({"host": RO_HOST_NAME})

        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 500)

    def test_delete_exception_inuse(self):
        self.mox.StubOutWithMock(db, "network_get_by_network_id")
        network_process_inuse = {"processes": [{"pid": "pid"}]}
        db.network_get_by_network_id(mox.IsA(context.RequestContext),
                                     GID,
                                     NETWORK_ID1)\
            .AndReturn(network_process_inuse)
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 409)
