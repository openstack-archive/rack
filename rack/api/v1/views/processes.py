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
from rack.api import common
from rack.openstack.common import log as logging

LOG = logging.getLogger(__name__)


class ViewBuilder(common.ViewBuilder):

    """Model a process API response as a python dictionary."""

    def index(self, process_list):
        return dict(processes=[self._base_response(process)
                               for process in process_list])

    def show(self, process):
        base = self._base_response(process)
        return dict(process=base)

    def show_proxy(self, process):
        base = self._base_response(process)
        return dict(proxy=base)

    def create(self, process):
        base = self._base_response(process)
        if process.get("is_proxy"):
            return dict(proxy=base)
        else:
            return dict(process=base)

    def update(self, process):
        base = self._base_response(process)
        base.pop("status")
        if process.get("is_proxy"):
            return dict(proxy=base)
        else:
            return dict(process=base)

    def _base_response(self, process):
        base = {
            "gid": process.get("gid"),
            "pid": process.get("pid"),
            "ppid": process.get("ppid"),
            "user_id": process.get("user_id"),
            "project_id": process.get("project_id"),
            "name": process.get("display_name"),
            "nova_instance_id": process.get("nova_instance_id"),
            "glance_image_id": process.get("glance_image_id"),
            "nova_flavor_id": process.get("nova_flavor_id"),
            "status": process.get("status"),
            "keypair_id": process.get("keypair_id"),
            "app_status": process.get("app_status"),
            "userdata": process.get("userdata"),
            "args": json.loads(process.get("args")),
            "networks": [{"network_id": network.get("network_id"),
                          "fixed": network.get("fixed"),
                          "floating": network.get("floating")}
                         for network in process.get("networks")],
            "securitygroup_ids": [securitygroup.get("securitygroup_id")
                                  for securitygroup in process
                                  .get("securitygroups")],
        }
        if process.get("is_proxy"):
            proxy_body = {
                "ipc_endpoint": process.get("ipc_endpoint"),
                "shm_endpoint": process.get("shm_endpoint"),
                "fs_endpoint": process.get("fs_endpoint")
            }
            base.update(proxy_body)
        return base
