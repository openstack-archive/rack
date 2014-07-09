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
    """Model a group API response as a python dictionary."""

    def index(self, group_list):
        return dict(groups=
                [self._base_response(group)
                 for group in group_list])

    def show(self, group):
        base = self._base_response(group)
        return dict(group=base)

    def create(self, group):
        base = self._base_response(group)
        return dict(group=base)

    def update(self, group):
        base = self._base_response(group)
        return dict(group=base)

    def _base_response(self, group):
        return {
            "gid": group["gid"],
            "user_id": group["user_id"],
            "project_id": group["project_id"],
            "name": group["display_name"],
            "description": group["display_description"],
            "status": group["status"]
        }

