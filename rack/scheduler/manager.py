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
Scheduler Service
"""

from oslo.config import cfg
from oslo import messaging

from rack.resourceoperator import rpcapi
from rack import exception
from rack import manager
from rack.openstack.common import importutils
from rack.openstack.common import jsonutils
from rack.openstack.common import log as logging


LOG = logging.getLogger(__name__)

scheduler_driver_opts = [
    cfg.StrOpt('scheduler_driver',
               default='rack.scheduler.chance.ChanceScheduler',
               help='Default driver to use for the scheduler'),
    cfg.IntOpt('scheduler_driver_task_period',
               default=60,
               help='How often (in seconds) to run periodic tasks in '
                    'the scheduler driver of your choice. '
                    'Please note this is likely to interact with the value '
                    'of service_down_time, but exactly how they interact '
                    'will depend on your choice of scheduler driver.'),
]
CONF = cfg.CONF
CONF.register_opts(scheduler_driver_opts)


class SchedulerManager(manager.Manager):

    target = messaging.Target(version='1.0')

    def __init__(self, scheduler_driver=None, *args, **kwargs):
        if not scheduler_driver:
            scheduler_driver = CONF.scheduler_driver
        self.driver = importutils.import_object(scheduler_driver)
        self.resourceoperator_rpcapi = rpcapi.ResourceOperatorAPI()
        super(SchedulerManager, self).__init__(service_name='scheduler',
                                               *args, **kwargs)

    @messaging.expected_exceptions(exception.NoValidHost)
    def select_destinations(self, context, request_spec, filter_properties):
        """Returns destinations(s) best suited for this request_spec and
        filter_properties.

        The result should be a list of dicts with 'host', 'nodename' and
        'limits' as keys.
        """
        dests = self.driver.select_destinations(context, request_spec,
            filter_properties)
        return jsonutils.to_primitive(dests)
