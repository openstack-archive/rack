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

import netaddr
import six
import uuid
import webob

from rack.api.v1.views import securitygroups as views_securitygroups
from rack.api import wsgi
from rack import db
from rack import exception

from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import strutils
from rack.openstack.common import uuidutils
from rack import utils

from rack.resourceoperator import rpcapi as operator_rpcapi
from rack.scheduler import rpcapi as scheduler_rpcapi


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Securitygroup controller for RACK API."""

    _view_builder_class = views_securitygroups.ViewBuilder

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
        except exception.SecuritygroupNotFound:
            msg = _("Securitygroup could not be found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        filters = {}
        securitygroup_id = req.params.get('securitygroup_id')
        name = req.params.get('name')
        status = req.params.get('status')
        is_default = req.params.get('is_default')

        if securitygroup_id:
            filters['securitygroup_id'] = securitygroup_id
        if name:
            filters['name'] = name
        if status:
            filters['status'] = status
        if is_default:
            filters['is_default'] = is_default

        context = req.environ['rack.context']
        securitygroup_list = db.securitygroup_get_all(context, gid, filters)

        return self._view_builder.index(securitygroup_list)

    @wsgi.response(200)
    def show(self, req, gid, securitygroup_id):

        def _validate(gid, securitygroup_id):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(securitygroup_id):
                raise exception.SecuritygroupNotFound(
                    securitygroup_id=securitygroup_id)

        try:
            _validate(gid, securitygroup_id)
            context = req.environ['rack.context']
            securitygroup = db.securitygroup_get_by_securitygroup_id(
                context, gid, securitygroup_id)
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        return self._view_builder.show(securitygroup)

    @wsgi.response(202)
    def create(self, req, body, gid):

        def _validate_securitygroup(gid, body):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not self.is_valid_body(body, 'securitygroup'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["securitygroup"]
            name = values.get("name")
            is_default = values.get("is_default")

            if isinstance(name, six.string_types):
                name = name.strip()
                utils.check_string_length(name, 'name', min_length=1,
                                          max_length=255)

            if is_default:
                try:
                    is_default = strutils.bool_from_string(
                        is_default, strict=True)
                except ValueError:
                    msg = _("is_default must be a boolean")
                    raise exception.InvalidInput(reason=msg)
            else:
                is_default = False

            valid_values = {}
            valid_values["gid"] = gid
            valid_values["display_name"] = name
            valid_values["is_default"] = is_default
            return valid_values

        def _validate_securitygrouprules(securitygrouprules):

            valid_securitygrouprules = []
            for securitygroup in securitygrouprules:
                protocol = securitygroup.get("protocol")
                port_range_max = securitygroup.get("port_range_max")
                port_range_min = securitygroup.get("port_range_min")
                remote_securitygroup_id = securitygroup.get(
                    "remote_securitygroup_id")
                remote_ip_prefix = securitygroup.get("remote_ip_prefix")

                if not protocol:
                    msg = _("SecurityGroupRule protocol is required")
                    raise exception.InvalidInput(reason=msg)
                elif not utils.is_valid_protocol(protocol):
                    msg = _(
                        "SecurityGroupRule protocol should be tcp or udp or "
                        "icmp")
                    raise exception.InvalidInput(reason=msg)

                if not remote_securitygroup_id and not remote_ip_prefix:
                    msg = _(
                        "SecurityGroupRule either remote_securitygroup_id or "
                        "remote_ip_prefix is required")
                    raise exception.InvalidInput(reason=msg)
                elif remote_securitygroup_id and remote_ip_prefix:
                    msg = _(
                        "SecurityGroupRule either remote_securitygroup_id or "
                        "remote_ip_prefix is required")
                    raise exception.InvalidInput(reason=msg)
                elif remote_securitygroup_id is not None:
                    if not uuidutils.is_uuid_like(remote_securitygroup_id):
                        raise exception.SecuritygroupNotFound(
                            securitygroup_id=remote_securitygroup_id)
                elif remote_ip_prefix is not None:
                    if not utils.is_valid_cidr(remote_ip_prefix):
                        msg = _(
                            "SecurityGroupRule remote_ip_prefix should be "
                            "cidr format")
                        raise exception.InvalidInput(reason=msg)

                if protocol in ["tcp", "udp"]:
                    if port_range_max is None:
                        msg = _("SecurityGroupRule port_range_max is "
                                "required")
                        raise exception.InvalidInput(reason=msg)
                    utils.validate_integer(
                        port_range_max, 'port_range_max', min_value=1,
                        max_value=65535)
                    if port_range_min:
                        utils.validate_integer(
                            port_range_min, 'port_range_min', min_value=1,
                            max_value=65535)
                        if port_range_min > port_range_max:
                            msg = _(
                                "SecurityGroupRule port_range_min should be "
                                "lower than port_range_max")
                            raise exception.InvalidInput(reason=msg)
                elif protocol == "icmp":
                    port_range_max = None
                    port_range_min = None

                valid_securitygrouprules.append({
                    "protocol": protocol,
                    "port_range_max": port_range_max,
                    "port_range_min": port_range_min,
                    "remote_securitygroup_id": remote_securitygroup_id,
                    "remote_ip_prefix": unicode(netaddr
                                                .IPNetwork(remote_ip_prefix))
                    if remote_ip_prefix else remote_ip_prefix
                })
            return valid_securitygrouprules

        try:
            context = req.environ['rack.context']
            values = _validate_securitygroup(gid, body)
            if(body["securitygroup"].get("securitygrouprules")):
                securitygrouprules = _validate_securitygrouprules(
                    body["securitygroup"].get("securitygrouprules"))
            else:
                securitygrouprules = []
        except exception.InvalidInput as exc:
            raise webob.exc.HTTPBadRequest(explanation=exc.format_message())
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        values["deleted"] = 0
        values["status"] = "BUILDING"
        values["securitygroup_id"] = unicode(uuid.uuid4())
        values["user_id"] = context.user_id
        values["project_id"] = context.project_id
        values["display_name"] = values[
            "display_name"] or "sec-" + values["securitygroup_id"]

        try:
            for i in range(len(securitygrouprules)):
                if securitygrouprules[i]["remote_securitygroup_id"]:
                    securitygroup = db\
                        .securitygroup_get_by_securitygroup_id(
                            context, gid,
                            securitygrouprules[i]["remote_securitygroup_id"])
                    remote_neutron_securitygroup_id = securitygroup.get(
                        "neutron_securitygroup_id")
                    securitygrouprules[i][
                        "remote_neutron_securitygroup_id"] =\
                        remote_neutron_securitygroup_id
            db.group_get_by_gid(context, gid)
            securitygroup = db.securitygroup_create(context, values)
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        try:
            host = self.scheduler_rpcapi.select_destinations(
                context,
                request_spec={},
                filter_properties={})
            self.operator_rpcapi.securitygroup_create(
                context,
                host["host"],
                gid=gid,
                securitygroup_id=values["securitygroup_id"],
                name=values["display_name"],
                securitygrouprules=securitygrouprules)
        except Exception:
            securitygroup_id = values["securitygroup_id"]
            db.securitygroup_update(
                context, gid, securitygroup_id, {"status": "ERROR"})
            raise exception.SecuritygroupCreateFailed()

        return self._view_builder.create(securitygroup)

    @wsgi.response(200)
    def update(self, req, body, gid, securitygroup_id):

        def _validate(body, gid, securitygroup_id):
            if not self.is_valid_body(body, 'securitygroup'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["securitygroup"]
            is_default = values.get("is_default")

            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(securitygroup_id):
                raise exception.SecuritygroupNotFound(
                    securitygroup_id=securitygroup_id)

            if is_default:
                try:
                    is_default = strutils.bool_from_string(
                        is_default, strict=True)
                except ValueError:
                    msg = _("is_default must be a boolean")
                    raise exception.InvalidInput(reason=msg)
            else:
                msg = _("SecurityGroup is_default is required")
                raise exception.InvalidInput(reason=msg)

            valid_values = {}
            valid_values["is_default"] = is_default
            return valid_values

        try:
            values = _validate(body, gid, securitygroup_id)
            context = req.environ['rack.context']
            securitygroup = db.securitygroup_update(
                context, gid, securitygroup_id, values)
        except exception.InvalidInput as exc:
            raise webob.exc.HTTPBadRequest(explanation=exc.format_message())
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        return self._view_builder.update(securitygroup)

    @wsgi.response(204)
    def delete(self, req, gid, securitygroup_id):

        def _validate(gid, securitygroup_id):

            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if not uuidutils.is_uuid_like(securitygroup_id):
                raise exception.SecuritygroupNotFound(
                    securitygroup_id=securitygroup_id)

        try:
            _validate(gid, securitygroup_id)
            context = req.environ['rack.context']
            securitygroup = db.securitygroup_get_by_securitygroup_id(
                context, gid, securitygroup_id)
            if securitygroup["processes"]:
                raise exception.SecuritygroupInUse(
                    securitygroup_id=securitygroup_id)
            securitygroup = db.securitygroup_delete(
                context, gid, securitygroup_id)
        except exception.SecuritygroupInUse as exc:
            raise webob.exc.HTTPConflict(explanation=exc.format_message())
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        try:
            host = self.scheduler_rpcapi.select_destinations(
                context,
                request_spec={},
                filter_properties={})
            self.operator_rpcapi.securitygroup_delete(
                context,
                host["host"],
                neutron_securitygroup_id=securitygroup["neutron_securitygroup"
                                                       "_id"])
        except Exception:
            raise exception.SecuritygroupDeleteFailed()


def create_resource():
    return wsgi.Resource(Controller())
