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

from neutronclient.v2_0 import client as neutron_client
from novaclient.v1_1 import client as nova_client

from rack import exception
from rack.openstack.common import log as logging

openstack_client_opts = [
    cfg.StrOpt('os_username',
               help='Valid username for OpenStack'),
    cfg.StrOpt('os_password',
               help='Valid password for OpenStack'),
    cfg.StrOpt('os_tenant_name',
               help='Valid tenant name for OpenStack'),
    cfg.StrOpt('os_auth_url',
               help='The keystone endpoint')
]

CONF = cfg.CONF
CONF.register_opts(openstack_client_opts)

LOG = logging.getLogger(__name__)


def get_nova_client():
    credentials = {
        "username": CONF.os_username,
        "api_key": CONF.os_password,
        "project_id": CONF.os_tenant_name,
        "auth_url": CONF.os_auth_url
    }

    for key, value in credentials.items():
        if not value:
            raise exception.InvalidOpenStackCredential(credential=key)

    return nova_client.Client(**credentials)


def get_neutron_client():
    credentials = {
        "username": CONF.os_username,
        "password": CONF.os_password,
        "tenant_name": CONF.os_tenant_name,
        "auth_url": CONF.os_auth_url
    }

    for key, value in credentials.items():
        if not value:
            raise exception.InvalidOpenStackCredential(credential=key)

    return neutron_client.Client(**credentials)
