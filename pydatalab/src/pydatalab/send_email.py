"""Send an email using Flask-Mail with the configured SMTP server."""

from flask_mail import Mail, Message

from pydatalab.config import CONFIG
from pydatalab.logger import LOGGER

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
    LOGGER.debug("Sending email to %s with subject %s", recipient, subject)

    sender = None
    if CONFIG.EMAIL_AUTH_SMTP_SETTINGS is not None:
        sender = CONFIG.EMAIL_AUTH_SMTP_SETTINGS.MAIL_DEFAULT_SENDER

    message = Message(
        sender=sender,
        recipients=[recipient],
        body=body,
        subject=subject,
    )
    MAIL.connect()
    MAIL.send(message)
    LOGGER.debug("Email sent to %s", recipient)
