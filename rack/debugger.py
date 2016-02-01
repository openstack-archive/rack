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


import sys


def enabled():
    return ('--remote_debug-host' in sys.argv and
            '--remote_debug-port' in sys.argv)


def register_cli_opts():
    from oslo.config import cfg

    cli_opts = [
        cfg.StrOpt('host',
                   help='Debug host (IP or name) to connect. Note '
                   'that using the remote debug option changes how '
                        'Rack uses the eventlet library to support async IO. '
                        'This could result in failures that do not occur '
                        'under normal operation. Use at your own risk.'),

        cfg.IntOpt('port',
                   help='Debug port to connect. Note '
                   'that using the remote debug option changes how '
                        'Rack uses the eventlet library to support async IO. '
                        'This could result in failures that do not occur '
                        'under normal operation. Use at your own risk.')

    ]

    cfg.CONF.register_cli_opts(cli_opts, 'remote_debug')


def init():
    from oslo.config import cfg
    CONF = cfg.CONF

    # NOTE(markmc): gracefully handle the CLI options not being registered
    if 'remote_debug' not in CONF:
        return

    if not (CONF.remote_debug.host and CONF.remote_debug.port):
        return

    from rack.openstack.common.gettextutils import _
    from rack.openstack.common import log as logging
    LOG = logging.getLogger(__name__)

    LOG.debug(_('Listening on %(host)s:%(port)s for debug connection'),
              {'host': CONF.remote_debug.host,
               'port': CONF.remote_debug.port})

    from pydev import pydevd
    pydevd.settrace(host=CONF.remote_debug.host,
                    port=CONF.remote_debug.port,
                    stdoutToServer=False,
                    stderrToServer=False)

    LOG.warning(_('WARNING: Using the remote debug option changes how '
               'Rack uses the eventlet library to support async IO. This '
               'could result in failures that do not occur under normal '
               'operation. Use at your own risk.'))
