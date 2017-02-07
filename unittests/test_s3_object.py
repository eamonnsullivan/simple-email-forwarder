import unittest
import logging
from SimpleForwarder import S3Object, SESForwarderError
from mock import Mock, MagicMock
from StringIO import StringIO
from botocore.exceptions import ClientError
from test_util import *

class testS3Object(unittest.TestCase):

    def setUp(self):
        self._s3_mock = Mock()
        get_mock = MagicMock()
        read_dict = {'Body': MagicMock(spec=file, wraps=StringIO(TEST_EMAIL_BODY))}
        get_mock.__getitem__.side_effect = read_dict.__getitem__
        self._s3_mock.Object.return_value.get.return_value = get_mock
        self._bucket = "bucket"
        self._id = "some-id"

    def test_get_ok(self):
        testObj = S3Object(self._s3_mock,
                           self._bucket,
                           self._id)
        result = testObj.get('Body')
        self.assertEqual(result, TEST_EMAIL_BODY)

    def test_get_ko(self):
        s3_mock = Mock(side_effect=ClientError(ERROR_RESPONSE,'operation_name'))
        get_mock = MagicMock()
        read_dict = {'Body': MagicMock(spec=file, wraps=StringIO(TEST_EMAIL_BODY))}
        get_mock.__getitem__.side_effect = read_dict.__getitem__
        s3_mock.Object.return_value.get.return_value = get_mock
        s3_mock.Object.return_value.get.side_effect = ClientError(ERROR_RESPONSE,'operation_name')
        testObj = S3Object(s3_mock,
                           self._bucket,
                           self._id)
        self.assertRaises(SESForwarderError, testObj.get, 'Body')

    def test_get_bucket(self):
        testObj = S3Object(self._s3_mock,
                           self._bucket,
                           self._id)
        self.assertEqual(testObj.get_bucket(), "bucket")

    def test_get_id(self):
        testObj = S3Object(self._s3_mock,
                           self._bucket,
                           self._id)
        self.assertEqual(testObj.get_id(), "some-id")


if __name__ == '__main__':
    unittest.main()
