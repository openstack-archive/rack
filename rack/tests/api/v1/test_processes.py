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
from mox import IgnoreArg
 
from rack.api.v1 import processes
from rack import context
from rack import db
from rack import exception
from rack.openstack.common import jsonutils
from rack import test
from rack.tests.api import fakes
from rack.api.v1.views.processes import ViewBuilder
from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi

import uuid
import webob
from rack.openstack.common import log as logging

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

METADATA1 = {"type1":"test1","type2":"test2"}

NOVA_INSTANCE_ID = unicode(uuid.uuid4())

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
            "pid":pid,
            "ppid":PPID1,
            "nova_instance_id":None,
            "gid":gid,
            "display_name":"test1",
            "nova_flavor_id":1,
            "glance_image_id":GLANCE_IMAGE_ID1,
            "keypair_id":KEYPAIR_ID1,
            "securitygroups":_base_securitygroups1(),
            "networks":_base_networks(),
            "status":"BUILDING"
               }


def _base_process2(gid, pid):
    return {
            "pid":pid,
            "ppid":PPID2,
            "nova_instance_id":None,
            "gid":gid,
            "display_name":"test2",
            "nova_flavor_id":2,
            "glance_image_id":GLANCE_IMAGE_ID2,
            "keypair_id":KEYPAIR_ID2,
            "securitygroups":_base_securitygroups2(),
            "networks":_base_networks(),
            "status":"BUILDING"
               }


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
    process.update(nova_instance_id=NOVA_INSTANCE_ID)
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
            "ppid": process["ppid"],
            "name": process["display_name"],
            "nova_flavor_id": process["nova_flavor_id"],
            "glance_image_id": process["glance_image_id"],
            "keypair_id": process["keypair_id"],
            "securitygroup_ids": [securitygroup["securitygroup_id"] 
                                  for securitygroup in process["securitygroups"]],
            "metadata" : METADATA1
            }


def get_base_request_body1(process):
    return {"process": get_base_body(process)}


def get_base_process_body(process):
    process_body = get_base_body(process)
    process_body.update(gid=GID)
    process_body.update(pid=process["pid"])
    process_body.update(status=process["status"])
    process_body.update(user_id="fake")
    process_body.update(project_id="fake")
    process_body.update(network_ids=[NETWORK_ID1,NETWORK_ID2])
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


class ProcessesTest(test.NoDBTestCase):

    def _set_mox_db_process_update_on_error(self):
        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(IsA(context.RequestContext), IsA(unicode), IsA(unicode), {"status": "ERROR"})

    def _set_mox_scheduler_select_destinations(self, return_value={"host": "fake_host"}, do_process_update=True):
        self.mox.StubOutWithMock(scheduler_rpcapi.SchedulerAPI, "select_destinations")
        method = scheduler_rpcapi.SchedulerAPI.select_destinations(
                                                                   IsA(context.RequestContext), 
                                                                   request_spec={}, 
                                                                   filter_properties={})
        if issubclass(return_value.__class__, Exception):
            method.AndRaise(return_value)
            if do_process_update:
                self._set_mox_db_process_update_on_error()
        else:
            method.AndReturn(return_value)

    def _set_mox_resource_operator_process_create(self, exception=None):
        self._set_mox_scheduler_select_destinations()
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "process_create")
        method = operator_rpcapi.ResourceOperatorAPI.process_create(IsA(context.RequestContext), "fake_host", 
                                                                    pid=IsA(unicode),
                                                                    ppid=IsA(unicode),
                                                                    gid=IsA(unicode),
                                                                    name=IsA(unicode), 
                                                                    glance_image_id=IsA(unicode), 
                                                                    nova_flavor_id=IsA(int), 
                                                                    nova_keypair_id=IgnoreArg(), 
                                                                    neutron_securitygroup_ids=IsA(list), 
                                                                    neutron_network_ids=IsA(list), 
                                                                    metadata=IsA(dict), 
                                                                    )
        if issubclass(exception.__class__, Exception):
            method.AndRaise(exception)
            self._set_mox_db_process_update_on_error()
        
    def setUp(self):
        super(ProcessesTest, self).setUp()
        self.stubs.Set(uuid, "uuid4", fake_pid1)
        self.stubs.Set(db, "keypair_get_by_keypair_id", fake_keypair_get_by_keypair_id)        
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

        url = get_base_url(GID)
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(body, expect)

    def test_index_with_param(self):
        param = \
          "?pid=" + PID1 + \
          "?ppid=" + PID1 + \
          "?status=" + PID1 + \
          "?glance_image_id=" + PID1 + \
          "?nova_flavor_id=" + PID1 + \
          "?securitygroup_id=" + PID1 + \
          "?keypair_id=" + PID1 + \
          "?network_id=" + PID1 + \
          "&name=test"
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
        process = _base_process1(GID, PID1)
        expect = get_base_process_response_body(process)

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
        self.stubs.Set(db, "keypair_get_by_keypair_id", fake_keypair_get_by_keypair_id_raise_not_found)
        url = get_base_url(GID) + "/" + PIDX
        req = get_request(url, 'GET')
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
  
    def test_create(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_raise_exception_by_scheduler_rpcapi(self):
        self._set_mox_scheduler_select_destinations(Exception())
        self.mox.ReplayAll()
 
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
   
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)

    def test_create_raise_exception_by_operator_rpcapi(self):
        self._set_mox_resource_operator_process_create(Exception())
        self.mox.ReplayAll()
  
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
   
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)
  
    def test_create_invalid_format_gid(self):
        gid = "aaaaaaaaa"
        process = _base_process1(gid, PID1)
        request_body = get_base_request_body1(process)
 
        url = get_base_url(gid)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
 
    def test_create_invalid_format_keypair_id(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(keypair_id="aaaaaaaaa")
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_without_keypair_id(self):
        self._set_mox_resource_operator_process_create()
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
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])
   
    def test_create_invalid_format_ppid(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(ppid="aaaaaaaaa")
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_without_ppid(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)

        request_body["process"].pop("ppid")
        expect["process"]["ppid"] = None

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_process_name_is_whitespace(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
   
        request_body["process"].update(name="   ")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
  
    def test_create_process_name_with_leading_trailing_whitespace(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)
        
        request_body["process"]["name"] = "  test  "
        expect["process"]["name"] = "test"

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_create_check_process_name_length(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
   
        MAX_LENGTH = 255
        request_body["process"].update(name="a" * (MAX_LENGTH + 1))

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
   
    def test_create_check_process_name_invalid_type(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(name=11111111)
   
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)
   
    def test_create_without_process_name(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)

        request_body["process"].pop("name")
        expect["process"]["name"] = "pro-" + PID1

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])
  
    def test_create_invalid_format_glance_image_id(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        
        request_body["process"].update(glance_image_id="aaaaaaaaa")
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_not_int_nova_flavor_id(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        
        request_body["process"].update(ppid=None)
        request_body["process"].update(nova_flavor_id=None)
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_not_list_securitygroup_ids(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(securitygroup_ids=unicode(uuid.uuid4()))
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_invalid_format_in_list_securitygroup_ids(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(securitygroup_ids=[unicode(uuid.uuid4()),"aaaaaaa"])
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_blank_list_securitygroup_ids(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(ppid=None)
        request_body["process"].update(securitygroup_ids=[])
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_not_dict_metadata(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)

        request_body["process"].update(metadata="aaaaaaa")
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 400)

    def test_create_without_metadata(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        expect = get_base_process_response_body(process)

        request_body["process"].pop("metadata")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

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

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_notfound_ppid(self):
        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        
        request_body["process"].update(ppid=PIDX)
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_notfound_keypair_id(self):
        self.stubs.Set(db, "keypair_get_by_keypair_id", fake_keypair_get_by_keypair_id_raise_not_found)

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
 
        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_create_without_secgroup_keypair_id_glance_image_flavor_id(self):
        self._set_mox_resource_operator_process_create()
        self.mox.ReplayAll()

        process = _base_process1(GID, PID1)
        request_body = get_base_request_body1(process)
        request_body["process"].update(securitygroup_ids=None)
        request_body["process"].update(keypair_id=None)
        request_body["process"].update(glance_image_id=None)
        request_body["process"].update(nova_flavor_id=None)
        
        expect = get_base_process_response_body(process)

        request_body["process"].pop("metadata")

        url = get_base_url(GID)
        req = get_request(url, 'POST', request_body)
        res = req.get_response(self.app)
        body = jsonutils.loads(res.body)
        self.assertEqual(res.status_code, 202)
        for key in body["process"]:
            self.assertEqual(body["process"][key], expect["process"][key])

    def test_delete_invalid_format_gid(self):
        url = get_base_url("aaaaaaa") + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)
  
    def test_delete_invalid_format_pid(self):
        url = get_base_url(GID) + "/" + "aaaaa"
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

class ProcessesTest2(test.NoDBTestCase):

    def _set_mox_db_process_update_on_error(self):
        self.mox.StubOutWithMock(db, "process_update")
        db.process_update(IsA(context.RequestContext), IsA(unicode), IsA(unicode), {"status": "ERROR"})

    def _set_mox_scheduler_select_destinations(self, return_value={"host": "fake_host"}, do_process_update=True):
        method = scheduler_rpcapi.SchedulerAPI.select_destinations(
                                                                   IsA(context.RequestContext), 
                                                                   request_spec={}, 
                                                                   filter_properties={})
        if issubclass(return_value.__class__, Exception):
            method.AndRaise(return_value)
            if do_process_update:
                self._set_mox_db_process_update_on_error()
        else:
            method.AndReturn(return_value)

        
    def _set_mox_resource_operator_process_delete(self, exception=None):
        self._set_mox_scheduler_select_destinations()
        method = operator_rpcapi.ResourceOperatorAPI.process_delete(IsA(context.RequestContext), "fake_host", 
                                                                    nova_instance_id=IsA(unicode), 
                                                                    )
        if issubclass(exception.__class__, Exception):
            method.AndRaise(exception)

    def setUp(self):
        super(ProcessesTest2, self).setUp()
        self.stubs.Set(uuid, "uuid4", fake_pid1)
        self.app = fakes.wsgi_app()
        self.view = ViewBuilder()

    def test_delete_non_parent(self):
        self.stubs.Set(db, "process_delete", fake_delete)
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(scheduler_rpcapi.SchedulerAPI, "select_destinations")
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "process_delete")
            
        self._set_mox_resource_operator_process_delete()
        db.process_get_all(IsA(context.RequestContext), GID, {"ppid": PID1}).AndReturn([{}])

        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_parent_child_relation(self):
        self.stubs.Set(db, "process_delete", fake_delete)
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(scheduler_rpcapi.SchedulerAPI, "select_destinations")
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "process_delete")
            
        self._set_mox_resource_operator_process_delete()
        self._set_mox_resource_operator_process_delete()

        db.process_get_all(IsA(context.RequestContext), GID, {"ppid": PID1}).AndReturn([{"pid" : PID2}])
        db.process_get_all(IsA(context.RequestContext), GID, {"ppid": PID2}).AndReturn([{}])

        self.mox.ReplayAll()

        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 204)

    def test_delete_not_found_exception(self):
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(db, 'process_delete')
            
        db.process_get_all(IsA(context.RequestContext), GID, {"ppid": PID1}).AndReturn([{}])
        db.process_delete(IsA(context.RequestContext), GID, PID1).AndRaise(exception.ProcessNotFound(pid=PID1))
        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 404)

    def test_delete_exception(self):
        self.stubs.Set(db, "process_delete", fake_delete)
        self.mox.StubOutWithMock(db, 'process_get_all')
        self.mox.StubOutWithMock(scheduler_rpcapi.SchedulerAPI, "select_destinations")
        self.mox.StubOutWithMock(operator_rpcapi.ResourceOperatorAPI, "process_delete")
            
        db.process_get_all(IsA(context.RequestContext), GID, {"ppid": PID1}).AndReturn([{}])
        self._set_mox_resource_operator_process_delete(Exception())

        self.mox.ReplayAll()
        url = get_base_url(GID) + "/" + PID1
        req = get_request(url, "DELETE")
        res = req.get_response(self.app)
        self.assertEqual(res.status_code, 500)
