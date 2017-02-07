import unittest
import logging
from SimpleForwarder import SESSender, SESForwarderError
from mock import Mock
from test_util import *

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

class testSESSender(unittest.TestCase):

    def setUp(self):
        ses_mock = Mock()
        ses_mock.send_raw_email.return_value = {
            'MessageId': 'some_message_id'
        }
        self.sender = SESSender(ses_mock, LOGGER)
        self.recipients = ['a@b', 'c@d']
        self.original = ['z@y']
        
    def test_send_ok(self):
        self.sender.set_email(TEST_SEND_EMAIL)
        result = self.sender.send(self.recipients, self.original[0])
        self.assertEqual(result, {'MessageId': 'some_message_id'})

    def test_send_ko(self):
        self.assertRaises(SESForwarderError,
                          self.sender.send,
                          self.recipients,
                          self.original[0])

    def test_set_email(self):
        self.sender.set_email(TEST_SEND_EMAIL)
        self.assertEqual(TEST_SEND_EMAIL, self.sender.get_email())
    

if __name__ == '__main__':
    unittest.main()        
