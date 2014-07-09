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
Scheduler base class that all Schedulers should inherit from
"""

from oslo.config import cfg

from rack import db
from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack import servicegroup

LOG = logging.getLogger(__name__)

scheduler_driver_opts = [
    # TODO: If we use intelligent scheduler driver like filter_scheduler, use this.
    #cfg.StrOpt('scheduler_host_manager',
    #           default='rack.scheduler.host_manager.HostManager',
    #           help='The scheduler host manager class to use'),
    cfg.IntOpt('scheduler_max_attempts',
               default=3,
               help='Maximum number of attempts to schedule an instance'),
    ]

CONF = cfg.CONF
CONF.register_opts(scheduler_driver_opts)


class Scheduler(object):
    """The base class that all Scheduler classes should inherit from."""

    def __init__(self):
        # TODO: If we use intelligent scheduler driver like filter_scheduler, use this.
        #self.host_manager = importutils.import_object(
        #        CONF.scheduler_host_manager)
        self.servicegroup_api = servicegroup.API()

    def run_periodic_tasks(self, context):
        """Manager calls this so drivers can perform periodic tasks."""
        pass

    def hosts_up(self, context, topic):
        """Return the list of hosts that have a running service for topic."""

        services = db.service_get_all_by_topic(context, topic)
        return [service['host']
                for service in services
                if self.servicegroup_api.service_is_up(service)]

    def select_destinations(self, context, request_spec, filter_properties):
        """Must override select_destinations method.

        :return: A list of dicts with 'host', 'nodename' and 'limits' as keys
            that satisfies the request_spec and filter_properties.
        """
        msg = _("Driver must implement select_destinations")
        raise NotImplementedError(msg)
