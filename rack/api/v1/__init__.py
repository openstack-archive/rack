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
"""
WSGI middleware for RACK API controllers.
"""

from oslo.config import cfg
import routes

from rack.api.v1 import groups
from rack.api.v1 import keypairs
from rack.api.v1 import networks
from rack.api.v1 import processes
from rack.api.v1 import securitygroups
from rack.api import versions
from rack.openstack.common import log as logging
from rack import wsgi as base_wsgi


openstack_client_opts = [
    cfg.StrOpt('sql_connection',
               help='Valid sql_connection for Rack'),
]

CONF = cfg.CONF
CONF.register_opts(openstack_client_opts)

LOG = logging.getLogger(__name__)


class APIMapper(routes.Mapper):

    def routematch(self, url=None, environ=None):
        if url == "":
            result = self._match("", environ)
            return result[0], result[1]
        return routes.Mapper.routematch(self, url, environ)

    def connect(self, *args, **kargs):
        # NOTE(vish): Default the format part of a route to only accept json
        #             and xml so it doesn't eat all characters after a '.'
        #             in the url.
        kargs.setdefault('requirements', {})
        if not kargs['requirements'].get('format'):
            kargs['requirements']['format'] = 'json|xml'
        return routes.Mapper.connect(self, *args, **kargs)


class APIRouter(base_wsgi.Router):

    """Routes requests on the RACK API to the appropriate controller
    and method.
    """
    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`rack.wsgi.Router` doesn't have one."""
        return cls()

    def __init__(self):
        mapper = APIMapper()
        self._setup_routes(mapper)
        super(APIRouter, self).__init__(mapper)

    def _setup_routes(self, mapper):
        versions_resource = versions.create_resource()
        mapper.connect("/",
                       controller=versions_resource,
                       action="show",
                       conditions={'method': ['GET']})

        mapper.redirect("", "/")

        groups_resource = groups.create_resource()
        mapper.connect("/groups",
                       controller=groups_resource,
                       action="index",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}",
                       controller=groups_resource,
                       action="show",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups",
                       controller=groups_resource,
                       action="create",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}",
                       controller=groups_resource,
                       action="update",
                       conditions={"method": ["PUT"]})
        mapper.connect("/groups/{gid}",
                       controller=groups_resource,
                       action="delete",
                       conditions={"method": ["DELETE"]})

        networks_resource = networks.create_resource()
        mapper.connect("/groups/{gid}/networks",
                       controller=networks_resource,
                       action="index",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/networks/{network_id}",
                       controller=networks_resource,
                       action="show",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/networks",
                       controller=networks_resource,
                       action="create",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}/networks/{network_id}",
                       controller=networks_resource,
                       action="update",
                       conditions={"method": ["PUT"]})
        mapper.connect("/groups/{gid}/networks/{network_id}",
                       controller=networks_resource,
                       action="delete",
                       conditions={"method": ["DELETE"]})

        keypairs_resource = keypairs.create_resource()
        mapper.connect("/groups/{gid}/keypairs",
                       controller=keypairs_resource,
                       action="index",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/keypairs/{keypair_id}",
                       controller=keypairs_resource,
                       action="show",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/keypairs",
                       controller=keypairs_resource,
                       action="create",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}/keypairs/{keypair_id}",
                       controller=keypairs_resource,
                       action="update",
                       conditions={"method": ["PUT"]})
        mapper.connect("/groups/{gid}/keypairs/{keypair_id}",
                       controller=keypairs_resource,
                       action="delete",
                       conditions={"method": ["DELETE"]})

        securitygroups_resource = securitygroups.create_resource()
        mapper.connect("/groups/{gid}/securitygroups",
                       controller=securitygroups_resource,
                       action="index",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/securitygroups/{securitygroup_id}",
                       controller=securitygroups_resource,
                       action="show",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/securitygroups",
                       controller=securitygroups_resource,
                       action="create",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}/securitygroups/{securitygroup_id}",
                       controller=securitygroups_resource,
                       action="update",
                       conditions={"method": ["PUT"]})
        mapper.connect("/groups/{gid}/securitygroups/{securitygroup_id}",
                       controller=securitygroups_resource,
                       action="delete",
                       conditions={"method": ["DELETE"]})

        processes_resource = processes.create_resource()
        mapper.connect("/groups/{gid}/processes",
                       controller=processes_resource,
                       action="index",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/processes/{pid}",
                       controller=processes_resource,
                       action="show",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/processes",
                       controller=processes_resource,
                       action="create",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}/processes/{pid}",
                       controller=processes_resource,
                       action="update",
                       conditions={"method": ["PUT"]})
        mapper.connect("/groups/{gid}/processes/{pid}",
                       controller=processes_resource,
                       action="delete",
                       conditions={"method": ["DELETE"]})

        # RACK proxy resources
        mapper.connect("/groups/{gid}/proxy",
                       controller=processes_resource,
                       action="show_proxy",
                       conditions={"method": ["GET"]})
        mapper.connect("/groups/{gid}/proxy",
                       controller=processes_resource,
                       action="create_proxy",
                       conditions={"method": ["POST"]})
        mapper.connect("/groups/{gid}/proxy",
                       controller=processes_resource,
                       action="update_proxy",
                       conditions={"method": ["PUT"]})
