import unittest
from mock import Mock, patch, call
from oo_client.hpoo import OOClient
import oo_client.errors as errors


class TestHPOO(unittest.TestCase):
    """Unittest tool for hpoo"""

    def setUp(self):
        pass

    @patch('oo_client.hpoo.OORestCaller.put')
    @patch('oo_client.hpoo.OORestCaller.get')
    @patch('__builtin__.open')
    def test_deploy_content_pack(self, mock_open, mock_get, mock_put):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_cp = mock_open()
        mock_response = Mock()
        mock_response = {"contentPackResponses": {"dummy.jar":
                         {"responses": [{"responseCategory": "Success",
                                         "message": "lolol"}]}}}
        mock_put.return_value = mock_response
        ret = client.deploy_content_pack('/path/to/dummy.jar')
        client.rest.put.assert_called_with("content-packs/dummy",
                                           mock_cp.__enter__())
        self.assertTrue(ret)
        mock_response = {"contentPackResponses": {"dummy.jar":
                         {"responses": [{"responseCategory": "FAIL",
                                         "message": "lolol"}]}}}
        mock_put.return_value = mock_response
        ret = client.deploy_content_pack('/path/to/dummy.jar')
        self.assertFalse(ret)

    @patch('oo_client.hpoo.OORestCaller.post')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_new_deployment(self, mock_get, mock_post):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_response = Mock()
        mock_response = {"deploymentProcessId": 1234}
        mock_config = {'return_value': mock_response}
        mock_post.configure_mock(**mock_config)
        ret = client.get_new_deployment()
        self.assertEqual(ret, 1234)

    @patch('oo_client.hpoo.OOClient.wait_for_deployment_to_complete')
    @patch('oo_client.hpoo.OORestCaller.put')
    @patch('oo_client.hpoo.OORestCaller.post')
    @patch('oo_client.hpoo.OORestCaller.get')
    @patch('__builtin__.open')
    @patch('oo_client.hpoo.OOClient.get_new_deployment')
    def test_deploy_content_packs(self, mock_get_dep, mock_open, mock_get,
                                  mock_post, mock_put, mock_wait):
        mock_get_dep.return_value = 1234
        mock_cp = mock_open()
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_response = {"contentPackResponses":
                         {"dummy.jar":
                          {"responses": [{"responseCategory": "Success",
                                          "message": "lolol"}]},
                          "not.jar":
                          {"responses": [{"responseCategory": "Success",
                                          "message": "lolol"}]}}}
        mock_wait.return_value = mock_response
        ret = client.deploy_content_packs(['/some/dummy.jar',
                                           '/another/not.jar'])
        first_cp = call("deployments/1234/files",
                        files={'file': ('dummy.jar',
                                        mock_cp.__enter__())})
        second_cp = call("deployments/1234/files",
                         files={'file': ('not.jar',
                                         mock_cp.__enter__())})
        client.rest.post.assert_has_calls([first_cp, second_cp])
        mock_wait.assert_called_with(1234, 3600, 5)
        mock_put.assert_called_with('deployments/1234', None)
        self.assertTrue(ret)
        mock_response = {"contentPackResponses":
                         {"dummy.jar":
                          {"responses": [{"responseCategory": "Success",
                                          "message": "lolol"}]},
                          "not.jar":
                          {"responses": [{"responseCategory": "NotASuccess",
                                         "message": "lolol"}]}}}
        mock_wait.return_value = mock_response
        ret = client.deploy_content_packs(['/some/dummy.jar',
                                           '/another/not.jar'])
        self.assertFalse(ret)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_is_deployment_complete(self, mock_get):
        mock_get.return_value = {'status': 'FINISHED',
                                 'deploymentResultVO': 'OBJECTblah'}
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.is_deployment_complete(5555)
        mock_get.assert_called_with('deployments/5555')
        self.assertEqual(ret, 'OBJECTblah')
        mock_get.return_value = {'status': 'PAUSED',
                                 'deploymentResultVO': 'OBJECTblah'}
        ret = client.is_deployment_complete(5555)
        self.assertFalse(ret)

    @patch('oo_client.hpoo.OORestCaller.post')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_run_flow_async(self, mock_get, mock_post):
        mock_ret = Mock()
        mock_post.return_value = mock_ret
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.run_flow_async('f1739b66-a586-44dc-942a-479caaecec34',
                                    run_name='some-name',
                                    inputs={'an': 'input'})
        mock_payload = {'uuid': 'f1739b66-a586-44dc-942a-479caaecec34',
                        'runName': 'some-name',
                        'inputs': {'an': 'input'}}
        client.rest.post.assert_called_with('executions', data=mock_payload)
        self.assertEqual(ret, mock_ret)

    @patch('oo_client.hpoo.OOClient.get_flow_uuid_from_path')
    @patch('oo_client.hpoo.OORestCaller.post')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_run_flow_async_by_path(self, mock_get, mock_post, mock_get_flow):
        mock_ret = Mock()
        mock_post.return_value = mock_ret
        mock_get_flow.return_value = 'the-uuid'
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.run_flow_async('Some/flow/path',
                                    run_name='some-name',
                                    inputs={'an': 'input'})
        mock_get_flow.assert_called_with('Some/flow/path')
        mock_payload = {'uuid': 'the-uuid',
                        'runName': 'some-name',
                        'inputs': {'an': 'input'}}
        client.rest.post.assert_called_with('executions', data=mock_payload)
        self.assertEqual(ret, mock_ret)

    @patch('oo_client.hpoo.OOClient.get_run_result_type')
    @patch('oo_client.hpoo.OOClient.get_run_status')
    @patch('oo_client.hpoo.OOClient.wait_for_run_to_complete')
    @patch('oo_client.hpoo.OOClient.run_flow_async')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_run_flow(self, mock_get, mock_run, mock_wait, mock_get_s,
                      mock_get_r):
        mock_run.return_value = {'executionId': 345}
        mock_get_s.return_value = 'COMPLETED'
        mock_get_r.return_value = 'result'
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.run_flow('Some/flow/path',
                              run_name='some-name',
                              inputs={'an': 'input'})
        mock_wait.assert_called_with(345, 300, 5)
        mock_get_s.assert_called_with(345)
        mock_get_r.assert_called_with(345)
        self.assertEqual(ret, 'result')
        mock_get_s.return_value = 'FAIL'
        ret = client.run_flow('Some/flow/path',
                              run_name='some-name',
                              inputs={'an': 'input'})
        self.assertIsNone(ret)

    @patch('oo_client.hpoo.OOClient.run_flow')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_run_flows(self, mock_get, mock_run_flow):
        mock_run_flow.side_effect = ['RESOLVED', 'RESOLVED']
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.run_flows(['Some/flow/path', 'Other/flow/path'])
        self.assertTrue(ret)
        mock_run_flow.side_effect = ['RESOLVED', 'ERROR']
        ret = client.run_flows(['Some/flow/path', 'Other/flow/path'])
        self.assertFalse(ret)

    @patch('oo_client.hpoo.OOClient.get_run_status')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_is_run_complete(self, mock_get, mock_get_run_status):
        mock_get_run_status.return_value = 'COMPLETED'
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.is_run_complete(12345)
        mock_get_run_status.assert_called_with(12345)
        self.assertTrue(ret)
        mock_get_run_status.return_value = 'PENDING'
        ret = client.is_run_complete(12345)
        self.assertFalse(ret)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_flow_uuid_from_path(self, mock_get):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_get.return_value = [{'id': 123, 'name': 'a_flow'},
                                 {'id': 456, 'name': 'a_nother_flow'}]
        ret = client.get_flow_uuid_from_path('path/to/a_flow')
        mock_get.assert_called_with('flows/tree/level', path='path/to')
        self.assertEqual(ret, 123)
        with self.assertRaises(errors.NotFound):
            client.get_flow_uuid_from_path('path/to/not_a_flow')

    @patch('oo_client.hpoo.OOClient.get_run_summary')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_run_status(self, mock_get, mock_get_run_s):
        mock_get_run_s.return_value = {'status': 'spam'}
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_run_status(666)
        mock_get_run_s.assert_called_with(666)
        self.assertEqual(ret, 'spam')

    @patch('oo_client.hpoo.OOClient.get_run_summary')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_run_result_type(self, mock_get, mock_get_run_s):
        mock_get_run_s.return_value = {'resultStatusType': 'eggs'}
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_run_result_type(666)
        mock_get_run_s.assert_called_with(666)
        self.assertEqual(ret, 'eggs')

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_run_summary(self, mock_get):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_get.return_value = ['some']
        ret = client.get_run_summary(123)
        mock_get.assert_called_with('executions/123/summary')
        self.assertEqual(ret, 'some')
        mock_get.return_value = []
        with self.assertRaises(errors.NotFound):
            client.get_flow_uuid_from_path('path/to/not_a_flow')

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_content_pack_id(self, mock_get):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_get.return_value = [{'id': 123, 'name': 'a_cp'},
                                 {'id': 456, 'name': 'a_nother_cp'}]
        ret = client.get_content_pack_id('a_cp')
        mock_get.assert_called_with('content-packs')
        self.assertEqual(ret, 123)
        with self.assertRaises(errors.NotFound):
            client.get_flow_uuid_from_path('not_a_cp')

    @patch('oo_client.hpoo.OOClient.get_flow_uuid_from_path')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_content_pack_from_flow(self, mock_get, mock_get_flow):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_get.return_value = {'cpName': 'my-cp'}
        mock_get_flow.return_value = 'uuidLOL'
        ret = client.get_content_pack_from_flow('Some/path/to/flow')
        mock_get.assert_called_with('flows/uuidLOL')
        self.assertEqual(ret, 'my-cp')

    @patch('oo_client.hpoo.OORestCaller.get')
    @patch('oo_client.hpoo.OOClient.get_content_pack_id')
    def test_get_all_flows_in_cp(self, mock_get_content, mock_get):
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_get_content.return_value = 1234
        mock_get.return_value = [{'id': 123, 'path': 'some/path/to/flow',
                                  'type': 'FLOW'},
                                 {'id': 456, 'path': 'another/flow',
                                  'type': 'FLOW'},
                                 {'id': 666, 'path': 'another/op',
                                  'type': 'OPERATION'}]
        ret = client.get_all_flows_in_cp('my-cp')
        mock_get_content.assert_called_with('my-cp')
        mock_get.assert_called_with('content-packs/1234/content-tree')
        expected = {123: 'some/path/to/flow', 456: 'another/flow'}
        self.assertEqual(ret, expected)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_name_value_pair(self, mock_get):
        mock_get.return_value = Mock()
        client = OOClient("https://blah:1234", "aa", "bb")
        mock_input = {"name": "sa1",
                      "value": "{\"username\":\"yf5\",\"password\":\"************\"}",
                      "path": "sa1",
                      "type": "system-accounts",
                      "uuid": "ebe1e757-46de-4c68-abd6-d41141ed76c2"}
        expected = {"name": "sa1",
                    "value": "{\"username\":\"yf5\",\"password\":\"************\"}"}
        ret = client.get_name_value_pair(mock_input)
        self.assertEqual(ret, expected)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_a_configuration_item(self, mock_get):
        # system-accounts
        mock_input = {"name": "sa1",
                      "value": "{\"username\":\"yf5\",\"password\":\"************\"}",
                      "path": "sa1",
                      "type": "system-accounts",
                      "uuid": "ebe1e757-46de-4c68-abd6-d41141ed76c2"}
        mock_get.return_value = mock_input
        mock_ret = {"name": "sa1",
                    "value": "{\"username\":\"yf5\",\"password\":\"************\"}"}
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_a_configuration_item('system-accounts', 'some/path')
        mock_get.assert_called_with('config-items/system-accounts/some/path')
        self.assertEqual(ret, mock_ret)
        # system-properties
        mock_input = {"name": "sp1",
                      "value": "blah",
                      "path": "sp1",
                      "type": "system-properties",
                      "uuid": "ebe1e757-46de-4c68-abd6-d41141ed76c2"}
        mock_get.return_value = mock_input
        mock_ret = {"name": "sp1",
                    "value": "blah"}
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_a_configuration_item('system-properties', 'sp1')
        mock_get.assert_called_with('config-items/system-properties/sp1')
        self.assertEqual(ret, mock_ret)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_all_configuration_item(self, mock_get):
        mock_input = [{"type": "selection-lists",
                       "path": "some/path",
                       "name": "Yes No",
                       "value": "Yes|No",
                       "uuid": "somesequence"},
                      {"type": "selection-lists",
                       "name": "Yes No - No Default",
                       "path": "some/path",
                       "value": "No|Yes",
                       "uuid": "somesequence"},
                      {"type": "group-aliases",
                       "name": "RAS_Operator_Path",
                       "path": "some/path",
                       "value": "RAS_Operator_Path",
                       "uuid": "somesequence"},
                      {"type": "system-accounts",
                       "name": "sa1",
                       "path": "some/path",
                       "uuid": "somesequence",
                       "value": "{\"username\":\"yf5\",\"password\":\"************\"}"}]
        mock_get.return_value = mock_input
        mock_ret = [{"type": "selection-lists",
                     "name": "Yes No",
                     "value": "Yes|No"},
                    {"type": "selection-lists",
                     "name": "Yes No - No Default",
                     "value": "No|Yes"},
                    {"type": "group-aliases",
                     "name": "RAS_Operator_Path",
                     "value": "RAS_Operator_Path"},
                    {"type": "system-accounts",
                     "name": "sa1",
                     "value": "{\"username\":\"yf5\",\"password\":\"************\"}"}]
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_all_configuration_items()
        mock_get.assert_called_with('config-items')
        self.assertEqual(ret, mock_ret)

    @patch('oo_client.hpoo.OORestCaller.get')
    def test_get_configuration_items_by_type(self, mock_get):
        mock_input = [{"type": "selection-lists",
                       "path": "some/path",
                       "name": "Yes No",
                       "value": "Yes|No",
                       "uuid": "somesequence"},
                      {"type": "selection-lists",
                       "name": "Yes No - No Default",
                       "path": "some/path",
                       "value": "No|Yes",
                       "uuid": "somesequence"}]
        mock_get.return_value = mock_input
        mock_ret = [{"name": "Yes No",
                     "value": "Yes|No"},
                    {"name": "Yes No - No Default",
                     "value": "No|Yes"}]
        client = OOClient("https://blah:1234", "aa", "bb")
        ret = client.get_configuration_items_by_type("selection-lists")
        mock_get.assert_called_with('config-items/selection-lists')
        self.assertEqual(ret, mock_ret)
        # system-accounts
        mock_input = [{"type": "system-accounts",
                       "name": "sa1",
                       "path": "some/path",
                       "uuid": "somesequence",
                       "value": "{\"username\":\"yf5\",\"password\":\"************\"}"},
                      {"type": "system-accounts",
                       "name": "sa2",
                       "path": "some/other/path",
                       "uuid": "somesequence",
                       "value": "{\"username\":\"yf6\",\"password\":\"************\"}"}]
        mock_get.return_value = mock_input
        mock_ret = [{"name": "sa1",
                     "value": "{\"username\":\"yf5\",\"password\":\"************\"}"},
                    {"name": "sa2",
                     "value": "{\"username\":\"yf6\",\"password\":\"************\"}"}]
        ret = client.get_configuration_items_by_type("system-accounts")
        mock_get.assert_called_with('config-items/system-accounts')
        self.assertEqual(ret, mock_ret)

    @patch('oo_client.hpoo.OORestCaller.put')
    @patch('oo_client.hpoo.OORestCaller.get')
    def test_set_a_configuration_item(self, mock_get, mock_put):
        mock_get.return_value = ['some']
        client = OOClient("https://blah:1234", "aa", "bb")
        # system-accounts
        mock_data = '"{\\"username\\": \\"blah\\", \\"password\\": \\"password\\"}"'
        mock_put_ret = {u'customValue': u'{"username":"blah","password":"************"}', u'name': u'sa1', u'defaultValue': u'{"username":"username","password":null}', u'value': u'{"username":"blah","password":"************"}', u'path': u'sa1', u'fullPath': u'Configuration/System Accounts/sa1.xml', u'type': u'system-accounts', u'uuid': u'ebe1e757-46de-4c68-abd6-d41141ed76c2'}
        mock_ret = {'name': u'sa1', 'value': u'{"username":"blah","password":"************"}'}
        mock_put.return_value = mock_put_ret
        ret = client.set_a_configuration_item('system-accounts', 'sa1', 'blah:password')
        mock_put.assert_called_with('config-items/system-accounts/sa1', mock_data)
        self.assertEqual(ret, mock_ret)
        # system-properties
        mock_data = '"blah"'
        mock_put_ret = {u'customValue': u'blah', u'name': u'sp1', u'defaultValue': u'', u'value': u'blah', u'path': u'sp1', u'fullPath': u'Configuration/System Properties/sp1.xml', u'type': u'system-properties', u'uuid': u'0c755cf0-67b6-4264-bfd9-7a880e280a73'}
        mock_ret = {'name': u'sp1', 'value': u'blah'}
        mock_put.return_value = mock_put_ret
        ret = client.set_a_configuration_item('system-properties', 'sp1', 'blah')
        mock_put.assert_called_with('config-items/system-properties/sp1', mock_data)
        self.assertEqual(ret, mock_ret)


def tearDown(self):
        pass
