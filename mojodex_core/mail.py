import os

from mojodex_core.logging_handler import  MojodexCoreLogger

mail_logger = MojodexCoreLogger("mail_logger")

admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []


class MailClientLogging:
    def __init__(self):
        pass

    def send_mail(self, subject, recipients, text):
        mail_logger.info(f"Subject: {subject} | Recipients: {recipients} | Text: {text}")


mojo_mail_client = None
try:
    if os.environ.get('SENDER_EMAIL', ''):
        from mojodex_core.email_sender import MojoAwsMail
        mojo_mail_client = MojoAwsMail(sender_name=os.environ['SENDER_NAME'], sender_email=os.environ['SENDER_EMAIL'],
                                    region="eu-west-3")
    else:
        mojo_mail_client = MailClientLogging()
except Exception as e:
    mail_logger.info(f"No email client available.")
    mojo_mail_client = MailClientLogging()


def send_admin_error_email(error_message):
    try:
        mojo_mail_client.send_mail(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                                       recipients=technical_email_receivers,
                                       text=error_message)
    except Exception as e:
        mail_logger.error(f"Error while sending admin email : {e}")


def send_admin_email(subject, recipients, text):
    try:
        if mojo_mail_client:
            mojo_mail_client.send_mail(subject=subject,
                                       recipients=recipients,
                                       text=text)
    except Exception as e:
        mail_logger.error(f"Error while sending admin email : {e}")
