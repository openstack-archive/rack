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
from rack import context
from rack import db
from rack import exception
from rack import test
import uuid


class ModelsObjectComparatorMixin(object):

    def _dict_from_object(self, obj, ignored_keys):
        if ignored_keys is None:
            ignored_keys = []
        return dict([(k, v) for k, v in obj.iteritems()
                     if k not in ignored_keys])

    def _assertEqualObjects(self, obj1, obj2, ignored_keys=None):
        obj1 = self._dict_from_object(obj1, ignored_keys)
        obj2 = self._dict_from_object(obj2, ignored_keys)

        self.assertEqual(len(obj1),
                         len(obj2),
                         "Keys mismatch: %s" %
                         str(set(obj1.keys()) ^ set(obj2.keys())))
        for key, value in obj1.iteritems():
            self.assertEqual(value, obj2[key])

    def _assertEqualListsOfObjects(self, objs1, objs2, ignored_keys=None):
        obj_to_dict = lambda o: self._dict_from_object(o, ignored_keys)
        sort_key = lambda d: [d[k] for k in sorted(d)]
        conv_and_sort = lambda obj: sorted(map(obj_to_dict, obj),
                                           key=sort_key)

        self.assertEqual(conv_and_sort(objs1), conv_and_sort(objs2))

    def _assertEqualOrderedListOfObjects(self, objs1, objs2,
                                         ignored_keys=None):
        obj_to_dict = lambda o: self._dict_from_object(o, ignored_keys)
        conv = lambda obj: map(obj_to_dict, obj)

        self.assertEqual(conv(objs1), conv(objs2))

    def _assertEqualListsOfPrimitivesAsSets(self, primitives1, primitives2):
        self.assertEqual(len(primitives1), len(primitives2))
        for primitive in primitives1:
            self.assertIn(primitive, primitives2)

        for primitive in primitives2:
            self.assertIn(primitive, primitives1)


class GroupTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(GroupTestCase, self).setUp()
        self.ctxt = context.get_admin_context()
        self.user_ctxt = context.RequestContext('user', 'user')
        self.gid = unicode(uuid.uuid4())

    def test_group_get_all(self):
        # set test data
        groups = [
            {
                "display_name": "display_name_01",
                "display_description": "display_description_01",
            },
            {
                "display_name": "display_name_02",
                "display_description": "display_description_02",
            },
            {
                "display_name": "display_name_03",
                "display_description": "display_description_03",
            },
            {
                "display_name": "display_name_04",
                "display_description": "display_description_04",
            }
        ]

        # create test data to group table
        user_ids = ["user_id_01", "user_id_02"]
        created_groups_list = []
        for user_id in user_ids:
            created_groups = [self._create_group(group, user_id=user_id,
                                                 project_id=user_id)
                              for group in groups]
            created_groups_list.append(created_groups)

        # test
        ctext = context.RequestContext(
            user_id=user_ids[0], project_id=user_ids[0])
        res_groups = db.group_get_all(ctext)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']
        self.assertEqual(len(res_groups), len(created_groups_list[0]))
        for group in range(0, len(res_groups)):
            self._assertEqualObjects(
                res_groups[group], created_groups_list[0][group],
                ignored_keys)

    def test_group_get_all_empty(self):
        ctext = context.RequestContext(
            user_id="user01", project_id="user01")
        res_groups = db.group_get_all(ctext)
        expected = []
        self.assertEqual(res_groups, expected)

    def test_group_get_by_gid(self):
        # set test data
        groups = [
            {
                "display_name": "display_name_01",
                "display_description": "display_description_01",
            },
            {
                "display_name": "display_name_02",
                "display_description": "display_description_02",
            },
            {
                "display_name": "display_name_03",
                "display_description": "display_description_03",
            },
            {
                "display_name": "display_name_04",
                "display_description": "display_description_04",
            }
        ]

        # create test data to group table
        user_id = "user_id_01"
        created_groups = [self._create_group(
            group, user_id=user_id, project_id=user_id)for group in groups]
        gid = created_groups[1]["gid"]

        # test
        ctext = context.RequestContext(
            user_id=user_id, project_id=user_id)
        res_group = db.group_get_by_gid(ctext, gid)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']
        self._assertEqualObjects(res_group, created_groups[1], ignored_keys)

    def test_group_get_by_gid_not_found(self):
        # test
        user_id = "user_id_01"
        ctext = context.RequestContext(
            user_id=user_id, project_id=user_id)
        gid = "00000000-0000-0000-0000-000000000010"
        status_code = 200
        try:
            db.group_get_by_gid(ctext, gid)
        except Exception as e:
            status_code = e.code
        self.assertEqual(status_code, 404)

    def _get_base_values(self):
        return {
            'gid': 'fake_name',
            'user_id': 'fake_user_id',
            'project_id': 'fake_project_id',
            'display_name': 'fake_dispalay_name',
            'display_description': 'fake_display_description',
            'status': 'fake_status'
        }

    def _create_group(self, values, user_id=None, project_id=None):
        user_ctxt = context.RequestContext(user_id, project_id)
        values['gid'] = unicode(uuid.uuid4())
        values['user_id'] = user_id
        values['project_id'] = project_id
        v = self._get_base_values()
        v.update(values)
        return db.group_create(user_ctxt, v)

    def test_group_create(self):
        values = {
            "gid": "12345678-1234-5678-9123-123456789012",
            "user_id": "user",
            "project_id": "user",
            "display_name": "test_group",
            "display_description": "This is test group",
            "status": "active"
        }
        group = db.group_create(self.user_ctxt, values)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']
        values.update({"user_id": "user",
                       "project_id": "user",
                       "status": "active"})
        self.assertIsNotNone(group['gid'])
        self._assertEqualObjects(group, values, ignored_keys)

    def test_group_update(self):
        values_before = {
            "gid": "12345678-1234-5678-9123-123456789012",
            "user_id": "user",
            "project_id": "user",
            "display_name": "My_group",
            "display_description": "This is my group.",
            "status": "active"
        }
        group_before = db.group_create(self.user_ctxt, values_before)
        values = {
            "gid": group_before["gid"],
            "display_name": "My_group_updated",
            "display_description": "This is my group updated."
        }
        group = db.group_update(self.user_ctxt, values)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at', "user_id", "project_id", "status"]
        self._assertEqualObjects(group, values, ignored_keys)

    def test_group_delete(self):
        values_before = {
            "gid": self.gid,
            "user_id": "user_id",
            "project_id": "project_id",
            "display_name": "My_group",
            "display_description": "This is my group.",
            "status": "active"
        }
        db.group_create(self.user_ctxt, values_before)
        deleted_group = db.group_delete(self.ctxt, self.gid)
        self.assertEqual(deleted_group["deleted"], 1)
        self.assertEqual(deleted_group["status"], "DELETING")
        self.assertIsNotNone(deleted_group.get("deleted_at"))

    def test_group_update_gid_not_found(self):
        # test
        values_before = {
            "gid": "12345678-1234-5678-9123-123456789012",
            "user_id": "user",
            "project_id": "user",
            "display_name": "My_group",
            "display_description": "This is my group.",
            "status": "active"
        }
        group_before = db.group_create(self.user_ctxt, values_before)
        values = {
            "gid": group_before["gid"] + "not-found",
            "display_name": "My_group_updated",
            "display_description": "This is my group updated."
        }
        try:
            db.group_update(self.user_ctxt, values)
        except Exception as e:
            status_code = e.code
        self.assertEqual(status_code, 404)

    def test_group_delete_not_found(self):
        self.assertRaises(exception.GroupNotFound,
                          db.group_delete,
                          context=self.user_ctxt,
                          gid=self.gid)


class ServiceTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(ServiceTestCase, self).setUp()
        self.ctxt = context.get_admin_context()

    def _get_base_values(self):
        return {
            'host': 'fake_host',
            'binary': 'fake_binary',
            'topic': 'fake_topic',
            'report_count': 3,
            'disabled': False
        }

    def _create_service(self, values):
        v = self._get_base_values()
        v.update(values)
        return db.service_create(self.ctxt, v)

    def test_service_create(self):
        service = self._create_service({})
        self.assertIsNotNone(service['id'])
        for key, value in self._get_base_values().iteritems():
            self.assertEqual(value, service[key])

    def test_service_destroy(self):
        service1 = self._create_service({})
        service2 = self._create_service({'host': 'fake_host2'})

        db.service_destroy(self.ctxt, service1['id'])
        self.assertRaises(exception.ServiceNotFound,
                          db.service_get, self.ctxt, service1['id'])
        self._assertEqualObjects(db.service_get(self.ctxt, service2['id']),
                                 service2)

    def test_service_update(self):
        service = self._create_service({})
        new_values = {
            'host': 'fake_host1',
            'binary': 'fake_binary1',
            'topic': 'fake_topic1',
            'report_count': 4,
            'disabled': True
        }
        db.service_update(self.ctxt, service['id'], new_values)
        updated_service = db.service_get(self.ctxt, service['id'])
        for key, value in new_values.iteritems():
            self.assertEqual(value, updated_service[key])

    def test_service_update_not_found_exception(self):
        self.assertRaises(exception.ServiceNotFound,
                          db.service_update, self.ctxt, 100500, {})

    def test_service_get(self):
        service1 = self._create_service({})
        self._create_service({'host': 'some_other_fake_host'})
        real_service1 = db.service_get(self.ctxt, service1['id'])
        self._assertEqualObjects(service1, real_service1,
                                 ignored_keys=['compute_node'])

    def test_service_get_not_found_exception(self):
        self.assertRaises(exception.ServiceNotFound,
                          db.service_get, self.ctxt, 100500)

    def test_service_get_by_host_and_topic(self):
        service1 = self._create_service({'host': 'host1', 'topic': 'topic1'})
        self._create_service({'host': 'host2', 'topic': 'topic2'})

        real_service1 = db.service_get_by_host_and_topic(self.ctxt,
                                                         host='host1',
                                                         topic='topic1')
        self._assertEqualObjects(service1, real_service1)

    def test_service_get_all(self):
        values = [
            {'host': 'host1', 'topic': 'topic1'},
            {'host': 'host2', 'topic': 'topic2'},
            {'disabled': True}
        ]
        services = [self._create_service(vals) for vals in values]
        disabled_services = [services[-1]]
        non_disabled_services = services[:-1]

        compares = [
            (services, db.service_get_all(self.ctxt)),
            (disabled_services, db.service_get_all(self.ctxt, True)),
            (non_disabled_services, db.service_get_all(self.ctxt, False))
        ]
        for comp in compares:
            self._assertEqualListsOfObjects(*comp)

    def test_service_get_all_by_topic(self):
        values = [
            {'host': 'host1', 'topic': 't1'},
            {'host': 'host2', 'topic': 't1'},
            {'disabled': True, 'topic': 't1'},
            {'host': 'host3', 'topic': 't2'}
        ]
        services = [self._create_service(vals) for vals in values]
        expected = services[:2]
        real = db.service_get_all_by_topic(self.ctxt, 't1')
        self._assertEqualListsOfObjects(expected, real)

    def test_service_get_all_by_host(self):
        values = [
            {'host': 'host1', 'topic': 't11', 'binary': 'b11'},
            {'host': 'host1', 'topic': 't12', 'binary': 'b12'},
            {'host': 'host2', 'topic': 't1'},
            {'host': 'host3', 'topic': 't1'}
        ]
        services = [self._create_service(vals) for vals in values]

        expected = services[:2]
        real = db.service_get_all_by_host(self.ctxt, 'host1')
        self._assertEqualListsOfObjects(expected, real)

    def test_service_get_by_args(self):
        values = [
            {'host': 'host1', 'binary': 'a'},
            {'host': 'host2', 'binary': 'b'}
        ]
        services = [self._create_service(vals) for vals in values]

        service1 = db.service_get_by_args(self.ctxt, 'host1', 'a')
        self._assertEqualObjects(services[0], service1)

        service2 = db.service_get_by_args(self.ctxt, 'host2', 'b')
        self._assertEqualObjects(services[1], service2)

    def test_service_get_by_args_not_found_exception(self):
        self.assertRaises(exception.HostBinaryNotFound,
                          db.service_get_by_args,
                          self.ctxt, 'non-exists-host', 'a')

    def test_service_binary_exists_exception(self):
        db.service_create(self.ctxt, self._get_base_values())
        values = self._get_base_values()
        values.update({'topic': 'top1'})
        self.assertRaises(exception.ServiceBinaryExists, db.service_create,
                          self.ctxt, values)

    def test_service_topic_exists_exceptions(self):
        db.service_create(self.ctxt, self._get_base_values())
        values = self._get_base_values()
        values.update({'binary': 'bin1'})
        self.assertRaises(exception.ServiceTopicExists, db.service_create,
                          self.ctxt, values)


class NetworksTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(NetworksTestCase, self).setUp()
        self.ctxt = context.get_admin_context()

        self.gid = unicode(uuid.uuid4())
        self.network_id = unicode(uuid.uuid4())
        self.neutron_network_id = unicode(uuid.uuid4())
        self.ext_router_id = unicode(uuid.uuid4())

    def test_networks_create(self):
        values = {
            "network_id": self.network_id,
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        network = db.network_create(self.ctxt, values)

        ignored_keys = ['deleted',
                        'deleted_at',
                        'updated_at',
                        'created_at']
        self._assertEqualObjects(network, values, ignored_keys)

    def test_network_get_all(self):
        values = {
            "network_id": "",
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        for i in range(1 - 5):
            values["network_id"] = "network_id" + str(i)
            db.network_create(self.ctxt, values)

        network_list = db.network_get_all(self.ctxt, self.gid)
        for network in network_list:
            self.assertEqual(network["gid"], self.gid)

    def test_network_get_all_return_empty_list(self):
        network_list = db.network_get_all(self.ctxt, self.gid)
        self.assertEqual(network_list, [])

    def test_network_get_by_network_id(self):
        values = {
            "network_id": "",
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        for i in range(1 - 5):
            values["network_id"] = "network_id" + str(i)
            db.network_create(self.ctxt, values)
        values["network_id"] = self.network_id
        db.network_create(self.ctxt, values)

        network = db.network_get_by_network_id(
            self.ctxt, self.gid, self.network_id)
        self.assertEqual(network["network_id"], self.network_id)

    def test_network_get_by_network_id_exception_notfound(self):
        values = {
            "network_id": "",
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        for i in range(1 - 5):
            values["network_id"] = "network_id" + str(i)
            db.network_create(self.ctxt, values)

        self.assertRaises(exception.NetworkNotFound,
                          db.network_get_by_network_id,
                          context=self.ctxt,
                          gid=self.gid,
                          network_id=self.network_id)

    def test_networks_update(self):
        create_values = {
            "network_id": self.network_id,
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        create_network = db.network_create(self.ctxt, create_values)
        create_network["status"] = "ACTIVE"

        update_values = {
            "status": "ACTIVE"
        }
        db.network_update(self.ctxt, self.network_id, update_values)

        network = db.network_get_by_network_id(
            self.ctxt, self.gid, self.network_id)
        ignored_keys = ['deleted',
                        'deleted_at',
                        'updated_at',
                        'processes']
        self.assertIsNotNone(network["updated_at"])
        self._assertEqualObjects(network, create_network, ignored_keys)

    def test_network_delete(self):
        create_values = {
            "network_id": self.network_id,
            "gid": self.gid,
            "neutron_network_id": "",
            "is_admin": True,
            "subnet": "10.0.0.0/24",
            "ext_router": "",
            "user_id": "user",
            "project_id": "user",
            "display_name": "net-" + self.network_id,
            "status": "BUILDING",
            "deleted": 0
        }
        db.network_create(self.ctxt, create_values)
        deleted_network = db.network_delete(
            self.ctxt, self.gid, self.network_id)
        self.assertEqual(deleted_network["deleted"], 1)
        network_list = db.network_get_all(self.ctxt, self.gid)
        self.assertEqual(network_list, [])


PRIVATE_KEY = ("-----BEGIN RSA PRIVATE KEY-----\nMIIEoAIBA"
               "AKCAQEA6W34Ak32uxp7Oh0rh1mCQclkw+NeqchAOhy"
               "O/rcphFt280D9\nYXxdUa43i51IDS9VpyFFd10Cv4c"
               "cynTPnky82CpGcuXCzaACzI/FHhmBeXTrFoXm\n682"
               "b/8kXVQfCVfSjnvChxeeATjPu9GQkNrgyYyoubHxrr"
               "W7fTaRLEz/Np9CvCq/F\nPJcsx7FwD0adFfmnulbZp"
               "plunqMGKX2nYXbDlLi7Ykjd3KbH1PRJuu+sPYDz3Gm"
               "Z\n4Z0naojOUDcajuMckN8RzNblBrksH8g6NDauoX5"
               "hQa9dyd1q36403NW9tcE6ZwNp\n1GYCnN7/YgI/ugH"
               "o30ptpBvGw1zuY5/+FkU7SQIBIwKCAQA8BlW3cyIwH"
               "MCZ6j5k\nofzsWFu9V7lBmeShOosrji8/Srgv7CPl3"
               "iaf+ZlBKHGc/YsNuBktUm5rw6hRUTyz\nrVUhpHiD8"
               "fBDgOrG4yQPDd93AM68phbO67pmWEfUCU86rJ8aPeB"
               "0t98qDVqz3zyD\nGWwK3vX+o6ao8J/SIu67zpP381d"
               "/ZigDsq+yqhtPpz04YJ2W0w67NV6XSPOV1AX0\nYLn"
               "iHMwfbSTdwJ/wVWoooIgbTo7ldPuBsKUwNIVW8H9tm"
               "apVdyQxAS9JAkr1Y2si\nxKURN4Iez2oyCFv5+P1em"
               "hoptgECr49kpOBAvhRfWWkumgR1azqynzTjSnpQVO6"
               "2\nvQr7AoGBAPkYWJX0tFNlqIWw4tcHtcPHJkRwvLd"
               "PUfM6Q0b6+YctKBmLoNJWBiXr\n39wiYnftSdJO+L9"
               "6HAG38RrmeCfafz19EDPVXepAUYZDwnY1HGx7ZqbiP"
               "wxYMN4C\n+Wg3LzuSh7d5fe409+TCtX4YqSVFQd9gl"
               "8Ml3sKVOTxeaDROw6hFAoGBAO/mdJOr\nSGcAj9V99"
               "df6IX8abZTPm2PmirT95WWwIYX4PRY//5iaCN6XyEK"
               "Ix5TJk9lmcQhS\ntb++PTsXpea01WUcxqaOO3vG7PQ"
               "hvAbpq8A4eMBZZiY9UyctCPNSMscPPNRU2r/C\ntAs"
               "XRk6BNkiGofgn2MY5YBoPkEgiJmJWMKE1AoGAeP0yV"
               "3bbPnM0mLUAdxJfmZs+\neQOO3LF/k2VxInnm6eK7t"
               "KLntp7PyUauj35qV4HiBxBqMR4Nmm9JOPOZcnFxAJv"
               "U\nq3ZDjwlMK0V7tcIGfdWJoYPVewZDnwjCSI/VHO9"
               "mfbAJ91uOWStfd8LV0EY18Cea\nK5YNHK7hSTUrTJt"
               "JFzcCgYB7YJO5qIuir9Txc/rG2Gj/ie82lqevuGSXm"
               "ISaslpi\nJ+Tm3xW8MfXu0bdyrL5pxsEQuFdjXbyOf"
               "xgtBNj6Tl8eDsyQK+QTxWPrRIyV10Ji\n2zbJUoxOL"
               "irDsMLGR4fUFncOHQLJBQwi9gbmi5hCjmHtVlI6DuD"
               "3dbfqlThP1I4J\nwwKBgHfbOPVCgcJA3733J+dBC8g"
               "Lt5QT2fCZ2N7PtaHcsSrW/B9VlGP+tviEC59U\nbmp"
               "OLADzAto1MZdRDr8uXByZ8/eI37Txn6YchMVp43uL2"
               "+WaTdn9GBtOBpWJ0Pqi\nx3HBmILbvIEzB2BX11/PD"
               "NGRMNcCy7edvnFMCxeAiW7DJqCb\n-----END RSA "
               "PRIVATE KEY-----\n")


class KeypairTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(KeypairTestCase, self).setUp()
        self.ctxt = context.get_admin_context()
        self.user_ctxt = context.RequestContext('user', 'user')

    def _get_base_values(self, gid):
        return {
            "keypair_id": "abcdefgh-ijkl-mnop-qrst-uvwxyzabcdef",
            "gid": gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "nova_keypair_id": "nova-test-keypair",
            "private_key": PRIVATE_KEY,
            "display_name": "test_keypair",
            "is_default": True,
            "status": "BUILDING"
        }

    def _create_group(self, gid):
        values = {
            "gid": gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_group",
            "dsplay_description": "This is test group.",
            "is_default": False,
            "status": "ACTIVE"
        }
        return db.group_create(self.user_ctxt, values)

    def _create_keypair(self, gid, values):
        v = self._get_base_values(gid)
        v.update(values)
        return db.keypair_create(self.user_ctxt, v)

    def test_keypair_get_all(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values = [
            {"keypair_id": unicode(uuid.uuid4()),
             "display_name": "test_keypair1"},
            {"keypair_id": unicode(uuid.uuid4()),
             "display_name": "test_keypair2"},
            {"keypair_id": unicode(uuid.uuid4()),
             "display_name": "test_keypair3"},
        ]
        keypairs = [self._create_keypair(gid, value) for value in values]
        expected_keypairs = db.keypair_get_all(self.user_ctxt, gid)
        self._assertEqualListsOfObjects(keypairs, expected_keypairs)

    def test_keypair_get_by_keypair_id(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values = [
            {"keypair_id": unicode(uuid.uuid4()),
             "display_name": "test_keypair1"},
            {"keypair_id": unicode(uuid.uuid4()),
             "display_name": "test_keypair2"},
        ]
        keypairs = [self._create_keypair(gid, value) for value in values]
        expected = db.keypair_get_by_keypair_id(
            self.user_ctxt, gid, values[0]["keypair_id"])
        self._assertEqualObjects(keypairs[0], expected)

    def test_keypair_get_keypair_not_found(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values = self._get_base_values(gid)
        db.keypair_create(self.user_ctxt, values)
        self.assertRaises(exception.KeypairNotFound,
                          db.keypair_get_by_keypair_id,
                          self.user_ctxt, gid, "aaaaa")

    def test_keypair_create(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)

        values = self._get_base_values(gid)
        keypair = db.keypair_create(self.user_ctxt, values)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']
        self._assertEqualObjects(keypair, values, ignored_keys)

    def test_keypair_update(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values_before = self._get_base_values(gid)
        keypair = db.keypair_create(self.user_ctxt, values_before)
        values = {
            "is_default": False,
            "status": "ACTIVE",
        }
        keypair_after = db.keypair_update(
            self.user_ctxt, gid, keypair["keypair_id"], values)
        self.assertEqual(keypair_after["is_default"], False)
        self.assertEqual(keypair_after["status"], "ACTIVE")

    def test_keypair_update_keypair_not_found(self):
        gid = "12345678-1234-5678-9123-123456789012"
        keypair_id = "12345678-1234-5678-9123-123456789012"
        self.assertRaises(exception.KeypairNotFound,
                          db.keypair_update,
                          context=self.user_ctxt,
                          gid=gid,
                          keypair_id=keypair_id,
                          values={})

    def test_keypair_delete(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values_before = self._get_base_values(gid)
        keypair = db.keypair_create(self.user_ctxt, values_before)
        keypair_after = db.keypair_delete(
            self.user_ctxt, gid, keypair["keypair_id"])
        self.assertEqual("DELETING", keypair_after["status"])
        self.assertEqual(1, keypair_after["deleted"])
        self.assertIsNotNone(keypair_after.get("deleted_at"))

    def test_keypair_delete_not_found(self):
        gid = "12345678-1234-5678-9123-123456789012"
        keypair_id = "12345678-1234-5678-9123-123456789012"
        self.assertRaises(exception.KeypairNotFound,
                          db.keypair_delete,
                          context=self.user_ctxt,
                          gid=gid, keypair_id=keypair_id)


class SecuritygroupTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(SecuritygroupTestCase, self).setUp()
        self.ctxt = context.get_admin_context()
        self.user_ctxt = context.RequestContext('user', 'user')

    def _get_base_values(self, gid, securitygroup_id=None):
        return {
            "securitygroup_id": securitygroup_id or "abcdefgh-ijkl-mnop-qrst-"
            "uvwxyzabcdef",
            "gid": gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "neutron_securitygroup_id": securitygroup_id or "neutron-test-"
            "securitygroup",
            "display_name": "test_securitygroup",
            "is_default": True,
            "status": "BUILDING",
            "deleted": 0
        }

    def _create_group(self, gid):
        values = {
            "gid": gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_group",
            "dsplay_description": "This is test group.",
            "is_default": False,
            "status": "ACTIVE",
            "deleted": 0
        }
        return db.group_create(self.user_ctxt, values)

    def test_securitygroup_get_all(self):
        group = self._create_group("gid1")
        securitygroup_ids = ["sc1", "sc2", "sc3"]
        securitygroups = []
        for securitygroup_id in securitygroup_ids:
            securitygroup = db.securitygroup_create(
                self.user_ctxt, self._get_base_values(group["gid"],
                                                      securitygroup_id))
            securitygroups.append(securitygroup)

        res_securitygroups = db.securitygroup_get_all(context, group["gid"])
        ignored_keys = ['deleted_at', 'updated_at', 'created_at']
        self.assertEqual(len(res_securitygroups), len(securitygroups))
        for i in range(0, len(res_securitygroups)):
            self._assertEqualObjects(
                res_securitygroups[i], securitygroups[i], ignored_keys)

    def test_securitygroup_get_all_empty(self):
        res_securitygroups = db.securitygroup_get_all(context, "gid")
        expected = []
        self.assertEqual(res_securitygroups, expected)

    def test_securitygroup_get_by_securitygroup_id(self):
        group = self._create_group("gid1")
        securitygroup_ids = ["sc1", "sc2", "sc3"]
        securitygroups = []
        for securitygroup_id in securitygroup_ids:
            securitygroup = db.securitygroup_create(
                self.user_ctxt, self._get_base_values(group["gid"],
                                                      securitygroup_id))
            securitygroups.append(securitygroup)

        res_securitygroup = db.securitygroup_get_by_securitygroup_id(
            self.user_ctxt, group["gid"], securitygroup_ids[0])
        ignored_keys = ['deleted_at', 'updated_at', 'created_at', 'processes']
        self._assertEqualObjects(
            res_securitygroup, securitygroups[0], ignored_keys)

    def test_securitygroup_get_by_securitygroup_id_not_found(self):
        try:
            db.securitygroup_get_by_securitygroup_id(
                self.user_ctxt, "gid", "sec")
        except Exception as e:
            status_code = e.code
        self.assertEqual(status_code, 404)

    def test_securitygroup_create(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)

        values = self._get_base_values(gid)
        securitygroup = db.securitygroup_create(self.user_ctxt, values)
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']
        self._assertEqualObjects(securitygroup, values, ignored_keys)

    def test_securitygroup_update(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values_before = self._get_base_values(gid)
        securitygroup = db.securitygroup_create(self.user_ctxt, values_before)
        values = {
            "is_default": False,
            "status": "ACTIVE",
        }
        securitygroup_after = db.securitygroup_update(
            self.user_ctxt, gid, securitygroup["securitygroup_id"], values)
        self.assertEqual(securitygroup_after["is_default"], False)
        self.assertEqual(securitygroup_after["status"], "ACTIVE")

    def test_securitygroup_update_securitygroup_not_found(self):
        gid = "12345678-1234-5678-9123-123456789012"
        securitygroup_id = "12345678-1234-5678-9123-123456789012"
        self.assertRaises(exception.SecuritygroupNotFound,
                          db.securitygroup_update,
                          context=self.user_ctxt,
                          gid=gid,
                          securitygroup_id=securitygroup_id,
                          values={})

    def test_securitygroup_delete(self):
        gid = "12345678-1234-5678-9123-123456789012"
        self._create_group(gid)
        values_before = self._get_base_values(gid)
        securitygroup = db.securitygroup_create(self.user_ctxt, values_before)
        securitygroup_after = db.securitygroup_delete(
            self.user_ctxt, gid, securitygroup["securitygroup_id"])
        self.assertEqual("DELETING", securitygroup_after["status"])
        self.assertEqual(1, securitygroup_after["deleted"])
        self.assertIsNotNone(securitygroup_after.get("deleted_at"))

    def test_securitygroup_delete_not_found(self):
        gid = "12345678-1234-5678-9123-123456789012"
        securitygroup_id = "12345678-1234-5678-9123-123456789012"
        self.assertRaises(exception.SecuritygroupNotFound,
                          db.securitygroup_delete,
                          context=self.user_ctxt,
                          gid=gid, securitygroup_id=securitygroup_id)


class ProcessTestCase(test.TestCase, ModelsObjectComparatorMixin):

    def setUp(self):
        super(ProcessTestCase, self).setUp()
        self.ctxt = context.get_admin_context()
        self.user_ctxt = context.RequestContext('user', 'user')
        self.gid = unicode(uuid.uuid4())
        self.group = self._create_group(self.gid)
        self.network = self._create_network(self.gid)
        self.keypair = self._create_keypair(self.gid)
        self.securitygroup = self._create_securitygroup(self.gid)

    def _get_base_values(self):
        return {
            "pid": unicode(uuid.uuid4()),
            "ppid": unicode(uuid.uuid4()),
            "nova_instance_id": unicode(uuid.uuid4()),
            "glance_image_id": unicode(uuid.uuid4()),
            "nova_flavor_id": 1,
            "keypair_id": self.keypair["keypair_id"],
            "gid": self.gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_process",
            "status": "BUILDING",
            "deleted": 0,
            "is_proxy": False,
            "app_status": "BUILDING",
            "shm_endpoint": None,
            "ipc_endpoint": None,
            "fs_endpoint": None,
            "args": None,
            "userdata": None
        }

    def _create_group(self, gid):
        values = {
            "gid": gid,
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_group",
            "dsplay_description": "This is test group.",
            "is_default": False,
            "status": "ACTIVE",
            "deleted": 0
        }
        return db.group_create(self.user_ctxt, values)

    def _create_network(self, gid):
        values = {
            "gid": gid,
            "network_id": unicode(uuid.uuid4()),
            "ext_router": unicode(uuid.uuid4()),
            "subnet": "10.0.0.1/24",
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_network",
            "is_admin": False,
            "status": "ACTIVE",
            "deleted": 0
        }
        return db.network_create(self.user_ctxt, values)

    def _create_keypair(self, gid):
        values = {
            "gid": gid,
            "keypair_id": unicode(uuid.uuid4()),
            "private_key": "test",
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_keypair",
            "is_default": False,
            "status": "ACTIVE",
            "deleted": 0
        }
        return db.keypair_create(self.user_ctxt, values)

    def _create_securitygroup(self, gid):
        values = {
            "gid": gid,
            "securitygroup_id": unicode(uuid.uuid4()),
            "user_id": self.user_ctxt.user_id,
            "project_id": self.user_ctxt.project_id,
            "display_name": "test_securitygroup",
            "is_default": False,
            "status": "ACTIVE",
            "deleted": 0
        }
        return db.securitygroup_create(self.user_ctxt, values)

    def _create_process(self, gid, create_count):
        processes = []
        for i in range(0, create_count):
            process = db.process_create(
                self.user_ctxt,
                self._get_base_values(),
                [self.network["network_id"]],
                [self.securitygroup["securitygroup_id"]])
            processes.append(process)
        return processes

    def test_process_get_all(self):
        processes = self._create_process(self.gid, 3)
        res_processes = db.process_get_all(context, self.gid)
        ignored_keys = ['deleted_at', 'updated_at', 'created_at']
        self.assertEqual(len(res_processes), len(processes))
        for i in range(0, len(res_processes)):
            self._assertEqualObjects(
                res_processes[i], processes[i], ignored_keys)

    def test_process_get_all_empty(self):
        res_processes = db.process_get_all(context, self.gid)
        expected = []
        self.assertEqual(res_processes, expected)

    def test_process_get_by_pid(self):
        processes = self._create_process(self.gid, 3)
        res_process = db.process_get_by_pid(
            self.user_ctxt, self.gid, processes[0]["pid"])
        ignored_keys = ['deleted_at', 'updated_at', 'created_at']
        self._assertEqualObjects(res_process, processes[0], ignored_keys)

    def test_process_get_by_pid_not_found(self):
        try:
            db.process_get_by_pid(self.user_ctxt, self.gid, "notfound-pid")
        except Exception as e:
            status_code = e.code
        self.assertEqual(status_code, 404)

    def test_process_create(self):
        values = self._get_base_values()
        process = db.process_create(self.user_ctxt,
                                    values,
                                    [self.network["network_id"]],
                                    [self.securitygroup["securitygroup_id"]])

        values["networks"] = [self.network]
        values["securitygroups"] = [self.securitygroup]
        ignored_keys = ['deleted', 'deleted_at', 'updated_at',
                        'created_at']

        self._assertEqualObjects(process, values, ignored_keys)

    def test_process_create_duplicated_network_id(self):
        values = self._get_base_values()
        try:
            db.process_create(self.user_ctxt,
                              values,
                              [self.network["network_id"],
                                  self.network["network_id"]],
                              [self.securitygroup["securitygroup_id"]])
        except exception.InvalidInput as e:
            status_code = e.code
        self.assertEqual(status_code, 400)

    def test_process_create_duplicated_securitygroup_id(self):
        values = self._get_base_values()
        try:
            db.process_create(self.user_ctxt,
                              values,
                              [self.network["network_id"]],
                              [self.securitygroup["securitygroup_id"],
                               self.securitygroup["securitygroup_id"]])
        except exception.InvalidInput as e:
            status_code = e.code
        self.assertEqual(status_code, 400)

    def test_process_update(self):
        values_before = self._get_base_values()
        process = db.process_create(self.user_ctxt,
                                    values_before,
                                    [self.network["network_id"]],
                                    [self.securitygroup["securitygroup_id"]])
        values = {
            "display_name": "test",
            "status": "ACTIVE",
        }
        process_after = db.process_update(
            self.user_ctxt, self.gid, process["pid"], values)
        self.assertEqual(process_after["display_name"], "test")
        self.assertEqual(process_after["status"], "ACTIVE")

    def test_process_update_process_not_found(self):
        self.assertRaises(exception.ProcessNotFound,
                          db.process_update,
                          context=self.user_ctxt,
                          gid=self.gid,
                          pid=unicode(uuid.uuid4()),
                          values={})

    def test_process_delete(self):
        values_before = self._get_base_values()
        process = db.process_create(self.user_ctxt,
                                    values_before,
                                    [self.network["network_id"]],
                                    [self.securitygroup["securitygroup_id"]])
        process_after = db.process_delete(
            self.user_ctxt, self.gid, process["pid"])
        self.assertEqual("DELETING", process_after["status"])
        self.assertEqual(1, process_after["deleted"])
        self.assertIsNotNone(process_after.get("deleted_at"))

    def test_process_delete_not_found(self):
        self.assertRaises(exception.ProcessNotFound,
                          db.process_delete,
                          context=self.user_ctxt,
                          gid=self.gid, pid=unicode(uuid.uuid4()))
