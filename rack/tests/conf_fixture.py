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


from rack import config
from rack.openstack.common.fixture import config as config_fixture
from rack import paths
from rack.tests import utils

CONF = cfg.CONF
CONF.import_opt('use_ipv6', 'rack.netconf')
CONF.import_opt('host', 'rack.netconf')
CONF.import_opt('policy_file', 'rack.policy')
CONF.import_opt('api_paste_config', 'rack.wsgi')


class ConfFixture(config_fixture.Config):
    """Fixture to manage global conf settings."""
    def setUp(self):
        super(ConfFixture, self).setUp()
        self.conf.set_default('api_paste_config',
                              paths.state_path_def('etc/api-paste.ini'))
        self.conf.set_default('host', 'fake-mini')
        self.conf.set_default('connection', "sqlite://", group='database')
        self.conf.set_default('sqlite_synchronous', False, group='database')
        self.conf.set_default('use_ipv6', True)
        config.parse_args([], default_config_files=[])
        self.addCleanup(utils.cleanup_dns_managers)
