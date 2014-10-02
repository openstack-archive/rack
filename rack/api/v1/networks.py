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

from rack import db
from rack import exception

from rack.api.v1.views import networks as views_networks
from rack.api import wsgi

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import strutils
from rack.openstack.common import uuidutils

from rack.resourceoperator import manager

import uuid
import webob


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Network controller for RACK API."""

    _view_builder_class = views_networks.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.manager = manager.ResourceOperator()

    def _uuid_check(self, gid=None, network_id=None):
        if gid:
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)
        if network_id:
            if not uuidutils.is_uuid_like(network_id):
                raise exception.NetworkNotFound(network_id=network_id)

    @wsgi.response(200)
    def index(self, req, gid):
        try:
            self._uuid_check(gid)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        context = req.environ['rack.context']
        network_list = db.network_get_all(context, gid)
        network_list = self.manager.network_list(context, network_list)

        return self._view_builder.index(network_list)

    @wsgi.response(200)
    def show(self, req, gid, network_id):
        context = req.environ['rack.context']
        try:
            self._uuid_check(gid, network_id)
            network = db.network_get_by_network_id(context, gid, network_id)
            self.manager.network_show(context, network)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show(network)

    @wsgi.response(201)
    def create(self, req, gid, body):

        def _validate(context, body, gid):
            self._uuid_check(gid)
            if not self.is_valid_body(body, "network"):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body.get("network")

            cidr = values.get("cidr")
            name = values.get("name")

            is_admin = values.get("is_admin")
            if is_admin:
                try:
                    is_admin = strutils.bool_from_string(
                        is_admin, strict=True)
                except ValueError:
                    msg = _("is_admin must be a boolean")
                    raise exception.InvalidInput(reason=msg)
            else:
                is_admin = False

            gateway = values.get("gateway")
            ext_router = values.get("ext_router_id")
            dns_nameservers = values.get("dns_nameservers")
            if dns_nameservers is not None and not isinstance(
                    dns_nameservers, list):
                msg = _("dns_nameservers must be a list")
                raise exception.InvalidInput(reason=msg)

            valid_values = {}
            valid_values["gid"] = gid
            valid_values["network_id"] = unicode(uuid.uuid4())
            if not name:
                name = "network-" + valid_values["network_id"]
            valid_values["display_name"] = name
            valid_values["cidr"] = cidr
            valid_values["is_admin"] = is_admin
            valid_values["gateway"] = gateway
            valid_values["ext_router"] = ext_router
            valid_values["dns_nameservers"] = dns_nameservers

            network_values = {}
            network_values["name"] = name
            network_values["cidr"] = cidr
            network_values["gateway"] = gateway
            network_values["ext_router"] = ext_router
            network_values["dns_nameservers"] = dns_nameservers

            return valid_values, network_values

        try:
            context = req.environ['rack.context']
            values, network_values = _validate(context, body, gid)
            db.group_get_by_gid(context, gid)
            result_value = self.manager.network_create(
                context, **network_values)
            values.update(result_value)
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            network = db.network_create(context, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.create(network)

    @wsgi.response(204)
    def delete(self, req, gid, network_id):
        try:
            self._uuid_check(gid, network_id)
            context = req.environ['rack.context']
            network = db.network_get_by_network_id(context, gid, network_id)
            if network["processes"]:
                raise exception.NetworkInUse(network_id=network_id)

            self.manager.network_delete(context, network["neutron_network_id"],
                                        network["ext_router"])
            db.network_delete(context, gid, network_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.NetworkInUse as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())


def create_resource():
    return wsgi.Resource(Controller())
