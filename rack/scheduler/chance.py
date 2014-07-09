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
Chance (Random) Scheduler implementation
"""

import random

from oslo.config import cfg

from rack import exception
from rack.openstack.common.gettextutils import _
from rack.scheduler import driver

CONF = cfg.CONF
CONF.import_opt('resourceoperator_topic', 'rack.resourceoperator.rpcapi')


class ChanceScheduler(driver.Scheduler):
    """Implements Scheduler as a random node selector."""

    def __init__(self, *args, **kwargs):
        super(ChanceScheduler, self).__init__(*args, **kwargs)

    def _filter_hosts(self, request_spec, hosts, filter_properties):
        """Filter a list of hosts based on request_spec."""

        ignore_hosts = filter_properties.get('ignore_hosts', [])
        hosts = [host for host in hosts if host not in ignore_hosts]
        return hosts

    def _schedule(self, context, topic, request_spec, filter_properties):
        """Picks a host that is up at random."""

        elevated = context.elevated()
        hosts = self.hosts_up(elevated, topic)
        if not hosts:
            msg = _("Is the appropriate service running?")
            raise exception.NoValidHost(reason=msg)

        hosts = self._filter_hosts(request_spec, hosts, filter_properties)
        if not hosts:
            msg = _("Could not find another resourceoperator")
            raise exception.NoValidHost(reason=msg)

        return random.choice(hosts)

    def select_destinations(self, context, request_spec, filter_properties):
        """Selects random destinations."""
        host = self._schedule(context, CONF.resourceoperator_topic,
                    request_spec, filter_properties)
        host_state = dict(host=host, nodename=None, limits=None)

        return host_state
