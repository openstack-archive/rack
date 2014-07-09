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
    """Model a networks API response as a python dictionary."""

    def index(self, network_list):
        return dict(networks=[
            self._base_response(network) for network in network_list])

    def show(self, network):
        base = self._base_response(network)
        return dict(network=base)

    def create(self, network):
        base = self._base_response(network)
        return dict(network=base)

    def _base_response(self, network):
        return {
            "network_id": network["network_id"],
            "neutron_network_id": network["neutron_network_id"],
            "gid": network["gid"],
            "user_id": network["user_id"],
            "project_id": network["project_id"],
            "name": network["display_name"],
            "is_admin": network["is_admin"],
            "cidr": network["subnet"],
            "ext_router_id": network["ext_router"],
            "status": network["status"]
        }
