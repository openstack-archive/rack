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
KEYPAIR_ID = unicode(uuid.uuid4())
PRIVATE_KEY = (
    "-----BEGIN RSA PRIVATE KEY-----\n"
    "MIIEoAIBAAKCAQEA6W34Ak32uxp7Oh0rh1mCQclkw+NeqchAOhyO/rcphFt280D9\n"
    "YXxdUa43i51IDS9VpyFFd10Cv4ccynTPnky82CpGcuXCzaACzI/FHhmBeXTrFoXm\n"
    "682b/8kXVQfCVfSjnvChxeeATjPu9GQkNrgyYyoubHxrrW7fTaRLEz/Np9CvCq/F\n"
    "PJcsx7FwD0adFfmnulbZpplunqMGKX2nYXbDlLi7Ykjd3KbH1PRJuu+sPYDz3GmZ\n"
    "4Z0naojOUDcajuMckN8RzNblBrksH8g6NDauoX5hQa9dyd1q36403NW9tcE6ZwNp\n"
    "1GYCnN7/YgI/ugHo30ptpBvGw1zuY5/+FkU7SQIBIwKCAQA8BlW3cyIwHMCZ6j5k\n"
    "ofzsWFu9V7lBmeShOosrji8/Srgv7CPl3iaf+ZlBKHGc/YsNuBktUm5rw6hRUTyz\n"
    "rVUhpHiD8fBDgOrG4yQPDd93AM68phbO67pmWEfUCU86rJ8aPeB0t98qDVqz3zyD\n"
    "GWwK3vX+o6ao8J/SIu67zpP381d/ZigDsq+yqhtPpz04YJ2W0w67NV6XSPOV1AX0\n"
    "YLniHMwfbSTdwJ/wVWoooIgbTo7ldPuBsKUwNIVW8H9tmapVdyQxAS9JAkr1Y2si\n"
    "xKURN4Iez2oyCFv5+P1emhoptgECr49kpOBAvhRfWWkumgR1azqynzTjSnpQVO62\n"
    "vQr7AoGBAPkYWJX0tFNlqIWw4tcHtcPHJkRwvLdPUfM6Q0b6+YctKBmLoNJWBiXr\n"
    "39wiYnftSdJO+L96HAG38RrmeCfafz19EDPVXepAUYZDwnY1HGx7ZqbiPwxYMN4C\n"
    "+Wg3LzuSh7d5fe409+TCtX4YqSVFQd9gl8Ml3sKVOTxeaDROw6hFAoGBAO/mdJOr\n"
    "SGcAj9V99df6IX8abZTPm2PmirT95WWwIYX4PRY//5iaCN6XyEKIx5TJk9lmcQhS\n"
    "tb++PTsXpea01WUcxqaOO3vG7PQhvAbpq8A4eMBZZiY9UyctCPNSMscPPNRU2r/C\n"
    "tAsXRk6BNkiGofgn2MY5YBoPkEgiJmJWMKE1AoGAeP0yV3bbPnM0mLUAdxJfmZs+\n"
    "eQOO3LF/k2VxInnm6eK7tKLntp7PyUauj35qV4HiBxBqMR4Nmm9JOPOZcnFxAJvU\n"
    "q3ZDjwlMK0V7tcIGfdWJoYPVewZDnwjCSI/VHO9mfbAJ91uOWStfd8LV0EY18Cea\n"
    "K5YNHK7hSTUrTJtJFzcCgYB7YJO5qIuir9Txc/rG2Gj/ie82lqevuGSXmISaslpi\n"
    "J+Tm3xW8MfXu0bdyrL5pxsEQuFdjXbyOfxgtBNj6Tl8eDsyQK+QTxWPrRIyV10Ji\n"
    "2zbJUoxOLirDsMLGR4fUFncOHQLJBQwi9gbmi5hCjmHtVlI6DuD3dbfqlThP1I4J\n"
    "wwKBgHfbOPVCgcJA3733J+dBC8gLt5QT2fCZ2N7PtaHcsSrW/B9VlGP+tviEC59U\n"
    "bmpOLADzAto1MZdRDr8uXByZ8/eI37Txn6YchMVp43uL2+WaTdn9GBtOBpWJ0Pqi\n"
    "x3HBmILbvIEzB2BX11/PDNGRMNcCy7edvnFMCxeAiW7DJqCb\n"
    "-----END RSA PRIVATE KEY-----\n")

KEYPAIR_ID1 = unicode(uuid.uuid4())
KEYPAIR_ID2 = unicode(uuid.uuid4())


def _base_keypair_get_response(context):
    return [
        {
            "keypair_id": KEYPAIR_ID1,
            "nova_keypair_id": "fake_key1",
            "gid": GID,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": "fake_key1",
            "private_key": PRIVATE_KEY,
            "is_default": False,
            "status": "ACTIVE"
        },
        {
            "keypair_id": KEYPAIR_ID2,
            "nova_keypair_id": "fake_key2",
            "gid": GID,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": "fake_key2",
            "private_key": PRIVATE_KEY,
            "is_default": False,
            "status": "ACTIVE"
        },
    ]


def fake_group_get_by_id(context, gid):
    pass


def fake_keypair_get_all(context, gid, filters=None):
    return _base_keypair_get_response(context)


def fake_keypair_get_by_keypair_id(context, gid, keypair_id):
    keypair_list = _base_keypair_get_response(context)
    for keypair in keypair_list:
        if keypair["keypair_id"] == keypair_id:
            return keypair
    raise exception.KeypairNotFound()


def fake_create(context, kwargs):
    return {
        "keypair_id": "1234-5678",
        "nova_keypair_id": kwargs.get("nova_keypair_id"),
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": kwargs.get("display_name"),
        "is_default": kwargs.get("is_default"),
        "private_key": "private-key-1234"
    }


def fake_update(context, gid, keypair_id, kwargs):
    return {
        "keypair_id": keypair_id,
        "nova_keypair_id": "test_keypair",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test_keypair",
        "private_key": PRIVATE_KEY,
        "is_default": kwargs.get("is_default"),
        "status": "ACTIVE"
    }


def fake_delete(context, gid, keypair_id):
    return {
        "keypair_id": keypair_id,
        "nova_keypair_id": "test_keypair",
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test_keypair",
        "private_key": PRIVATE_KEY,
        "is_default": False,
        "status": "DELETING"
    }


def get_request(url, method, body=None):
    req = webob.Request.blank(url)
    req.headers['Content-Type'] = 'application/json'
    req.method = method
    if body is not None:
        req.body = jsonutils.dumps(body)
    return req


class KeypairsTest(test.NoDBTestCase):

    def setUp(self):
        super(KeypairsTest, self).setUp()
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_id)
        self.stubs.Set(db, "keypair_get_all", fake_keypair_get_all)
        self.stubs.Set(db, "keypair_create", fake_create)
        self.stubs.Set(db, "keypair_update", fake_update)
        self.stubs.Set(db, "keypair_delete", fake_delete)
        self.app = fakes.wsgi_app()

    def test_index(self):

        def _mock_data():
            return [
                {
                    "keypair_id": KEYPAIR_ID1,
                    "nova_keypair_id": "fake_key1",
                    "gid": GID,
                    "user_id": "fake",
                    "project_id": "fake",
                    "display_name": "fake_key1",
                    "private_key": PRIVATE_KEY,
                    "is_default": False,
                    "status": "ACTIVE"
                },
                {
                    "keypair_id": KEYPAIR_ID2,
                    "nova_keypair_id": "fake_key2",
                    "gid": GID,
                    "user_id": "fake",
                    "project_id": "fake",
                    "display_name": "fake_key2",
                    "private_key": PRIVATE_KEY,
                    "is_default": False,
                    "status": "ACTIVE"
                }]

        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_list")
        manager.ResourceOperator.keypair_list(
            IsA(context.RequestContext),
            IsA(list)).AndReturn(_mock_data())
        self.mox.ReplayAll()

        expect = _mock_data()
        expect[0].update(name="fake_key1")
        expect[1].update(name="fake_key2")

        url = "/v1/groups/" + GID + "/keypairs"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(200, res.status_code)
        for i in range(len(body["keypairs"])):
            for key in body["keypairs"][i]:
                self.assertEqual(expect[i][key], body["keypairs"][i][key])

    def test_index_invalid_format_gid(self):
        url = "/v1/groups/" + "aaaaa" + "/keypairs"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show(self):

        def _mock_data():
            return {
                "keypair_id": KEYPAIR_ID1,
                "nova_keypair_id": "fake_key1",
                "gid": GID,
                "user_id": "noauth",
                "project_id": "noauth",
                "display_name": "fake_key1",
                "private_key": PRIVATE_KEY,
                "is_default": False,
                "status": "ACTIVE"
            }

        self.mox.StubOutWithMock(db, "keypair_get_by_keypair_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_show")
        db.keypair_get_by_keypair_id(IsA(context.RequestContext),
                                     GID, KEYPAIR_ID1).AndReturn(_mock_data())
        manager.ResourceOperator.keypair_show(
            IsA(context.RequestContext),
            IsA(dict)).AndReturn(_mock_data())

        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expect = _mock_data()
        expect.update(name="fake_key1")

        self.assertEqual(res.status_code, 200)
        for key in body["keypair"]:
            self.assertEqual(expect[key], body["keypair"][key])

    def test_show_not_found(self):
        self.mox.StubOutWithMock(db, "keypair_get_by_keypair_id")
        db.keypair_get_by_keypair_id(
            IsA(context.RequestContext),
            GID, KEYPAIR_ID1).AndRaise(
                exception.KeypairNotFound(keypair_id=KEYPAIR_ID1))
        self.mox.ReplayAll()
        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_invalid_format_gid(self):
        url = "/v1/groups/" + "aaaaa" + "/keypairs/" + KEYPAIR_ID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create(self):
        request_body = {
            "keypair": {
                "name": "test_keypair",
                "is_default": "true",
            }
        }

        self.mox.StubOutWithMock(db, "keypair_get_all")
        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_create")
        self.mox.StubOutWithMock(uuid, 'uuid4')
        mock_id = "1234-5678"
        uuid.uuid4().AndReturn(mock_id)
        uuid.uuid4().AndReturn(mock_id)
        db.keypair_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict)).AndReturn([])
        manager.ResourceOperator.keypair_create(
            IsA(context.RequestContext), IsA(unicode)).AndReturn(
                {"nova_keypair_id": "keypair-" + mock_id,
                 "private_key": "private-key-1234"})
        self.mox.ReplayAll()

        expect = {
            "keypair": {
                "keypair_id": mock_id,
                "nova_keypair_id": "keypair-" + mock_id,
                "user_id": "noauth",
                "project_id": "noauth",
                "gid": GID,
                "name": "test_keypair",
                "private_key": "private-key-1234",
                "is_default": True}
        }

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["keypair"]:
            self.assertEqual(expect["keypair"][key], body["keypair"][key])
        self.assertEqual(res.status_code, 201)

    def test_create_without_name(self):
        request_body = {
            "keypair": {
            }
        }

        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_create")
        self.mox.StubOutWithMock(uuid, 'uuid4')
        mock_id = "1234-5678"
        uuid.uuid4().AndReturn(mock_id)
        uuid.uuid4().AndReturn(mock_id)
        manager.ResourceOperator.keypair_create(
            IsA(context.RequestContext), IsA(unicode)).AndReturn(
                {"nova_keypair_id": "keypair-" + mock_id,
                 "private_key": "private-key-1234"})
        self.mox.ReplayAll()

        expect = {
            "keypair": {
                "keypair_id": mock_id,
                "nova_keypair_id": "keypair-" + mock_id,
                "user_id": "noauth",
                "project_id": "noauth",
                "gid": GID,
                "name": "keypair-" + mock_id,
                "private_key": "private-key-1234",
                "is_default": False}
        }

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["keypair"]:
            self.assertEqual(expect["keypair"][key], body["keypair"][key])
        self.assertEqual(res.status_code, 201)

    def test_create_default_keypair_already_exists(self):
        request_body = {
            "keypair": {
                "is_default": "true"
            }
        }

        self.mox.StubOutWithMock(db, "keypair_get_all")
        db.keypair_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_raise_exception_by_db_keypair_create(self):
        self.mox.StubOutWithMock(db, "group_get_by_gid")
        db.group_get_by_gid(IsA(context.RequestContext), GID)\
            .AndRaise(exception.GroupNotFound(gid=GID))
        self.mox.ReplayAll()

        request_body = {
            "keypair": {
                "name": "test_key",
            }
        }
        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_invalid_format_gid(self):
        request_body = {
            "keypair": {
                "name": "test_keypair",
            }
        }

        url = '/v1/groups/' + 'aaaaaaa' + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_without_is_default(self):
        request_body = {
            "keypair": {
                "name": "test_keypair"
            }
        }

        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_create")
        self.mox.StubOutWithMock(uuid, 'uuid4')
        mock_id = "1234-5678"
        uuid.uuid4().AndReturn(mock_id)
        uuid.uuid4().AndReturn(mock_id)
        manager.ResourceOperator.keypair_create(
            IsA(context.RequestContext), IsA(unicode)).AndReturn(
                {"nova_keypair_id": "keypair-" + mock_id,
                 "private_key": "private-key-1234"})
        self.mox.ReplayAll()

        expect = {
            "keypair": {
                "keypair_id": mock_id,
                "nova_keypair_id": "keypair-" + mock_id,
                "user_id": "noauth",
                "project_id": "noauth",
                "gid": GID,
                "name": "test_keypair",
                "private_key": "private-key-1234",
                "is_default": False}
        }

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["keypair"]:
            self.assertEqual(expect["keypair"][key], body["keypair"][key])
        self.assertEqual(res.status_code, 201)

    def test_create_empty_request_body(self):
        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_create")
        self.mox.StubOutWithMock(uuid, 'uuid4')
        mock_id = "1234-5678"
        uuid.uuid4().AndReturn(mock_id)
        uuid.uuid4().AndReturn(mock_id)
        manager.ResourceOperator.keypair_create(
            IsA(context.RequestContext), IsA(unicode)).AndReturn(
                {"nova_keypair_id": "keypair-" + mock_id,
                 "private_key": "private-key-1234"})
        self.mox.ReplayAll()

        expect = {
            "keypair": {
                "keypair_id": mock_id,
                "nova_keypair_id": "keypair-" + mock_id,
                "user_id": "noauth",
                "project_id": "noauth",
                "gid": GID,
                "name": "keypair-" + mock_id,
                "private_key": "private-key-1234",
                "is_default": False}
        }

        url = '/v1/groups/' + GID + '/keypairs'
        request_body = {"keypair": {}}
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for key in body["keypair"]:
            self.assertEqual(expect["keypair"][key], body["keypair"][key])
        self.assertEqual(res.status_code, 201)

    def test_create_no_body(self):
        request_body = {}

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_body(self):
        request_body = []

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_is_default(self):
        request_body = {
            "keypair": {
                "name": "test_keypair",
                "is_default": "aaa"
            }
        }

        url = '/v1/groups/' + GID + '/keypairs'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update(self):
        request_body = {
            "keypair": {
                "is_default": "true"
            }
        }
        expected = {
            "keypair": {
                "keypair_id": KEYPAIR_ID,
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "nova_keypair_id": "test_keypair",
                "name": "test_keypair",
                "private_key": PRIVATE_KEY,
                "is_default": True,
                "status": "ACTIVE"
            }
        }

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in request_body["keypair"]:
            self.assertEqual(body["keypair"][key], expected["keypair"][key])

    def test_update_invalid_format_gid(self):
        request_body = {
            "keypair": {
                "is_default": "true",
            }
        }

        url = "/v1/groups/" + "aaaaaaa" + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update_invalid_format_keypair_id(self):
        request_body = {
            "keypair": {
                "is_default": "true",
            }
        }

        url = "/v1/groups/" + GID + "/keypairs/" + "aaaaa"
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update_invalid_format_is_default(self):
        request_body = {
            "keypair": {
                "is_default": "aaa",
            }
        }

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_without_is_default(self):
        request_body = {
            "keypair": {
                "name": "aaa",
            }
        }

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_empty_body(self):
        request_body = {"keypair": {}}
        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_no_body(self):
        request_body = {}
        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_invalid_body(self):
        request_body = []
        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "PUT", request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_delete(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "keypair_get_by_keypair_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_delete")

        db.process_get_all(IsA(context.RequestContext), GID,
                           filters={"keypair_id": KEYPAIR_ID}).AndReturn([])

        db.keypair_get_by_keypair_id(
            IsA(context.RequestContext),
            GID, KEYPAIR_ID).AndReturn(
                {"nova_keypair_id": KEYPAIR_ID})
        manager.ResourceOperator.keypair_delete(
            IsA(context.RequestContext), KEYPAIR_ID)
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_invalid_format_gid(self):
        url = "/v1/groups/" + "aaaaaaa" + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_invalid_format_keypair_id(self):
        url = "/v1/groups/" + GID + "/keypairs/" + "aaaaa"
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_keypair_not_found(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "keypair_get_by_keypair_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "keypair_delete")

        db.process_get_all(IsA(context.RequestContext), GID,
                           filters={"keypair_id": KEYPAIR_ID}).AndReturn([])

        db.keypair_get_by_keypair_id(
            IsA(context.RequestContext),
            GID, KEYPAIR_ID).AndReturn(
                {"nova_keypair_id": KEYPAIR_ID})
        manager.ResourceOperator.keypair_delete(
            IsA(context.RequestContext), KEYPAIR_ID).AndRaise(
                exception.NotFound())
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_raise_exception_keypair_inuse(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(IsA(context.RequestContext), GID,
                           filters={"keypair_id": KEYPAIR_ID}).AndReturn([{}])
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/keypairs/" + KEYPAIR_ID
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)
