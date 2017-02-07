import unittest
import logging
from StringIO import StringIO
from SimpleForwarder import *
from mock import Mock, MagicMock
from botocore.exceptions import ClientError
from test_util import *
import copy

class testSESEmail(unittest.TestCase):

    def setUp(self):
        self._ses_mock = Mock()
        self._ses_mock.send_raw_email.return_value = {
        'MessageId': 'some_message_id'
        }
        self._s3_mock = Mock()
        self._read_dict = {'Body': MagicMock(spec=file, wraps=StringIO(TEST_EMAIL_BODY))}
        self._get_mock = MagicMock()
        self._get_mock.__getitem__.side_effect = self._read_dict.__getitem__
        self._s3_mock.Object.return_value.get.return_value = self._get_mock
    
    def test_event_ok(self):
        self.assertIsNone(lambda_handler(TEST_EVENT, {},
                                         self._ses_mock,
                                         self._s3_mock,
                                         TEST_CONFIG))

        destinations = self._ses_mock.send_raw_email.call_args[1]['Destinations']
        original = self._ses_mock.send_raw_email.call_args[1]['Source']
        raw_message = self._ses_mock.send_raw_email.call_args[1]['RawMessage']['Data']

        self.assertTrue('user1@example.com' in destinations)
        self.assertTrue('user2@example.com' in destinations)
        self.assertTrue('user3@example.com' in destinations)

        self.assertTrue('info@example.com' in original)
        self.assertEqual(TEST_SEND_EMAIL, raw_message)

    def test_no_config(self):
        self.assertIsNone(lambda_handler(TEST_EVENT, {},
                                         self._ses_mock,
                                         self._s3_mock))

        self.assertFalse(self._ses_mock.send_raw_email.called)

if __name__ == '__main__':
    unittest.main()
