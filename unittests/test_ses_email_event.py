import unittest
from SimpleForwarder import SESEmailEvent, SESForwarderError
from test_util import TEST_EVENT

class testSESEmailEvent(unittest.TestCase):

    def setUp(self):
        self.test = SESEmailEvent(TEST_EVENT)
    
    def test_get_email(self):
        email = self.test.get_email()
        expected = {
            "source": "someone@somedomain.com",
            "messageId": "3bnsm1c2akm1gded3speted0hpnglijt74jbd201",
            "destination": [
                "info@example.com"
            ],
            "headers": [],
            "commonHeaders": {}
        }
        self.assertEqual(email, expected)

    def test_get_recipients(self):
        recipients = self.test.get_recipients()
        expected = ['info@example.com', 'members@example.com']
        self.assertEqual(recipients, expected)

    def test_invalid_event(self):
        invalid = TEST_EVENT['eventVersion'] = '2.0'
        self.assertRaises(SESForwarderError, SESEmailEvent, invalid)
    

if __name__ == '__main__':
    unittest.main()        
