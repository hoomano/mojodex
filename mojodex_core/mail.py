import os
from mojodex_core.logging_handler import  MojodexCoreLogger

mail_logger = MojodexCoreLogger("mail_logger")

admin_email_receivers = os.environ["ADMIN_EMAIL_RECEIVERS"].split(",") if "ADMIN_EMAIL_RECEIVERS" in os.environ else []
technical_email_receivers = os.environ["TECHNICAL_EMAIL_RECEIVERS"].split(",") if "TECHNICAL_EMAIL_RECEIVERS" in os.environ else []
print("🔵🔵🔵🔵🔵")
def _configure_email_sender():
    try:
        mojo_mail_client = None
        if os.environ.get('AWS_SES_REGION', ''):
            from mojodex_core.email_sender.aws_email_sender import MojoAwsMail
            mojo_mail_client = MojoAwsMail()
            mail_logger.info("🔵 AWS SES email client configured.")
        elif os.environ.get('SMTP_ADDRESS', ''):
            from mojodex_core.email_sender.smtp_email_sender import SMTPEmailSender
            mojo_mail_client = SMTPEmailSender()
            mail_logger.info("🔵 SMTP email client configured.")
        else:
            mail_logger.info("🔵 No email client configured.")
        return mojo_mail_client
    except Exception as e:
        mail_logger.info(f"Error configuring email sender: {e}")

mojo_mail_client = _configure_email_sender()

def send_technical_error_email(error_message):
    try:
        if mojo_mail_client:
            mojo_mail_client.send_email(subject=f"MOJODEX ERROR - {os.environ['ENVIRONMENT']}",
                                        recipients=technical_email_receivers,
                                        text_body=error_message)
    except Exception as e:
        mail_logger.error(f"Error while sending technical error email : {e}")


def send_admin_email(subject, recipients, text):
    try:
        if mojo_mail_client:
            mojo_mail_client.send_email(subject=subject,
                                       recipients=recipients,
                                       text_body=text)
    except Exception as e:
        mail_logger.error(f"Error while sending admin email : {e}")
