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

import six
import webob

from rack.api.v1.views import groups as views_groups
from rack.api import wsgi
from rack import db
from rack import exception
from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import uuidutils
from rack import utils


LOG = logging.getLogger(__name__)


class Controller(wsgi.Controller):

    """Group controller for RACK API."""

    _view_builder_class = views_groups.ViewBuilder

    def __init__(self):
        super(Controller, self).__init__()

    @wsgi.response(200)
    def index(self, req):
        filters = {}
        project_id = req.params.get('project_id')
        name = req.params.get('name')
        status = req.params.get('status')

        if project_id:
            filters['project_id'] = project_id
        if name:
            filters['display_name'] = name
        if status:
            filters['status'] = status

        context = req.environ['rack.context']
        group_list = db.group_get_all(context, filters)

        return self._view_builder.index(group_list)

    @wsgi.response(200)
    def show(self, req, gid):

        def _validate(gid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

        try:
            _validate(gid)
            context = req.environ['rack.context']
            group = db.group_get_by_gid(context, gid)
        except exception.NotFound:
            msg = _("Group could not be found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        return self._view_builder.show(group)

    @wsgi.response(201)
    def create(self, req, body):

        def _validate(body):
            if not self.is_valid_body(body, 'group'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["group"]
            name = values.get("name")
            description = values.get("description")

            if not name:
                msg = _("Group name is required")
                raise exception.InvalidInput(reason=msg)

            if isinstance(name, six.string_types):
                name = name.strip()
            utils.check_string_length(name, 'name', min_length=1,
                                      max_length=255)

            if description:
                utils.check_string_length(description, 'description',
                                          min_length=0, max_length=255)

            valid_values = {}
            valid_values["display_name"] = name
            valid_values["display_description"] = description
            return valid_values

        try:
            values = _validate(body)
        except exception.InvalidInput as exc:
            raise webob.exc.HTTPBadRequest(explanation=exc.format_message())

        context = req.environ['rack.context']
        values["gid"] = unicode(uuid.uuid4())
        values["user_id"] = context.user_id
        values["project_id"] = context.project_id
        values["status"] = "ACTIVE"
        group = db.group_create(context, values)

        return self._view_builder.create(group)

    @wsgi.response(200)
    def update(self, req, body, gid):

        def _validate(body, gid):
            if not self.is_valid_body(body, 'group'):
                msg = _("Invalid request body")
                raise exception.InvalidInput(reason=msg)

            values = body["group"]
            name = values.get("name")
            description = values.get("description")

            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)

            if name is None and description is None:
                msg = _("Group name or description is required")
                raise exception.InvalidInput(reason=msg)

            if name is not None:
                if isinstance(name, six.string_types):
                    name = name.strip()
                utils.check_string_length(name, 'name', min_length=1,
                                          max_length=255)

            if description is not None:
                utils.check_string_length(description, 'description',
                                          min_length=0, max_length=255)

            valid_values = {}
            if name:
                valid_values["display_name"] = name
            # allow blank string to clear description
            if description is not None:
                valid_values["display_description"] = description
            valid_values["gid"] = gid
            return valid_values

        context = req.environ['rack.context']

        try:
            values = _validate(body, gid)
            group = db.group_update(context, values)
        except exception.InvalidInput as exc:
            raise webob.exc.HTTPBadRequest(explanation=exc.format_message())
        except exception.GroupNotFound:
            msg = _("Group could not be found")
            raise webob.exc.HTTPNotFound(explanation=msg)

        return self._view_builder.update(group)

    @wsgi.response(204)
    def delete(self, req, gid):

        def _validate(gid):
            if not uuidutils.is_uuid_like(gid):
                raise exception.GroupNotFound(gid=gid)
        try:
            _validate(gid)

            context = req.environ['rack.context']

            keypairs = db.keypair_get_all(context, gid)
            if keypairs:
                raise exception.GroupInUse(gid=gid)

            securitygroups = db.securitygroup_get_all(context, gid)
            if securitygroups:
                raise exception.GroupInUse(gid=gid)

            networks = db.network_get_all(context, gid)
            if networks:
                raise exception.GroupInUse(gid=gid)

            processes = db.process_get_all(context, gid)
            if processes:
                raise exception.GroupInUse(gid=gid)

            db.group_delete(context, gid)

        except exception.NotFound as e:
            raise webob.exc.HTTPNotFound(explanation=e.format_message())

        except exception.GroupInUse as e:
            raise webob.exc.HTTPConflict(explanation=e.format_message())

        except Exception as e:
            LOG.warning(e)
            raise exception.GroupDeleteFailed()


def create_resource():
    return wsgi.Resource(Controller())
