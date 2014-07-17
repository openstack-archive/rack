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
    cfg.StrOpt('scheduler_topic',
               default='scheduler',
               help='The topic scheduler nodes listen on'),
]

CONF = cfg.CONF
CONF.register_opts(rpcapi_opts)

rpcapi_cap_opt = cfg.StrOpt('scheduler',
                            help='Set a version cap for messages sent to '
                            'scheduler services')
CONF.register_opt(rpcapi_cap_opt, 'upgrade_levels')


class SchedulerAPI(object):

    '''Client side of the scheduler rpc API.

    API version history:

        1.0 - Initial version.
    '''

    VERSION_ALIASES = {
        'juno': '1.0',
    }

    def __init__(self):
        super(SchedulerAPI, self).__init__()
        target = messaging.Target(topic=CONF.scheduler_topic, version='1.0')
        version_cap = self.VERSION_ALIASES.get(CONF.upgrade_levels.scheduler,
                                               CONF.upgrade_levels.scheduler)
        serializer = rack_object.RackObjectSerializer()
        self.client = rpc.get_client(target, version_cap=version_cap,
                                     serializer=serializer)

    def select_destinations(self, ctxt, request_spec, filter_properties):
        cctxt = self.client.prepare()
        return cctxt.call(ctxt, 'select_destinations',
                          request_spec=request_spec,
                          filter_properties=filter_properties)
