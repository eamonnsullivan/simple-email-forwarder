import unittest
import logging
from SimpleForwarder import SESForwarderError

class testSESForwarderError(unittest.TestCase):

    def setUp(self):
        self._exception = SESForwarderError("Test Error")

    def test_str_ok(self):
        self.assertEqual("'Test Error'", str(self._exception))

if __name__ == '__main__':
    unittest.main()
