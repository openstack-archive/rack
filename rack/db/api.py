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
from rack.openstack.common.db import api as db_api


CONF = cfg.CONF
db_opts = [
    cfg.BoolOpt('enable_new_services',
                default=True,
                help='Services to be added to the available pool on create')
]
CONF.register_opts(db_opts)
CONF.import_opt('backend', 'rack.openstack.common.db.options',
                group='database')

_BACKEND_MAPPING = {'sqlalchemy': 'rack.db.sqlalchemy.api'}


IMPL = db_api.DBAPI(CONF.database.backend, backend_mapping=_BACKEND_MAPPING)


def group_get_all(context, filters=None):
    return IMPL.group_get_all(context, filters)


def group_get_by_gid(context, gid):
    return IMPL.group_get_by_gid(context, gid)


def group_create(context, values):
    return IMPL.group_create(context, values)


def group_update(context, values):
    return IMPL.group_update(context, values)

def group_delete(context, gid):
    return IMPL.group_delete(context, gid)


def service_destroy(context, service_id):
    """Destroy the service or raise if it does not exist."""
    return IMPL.service_destroy(context, service_id)


def service_get(context, service_id):
    """Get a service or raise if it does not exist."""
    return IMPL.service_get(context, service_id)


def service_get_by_host_and_topic(context, host, topic):
    """Get a service by host it's on and topic it listens to."""
    return IMPL.service_get_by_host_and_topic(context, host, topic)


def service_get_all(context, disabled=None):
    """Get all services."""
    return IMPL.service_get_all(context, disabled)


def service_get_all_by_topic(context, topic):
    """Get all services for a given topic."""
    return IMPL.service_get_all_by_topic(context, topic)


def service_get_all_by_host(context, host):
    """Get all services for a given host."""
    return IMPL.service_get_all_by_host(context, host)


def service_get_by_args(context, host, binary):
    """Get the state of a service by node name and binary."""
    return IMPL.service_get_by_args(context, host, binary)


def service_create(context, values):
    """Create a service from the values dictionary."""
    return IMPL.service_create(context, values)


def service_update(context, service_id, values):
    """Set the given properties on a service and update it.

    Raises NotFound if service does not exist.

    """
    return IMPL.service_update(context, service_id, values)


def network_create(context, values):
    return IMPL.network_create(context, values)


def network_update(context, network_id, values):
    IMPL.network_update(context, network_id, values)


def network_get_all(context, gid, filters={}):
    return IMPL.network_get_all(context, gid, filters)


def network_get_by_network_id(context, gid, network_id):
    return IMPL.network_get_by_network_id(context, gid, network_id)


def network_delete(context, gid, network_id):
    return IMPL.network_delete(context, gid, network_id)


def keypair_get_all(context, gid, filters={}):
    return IMPL.keypair_get_all(context, gid, filters)


def keypair_get_by_keypair_id(context, gid, keypair_id):
    return IMPL.keypair_get_by_keypair_id(context, gid, keypair_id)


def keypair_create(context, values):
    return IMPL.keypair_create(context, values)


def keypair_update(context, gid, keypair_id, values):
    return IMPL.keypair_update(context, gid, keypair_id, values)


def keypair_delete(context, gid, keypair_id):
    return IMPL.keypair_delete(context, gid, keypair_id)


def securitygroup_get_all(context, gid, filters={}):
    return IMPL.securitygroup_get_all(context, gid, filters)


def securitygroup_get_by_securitygroup_id(context, gid, securitygroup_id):
    return IMPL.securitygroup_get_by_securitygroup_id(context, gid, securitygroup_id)


def securitygroup_create(context, values):
    return IMPL.securitygroup_create(context, values)


def securitygroup_update(context, gid, securitygroup_id, values):
    return IMPL.securitygroup_update(context, gid, securitygroup_id, values)


def securitygroup_delete(context, gid, securitygroup_id):
    return IMPL.securitygroup_delete(context, gid, securitygroup_id)


def process_get_all(context, gid, filters={}):
    return IMPL.process_get_all(context, gid, filters)


def process_get_by_pid(context, gid, pid):
    return IMPL.process_get_by_pid(context, gid, pid)


def process_get_not_error_status_for_proxy(context, gid):
    return IMPL.process_get_not_error_status_for_proxy(context, gid)


def process_create(context, values, network_ids, securitygroup_ids):
    return IMPL.process_create(context, values, network_ids, securitygroup_ids)


def process_update(context, gid, pid, values):
    return IMPL.process_update(context, gid, pid, values)


def process_delete(context, gid, pid):
    return IMPL.process_delete(context, gid, pid)
