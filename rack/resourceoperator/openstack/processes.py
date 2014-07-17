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
from rack import exception
from rack.openstack.common import log as logging
from rack.resourceoperator import openstack as os_client
import time


LOG = logging.getLogger(__name__)


class ProcessesAPI(object):

    def process_create(self,
                       display_name,
                       glance_image_id,
                       nova_flavor_id,
                       nova_keypair_id,
                       neutron_securitygroup_ids,
                       neutron_network_ids,
                       metadata,
                       userdata
                       ):
        try:
            nova = os_client.get_nova_client()
            nics = []
            for network_id in neutron_network_ids:
                nics.append({"net-id": network_id})
            process = nova.servers.create(
                name=display_name,
                image=glance_image_id,
                flavor=nova_flavor_id,
                meta=metadata,
                nics=nics,
                key_name=nova_keypair_id,
                security_groups=neutron_securitygroup_ids,
                userdata=userdata
            )

            while process.status != "ACTIVE":
                if process.status == "ERROR":
                    raise Exception()
                time.sleep(5)
                process = nova.servers.get(process.id)

            return process.id
        except Exception as e:
            LOG.exception(e)
            raise exception.ProcessCreateFailed()

    def process_delete(self, nova_instance_id):
        try:
            nova = os_client.get_nova_client()
            nova.servers.delete(nova_instance_id)
        except Exception as e:
            LOG.exception(e)
            raise exception.ProcessDeleteFailed()
