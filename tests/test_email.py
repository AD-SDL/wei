"""Send email notifications using AWS SES"""

import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

# AWS SES configuration
AWS_REGION = "us-west-1"  # Change to your AWS region
AWS_ACCESS_KEY = "key"
AWS_SECRET_KEY = "key"

# Email details
SENDER = "yamacozgulbas@gmail.com"
SUBJECT = "Test Email from Amazon SES"
BODY_TEXT = (
    "Amazon SES Test (Python)\r\n"
    "This email was sent with Amazon SES using the "
    "AWS SDK for Python (Boto)."
)
BODY_HTML = """<html>
<head></head>
<body>
  <h1>Amazon SES Test (Python)</h1>
  <p>This email was sent with
    <a href='https://aws.amazon.com/ses/'>Amazon SES</a> using the
    <a href='https://boto3.amazonaws.com/v1/documentation/api/latest/index.html'>AWS SDK for Python (Boto)</a>.
  </p>
</body>
</html>
"""

CHARSET = "UTF-8"


def send_email_ses(recipient):
    """Create a new SES resource and specify a region"""
    client = boto3.client(
        "ses",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )

    # Try to send the email
    try:
        response = client.send_email(
            Destination={
                "ToAddresses": [recipient],
            },
            Message={
                "Body": {
                    "Html": {
                        "Charset": CHARSET,
                        "Data": BODY_HTML,
                    },
                    "Text": {
                        "Charset": CHARSET,
                        "Data": BODY_TEXT,
                    },
                },
                "Subject": {
                    "Charset": CHARSET,
                    "Data": SUBJECT,
                },
            },
            Source=SENDER,
        )
    except NoCredentialsError:
        print("Credentials not available")
        return False
    except PartialCredentialsError:
        print("Incomplete credentials")
        return False
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False

    return response


def main():
    """Main function to send emails to the addresses in the list"""
    email_addresses = ["dozgulbas@anl.gov"]

    for email in email_addresses:
        response = send_email_ses(email)
        if response:
            print(f"Email sent to {email}. Message ID: {response['MessageId']}")
        else:
            print(f"Failed to send email to {email}")


if __name__ == "__main__":
    main()
