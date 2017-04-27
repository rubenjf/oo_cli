import unittest

from mock import Mock, patch

from oo_client.hpoo_tester import IntegrationTester
import oo_client.errors as errors


class TestHPOOTester(unittest.TestCase):
    def setUp(self):
        pass

    def test_filter_flows(self):
        mock_client = Mock()
        it = IntegrationTester(mock_client, 'path/to_tests/test_')
        ret = it.filter_flows(['some/path/to/flow', 'another/path/to/flow'],
                              'some')
        self.assertEqual(ret, ['some/path/to/flow'])

    @patch('oo_client.hpoo_tester.IntegrationTester.filter_flows')
    def test_run_tests(self, mock_filter):
        mock_client = Mock()
        it = IntegrationTester(mock_client, 'some')
        flows = {123: 'some/path/to/flow', 456: 'another/path/to/flow'}
        mock_filter.return_value = ['some/path/to/flow']
        mock_client.get_all_flows_in_cp.return_value = flows
        mock_client.run_flows.return_value = True
        ret = it.run_tests('my-cp')
        mock_client.get_all_flows_in_cp.assert_called_with('my-cp')
        mock_filter.assert_called_with(['another/path/to/flow',
                                        'some/path/to/flow'],
                                       'some')
        mock_client.run_flows.assert_called_with(['some/path/to/flow'],
                                                 timeout=300)
        self.assertTrue(ret)
        with self.assertRaises(errors.NoFlowsFound):
            mock_filter.return_value = []
            ret = it.run_tests('my-cp')

    def tearDown(self):
        pass
