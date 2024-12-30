from django.conf import settings
from django.core.mail import send_mail


def mail_send(address, subject, message):
    address = address
    subject = subject
    message = message

    if address and subject and message:
        try:
            send_mail(subject, message, settings.EMAIL_HOST_USER, [address])
            print("Email sent successfully")
        except Exception as e:
            print(f"Error sending email: {e}")
