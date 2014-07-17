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
"""
Unit Tests for rack.resourceoperator.rpcapi
"""

import mox
from oslo.config import cfg

from rack import context
from rack.resourceoperator import rpcapi as operator_rpcapi
from rack import test

CONF = cfg.CONF


class ResourceOperatorRpcAPITestCase(test.NoDBTestCase):

    def _test_operator_api(self, method, rpc_method, version=None,
                           fanout=None, host=None, **kwargs):
        ctxt = context.RequestContext('fake_user', 'fake_project')

        rpcapi = operator_rpcapi.ResourceOperatorAPI()
        self.assertIsNotNone(rpcapi.client)
        self.assertEqual(
            rpcapi.client.target.topic, CONF.resourceoperator_topic)

        expected_retval = 'foo' if rpc_method == 'call' else None
        expected_version = version
        expected_fanout = fanout
        expected_server = host
        expected_kwargs = kwargs.copy()
        if host:
            kwargs['host'] = host

        self.mox.StubOutWithMock(rpcapi, 'client')

        rpcapi.client.can_send_version(
            mox.IsA(str)).MultipleTimes().AndReturn(True)

        prepare_kwargs = {}
        if expected_fanout:
            prepare_kwargs['fanout'] = True
        if expected_version:
            prepare_kwargs['version'] = expected_version
        if expected_server:
            prepare_kwargs['server'] = expected_server
        rpcapi.client.prepare(**prepare_kwargs).AndReturn(rpcapi.client)

        rpc_method = getattr(rpcapi.client, rpc_method)

        rpc_method(ctxt, method, **expected_kwargs).AndReturn('foo')

        self.mox.ReplayAll()

        rpcapi.client.can_send_version('I fool you mox')

        retval = getattr(rpcapi, method)(ctxt, **kwargs)
        self.assertEqual(retval, expected_retval)

    def test_keypair_create(self):
        self._test_operator_api('keypair_create', rpc_method='cast',
                                host='fake_host', gid='fake_gid',
                                keypair_id='fake_keypair_id',
                                name='fake_name')

    def test_keypair_delete(self):
        self._test_operator_api('keypair_delete', rpc_method='cast',
                                host='fake_host',
                                nova_keypair_id='fake_nova_keypair_id')

    def test_securitygroup_create(self):
        self._test_operator_api('securitygroup_create', rpc_method='cast',
                                host='fake_host', gid='fake_gid',
                                securitygroup_id='fake_securitygroup_id',
                                name='fake_name',
                                securitygrouprules='fake_rules')

    def test_securitygroup_delete(self):
        self._test_operator_api(
            'securitygroup_delete', rpc_method='cast',
            host='fake_host',
            neutron_securitygroup_id='fake_neutron_securitygroup_id')

    def test_network_create(self):
        network = {"network_id": "fake_id"}
        self._test_operator_api('network_create',
                                rpc_method='cast',
                                host='fake_host',
                                network=network)

    def test_network_delete(self):
        self._test_operator_api('network_delete', rpc_method='cast',
                                host='fake_host',
                                neutron_network_id='fake_neutron_network_id',
                                ext_router='fake_ext_router')
