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

    """Model a keypair API response as a python dictionary."""

    def index(self, keypair_list):
        return dict(keypairs=[self._base_response(keypair)
                              for keypair in keypair_list])

    def show(self, keypair):
        base = self._base_response(keypair)
        return dict(keypair=base)

    def create(self, keypair):
        base = self._base_response(keypair)
        base.pop('status')
        return dict(keypair=base)

    def update(self, keypair):
        base = self._base_response(keypair)
        base.pop("status")
        return dict(keypair=base)

    def _base_response(self, keypair):
        return {
            "keypair_id": keypair.get("keypair_id"),
            "nova_keypair_id": keypair.get("nova_keypair_id"),
            "user_id": keypair.get("user_id"),
            "project_id": keypair.get("project_id"),
            "gid": keypair.get("gid"),
            "name": keypair.get("display_name"),
            "private_key": keypair.get("private_key"),
            "is_default": keypair.get("is_default"),
            "status": keypair.get("status")
        }
