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

from oslo.config import cfg
import six

from rack import context
from rack import db
from rack.openstack.common.gettextutils import _
from rack.openstack.common import log as logging
from rack.openstack.common import timeutils
from rack.servicegroup import api


CONF = cfg.CONF
CONF.import_opt('service_down_time', 'rack.service')

LOG = logging.getLogger(__name__)


class DbDriver(api.ServiceGroupDriver):

    def __init__(self, *args, **kwargs):
        self.db_allowed = kwargs.get('db_allowed', True)
        self.service_down_time = CONF.service_down_time

    def join(self, member_id, group_id, service=None):
        """Join the given service with it's group."""

        msg = _('DB_Driver: join new ServiceGroup member %(member_id)s to '
                    'the %(group_id)s group, service = %(service)s')
        LOG.debug(msg, {'member_id': member_id, 'group_id': group_id,
                        'service': service})
        if service is None:
            raise RuntimeError(_('service is a mandatory argument for DB based'
                                 ' ServiceGroup driver'))
        report_interval = service.report_interval
        if report_interval:
            service.tg.add_timer(report_interval, self._report_state,
                                 api.INITIAL_REPORTING_DELAY, service)

    def is_up(self, service_ref):
        """Moved from rack.utils
        Check whether a service is up based on last heartbeat.
        """
        last_heartbeat = service_ref['updated_at'] or service_ref['created_at']
        if isinstance(last_heartbeat, six.string_types):
            last_heartbeat = timeutils.parse_strtime(last_heartbeat)
        else:
            last_heartbeat = last_heartbeat.replace(tzinfo=None)
        elapsed = timeutils.delta_seconds(last_heartbeat, timeutils.utcnow())
        is_up = abs(elapsed) <= self.service_down_time
        if not is_up:
            msg = _('Seems service is down. Last heartbeat was %(lhb)s. '
                    'Elapsed time is %(el)s')
            LOG.debug(msg, {'lhb': str(last_heartbeat), 'el': str(elapsed)})
        return is_up

    def get_all(self, group_id):
        """Returns ALL members of the given group
        """
        LOG.debug(_('DB_Driver: get_all members of the %s group') % group_id)
        rs = []
        ctxt = context.get_admin_context()
        services = db.service_get_all_by_topic(ctxt, group_id)
        for service in services:
            if self.is_up(service):
                rs.append(service['host'])
        return rs

    def _report_state(self, service):
        """Update the state of this service in the datastore."""
        ctxt = context.get_admin_context()
        state_catalog = {}
        try:
            report_count = service.service_ref['report_count'] + 1
            state_catalog['report_count'] = report_count

            service.service_ref = db.service_update(ctxt,
                    service.service_ref['id'], state_catalog)

            if getattr(service, 'model_disconnected', False):
                service.model_disconnected = False
                LOG.error(_('Recovered model server connection!'))

        except Exception:
            if not getattr(service, 'model_disconnected', False):
                service.model_disconnected = True
                LOG.exception(_('model server went away'))
