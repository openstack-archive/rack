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
import json

from oslo.config import cfg

import base64
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

from rack.resourceoperator import manager


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Process controller for RACK API."""

    _view_builder_class = views_processes.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.manager = manager.ResourceOperator()

    def _uuid_check(self, gid=None, pid=None, keypair_id=None,
                    securitygroup_id=None):
        if gid:
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)
        if pid:
            if not uuidutils.is_uuid_like(pid):
                raise exception.ProcessNotFound(pid=pid)
        if keypair_id:
            if not uuidutils.is_uuid_like(keypair_id):
                raise exception.KeypairNotFound(keypair_id=keypair_id)
        if securitygroup_id:
            if not uuidutils.is_uuid_like(securitygroup_id):
                raise exception.SecuritygroupNotFound(
                    securitygroup_id=securitygroup_id)

    @wsgi.response(200)
    def index(self, req, gid):
        try:
            self._uuid_check(gid)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        context = req.environ['rack.context']
        process_list = db.process_get_all(context, gid)
        process_list = self.manager.process_list(context, process_list)

        return self._view_builder.index(process_list)

    @wsgi.response(200)
    def show(self, req, gid, pid):
        try:
            self._uuid_check(gid, pid)
            context = req.environ['rack.context']
            process = db.process_get_by_pid(context, gid, pid)
            self.manager.process_show(context, process)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show(process)

    @wsgi.response(200)
    def show_proxy(self, req, gid):
        try:
            self._uuid_check(gid)
            context = req.environ['rack.context']
            process = db.process_get_all(
                context, gid, filters={"is_proxy": True})
            if not process:
                msg = _("Proxy process does not exist in the group %s" % gid)
                raise webob.exc.HTTPBadRequest(explanation=msg)
            self.manager.process_show(context, process[0])
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show_proxy(process[0])

    @wsgi.response(202)
    def create(self, req, body, gid, is_proxy=False):

        def _validate(context, body, gid, is_proxy=False):
            proxy = db.process_get_all(
                context, gid, filters={"is_proxy": True})
            if is_proxy:
                if len(proxy) > 0:
                    msg = _(
                        "Proxy process already exists in the group %s" % gid)
                    raise exception.InvalidInput(reason=msg)
            else:
                if len(proxy) != 1:
                    msg = _(
                        "Proxy process does not exist in the group %s" % gid)
                    raise webob.exc.HTTPBadRequest(explanation=msg)

            keyname = "proxy" if is_proxy else "process"
            if not self.is_valid_body(body, keyname):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body[keyname]
            ppid = values.get("ppid")
            name = values.get("name")
            keypair_id = values.get("keypair_id")
            securitygroup_ids = values.get("securitygroup_ids")
            floating_networks = values.get("floating_networks")
            glance_image_id = values.get("glance_image_id")
            nova_flavor_id = values.get("nova_flavor_id")
            userdata = values.get("userdata")
            args = values.get("args")

            self._uuid_check(gid, ppid, keypair_id)

            pid = unicode(uuid.uuid4())
            if not name:
                prefix = "proxy-" if is_proxy else "process-"
                name = prefix + pid

            if ppid:
                parent_process = db.process_get_by_pid(context, gid, ppid)

            nova_keypair_id = None
            if keypair_id:
                keypair = db.keypair_get_by_keypair_id(
                    context, gid, keypair_id)
                nova_keypair_id = keypair["nova_keypair_id"]
            elif ppid:
                keypair_id = parent_process.get("keypair_id")
                if keypair_id:
                    keypair = db.keypair_get_by_keypair_id(
                        context, gid, keypair_id)
                    nova_keypair_id = keypair["nova_keypair_id"]
            else:
                default_keypair = db.keypair_get_all(
                    context, gid,
                    filters={"is_default": True})
                if default_keypair:
                    keypair_id = default_keypair[0]["keypair_id"]
                    nova_keypair_id = default_keypair[0]["nova_keypair_id"]

            if securitygroup_ids is not None and\
                    not isinstance(securitygroup_ids, list):
                msg = _("securitygroupids must be a list")
                raise exception.InvalidInput(reason=msg)
            elif securitygroup_ids:
                neutron_securitygroup_ids = []
                for id in securitygroup_ids:
                    self._uuid_check(securitygroup_id=id)
                    securitygroup = db.securitygroup_get_by_securitygroup_id(
                        context, gid, id)
                    neutron_securitygroup_ids.append(
                        securitygroup["neutron_securitygroup_id"])
            elif ppid:
                securitygroups = parent_process.get("securitygroups")
                securitygroup_ids =\
                    [securitygroup["securitygroup_id"]
                        for securitygroup in securitygroups]
                neutron_securitygroup_ids =\
                    [securitygroup["neutron_securitygroup_id"]
                        for securitygroup in securitygroups]
            else:
                default_securitygroups = db.securitygroup_get_all(
                    context, gid,
                    filters={"is_default": True})
                if default_securitygroups:
                    securitygroup_ids =\
                        [securitygroup["securitygroup_id"]
                            for securitygroup in default_securitygroups]
                    neutron_securitygroup_ids =\
                        [securitygroup["neutron_securitygroup_id"]
                            for securitygroup in default_securitygroups]
                else:
                    msg = _(
                        "securitygroup_ids is required. Default \
                            securitygroup_ids are not registered.")
                    raise exception.InvalidInput(reason=msg)

            if not glance_image_id and ppid:
                glance_image_id = parent_process.get("glance_image_id")

            if not nova_flavor_id and ppid:
                nova_flavor_id = parent_process.get("nova_flavor_id")

            if userdata:
                try:
                    base64.b64decode(userdata)
                except TypeError:
                    msg = _("userdadta must be a base64 encoded value.")
                    raise exception.InvalidInput(reason=msg)

            networks = db.network_get_all(context, gid)
            if not networks:
                msg = _("Netwoks does not exist in the group %s" % gid)
                raise webob.exc.HTTPBadRequest(explanation=msg)

            if floating_networks is None:
                floating_networks = []
            elif floating_networks is not None and\
                    not isinstance(floating_networks, list):
                msg = _("floating_networks must be a list")
                raise exception.InvalidInput(reason=msg)

            network_ids =\
                [network["network_id"] for network in networks]

            for floating_net_id in floating_networks:
                if floating_net_id not in network_ids:
                    msg = _("floating_networks do not exist in the group %s"\
                            % gid)
                    raise webob.exc.HTTPBadRequest(explanation=msg)

                for network in networks:
                    if floating_net_id == network["network_id"] and\
                            not network["ext_router"]:
                        msg = _("floating_networks must be connected to a "
                                "router that connects to an external network")
                        raise webob.exc.HTTPBadRequest(explanation=msg)
                    else:
                        network["is_floating"] = True

            if args is None:
                args = {}
            elif args is not None and\
                    not isinstance(args, dict):
                msg = _("args must be a dict.")
                raise exception.InvalidInput(reason=msg)
            else:
                for key in args.keys():
                    args[key] = str(args[key])

            default_args = {
                "gid": gid,
                "pid": pid,
            }
            if ppid:
                default_args["ppid"] = ppid

            if is_proxy:
                default_args["rackapi_ip"] = cfg.CONF.my_ip
                default_args["os_username"] = cfg.CONF.os_username
                default_args["os_password"] = cfg.CONF.os_password
                default_args["os_tenant_name"] = cfg.CONF.os_tenant_name
                default_args["os_auth_url"] = cfg.CONF.os_auth_url
                default_args["os_region_name"] = cfg.CONF.os_region_name
            else:
                proxy_instance_id = proxy[0]["nova_instance_id"]
                default_args["proxy_ip"] = self.manager.get_process_address(
                    context, proxy_instance_id)
            args.update(default_args)

            valid_values = {}
            valid_values["gid"] = gid
            valid_values["ppid"] = ppid
            valid_values["pid"] = pid
            valid_values["display_name"] = name
            valid_values["keypair_id"] = keypair_id
            valid_values["securitygroup_ids"] = securitygroup_ids
            valid_values["glance_image_id"] = glance_image_id
            valid_values["nova_flavor_id"] = nova_flavor_id
            valid_values["userdata"] = userdata
            valid_values["args"] = json.dumps(args)
            valid_values["is_proxy"] = True if is_proxy else False
            valid_values["network_ids"] = network_ids

            if is_proxy:
                ipc_endpoint = values.get("ipc_endpoint")
                shm_endpoint = values.get("shm_endpoint")
                fs_endpoint = values.get("fs_endpoint")
                if ipc_endpoint:
                    utils.check_string_length(
                        ipc_endpoint, 'ipc_endpoint', min_length=1,
                        max_length=255)
                if shm_endpoint:
                    utils.check_string_length(
                        shm_endpoint, 'shm_endpoint', min_length=1,
                        max_length=255)
                if fs_endpoint:
                    utils.check_string_length(
                        fs_endpoint, 'fs_endpoint', min_length=1,
                        max_length=255)
                valid_values["ipc_endpoint"] = ipc_endpoint
                valid_values["shm_endpoint"] = shm_endpoint
                valid_values["fs_endpoint"] = fs_endpoint

            boot_values = {}
            boot_values["name"] = name
            boot_values["key_name"] = nova_keypair_id
            boot_values["security_groups"] = neutron_securitygroup_ids
            boot_values["image"] = glance_image_id
            boot_values["flavor"] = nova_flavor_id
            boot_values["userdata"] = userdata
            boot_values["meta"] = args
            boot_values["networks"] = networks

            return valid_values, boot_values

        try:
            context = req.environ['rack.context']
            values, boot_values = _validate(context, body, gid, is_proxy)
            nova_instance_id, status = self.manager.process_create(
                context, **boot_values)
            values["nova_instance_id"] = nova_instance_id
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            process = db.process_create(context, values,
                                        values.pop("network_ids"),
                                        values.pop("securitygroup_ids"))
            process["status"] = status
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.create(process)

    @wsgi.response(202)
    def create_proxy(self, req, body, gid):
        return self.create(req, body, gid, is_proxy=True)

    @wsgi.response(200)
    def update(self, req, body, gid, pid):

        def _validate(body, gid, pid):
            self._uuid_check(gid, pid)

            if not self.is_valid_body(body, 'process'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["process"]
            app_status = values.get("app_status")

            if not app_status:
                msg = _("app_status is required")
                raise exception.InvalidInput(reason=msg)

            valid_values = {"app_status": app_status}

            return valid_values

        try:
            values = _validate(body, gid, pid)
            context = req.environ['rack.context']
            process = db.process_update(context, gid, pid, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.ProcessNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.update(process)

    @wsgi.response(200)
    def update_proxy(self, req, body, gid):

        def _validate(context, body, gid):
            self._uuid_check(gid)
            process = db.process_get_all(
                context, gid, filters={"is_proxy": True})
            if not process:
                msg = _("Proxy process does not exist in the group %s" % gid)
                raise exception.InvalidInput(reason=msg)

            if not self.is_valid_body(body, 'proxy'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["proxy"]
            app_status = values.get("app_status")
            ipc_endpoint = values.get("ipc_endpoint")
            shm_endpoint = values.get("shm_endpoint")
            fs_endpoint = values.get("fs_endpoint")

            valid_values = {}
            if app_status:
                utils.check_string_length(
                    app_status, 'app_status', min_length=1, max_length=255)
                valid_values["app_status"] = app_status
            if ipc_endpoint:
                utils.check_string_length(
                    ipc_endpoint, 'ipc_endpoint', min_length=1, max_length=255)
                valid_values["ipc_endpoint"] = ipc_endpoint
            if shm_endpoint:
                utils.check_string_length(
                    shm_endpoint, 'shm_endpoint', min_length=1, max_length=255)
                valid_values["shm_endpoint"] = shm_endpoint
            if fs_endpoint:
                utils.check_string_length(
                    fs_endpoint, 'fs_endpoint', min_length=1, max_length=255)
                valid_values["fs_endpoint"] = fs_endpoint

            if not valid_values:
                msg = _("No keyword is provided.")
                raise exception.InvalidInput(reason=msg)

            return process[0]["pid"], valid_values

        try:
            context = req.environ['rack.context']
            pid, values = _validate(context, body, gid)
            process = db.process_update(context, gid, pid, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.ProcessNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.update(process)

    @wsgi.response(204)
    def delete(self, req, gid, pid):

        def _delete_children(context, gid, pid):
            processes = db.process_get_all(context, gid, {"ppid": pid})
            for process in processes:
                _delete_children(context, gid, process["pid"])
                _delete(context, gid, process["pid"],
                        process["nova_instance_id"])
            return

        def _delete(context, gid, pid, nova_id):
            self.manager.process_delete(context, nova_id)
            try:
                db.process_delete(context, gid, pid)
            except exception.NotFound as e:
                LOG.exception(e)

        self._uuid_check(gid, pid)
        context = req.environ['rack.context']
        try:
            process = db.process_get_by_pid(context, gid, pid)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        _delete_children(context, gid, pid)
        _delete(context, gid, pid, process["nova_instance_id"])


def create_resource():
    return wsgi.Resource(Controller())
