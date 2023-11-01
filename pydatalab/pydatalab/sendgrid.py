def send_mail(recipient, subject, body):
    import os

    import sendgrid
    from sendgrid.helpers.mail import Content, Email, Mail, To

    sg = sendgrid.SendGridAPIClient(api_key=os.environ["MAIL_PASSWORD"])
    from_email = Email(os.environ["MAIL_DEFAULT_SENDER"])
    try:
        to_email = To(recipient)
    except ValueError:
        raise RuntimeError(f"Invalid email address {recipient}")
    content = Content("text/plain", body)
    mail = Mail(from_email, to_email, subject, content)
    response = sg.client.mail.send.post(request_body=mail.get())
    if response.status_code != 202:
        raise RuntimeError(f"Failed to send email: {response.body}")
