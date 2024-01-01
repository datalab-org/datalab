"""Send an email using Flask-Mail with the configured SMTP server."""

import os

from flask_mail import Mail, Message

MAIL = Mail()


def send_mail(recipient: str, subject: str, body: str):
    """Send an email via the configured SMTP server.

    Mail will be sent from the configured `MAIL_DEFAULT_SENDER` address,
    via the configured `MAIL_SERVER` using `MAIL_USERNAME` and `MAIL_PASSWORD` credentials
    on `MAIL_PORT` using `MAIL_USE_TLS` encryption.

    Parameters:
        recipient (str): The email address of the recipient.
        subject (str): The subject of the email.
        body (str): The body of the email.

    """
    message = Message(
        sender=os.environ["MAIL_DEFAULT_SENDER"], recipients=[recipient], body=body, subject=subject
    )
    MAIL.send(message)
