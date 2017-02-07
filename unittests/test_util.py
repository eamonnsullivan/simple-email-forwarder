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
                    "recipients": ['info@example.com', 'members@example.com']
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

ERROR_RESPONSE = {'Error': {}}

TEST_SEND_EMAIL = b"""From: Some One at someone@someplace.com <info@example.com>\r
Subject: [TEST Info] Testing for event format\r
To: info@example.com\r
Reply-To: Some One <someone@someplace.com>\r
\r
Test message.\r
"""

TEST_EMAILS = {
    'admin': ['admin@example.com'],
    'info': ['user1@example.com', 'user2@example.com'],
    'members': ['user1@example.com', 'user2@example.com', 'user3@example.com']
}

TEST_CONFIG = {
    'fromEmail': '',
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
