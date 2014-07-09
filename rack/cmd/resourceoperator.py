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

"""Starter script for RACK ResourceOperator."""

import sys

from oslo.config import cfg

from rack import config
from rack.openstack.common import log as logging
from rack import service
from rack import utils

CONF = cfg.CONF
CONF.import_opt('resourceoperator_topic', 'rack.resourceoperator.rpcapi')
CONF.import_opt('os_username', 'rack.resourceoperator.openstack')
CONF.import_opt('os_password', 'rack.resourceoperator.openstack')
CONF.import_opt('os_tenant_name', 'rack.resourceoperator.openstack')
CONF.import_opt('os_auth_url', 'rack.resourceoperator.openstack')


def main():
    config.parse_args(sys.argv)
    logging.setup("rack")
    utils.monkey_patch()

    server = service.Service.create(binary='rack-resourceoperator',
                                    topic=CONF.resourceoperator_topic)
    service.serve(server)
    service.wait()
