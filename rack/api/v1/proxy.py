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
import base64
import json
import re
import six
import uuid
import webob

from oslo.config import cfg

from rack.api.v1.views import proxy as view_proxy
from rack.api import wsgi

from rack import db
from rack import exception
from rack import utils

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import uuidutils
from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi

LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """proxy controller for RACK API."""

    _view_builder_class = view_proxy.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.scheduler_rpcapi = scheduler_rpcapi.SchedulerAPI()
        self.operator_rpcapi = operator_rpcapi.ResourceOperatorAPI()

    @wsgi.response(200)
    def show(self, req, gid):

        def _validate(gid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

        try:
            _validate(gid)
            context = req.environ['rack.context']
            proxy = db.process_get_all(
                context, gid, {"is_proxy": True, "status": "ACTIVE"})
            if len(proxy) == 0:
                msg = _("Proxy instance not exists in this group")
                raise exception.ProxyNotFound(msg)

        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show(proxy[0])

    @wsgi.response(202)
    def create(self, req, body, gid):

        def _validate_proxy(context, gid, body):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            proxy = db.process_get_not_error_status_for_proxy(context, gid)
            if len(proxy) > 0:
                msg = _("Proxy instance already exists in this group")
                raise exception.ProxyCreateFailed(msg)

            if not self.is_valid_body(body, 'proxy'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["proxy"]
            keypair_id = values.get("keypair_id")
            name = values.get("name")
            glance_image_id = values.get("glance_image_id")
            nova_flavor_id = values.get("nova_flavor_id")
            securitygroup_ids = values.get("securitygroup_ids")
            userdata = values.get("userdata")

            if keypair_id is not None:
                if not uuidutils.is_uuid_like(keypair_id):
                    raise exception.KeypairNotFound(keypair_id=keypair_id)

            if isinstance(name, six.string_types):
                name = name.strip()
                utils.check_string_length(name, 'name', min_length=1,
                                          max_length=255)
            elif name is not None:
                msg = _("name must be a String")
                raise exception.InvalidInput(reason=msg)

            if not uuidutils.is_uuid_like(glance_image_id):
                msg = _("glance_image_id is invalid format")
                raise exception.InvalidInput(reason=msg)

            utils.validate_integer(nova_flavor_id, 'nova_flavor_id')

            if not securitygroup_ids:
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
            valid_values_proxy = {}
            valid_values_proxy["gid"] = gid
            valid_values_proxy["keypair_id"] = keypair_id
            valid_values_proxy["display_name"] = name
            valid_values_proxy["glance_image_id"] = glance_image_id
            valid_values_proxy["nova_flavor_id"] = nova_flavor_id
            valid_values_proxy["is_proxy"] = True
            valid_values_proxy["app_status"] = "BUILDING"

            valid_values_userdata = {}
            valid_values_userdata["userdata"] = userdata

            valid_values_securitygroup = {}
            valid_values_securitygroup["securitygroup_ids"] = securitygroup_ids

            valid_values["proxy"] = valid_values_proxy
            valid_values["userdata"] = valid_values_userdata
            valid_values["securitygroup"] = valid_values_securitygroup

            return valid_values

        def _validate_metadata(args):
            if args is None:
                return dict(roles="ipc/shm/api/proxy")
            else:
                if not isinstance(args, dict):
                    msg = _("args must be a dict")
                    raise exception.InvalidInput(reason=msg)

                if args.get("roles"):
                    args["roles"] = args.get("roles") + "/proxy"
                else:
                    args["roles"] = "ipc/shm/api/proxy"

            return args

        def _get_proxy_conf():
            conf = {}
            expr = "(127.0.0.1|localhost)"
            conf.update(dict(rabbit_userid=cfg.CONF.rabbit_userid))
            conf.update(dict(rabbit_password=cfg.CONF.rabbit_password))
            conf.update(
                dict(rabbit_host=re.sub(expr, cfg.CONF.my_ip,
                                        cfg.CONF.rabbit_host)))
            conf.update(
                dict(sql_connection=re.sub(expr, cfg.CONF.my_ip,
                                           cfg.CONF.sql_connection)))
            return conf

        try:
            context = req.environ['rack.context']
            valid_values = _validate_proxy(context, gid, body)
            values = valid_values.get("proxy")
            securitygroup_ids = valid_values.get(
                "securitygroup").get("securitygroup_ids")
            userdata = valid_values.get("userdata")
            args = _validate_metadata(body["proxy"].get("args"))
            metadata = dict(args)
            metadata.update(_get_proxy_conf())

            values["deleted"] = 0
            values["status"] = "BUILDING"
            values["pid"] = unicode(uuid.uuid4())
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            values["display_name"] = values[
                "display_name"] or "pro-" + values["pid"]
            values["userdata"] = userdata.get("userdata")
            values["args"] = json.dumps(args)

            if values["keypair_id"]:
                nova_keypair_id = db.keypair_get_by_keypair_id(
                    context, gid, values["keypair_id"]).get("nova_keypair_id")
            else:
                nova_keypair_id = None
            networks = db.network_get_all(context, gid, {"status": "ACTIVE"})
            if not networks:
                raise exception.NoNetworksFound(gid=values["gid"])
            network_ids = [network["network_id"] for network in networks]
            proxy = db.process_create(
                context, values, network_ids, securitygroup_ids)

        except exception.ProxyCreateFailed as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        try:
            host = self.scheduler_rpcapi.select_destinations(
                context,
                request_spec={},
                filter_properties={})
            self.operator_rpcapi.process_create(
                context,
                host["host"],
                pid=values["pid"],
                ppid="",
                gid=gid,
                name=values["display_name"],
                glance_image_id=values["glance_image_id"],
                nova_flavor_id=values["nova_flavor_id"],
                nova_keypair_id=nova_keypair_id,
                neutron_securitygroup_ids=[securitygroup[
                    "neutron_securitygroup_id"]
                    for securitygroup in proxy["securitygroups"]],
                neutron_network_ids=[network["neutron_network_id"]
                                     for network in proxy["networks"]],
                metadata=metadata,
                userdata=userdata.get("userdata"))
        except Exception as e:
            LOG.exception(e)
            pid = values["pid"]
            db.process_update(context, gid, pid, {"status": "ERROR"})
            raise exception.ProcessCreateFailed()

        return self._view_builder.create(proxy)

    @wsgi.response(200)
    def update(self, req, body, gid):

        def _validate(body, gid):
            if not uuidutils.is_uuid_like(gid):

                raise exception.GroupNotFound(gid=gid)

            if not self.is_valid_body(body, 'proxy'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            proxy = db.process_get_all(
                context, gid, {"is_proxy": True, "status": "ACTIVE"})
            if len(proxy) == 0:
                msg = _("Proxy instance not exists in this group")
                raise exception.ProxyNotFound(msg)

            values = body["proxy"]
            app_status = values.get("app_status")
            if not app_status:
                msg = _("app_status is required")
                raise exception.InvalidInput(reason=msg)

            valid_values = {}
            if values.get("shm_endpoint"):
                valid_values["shm_endpoint"] = values.get("shm_endpoint")
            if values.get("ipc_endpoint"):
                valid_values["ipc_endpoint"] = values.get("ipc_endpoint")
            if values.get("fs_endpoint"):
                valid_values["fs_endpoint"] = values.get("fs_endpoint")
            valid_values["app_status"] = app_status
            valid_values["pid"] = proxy[0]["pid"]
            valid_values

            return valid_values

        context = req.environ['rack.context']

        try:
            values = _validate(body, gid)
            proxy = db.process_update(context, gid, values["pid"], values)

        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        except exception.ProxyNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.update(proxy)


def create_resource():
    return wsgi.Resource(Controller())
