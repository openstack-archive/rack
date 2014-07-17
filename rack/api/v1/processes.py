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

from oslo.config import cfg

import base64
import six
import uuid
import webob

from rack import db
from rack import exception
from rack import utils

from rack.api.v1.views import processes as views_processes
from rack.api import wsgi

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import uuidutils

from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Process controller for RACK API."""

    _view_builder_class = views_processes.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()
        self.operator_rpcapi = operator_rpcapi.ResourceOperatorAPI()

    @wsgi.response(200)
    def index(self, req, gid):

        def _validate(gid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

        try:
            _validate(gid)
        except exception.ProcessNotFound:
            msg = _("Process could not be found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        filters = {}
        pid = req.params.get('pid')
        ppid = req.params.get('ppid')
        name = req.params.get('name')
        status = req.params.get('status')
        glance_image_id = req.params.get('glance_image_id')
        nova_flavor_id = req.params.get('nova_flavor_id')
        securitygroup_id = req.params.get('securitygroup_id')
        network_id = req.params.get('network_id')
        keypair_id = req.params.get('keypair_id')

        if pid:
            filters['pid'] = pid
        if ppid:
            filters['ppid'] = ppid
        if name:
            filters['name'] = name
        if status:
            filters['status'] = status
        if glance_image_id:
            filters['glance_image_id'] = glance_image_id
        if nova_flavor_id:
            filters['nova_flavor_id'] = nova_flavor_id
        if securitygroup_id:
            filters['securitygroup_id'] = securitygroup_id
        if network_id:
            filters['network_id'] = network_id
        if keypair_id:
            filters['keypair_id'] = keypair_id

        context = req.environ['rack.context']
        process_list = db.process_get_all(context, gid, filters)

        return self._view_builder.index(process_list)

    @wsgi.response(200)
    def show(self, req, gid, pid):

        def _validate(gid, pid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(pid):
                raise exception.ProcessNotFound(pid=pid)

        try:
            _validate(gid, pid)
            context = req.environ['rack.context']
            process = db.process_get_by_pid(context, gid, pid)
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        return self._view_builder.show(process)

    @wsgi.response(202)
    def create(self, req, body, gid):

        def _validate_process(context, gid, body):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not self.is_valid_body(body, 'process'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["process"]
            ppid = values.get("ppid")
            keypair_id = values.get("keypair_id")
            name = values.get("name")
            glance_image_id = values.get("glance_image_id")
            nova_flavor_id = values.get("nova_flavor_id")
            securitygroup_ids = values.get("securitygroup_ids")
            userdata = values.get("userdata")

            if ppid is not None:
                if not uuidutils.is_uuid_like(ppid):
                    raise exception.ProcessNotFound(pid=ppid)
                p_process = db.process_get_by_pid(context, gid, ppid)

            if keypair_id is not None:
                if not uuidutils.is_uuid_like(keypair_id):
                    raise exception.KeypairNotFound(keypair_id=keypair_id)
            elif ppid is not None:
                keypair_id = p_process.get("keypair_id")

            if isinstance(name, six.string_types):
                name = name.strip()
                utils.check_string_length(name, 'name', min_length=1,
                                          max_length=255)
            elif name is not None:
                msg = _("name must be a String")
                raise exception.InvalidInput(reason=msg)

            if glance_image_id is None:
                if ppid is not None:
                    glance_image_id = p_process.get("glance_image_id")
            elif not uuidutils.is_uuid_like(glance_image_id):
                msg = _("glance_image_id is invalid format")
                raise exception.InvalidInput(reason=msg)

            if nova_flavor_id is None and ppid is not None:
                nova_flavor_id = p_process.get("nova_flavor_id")
            utils.validate_integer(nova_flavor_id, 'nova_flavor_id')

            if not securitygroup_ids:
                if ppid is not None:
                    securitygroup_ids = [securitygroup.get("securitygroup_id")
                                         for securitygroup in p_process.get(
                                         "securitygroups")]
                else:
                    msg = _("securitygroup_ids is required")
                    raise exception.InvalidInput(reason=msg)

            if isinstance(securitygroup_ids, list):
                for securitygroup_id in securitygroup_ids:
                    if securitygroup_id is not None and not uuidutils\
                            .is_uuid_like(securitygroup_id):
                        raise exception.SecuritygroupNotFound(
                            securitygroup_id=securitygroup_id)
            else:
                msg = _("securitygroup_ids must be list")
                raise exception.InvalidInput(reason=msg)

            if userdata:
                try:
                    userdata = base64.b64decode(userdata)
                except TypeError as e:
                    raise webob.exc.HTTPBadRequest(
                        explanation=e.format_message())

            valid_values = {}
            valid_values_process = {}
            valid_values_process["gid"] = gid
            valid_values_process["keypair_id"] = keypair_id
            valid_values_process["ppid"] = ppid
            valid_values_process["display_name"] = name
            valid_values_process["glance_image_id"] = glance_image_id
            valid_values_process["nova_flavor_id"] = nova_flavor_id
            valid_values_process["is_proxy"] = False
            valid_values_process["app_status"] = "BUILDING"

            valid_values_userdata = {}
            valid_values_userdata["userdata"] = userdata

            valid_values_securitygroup = {}
            valid_values_securitygroup["securitygroup_ids"] = securitygroup_ids

            valid_values["process"] = valid_values_process
            valid_values["userdata"] = valid_values_userdata
            valid_values["securitygroup"] = valid_values_securitygroup

            return valid_values

        def _validate_metadata(metadata):
            if metadata is None:
                return {}

            if not isinstance(metadata, dict):
                msg = _("metadata must be a dict")
                raise exception.InvalidInput(reason=msg)

            return metadata

        try:
            context = req.environ['rack.context']
            valid_values = _validate_process(context, gid, body)
            values = valid_values.get("process")
            securitygroup_ids = valid_values.get(
                "securitygroup").get("securitygroup_ids")
            metadata = _validate_metadata(metadata=body["process"]
                                          .get("args"))
            metadata.update({"proxy_ip": cfg.CONF.my_ip})
            userdata = valid_values.get("userdata")

            values["deleted"] = 0
            values["status"] = "BUILDING"
            values["pid"] = unicode(uuid.uuid4())
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            values["display_name"] = values[
                "display_name"] or "pro-" + values["pid"]
            values["userdata"] = userdata.get("userdata")

            if values["ppid"]:
                db.process_get_by_pid(context, gid, values["ppid"])
            if values["keypair_id"]:
                nova_keypair_id = db.keypair_get_by_keypair_id(
                    context, gid, values["keypair_id"]).get("nova_keypair_id")
            else:
                nova_keypair_id = None
            networks = db.network_get_all(context, gid, {"status": "ACTIVE"})
            if not networks:
                raise exception.NoNetworksFound(gid=values["gid"])
            network_ids = [network["network_id"] for network in networks]
            process = db.process_create(
                context, values, network_ids, securitygroup_ids)

        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        try:
            host = self.scheduler_rpcapi.select_destinations(
                context,
                request_spec={},
                filter_properties={})
            self.operator_rpcapi.process_create(
                context,
                host["host"],
                pid=values["pid"],
                ppid=values["ppid"] or values["pid"],
                gid=gid,
                name=values["display_name"],
                glance_image_id=values["glance_image_id"],
                nova_flavor_id=values["nova_flavor_id"],
                nova_keypair_id=nova_keypair_id,
                neutron_securitygroup_ids=[securitygroup[
                    "neutron_securitygroup_id"]
                    for securitygroup in process["securitygroups"]],
                neutron_network_ids=[network["neutron_network_id"]
                                     for network in process["networks"]],
                metadata=metadata,
                userdata=userdata.get("userdata"))
        except Exception as e:
            LOG.exception(e)
            pid = values["pid"]
            db.process_update(context, gid, pid, {"status": "ERROR"})
            raise exception.ProcessCreateFailed()

        return self._view_builder.create(process)

    @wsgi.response(200)
    def update(self, req, body, gid, pid):

        def _validate(body, gid, pid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(pid):
                raise exception.ProcessNotFound(pid=pid)

            if not self.is_valid_body(body, 'process'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            db.process_get_by_pid(context, gid, pid)

            values = body["process"]
            app_status = values.get("app_status")

            if not app_status:
                msg = _("app_status is required")
                raise exception.InvalidInput(reason=msg)

            valid_values = {}
            valid_values["app_status"] = app_status

            return valid_values

        context = req.environ['rack.context']

        try:
            values = _validate(body, gid, pid)
            process = db.process_update(context, gid, pid, values)

        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        except exception.ProcessNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.update(process)

    @wsgi.response(204)
    def delete(self, req, gid, pid):

        def _validate(gid, pid):

            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(pid):
                raise exception.ProcessNotFound(pid=pid)

        def _get_child_pid(context, gid, pid):
            processes = db.process_get_all(context, gid, {"ppid": pid})
            targets = []
            for process in processes:
                if "pid" in process:
                    targets.append(process["pid"])
                    targets.extend(
                        _get_child_pid(context, gid, process["pid"]))
            return targets

        try:
            _validate(gid, pid)
            context = req.environ['rack.context']
            targets = _get_child_pid(context, gid, pid)
            targets.append(pid)

            for target in targets:
                process = db.process_delete(context, gid, target)
                host = self.scheduler_rpcapi.select_destinations(
                    context,
                    request_spec={},
                    filter_properties={})
                self.operator_rpcapi.process_delete(
                    context,
                    host["host"],
                    nova_instance_id=process["nova_instance_id"])

        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        except Exception as e:
            LOG.exception(e)
            raise exception.ProcessDeleteFailed()


def create_resource():
    return wsgi.Resource(Controller())
