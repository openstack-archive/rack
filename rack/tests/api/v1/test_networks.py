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


def fake_network_get_all(context, gid):
    return _return_base_network_list(context, gid)


def fake_network_get_all_empty_list(contextm, gid):
    return []


def fake_raise_exception():
    raise Exception()


def _return_base_network_list(context, gid):
    return [
        {"network_id": NETWORK_ID1,
         "neutron_network_id": "net-" + NETWORK_ID1,
         "gid": gid,
         "user_id": context.user_id,
         "project_id": context.project_id,
         "display_name": "net-45212048-abc3-43cc-89b3-377341426ac",
         "is_admin": "True",
         "cidr": "10.0.0.0/24",
         "ext_router": "11212048-abc3-43cc-89b3-377341426aca",
         "status": "Exist"},
        {"network_id": NETWORK_ID2,
         "neutron_network_id": None,
         "gid": gid,
         "user_id": context.user_id,
         "project_id": context.project_id,
         "display_name": "net-13092048-abc3-43cc-89b3-377341426ac",
         "is_admin": "True",
         "cidr": "10.0.1.0/24",
         "ext_router": "21212048-abc3-43cc-89b3-377341426aca",
         "status": "Exist"}
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
        self.user_id = 'fake'
        self.project_id = 'fake'
        self.context = FakeContext(self.user_id, self.project_id)
        self.app = fakes.wsgi_app()

    def test_index(self):
        self.stubs.Set(db, "network_get_all", fake_network_get_all)
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_list")
        manager.ResourceOperator.network_list(
            IsA(context.RequestContext),
            IsA(list)).AndReturn(_return_base_network_list(self.context, GID))
        self.mox.ReplayAll()

        expect = _return_base_network_list(self.context, GID)
        expect[0].update(ext_router_id="11212048-abc3-43cc-89b3-377341426aca")
        expect[1].update(ext_router_id="21212048-abc3-43cc-89b3-377341426aca")
        expect[0].update(name="net-45212048-abc3-43cc-89b3-377341426ac")
        expect[1].update(name="net-13092048-abc3-43cc-89b3-377341426ac")
        expect[0].update(cidr="10.0.0.0/24")
        expect[1].update(cidr="10.0.1.0/24")

        url = "/v1/groups/" + GID + "/networks"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(200, res.status_code)
        for i in range(len(body["networks"])):
            for key in body["networks"][i]:
                self.assertEqual(expect[i][key], body["networks"][i][key])

    def test_index_return_empty_list(self):
        self.stubs.Set(db, "network_get_all", fake_network_get_all_empty_list)
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_list")
        manager.ResourceOperator.network_list(
            IsA(context.RequestContext), []).AndReturn([])
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected_body = {"networks": []}

        self.assertEqual(expected_body, body)
        self.assertEqual(res.status_code, 200)

    def test_index_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show(self):

        def _mock_data():
            return {
                "network_id": NETWORK_ID1,
                "neutron_network_id": None,
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "display_name": "net-45212048-abc3-43cc-89b3-377341426ac",
                "is_admin": "True",
                "cidr": "10.0.0.0/24",
                "ext_router": "11212048-abc3-43cc-89b3-377341426aca",
                "status": "Exist"}

        mock_data = _mock_data()
        self.mox.StubOutWithMock(db, "network_get_by_network_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_show")
        db.network_get_by_network_id(IsA(context.RequestContext),
                                     GID, NETWORK_ID1).AndReturn(_mock_data())
        manager.ResourceOperator.network_show(IsA(context.RequestContext),
                                              IsA(dict))

        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url + "/" + NETWORK_ID1, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        expect = mock_data
        expect.update(ext_router_id="11212048-abc3-43cc-89b3-377341426aca")
        expect.update(name="net-45212048-abc3-43cc-89b3-377341426ac")
        expect.update(cidr="10.0.0.0/24")

        self.assertEqual(res.status_code, 200)
        for key in body["network"]:
            self.assertEqual(expect[key], body["network"][key])

    def test_show_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks/' + NETWORK_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_validate_exception_by_network_id_format(self):
        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1 + "aaa"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_exception_networknotfound(self):
        self.mox.StubOutWithMock(db, "network_get_by_network_id")
        db.network_get_by_network_id(IsA(context.RequestContext), GID,
                                     NETWORK_ID1)\
            .AndRaise(exception.NetworkNotFound(network_id=NETWORK_ID1))
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url + "/" + NETWORK_ID1, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        self.stubs.Set(db, "network_create", fake_create_db)
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_create")
        manager.ResourceOperator.network_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            cidr=IsA(unicode),
            gateway=IsA(unicode),
            dns_nameservers=IsA(list),
            ext_router=IsA(unicode)).AndReturn(
                {"neutron_network_id": "neutron-id-data"})
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

        expect = {
            "network": {
                "network_id": NETWORK_ID1,
                "neutron_network_id": "neutron-id-data",
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "name": "network-test",
                "is_admin": True,
                "cidr": "10.0.0.0/24",
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["network"]:
            self.assertEqual(
                expect["network"][key], body["network"][key])
        self.assertEqual(res.status_code, 201)

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
        self.mox.StubOutWithMock(db, "group_get_by_gid")
        db.group_get_by_gid(IsA(context.RequestContext),
                            GID).AndRaise(exception.GroupNotFound(gid=GID))
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

    def test_create_by_name_blank(self):
        self.stubs.Set(db, "network_create", fake_create_db)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        self.mox.StubOutWithMock(uuid, "uuid4")
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_create")

        mock_uuid = NETWORK_ID1
        uuid.uuid4().AndReturn(mock_uuid)
        uuid.uuid4().AndReturn(mock_uuid)

        network_value = {
            "name": "network-" + mock_uuid,
            "cidr": "10.0.0.0/24",
            "gateway": "10.0.0.254",
            "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
            "ext_router": "91212048-abc3-43cc-89b3-377341426aca"}
        manager.ResourceOperator.network_create(
            IsA(context.RequestContext), **network_value).AndReturn(
                {"neutron_network_id": "neutron-id-data"})
        self.mox.ReplayAll()

        request_body = {
            "network": {
                "name": None,
                "is_admin": "True",
                "cidr": "10.0.0.0/24",
                "gateway": "10.0.0.254",
                "dns_nameservers": ["8.8.8.8", "8.8.4.4"],
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        expect = {
            "network": {
                "network_id": mock_uuid,
                "neutron_network_id": "neutron-id-data",
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "name": "network-" + mock_uuid,
                "is_admin": True,
                "cidr": "10.0.0.0/24",
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["network"]:
            self.assertEqual(
                expect["network"][key], body["network"][key])
        self.assertEqual(res.status_code, 201)

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

    def test_create_validate_exception_by_dns_nameservers_is_not_list(self):
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)

        request_body = {
            "network": {
                "name": "test_network",
                "cidr": "10.0.0.0/24",
                "is_admin": False,
                "gateway": "10.0.0.254",
                "dns_nameservers": "8.8.8.8, 8.8.4.4",
                "ext_router_id": "91212048-abc3-43cc-89b3-377341426aca"
            }
        }

        url = '/v1/groups/' + GID + '/networks'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_delete(self):
        self.stubs.Set(db,
                       "network_get_by_network_id",
                       fake_network_get_by_network_id)
        self.stubs.Set(db,
                       "network_delete", fake_network_delete)
        self.mox.StubOutWithMock(manager.ResourceOperator, "network_delete")
        manager.ResourceOperator.network_delete(
            IsA(context.RequestContext), IsA(unicode), IsA(str))
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/networks/" + NETWORK_ID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_validate_exception_by_gid_format(self):
        not_uuid_gid = "aaaaa"
        url = '/v1/groups/' + not_uuid_gid + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exception_not_found(self):
        self.mox.StubOutWithMock(db, "network_get_by_network_id")
        db.network_get_by_network_id(
            IsA(context.RequestContext), GID, NETWORK_ID1)\
            .AndRaise(exception.NetworkNotFound(network_id=NETWORK_ID1))
        self.mox.ReplayAll()
        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exception_inuse(self):
        self.mox.StubOutWithMock(db, "network_get_by_network_id")
        network_process_inuse = {"processes": [{"pid": "pid"}]}
        db.network_get_by_network_id(IsA(context.RequestContext),
                                     GID,
                                     NETWORK_ID1)\
            .AndReturn(network_process_inuse)
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/networks/' + NETWORK_ID1
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)

        self.assertEqual(res.status_code, 409)
