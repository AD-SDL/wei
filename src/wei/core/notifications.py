"""
Code for sending notifications to workcell users
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from wei.config import Config
from wei.core.state_manager import state_manager
from wei.types import Step
from wei.types.workflow_types import WorkflowRun
from wei.utils import threaded_task


@threaded_task
def send_email(subject: str, email_address: str, body: str):
    """Sends an email with the provided subject and body to the specified email address, using the configured SMTP relay server"""
    smtp_server = Config.smtp_server
    smtp_port = Config.smtp_port
    sender = "no-reply-rpl@anl.gov"

    try:
        # Create the MIMEText objects for the email content
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = email_address

        # Attach both plain text and HTML versions
        import re

        part1 = MIMEText(
            re.sub("<[^<]+?>", "", body), "plain"
        )  # * Strip HTML tags for plaintext
        part2 = MIMEText(body, "html")
        msg.attach(part1)
        msg.attach(part2)

        # Send the email via the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.sendmail(sender, email_address, msg.as_string())
        print(f"Email sent to {email_address}")
        return True
    except Exception as e:
        print(f"Error sending email to {email_address}: {e}")
        return False


def send_failed_step_notification(
    workflow_run: WorkflowRun,
    step: Step,
) -> None:
    """Send notifications using the configuration defined in the Workcell definition/cli args."""

    experiment = state_manager.get_experiment(workflow_run.experiment_id)
    for email_address in experiment.email_addresses:
        # * Email Content
        subject = f"STEP FAILED: {step.name}"
        body_html = f"""\
        <html>
        <body>
            <h1>Step '{step.name}' Failed</h1>
            <ul>
                <li>Step: {step.name} ({step.id})</li>
                <li>Module: {step.module}</li>
                <li>Workflow: {workflow_run.name} ({workflow_run.run_id})</li>
                <li>Experiment: {experiment.experiment_name} ({experiment.experiment_id})</li>
            </ul>
            See below for more info.
            <h2>Step Response</h2>
            <pre>{step.result.model_dump_json(indent=2)}</pre>
            <h2>Step Info</h2>
            <pre>{step.model_dump_json(indent=2)}</pre>
            <h2>Workflow Info</h2>
            <pre>{workflow_run.model_dump_json(indent=2)}</pre>
            <h2>Experiment Info</h2>
            <pre>{experiment.model_dump_json(indent=2)}</pre>
        </body>
        </html>
        """

        send_email(
            subject=subject,
            email_address=email_address,
            body=body_html,
        )
