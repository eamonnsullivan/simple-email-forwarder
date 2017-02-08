"""
To use, modify the DEFAULT_CONFIG. At a minimum, you'll need to
provide an emailBucket and change the forwardMapping to the addresses
you want to handle.

"""

from __future__ import print_function
import logging
import re
import boto3
import botocore

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

DEFAULT_CONFIG = {
    'fromEmail': '',
    'subjectPrefix': {
        'Default': '',
        'admin@example.com': '[Admin] ',
        'info@example.com': '[Info] ',
        'members@example.com': '[Members] '
    },
    'emailBucket': 's3-bucket-for-email',
    'emailKeyPrefix': '',
    'forwardMapping': {
        'admin@example.com': [
            'user1@example.com',
            'user2@example.com'
        ],
        'info@example': [
            'user1@example.com',
            'user2@example.com',
            'user3@example.com'
        ],
        'members@svpsouthruislip.org.uk': [
            'user3@example.com',
            'user4@example.com',
            'user5@example.com'
        ],
        'example.com': [
            # messages to users that don't match the above
        ]
    }
}


def lambda_handler(event,
                   context,
                   ses_client=boto3.client('ses'),
                   s3_client=boto3.resource('s3'),
                   config=None):
    """
    Handler function to be invoked with an inbound SES email as the
    event.
    """
    if not config:
        config = DEFAULT_CONFIG
    LOGGER.info("Got event: %s", event)
    LOGGER.debug("Context: %s", context)
    event = SESEmailEvent(event)
    new_recipients = get_new_recipients(event.get_recipients(), config)
    if len(new_recipients) > 0:
        LOGGER.info("Rewriting original recipients %s to %s",
                    event.get_recipients(), new_recipients)
        sender = SESSender(ses_client, LOGGER)
        full_email = S3Object(s3_client,
                              config['emailBucket'],
                              event.get_email()['messageId'])
        email = SESEmail(full_email.get('Body'),
                         event, sender, config, LOGGER)
        email.send()
    else:
        LOGGER.info("Finishing event, no matching recipients")


def get_new_recipients(original_recipients, config):
    """ Find the new recipients. """
    original = [x.lower() for x in original_recipients]
    new_recipients = []
    forward_mapping = config['forwardMapping']
    for recipient in original:
        if recipient in forward_mapping:
            new_recipients.extend(forward_mapping[recipient])
        else:
            domain = recipient.split('@')[1]
            if domain in forward_mapping:
                new_recipients.extend(forward_mapping[domain])
    new_recipients = list(set(new_recipients))
    return new_recipients


class SESForwarderError(Exception):
    """ Exception wrapper. """
    def __init__(self, value):
        super(SESForwarderError, self).__init__(value)
        self.value = value

    def __str__(self):
        return repr(self.value)


class SESEmailEvent(object):
    """ Wraps an event with some simple getters."""
    def __init__(self, event):
        self._event = event
        if not self._validate_event():
            raise SESForwarderError("Invalid event: {}".format(event))

    def get_email(self):
        """ return just the email part of the event"""
        return self._event['Records'][0]['ses']['mail']

    def get_recipients(self):
        """ Return just the recipients part of the event."""
        return self._event['Records'][0]['ses']['receipt']['recipients']

    def _validate_event(self):
        """ Ensure that we have the bits we need. """
        if 'Records' in self._event:
            if len(self._event['Records']) > 0:
                record = self._event['Records'][0]
                if 'eventSource' in record and 'eventVersion' in record:
                    return record['eventSource'] == 'aws:ses'


class SESSender(object):
    """Wraps sending functionality for dependency injection during
       testing."""
    def __init__(self, awsClient, logger):
        self._client = awsClient
        self._logger = logger
        self._email = None

    def send(self, recipients, original_recipient):
        """ Send the email to the specified recipients. """
        if not self._email:
            raise SESForwarderError("No email set before sending.")
        try:
            self._logger.debug("Sending email from: %s", original_recipient)
            self._logger.debug("Sending destination: %s", recipients)
            self._logger.debug("Sending email: %s", self._email)
            return self._client.send_raw_email(
                Destinations=recipients,
                Source=original_recipient,
                RawMessage={
                    'Data': self._email
                })
        except botocore.exceptions.ClientError as err:
            self._logger.error("Failed to send message. Error: %s", err)
            raise

    def set_email(self, email):
        """ Set the email to be sent."""
        self._email = bytearray(email, 'utf-8')

    def get_email(self):
        """ Get the currently set email."""
        return self._email


class S3Object(object):
    """Wraps getting an object from an S3 bucket for dependency injection
       during testing."""
    def __init__(self, awsStorageClient, bucket, objectId):
        self._client = awsStorageClient
        self._bucket = bucket
        self._id = objectId

    def get(self, section):
        """ Return the specified section of the object as a blob"""
        try:
            return self._client.Object(
                self._bucket, self._id).get()[section].read()
        except botocore.exceptions.ClientError:
            raise SESForwarderError(
                "Failed to get object from s3 bucket: {0}, key: {1}".format(
                    self._bucket, self._id))

    def get_bucket(self):
        """ Currently active bucket."""
        return self._bucket

    def get_id(self):
        """ Currently active id. """
        return self._id


class SESEmail(object):
    """ Wraps the email and methods to transform it.  """
    def __init__(self, emailS3Blob, event,
                 sender, config, logger):
        whole = emailS3Blob.split('\r\n')
        start_body = whole.index('')
        self._header = whole[0:start_body]
        self._body = whole[start_body:]
        self._event = event
        self._recipients = get_new_recipients(event.get_recipients(), config)
        self._sender = sender
        self._config = config
        self._logger = logger
        self._rewrite_header()

    def email(self):
        """ Return the processed email. """
        result = '\r\n'.join(self._header) + '\r\n' + '\r\n'.join(self._body)
        # Remove all DKIM-Signature headers, since we've modified the
        # message and they'll be invalid anyway. We have to do this with
        # regular expressions because they span lines.
        pattern = re.compile(r"DKIM-Signature: .+\r\n(\s+.+\r\n)+",
                             re.MULTILINE)
        return pattern.sub("", result)

    def send(self):
        """ Send the email. """
        self._sender.set_email(self.email())
        self._logger.info("Sending email. New: %s, Original: %s",
                          self._recipients,
                          self._event.get_recipients())
        if len(self._recipients) and len(self._event.get_recipients()):
            return self._sender.send(self._recipients,
                                     self._event.get_recipients()[0])
        else:
            raise SESForwarderError(
                "Attempt to send with no recipients or original_recipients.")

    def _rewrite_header(self):
        self._add_reply_to()
        self._replace_from()
        self._add_subject_prefix()
        self._remove_return_path()
        self._remove_sender_header()

    def _add_reply_to(self):
        prev_reply_to = self._get_header_section('Reply-To: ')
        if len(prev_reply_to) > 0:
            # remove any existing reply-to header
            self._logger.info("removing exist reply-to header: %s",
                              prev_reply_to)
            self._header = self._remove_header_section('Reply-To: ')
        from_line = self._get_header_section('From: ')
        if len(from_line) > 0:
            reply_to = 'Reply-To: ' + from_line[0].replace('From: ', '')
            self._logger.info("Adding Reply-To to the header: %s",
                              reply_to)
            self._header.append(reply_to)
        else:
            self._logger.error("Unable to extract From address.")

    def _replace_from(self):
        # Replace the message's From: and Return-Path: headers with
        # either the hard-coded from address from the configuration or
        # the first, original recipient. Either is a verified
        # domain. SES won't let us send from an unverified "From"
        # address, so error out if this fails.
        from_line = self._get_header_section('From: ')
        if not len(self._event.get_recipients()) or len(from_line) == 0:
            raise SESForwarderError(
                "Failed to rewrite 'from' address. Header: {}".format(
                    self._header))

        self._logger.info("Original from address: %s", from_line[0])
        new_from = from_line[0]
        original = self._config['fromEmail'] or self._event.get_recipients()[0]
        self._logger.info("Replacing from address with: %s", original)
        new_from = new_from.strip(' \r\n\t')
        new_from = new_from.replace('<', 'at ')
        new_from = new_from.replace('>', '')
        new_from = new_from + ' <' + original + '>'
        self._header[self._header.index(from_line[0])] = new_from

        # do similar to the Return-Path line, if it exists
        return_path = self._get_header_section('Return-Path: ')
        if len(return_path) > 0:
            index = self._header.index(return_path[0])
            self._header[index] = "Return-Path: <" + original + ">"

    def _add_subject_prefix(self):
        prefix = self._config['subjectPrefix']['Default']
        first_recipient = self._event.get_recipients()[0]
        if first_recipient in self._config['subjectPrefix']:
            prefix = self._config['subjectPrefix'][first_recipient]
        subject = self._get_header_section('Subject: ')[0]
        if subject:
            indx = self._header.index(subject)
            self._header[indx] = 'Subject: ' + \
                                 prefix + \
                                 subject.replace('Subject: ', '')

    def _remove_return_path(self):
        self._header = self._remove_header_section('Return-Path: ')

    def _remove_sender_header(self):
        self._header = self._remove_header_section('Sender: ')

    def _get_header_section(self, start):
        return [elem for elem in self._header if elem.startswith(start)]

    def _remove_header_section(self, start):
        return [elem for elem in self._header if not elem.startswith(start)]
