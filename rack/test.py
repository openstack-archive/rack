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

"""Base classes for our unit tests.

Allows overriding of flags for use of fakes, and some black magic for
inline callbacks.

"""

import eventlet
eventlet.monkey_patch(os=False)

import gettext
import logging
import os
import shutil
import sys
import uuid
import mock
import datetime

import fixtures
from oslo.config import cfg
from oslo.messaging import conffixture as messaging_conffixture
import testtools

from rack.db import migration
from rack.db.sqlalchemy import api as session
from rack.openstack.common.fixture import logging as log_fixture
from rack.openstack.common.fixture import moxstubout
from rack.openstack.common import log as oslo_logging
from rack.openstack.common import timeutils
from rack import paths
from rack import service
from rack.tests import conf_fixture
from rack.tests import policy_fixture


test_opts = [
    cfg.StrOpt('sqlite_clean_db',
               default='clean.sqlite',
               help='File name of clean sqlite db'),
]

CONF = cfg.CONF
CONF.register_opts(test_opts)
CONF.import_opt('connection',
                'rack.openstack.common.db.options',
                group='database')
CONF.import_opt('sqlite_db', 'rack.openstack.common.db.options',
                group='database')
CONF.set_override('use_stderr', False)

oslo_logging.setup('rack')

_DB_CACHE = None
_TRUE_VALUES = ('True', 'true', '1', 'yes')


class Database(fixtures.Fixture):

    def __init__(self, db_session, db_migrate, sql_connection,
                 sqlite_db, sqlite_clean_db):
        self.sql_connection = sql_connection
        self.sqlite_db = sqlite_db
        self.sqlite_clean_db = sqlite_clean_db

        self.engine = db_session.get_engine()
        self.engine.dispose()
        conn = self.engine.connect()
        if sql_connection == "sqlite://":
            if db_migrate.db_version() > db_migrate.db_initial_version():
                return
        else:
            testdb = paths.state_path_rel(sqlite_db)
            if os.path.exists(testdb):
                return
        db_migrate.db_sync()
        if sql_connection == "sqlite://":
            conn = self.engine.connect()
            self._DB = "".join(line for line in conn.connection.iterdump())
            self.engine.dispose()
        else:
            cleandb = paths.state_path_rel(sqlite_clean_db)
            shutil.copyfile(testdb, cleandb)

    def setUp(self):
        super(Database, self).setUp()

        if self.sql_connection == "sqlite://":
            conn = self.engine.connect()
            conn.connection.executescript(self._DB)
            self.addCleanup(self.engine.dispose)
        else:
            shutil.copyfile(paths.state_path_rel(self.sqlite_clean_db),
                            paths.state_path_rel(self.sqlite_db))


class ReplaceModule(fixtures.Fixture):

    """Replace a module with a fake module."""

    def __init__(self, name, new_value):
        self.name = name
        self.new_value = new_value

    def _restore(self, old_value):
        sys.modules[self.name] = old_value

    def setUp(self):
        super(ReplaceModule, self).setUp()
        old_value = sys.modules.get(self.name)
        sys.modules[self.name] = self.new_value
        self.addCleanup(self._restore, old_value)


class ServiceFixture(fixtures.Fixture):

    """Run a service as a test fixture."""

    def __init__(self, name, host=None, **kwargs):
        name = name
        host = host and host or uuid.uuid4().hex
        kwargs.setdefault('host', host)
        kwargs.setdefault('binary', 'rack-%s' % name)
        self.kwargs = kwargs

    def setUp(self):
        super(ServiceFixture, self).setUp()
        self.service = service.Service.create(**self.kwargs)
        self.service.start()
        self.addCleanup(self.service.kill)


class TranslationFixture(fixtures.Fixture):

    """Use gettext NullTranslation objects in tests."""

    def setUp(self):
        super(TranslationFixture, self).setUp()
        nulltrans = gettext.NullTranslations()
        gettext_fixture = fixtures.MonkeyPatch('gettext.translation',
                                               lambda *x, **y: nulltrans)
        self.gettext_patcher = self.useFixture(gettext_fixture)


class TestingException(Exception):
    pass


class TestCase(testtools.TestCase):

    """Test case base class for all unit tests.

    Due to the slowness of DB access, please consider deriving from
    `NoDBTestCase` first.
    """
    USES_DB = True

    # NOTE(rpodolyaka): this attribute can be overridden in subclasses in order
    #                   to scale the global test timeout value set for each
    #                   test case separately. Use 0 value to disable timeout.
    TIMEOUT_SCALING_FACTOR = 1

    def setUp(self):
        """Run before each test method to initialize test environment."""
        super(TestCase, self).setUp()
        test_timeout = os.environ.get('OS_TEST_TIMEOUT', 0)
        try:
            test_timeout = int(test_timeout)
        except ValueError:
            # If timeout value is invalid do not set a timeout.
            test_timeout = 0

        if self.TIMEOUT_SCALING_FACTOR >= 0:
            test_timeout *= self.TIMEOUT_SCALING_FACTOR
        else:
            raise ValueError('TIMEOUT_SCALING_FACTOR value must be >= 0')

        if test_timeout > 0:
            self.useFixture(fixtures.Timeout(test_timeout, gentle=True))
        self.useFixture(fixtures.NestedTempfile())
        self.useFixture(fixtures.TempHomeDir())
        self.useFixture(TranslationFixture())
        self.useFixture(log_fixture.get_logging_handle_error_fixture())

        if os.environ.get('OS_STDOUT_CAPTURE') in _TRUE_VALUES:
            stdout = self.useFixture(fixtures.StringStream('stdout')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stdout', stdout))
        if os.environ.get('OS_STDERR_CAPTURE') in _TRUE_VALUES:
            stderr = self.useFixture(fixtures.StringStream('stderr')).stream
            self.useFixture(fixtures.MonkeyPatch('sys.stderr', stderr))

        fs = '%(levelname)s [%(name)s] %(message)s'
        self.log_fixture = self.useFixture(fixtures.FakeLogger(
            level=logging.DEBUG,
            format=fs))
        self.useFixture(conf_fixture.ConfFixture(CONF))

        self.messaging_conf = messaging_conffixture.ConfFixture(CONF)
        self.messaging_conf.transport_driver = 'fake'
        self.messaging_conf.response_timeout = 15
        self.useFixture(self.messaging_conf)

        if self.USES_DB:
            global _DB_CACHE
            if not _DB_CACHE:
                _DB_CACHE = Database(session, migration,
                                     sql_connection=CONF.database.connection,
                                     sqlite_db=CONF.database.sqlite_db,
                                     sqlite_clean_db=CONF.sqlite_clean_db)

            self.useFixture(_DB_CACHE)

        mox_fixture = self.useFixture(moxstubout.MoxStubout())
        self.mox = mox_fixture.mox
        self.stubs = mox_fixture.stubs
        self.addCleanup(self._clear_attrs)
        self.useFixture(fixtures.EnvironmentVariable('http_proxy'))
        self.policy = self.useFixture(policy_fixture.PolicyFixture())
        CONF.set_override('fatal_exception_format_errors', True)

    def _clear_attrs(self):
        # Delete attributes that don't start with _ so they don't pin
        # memory around unnecessarily for the duration of the test
        # suite
        for key in [k for k in self.__dict__.keys() if k[0] != '_']:
            del self.__dict__[key]

    def flags(self, **kw):
        """Override flag variables for a test."""
        group = kw.pop('group', None)
        for k, v in kw.iteritems():
            CONF.set_override(k, v, group)

    def start_service(self, name, host=None, **kwargs):
        svc = self.useFixture(ServiceFixture(name, host, **kwargs))
        return svc.service


class APICoverage(object):

    cover_api = None

    def test_api_methods(self):
        self.assertTrue(self.cover_api is not None)
        api_methods = [x for x in dir(self.cover_api)
                       if not x.startswith('_')]
        test_methods = [x[5:] for x in dir(self)
                        if x.startswith('test_')]
        self.assertThat(
            test_methods,
            testtools.matchers.ContainsAll(api_methods))


class TimeOverride(fixtures.Fixture):

    """Fixture to start and remove time override."""

    @mock.patch.object(timeutils, 'utcnow')
    def setUp(self, mock_utcnow):
        super(TimeOverride, self).setUp()
        now = datetime.datetime.utcnow()
        mock_utcnow.return_value = now


class NoDBTestCase(TestCase):

    """`NoDBTestCase` differs from TestCase in that DB access is not supported.
    This makes tests run significantly faster. If possible, all new tests
    should derive from this class.
    """
    USES_DB = False
