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

    """Model a securitygroup API response as a python dictionary."""

    def index(self, securitygroup_list):
        return dict(securitygroups=[self._base_response(securitygroup)
                                    for securitygroup in securitygroup_list])

    def show(self, securitygroup):
        base = self._base_response(securitygroup)
        return dict(securitygroup=base)

    def create(self, securitygroup):
        base = self._base_response(securitygroup)
        base.pop('status')
        return dict(securitygroup=base)

    def update(self, securitygroup):
        base = self._base_response(securitygroup)
        base.pop("status")
        return dict(securitygroup=base)

    def _base_response(self, securitygroup):
        return {
            "securitygroup_id": securitygroup.get("securitygroup_id"),
            "neutron_securitygroup_id": securitygroup
            .get("neutron_securitygroup_id"),
            "user_id": securitygroup.get("user_id"),
            "project_id": securitygroup.get("project_id"),
            "gid": securitygroup.get("gid"),
            "name": securitygroup.get("display_name"),
            "is_default": securitygroup.get("is_default"),
            "status": securitygroup.get("status")
        }
