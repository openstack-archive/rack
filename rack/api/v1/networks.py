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
from rack import db, utils
from rack import exception
from rack.api import wsgi
from rack.api.v1.views import networks as views_networks
from rack.openstack.common import log as logging, uuidutils, strutils
from rack.openstack.common.gettextutils import _
from rack.resourceoperator import rpcapi as ro_rpcapi
from rack.scheduler import rpcapi as sch_rpcapi
import uuid

import webob


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Network controller for RACK API."""

    _view_builder_class = views_networks.ViewBuilder

    def __init__(self):
        self.scheduler_rpcapi = sch_rpcapi.SchedulerAPI()
        self.resourceoperator_rpcapi = ro_rpcapi.ResourceOperatorAPI()
        super(Controller, self).__init__()

    @wsgi.response(202)
    def create(self, req, gid, body):

        def _validate(context, body, gid):
            # validation checks
            if not self.is_valid_body(body, "network"):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body.get("network")

            # Required item
            subnet = values.get("cidr")
            if subnet is None:
                msg = _("Ntwork cidr is required")
                raise exception.InvalidInput(reason=msg)
            if not utils.is_valid_cidr(subnet):
                msg = _("cidr must be a CIDR")
                raise exception.InvalidInput(reason=msg)

            # Non-essential items
            network_id = unicode(uuid.uuid4())
            name = values.get("name")
            if name is None or not name:
                name = "net-" + network_id
            else:
                name = name.strip()
                utils.check_string_length(name, 'name', min_length=1,max_length=255)

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
            if gateway is not None and not utils.is_valid_ip_address(gateway):
                msg = _("Invalid gateway")
                raise exception.InvalidInput(reason=msg)

            dns_nameservers = values.get("dns_nameservers")
            if dns_nameservers is not None:
                if isinstance(dns_nameservers, list):
                    for dns in dns_nameservers:
                        if dns == "" or not utils.is_valid_ip_address(dns):
                            msg = _("Invalid dns_nameservers")
                            raise exception.InvalidInput(reason=msg)
                else:
                    msg = _("dns_nameservers must be list format")
                    raise exception.InvalidInput(reason=msg)

            ext_router = values.get("ext_router_id")
            if ext_router is not None and not uuidutils.is_uuid_like(ext_router):
                msg = _("ext_router must be a uuid")
                raise exception.InvalidInput(reason=msg)

            valid_values1 = {}
            valid_values1["network_id"] = network_id
            valid_values1["gid"] = gid
            valid_values1["neutron_network_id"] = None
            valid_values1["is_admin"] = is_admin
            valid_values1["subnet"] = subnet
            valid_values1["ext_router"] = ext_router
            valid_values1["user_id"] = context.user_id
            valid_values1["project_id"] = context.project_id
            valid_values1["display_name"] = name
            valid_values1["status"] = "BUILDING"
            valid_values1["deleted"] = 0

            valid_values2 = {}
            valid_values2["gateway"] = gateway
            valid_values2["dns_nameservers"] = dns_nameservers

            valid_values = {}
            valid_values["db"] = valid_values1
            valid_values["opst"] = valid_values2

            return valid_values

        try:
            context = req.environ['rack.context']
            values = _validate(context, body, gid)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        try:
            # db access
            self._check_gid(gid, is_create=True, context=context)
            network = db.network_create(context, values["db"])
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except Exception as e:
            LOG.exception(e)
            raise exception.NetworkCreateFailed()

        try:
            # scheduler access
            resourceoperator = self._get_resorceoperator(context)
            # resource operator access
            for k, v in values["opst"].items():
                if v is not None: 
                    network[k] = v
            self.resourceoperator_rpcapi.network_create(context, resourceoperator["host"], network)
        except Exception as e:
            LOG.exception(e)
            error_values = {"status": "ERROR"}
            db.network_update(context, network["network_id"], error_values)
            raise exception.NetworkCreateFailed()

        return self._view_builder.create(network)

    @wsgi.response(200)
    def index(self, req, gid):
        def _validate(gid):
            self._check_gid(gid)

        try:
            context = req.environ['rack.context']
            _validate(gid)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        filters = {}
        network_id = req.params.get('network_id')
        neutron_network_id = req.params.get('neutron_network_id')
        name = req.params.get('name')
        status = req.params.get('status')
        is_admin = req.params.get('is_admin')
        subnet = req.params.get('subnet')
        ext_router = req.params.get('ext_router')


        if network_id:
            filters['network_id'] = network_id
        if neutron_network_id:
            filters['neutron_network_id'] = neutron_network_id
        if name:
            filters['name'] = name
        if status:
            filters['status'] = status
        if is_admin:
            filters['is_admin'] = is_admin
        if subnet:
            filters['subnet'] = subnet
        if ext_router:
            filters['ext_router'] = ext_router


        network_list = db.network_get_all(context, gid)

        return self._view_builder.index(network_list)

    @wsgi.response(200)
    def show(self, req, gid, network_id):
        def _validate(gid, network_id):
            self._check_gid(gid)
            if not uuidutils.is_uuid_like(network_id):
                raise exception.NetworkNotFound(network_id=network_id)

        try:
            context = req.environ['rack.context']
            _validate(gid, network_id)
            network = db.network_get_by_network_id(context, gid, network_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show(network)

    @wsgi.response(204)
    def delete(self, req, gid, network_id):
        def _validate(gid, network_id):
            self._check_gid(gid)
            if not uuidutils.is_uuid_like(network_id):
                raise exception.NetworkNotFound(network_id=network_id)

        try:
            context = req.environ['rack.context']
            _validate(gid, network_id)
            network = db.network_get_by_network_id(context, gid, network_id)
            if network["processes"]:
                raise exception.NetworkInUse(network_id=network_id)
            network = db.network_delete(context, gid, network_id)
            resourceoperator = self._get_resorceoperator(context)
            self.resourceoperator_rpcapi.network_delete(
                context, resourceoperator["host"],
                neutron_network_id=network["neutron_network_id"],
                ext_router=network["ext_router"])
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.NetworkInUse as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())
        except Exception as e:
            LOG.exception(e)
            raise exception.NetworkDeleteFailed()

    def _check_gid(self, gid, is_create=False, context=None):
        if not uuidutils.is_uuid_like(gid):
            raise exception.GroupNotFound(gid=gid)
        if is_create:
            db.group_get_by_gid(context, gid)

    def _get_resorceoperator(self, context,
                             request_spec={}, filter_properties={}):
        resorceoperator = self.scheduler_rpcapi.select_destinations(context, request_spec, filter_properties)
        return resorceoperator


def create_resource():
    return wsgi.Resource(Controller())
