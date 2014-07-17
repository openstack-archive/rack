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

from rack.db.sqlalchemy import models
from rack import exception

from rack.openstack.common import jsonutils
from rack.openstack.common import log as logging
from rack.openstack.common import timeutils

from rack.openstack.common.db import exception as db_exc
from rack.openstack.common.db.sqlalchemy import session as db_session
from rack.openstack.common.gettextutils import _

import functools
import rack.context
import sys

LOG = logging.getLogger(__name__)

CONF = cfg.CONF
CONF.import_opt('connection',
                'rack.openstack.common.db.options',
                group='database')

_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade(
            CONF.database.connection,
            **dict(CONF.database.iteritems()))
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    return sys.modules[__name__]


def group_get_all(context, filters=None):
    session = get_session()
    filters = filters or {}
    query = session.query(models.Group).filter_by(user_id=context.user_id)\
        .filter_by(deleted=0)
    if 'project_id' in filters:
        query = query.filter_by(project_id=filters['project_id'])
    if 'name' in filters:
        query = query.filter_by(display_name=filters['name'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    responce_groups = query.all()

    return [dict(group) for group in responce_groups]


def group_get_by_gid(context, gid):
    session = get_session()
    group = session.query(models.Group)\
        .filter_by(user_id=context.user_id)\
        .filter_by(gid=gid)\
        .filter_by(deleted=0)\
        .first()

    if not group:
        raise exception.GroupNotFound(gid=gid)
    return dict(group)


def require_admin_context(f):
    """Decorator to require admin request context.

    The first argument to the wrapped function must be the context.

    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        rack.context.require_admin_context(args[0])
        return f(*args, **kwargs)
    return wrapper


def group_create(context, values):
    session = get_session()
    group_ref = models.Group()
    group_ref.update(values)
    group_ref.save(session)

    return dict(group_ref)


def group_update(context, values):
    session = get_session()
    group_ref = session.query(models.Group). \
        filter(models.Group.gid == values["gid"]).first()
    if group_ref is None:
        raise exception.GroupNotFound(gid=values["gid"])

    group_ref.update(values)
    group_ref.save(session)

    return dict(group_ref)


def group_delete(context, gid):
    session = get_session()
    group_ref = session.query(models.Group)\
        .filter_by(deleted=0)\
        .filter_by(gid=gid)\
        .first()
    if group_ref is None:
        raise exception.GroupNotFound(gid=gid)

    values = {
        "status": "DELETING",
        "deleted": 1,
        "deleted_at": timeutils.utcnow()
    }
    group_ref.update(values)
    group_ref.save(session)

    return dict(group_ref)


def service_model_query(context, model, *args, **kwargs):
    session = kwargs.get('session') or get_session()
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    query = session.query(model, *args)

    default_deleted_value = model.__mapper__.c.deleted.default.arg
    if read_deleted == 'no':
        query = query.filter(model.deleted == default_deleted_value)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter(model.deleted != default_deleted_value)
    else:
        raise Exception(_("Unrecognized read_deleted value '%s'")
                        % read_deleted)

    return query


@require_admin_context
def service_destroy(context, service_id):
    session = get_session()
    with session.begin():
        count = service_model_query(context, models.Service,
                                    session=session).\
            filter_by(id=service_id).\
            soft_delete(synchronize_session=False)

        if count == 0:
            raise exception.ServiceNotFound(service_id=service_id)


@require_admin_context
def service_get(context, service_id):
    session = get_session()
    service_ref = service_model_query(context, models.Service,
                                      session=session).\
        filter_by(id=service_id).\
        first()

    if not service_ref:
        raise exception.ServiceNotFound(service_id=service_id)

    return jsonutils.to_primitive(service_ref)


@require_admin_context
def service_get_all(context, disabled=None):
    session = get_session()
    query = service_model_query(context, models.Service,
                                session=session)

    if disabled is not None:
        query = query.filter_by(disabled=disabled)

    service_refs = query.all()
    return jsonutils.to_primitive(service_refs)


@require_admin_context
def service_get_all_by_topic(context, topic):
    session = get_session()
    service_refs = service_model_query(context, models.Service,
                                       session=session,
                                       read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(topic=topic).\
        all()

    return jsonutils.to_primitive(service_refs)


@require_admin_context
def service_get_by_host_and_topic(context, host, topic):
    session = get_session()
    service_ref = service_model_query(context, models.Service,
                                      session=session,
                                      read_deleted="no").\
        filter_by(disabled=False).\
        filter_by(host=host).\
        filter_by(topic=topic).\
        first()

    return jsonutils.to_primitive(service_ref)


@require_admin_context
def service_get_all_by_host(context, host):
    session = get_session()
    service_refs = service_model_query(context, models.Service,
                                       session=session,
                                       read_deleted="no").\
        filter_by(host=host).\
        all()

    return jsonutils.to_primitive(service_refs)


@require_admin_context
def service_get_by_args(context, host, binary):
    session = get_session()
    service_ref = service_model_query(context, models.Service,
                                      session=session).\
        filter_by(host=host).\
        filter_by(binary=binary).\
        first()

    if not service_ref:
        raise exception.HostBinaryNotFound(host=host, binary=binary)

    return jsonutils.to_primitive(service_ref)


@require_admin_context
def service_create(context, values):
    session = get_session()
    service_ref = models.Service()
    service_ref.update(values)
    if not CONF.enable_new_services:
        service_ref.disabled = True
    try:
        service_ref.save(session)
    except db_exc.DBDuplicateEntry as e:
        if 'binary' in e.columns:
            raise exception.ServiceBinaryExists(host=values.get('host'),
                                                binary=values.get('binary'))
        raise exception.ServiceTopicExists(host=values.get('host'),
                                           topic=values.get('topic'))

    return jsonutils.to_primitive(service_ref)


@require_admin_context
def service_update(context, service_id, values):
    session = get_session()
    with session.begin():
        service_ref = service_model_query(context, models.Service,
                                          session=session).\
            filter_by(id=service_id).\
            first()

        if not service_ref:
            raise exception.ServiceNotFound(service_id=service_id)

        service_ref.update(values)

    return jsonutils.to_primitive(service_ref)


def network_create(context, values):
    session = get_session()
    network_ref = models.Network()
    network_ref.update(values)
    network_ref.save(session)

    return dict(network_ref)


def network_update(context, network_id, values):
    session = get_session()
    network_ref = session.query(models.Network)\
        .filter(models.Network.deleted == 0)\
        .filter(models.Network.network_id == network_id)\
        .first()

    network_ref.update(values)
    network_ref.save(session)


def network_get_all(context, gid, filters):
    session = get_session()
    query = session.query(models.Network)\
        .filter_by(deleted=0)\
        .filter_by(gid=gid)

    if 'network_id' in filters:
        query = query.filter_by(network_id=filters['network_id'])
    if 'neutron_network_id' in filters:
        query = query.filter_by(
            neutron_network_id=filters['neutron_network_id'])
    if 'display_name' in filters:
        query = query.filter_by(display_name=filters['display_name'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    if 'is_admin' in filters:
        query = query.filter_by(is_admin=filters['is_admin'])
    if 'subnet' in filters:
        query = query.filter_by(subnet=filters['subnet'])
    if 'ext_router' in filters:
        query = query.filter_by(ext_router=filters['ext_router'])

    networks = query.all()

    return [dict(network) for network in networks]


def network_get_by_network_id(context, gid, network_id):
    session = get_session()
    network = session.query(models.Network)\
        .filter_by(deleted=0)\
        .filter_by(gid=gid)\
        .filter_by(network_id=network_id)\
        .first()
    if not network:
        raise exception.NetworkNotFound(network_id=network_id)

    network_dict = dict(network)
    network_dict.update(
        dict(processes=[dict(process) for process in network.processes]))

    return network_dict


def network_delete(context, gid, network_id):
    session = get_session()
    network_ref = session.query(models.Network)\
        .filter(models.Network.deleted == 0)\
        .filter(models.Network.gid == gid)\
        .filter(models.Network.network_id == network_id)\
        .first()
    values = {}
    values["deleted"] = 1
    values["deleted_at"] = timeutils.utcnow()
    values["status"] = "DELETING"
    network_ref.update(values)
    network_ref.save(session)
    return dict(network_ref)


def keypair_get_all(context, gid, filters={}):
    session = get_session()
    query = session.query(models.Keypair)\
        .filter_by(gid=gid)\
        .filter_by(deleted=0)
    if 'keypair_id' in filters:
        query = query.filter_by(keypair_id=filters['keypair_id'])
    if 'nova_keypair_id' in filters:
        query = query.filter_by(nova_keypair_id=filters['nova_keypair_id'])
    if 'display_name' in filters:
        query = query.filter_by(display_name=filters['display_name'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    if 'is_default' in filters:
        query = query.filter_by(is_default=filters['is_default'])

    responce_keypairs = query.all()

    return [dict(keypair) for keypair in responce_keypairs]


def keypair_get_by_keypair_id(context, gid, keypair_id):
    session = get_session()
    keypair = session.query(models.Keypair)\
        .filter_by(gid=gid)\
        .filter_by(keypair_id=keypair_id)\
        .filter_by(deleted=0)\
        .first()

    if not keypair:
        raise exception.KeypairNotFound(keypair_id=keypair_id)

    return dict(keypair)


def keypair_create(context, values):
    session = get_session()
    keypair_ref = models.Keypair()
    keypair_ref.update(values)
    keypair_ref.save(session)
    return dict(keypair_ref)


def keypair_update(context, gid, keypair_id, values):
    session = get_session()
    keypair_ref = session.query(models.Keypair)\
        .filter_by(gid=gid)\
        .filter_by(keypair_id=keypair_id)\
        .filter_by(deleted=0)\
        .first()
    if keypair_ref is None:
        raise exception.KeypairNotFound(keypair_id=keypair_id)

    keypair_ref.update(values)
    keypair_ref.save(session)

    return dict(keypair_ref)


def keypair_delete(context, gid, keypair_id):
    session = get_session()
    keypair_ref = session.query(models.Keypair)\
        .filter_by(gid=gid)\
        .filter_by(keypair_id=keypair_id)\
        .filter_by(deleted=0)\
        .first()
    if keypair_ref is None:
        raise exception.KeypairNotFound(keypair_id=keypair_id)

    values = {
        "status": "DELETING",
        "deleted": 1,
        "deleted_at": timeutils.utcnow()
    }
    keypair_ref.update(values)
    keypair_ref.save(session)

    return dict(keypair_ref)


def securitygroup_get_all(context, gid, filters={}):
    session = get_session()
    query = session.query(models.Securitygroup).filter_by(gid=gid, deleted=0)

    if 'securitygroup_id' in filters:
        query = query.filter_by(securitygroup_id=filters['securitygroup_id'])
    if 'name' in filters:
        query = query.filter_by(display_name=filters['name'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    if 'is_default' in filters:
        query = query.filter_by(is_default=filters['is_default'])
    securitygroups = query.all()

    return [dict(securitygroup) for securitygroup in securitygroups]


def securitygroup_get_by_securitygroup_id(context, gid, securitygroup_id):
    session = get_session()
    securitygroup = session.query(models.Securitygroup)\
        .filter_by(deleted=0)\
        .filter_by(gid=gid)\
        .filter_by(securitygroup_id=securitygroup_id)\
        .first()

    if not securitygroup:
        raise exception.SecuritygroupNotFound(
            securitygroup_id=securitygroup_id)

    securitygroup_dict = dict(securitygroup)
    securitygroup_dict.update(
        dict(processes=[dict(process) for process in securitygroup.processes]))
    return securitygroup_dict


def securitygroup_create(context, values):
    session = get_session()
    securitygroup_ref = models.Securitygroup()
    securitygroup_ref.update(values)
    securitygroup_ref.save(session)

    return dict(securitygroup_ref)


def securitygroup_update(context, gid, securitygroup_id, values):
    session = get_session()
    securitygroup_ref = session.query(models.Securitygroup). \
        filter_by(deleted=0). \
        filter_by(gid=gid). \
        filter_by(securitygroup_id=securitygroup_id). \
        first()
    if securitygroup_ref is None:
        raise exception.SecuritygroupNotFound(
            securitygroup_id=securitygroup_id)

    securitygroup_ref.update(values)
    securitygroup_ref.save(session)

    return dict(securitygroup_ref)


def securitygroup_delete(context, gid, securitygroup_id):
    session = get_session()
    securitygroup_ref = session.query(models.Securitygroup). \
        filter_by(deleted=0). \
        filter_by(gid=gid). \
        filter_by(securitygroup_id=securitygroup_id). \
        first()
    if securitygroup_ref is None:
        raise exception.SecuritygroupNotFound(
            securitygroup_id=securitygroup_id)

    securitygroup_ref.update({"deleted": 1,
                              'deleted_at': timeutils.utcnow(),
                              "status": "DELETING"})
    securitygroup_ref.save(session)

    return dict(securitygroup_ref)


def process_get_all(context, gid, filters={}):
    session = get_session()
    query = session.query(models.Process).filter_by(gid=gid, deleted=0)

    if 'pid' in filters:
        query = query.filter_by(pid=filters['pid'])
    if 'ppid' in filters:
        query = query.filter_by(ppid=filters['ppid'])
    if 'name' in filters:
        query = query.filter_by(display_name=filters['name'])
    if 'status' in filters:
        query = query.filter_by(status=filters['status'])
    if 'glance_image_id' in filters:
        query = query.filter_by(glance_image_id=filters['glance_image_id'])
    if 'nova_flavor_id' in filters:
        query = query.filter_by(nova_flavor_id=filters['nova_flavor_id'])
    if 'keypair_id' in filters:
        query = query.filter_by(keypair_id=filters['keypair_id'])
    if 'securitygroup_id' in filters:
        query = query.filter(
            models.Process.securitygroups.any(
                securitygroup_id=filters["securitygroup_id"]))
    if 'network_id' in filters:
        query = query.filter(
            models.Process.networks.any(
                network_id=filters["network_id"]))
    if 'is_proxy' in filters:
        query = query.filter_by(is_proxy=filters['is_proxy'])
    if 'app_status' in filters:
        query = query.filter_by(app_status=filters['app_status'])

    process_refs = query.all()
    return [_get_process_dict(process_ref) for process_ref in process_refs]


def process_get_by_pid(context, gid, pid):
    session = get_session()
    process_ref = session.query(models.Process)\
        .filter_by(deleted=0)\
        .filter_by(gid=gid)\
        .filter_by(pid=pid)\
        .first()

    if not process_ref:
        raise exception.ProcessNotFound(pid=pid)
    return _get_process_dict(process_ref)


def process_get_not_error_status_for_proxy(context, gid):
    session = get_session()
    query = session.query(models.Process).filter_by(
        gid=gid, deleted=0, is_proxy=True)
    process_refs = query.filter(models.Process.status != 'ERROR').all()

    return [_get_process_dict(process_ref) for process_ref in process_refs]


def process_create(context, values, network_ids, securitygroup_ids):
    session = get_session()
    with session.begin():
        process_ref = models.Process(**values)
        session.add(process_ref)

        try:
            if network_ids:
                for network_id in network_ids:
                    network_ref = session.query(models.Network)\
                        .filter_by(deleted=0)\
                        .filter_by(gid=values["gid"])\
                        .filter_by(network_id=network_id)\
                        .first()
                    if network_ref is None:
                        raise exception.NetworkNotFound(network_id=network_id)
                    session.add(
                        models.ProcessNetwork(pid=values["pid"],
                                              network_id=network_ref
                                              .network_id))

            if securitygroup_ids:
                for securitygroup_id in securitygroup_ids:
                    securitygroup_ref = session.query(models.Securitygroup)\
                        .filter_by(deleted=0)\
                        .filter_by(gid=values["gid"])\
                        .filter_by(securitygroup_id=securitygroup_id)\
                        .first()
                    if securitygroup_ref is None:
                        raise exception.SecuritygroupNotFound(
                            securitygroup_id=securitygroup_id)
                    session.add(models.ProcessSecuritygroup(
                        pid=values["pid"],
                        securitygroup_id=securitygroup_ref.securitygroup_id))

            session.flush()
        except db_exc.DBDuplicateEntry:
            msg = _("securitygroup or network is duplicated")
            raise exception.InvalidInput(reason=msg)

    return _get_process_dict(process_ref)


def process_update(context, gid, pid, values):
    session = get_session()
    process_ref = session.query(models.Process). \
        filter_by(deleted=0). \
        filter_by(gid=gid). \
        filter_by(pid=pid). \
        first()
    if process_ref is None:
        raise exception.ProcessNotFound(pid=pid)

    process_ref.update(values)
    process_ref.save(session)

    return dict(process_ref)


def process_delete(context, gid, pid):
    session = get_session()
    process_ref = session.query(models.Process). \
        filter_by(deleted=0). \
        filter_by(gid=gid). \
        filter_by(pid=pid). \
        first()
    if process_ref is None:
        raise exception.ProcessNotFound(pid=pid)

    process_ref.update({"deleted": 1,
                        'deleted_at': timeutils.utcnow(),
                        "status": "DELETING"})
    process_ref.save(session)

    return _get_process_dict(process_ref)


def _get_process_dict(process_ref):
    process_dict = dict(process_ref)
    process_dict.update(dict(securitygroups=[dict(securitygroup)
                                             for securitygroup in process_ref
                                             .securitygroups]))
    process_dict.update(dict(networks=[dict(network)
                                       for network in process_ref.networks]))
    return process_dict
