import unittest
import logging
from StringIO import StringIO
from SimpleForwarder import *
from mock import Mock, MagicMock
from botocore.exceptions import ClientError
from test_util import *
import copy

EMAIL_WITH_REPLY_TO = """Return-Path: <someone@someplace.com>\r
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\r
        d=gmail.com; s=20161025;\r
        h=mime-version:from:date:message-id:subject:to;\r
        bh=4c9vZm70ItvTkbMF9HikO6KKWJl5M95+W6HmkZxAYA0=;\r
        b=LUsCaJ4FEtgn0IYraRp5+iB2SDwwJ1wcTrgzdIyBqpYJNSaA0X0L6vweduQ7szGID9\r
         1vzYdqYgjoiyusVTEaNlZZq1Y0IseIUdlFhrR8oyYsSPgWDvSb5fHcXZzQrw0MKojakm\r
         1uQsHjiGYyLJZiDbg37g2O2FOah5imBRKsCd+xCy7bpFdhS3tuVtxUOZ1W0uXRd2PKB2\r
         DlLgfMtcpliGskJp4G6Kvv+BfSI835fULU0gITzL5wIt6YheL9Qu5ZKfQX94wpIRI5uj\r
         3o+jmMMCNWQWw/5Kt/2Y6Te4zHOS2cqoaZdlzCwokN3cX6fmfGXiuC6MJO/LNN3/cPH5\r
         SPIA==\r
From: Some One <someone@someplace.com>\r
Subject: Testing for event format\r
To: info@example.com\r
Reply-To: <test@example.com>\r
\r
Test message.\r
"""

EMAIL_WITH_BORKED_TO = """Return-Path: <someone@someplace.com>\r
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed;\r
        d=gmail.com; s=20161025;\r
        h=mime-version:from:date:message-id:subject:to;\r
        bh=4c9vZm70ItvTkbMF9HikO6KKWJl5M95+W6HmkZxAYA0=;\r
        b=LUsCaJ4FEtgn0IYraRp5+iB2SDwwJ1wcTrgzdIyBqpYJNSaA0X0L6vweduQ7szGID9\r
         1vzYdqYgjoiyusVTEaNlZZq1Y0IseIUdlFhrR8oyYsSPgWDvSb5fHcXZzQrw0MKojakm\r
         1uQsHjiGYyLJZiDbg37g2O2FOah5imBRKsCd+xCy7bpFdhS3tuVtxUOZ1W0uXRd2PKB2\r
         DlLgfMtcpliGskJp4G6Kvv+BfSI835fULU0gITzL5wIt6YheL9Qu5ZKfQX94wpIRI5uj\r
         3o+jmMMCNWQWw/5Kt/2Y6Te4zHOS2cqoaZdlzCwokN3cX6fmfGXiuC6MJO/LNN3/cPH5\r
         SPIA==\r
From: Some One <someone@someplace.com>\r
Subject: Testing for event format\r
To: "Some One at someone@someplace.com"\r
            <info@example.com>\r
Reply-To: <test@example.com>\r
\r
Test message.\r
"""

class testSESEmail(unittest.TestCase):

    def setUp(self):
        # event
        self._event = SESEmailEvent(TEST_EVENT)
        # sender
        sender = Mock()
        sender.send_raw_email.return_value = {
            'MessageId': 'some_message_id'
        }
        self._sender = SESSender(sender, LOGGER)
        # config
        self._config = TEST_CONFIG
        # logger
        self._logger = Mock()

        self._email = SESEmail(TEST_EMAIL_BODY, self._event,
                               self._sender, self._config,
                               self._logger)

    def test_email_ok(self):
        self.assertEqual(TEST_SEND_EMAIL, self._email.email())

    def test_bad_event_in_constructor(self):
        event = copy.deepcopy(TEST_EVENT)
        event['Records'][0]['ses']['receipt']['recipients'] = []
        self.assertRaises(SESForwarderError, SESEmail, TEST_EMAIL_BODY,
                          SESEmailEvent(event), self._sender, self._config,
                          self._logger)

    def test_no_to_line(self):
        email = copy.deepcopy(TEST_EMAIL_BODY)
        email = email.replace("To: ", "Three: ")
        testObj = SESEmail(email, self._event,
                           self._sender, self._config,
                           self._logger)
        expected = copy.deepcopy(TEST_SEND_EMAIL)
        expected = expected.replace("To: ", "Three: ")
        expected = expected.replace("Reply-Three: ", "Reply-To: ")
        self.assertEqual(expected, testObj.email())

    def test_borked_to_line(self):
        email = copy.deepcopy(EMAIL_WITH_BORKED_TO)
        testObj = SESEmail(email, self._event,
                           self._sender, self._config,
                           self._logger)
        expected = copy.deepcopy(TEST_SEND_EMAIL)
        expected = expected.replace("To: info@example.com", 'To: "Some One at someone@someplace.com"\r\n            <info@example.com>')
        self.assertEqual(expected, testObj.email())
        

    def test_existing_reply_to(self):
        testObj = SESEmail(EMAIL_WITH_REPLY_TO, self._event,
                           self._sender, self._config,
                           self._logger)
        self.assertEqual(TEST_SEND_EMAIL, testObj.email())

    def test_from_line(self):
        email = copy.deepcopy(TEST_EMAIL_BODY)
        email = email.replace("From: ", "Three: ")
        self.assertRaises(SESForwarderError, SESEmail, email,
                          self._event, self._sender, self._config,
                           self._logger)

    def test_no_recipients(self):
        event = copy.deepcopy(TEST_EVENT)
        event['Records'][0]['ses']['receipt']['recipients'] = []
        self.assertRaises(SESForwarderError, SESEmail, TEST_EMAIL_BODY,
                          SESEmailEvent(event), self._sender, self._config,
                          self._logger)
        
    def test_send_ok(self):
        self.assertEqual('some_message_id', self._email.send()['MessageId'])

    def test_send_ko(self):
        event = copy.deepcopy(TEST_EVENT)
        event['Records'][0]['ses']['receipt']['recipients'] = ['nobody@example.com']
        testObj = SESEmail(TEST_EMAIL_BODY, SESEmailEvent(event),
                           self._sender, self._config,
                           self._logger)
        self.assertRaises(SESForwarderError, testObj.send)

    def test_send_raw_exception(self):
        sender = Mock()
        sender.send_raw_email.return_value = {
            'MessageId': 'some_message_id'
        }
        sender.send_raw_email.side_effect = ClientError(ERROR_RESPONSE,'operation_name')
        exceptionSender = SESSender(sender, LOGGER)
        testObj = SESEmail(TEST_EMAIL_BODY, SESEmailEvent(TEST_EVENT),
                           exceptionSender, self._config,
                           self._logger)
        self.assertRaises(ClientError, testObj.send)
        
if __name__ == '__main__':
    unittest.main()
