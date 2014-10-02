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
from rack.openstack.common import log as logging
from rack.resourceoperator import openstack as os_client

LOG = logging.getLogger(__name__)


class KeypairAPI(object):

    def __init__(self):
        super(KeypairAPI, self).__init__()

    def keypair_list(self):
        nova = os_client.get_nova_client()
        keypairs = nova.keypairs.list()
        nova_keypair_ids = []
        for keypair in keypairs:
            nova_keypair_ids.append(keypair.id)
        return nova_keypair_ids

    def keypair_show(self, nova_keypair_id):
        nova = os_client.get_nova_client()
        return nova.keypairs.get(nova_keypair_id)

    def keypair_create(self, name):
        nova = os_client.get_nova_client()
        keypair = nova.keypairs.create(name)
        values = {}
        values["nova_keypair_id"] = keypair.name
        values["private_key"] = keypair.private_key
        return values

    def keypair_delete(self, nova_keypair_id):
        nova = os_client.get_nova_client()
        nova.keypairs.delete(nova_keypair_id)
