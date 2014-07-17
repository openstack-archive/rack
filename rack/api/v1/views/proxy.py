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
from rack.api import common
from rack.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class ViewBuilder(common.ViewBuilder):

    """Model a proxy API response as a python dictionary."""
    def show(self, proxy):
        return dict(proxy=self._base_response(proxy))

    def create(self, proxy):
        base = self._base_response(proxy)
        base.update(
            {"network_ids": [network.get("network_id") 
                                  for network in proxy.get("networks")],
            "securitygroup_ids": [securitygroup.get("securitygroup_id") 
                                  for securitygroup in proxy.get("securitygroups")]
              })

        return dict(proxy=base)

    def update(self, proxy):
        return dict(proxy=self._base_response(proxy))

    def _base_response(self, proxy):
        return {
            "gid": proxy.get("gid"),
            "pid": proxy.get("pid"),
            "ppid": proxy.get("ppid", ""),
            "user_id": proxy.get("user_id"),
            "project_id": proxy.get("project_id"),
            "name": proxy.get("display_name"),
            "glance_image_id": proxy.get("glance_image_id"),
            "nova_flavor_id": proxy.get("nova_flavor_id"),
            "status": proxy.get("status"),
            "keypair_id": proxy.get("keypair_id"),
            "shm_endpoint": proxy.get("shm_endpoint"),
            "ipc_endpoint": proxy.get("ipc_endpoint"),
            "fs_endpoint": proxy.get("fs_endpoint"),
            "app_status": proxy.get("app_status"),
            "userdata": proxy.get("userdata"),
            "args": proxy.get("args")
         }
