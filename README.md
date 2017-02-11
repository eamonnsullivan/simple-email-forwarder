# Simple Forwarder

The Simple Forwarder is designed to run on Amazon Web Services, as a lambda function. It interacts with the Simple Email Service (SES) and Simple Storage Service (S3), taking email sent to an address and forwarding it a list of other email addresses. It is a very basic solution for small businesses, charities and other organizations that need a public-facing email address at their own domain (`info@example.com`), but don't need the complexity of a full email server.

If you just need to put an email address on the side of a van or on a poster, and you don't need a full, online-office solution, this might be what you are looking for.

## Credit

The software was inspired by and largely follows the approach of @arithmetric's node.js-based [AWS Lambda SES Email Forwarder](https://github.com/arithmetric/aws-lambda-ses-forwarder). The configuration, for example, is almost identical and it works basically the same way. If you are more familiar with JavaScript, then @arithmetric's project will be a better fit. The only reason I rewrote it was to learn AWS's Python API. I also had a need to refresh myself on the latest testing frameworks in Python. I used [Behave](http://pythonhosted.org/behave/) for the high-level, behaviour-driven testing and [nose2](http://nose2.readthedocs.io/en/latest/getting_started.html) for the unit testing.

## How It Works (high level)

1. SES accepts email for your domain, saves the email to an S3 bucket and sends an "event" to SimpleForwarder.
2. SimpleForwarder reads the email from the S3 bucket and sends the email to a specified list of addresses. You can specify different forwarding lists for each receiving address. For example, email sent to `info@yourdomain.com` can go to one set of addresses, while email sent to `orders@yourdomain.com` goes to another.

## Limitations

SES will only send email from a "verified" address, one that is at a domain you control or one that you have set up in advance (by clicking a link sent to that email address). Since this software is designed to forward email from arbitrary senders, we can't just put the sender's email into the "From:" header. Instead, we add a "Reply-To:" header that points to the sender's original address. We then rewrite the "From:" address, either with an address you specify (in fromEmail) or we take the first To: address (which, by definition, is verified). 

This will be easier to understand with an example: If `Jane Doe <janedoe@example.com>` sends an email to `info@yourdomain.com` and we've configured `user1@yourdomain.com` to accept "info" email, SimpleForwarder will rewrite the header to something like this before sending:

```
From: "Jane Doe at janedoe@example.com" <info@yourdomain.com>
To: <user1@yourdomain.com>
Reply-To: <janedoe@example.com>
```

If your email doesn't handle the Reply-To correctly (Gmail appears to ignore this, for example), you might need to copy & paste the email from the To: section. This is why the software includes the original address in the text part of the From: header. In most email software, this will be displayed as `Jane Doe at janedoe@example.com`, making it easy to see and reply to the sender, even if your software ignores the Reply-To: header.

Also, SES won't *send* to any address that isn't verified while in the "SandBox". That might be fine if the addresses you are sending to are your own or family members, but if you need to be able to send to arbitrary addresses, you'll need to break out of the sandbox. The main [Amazon SES documentation](http://docs.aws.amazon.com/ses/latest/DeveloperGuide/Welcome.html) covers this in great detail. You basically fill out a form and promise not to spam.

## Setup

1. Set up SES to accept email for your domain. If you have registered a domain using Amazon's own Route 53, then this is a little easier, but it's not that difficult if you are using someone else's DNS. You'll need to add a TXT record to your domain with a particular value.

2. Create an S3 bucket to hold the received email. We'll need to configure the access controls on this so that both SES and the lambda function can access it, but we'll get back to that. Depending on how much email you get, you might want to configure some Storage Management on this bucket. I've set up mine to transfer email to cheaper storage after 30 days and then permanently delete it after 60 days.

3. Modify SimpleForwarder.py by changing the configuration at the top of the script to suit your needs. At a minimum, you'll need to modify the domain and provide an S3 bucket location (which you just created) where SES will put the emails.

4. Create a new "Blank" Lambda function. Give it a name (we'll assume it's called "SimpleForwarder" in subsequent steps) and use the Python 2.7 runtime environment. Copy & paste the code from SimpleForwarder.py into the code editor. The code is organized so it is all in one file. Ensure the handler is set to `SimpleForwarder.lambda_handler`. You can also upload the code using the aws command-line interface and a zip file. See the `deploy-version.sh` script as an example.

5. For the Role, choose "Basic Execution Role" under Create New Role. Give the role a name, like SimpleForwarderRole. You'll need to modify the role policy to allow sending email and reading and writing from S3. My looks something like this. Substitute MY-BUCKET-NAME-HERE with the name you gave your S3 bucket:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        },
        {
            "Effect": "Allow",
            "Action": "ses:SendRawEmail",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
				"s3:PutObjectAcl",
				"s3:PutObjectVersionAcl",
				"s3:ReplicateDelete",
				"s3:ReplicateObject"
            ],
            "Resource": "arn:aws:s3:::MY-BUCKET-NAME-HERE/*"
        }
    ]
}
```

6. Leave the memory set to 128MB. I set the timeout to 5 seconds, which seems to be plenty of time. 

7. Configure a rule set for SES so that it runs your lambda function when it receives email. The way I did this was to create a rule to handle the addresses I want to receive (in my case it was `admin@mydomain`, `info@mydomain` and `members@mydomain`). The first action is save the email to an S3 bucket, the one you created in step 2 and specified in the role policy in step 5. The second action is to run your Lambda function. Choose the name from the "Lambda function" drop-down. Set the "Invocation type" to "Event". If asked to allow SES to set up "invoke lambda" permissions, say yes.

8. This step is optional. I wanted to bounce emails that aren't one of the three I've set up. So I set the last action to "Stop Rule Set". Then I created another rule set to bounce any emails addressed to other users, using the 550 "Mailbox does not exist" template. Make sure this action runs after the forwarding.

9. You'll probably need to configure your S3 bucket to allow access to both the lambda function and SES. Go to the S3 bucket, click on Properties, then Permissions and then Edit Bucket policy. Mine looks something like this. Fill in your own MY-BUCKET-NAME-HERE, MY-ACCOUNT-NUMBER, MY-ROLE-NAME-HERE.

```json
{
	"Version": "2012-10-17",
	"Id": "Policy1482002421752",
	"Statement": [
		{
			"Sid": "GiveSESPermissionToWriteEmail",
			"Effect": "Allow",
			"Principal": {
				"Service": "ses.amazonaws.com"
			},
			"Action": "s3:PutObject",
			"Resource": "arn:aws:s3:::MY-BUCKET-NAME-HERE/*",
			"Condition": {
				"StringEquals": {
					"aws:Referer": "MY-ACCOUNT-NUMBER"
				}
			}
		},
		{
			"Sid": "xxxxx",
			"Effect": "Allow",
			"Principal": {
				"AWS": "arn:aws:iam::MY-ACCOUNT-NUMBER:role/MY-ROLE-NAME-HERE"
			},
			"Action": [
				"s3:GetObject",
				"s3:PutObject",
				"s3:PutObjectAcl",
				"s3:PutObjectVersionAcl",
				"s3:ReplicateDelete",
				"s3:ReplicateObject"
			],
			"Resource": "arn:aws:s3:::MY-BUCKET-NAME-HERE/*",
			"Condition": {
				"StringEquals": {
					"aws:Referer": "MY-ACCOUNT-NUMBER"
				}
			}
		}
	]
}
```




