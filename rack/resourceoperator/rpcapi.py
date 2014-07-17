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
Client side of the scheduler manager RPC API.
"""

from oslo.config import cfg
from oslo import messaging

from rack import object as rack_object
from rack import rpc

rpcapi_opts = [
    cfg.StrOpt('resourceoperator_topic',
               default='resourceoperator',
               help='The topic resouceoperator nodes listen on'),
]

CONF = cfg.CONF
CONF.register_opts(rpcapi_opts)

rpcapi_cap_opt = cfg.StrOpt('resourceoperator',
                            help='Set a version cap for messages sent to resourceoperator services')
CONF.register_opt(rpcapi_cap_opt, 'upgrade_levels')


class ResourceOperatorAPI(object):

    '''Client side of the resource_operator rpc API.

    API version history:

        1.0 - Initial version.
    '''

    VERSION_ALIASES = {
        'juno': '1.0',
    }

    def __init__(self):
        super(ResourceOperatorAPI, self).__init__()
        target = messaging.Target(topic=CONF.resourceoperator_topic, version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.resourceoperator,
                                               CONF.upgrade_levels.resourceoperator)
        serializer = rack_object.RackObjectSerializer()
        self.client = rpc.get_client(target, version_cap=version_cap,
                                     serializer=serializer)

    def keypair_create(self, ctxt, host, gid, keypair_id, name):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "keypair_create", gid=gid,
                   keypair_id=keypair_id, name=name)

    def keypair_delete(self, ctxt, host, nova_keypair_id):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "keypair_delete",
                   nova_keypair_id=nova_keypair_id)

    def network_create(self, ctxt, host, network):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, 'network_create', network=network)

    def network_delete(self, ctxt, host, neutron_network_id, ext_router):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, 'network_delete',
                   neutron_network_id=neutron_network_id,
                   ext_router=ext_router)

    def securitygroup_create(self, ctxt, host, gid, securitygroup_id, name, securitygrouprules):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "securitygroup_create",
                   gid=gid,
                   securitygroup_id=securitygroup_id, 
                   name=name,
                   securitygrouprules=securitygrouprules)

    def securitygroup_delete(self, ctxt, host, neutron_securitygroup_id):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "securitygroup_delete",
                   neutron_securitygroup_id=neutron_securitygroup_id)

    def process_create(self, ctxt, host, pid, ppid, gid, name, 
                       glance_image_id, nova_flavor_id, 
                       nova_keypair_id, neutron_securitygroup_ids, 
                       neutron_network_ids, metadata, userdata):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "process_create",
                   pid=pid, ppid=ppid, gid=gid, name=name, 
                   glance_image_id=glance_image_id, nova_flavor_id=nova_flavor_id, 
                   nova_keypair_id=nova_keypair_id, neutron_securitygroup_ids=neutron_securitygroup_ids, 
                   neutron_network_ids=neutron_network_ids, metadata=metadata, userdata=userdata)

    def process_delete(self, ctxt, host, nova_instance_id):
        cctxt = self.client.prepare(server=host)
        cctxt.cast(ctxt, "process_delete", nova_instance_id=nova_instance_id)
