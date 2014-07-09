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

from rack import debugger
from rack.openstack.common.db import options
from rack import paths
from rack import rpc
from rack import version

_DEFAULT_SQL_CONNECTION = 'sqlite:///' + paths.state_path_def('rack.sqlite')


def parse_args(argv, default_config_files=None):
    options.set_defaults(sql_connection=_DEFAULT_SQL_CONNECTION,
                         sqlite_db='rack.sqlite')
    rpc.set_defaults(control_exchange='rack')
    debugger.register_cli_opts()
    cfg.CONF(argv[1:],
             project='rack',
             version=version.version_string(),
             default_config_files=default_config_files)
    rpc.init(cfg.CONF)
