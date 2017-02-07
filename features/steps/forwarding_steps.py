"""
Steps file for testing forwarding of emails.

"""
from behave import *
from SimpleForwarder import *
from mock import Mock, MagicMock
from StringIO import StringIO

with open('emailBody.txt', 'r') as fp:
    FULL_TEST_EMAIL = fp.read()

TEST_EMAILS = {
    'admin': ['admin@example.com'],
    'info': ['user1@example.com', 'user2@example.com'],
    'members': ['user1@example.com', 'user2@example.com', 'user3@example.com']
}

TEST_CONFIG = {
    'fromEmail': 'testing@example.com',
    'subjectPrefix': {
        'Default': '[SVP] ',
        'admin@example.com': '[TEST Admin] ',
        'info@example.com': '[TEST Info] ',
        'members@example.com': '[TEST Members] '
    },
    'emailBucket': 'test-bucket',
    'emailKeyPrefix': '',
    'forwardMapping': {
        'admin@example.com': TEST_EMAILS['admin'],
        'info@example.com': TEST_EMAILS['info'],
        'members@example.com': TEST_EMAILS['members'],
        'example.com': [
            # messages to users that don't match the above
        ]
    }
}

TEST_EVENT = {
    "Records": [
        {
            "eventSource": "aws:ses",
            "eventVersion": "1.0",
            "ses": {
                "mail": {
                    "source": "someone@somedomain.com",
                    "messageId": "3bnsm1c2akm1gded3speted0hpnglijt74jbd201",
                    "destination": [
                        "info@example.com"
                    ],
                    "headers": [],
                    "commonHeaders": {}
                },
                "receipt": {
                    "recipients": [],
                }
            }
        }
    ]
}

TEST_EMAIL_BODY = """Return-Path: <someone@someplace.com>\r
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
\r
Test message.\r
"""

EXPECTED_EMAIL_BODY_INFO = b"""From: Some One at someone@someplace.com <testing@example.com>\r
Subject: [TEST Info] Testing for event format\r
To: info@example.com\r
Reply-To: Some One <someone@someplace.com>\r
\r
Test message.\r
"""

EXPECTED_EMAIL_BODY_MEMBERS = b"""From: Some One at someone@someplace.com <testing@example.com>\r
Subject: [TEST Members] Testing for event format\r
To: info@example.com\r
Reply-To: Some One <someone@someplace.com>\r
\r
Test message.\r
"""

EXPECTED_SUBJECT = {
    'info': '[TEST Info] Testing for event format',
    'members': '[TEST Members] Testing for event format'
}

# mock SES client
SES_MOCK = Mock()

# mock S3 resource
S3_MOCK = Mock()


class TestFailure(Exception):
    """ Exception wrapper. """
    def __init__(self, value):
        super(TestFailure, self).__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)


@given(u'emails have been configured for the {text} address')
def step_impl(context, text):
    SES_MOCK.reset_mock()
    SES_MOCK.send_raw_email.return_value = {
        'MessageId': 'some_message_id'
    }
    S3_MOCK.reset_mock()
    address = text.replace('"', '')
    read_dict = {'Body': MagicMock(spec=file, wraps=StringIO(TEST_EMAIL_BODY))}
    get_mock = MagicMock()
    get_mock.__getitem__.side_effect = read_dict.__getitem__
    S3_MOCK.Object.return_value.get.return_value = get_mock
    config = TEST_CONFIG['forwardMapping']
    config[address + '@example.com'] = TEST_EMAILS[address]


@when(u'an email is sent to the {text} address')
def step_impl(context, text):
    event = TEST_EVENT
    address = [text.replace('"', '') + '@example.com']
    event['Records'][0]['ses']['receipt']['recipients'] = address
    lambda_handler(event, {}, SES_MOCK, S3_MOCK, config=TEST_CONFIG)


@then(u'the email is forwarded to the {text} emails')
def step_impl(context, text):
    address = text.replace('"', '')
    destinations = SES_MOCK.send_raw_email.call_args[1]['Destinations']
    source = SES_MOCK.send_raw_email.call_args[1]['Source']
    raw_message = SES_MOCK.send_raw_email.call_args[1]['RawMessage']
    for email in TEST_EMAILS[address]:
        if email not in destinations:
            errMsg = 'Email {} not found in {}'.format(
                email,
                destinations
            )
            raise TestFailure(errMsg)
    if not source == address + '@example.com':
        errMsg = 'Source of {} is not as expected: {}'.format(
            source,
            address + '@example.com'
        )
        raise TestFailure(errMsg)

    if address == 'info':
        expected_raw_message = {'Data': bytearray(EXPECTED_EMAIL_BODY_INFO)}
    else:
        expected_raw_message = {'Data': bytearray(EXPECTED_EMAIL_BODY_MEMBERS)}

    if raw_message != expected_raw_message:
        raise TestFailure('expected message: {}, actual_message {}'.format(
            expected_raw_message,
            raw_message
        ))


@given(u'no emails have been configured for the default domain address')
def step_impl(context):
    TEST_CONFIG['forwardMapping']['example.com'] = []


@when(u'an email is sent to an unknown address')
def step_impl(context):
    event = TEST_EVENT
    addr = ['unknown@example.com']
    event['Records'][0]['ses']['receipt']['recipients'] = addr
    lambda_handler(event, {}, SES_MOCK, S3_MOCK, config=TEST_CONFIG)


@then(u'the email is dropped and no action is taken')
def step_impl(context):
    if SES_MOCK.called:
        raise TestFailure('The send function was called.')


@given(u'a prefix has been configured for {text} subject lines')
def step_impl(context, text):
    TEST_CONFIG['subjectPrefix'] = {
        'Default': '[SVP] ',
        'admin@example.com': '[TEST Admin] ',
        'info@example.com': '[TEST Info] ',
        'members@example.com': '[TEST Members] '
    }


@then(u'the resulting email subject line includes the {text} prefix')
def step_impl(context, text):
    address = text.replace('"', '')
    raw_message = SES_MOCK.send_raw_email.call_args[1]['RawMessage']
    expected = EXPECTED_SUBJECT[address]
    if expected not in raw_message['Data']:
        raise TestFailure(
            'Expected subject {} not found in message: {}'.format(
                expected,
                raw_message
            ))

@given(u'the configuration specifies a hard-coded fromEmail')
def step_impl(context):
    TEST_CONFIG['fromEmail'] = 'me@example.com'


@given(u"the configuration doesn't specify a fromEmail")
def step_impl(context):
    TEST_CONFIG['fromEmail'] = None

@then(u'the resulting email "From" header includes the configured address')
def step_impl(context):
    address = "members"
    raw_message = SES_MOCK.send_raw_email.call_args[1]['RawMessage']
    expected_from = 'From: Some One at someone@someplace.com <me@example.com>'
    if expected_from not in raw_message['Data']:
        raise TestFailure(
            'Expected from {} not found in message: {}'.format(
                expected_from,
                raw_message
            ))


@then(u'the resulting email "From" header includes the first "to" address')
def step_impl(context):
    address = "info"
    raw_message = SES_MOCK.send_raw_email.call_args[1]['RawMessage']
    expected_from = 'From: Some One at someone@someplace.com <info@example.com>'
    if expected_from not in raw_message['Data']:
        raise TestFailure(
            'Expected from {} not found in message: {}'.format(
                expected_from,
                raw_message
            ))

@then(u'the resulting email doesn\'t have a "Return-Path" header')
def step_impl(context):
    raw_message = SES_MOCK.send_raw_email.call_args[1]['RawMessage']
    return_path = 'Return-Path: <info@example.com>'
    if return_path in raw_message['Data']:
        raise TestFailure(
            'Unexpected Return-Path {} found in message: {}'.format(
                return_path,
                raw_message
            ))



