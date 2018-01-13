Feature: Forward emails sent to Amazon's SES

  Scenario: Email sent to info@ gets forwarded to the correct list
    Given emails have been configured for the "info" address
    When an email is sent to the "info" address
    Then the email is forwarded to the "info" emails

  Scenario: Email sent to members@ gets forwarded to correct list
    Given emails have been configured for the "members" address
    When an email is sent to the "members" address
    Then the email is forwarded to the "members" emails

  Scenario: Email sent to an unknown address is dropped
    Given no emails have been configured for the default domain address
    When an email is sent to an unknown address
    Then the email is dropped and no action is taken

  Scenario: Email sent to info@ gets a special subject prefix
    Given emails have been configured for the "info" address
    And a prefix has been configured for "info" subject lines
    When an email is sent to the "info" address
    Then the resulting email subject line includes the "info" prefix

  Scenario: Email sent to members@ gets a special subject prefix
    Given emails have been configured for the "members" address
    And a prefix has been configured for "members" subject lines
    When an email is sent to the "members" address
    Then the resulting email subject line includes the "members" prefix

  Scenario: Email gets configured "from" address
    Given emails have been configured for the "members" address
    And the configuration specifies a hard-coded fromEmail
    When an email is sent to the "members" address
    Then the resulting email "From" header includes the configured address
    And the resulting email doesn't have a "Return-Path" header

  Scenario: Email gets first "to" address if "fromEmail" is blank
    Given emails have been configured for the "info" address
    And the configuration doesn't specify a fromEmail
    When an email is sent to the "info" address
    Then the resulting email "From" header includes the first "to" address
    And the resulting email doesn't have a "Return-Path" header

  Scenario: Email flagged as spam is dropped
    Given emails have been configured for the "info" address
    When an email is sent to the "info" address with a header indicating spam
    Then the email is dropped and no action is taken

  Scenario: Email flagged as containing a virus is dropped
    Given emails have been configured for the "members" address
    When an email is sent to the "members" address with a header indicating a virus
    Then the email is dropped and no action is taken
