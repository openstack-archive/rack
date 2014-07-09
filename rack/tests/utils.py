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

import errno
import platform
import socket
import sys

from oslo.config import cfg

import rack.context
import rack.db
from rack import exception

CONF = cfg.CONF
CONF.import_opt('use_ipv6', 'rack.netconf')


def get_test_admin_context():
    return rack.context.get_admin_context()



def is_osx():
    return platform.mac_ver()[0] != ''


test_dns_managers = []


def cleanup_dns_managers():
    global test_dns_managers
    for manager in test_dns_managers:
        manager.delete_dns_file()
    test_dns_managers = []


def killer_xml_body():
    return (("""<!DOCTYPE x [
            <!ENTITY a "%(a)s">
            <!ENTITY b "%(b)s">
            <!ENTITY c "%(c)s">]>
        <foo>
            <bar>
                <v1>%(d)s</v1>
            </bar>
        </foo>""") % {
        'a': 'A' * 10,
        'b': '&a;' * 10,
        'c': '&b;' * 10,
        'd': '&c;' * 9999,
    }).strip()


def is_ipv6_supported():
    has_ipv6_support = socket.has_ipv6
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        s.close()
    except socket.error as e:
        if e.errno == errno.EAFNOSUPPORT:
            has_ipv6_support = False
        else:
            raise

    # check if there is at least one interface with ipv6
    if has_ipv6_support and sys.platform.startswith('linux'):
        try:
            with open('/proc/net/if_inet6') as f:
                if not f.read():
                    has_ipv6_support = False
        except IOError:
            has_ipv6_support = False

    return has_ipv6_support
