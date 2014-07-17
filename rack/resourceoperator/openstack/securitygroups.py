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
from rack import exception
from rack.openstack.common import log as logging
from rack.resourceoperator import openstack as os_client

LOG = logging.getLogger(__name__)


class SecuritygroupAPI(object):

    def securitygroup_create(self, name):
        try:
            neutron = os_client.get_neutron_client()
            res = neutron.create_security_group({"security_group":
                                                 {"name": name}})
            neutron_securitygroup_id = res['security_group']['id']
        except Exception as e:
            LOG.exception(e)
            raise exception.SecuritygroupCreateFailed()

        return neutron_securitygroup_id

    def securitygroup_delete(self, neutron_securitygroup_id):
        try:
            neutron = os_client.get_neutron_client()
            neutron.delete_security_group(neutron_securitygroup_id)
        except Exception as e:
            LOG.exception(e)
            raise exception.SecuritygroupDeleteFailed()


class SecuritygroupruleAPI(object):

    def securitygrouprule_create(self, neutron_securitygroup_id, protocol,
                                 port_range_min=None, port_range_max=None,
                                 remote_neutron_securitygroup_id=None,
                                 remote_ip_prefix=None,
                                 direction="ingress", ethertype="IPv4"):
        try:
            self.neutron = os_client.get_neutron_client()
            if remote_neutron_securitygroup_id:
                self.neutron.create_security_group_rule(
                    {"security_group_rule":
                     {"direction": direction,
                      "ethertype": ethertype,
                      "security_group_id": neutron_securitygroup_id,
                      "protocol": protocol,
                      "port_range_min": port_range_min or port_range_max,
                      "port_range_max": port_range_max,
                      "remote_group_id": remote_neutron_securitygroup_id,
                      }})
            elif remote_ip_prefix:
                self.neutron.create_security_group_rule(
                    {"security_group_rule":
                     {"direction": direction,
                      "ethertype": ethertype,
                      "security_group_id": neutron_securitygroup_id,
                      "protocol": protocol,
                      "port_range_min": port_range_min or port_range_max,
                      "port_range_max": port_range_max,
                      "remote_ip_prefix": remote_ip_prefix,
                      }})
        except Exception as e:
            LOG.exception(e)
            raise exception.SecuritygroupCreateFailed()
