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

from oslo.config import cfg

from rack.api.v1.views.processes import ViewBuilder
from rack import context
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack.openstack.common import log as logging
from rack.resourceoperator import manager
from rack import test
from rack.tests.api import fakes

import json
import uuid
import webob

LOG = logging.getLogger(__name__)


GID = unicode(uuid.uuid4())

PPID1 = unicode(uuid.uuid4())
PPID2 = unicode(uuid.uuid4())

PID1 = unicode(uuid.uuid4())
PID2 = unicode(uuid.uuid4())

PIDX = unicode(uuid.uuid4())

KEYPAIR_ID1 = unicode(uuid.uuid4())
KEYPAIR_ID2 = unicode(uuid.uuid4())

NOVA_KEYPAIR_ID1 = unicode(uuid.uuid4())

SECURITYGROUP_ID1 = unicode(uuid.uuid4())
SECURITYGROUP_ID2 = unicode(uuid.uuid4())
SECURITYGROUP_ID3 = unicode(uuid.uuid4())

NEUTRON_SECURITYGROUP_ID1 = unicode(uuid.uuid4())
NEUTRON_SECURITYGROUP_ID2 = unicode(uuid.uuid4())
NEUTRON_SECURITYGROUP_ID3 = unicode(uuid.uuid4())

NETWORK_ID1 = unicode(uuid.uuid4())
NETWORK_ID2 = unicode(uuid.uuid4())

NEUTRON_NETWORK_ID1 = unicode(uuid.uuid4())
NEUTRON_NETWORK_ID2 = unicode(uuid.uuid4())

GLANCE_IMAGE_ID1 = unicode(uuid.uuid4())
GLANCE_IMAGE_ID2 = unicode(uuid.uuid4())

METADATA1 = {"type1": "test1", "type2": "test2"}

USER_DATA_B64_ENC = "IyEvYmluL3NoCmVjaG8gXCd0ZXN0Llwn"
USER_DATA_B64_DEC = "#!/bin/sh\necho \\'test.\\'"

NOVA_INSTANCE_ID1 = unicode(uuid.uuid4())
NOVA_INSTANCE_ID2 = unicode(uuid.uuid4())
NOVA_INSTANCE_ID3 = unicode(uuid.uuid4())


def _base(context):
    return {
        "user_id": context.user_id,
        "project_id": context.project_id
    }


def _base_keypair(keypair_id, nova_keypair_id):
    return {
        "keypair_id": keypair_id,
        "nova_keypair_id": nova_keypair_id
    }


def _base_securitygroup(securitygroup_id, neutron_securitygroup_id):
    return {
        "securitygroup_id": securitygroup_id,
        "neutron_securitygroup_id": neutron_securitygroup_id
    }


def _base_securitygroups1():
    return [
        _base_securitygroup(SECURITYGROUP_ID1, NEUTRON_SECURITYGROUP_ID1),
        _base_securitygroup(SECURITYGROUP_ID2, NEUTRON_SECURITYGROUP_ID2),
    ]


def _base_securitygroups2():
    return [
        _base_securitygroup(SECURITYGROUP_ID3, NEUTRON_SECURITYGROUP_ID3),
    ]


def _base_network(network_id, neutron_network_id):
    return {
        "network_id": network_id,
        "neutron_network_id": neutron_network_id
    }


def _base_networks():
    return [
        _base_network(NETWORK_ID1, NEUTRON_NETWORK_ID1),
        _base_network(NETWORK_ID2, NEUTRON_NETWORK_ID2),
    ]


def _base_process1(gid, pid):
    return {
        "pid": pid,
        "ppid": PPID1,
        "nova_instance_id": NOVA_INSTANCE_ID1,
        "gid": gid,
        "project_id": "noauth",
        "user_id": "noauth",
        "display_name": "test1",
        "nova_flavor_id": 1,
        "glance_image_id": GLANCE_IMAGE_ID1,
        "keypair_id": KEYPAIR_ID1,
        "securitygroups": _base_securitygroups1(),
        "networks": _base_networks(),
        "is_proxy": False,
        "status": "BUILDING",
        "app_status": None,
        "userdata": USER_DATA_B64_ENC,
        "shm_endpoint": "shm_endpoint_data",
        "ipc_endpoint": "ipc_endpoint_data",
        "fs_endpoint": "fs_endpoint_data",
        "args": '{"gid": "' + gid + '","pid": "' + pid + '"}'}


def _base_process2(gid, pid):
    return {
        "pid": pid,
        "ppid": PPID2,
        "nova_instance_id": NOVA_INSTANCE_ID2,
        "gid": gid,
        "project_id": "noauth",
        "user_id": "noauth",
        "display_name": "test2",
        "nova_flavor_id": 2,
        "glance_image_id": GLANCE_IMAGE_ID2,
        "keypair_id": KEYPAIR_ID2,
        "securitygroups": _base_securitygroups2(),
        "networks": _base_networks(),
        "is_proxy": False,
        "status": "BUILDING",
        "app_status": "BUILDING",
        "userdata": USER_DATA_B64_ENC,
        "shm_endpoint": "shm_endpoint_data",
        "ipc_endpoint": "ipc_endpoin_datat",
        "fs_endpoint": "fs_endpoint_data",
        "args": '{"key": "value"}'}


def _base_process3(gid, pid):
    return {
        "pid": pid,
        "ppid": PPID1,
        "nova_instance_id": NOVA_INSTANCE_ID3,
        "gid": gid,
        "project_id": "noauth",
        "user_id": "noauth",
        "display_name": "test1",
        "nova_flavor_id": 1,
        "glance_image_id": GLANCE_IMAGE_ID1,
        "keypair_id": KEYPAIR_ID1,
        "securitygroups": _base_securitygroups1(),
        "networks": _base_networks(),
        "is_proxy": True,
        "status": "BUILDING",
        "app_status": "BUILDING",
        "userdata": USER_DATA_B64_ENC,
        "shm_endpoint": "shm_endpoint_data",
        "ipc_endpoint": "ipc_endpoint_data",
        "fs_endpoint": "fs_endpoint_data",
        "args": '{"key": "value"}'}


def _base_processes(gid):
    return [
        _base_process1(gid, PPID1),
        _base_process2(gid, PPID2),
        _base_process1(gid, PID1),
        _base_process2(gid, PID2),
    ]


def fake_keypair_get_by_keypair_id(context, gid, keypair_id):
    return _base_keypair(keypair_id, NOVA_KEYPAIR_ID1)


def fake_keypair_get_by_keypair_id_raise_not_found(context, gid, keypair_id):
    raise exception.KeypairNotFound(keypair_id=keypair_id)


def fake_network_get_all(context, gid, filters=None):
    return _base_networks()


def fake_network_get_all_not_found(context, gid, filters=None):
    return []


def fake_process_get_all(context, gid, filters=None):
    processes = _base_processes(gid)
    for process in processes:
        process.update(_base(context))
    return processes


def fake_process_get_all_for_proxy(context, gid, filters=None):
    process = _base_process3(gid, PID1)
    return [process]


def fake_process_get_by_pid(context, gid, pid):
    processes = _base_processes(gid)
    for process in processes:
        if process["pid"] == pid:
            process.update(_base(context))
            return process
    raise exception.ProcessNotFound(pid=pid)


def fake_pid1():
    return PID1


def fake_create(context, kwargs, network_ids, securitygroup_ids):
    process = _base(context)
    process.update(kwargs)
    process["networks"] = fake_network_get_all(context, GID)
    process["securitygroups"] = _base_securitygroups1()
    return process


def fake_delete(context, gid, pid):
    process = _base(context)
    process.update(gid=gid)
    process.update(pid=pid)
    process.update(nova_instance_id=NOVA_INSTANCE_ID1)
    return process


def get_request(url, method, body=None):
    req = webob.Request.blank(url)
    req.headers['Content-Type'] = 'application/json'
    req.method = method
    if body is not None:
        req.body = jsonutils.dumps(body)
    return req


def get_base_url(gid):
    return "/v1/groups/" + gid + "/processes"


def get_base_body(process):
    return {
        "project_id": process["project_id"],
        "user_id": process["user_id"],
        "ppid": process["ppid"],
        "name": process["display_name"],
        "nova_instance_id": process["nova_instance_id"],
        "nova_flavor_id": process["nova_flavor_id"],
        "glance_image_id": process["glance_image_id"],
        "keypair_id": process["keypair_id"],
        "securitygroup_ids": [securitygroup["securitygroup_id"]
                              for securitygroup in process["securitygroups"]],
        "metadata": METADATA1,
        "userdata": process["userdata"]
    }


def get_base_request_body1(process):
    return {"process": get_base_body(process)}


def get_proxy_request_body1(process):
    body = get_base_body(process)
    body.update(ipc_endpoint="ipc_endpoint_data")
    body.update(shm_endpoint="shm_endpoint_data")
    body.update(fs_endpoint="fs_endpoint_data")
    return {"proxy": body}


def get_base_process_body(process):
    process_body = get_base_body(process)
    process_body.update(gid=GID)
    process_body.update(pid=process["pid"])
    process_body.update(status=process["status"])
    process_body.update(networks=[
        {"fixed": None,
         "floating": None,
         "network_id": NETWORK_ID1},
        {"fixed": None,
         "floating": None,
         "network_id": NETWORK_ID2}])
    process_body.update(app_status=process["app_status"])
    process_body.update(userdata=process["userdata"])
    process_body.update(args=json.loads(process["args"]))
    process_body.pop("metadata")
    return process_body


def get_base_prxoy_body(process):
    process_body = get_base_body(process)
    process_body.update(gid=GID)
    process_body.update(pid=process["pid"])
    process_body.update(status=process["status"])
    process_body.update(networks=[
        {"fixed": None,
         "floating": None,
         "network_id": NETWORK_ID1},
        {"fixed": None,
         "floating": None,
         "network_id": NETWORK_ID2}])
    process_body.update(app_status=process["app_status"])
    process_body.update(userdata=process["userdata"])
    process_body.update(args=json.loads(process["args"]))
    process_body.update(ipc_endpoint=process["ipc_endpoint"])
    process_body.update(shm_endpoint=process["shm_endpoint"])
    process_body.update(fs_endpoint=process["fs_endpoint"])
    process_body.pop("metadata")
    return process_body


def get_base_process_response_body(process):
    process_body = get_base_process_body(process)
    return {"process": process_body}


def get_base_processes_response_body(processes):
    processes_body = []
    for process in processes:
        process_body = get_base_process_body(process)
        processes_body.append(process_body)
    return {"processes": processes_body}


def get_proxy_response_body(process):
    process_body = get_base_prxoy_body(process)
    return {"proxy": process_body}


class ProcessesTest(test.NoDBTestCase):

    def _set_mox_db_process_update_on_error(self):
        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(IsA(context.RequestContext), IsA(
            unicode), IsA(unicode), {"status": "ERROR"})

    def setUp(self):
        super(ProcessesTest, self).setUp()
        self.stubs.Set(uuid, "uuid4", fake_pid1)
        self.stubs.Set(
            db, "keypair_get_by_keypair_id", fake_keypair_get_by_keypair_id)
        self.stubs.Set(db, "network_get_all", fake_network_get_all)
        self.stubs.Set(db, "process_get_all", fake_process_get_all)
        self.stubs.Set(db, "process_get_by_pid", fake_process_get_by_pid)
        self.stubs.Set(db, "process_create", fake_create)
        self.stubs.Set(db, "process_delete", fake_delete)
        self.app = fakes.wsgi_app()
        self.view = ViewBuilder()

    def test_index(self):
        processes = _base_processes(GID)
        expect = get_base_processes_response_body(processes)
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_list")
        manager.ResourceOperator.process_list(IsA(context.RequestContext),
                                              IsA(list)).AndReturn(processes)
        self.mox.ReplayAll()

        url = get_base_url(GID)
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        for i in range(len(body["processes"])):
            for key in body["processes"][i]:
                self.assertEqual(
                    expect["processes"][i][key], body["processes"][i][key])
        self.assertEqual(200, res.status_code)

    def test_index_invalid_format_gid(self):
        url = get_base_url("aaaaa")
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show(self):
        process = _base_process1(GID, PID1)
        expect = get_base_process_response_body(process)
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_show")
        manager.ResourceOperator.process_show(IsA(context.RequestContext),
                                              IsA(dict))
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expect)

    def test_show_invalid_format_gid(self):
        url = get_base_url("aaaaa") + "/" + PID1
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_invalid_format_pid(self):
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_process_not_found(self):
        self.stubs.Set(db, "keypair_get_by_keypair_id",
                       fake_keypair_get_by_keypair_id_raise_not_found)
        url = get_base_url(GID) + "/" + PIDX
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_proxy(self):
        process = _base_process3(GID, PID1)
        expect = get_proxy_response_body(process)
        self.stubs.Set(db, "process_get_all", fake_process_get_all_for_proxy)
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_show")
        manager.ResourceOperator.process_show(IsA(context.RequestContext),
                                              IsA(dict))
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expect)

    def test_show_proxy_not_found_exception(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndRaise(exception.NotFound())
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_show_proxy_bad_request(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict)).AndReturn([])
        self.mox.ReplayAll()

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_proxy(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(cfg.CONF, "my_ip")
        self.mox.StubOutWithMock(cfg.CONF, "os_username")
        self.mox.StubOutWithMock(cfg.CONF, "os_password")
        self.mox.StubOutWithMock(cfg.CONF, "os_tenant_name")
        self.mox.StubOutWithMock(cfg.CONF, "os_auth_url")
        self.mox.StubOutWithMock(cfg.CONF, "os_region_name")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        cfg.CONF.my_ip = "my_ip_data"
        cfg.CONF.os_username = "os_username_data"
        cfg.CONF.os_password = "os_password_data"
        cfg.CONF.os_tenant_name = "os_tenant_name_data"
        cfg.CONF.os_auth_url = "os_auth_url_data"
        cfg.CONF.os_region_name = "os_region_name"
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        expect = get_proxy_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["proxy"]["userdata"] = USER_DATA_B64_ENC
        expect["proxy"]["args"].update(ppid=PPID1)
        expect["proxy"]["args"].update(rackapi_ip="my_ip_data")
        expect["proxy"]["args"].update(os_username="os_username_data")
        expect["proxy"]["args"].update(os_password="os_password_data")
        expect["proxy"]["args"].update(os_tenant_name="os_tenant_name_data")
        expect["proxy"]["args"].update(os_auth_url="os_auth_url_data")
        expect["proxy"]["args"].update(os_region_name="os_region_name")
        for key in body["proxy"]:
            self.assertEqual(body["proxy"][key], expect["proxy"][key])

    def test_create_proxy_without_proxy_name(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(cfg.CONF, "my_ip")
        self.mox.StubOutWithMock(cfg.CONF, "os_username")
        self.mox.StubOutWithMock(cfg.CONF, "os_password")
        self.mox.StubOutWithMock(cfg.CONF, "os_tenant_name")
        self.mox.StubOutWithMock(cfg.CONF, "os_auth_url")
        self.mox.StubOutWithMock(cfg.CONF, "os_region_name")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        cfg.CONF.my_ip = "my_ip_data"
        cfg.CONF.os_username = "os_username_data"
        cfg.CONF.os_password = "os_password_data"
        cfg.CONF.os_tenant_name = "os_tenant_name_data"
        cfg.CONF.os_auth_url = "os_auth_url_data"
        cfg.CONF.os_region_name = "os_region_name"
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        request_body["proxy"].pop("name")
        expect = get_proxy_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["proxy"]["userdata"] = USER_DATA_B64_ENC
        expect["proxy"]["args"].update(ppid=PPID1)
        expect["proxy"]["args"].update(rackapi_ip="my_ip_data")
        expect["proxy"]["args"].update(os_username="os_username_data")
        expect["proxy"]["args"].update(os_password="os_password_data")
        expect["proxy"]["args"].update(os_tenant_name="os_tenant_name_data")
        expect["proxy"]["args"].update(os_auth_url="os_auth_url_data")
        expect["proxy"]["args"].update(os_region_name="os_region_name")
        expect["proxy"].update(name="proxy-" + PID1)
        for key in body["proxy"]:
            self.assertEqual(body["proxy"][key], expect["proxy"][key])

    def test_create_proxy_ipc_endpoint_invalid_max_length(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(cfg.CONF, "my_ip")
        self.mox.StubOutWithMock(cfg.CONF, "os_username")
        self.mox.StubOutWithMock(cfg.CONF, "os_password")
        self.mox.StubOutWithMock(cfg.CONF, "os_tenant_name")
        self.mox.StubOutWithMock(cfg.CONF, "os_auth_url")
        self.mox.StubOutWithMock(cfg.CONF, "os_region_name")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        cfg.CONF.my_ip = "my_ip_data"
        cfg.CONF.os_username = "os_username_data"
        cfg.CONF.os_password = "os_password_data"
        cfg.CONF.os_tenant_name = "os_tenant_name_data"
        cfg.CONF.os_auth_url = "os_auth_url_data"
        cfg.CONF.os_region_name = "os_region_name"
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        request_body["proxy"].update(ipc_endpoint="a" * (256))

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_proxy_shm_endpoint_invalid_max_length(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(cfg.CONF, "my_ip")
        self.mox.StubOutWithMock(cfg.CONF, "os_username")
        self.mox.StubOutWithMock(cfg.CONF, "os_password")
        self.mox.StubOutWithMock(cfg.CONF, "os_tenant_name")
        self.mox.StubOutWithMock(cfg.CONF, "os_auth_url")
        self.mox.StubOutWithMock(cfg.CONF, "os_region_name")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        cfg.CONF.my_ip = "my_ip_data"
        cfg.CONF.os_username = "os_username_data"
        cfg.CONF.os_password = "os_password_data"
        cfg.CONF.os_tenant_name = "os_tenant_name_data"
        cfg.CONF.os_auth_url = "os_auth_url_data"
        cfg.CONF.os_region_name = "os_region_name"
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        request_body["proxy"].update(shm_endpoint="a" * (256))

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_proxy_fs_endpoint_invalid_max_length(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(cfg.CONF, "my_ip")
        self.mox.StubOutWithMock(cfg.CONF, "os_username")
        self.mox.StubOutWithMock(cfg.CONF, "os_password")
        self.mox.StubOutWithMock(cfg.CONF, "os_tenant_name")
        self.mox.StubOutWithMock(cfg.CONF, "os_auth_url")
        self.mox.StubOutWithMock(cfg.CONF, "os_region_name")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        cfg.CONF.my_ip = "my_ip_data"
        cfg.CONF.os_username = "os_username_data"
        cfg.CONF.os_password = "os_password_data"
        cfg.CONF.os_tenant_name = "os_tenant_name_data"
        cfg.CONF.os_auth_url = "os_auth_url_data"
        cfg.CONF.os_region_name = "os_region_name"
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        request_body["proxy"].update(fs_endpoint="a" * (256))

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_proxy_already_exist(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        request_body["proxy"].update(fs_endpoint="a" * (256))

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_proxy_invalid_dict_key(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(ppid=PPID1)
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_args_value_integer(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(args={
            "test_key1": 123, "test_key2": 456})
        expect = get_base_process_response_body(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(ppid=PPID1)
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        expect["process"]["args"].update(test_key1="123")
        expect["process"]["args"].update(test_key2="456")
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_default_securitygroup(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_all")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        db.securitygroup_get_all(
            IsA(context.RequestContext), GID,
            filters=IsA(dict)).AndReturn([
                {"securitygroup_id": "securitygroup_id_data",
                 "neutron_securitygroup_id": "neutron_securitygroup_id_data"}])
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].pop("securitygroup_ids")
        request_body["process"].pop("ppid")
        expect = get_base_process_response_body(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        expect["process"].update(ppid=None)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_parent_securitygroup_and_image_and_flavor(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].pop("securitygroup_ids")
        request_body["process"].pop("glance_image_id")
        request_body["process"].pop("nova_flavor_id")
        request_body["process"].update(args={"key": "value"})

        expect = get_base_process_response_body(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        expect["process"]["args"].update(ppid=PPID1)
        expect["process"]["args"].update(key="value")
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_without_keypair_id(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)
        request_body["process"].pop("keypair_id")
        expect["process"]["keypair_id"] = KEYPAIR_ID1

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(ppid=PPID1)
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_without_keypair_id_and_ppid(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(db, "keypair_get_all")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.keypair_get_all(IsA(context.RequestContext), GID,
                           filters=IsA(dict))\
            .AndReturn([{"keypair_id": "keypair_id_data",
                         "nova_keypair_id": "nova_keypair_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(str),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)
        request_body["process"].pop("keypair_id")
        request_body["process"].pop("ppid")
        expect["process"]["keypair_id"] = KEYPAIR_ID1

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        expect["process"].update(keypair_id="keypair_id_data")
        expect["process"].update(ppid=None)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_without_process_name(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_create")
        self.mox.StubOutWithMock(
            manager.ResourceOperator, "get_process_address")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        manager.ResourceOperator.get_process_address(
            IsA(context.RequestContext),
            IsA(str)).AndReturn("proxy_instance_id_data")
        manager.ResourceOperator.process_create(
            IsA(context.RequestContext),
            name=IsA(unicode),
            key_name=IsA(unicode),
            security_groups=IsA(list),
            image=IsA(unicode),
            flavor=IsA(int),
            userdata=IsA(unicode),
            meta=IsA(dict),
            nics=IsA(list)).AndReturn((NOVA_INSTANCE_ID1, "BUILDING"))
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].pop("name")
        expect = get_base_process_response_body(process)
        expect["process"]["name"] = "process-" + PID1

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)

        self.assertEqual(res.status_code, 202)
        expect["process"]["userdata"] = USER_DATA_B64_ENC
        expect["process"]["args"].update(ppid=PPID1)
        expect["process"]["args"].update(proxy_ip="proxy_instance_id_data")
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_process_proxy_not_exits(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_process_invalid_dict_key(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_proxy_request_body1(process)
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_gid(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), IsA(unicode), filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        self.mox.ReplayAll()

        gid = "aaaaaaaaa"
        process = _base_process1(gid, PID1)
        request_body = get_base_request_body1(process)

        url = get_base_url(gid)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_invalid_securitygroup_ids(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), IsA(unicode), filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(securitygroup_ids={"key": "value"})
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_securitygroup_ids(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), IsA(unicode), filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(securitygroup_ids=["invalid_id"])
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_invalid_args(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(args=[{"key": "value"}])

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_keypair_id(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), IsA(unicode), filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(keypair_id="aaaaaaaaa")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_invalid_format_ppid(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), IsA(unicode), filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(ppid="aaaaaaaaa")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_process_name_is_whitespace(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(name="   ")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_default_security_group_not_found(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_all(IsA(context.RequestContext), GID,
                                 filters=IsA(dict)).AndReturn([])
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].pop("securitygroup_ids")
        request_body["process"].pop("ppid")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_userdata(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")

        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(userdata="/")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_empty_body(self):
        request_body = {"process": {}}

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

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

    def test_create_notfound_networks(self):
        self.stubs.Set(db, "network_get_all", fake_network_get_all_not_found)
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "securitygroup_get_by_securitygroup_id")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"nova_instance_id": "nova_instance_id_data"}])
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data1"})
        db.securitygroup_get_by_securitygroup_id(
            IsA(context.RequestContext), GID, IsA(unicode)).AndReturn(
                {"neutron_securitygroup_id": "securitygroup_id_data2"})
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def delete_invalid_format_gid(self):
        url = get_base_url("aaaaaaa") + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_invalid_format_pid(self):
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update(self):

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(args='{"key": "value"}')
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": "ACTIVE",
                "userdata": None,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"process": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_instance_id": process["nova_instance_id"],
                "nova_flavor_id": process["nova_flavor_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": process["app_status"],
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"process": {"app_status": "ACTIVE"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["process"]:
            self.assertEqual(expect["process"][key], body["process"][key])

    def test_update_invalid_request_body(self):
        request_body = {"invalid": {"app_status": "ACTIVE"}}

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_app_status_required(self):
        request_body = {"process": {}}

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_not_found(self):
        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(
            IsA(context.RequestContext), GID, PID1, IsA(dict))\
            .AndRaise(exception.ProcessNotFound(pid=PID1))
        self.mox.ReplayAll()
        request_body = {"process": {"app_status": "ACTIVE"}}
        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_update_proxy_all(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(args='{"key": "value"}')
            process.update(is_proxy=True)
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": "app_status_data",
                "ipc_endpoint": "ipc_endpoint_data",
                "shm_endpoint": "shm_endpoint_data",
                "fs_endpoint": "fs_endpoint_data",
                "userdata": None,
                "is_proxy": True,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"proxy": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_flavor_id": process["nova_flavor_id"],
                "nova_instance_id": process["nova_instance_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": process["app_status"],
                "ipc_endpoint": process.get("ipc_endpoint"),
                "shm_endpoint": process.get("shm_endpoint"),
                "fs_endpoint": process.get("fs_endpoint"),
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"proxy": {
            "app_status": "app_status_data",
            "ipc_endpoint": "ipc_endpoint_data",
            "shm_endpoint": "shm_endpoint_data",
            "fs_endpoint": "fs_endpoint_data"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["proxy"]:
            self.assertEqual(expect["proxy"][key], body["proxy"][key])

    def test_update_proxy_ipc_endpoint(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(is_proxy=True)
            process.update(args='{"key": "value"}')
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": "ipc_endpoint_data",
                "shm_endpoint": None,
                "fs_endpoint": None,
                "userdata": None,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"proxy": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_instance_id": process["nova_instance_id"],
                "nova_flavor_id": process["nova_flavor_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": process.get("ipc_endpoint"),
                "shm_endpoint": None,
                "fs_endpoint": None,
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"proxy": {
            "ipc_endpoint": "ipc_endpoint_data"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["proxy"]:
            self.assertEqual(expect["proxy"][key], body["proxy"][key])

    def test_update_proxy_shm_endpoint(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(is_proxy=True)
            process.update(args='{"key": "value"}')
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": None,
                "shm_endpoint": "shm_endpoint_data",
                "fs_endpoint": None,
                "userdata": None,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"proxy": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_instance_id": process["nova_instance_id"],
                "nova_flavor_id": process["nova_flavor_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": None,
                "shm_endpoint": process.get("shm_endpoint"),
                "fs_endpoint": None,
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"proxy": {
            "shm_endpoint": "shm_endpoint_data"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["proxy"]:
            self.assertEqual(expect["proxy"][key], body["proxy"][key])

    def test_update_proxy_fs_endpoint(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(is_proxy=True)
            process.update(args='{"key": "value"}')
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": None,
                "shm_endpoint": None,
                "fs_endpoint": "fs_endpoint_data",
                "userdata": None,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"proxy": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_instance_id": process["nova_instance_id"],
                "nova_flavor_id": process["nova_flavor_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": None,
                "ipc_endpoint": None,
                "shm_endpoint": None,
                "fs_endpoint": process.get("fs_endpoint"),
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"proxy": {
            "fs_endpoint": "fs_endpoint_data"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["proxy"]:
            self.assertEqual(expect["proxy"][key], body["proxy"][key])

    def test_update_proxy_app_status(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])

        def _fake_update(context, gid, pid, kwargs):
            process = _base(context)
            process.update(gid=gid)
            process.update(pid=pid)
            process.update(kwargs)
            process.update(is_proxy=True)
            process.update(args='{"key": "value"}')
            process.update(securitygroups=[{"securitygroup_id": None}])
            process.update(networks=[{"network_id": None}])
            return process

        def _update_process_mockdata(gid, pid):
            return {
                "pid": pid,
                "ppid": None,
                "gid": gid,
                "nova_instance_id": None,
                "nova_flavor_id": None,
                "display_name": None,
                "glance_image_id": None,
                "keypair_id": None,
                "userdata": None,
                "status": None,
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": "app_status_data",
                "ipc_endpoint": None,
                "shm_endpoint": None,
                "fs_endpoint": None,
                "userdata": None,
                "args": '{"key": "value"}',
                "securitygroups": [{"securitygroup_id": None}],
                "networks": [{"network_id": None}]}

        def _get_update_response_body(process):
            return {"proxy": {
                "pid": process["pid"],
                "ppid": process["ppid"],
                "gid": process["gid"],
                "nova_instance_id": process["nova_instance_id"],
                "nova_flavor_id": process["nova_flavor_id"],
                "name": process["display_name"],
                "glance_image_id": process["glance_image_id"],
                "keypair_id": process["keypair_id"],
                "userdata": process["userdata"],
                "status": process["status"],
                "user_id": "noauth",
                "project_id": "noauth",
                "app_status": process.get("app_status"),
                "ipc_endpoint": None,
                "shm_endpoint": None,
                "fs_endpoint": None,
                "userdata": process["userdata"],
                "args": json.loads(process["args"]),
                "securitygroup_ids": [None],
                "networks": [{
                    "fixed": None, "floating": None, "network_id": None}]}}

        self.stubs.Set(db, "process_update", _fake_update)
        self.mox.ReplayAll()

        request_body = {"proxy": {
            "app_status": "app_status_data"}}
        process = _update_process_mockdata(GID, PID1)
        expect = _get_update_response_body(process)

        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        for key in body["proxy"]:
            self.assertEqual(expect["proxy"][key], body["proxy"][key])

    def test_update_proxy_does_not_exist(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([])
        self.mox.ReplayAll()

        request_body = {"proxy": {"app_status": "app_status_data"}}
        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_proxy_invalid_request_body(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        request_body = {"invalid": {"app_status": "app_status_data"}}
        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_prxoy_no_keyword(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{}])
        self.mox.ReplayAll()

        request_body = {"proxy": {}}
        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_update_proxy_not_found(self):
        self.mox.StubOutWithMock(db, "process_get_all")
        self.mox.StubOutWithMock(db, "process_update")
        db.process_get_all(
            IsA(context.RequestContext), GID, filters=IsA(dict))\
            .AndReturn([{"pid": PID1}])
        db.process_update(
            IsA(context.RequestContext), GID, PID1, IsA(dict))\
            .AndRaise(exception.ProcessNotFound(pid=PID1))
        self.mox.ReplayAll()

        request_body = {"proxy": {"app_status": "app_status_data"}}
        url = "/v1/groups/" + GID + "/proxy"
        req = get_request(url, 'PUT', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_non_parent(self):
        self.stubs.Set(db, "process_delete", fake_delete)
        self.mox.StubOutWithMock(db, "process_get_by_pid")
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_delete")
        db.process_get_by_pid(
            IsA(context.RequestContext), GID, PID1)\
            .AndReturn(
                {"pid": PID1, "nova_instance_id": "nova_instance_id_data"})
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": PID1}).AndReturn([])
        manager.ResourceOperator.process_delete(
            IsA(context.RequestContext), IsA(str))
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_parent_child_relation(self):
        self.stubs.Set(db, "process_delete", fake_delete)
        self.mox.StubOutWithMock(db, "process_get_by_pid")
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(manager.ResourceOperator, "process_delete")

        # ppid
        #  |-- pid_1
        #  |    |---pid_1_1
        #  |---pid_2
        #  |    |---pid_2_1
        #  |         |---pid_2_1_1
        #  |         |---pid_2_1_2
        #  |---pid_3
        ppid = unicode(uuid.uuid4())
        pid_1 = unicode(uuid.uuid4())
        pid_1_1 = unicode(uuid.uuid4())
        pid_2 = unicode(uuid.uuid4())
        pid_2_1 = unicode(uuid.uuid4())
        pid_2_1_1 = unicode(uuid.uuid4())
        pid_2_1_2 = unicode(uuid.uuid4())
        pid_3 = unicode(uuid.uuid4())

        db.process_get_by_pid(IsA(context.RequestContext), GID, ppid)\
            .AndReturn(
                {"pid": ppid, "nova_instance_id": "nova_id_ppid"})

        # ppid -> [pid_1, pid_2, pid_3]
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": ppid})\
            .AndReturn(
                [{"pid": pid_1, "nova_instance_id": "nova_id_pid_1"},
                 {"pid": pid_2, "nova_instance_id": "nova_id_pid_2"},
                 {"pid": pid_3, "nova_instance_id": "nova_id_pid_3"}])

        # pid_1 -> [pid_1_1]
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_1})\
            .AndReturn(
                [{"pid": pid_1_1, "nova_instance_id": "nova_id_pid_1_1"}])

        # pid_1_1 -> []
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_1_1})\
            .AndReturn([])

        # pid_2 -> [pid_2_1]
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_2})\
            .AndReturn(
                [{"pid": pid_2_1, "nova_instance_id": "nova_id_pid_2_1"}])

        # pid_2_1 -> [pid_2_1_1, pid_2_1_2]
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_2_1})\
            .AndReturn(
                [{"pid": pid_2_1_1, "nova_instance_id": "nova_id_pid_2_1_1"},
                 {"pid": pid_2_1_2, "nova_instance_id": "nova_id_pid_2_1_2"}])

        # pid_2_1_1 -> []
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_2_1_1})\
            .AndReturn([])

        # pid_2_1_2 -> []
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_2_1_2})\
            .AndReturn([])

        # pid_3 -> []
        db.process_get_all(
            IsA(context.RequestContext), GID, {"ppid": pid_3})\
            .AndReturn([])

        for i in range(8):
            manager.ResourceOperator.process_delete(
                        IsA(context.RequestContext), IsA(str))

        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + ppid
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_not_found_exception(self):
        self.mox.StubOutWithMock(db, "process_get_by_pid")
        db.process_get_by_pid(IsA(context.RequestContext), GID, PID1)\
            .AndRaise(exception.NotFound())
        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
