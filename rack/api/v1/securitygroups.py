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
from rack.resourceoperator import manager


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Securitygroup controller for RACK API."""

    _view_builder_class = views_securitygroups.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.manager = manager.ResourceOperator()

    def _uuid_check(self, gid=None, securitygroup_id=None):
        if gid:
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)
        if securitygroup_id:
            if not uuidutils.is_uuid_like(securitygroup_id):
                raise exception.SecuritygroupNotFound(
                    securitygroup_id=securitygroup_id)

    @wsgi.response(200)
    def index(self, req, gid):
        try:
            self._uuid_check(gid)
        except exception.SecuritygroupNotFound:
            msg = _("Securitygroup could not be found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        context = req.environ['rack.context']
        securitygroup_list = db.securitygroup_get_all(context, gid)
        securitygroup_list = self.manager.securitygroup_list(
            context, securitygroup_list)

        return self._view_builder.index(securitygroup_list)

    @wsgi.response(200)
    def show(self, req, gid, securitygroup_id):
        try:
            self._uuid_check(gid, securitygroup_id)
            context = req.environ['rack.context']
            securitygroup = db.securitygroup_get_by_securitygroup_id(
                context, gid, securitygroup_id)
            securitygroup = self.manager.securitygroup_show(
                context, securitygroup)
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())

        return self._view_builder.show(securitygroup)

    @wsgi.response(201)
    def create(self, req, body, gid):

        def _validate(context, body, gid):
            if not self.is_valid_body(body, 'securitygroup'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            self._uuid_check(gid)
            db.group_get_by_gid(context, gid)
            values = body["securitygroup"]
            name = values.get("name")
            is_default = values.get("is_default")

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

            rules = values.get("securitygrouprules")
            valid_rules = []
            if rules is not None:
                if not isinstance(rules, list):
                    msg = _("securitygrouprules must be a list")
                    raise exception.InvalidInput(reason=msg)

                for rule in rules:
                    valid_rule = {}
                    valid_rule["protocol"] = rule.get("protocol")
                    valid_rule["port_range_max"] = rule.get("port_range_max")
                    valid_rule["port_range_min"] = rule.get("port_range_min")
                    valid_rule["remote_ip_prefix"] = rule.get(
                        "remote_ip_prefix")
                    remote_securitygroup_id = rule.get(
                        "remote_securitygroup_id")
                    if remote_securitygroup_id:
                        ref = db.securitygroup_get_by_securitygroup_id(
                            context, gid,
                            remote_securitygroup_id)
                        valid_rule['remote_neutron_securitygroup_id'] =\
                            ref['neutron_securitygroup_id']
                    valid_rules.append(valid_rule)

            return valid_values, valid_rules

        try:
            context = req.environ['rack.context']
            values, rules = _validate(context, body, gid)
            values["securitygroup_id"] = unicode(uuid.uuid4())
            if not values["display_name"]:
                values["display_name"] = "securitygroup-" + \
                    values["securitygroup_id"]
            result_value = self.manager.securitygroup_create(
                context, values["display_name"], rules)
            values.update(result_value)
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            securitygroup = db.securitygroup_create(context, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.GroupNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.create(securitygroup)

    @wsgi.response(200)
    def update(self, req, body, gid, securitygroup_id):

        def _validate(body, gid, securitygroup_id):
            if not self.is_valid_body(body, 'securitygroup'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            self._uuid_check(gid, securitygroup_id)
            values = body["securitygroup"]
            is_default = values.get("is_default")
            if is_default is not None:
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
        try:
            self._uuid_check(gid, securitygroup_id)
            context = req.environ['rack.context']
            securitygroup = db.securitygroup_get_by_securitygroup_id(
                context, gid, securitygroup_id)
            if securitygroup["processes"]:
                raise exception.SecuritygroupInUse(
                    securitygroup_id=securitygroup_id)
            self.manager.securitygroup_delete(
                context, securitygroup['neutron_securitygroup_id'])
            db.securitygroup_delete(context, gid, securitygroup_id)
        except exception.SecuritygroupInUse as exc:
            raise webob.exc.HTTPConflict(explanation=exc.format_message())
        except exception.NotFound as exc:
            raise webob.exc.HTTPNotFound(explanation=exc.format_message())


def create_resource():
    return wsgi.Resource(Controller())
