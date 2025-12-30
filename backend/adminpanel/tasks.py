from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_admin_notification_email(recipients, message_markdown):
    """
    recipients: list of email strings
    message_markdown: markdown text (currently sent as plain text)
    """
    subject = "Team Task Board Notification"
    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@example.com")

    if not recipients:
        return {"status": "no_recipients"}

    send_mail(
        subject=subject,
        message=message_markdown,
        from_email=from_email,
        recipient_list=recipients,
        fail_silently=False,
    )
    return {"status": "sent", "recipients_count": len(recipients)}
