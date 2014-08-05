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
Unit Tests for remote procedure calls using queue
"""

import sys
import testtools

import mock
import mox
from oslo.config import cfg

from rack import context
from rack import db
from rack import exception
from rack import manager
from rack import rpc
from rack import service
from rack import test
from rack.tests import utils
from rack import wsgi

from rack.openstack.common import service as _service

test_service_opts = [
    cfg.StrOpt("fake_manager",
               default="rack.tests.test_service.FakeManager",
               help="Manager for testing"),
    cfg.StrOpt("test_service_listen",
               default='127.0.0.1',
               help="Host to bind test service to"),
    cfg.IntOpt("test_service_listen_port",
               default=0,
               help="Port number to bind test service to"),
]

CONF = cfg.CONF
CONF.register_opts(test_service_opts)


class FakeManager(manager.Manager):

    """Fake manager for tests."""

    def test_method(self):
        return 'manager'


class ExtendedService(service.Service):

    def test_method(self):
        return 'service'


class ServiceManagerTestCase(test.TestCase):

    """Test cases for Services."""

    def test_message_gets_to_manager(self):
        serv = service.Service('test',
                               'test',
                               'test',
                               'rack.tests.test_service.FakeManager')
        serv.start()
        self.assertEqual(serv.test_method(), 'manager')

    def test_override_manager_method(self):
        serv = ExtendedService('test',
                               'test',
                               'test',
                               'rack.tests.test_service.FakeManager')
        serv.start()
        self.assertEqual(serv.test_method(), 'service')

    def test_service_with_min_down_time(self):
        CONF.set_override('service_down_time', 10)
        CONF.set_override('report_interval', 10)
        serv = service.Service('test',
                               'test',
                               'test',
                               'rack.tests.test_service.FakeManager')
        serv.start()
        self.assertEqual(CONF.service_down_time, 25)


class ServiceFlagsTestCase(test.TestCase):

    def test_service_enabled_on_create_based_on_flag(self):
        self.flags(enable_new_services=True)
        host = 'foo'
        binary = 'rack-fake'
        app = service.Service.create(host=host, binary=binary)
        app.start()
        app.stop()
        ref = db.service_get(context.get_admin_context(), app.service_id)
        db.service_destroy(context.get_admin_context(), app.service_id)
        self.assertTrue(not ref['disabled'])

    def test_service_disabled_on_create_based_on_flag(self):
        self.flags(enable_new_services=False)
        host = 'foo'
        binary = 'rack-fake'
        app = service.Service.create(host=host, binary=binary)
        app.start()
        app.stop()
        ref = db.service_get(context.get_admin_context(), app.service_id)
        db.service_destroy(context.get_admin_context(), app.service_id)
        self.assertTrue(ref['disabled'])


class ServiceTestCase(test.TestCase):

    """Test cases for Services."""

    def setUp(self):
        super(ServiceTestCase, self).setUp()
        self.host = 'foo'
        self.binary = 'rack-fake'
        self.topic = 'fake'
        self.mox.StubOutWithMock(db, 'service_create')
        self.mox.StubOutWithMock(db, 'service_get_by_args')

    def test_create(self):
        app = service.Service.create(host=self.host, binary=self.binary,
                                     topic=self.topic)

        self.assertTrue(app)

    def _service_start_mocks(self):
        service_create = {'host': self.host,
                          'binary': self.binary,
                          'topic': self.topic,
                          'report_count': 0}
        service_ref = {'host': self.host,
                       'binary': self.binary,
                       'topic': self.topic,
                       'report_count': 0,
                       'id': 1}

        db.service_get_by_args(mox.IgnoreArg(),
                               self.host, self.binary)\
            .AndRaise(exception.NotFound())
        db.service_create(mox.IgnoreArg(),
                          service_create).AndReturn(service_ref)
        return service_ref

    def test_init_and_start_hooks(self):
        self.manager_mock = self.mox.CreateMock(FakeManager)
        self.mox.StubOutWithMock(sys.modules[__name__],
                                 'FakeManager', use_mock_anything=True)
        self.mox.StubOutWithMock(self.manager_mock, 'init_host')
        self.mox.StubOutWithMock(self.manager_mock, 'pre_start_hook')
        self.mox.StubOutWithMock(self.manager_mock, 'post_start_hook')

        FakeManager(host=self.host).AndReturn(self.manager_mock)

        self.manager_mock.service_name = self.topic
        self.manager_mock.additional_endpoints = []

        # init_host is called before any service record is created
        self.manager_mock.init_host()
        self._service_start_mocks()
        # pre_start_hook is called after service record is created,
        # but before RPC consumer is created
        self.manager_mock.pre_start_hook()
        # post_start_hook is called after RPC consumer is created.
        self.manager_mock.post_start_hook()

        self.mox.ReplayAll()

        serv = service.Service(self.host,
                               self.binary,
                               self.topic,
                               'rack.tests.test_service.FakeManager')
        serv.start()

    def test_service_check_create_race(self):
        self.manager_mock = self.mox.CreateMock(FakeManager)
        self.mox.StubOutWithMock(sys.modules[__name__], 'FakeManager',
                                 use_mock_anything=True)
        self.mox.StubOutWithMock(self.manager_mock, 'init_host')
        self.mox.StubOutWithMock(self.manager_mock, 'pre_start_hook')
        self.mox.StubOutWithMock(self.manager_mock, 'post_start_hook')

        FakeManager(host=self.host).AndReturn(self.manager_mock)

        # init_host is called before any service record is created
        self.manager_mock.init_host()

        db.service_get_by_args(mox.IgnoreArg(), self.host, self.binary
                               ).AndRaise(exception.NotFound)
        ex = exception.ServiceTopicExists(host='foo', topic='bar')
        db.service_create(mox.IgnoreArg(), mox.IgnoreArg()
                          ).AndRaise(ex)

        class TestException(Exception):
            pass

        db.service_get_by_args(mox.IgnoreArg(), self.host, self.binary
                               ).AndRaise(TestException)

        self.mox.ReplayAll()

        serv = service.Service(self.host,
                               self.binary,
                               self.topic,
                               'rack.tests.test_service.FakeManager')
        self.assertRaises(TestException, serv.start)

    def test_parent_graceful_shutdown(self):
        self.manager_mock = self.mox.CreateMock(FakeManager)
        self.mox.StubOutWithMock(sys.modules[__name__],
                                 'FakeManager', use_mock_anything=True)
        self.mox.StubOutWithMock(self.manager_mock, 'init_host')
        self.mox.StubOutWithMock(self.manager_mock, 'pre_start_hook')
        self.mox.StubOutWithMock(self.manager_mock, 'post_start_hook')

        self.mox.StubOutWithMock(_service.Service, 'stop')

        FakeManager(host=self.host).AndReturn(self.manager_mock)

        self.manager_mock.service_name = self.topic
        self.manager_mock.additional_endpoints = []

        # init_host is called before any service record is created
        self.manager_mock.init_host()
        self._service_start_mocks()
        # pre_start_hook is called after service record is created,
        # but before RPC consumer is created
        self.manager_mock.pre_start_hook()
        # post_start_hook is called after RPC consumer is created.
        self.manager_mock.post_start_hook()

        _service.Service.stop()

        self.mox.ReplayAll()

        serv = service.Service(self.host,
                               self.binary,
                               self.topic,
                               'rack.tests.test_service.FakeManager')
        serv.start()

        serv.stop()

    @mock.patch('rack.servicegroup.API')
    @mock.patch('rack.db.api.service_get_by_args')
    def test_parent_graceful_shutdown_with_cleanup_host(self,
                                                        mock_svc_get_by_args,
                                                        mock_API):
        self.mox.UnsetStubs()
        mock_svc_get_by_args.return_value = {'id': 'some_value'}
        mock_manager = mock.Mock()

        serv = service.Service(self.host,
                               self.binary,
                               self.topic,
                               'rack.tests.test_service.FakeManager')

        serv.manager = mock_manager
        serv.manager.additional_endpoints = []

        serv.start()
        serv.manager.init_host.assert_called_with()

        serv.stop()
        serv.manager.cleanup_host.assert_called_with()

    @mock.patch('rack.servicegroup.API')
    @mock.patch('rack.db.api.service_get_by_args')
    @mock.patch.object(rpc, 'get_server')
    def test_service_stop_waits_for_rpcserver(
            self, mock_rpc, mock_svc_get_by_args, mock_API):
        self.mox.UnsetStubs()
        mock_svc_get_by_args.return_value = {'id': 'some_value'}
        serv = service.Service(self.host,
                               self.binary,
                               self.topic,
                               'rack.tests.test_service.FakeManager')
        serv.start()
        serv.stop()
        serv.rpcserver.start.assert_called_once_with()
        serv.rpcserver.stop.assert_called_once_with()
        serv.rpcserver.wait.assert_called_once_with()


class TestWSGIService(test.TestCase):

    def setUp(self):
        super(TestWSGIService, self).setUp()
        self.stubs.Set(wsgi.Loader, "load_app", mox.MockAnything())

    def test_service_random_port(self):
        test_service = service.WSGIService("test_service")
        test_service.start()
        self.assertNotEqual(0, test_service.port)
        test_service.stop()

    def test_service_start_with_illegal_workers(self):
        CONF.set_override("rackapi_workers", -1)
        self.assertRaises(exception.InvalidInput,
                          service.WSGIService, "rackapi")

    @testtools.skipIf(not utils.is_ipv6_supported(), "no ipv6 support")
    def test_service_random_port_with_ipv6(self):
        CONF.set_default("test_service_listen", "::1")
        test_service = service.WSGIService("test_service")
        test_service.start()
        self.assertEqual("::1", test_service.host)
        self.assertNotEqual(0, test_service.port)
        test_service.stop()


class TestLauncher(test.TestCase):

    def setUp(self):
        super(TestLauncher, self).setUp()
        self.stubs.Set(wsgi.Loader, "load_app", mox.MockAnything())
        self.service = service.WSGIService("test_service")

    def test_launch_app(self):
        service.serve(self.service)
        self.assertNotEqual(0, self.service.port)
        service._launcher.stop()
