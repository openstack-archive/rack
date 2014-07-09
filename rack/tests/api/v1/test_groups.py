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

from rack.api.v1 import groups
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack import test
from rack.tests.api import fakes

import copy
import uuid
import webob

GID = str(uuid.uuid4())

FAKE_GROUPS = {
    "groups": [
        {
            "gid": "gid1",
            "user_id": "user_id1",
            "project_id": "fake",
            "display_name": "fake",
            "display_description": "fake",
            "status": "ACTIVE"
        },
        {
            "gid": "gid2",
            "user_id": "user_id1",
            "project_id": "fake",
            "display_name": "fake",
            "display_description": "fake",
            "status": "ACTIVE"
        },
        {
            "gid": "gid3",
            "user_id": "user_id2",
            "project_id": "fake",
            "display_name": "fake",
            "display_description": "fake",
            "status": "ACTIVE"
        }
    ]
}


def fake_create(context, kwargs):
    return {"gid": GID,
            "user_id": context.user_id,
            "project_id": context.project_id,
            "display_name": kwargs["display_name"],
            "display_description": kwargs["display_description"],
            "status": "ACTIVE"}


def fake_update(context, kwargs):
    return {
        "gid": GID,
        "user_id": context.user_id,
        "project_id": context.project_id,
        "display_name": "test",
        "display_description": "test",
        "status": "ACTIVE"
    }

def fake_delete(context, kwargs):
    return {
    }

def fake_not_group_data_exists(context, kwargs):
    return {"dummy-key" : "dummy-data"}

def fake_not_group_data_not_exists(context, kwargs):
    return {}

def fake_raise_exception(context, kwargs):
    raise Exception()

def raise_group_not_found(context, kwargs):
    raise exception.GroupNotFound(gid=GID)

def fake_group_get_all(context, filters):
    if not filters:
        return copy.deepcopy(FAKE_GROUPS["groups"])
    else:
        return [
            {"gid": "fake",
             "user_id": "fake",
             "project_id": filters["project_id"],
             "display_name": filters["display_name"],
             "display_description": "fake",
             "status": filters["status"]}
        ]


def fake_group_get_by_gid(context, gid):
    return {
        "gid": gid,
        "user_id": "a4362182a2ac425c9b0b0826ad187d31",
        "project_id": "a43621849823764c9b0b0826ad187d31t",
        "display_name": "my_group",
        "display_description": "This is my group.",
        "status": "ACTIVE"
    }


def get_request(url, method, body=None):
    req = webob.Request.blank(url)
    req.headers['Content-Type'] = 'application/json'
    req.method = method
    if body is not None:
        req.body = jsonutils.dumps(body)
    return req


class GroupsTest(test.NoDBTestCase):

    def setUp(self):
        super(GroupsTest, self).setUp()
        self.stubs.Set(db, "group_create", fake_create)
        self.stubs.Set(db, "group_get_all", fake_group_get_all)
        self.stubs.Set(db, "group_get_by_gid", fake_group_get_by_gid)
        self.stubs.Set(db, "group_update", fake_update)
        self.stubs.Set(db, "group_delete", fake_delete)
        self.controller = groups.Controller()
        self.app = fakes.wsgi_app()

    def test_index(self):
        url = '/v1/groups'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected = copy.deepcopy(FAKE_GROUPS)
        for group in expected["groups"]:
            group["name"] = group.pop("display_name")
            group["description"] = group.pop("display_description")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expected)

    def test_index_filters(self):
        url = '/v1/groups?project_id=PID&name=NAME&status=STATUS'

        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        expected = {"groups": [
            {"gid": "fake",
             "user_id": "fake",
             "project_id": "PID",
             "name": "NAME",
             "description": "fake",
             "status": "STATUS"}
        ]}
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expected)

    def test_show(self):
        url = '/v1/groups/00000000-0000-0000-0000-000000000010'
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        expected = {"group": {
                    "gid": "00000000-0000-0000-0000-000000000010",
                    "user_id": "a4362182a2ac425c9b0b0826ad187d31",
                    "project_id": "a43621849823764c9b0b0826ad187d31t",
                    "name": "my_group",
                    "description": "This is my group.",
                    "status": "ACTIVE"
                    }}

        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expected)

    def test_show_not_found_exception(self):
        self.stubs.Set(db, "group_get_by_gid",
                       raise_group_not_found)
        url = '/v1/groups/' + GID
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
        self.assertRaises(
            webob.exc.HTTPNotFound, self.controller.show, req, GID)

    def test_show_gid_is_not_uuid_format(self):
        gid = "abcdefgid"
        url = '/v1/groups/' + gid
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
        self.assertRaises(
            webob.exc.HTTPNotFound, self.controller.show, req, gid)

    def test_create(self):
        name = "test_group"
        description = "This is test group."
        request_body = {
            "group": {
                "name": name,
                "description": description,
            }
        }
        expected = {
            "group": {
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": name,
                "description": description,
                "status": "ACTIVE"
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in expected["group"]:
            self.assertEqual(body["group"][key], expected["group"][key])

    def test_create_group_name_is_whitespace(self):
        request_body = {
            "group": {
                "name": " ",
                "description": "This is test group",
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_group_name_with_leading_trailing_whitespace(self):
        request_body = {
            "group": {
                "name": " test_group ",
                "description": "This is test group"
            }
        }
        expected = {
            "group": {
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test_group",
                "description": "This is test group",
                "status": "ACTIVE"
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in expected["group"]:
            self.assertEqual(body["group"][key], expected["group"][key])

    def test_create_without_group_name(self):
        request_body = {
            "group": {
                "description": "This is test group",
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_without_group_description(self):
        request_body = {
            "group": {
                "name": "test_group",
            }
        }
        expected = {
            "group": {
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test_group",
                "status": "ACTIVE"
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in expected["group"]:
            self.assertEqual(body["group"][key], expected["group"][key])

    def test_create_empty_body(self):
        request_body = {"group": {}}

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_no_body(self):
        request_body = {}

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_body(self):
        request_body = []

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_check_group_name_length(self):
        MAX_LENGTH = 255
        request_body = {
            "group": {
                "name": "a" * (MAX_LENGTH + 1),
                "description": "This is test group"
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_group_description_length_zero(self):
        request_body = {
            "group": {
                "name": "test_group",
                "description": ""
            }
        }
        expected = {
            "group": {
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test_group",
                "description": "",
                "status": "ACTIVE"
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 201)
        for key in expected["group"]:
            self.assertEqual(body["group"][key], expected["group"][key])

    def test_create_check_group_description_length(self):
        MAX_LENGTH = 255
        request_body = {
            "group": {
                "name": "test_group",
                "description": "a" * (MAX_LENGTH + 1)
            }
        }

        url = '/v1/groups'
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update(self):
        request_body = {
            "group": {
                "name": "My_Group_updated",
                "description": "This is my group updated.",
            }
        }
        expected = {
            "group": {
                "gid": GID,
                "user_id": "fake",
                "project_id": "fake",
                "name": "test",
                "description": "test",
                "status": "ACTIVE"
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in request_body["group"]:
            self.assertEqual(body["group"][key], expected["group"][key])

    def test_update_allow_group_name_none(self):
        request_body = {
            "group": {
                "description": "This is test group"
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 200)

    def test_update_allow_group_description_none(self):
        request_body = {
            "group": {
                "name": "my_group",
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 200)

    def test_update_allow_group_description_blank(self):
        request_body = {
            "group": {
                "name": "my_group",
                "description": "",
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 200)

    def test_update_invalid_gid(self):
        request_body = {
            "group": {
                "description": "This is test group"
            }
        }

        url = '/v1/groups/' + GID + "err"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update_empty_body(self):
        request_body = {"group": {}}

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_no_body(self):
        request_body = {}

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_invalid_format_body(self):
        request_body = []

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_group_name_blank(self):
        request_body = {
            "group": {
                "name": "",
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_check_group_name_length(self):
        MAX_LENGTH = 255
        request_body = {
            "group": {
                "name": "a" * (MAX_LENGTH + 1),
                "description": "This is test group"
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_check_group_description_length(self):
        MAX_LENGTH = 255
        request_body = {
            "group": {
                "name": "my_group",
                "description": "a" * (MAX_LENGTH + 1)
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_group_not_found_on_db(self):
        self.stubs.Set(db, "group_update", raise_group_not_found)
        request_body = {
            "group": {
                "description": "This is test group"
            }
        }

        url = '/v1/groups/' + GID
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
        self.assertRaises(
            webob.exc.HTTPNotFound, self.controller.update, req, request_body, GID)

    def test_delete_invalid_format_gid(self):
        url = '/v1/groups/' + GID + "err"
        req = get_request(url, 'DELETE')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
        body = jsonutils.loads(res.body)
        print(body)

    def test_delete(self):
        url = '/v1/groups/'+GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "securitygroup_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "network_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "process_get_all", fake_not_group_data_not_exists)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_group_inuse_keypair(self):
        url = '/v1/groups/' + GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_not_group_data_exists)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)
    
    def test_delete_group_inuse_securitygroup(self):
        url = '/v1/groups/' + GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "securitygroup_get_all", fake_not_group_data_exists)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)

    def test_delete_group_inuse_network(self):
        url = '/v1/groups/' + GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "securitygroup_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "network_get_all", fake_not_group_data_exists)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)

    def test_delete_group_inuse_process(self):
        url = '/v1/groups/' + GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "securitygroup_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "network_get_all", fake_not_group_data_not_exists)
        self.stubs.Set(db, "process_get_all", fake_not_group_data_exists)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 409)
        
    def test_delete_exception(self):
        url = '/v1/groups/' + GID
        req = get_request(url, 'DELETE')
        self.stubs.Set(db, "keypair_get_all", fake_raise_exception)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)
