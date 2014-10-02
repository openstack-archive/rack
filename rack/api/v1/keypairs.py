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

from rack.api.v1.views import keypairs as views_keypairs
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

    """Keypair controller for RACK API."""

    _view_builder_class = views_keypairs.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()
        self.manager = manager.ResourceOperator()

    def _uuid_check(self, gid=None, keypair_id=None):
        if gid:
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)
        if keypair_id:
            if not uuidutils.is_uuid_like(keypair_id):
                raise exception.KeypairNotFound(keypair_id=keypair_id)

    @wsgi.response(200)
    def index(self, req, gid):
        try:
            self._uuid_check(gid=gid)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        context = req.environ['rack.context']
        keypair_list = db.keypair_get_all(context, gid)
        keypair_list = self.manager.keypair_list(context, keypair_list)
        return self._view_builder.index(keypair_list)

    @wsgi.response(200)
    def show(self, req, gid, keypair_id):
        try:
            self._uuid_check(gid=gid, keypair_id=keypair_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        context = req.environ['rack.context']
        try:
            keypair = db.keypair_get_by_keypair_id(context, gid, keypair_id)
            self.manager.keypair_show(context, keypair)
        except exception.KeypairNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.show(keypair)

    @wsgi.response(201)
    def create(self, req, body, gid):

        def _validate(context, body, gid):
            if not self.is_valid_body(body, 'keypair'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            self._uuid_check(gid)
            values = body["keypair"]
            name = values.get("name")
            is_default = values.get("is_default")

            if is_default:
                try:
                    is_default = strutils.bool_from_string(
                        is_default, strict=True)
                    keypairs = db.keypair_get_all(context, gid,
                                                  filters={"is_default": True})
                    if keypairs:
                        msg = _("Default keypair already exists in the "
                                "group %s" % gid)
                        raise exception.InvalidInput(reason=msg)
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

        try:
            context = req.environ['rack.context']
            values = _validate(context, body, gid)
            db.group_get_by_gid(context, gid)
            values["keypair_id"] = unicode(uuid.uuid4())
            if not values["display_name"]:
                values["display_name"] = "keypair-" + values["keypair_id"]
            result_value = self.manager.keypair_create(
                context, values["display_name"])
            values.update(result_value)
            values["user_id"] = context.user_id
            values["project_id"] = context.project_id
            keypair = db.keypair_create(context, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.GroupNotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.create(keypair)

    @wsgi.response(200)
    def update(self, req, body, gid, keypair_id):

        def _validate(body, gid, keypair_id):
            if not self.is_valid_body(body, 'keypair'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            self._uuid_check(gid, keypair_id)
            values = body["keypair"]
            is_default = values.get("is_default")

            if is_default is not None:
                try:
                    is_default = strutils.bool_from_string(
                        is_default, strict=True)
                except ValueError:
                    msg = _("is_default must be a boolean")
                    raise exception.InvalidInput(reason=msg)
            else:
                msg = _("is_default is required")
                raise exception.InvalidInput(reason=msg)

            valid_values = {"is_default": is_default}
            return valid_values

        context = req.environ['rack.context']

        try:
            values = _validate(body, gid, keypair_id)
            keypair = db.keypair_update(context, gid, keypair_id, values)
        except exception.InvalidInput as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        return self._view_builder.update(keypair)

    @wsgi.response(204)
    def delete(self, req, gid, keypair_id):
        context = req.environ['rack.context']

        try:
            self._uuid_check(gid=gid, keypair_id=keypair_id)
            filters = {"keypair_id": keypair_id}
            processes = db.process_get_all(context, gid, filters=filters)
            if processes:
                raise exception.keypairInUse(keypair_id=keypair_id)

            keypair = db.keypair_get_by_keypair_id(context, gid, keypair_id)
            self.manager.keypair_delete(context, keypair["nova_keypair_id"])
            db.keypair_delete(context, gid, keypair_id)
        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())
        except exception.keypairInUse as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())


def create_resource():
    return wsgi.Resource(Controller())
