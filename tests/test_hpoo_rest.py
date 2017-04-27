import unittest

from mock import Mock

from oo_client.hpoo import OORestCaller

import oo_client.errors as errors

import requests


class TestHPOORest(unittest.TestCase):
    def setUp(self):
        self.mock_reqs = Mock()
        requests.Session = self.mock_reqs

    def test_post(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'post.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        ret = rest.post('some-path')
        url = "https://blah:1234/oo/rest/v1/some-path"
        mock_session.post.assert_called_with(url, None)
        self.assertEquals(ret, {'aaa': 'aaa'})

    def test_post_file(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'post.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        ret = rest.post('some-path', files=['some_file', 'some_other_file'])
        url = "https://blah:1234/oo/rest/v1/some-path"
        mock_session.post.assert_called_with(url,
                                             files=['some_file',
                                                    'some_other_file'])
        self.assertEquals(ret, {'aaa': 'aaa'})

    def test_post_json(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'post.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        ret = rest.post('some-path', data={'some': 'data'})
        url = "https://blah:1234/oo/rest/v1/some-path"
        mock_session.post.assert_called_with(url,
                                             '{"some": "data"}')
        self.assertEquals(ret, {'aaa': 'aaa'})

    def test_post_error(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'post.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        with self.assertRaises(errors.HTTPNon200):
            rest.post('some-path', Mock())

    def test_put(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'put.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        mock_data = Mock()
        rest.put('some-path', mock_data)
        url = "https://blah:1234/oo/rest/v1/some-path"
        mock_session.put.assert_called_with(url, mock_data)

    def test_put_error(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'put.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        with self.assertRaises(errors.HTTPNon200):
            rest.put('some-path', Mock())

    def test_get(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '{"aaa": "aaa"}'
        mock_response.headers = {}
        mock_config = {'get.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        assert rest.session.auth == ("aa", "bb")
        assert rest.session.verify is True
        ret = rest.get('some-path')
        self.assertEquals(ret, {'aaa': 'aaa'})
        url = "https://blah:1234/oo/rest/v1/some-path"
        mock_session.get.assert_called_with(url, params={})

    def test_get_error(self):
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = '{"aaa": "aaa"}'
        mock_config = {'get.return_value': mock_response}
        mock_session.configure_mock(**mock_config)
        self.mock_reqs.return_value = mock_session
        rest = OORestCaller("https://blah:1234", "aa", "bb")
        with self.assertRaises(errors.HTTPNon200):
            rest.get('some-path')

    def tearDown(self):
        pass
