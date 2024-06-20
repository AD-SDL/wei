"""SMTP method to send emails over Argonne gateway"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# SMTP server configuration
SMTP_SERVER = "mailgateway.anl.gov"
SMTP_PORT = 25  # Port 25 is commonly used for SMTP

# Email details
SENDER = "no-reply@anl.gov"  # Your email address
SUBJECT = "Test Email from SMTP Server"
# STEP FAILED ON ACTION/MODULE
BODY_TEXT = "This is a test email sent using the SMTP server."
# BODY INCLUDE WORKFLOW OBJECT (JSON TO STR) & STEP RESPONSE
BODY_HTML = """\
<html>
  <body>
    <h1>This is a test email</h1>
    <p>This email was sent using the SMTP server.</p>
  </body>
</html>
"""


def send_email_smtp(recipient):
    """Sends emails using smtp server over Argonne mailgateway"""
    try:
        # Create the MIMEText objects for the email content
        msg = MIMEMultipart("alternative")
        msg["Subject"] = SUBJECT
        msg["From"] = SENDER
        msg["To"] = recipient

        # Attach both plain text and HTML versions
        part1 = MIMEText(BODY_TEXT, "plain")
        part2 = MIMEText(BODY_HTML, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send the email via the SMTP server
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(SENDER, recipient, msg.as_string())
        print(f"Email sent to {recipient}")
        return True
    except Exception as e:
        print(f"Error sending email to {recipient}: {e}")
        return False


def main():
    """Main function"""
    email_addresses = ["dozgulbas@anl.gov", "ryan.lewis@anl.gov"]

    for email in email_addresses:
        send_email_smtp(email)


if __name__ == "__main__":
    main()
