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
from rack.openstack.common import log as logging
from rack.resourceoperator import openstack as os_client

LOG = logging.getLogger(__name__)


class SecuritygroupAPI(object):

    def securitygroup_list(self):
        neutron = os_client.get_neutron_client()
        securitygroup_list = neutron.list_security_groups()
        neutron_securitygroup_ids = []
        for securitygroup in securitygroup_list['security_groups']:
            neutron_securitygroup_ids.append(securitygroup['id'])
        return neutron_securitygroup_ids

    def securitygroup_get(self, securitygroup_id):
        neutron = os_client.get_neutron_client()
        securitygroup = neutron.show_security_group(securitygroup_id)
        return securitygroup['security_group']['id']

    def securitygroup_create(self, name, rules):
        neutron = os_client.get_neutron_client()
        body = {"security_group": {"name": name}}
        securitygroup = neutron.create_security_group(body)['security_group']
        neutron_securitygroup_id = securitygroup['id']

        def _securitygroup_rule_create(neutron_securitygroup_id,
                                       protocol, port_range_min=None,
                                       port_range_max=None,
                                       remote_neutron_securitygroup_id=None,
                                       remote_ip_prefix=None):
            body = {
                "security_group_rule": {
                    "direction": "ingress",
                    "ethertype": "IPv4",
                    "security_group_id": neutron_securitygroup_id,
                    "protocol": protocol,
                    "port_range_min": port_range_min or port_range_max,
                    "port_range_max": port_range_max,
                }
            }
            if remote_neutron_securitygroup_id:
                body['security_group_rule']['remote_group_id'] =\
                    remote_neutron_securitygroup_id
            elif remote_ip_prefix:
                body['security_group_rule']['remote_ip_prefix'] =\
                    remote_ip_prefix
            neutron.create_security_group_rule(body)

        if rules:
            try:
                for rule in rules:
                    _securitygroup_rule_create(
                        neutron_securitygroup_id, **rule)
            except Exception as e:
                neutron.delete_security_group(neutron_securitygroup_id)
                raise e

        return dict(neutron_securitygroup_id=neutron_securitygroup_id)

    def securitygroup_delete(self, neutron_securitygroup_id):
        neutron = os_client.get_neutron_client()
        neutron.delete_security_group(neutron_securitygroup_id)
